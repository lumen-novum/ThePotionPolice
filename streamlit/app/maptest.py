import os
from pathlib import Path

import pandas as pd
import streamlit as st
import pydeck as pdk
import matplotlib.pyplot as plt
import numpy as np


st.set_page_config(page_title="Cauldron Map (local)", layout="wide")


BASE = Path(__file__).resolve().parents[2]  # repo root
BACKEND_DIR = BASE / 'backend'

CAULDRONS_CSV = BACKEND_DIR / 'cauldrons.csv'
DATA_CSV = BACKEND_DIR / 'cauldron_data.csv'
RATES_CSV = BACKEND_DIR / 'cauldron_rates.csv'


def load_cauldrons(path):
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    # normalize column names
    cols = {c.lower(): c for c in df.columns}
    # prefer latitude/longitude, fallback to lat/lng
    lat_col = cols.get('latitude') or cols.get('lat')
    lon_col = cols.get('longitude') or cols.get('lng') or cols.get('lon')
    id_col = cols.get('id') or cols.get('cauldron_id')
    name_col = cols.get('name')
    if not lat_col or not lon_col:
        return pd.DataFrame()
    df = df.rename(columns={lat_col: 'lat', lon_col: 'lon'})
    if id_col:
        df = df.rename(columns={id_col: 'id'})
    if name_col:
        df = df.rename(columns={name_col: 'name'})
    return df


def load_rates(path):
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    # try to find cauldron id column
    cols = {c.lower(): c for c in df.columns}
    id_col = cols.get('cauldron_id') or cols.get('id')
    return df.rename(columns={id_col: 'id'}) if id_col else df


def load_levels(path):
    # returns latest level per cauldron (as percent if max volume known)
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    # expect a timestamp column and one column per cauldron id
    if 'timestamp' not in [c.lower() for c in df.columns]:
        # try exact 'timestamp'
        if 'timestamp' not in df.columns:
            return {}
    # normalize timestamp col name
    ts_col = None
    for c in df.columns:
        if c.lower() == 'timestamp':
            ts_col = c
            break
    if ts_col is None:
        return {}
    out = {}
    # take last non-null value for each cauldron column
    for col in df.columns:
        if col == ts_col:
            continue
        series = df[col].dropna()
        if series.empty:
            continue
        try:
            val = float(series.iloc[-1])
        except Exception:
            continue
        out[col] = val
    return out


st.title('Cauldron Map (local CSV data)')

cauldrons_df = load_cauldrons(CAULDRONS_CSV)
rates_df = load_rates(RATES_CSV)
levels_latest = load_levels(DATA_CSV)

if cauldrons_df.empty:
    st.warning(f'No cauldrons found at {CAULDRONS_CSV}. Make sure the CSV exists and has latitude/longitude columns.')
    st.stop()

# Merge rates (if present)
if not rates_df.empty and 'id' in rates_df.columns:
    cauldrons_df = cauldrons_df.merge(rates_df.set_index('id'), how='left', left_on='id', right_index=True).reset_index(drop=True)

# Add latest level (raw value) if available; convert to percent if max_volume exists
def compute_display_level(row):
    cid = row.get('id')
    if cid is None:
        return None
    raw = levels_latest.get(cid)
    if raw is None:
        return None
    max_v = row.get('max_volume')
    try:
        if pd.notna(max_v) and float(max_v) > 0:
            return round((float(raw) / float(max_v)) * 100.0, 2)
    except Exception:
        pass
    try:
        return round(float(raw), 2)
    except Exception:
        return None

cauldrons_df['display_level'] = cauldrons_df.apply(compute_display_level, axis=1)

# Build locations list and adjacent paths (by CSV order)
locations = []
paths = []
rows = cauldrons_df.to_dict(orient='records')
for r in rows:
    lat = r.get('lat')
    lon = r.get('lon')
    if pd.isna(lat) or pd.isna(lon):
        continue
    try:
        lat = float(lat)
        lon = float(lon)
    except Exception:
        continue
    if lat == 0 and lon == 0:
        continue
    locations.append({'id': r.get('id'), 'name': r.get('name'), 'lat': lat, 'lon': lon, 'level': r.get('display_level')})

