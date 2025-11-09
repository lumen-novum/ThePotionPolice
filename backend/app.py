from flask import Flask, jsonify
from datetime import datetime
import csv
import os

app = Flask(__name__)

# Paths to the CSV files (assumed to live in the backend/ directory)
BASE_DIR = os.path.dirname(__file__)
CAULDRONS_CSV = os.path.join(BASE_DIR, 'cauldrons.csv')
DATA_CSV = os.path.join(BASE_DIR, 'cauldron_data.csv')
RATES_CSV = os.path.join(BASE_DIR, 'cauldron_rates.csv')


def _load_cauldrons_metadata():
    """Read `cauldrons.csv` and return a dict keyed by cauldron id with metadata.

    Expected columns: max_volume,id,name,latitude,longitude
    """
    meta = {}
    try:
        with open(CAULDRONS_CSV, newline='') as fh:
            reader = csv.DictReader(fh)
            for r in reader:
                cid = r.get('id')
                if not cid:
                    continue
                try:
                    max_vol = float(r.get('max_volume') or 0)
                except Exception:
                    max_vol = 0
                try:
                    lat = float(r.get('latitude') or 0)
                    lng = float(r.get('longitude') or 0)
                except Exception:
                    lat = lng = 0
                meta[cid] = {
                    'id': cid,
                    'name': r.get('name') or cid,
                    'lat': lat,
                    'lng': lng,
                    'max_volume': max_vol
                }
    except FileNotFoundError:
        pass
    return meta


def _load_rates():
    """Read `cauldron_rates.csv` as a map of id -> {fill_rate, drain_rate}"""
    rates = {}
    try:
        with open(RATES_CSV, newline='') as fh:
            reader = csv.DictReader(fh)
            for r in reader:
                cid = r.get('cauldron_id')
                if not cid:
                    continue
                try:
                    fill = float(r.get('fill_rate') or 0)
                except Exception:
                    fill = 0
                try:
                    drain = float(r.get('drain_rate') or 0)
                except Exception:
                    drain = 0
                rates[cid] = {'fill_rate': fill, 'drain_rate': drain}
    except FileNotFoundError:
        pass
    return rates


def _load_levels_by_cauldron(max_volumes):
    """Read `cauldron_data.csv` and return a dict {cauldron_id: [ {t: ms, level: percent}, ... ]}.

    `max_volumes` is a dict mapping id to max_volume for percent calculation. If missing, raw value is returned.
    """
    levels = {}
    try:
        with open(DATA_CSV, newline='') as fh:
            reader = csv.DictReader(fh)
            # header contains timestamp plus cauldron columns
            for row in reader:
                ts_str = row.get('timestamp')
                if not ts_str:
                    continue
                # parse timestamp (example: 2025-10-30 00:00:00+00:00)
                try:
                    dt = datetime.fromisoformat(ts_str)
                    t_ms = int(dt.timestamp() * 1000)
                except Exception:
                    # fallback: try to parse without offset
                    try:
                        dt = datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')
                        t_ms = int(dt.timestamp() * 1000)
                    except Exception:
                        continue

                for cid, raw in row.items():
                    if cid == 'timestamp':
                        continue
                    if raw is None or raw == '':
                        continue
                    try:
                        val = float(raw)
                    except Exception:
                        continue
                    max_v = max_volumes.get(cid) or None
                    if max_v:
                        percent = (val / max_v) * 100.0
                        lvl = round(percent, 2)
                    else:
                        lvl = round(val, 2)
                    levels.setdefault(cid, []).append({'t': t_ms, 'level': lvl})
    except FileNotFoundError:
        pass
    return levels


_CAULDRON_META = _load_cauldrons_metadata()
_CAULDRON_RATES = _load_rates()
_CAULDRON_LEVELS = _load_levels_by_cauldron({k: v.get('max_volume') for k, v in _CAULDRON_META.items()})


@app.route('/api/cauldrons')
def cauldrons():
    """Return a list of cauldron objects with metadata, rates, and time-series levels (level expressed as percent of max_volume when available)."""
    out = []
    for cid, meta in _CAULDRON_META.items():
        item = {
            'id': cid,
            'name': meta.get('name'),
            'lat': meta.get('lat'),
            'lng': meta.get('lng'),
            'max_volume': meta.get('max_volume'),
            'levels': _CAULDRON_LEVELS.get(cid, [])
        }
        if cid in _CAULDRON_RATES:
            item.update(_CAULDRON_RATES[cid])
        out.append(item)
    return jsonify(out)


@app.route('/api/network-map')
def network_map():
    # Build a network map that includes both locations and adjacent paths.
    # Response shape:
    # { "locations": [ {id,name,lat,lng}, ... ], "paths": [ {from,to,coordinates:[[lat,lng],...], color}, ... ] }
    cauldron_items = list(_CAULDRON_META.items())
    locations = []
    paths = []

    # Locations: include all cauldrons with their coordinates
    for cid, meta in cauldron_items:
        lat = meta.get('lat')
        lng = meta.get('lng')
        # skip if no coordinates (None) or both zero
        if lat is None or lng is None:
            continue
        if lat == 0 and lng == 0:
            continue
        locations.append({'id': cid, 'name': meta.get('name'), 'lat': lat, 'lng': lng})

    # Paths: connect adjacent cauldrons (A->B, B->C, ...), using the metadata order
    for i in range(len(cauldron_items) - 1):
        id_a, a_meta = cauldron_items[i]
        id_b, b_meta = cauldron_items[i + 1]
        a_lat = a_meta.get('lat')
        a_lng = a_meta.get('lng')
        b_lat = b_meta.get('lat')
        b_lng = b_meta.get('lng')
        # skip if coordinates are missing or invalid
        if a_lat is None or a_lng is None or b_lat is None or b_lng is None:
            continue
        if (a_lat == 0 and a_lng == 0) or (b_lat == 0 and b_lng == 0):
            continue
        coords = [[a_lat, a_lng], [b_lat, b_lng]]
        paths.append({'from': id_a, 'to': id_b, 'coordinates': coords, 'color': '#2b8cbe'})

    return jsonify({'locations': locations, 'paths': paths})


@app.route('/api/tickets')
def tickets():
    return jsonify([
        {"id": "t1", "summary": "Low potion level at North Cauldron", "status": "open", "created_at": "2025-11-09T08:00:00Z"},
        {"id": "t2", "summary": "Sensor offline at East Cauldron", "status": "investigating", "created_at": "2025-11-08T21:30:00Z"}
    ])
