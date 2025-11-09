# verify_drain_tickets_local.py
import os
import pandas as pd

# --- 1. Load drain events ---
script_dir = os.path.dirname(__file__)
drain_file = os.path.join(script_dir, "drain_events.csv")
drains = pd.read_csv(drain_file, parse_dates=["start_time", "end_time"])

# Ensure drain events are tz-aware UTC
drains["start_time"] = pd.to_datetime(drains["start_time"], utc=True)
drains["end_time"] = pd.to_datetime(drains["end_time"], utc=True)

# --- 2. Load ticket CSV ---
ticket_file = os.path.join(script_dir, "tickets.csv")
tickets = pd.read_csv(ticket_file, parse_dates=["date"])

# Ensure tickets are tz-aware UTC
tickets["date"] = pd.to_datetime(tickets["date"], utc=True)

# --- 3. Compare drains with tickets per day ---
suspicious_events = []

# Group drains by cauldron and day
drains["day"] = drains["start_time"].dt.floor("D")
grouped_drains = drains.groupby(["cauldron_id", "day"])["volume_lost"].sum().reset_index()

for _, row in grouped_drains.iterrows():
    cauldron = row["cauldron_id"]
    day = row["day"]
    total_lost = row["volume_lost"]

    # Get ticket for that cauldron and day
    mask = (tickets["cauldron_id"] == cauldron) & (tickets["date"].dt.floor("D") == day)
    ticket_row = tickets[mask]

    collected = ticket_row["amount_collected"].sum() if not ticket_row.empty else 0

    # Flag as suspicious if total_lost and collected differ
    if abs(total_lost - collected) > 10:  # tolerance for floating point
        suspicious_events.append({
            "cauldron_id": cauldron,
            "day": day,
            "total_lost": total_lost,
            "collected": collected,
            "difference": collected - total_lost
        })

# --- 4. Save suspicious events ---
if suspicious_events:
    suspicious_df = pd.DataFrame(suspicious_events)
    output_file = os.path.join(script_dir, "suspicious_events.csv")
    suspicious_df.to_csv(output_file, index=False)
    print(f"Suspicious events saved to {output_file}")
else:
    print("No suspicious events detected.")
