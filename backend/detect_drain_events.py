import os
import pandas as pd

script_dir = os.path.dirname(__file__)
file_path = os.path.join(script_dir, "cauldron_data.csv")
df = pd.read_csv(file_path, parse_dates=["timestamp"])
df.set_index("timestamp", inplace=True)

DRAIN_DROP_THRESHOLD = 0.01  # catch all small drops
MIN_EVENT_GAP = 1  # minutes
ROLLING_WINDOW = 3

drain_events = []

for cauldron in df.columns:
    diff = df[cauldron].diff(ROLLING_WINDOW)
    drain_mask = diff < -DRAIN_DROP_THRESHOLD
    drain_times = df.index[drain_mask]

    if not drain_times.empty:
        current_event = [drain_times[0]]
        for t in drain_times[1:]:
            if (t - current_event[-1]).seconds / 60 > MIN_EVENT_GAP:
                event_start = current_event[0]
                event_end = current_event[-1]
                volume_change = df.loc[event_start, cauldron] - df.loc[event_end, cauldron]
                drain_events.append({
                    "cauldron_id": cauldron,
                    "start_time": event_start,
                    "end_time": event_end,
                    "volume_lost": abs(volume_change)
                })
                current_event = [t]
            else:
                current_event.append(t)
        # last event
        event_start = current_event[0]
        event_end = current_event[-1]
        volume_change = df.loc[event_start, cauldron] - df.loc[event_end, cauldron]
        drain_events.append({
            "cauldron_id": cauldron,
            "start_time": event_start,
            "end_time": event_end,
            "volume_lost": abs(volume_change)
        })

events_df = pd.DataFrame(drain_events)
events_df["significant"] = events_df["volume_lost"] >= 0.2
events_file = os.path.join(script_dir, "drain_events.csv")
events_df.to_csv(events_file, index=False)
print("Drain events detected and saved to drain_events.csv")
