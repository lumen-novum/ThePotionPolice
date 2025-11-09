import requests
import pandas as pd

url = "https://hackutd2025.eog.systems/api/Information/cauldrons"

response = requests.get(url)

print("Status code:", response.status_code)
print("Raw text response:")
print(response.text[:500])  # show first 500 characters to inspect

if response.status_code == 200:
    try:
        data = response.json()
        df = pd.DataFrame(data)
        df.to_csv("cauldrons.csv", index=False)
        print("Cauldron data fetched and saved to cauldrons.csv")
    except Exception as e:
        print("Could not parse JSON:", e)
else:
    print(f"Failed to fetch cauldron data (status {response.status_code})")
