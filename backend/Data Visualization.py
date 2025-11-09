import sys
import pandas as pd

# /backend/Data Visualization.py
# Simple data visualization using pandas and matplotlib.
# If packages are missing, the script will instruct how to install them.


try:
    import matplotlib.pyplot as plt
except ImportError as e:
    missing = e.name if hasattr(e, "name") else str(e)
    print(f"Missing package: {missing}. Install with:\n    pip install pandas matplotlib")
    sys.exit(1)


def make_sample_df():
    # generate a small time series with two series
    dates = pd.date_range(end=pd.Timestamp.today(), periods=12, freq="M")
    df = pd.DataFrame({
        "date": dates,
        "sales_A": (100 + (pd.np.linspace(0, 30, 12)) + pd.np.random.randn(12) * 5).round(1),
        "sales_B": (80 + (pd.np.linspace(5, 40, 12)) + pd.np.random.randn(12) * 6).round(1),
    })
    df.set_index("date", inplace=True)
    return df


def plot_timeseries(df, out_path="timeseries.png"):
    ax = df.plot(title="Monthly Sales", figsize=(8, 4), marker="o")
    ax.set_ylabel("Sales")
    ax.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


def plot_monthly_bar(df, out_path="monthly_bar.png"):
    df_sum = df.resample("M").sum()
    ax = df_sum.plot(kind="bar", title="Monthly Sales (bar)", figsize=(8, 4))
    ax.set_ylabel("Sales")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


def main(csv_path=None):
    if csv_path:
        # try to read user CSV; expect a date column or index
        df = pd.read_csv(csv_path, parse_dates=True, index_col=0)
    else:
        df = make_sample_df()

    plot_timeseries(df, out_path="timeseries.png")
    plot_monthly_bar(df, out_path="monthly_bar.png")
    print("Saved: timeseries.png, monthly_bar.png")


if __name__ == "__main__":
    # optionally pass a CSV file path as the first argument
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    main(arg)