import os
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split


MODEL_PATH = os.environ.get('RISK_MODEL_PATH', './models/risk_model.joblib')




class RiskModel:
def __init__(self, model):
self.model = model


def predict_proba(self, payload: dict):
# payload is expected to contain numeric features; in real production, build feature pipeline
df = pd.DataFrame([payload])
if 'probability' in dir(self.model):
proba = self.model.predict_proba(df)[0, 1]
else:
proba = float(self.model.predict(df)[0])
return float(proba)


@staticmethod
def load_or_train():
# Try load
try:
m = joblib.load(MODEL_PATH)
return RiskModel(m)
except Exception:
# Train a dummy model on the sample labels in da
