# app.py
import os
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title("Historic Data Playback")

# -------------------------------
# 1️. Set paths to data folder
# -------------------------------
import os

BASE_DIR = os.path.dirname(__file__)  # points to streamlit_app
DATA_DIR = os.path.join(BASE_DIR, "data")  # look inside streamlit_app/data


potion_path = os.path.join(DATA_DIR, "cauldron_data.csv")
ticket_path = os.path.join(DATA_DIR, "tickets.csv")
cauldrons_path = os.path.join(DATA_DIR, "cauldrons.csv")
rates_path = os.path.join(DATA_DIR, "cauldron_rates.csv")

# -------------------------------
# 2. Load CSVs
# -------------------------------
potion_df = pd.read_csv(potion_path, parse_dates=["timestamp"])
ticket_df = pd.read_csv(ticket_path, parse_dates=["date"])
cauldrons_df = pd.read_csv(cauldrons_path)
rates_df = pd.read_csv(rates_path)

# -------------------------------
# 3️. Transform potion_df to long format
# -------------------------------
potion_long = potion_df.melt(id_vars=["timestamp"],
                             var_name="cauldron_id",
                             value_name="level")

# -------------------------------
# 4️. Merge with cauldrons info and rates
# -------------------------------
potion_long = potion_long.merge(cauldrons_df, left_on="cauldron_id", right_on="id", how="left")
potion_long = potion_long.merge(rates_df, on="cauldron_id", how="left")

ticket_long = ticket_df.copy()  # Assuming ticket_df already has cauldron_id

# -------------------------------
# 5️. Date selection
# -------------------------------
min_date = min(potion_long["timestamp"].min(), ticket_long["date"].min())
max_date = max(potion_long["timestamp"].max(), ticket_long["date"].max())
selected_date = st.date_input("Select Date", min_value=min_date, max_value=max_date, value=min_date)

# -------------------------------
# 6️. Cauldron selection
# -------------------------------
cauldrons = potion_long["cauldron_id"].unique()
selected_cauldrons = st.multiselect("Select Cauldrons", options=cauldrons, default=cauldrons)

# -------------------------------
# 7️. Filter data
# -------------------------------
filtered_potion = potion_long[(potion_long["cauldron_id"].isin(selected_cauldrons)) &
                              (potion_long["timestamp"].dt.date <= selected_date)]
filtered_ticket = ticket_long[(ticket_long["cauldron_id"].isin(selected_cauldrons)) &
                              (ticket_long["date"].dt.date <= selected_date)]

# -------------------------------
# 8️. Define cauldron colors & names
# -------------------------------
cauldron_colors = {
    "cauldron_001": "#E74C3C",
    "cauldron_002": "#3498DB",
    "cauldron_003": "#F1C40F",
    "cauldron_004": "#2ECC71",
    "cauldron_005": "#9B59B6",
    "cauldron_006": "#1ABC9C",
    "cauldron_007": "#C0392B",
    "cauldron_008": "#2980B9",
    "cauldron_009": "#F39C12",
    "cauldron_010": "#8E44AD",
    "cauldron_011": "#34495E",
    "cauldron_012": "#16A085"
}

cauldron_names = dict(zip(cauldrons_df["id"], cauldrons_df["name"]))

# -------------------------------
# 9️. Visualize Potion Levels
# -------------------------------
st.subheader("Potion Levels Over Time")
plt.figure(figsize=(10, 5))
for cauldron in selected_cauldrons:
    df = filtered_potion[filtered_potion["cauldron_id"] == cauldron]
    plt.plot(df["timestamp"], df["level"], 
             label=cauldron_names[cauldron], 
             color=cauldron_colors[cauldron])
plt.xlabel("Time")
plt.ylabel("Potion Level")
plt.legend()
st.pyplot(plt)

# -------------------------------
# 10. Visualize Tickets Collected
# -------------------------------
st.subheader("Tickets Collected Over Time")

# 1️⃣ Make ticket dates naive (remove timezone)
ticket_long["date"] = ticket_long["date"].dt.tz_localize(None)

# 2️⃣ Filter ticket data for selected cauldrons & date
filtered_ticket = ticket_long[
    (ticket_long["cauldron_id"].isin(selected_cauldrons)) &
    (ticket_long["date"].dt.date <= selected_date)
]

# 3️⃣ Aggregate by date and cauldron
ticket_sum = filtered_ticket.groupby(["date", "cauldron_id"])["amount_collected"].sum().reset_index()

# 4️⃣ Plot
plt.figure(figsize=(10, 5))
for cauldron in selected_cauldrons:
    df = ticket_sum[ticket_sum["cauldron_id"] == cauldron]
    plt.plot(df["date"], df["amount_collected"], 
             label=cauldron_names[cauldron], 
             color=cauldron_colors[cauldron])
plt.xlabel("Date")
plt.ylabel("Amount Collected")
plt.legend()
st.pyplot(plt)
