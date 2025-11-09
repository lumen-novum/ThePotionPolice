import requests
import pandas as pd

# 1. Call the API to fetch cauldron level data
url = "https://hackutd2025.eog.systems/api/Data/?start_date=0&end_date=2000000000"
response = requests.get(url)
print("Status Code:", response.status_code)  # Check if the API request was successful

data = response.json()  # Parse the JSON response

# 2. Convert JSON into a pandas DataFrame
df = pd.DataFrame([
    {'timestamp': item['timestamp'], **item['cauldron_levels']} for item in data
])

# 3. Convert timestamp to datetime format and sort the DataFrame by timestamp
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.set_index('timestamp').sort_index()

# 4. Check a sample of the data
print(df.head())

# 5. Save the full dataset to a CSV file for later analysis
df.to_csv("cauldron_data.csv")
