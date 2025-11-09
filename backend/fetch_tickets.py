# fetch_tickets.py
import os
import pandas as pd
import requests

# API endpoint
TICKET_API = "https://hackutd2025.eog.systems/api/Tickets"

# Directory for saving CSV
script_dir = os.path.dirname(__file__)
output_file = os.path.join(script_dir, "../data/tickets.csv")

# Fetch tickets from API
response = requests.get(TICKET_API)
if response.status_code != 200:
    raise RuntimeError(f"Failed to fetch ticket data: {response.status_code}")

tickets_json = response.json()
tickets = pd.DataFrame(tickets_json.get("transport_tickets", []))

if tickets.empty:
    print("No tickets found in API data.")
else:
    # Convert ticket date to datetime (UTC)
    tickets["date"] = pd.to_datetime(tickets["date"], utc=True)

    # Keep only needed columns
    tickets = tickets[["cauldron_id", "date", "amount_collected"]]

    # Save to CSV
    tickets.to_csv(output_file, index=False)
    print(f"Tickets saved to {output_file}")
