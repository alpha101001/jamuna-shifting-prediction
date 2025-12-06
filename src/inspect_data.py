import pandas as pd
import re
from pathlib import Path

# Define Paths
BASE_DIR = Path(__file__).parent.parent
RAW_PATH = BASE_DIR / 'data' / 'raw' / 'bankline_data.xlsx'
PROCESSED_PATH = BASE_DIR / 'data' / 'processed' / 'jamuna_bankline_long.csv'

def clean_and_reshape():
    print("🧹 Starting Data Preprocessing Pipeline...")

    # 1. Load Data
    # header=[0, 1] reads the first two rows as a MultiIndex
    try:
        df = pd.read_excel(RAW_PATH, sheet_name='Data', header=[0, 1])
    except ValueError as e:
        print(f"❌ Error loading Excel: {e}")
        return

    print(f"   [+] Raw shape: {df.shape}")

    # 2. Extract and Clean Headers
    # We iterate through the columns to build a clean list of names.
    new_columns = []

    # df.columns is a list of tuples: [('Reaches', 'Reaches'), ('Point', 'Left Bank'), ...]
    for col_idx, col_tuple in enumerate(df.columns):
        level0 = str(col_tuple[0]) # Top Header (e.g., "Distance(1991)")
        level1 = str(col_tuple[1]) # Sub Header (e.g., "Left Bank (m)")

        # Logic to rename columns
        if "Reaches" in level0 or "Reaches" in level1:
            new_columns.append("Reach_ID")

        elif "Point" in level0:
            # Columns B and C in your screenshot
            if "Left" in level1:
                new_columns.append("Baseline_Point_Left")
            elif "Right" in level1:
                new_columns.append("Baseline_Point_Right")
            else:
                new_columns.append(f"Point_{col_idx}") # Fallback

        elif "Distance" in level0:
            # Extract Year: "Distance(1991)" -> "1991"
            year_match = re.search(r'(\d{4})', level0)
            if year_match:
                year = year_match.group(1)

                # Determine Bank Side
                if "Left" in level1:
                    new_columns.append(f"{year}_Left")
                elif "Right" in level1:
                    new_columns.append(f"{year}_Right")
                else:
                    new_columns.append(f"{year}_Unknown")
            else:
                # If "Distance" exists but no year (unlikely), drop or label
                new_columns.append(f"Unknown_Distance_{col_idx}")

        elif "Unnamed" in level0:
            # Handle cases where the merge is weird, but usually Level 1 has info
            if "Left" in level1:
                 # This handles if 'Distance(1991)' didn't propagate in the pandas read
                 # We might need a smarter look-back, but usually pandas ffill isn't automatic on read
                 # For now, let's mark it.
                 new_columns.append(f"CheckMe_{col_idx}")
            else:
                 new_columns.append(f"DropMe_{col_idx}")
        else:
            new_columns.append(f"Extra_{col_idx}")

    # 3. Handle the "Merged Header Issue" (Pandas sometimes sees NaNs in Level 0)
    # If the Excel merge wasn't read perfectly, we might have 'nan' for the second column of a year.
    # We fix this by iterating and carrying forward the Year.
    final_columns = []
    current_year = None

    for i, col_name in enumerate(new_columns):
        # If we detected a year, remember it
        if re.match(r'\d{4}_(Left|Right)', col_name):
            current_year = col_name.split('_')[0]
            final_columns.append(col_name)
        elif "CheckMe" in col_name and current_year:
            # If we are in a 'CheckMe' column (Level 0 was NaN), assume same year as previous
            if "Left" in df.columns[i][1]:
                final_columns.append(f"{current_year}_Left")
            elif "Right" in df.columns[i][1]:
                final_columns.append(f"{current_year}_Right")
        elif "DropMe" in col_name:
             final_columns.append(f"Drop_{i}")
        else:
            # Reset year if we hit a non-year column
            if "Reach" in col_name or "Baseline" in col_name:
                pass
            else:
                # If it's a new distance block but our regex failed earlier
                pass
            final_columns.append(col_name)

    # Apply new column names
    df.columns = final_columns

    # 4. Melt to Long Format
    # ID Variables: Things that don't change over time
    id_vars = ['Reach_ID', 'Baseline_Point_Left', 'Baseline_Point_Right']

    # Value Variables: The Years (e.g., '1991_Left', '1991_Right'...)
    # Filter columns that start with a digit
    value_vars = [c for c in df.columns if c[0].isdigit()]

    print(f"   [+] Identification Cols: {id_vars}")
    print(f"   [+] Time-Series Cols (Count): {len(value_vars)}")

    df_long = df.melt(id_vars=id_vars, value_vars=value_vars, var_name='Year_Bank', value_name='Shift')

    # 5. Feature Extraction
    # Split '1991_Left' into '1991' and 'Left'
    df_long[['Year', 'Bank']] = df_long['Year_Bank'].str.split('_', expand=True)

    # Type Conversion
    df_long['Year'] = pd.to_numeric(df_long['Year'])
    df_long['Shift'] = pd.to_numeric(df_long['Shift'], errors='coerce') # Force non-numbers to NaN

    # 6. Structuring
    # We don't need 'Year_Bank' anymore
    df_long = df_long.drop(columns=['Year_Bank'])

    # Sort for Time Series (Reach 1: 1991, 1993, 1995...)
    df_long = df_long.sort_values(by=['Reach_ID', 'Bank', 'Year'])

    # 7. Clean NAs
    # Remove rows where the Shift is empty (maybe future years in sheet with no data yet)
    before_drop = len(df_long)
    df_long = df_long.dropna(subset=['Shift'])
    print(f"   [+] Dropped {before_drop - len(df_long)} rows with missing shift data.")

    # 8. Save
    PROCESSED_PATH.parent.mkdir(parents=True, exist_ok=True)
    df_long.to_csv(PROCESSED_PATH, index=False)

    print("\n✅ PREPROCESSING COMPLETE")
    print(f"   Saved to: {PROCESSED_PATH}")
    print("\n📊 Sample Data (First 5 Rows):")
    print(df_long[['Reach_ID', 'Year', 'Bank', 'Shift']].head(5))

if __name__ == "__main__":
    clean_and_reshape()
