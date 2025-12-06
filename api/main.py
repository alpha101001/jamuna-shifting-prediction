from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import pandas as pd
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware

# 1. Initialize the App
app = FastAPI(title="Jamuna River Prediction API", version="1.0")

# 2. Configure CORS (Crucial for Frontend)
# This allows your Next.js app (running on localhost:3000) to talk to this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with specific domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Load the Model (The "Brain")
# We load this ONCE when the server starts, not for every request.
BASE_DIR = Path(__file__).parent.parent
MODEL_PATH = BASE_DIR / 'models' / 'river_predictor_v1.pkl'

if not MODEL_PATH.exists():
    raise RuntimeError(f"❌ Model not found at {MODEL_PATH}. Did you run train.py?")

print("🧠 Loading Model into Memory...")
model = joblib.load(MODEL_PATH)
print("✅ Model Loaded!")

# 4. Define Data Schema (Pydantic)
# CS Analogy: Strong Typing / Struct Definition
class PredictionRequest(BaseModel):
    reach_id: int  # e.g., 1 to 50
    year: int      # e.g., 2025
    bank: str      # "Left" or "Right"

# 5. The Endpoint
@app.post("/predict")
def predict_shift(request: PredictionRequest):
    try:
        # Input Validation Logic
        if request.bank not in ["Left", "Right"]:
            raise HTTPException(status_code=400, detail="Bank must be 'Left' or 'Right'")

        # Convert JSON -> Pandas DataFrame (Model expects this format)
        input_data = pd.DataFrame([{
            'Reach_ID': request.reach_id,
            'Year': request.year,
            'Bank': request.bank
        }])

        # Run Inference
        prediction = model.predict(input_data)

        # Return JSON
        return {
            "reach_id": request.reach_id,
            "year": request.year,
            "bank": request.bank,
            "predicted_shift_meters": float(round(prediction[0], 2)),
            "status": "Erosion" if prediction[0] < 0 else "Accretion"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def health_check():
    return {"status": "active", "model": "RandomForest_v1"}
