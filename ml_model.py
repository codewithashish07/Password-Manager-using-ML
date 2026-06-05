import re
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib
import os

MODEL_FILE = "strength_model.pkl"

def extract_features(password: str) -> list:
    length = len(password)
    has_upper = int(bool(re.search(r'[A-Z]', password)))
    has_lower = int(bool(re.search(r'[a-z]', password)))
    has_digit = int(bool(re.search(r'\d', password)))
    has_special = int(bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password)))
    unique_chars = len(set(password))
    digit_count = len(re.findall(r'\d', password))
    special_count = len(re.findall(r'[!@#$%^&*]', password))
    sequential = int(any(password[i:i+3].lower() in
                    "abcdefghijklmnopqrstuvwxyz0123456789"
                    for i in range(len(password)-2)))
    repeated = int(any(password[i] == password[i+1] == password[i+2]
                   for i in range(len(password)-2)))
    return [length, has_upper, has_lower, has_digit, has_special,
            unique_chars, digit_count, special_count, sequential, repeated]

def get_training_data():
    samples = [
        ("123456", 0), ("password", 0), ("abc", 0), ("qwerty", 0),
        ("111111", 0), ("iloveyou", 0), ("admin", 0), ("letmein", 0),
        ("Pass1234", 1), ("Hello@123", 1), ("Summer2023", 1),
        ("MyPass#1", 1), ("Company12!", 1), ("Tiger2024$", 1),
        ("Ashish@123", 1), ("India2024!", 1),
        ("X!9kL#mP2@qW", 2), ("Tr0ub4dor&3", 2), ("correcthorsebattery", 2),
        ("P@$$w0rd!2024Secure", 2), ("Zx!9Lm@3Kq#7Np", 2),
        ("Vy$8Nm!2Pk#5Lz", 2), ("&R4kM!nX9@Lw2Pz", 2),
    ]
    X = [extract_features(pw) for pw, _ in samples]
    y = [label for _, label in samples]
    return np.array(X), np.array(y)

def train_model():
    X, y = get_training_data()
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)
    joblib.dump(model, MODEL_FILE)
    print("✅ ML model trained and saved.")
    return model

def load_model():
    if os.path.exists(MODEL_FILE):
        return joblib.load(MODEL_FILE)
    return train_model()

def predict_strength(password: str) -> dict:
    model = load_model()
    features = np.array([extract_features(password)])
    prediction = model.predict(features)[0]
    proba = model.predict_proba(features)[0]
    labels = {0: "Weak 🔴", 1: "Medium 🟡", 2: "Strong 🟢"}
    return {
        "label": labels[prediction],
        "score": round(float(max(proba)), 2),
        "raw": int(prediction)
    }
