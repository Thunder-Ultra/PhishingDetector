import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib

print("1. Loading the custom dataset...")
# Load the CSV you generated tonight
df = pd.read_csv("phishing_datasets/final/result.csv")

# 2. Clean the Data (AI hates text and blank spaces)
# Drop the actual 'url' string column because AI only understands numbers
df = df.drop(columns=["url"])

# If any row has a blank value (NaN), drop it
df = df.dropna()

# 3. Define X (Features) and y (Target/Label)
X = df.drop(columns=["phishing"])  # Everything EXCEPT the answer
y = df["phishing"]  # ONLY the answer (True/False)

print("2. Splitting data into 80% Training and 20% Testing...")
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print("3. Training the Random Forest AI...")
print("Training Features Order:", X_train.columns.tolist())
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

print("4. Testing the AI on unseen data...")
y_pred = model.predict(X_test)

# The Moment of Truth!
accuracy = accuracy_score(y_test, y_pred)
print(f"\n✅ AI Accuracy Score: {accuracy * 100:.2f}%\n")
print(classification_report(y_test, y_pred))

print("5. Saving the trained brain to a file...")
joblib.dump(model, "rf_model.pkl")
print("Saved as 'rf_model.pkl'. Phase 2 is complete!")