for i in range(len(locations) - 1):
    a = locations[i]
    b = locations[i + 1]
    paths.append({'from': a['id'], 'to': b['id'], 'coords': [[a['lat'], a['lon']], [b['lat'], b['lon']]]})

st.write(f'Loaded {len(locations)} cauldron locations and {len(paths)} paths.')

show_paths = st.checkbox('Show paths', value=False)
marker_radius = st.slider('Marker radius', 0.1, 1.0, 0.1)

# Prepare pydeck layers
layers = []
if locations:
    # add a friendly level_display for tooltip (e.g. '42.5%' or 'N/A')
    for loc in locations:
        lvl = loc.get('level')
        loc['level_display'] = f"{lvl}%" if (lvl is not None) else 'N/A'
    df_loc = pd.DataFrame(locations)
    layers.append(pdk.Layer(
        'ScatterplotLayer',
        df_loc,
        get_position='[lon, lat]',
        get_fill_color='[22,163,74, 200]',
        get_radius=marker_radius * 100,
        radius_scale=1,
        pickable=True,
        tooltip=True,
    ))

if show_paths and paths:
    # build list of path objects - pydeck/Deck.gl expects [lon, lat] ordering for coordinates
    line_data = [{'path': [[c[1], c[0]] for c in p['coords']], 'color': [43,140,190]} for p in paths]
    # Use PathLayer which accepts an array of coordinates per feature via the `path` accessor
    layers.append(pdk.Layer(
        'PathLayer',
        line_data,
        get_path='path',
        get_color='color',
        width_scale=20,
        width_min_pixels=2,
    ))

# initial view state
if locations:
    first = locations[0]
    view_state = pdk.ViewState(latitude=first['lat'], longitude=first['lon'], zoom=15, pitch=0)
else:
    view_state = pdk.ViewState(latitude=37.76, longitude=-122.4, zoom=15, pitch=0)

tooltip = {
    'html': '<b>{name}</b><br/>ID: {id}<br/>Level: {level_display}',
    'style': {
        'backgroundColor': 'steelblue',
        'color': 'white'
    }
}

deck = pdk.Deck(layers=layers, initial_view_state=view_state, tooltip=tooltip)

st.pydeck_chart(deck)


## Ticket matching diagnostics (embedded)
st.markdown('---')
st.header('Ticket matching diagnostics (local CSV)')

TICKETS_CSV = BACKEND_DIR / 'tickets.csv'
DRAINS_CSV = BACKEND_DIR / 'drain_events.csv'


def load_tickets(path):
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    # parse date if present
    if any(c.lower() == 'date' for c in df.columns):
        for c in df.columns:
            if c.lower() == 'date':
                df[c] = pd.to_datetime(df[c], utc=True, errors='coerce')
                df = df.rename(columns={c: 'date'})
                break
    # ensure numeric amount column
    amt_col = None
    for c in df.columns:
        if c.lower() in ('amount_collected', 'amount'):
            amt_col = c
            break
    if amt_col:
        df = df.rename(columns={amt_col: 'amount_collected'})
        df['amount_collected'] = pd.to_numeric(df['amount_collected'], errors='coerce')
    return df


def load_drains(path):
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    # parse times
    for tcol in ('start_time', 'end_time'):
        for c in df.columns:
            if c.lower() == tcol:
                df[c] = pd.to_datetime(df[c], utc=True, errors='coerce')
    # numeric volume
    if any(c.lower() == 'volume_lost' for c in df.columns):
        for c in df.columns:
            if c.lower() == 'volume_lost':
                df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0.0)
    return df


