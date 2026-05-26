import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib

print("1. Loading dataset...")
df = pd.read_csv("phishing_datasets/final/result.csv")
df = df.drop(columns=["url"]).dropna()

X = df.drop(columns=["phishing"])
y = df["phishing"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print("2. Building the Neural Network (FLNN)...")
# MLP = Multi-Layer Perceptron.
# hidden_layer_sizes=(16, 8) means 2 hidden layers with 16 and 8 neurons.
nn_model = MLPClassifier(
    hidden_layer_sizes=(16, 8),
    activation="relu",
    solver="adam",
    max_iter=500,
    random_state=42,
)

print("3. Training the Neural Network...")
nn_model.fit(X_train, y_train)

print("4. Testing the Neural Network...")
y_pred = nn_model.predict(X_test)

accuracy = accuracy_score(y_test, y_pred)
print(f"\n🧠 Neural Network Accuracy Score: {accuracy * 100:.2f}%\n")
print(classification_report(y_test, y_pred))

print("5. Saving the Neural Network...")
joblib.dump(nn_model, "nn_model.pkl")
print("Saved as 'nn_model.pkl'. Phase 3 is complete!")
