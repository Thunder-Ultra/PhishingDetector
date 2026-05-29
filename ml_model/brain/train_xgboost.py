import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib
import matplotlib.pyplot as plt

print("1. Loading the V2 Massive Dataset...")
df = pd.read_csv("phishing_datasets/final/massive_dataset.csv")

print("2. Cleaning data...")
# Drop the URL string (AI only reads numbers)
if "url" in df.columns:
    df = df.drop(columns=["url"])

# Ensure all data is numeric, drop any weird rows
df = df.apply(pd.to_numeric, errors="coerce").dropna()

# 3. Define Features (X) and Target (y)
X = df.drop(columns=["phishing"])
y = df["phishing"]

feature_names = X.columns.tolist()
print(f"   -> Features being trained on: {feature_names}")

print("\n3. Splitting into 80% Training and 20% Testing...")
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print("\n4. Training the XGBoost AI (This might take a minute)...")
model = xgb.XGBClassifier(
    n_estimators=300,
    learning_rate=0.1,
    max_depth=6,
    random_state=42,
    eval_metric="logloss",
)

model.fit(X_train, y_train)

print("\n5. Testing the AI on unseen data...")
y_pred = model.predict(X_test)

# --- RESULTS ---
accuracy = accuracy_score(y_test, y_pred)
print("=" * 50)
print(f"🏆 XGBoost Accuracy Score: {accuracy * 100:.2f}%")
print("=" * 50)
print(classification_report(y_test, y_pred, target_names=["Safe (0)", "Phishing (1)"]))

# --- SAVE THE MODEL ---
print("\n6. Saving the trained model...")
joblib.dump(model, "xgboost_model.pkl")
print("✅ Saved as 'xgboost_model.pkl'. Phase 2 is complete!")