def match_tickets_to_drains(tickets, drains, window_hours=24, outlier_frac=0.3):
    if tickets.empty:
        return pd.DataFrame()
    # median per cauldron for simple outlier detection
    med = tickets.groupby('cauldron_id')['amount_collected'].median()
    rows = []
    for i, t in tickets.reset_index().iterrows():
        cid = t.get('cauldron_id')
        tdate = t.get('date')
        amt = t.get('amount_collected')
        dup_count = 0
        status = 'needs-review'
        matched = pd.DataFrame()

        # duplicates (same cauldron, same date and amount)
        if pd.notna(tdate):
            same = tickets[(tickets['cauldron_id'] == cid) & (tickets['date'].dt.date == tdate.date()) & (tickets['amount_collected'] == amt)]
            dup_count = len(same)

        if pd.notna(tdate) and not drains.empty:
            start = tdate - pd.Timedelta(hours=window_hours)
            end = tdate + pd.Timedelta(hours=window_hours)
            cond = (
                (drains['cauldron_id'] == cid) & (
                    ((drains['start_time'] >= start) & (drains['start_time'] <= end)) |
                    ((drains['end_time'] >= start) & (drains['end_time'] <= end)) |
                    ((drains['start_time'] <= tdate) & (drains['end_time'] >= tdate))
                )
            )
            matched = drains.loc[cond].sort_values(by='start_time') if not drains.empty else pd.DataFrame()

        matched_significant = False
        matched_vol = 0.0
        if not matched.empty:
            if 'significant' in matched.columns:
                matched_significant = matched['significant'].astype(bool).any()
            if 'volume_lost' in matched.columns:
                matched_vol = float(matched['volume_lost'].sum())

        # outlier detection
        median = med.get(cid) if cid in med.index else None
        is_outlier = False
        if median is not None and pd.notna(amt):
            try:
                if abs(float(amt) - float(median)) / max(1e-6, float(median)) > outlier_frac:
                    is_outlier = True
            except Exception:
                is_outlier = False

        # heuristics for classification
        if matched_significant:
            status = 'valid'
        elif dup_count > 1:
            status = 'duplicate'
        elif is_outlier:
            status = 'outlier'
        elif matched.empty:
            status = 'suspicious'
        else:
            status = 'needs-review'

        rows.append({
            'ticket_index': t['index'] if 'index' in t else i,
            'cauldron_id': cid,
            'date': tdate,
            'amount_collected': amt,
            'dup_count': dup_count,
            'matched_events': len(matched),
            'matched_significant': bool(matched_significant),
            'matched_volume_sum': matched_vol,
            'median_amount': float(median) if median is not None and pd.notna(median) else None,
            'is_outlier': bool(is_outlier),
            'status': status,
            'matched_preview': matched[['start_time', 'end_time', 'volume_lost', 'significant']].to_dict('records') if not matched.empty else []
        })

    return pd.DataFrame(rows)


