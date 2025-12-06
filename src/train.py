import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_PATH = BASE_DIR / 'data' / 'processed' / 'jamuna_bankline_long.csv'
MODEL_PATH = BASE_DIR / 'models' / 'river_predictor_v1.pkl'

def train_model():
    print("🧠 Initializing Training Pipeline...")

    # 1. Load Data
    df = pd.read_csv(DATA_PATH)

    # 2. Feature Engineering
    # We need to convert categorical data ('Bank') into numbers.
    # We will use 'Reach_ID', 'Year', and 'Bank' to predict 'Shift'.

    X = df[['Reach_ID', 'Year', 'Bank']]
    y = df['Shift']

    print(f"   [+] Dataset Shape: {X.shape}")

    # 3. Split Data (80% Train, 20% Test)
    # CS Concept: We hide 20% of data from the model to simulate "Future Unknowns".
    # random_state=42 ensures reproducibility (the Answer to the Universe).
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 4. Define the Pipeline
    # CS Concept: A "Pipeline" chains preprocessing and model inference into one object.
    # This prevents "Training/Serving Skew" because the exact same transforms happen in production.

    preprocessor = ColumnTransformer(
        transformers=[
            # Encode 'Bank' (Left/Right) as [0, 1] or [1, 0]
            ('cat', OneHotEncoder(), ['Bank']),
            # 'Reach_ID' and 'Year' are passed through as-is
            ('num', 'passthrough', ['Reach_ID', 'Year'])
        ]
    )

    # The Model: Random Forest
    # n_estimators=100: Create 100 decision trees and average their vote.
    model = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('regressor', RandomForestRegressor(n_estimators=100, random_state=42))
    ])

    # 5. Train (Fit)
    print("   [+] Training Random Forest Model (this may take a moment)...")
    model.fit(X_train, y_train)

    # 6. Evaluation
    print("   [+] Evaluating Model Performance...")
    predictions = model.predict(X_test)

    # MAE: On average, how many meters are we off?
    mae = mean_absolute_error(y_test, predictions)
    # R2: How well do we explain the variance? (1.0 is perfect, 0.0 is random guessing)
    r2 = r2_score(y_test, predictions)

    print(f"\n📊 RESULTS:")
    print(f"   ---------------------------")
    print(f"   Mean Absolute Error (MAE): {mae:.2f} meters")
    print(f"   R² Score (Accuracy):       {r2:.4f}")
    print(f"   ---------------------------")

    # Interpret results
    if r2 > 0.7:
        print("   ✅ Grade: A (Excellent Model)")
    elif r2 > 0.5:
        print("   ⚠️ Grade: B (Good, but needs tuning)")
    else:
        print("   ❌ Grade: F (Model is failing, data might be too noisy)")

    # 7. Serialization (Save to Disk)
    # CS Concept: We 'pickle' the object effectively freezing its state to disk.
    joblib.dump(model, MODEL_PATH)
    print(f"\n💾 Model saved to: {MODEL_PATH}")

if __name__ == "__main__":
    train_model()
