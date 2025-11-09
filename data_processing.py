import pandas as pd

# 1. Load minute-level cauldron data
df = pd.read_csv("cauldron_levels.csv", index_col='timestamp', parse_dates=True)

# 2. Prepare a dictionary to store rates
rates = {}

# 3. Loop through all cauldrons
for cauldron in df.columns:
    df['diff'] = df[cauldron].diff()
    fill_rate = df[df['diff'] > 0]['diff'].mean()
    drain_rate = abs(df[df['diff'] < 0]['diff'].mean())
    rates[cauldron] = {
        'fill_rate': fill_rate,
        'drain_rate': drain_rate
    }

# 4. Convert to DataFrame
rates_df = pd.DataFrame(rates).T
rates_df.index.name = 'cauldron_id'

# 5. Save to a separate CSV
rates_df.to_csv("cauldron_rates_summary.csv")

print("Fill/Drain rates calculated and saved!")
print(rates_df)