with st.expander('Ticket matching (diagnostics)', expanded=False):
    tickets = load_tickets(TICKETS_CSV)
    drains = load_drains(DRAINS_CSV)

    st.write(f'Loaded {len(tickets)} tickets and {len(drains)} drain events')

    w = st.number_input('Time window (hours) around ticket to match drains', value=24, min_value=1, max_value=168)
    outlier_frac = st.slider('Outlier fraction from median', min_value=0.05, max_value=1.0, value=0.3)

    if tickets.empty:
        st.info('No tickets.csv found or it is empty')
    else:
        results = match_tickets_to_drains(tickets, drains, window_hours=w, outlier_frac=outlier_frac)
        if results.empty:
            st.info('No ticket results')
        else:
            st.subheader('Status counts')
            st.write(results['status'].value_counts().to_dict())

            st.subheader('Suspicious / needs review')
            st.dataframe(results[results['status'].isin(['suspicious', 'outlier', 'needs-review', 'duplicate'])].sort_values('date', ascending=False))

            st.subheader('Valid tickets (sample)')
            st.dataframe(results[results['status'] == 'valid'].sort_values('date', ascending=False).head(50))

            st.subheader('Inspect ticket by index')
            ti = st.number_input('Ticket index to inspect', min_value=int(results['ticket_index'].min()), max_value=int(results['ticket_index'].max()), value=int(results['ticket_index'].min()))
            sel = results[results['ticket_index'] == ti]
            if not sel.empty:
                st.json(sel.iloc[0].to_dict())
                if sel.iloc[0]['matched_preview']:
                    st.table(pd.DataFrame(sel.iloc[0]['matched_preview']))

    ## Advanced analytics (charts & graphs)
    st.markdown('---')
    st.header('Advanced analytics')


    def build_daily_summary(cauldrons_df, cauldron_data_path, tickets_df, drains_df):
        """Build a daily summary table similar to the analysis notebook.
        Returns a DataFrame with end_of_day volume, ticket_volume, drain_volume and mismatch fields.
        """
        # load cauldron_data (wide format expected: timestamp + cauldron columns)
        if not Path(cauldron_data_path).exists():
            return pd.DataFrame()
        data = pd.read_csv(cauldron_data_path)
        # find timestamp column
        ts_col = None
        for c in data.columns:
            if c.lower() == 'timestamp':
                ts_col = c
                break
        if ts_col is None:
            return pd.DataFrame()
        data[ts_col] = pd.to_datetime(data[ts_col], utc=True, errors='coerce')
        data['date'] = data[ts_col].dt.date

        # melt to long form
        level_cols = [c for c in data.columns if c not in [ts_col, 'date']]
        if not level_cols:
            return pd.DataFrame()
        long = data.melt(id_vars=[ts_col, 'date'], value_vars=level_cols, var_name='cauldron_id', value_name='volume')

        # end-of-day last reading per cauldron
        end_volume = (
            long.sort_values(ts_col)
                .groupby(['cauldron_id', 'date'], as_index=False)
                .agg(end_volume=('volume', 'last'))
        )

        # tickets per day
        t = tickets_df.copy()
        if not t.empty and 'date' in t.columns:
            t['date'] = pd.to_datetime(t['date'], utc=True, errors='coerce').dt.date
        ticket_daily = (t.groupby(['cauldron_id', 'date'], as_index=False)['amount_collected'].sum().rename(columns={'amount_collected': 'ticket_volume'}) if not t.empty else pd.DataFrame())

        # drains per day (use start_time or end_time if present)
        d = drains_df.copy()
        if not d.empty:
            for col in d.columns:
                if col.lower() in ('start_time', 'end_time'):
                    d[col] = pd.to_datetime(d[col], utc=True, errors='coerce')
            # prefer end_time if present
            time_col = None
            for name in ('end_time', 'start_time'):
                for c in d.columns:
                    if c.lower() == name:
                        time_col = c
                        break
                if time_col:
                    break
            if time_col:
                d['date'] = d[time_col].dt.date
        drain_daily = (d.groupby(['cauldron_id', 'date'], as_index=False)['volume_lost'].sum().rename(columns={'volume_lost': 'drain_volume'}) if not d.empty and 'volume_lost' in d.columns else pd.DataFrame())

        # combine
        daily = end_volume
        if not ticket_daily.empty:
            daily = daily.merge(ticket_daily, on=['cauldron_id', 'date'], how='left')
        else:
            daily['ticket_volume'] = 0.0
        if not drain_daily.empty:
            daily = daily.merge(drain_daily, on=['cauldron_id', 'date'], how='left')
        else:
            daily['drain_volume'] = 0.0

        daily[['ticket_volume', 'drain_volume']] = daily[['ticket_volume', 'drain_volume']].fillna(0.0)

        # attach capacity if available
        use_cols = [c for c in ['id', 'max_volume'] if c in cauldrons_df.columns]
        if use_cols:
            caul_short = cauldrons_df.copy()
            if 'id' in caul_short.columns:
                caul_short = caul_short.rename(columns={'id': 'cauldron_id'})
            select_cols = ['cauldron_id' if c == 'id' else c for c in use_cols]
            select_cols = [c for c in select_cols if c in caul_short.columns]
            caul_short = caul_short[select_cols] if select_cols else pd.DataFrame()
            daily = daily.merge(caul_short, on='cauldron_id', how='left')
        if 'max_volume' in daily.columns:
            daily['fill_pct'] = (daily['end_volume'] / daily['max_volume']) * 100

        # mismatches
        daily['mismatch'] = daily['ticket_volume'] - daily['drain_volume']
        daily['mismatch_abs'] = daily['mismatch'].abs()
        daily['mismatch_pct'] = np.where(daily.get('max_volume', 0) > 0, (daily['mismatch_abs'] / daily['max_volume']) * 100, np.nan)

        return daily


    with st.expander('Show advanced charts', expanded=False):
        # reload tickets / drains here so advanced charts operate independently
        tickets_adv = load_tickets(TICKETS_CSV)
        drains_adv = load_drains(DRAINS_CSV)

        st.subheader('Current fill level by cauldron')
        # use display_level column we already computed
        fill_df = cauldrons_df[['name', 'display_level']].dropna().sort_values('display_level', ascending=False)
        if not fill_df.empty:
            # Use matplotlib to avoid pulling in Altair (streamlit.bar_chart imports Altair which may be incompatible
            # with some Python / Altair installations).
            names = list(fill_df['name'])
            values = list(fill_df['display_level'])
            fig, ax = plt.subplots(figsize=(10, 3))
            ax.bar(range(len(names)), values, color='darkgreen', edgecolor='orange')
            ax.set_ylabel('Display level')
            ax.set_xticks(range(len(names)))
            ax.set_xticklabels(names, rotation=90)
            ax.set_title('Current fill level by cauldron')
            plt.tight_layout()
            st.pyplot(fig)
        else:
            st.info('No fill level data available to show bar chart')

        st.subheader('Per-cauldron historic timeline')
        # load cauldron_data and allow selection
        if Path(DATA_CSV).exists():
            cd = pd.read_csv(DATA_CSV)
            # normalize timestamp
            ts = None
            for c in cd.columns:
                if c.lower() == 'timestamp':
                    ts = c
                    break
            if ts is not None:
                cd[ts] = pd.to_datetime(cd[ts], utc=True, errors='coerce')
                level_cols = [c for c in cd.columns if c not in [ts]]
                sel_id = st.selectbox('Select cauldron column (historic)', options=level_cols)
                if sel_id:
                    fig, ax = plt.subplots(figsize=(10, 3))
                    ax.plot(cd[ts], pd.to_numeric(cd[sel_id], errors='coerce'), label='level')
                    ax.set_title(f'Historic levels for {sel_id}')
                    ax.set_ylabel('Volume')
                    ax.grid(True)
                    st.pyplot(fig)
            else:
                st.info('cauldron_data.csv missing a timestamp column; cannot show timeline')
        else:
            st.info('No cauldron_data.csv found for historic timelines')

        st.subheader('Daily mismatch heatmap')
        daily = build_daily_summary(cauldrons_df, DATA_CSV, tickets_adv, drains_adv)
        if daily.empty:
            st.info('Not enough data to compute daily summary')
        else:
            # pivot by cauldron x date for mismatch_pct
            heat = daily.pivot(index='cauldron_id', columns='date', values='mismatch_pct').fillna(0)
            fig, ax = plt.subplots(figsize=(12, max(3, heat.shape[0] * 0.5)))
            im = ax.imshow(heat.values, aspect='auto', cmap='YlOrRd', origin='upper')
            ax.set_yticks(range(len(heat.index)))
            ax.set_yticklabels(heat.index)
            ax.set_xticks(range(len(heat.columns)))
            ax.set_xticklabels([d.strftime('%b %d') for d in heat.columns], rotation=90)
            ax.set_title('Daily Ticket vs Drain Mismatch (% of capacity)')
            fig.colorbar(im, ax=ax, label='Mismatch %')
            st.pyplot(fig)

        st.subheader('Daily summary table & KPIs')
        if not daily.empty:
            total_unaccounted = daily['mismatch_abs'].sum()
            total_days = len(daily)
            suspicious_days = int((daily['mismatch_abs'] > 0).sum())
            suspicious_rate = (suspicious_days / total_days * 100) if total_days else 0
            cols = ['cauldron_id', 'date', 'end_volume', 'max_volume', 'fill_pct', 'ticket_volume', 'drain_volume', 'mismatch']
            st.metric('Total unaccounted (L)', round(float(total_unaccounted), 2))
            st.metric('Suspicious day rate (%)', f"{round(suspicious_rate,1)}%")
            st.dataframe(daily[cols].sort_values(['cauldron_id', 'date'], ascending=[True, False]).head(200))
        else:
            st.info('No daily summary available')

