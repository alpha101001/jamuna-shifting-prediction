import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_PATH = BASE_DIR / 'data' / 'processed' / 'jamuna_bankline_long.csv'
PLOT_DIR = BASE_DIR / 'notebooks' / 'plots'

# Ensure plot directory exists
PLOT_DIR.mkdir(parents=True, exist_ok=True)

def perform_eda():
    print("📊 Starting Exploratory Data Analysis...")

    # 1. Load Data
    df = pd.read_csv(DATA_PATH)
    print(f"   [+] Loaded {len(df)} data points.")

    # Set visual style
    sns.set_theme(style="whitegrid")

    # --- PLOT 1: River Migration Over Time (The "Spaghetti" Plot) ---
    # We want to see the general movement of the Left vs Right bank over 30 years.
    print("   [+] Generating Trend Analysis...")

    plt.figure(figsize=(12, 6))

    # We plot the Mean shift across all reaches for each year
    # aggregated by Bank
    sns.lineplot(data=df, x='Year', y='Shift', hue='Bank', marker='o')

    plt.title('Average Bankline Shift (1990-2025)', fontsize=16)
    plt.ylabel('Distance from Baseline (m)', fontsize=12)
    plt.xlabel('Year', fontsize=12)
    plt.axhline(0, color='black', linestyle='--', alpha=0.5) # The 1990 Baseline

    save_path = PLOT_DIR / '01_average_migration_trend.png'
    plt.savefig(save_path)
    plt.close()
    print(f"      Saved: {save_path}")

    # --- PLOT 2: Volatility Heatmap (Which Reach is dangerous?) ---
    # We pivot the data: Rows=Reach_ID, Cols=Year, Values=Shift
    # This creates a matrix we can visualize as a heatmap.
    print("   [+] Generating Volatility Heatmap...")

    # Filter for Left Bank only for clarity (Can change to Right)
    left_bank_df = df[df['Bank'] == 'Left']
    pivot_df = left_bank_df.pivot(index='Reach_ID', columns='Year', values='Shift')

    plt.figure(figsize=(14, 10))
    sns.heatmap(pivot_df, cmap="RdBu", center=0, cbar_kws={'label': 'Erosion/Accretion (m)'})

    plt.title('Left Bank Erosion Heatmap (Red=Erosion, Blue=Accretion)', fontsize=16)
    plt.ylabel('Reach ID (North to South)', fontsize=12)

    save_path = PLOT_DIR / '02_erosion_heatmap_left.png'
    plt.savefig(save_path)
    plt.close()
    print(f"      Saved: {save_path}")

    # --- PLOT 3: Distribution of Shifts (Bell Curve Check) ---
    # ML Models (like Linear Regression) assume errors are normally distributed.
    # We need to see if our data is Gaussian.
    print("   [+] Generating Distribution Check...")

    plt.figure(figsize=(10, 6))
    sns.histplot(data=df, x='Shift', hue='Bank', kde=True, bins=50)

    plt.title('Distribution of Bank Shifts', fontsize=16)
    plt.xlabel('Shift Distance (m)', fontsize=12)

    save_path = PLOT_DIR / '03_shift_distribution.png'
    plt.savefig(save_path)
    plt.close()
    print(f"      Saved: {save_path}")

    print("\n✅ EDA Complete. Open 'notebooks/plots/' to view results.")

if __name__ == "__main__":
    perform_eda()
