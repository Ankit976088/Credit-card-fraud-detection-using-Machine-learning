
import argparse, os
from pathlib import Path
import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix

FEATURES = [
    "amount",            # transaction amount
    "hour",              # hour of day (0-23)
    "distance_from_home_km",
    "avg_amount_ratio",  # amount / customer's average amount
    "txn_last_24h",      # number of transactions in last 24 hours
    "is_online",         # 1 = card-not-present
    "is_foreign",        # 1 = transaction in a foreign country
    "used_pin_or_chip",  # 1 = chip/PIN verified
    "merchant_risk",     # 0 = low (grocery) .. 2 = high (jewellery, crypto, gift cards)
]

def generate_synthetic(n=60000, fraud_rate=0.03, seed=42):
    """Synthetic data that mimics typical fraud patterns (replace with real data in production)."""
    rng = np.random.default_rng(seed)
    y = rng.random(n) < fraud_rate
    f = ~y
    df = pd.DataFrame(index=range(n))
    df["amount"] = np.where(y, rng.lognormal(6.0, 1.0, n), rng.lognormal(3.8, 0.9, n)).round(2)
    df["hour"] = np.where(y, rng.choice([0,1,2,3,4,23,12,15,20], n), rng.choice(range(24), n,
                 p=np.array([1,1,1,1,1,2,4,6,8,8,8,8,8,8,8,8,8,8,8,7,5,3,2,1])/sum([1,1,1,1,1,2,4,6,8,8,8,8,8,8,8,8,8,8,8,7,5,3,2,1])))
    trav = rng.random(n) < 0.15            # genuine customers sometimes travel
    df["distance_from_home_km"] = np.where(y, np.where(rng.random(n) < 0.25, rng.exponential(15, n), rng.exponential(500, n)),
                                           np.where(trav, rng.exponential(500, n), rng.exponential(10, n))).round(1)
    df["avg_amount_ratio"] = np.where(y, rng.lognormal(1.0, 1.0, n), rng.lognormal(0.0, 0.7, n)).round(2)
    df["txn_last_24h"] = np.where(y, rng.poisson(4, n), rng.poisson(1.5, n))
    df["is_online"] = (rng.random(n) < np.where(y, 0.80, 0.35)).astype(int)
    df["is_foreign"] = (rng.random(n) < np.where(y, 0.35, 0.05)).astype(int)
    df["used_pin_or_chip"] = (rng.random(n) < np.where(y, 0.20, 0.60)).astype(int)
    df["merchant_risk"] = np.where(y, rng.choice([0,1,2], n, p=[.15,.30,.55]),
                                      rng.choice([0,1,2], n, p=[.65,.30,.05]))
    df["is_fraud"] = y.astype(int)
    return df

BASE = Path(__file__).resolve().parent

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(BASE / "data" / "transactions.csv"))
    args = ap.parse_args()

    if os.path.exists(args.data):
        df = pd.read_csv(args.data); print(f"Loaded {args.data}")
    else:
        os.makedirs(BASE / "data", exist_ok=True)
        df = generate_synthetic(); df.to_csv(args.data, index=False)
        print(f"No dataset found - generated synthetic data -> {args.data}")

    X, y = df[FEATURES], df["is_fraud"]
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

    # Fraud is rare, so weight fraud samples more heavily
    w = np.where(ytr == 1, (ytr == 0).sum() / (ytr == 1).sum() / 4, 1.0)
    model = GradientBoostingClassifier(n_estimators=200, max_depth=3, learning_rate=0.1, random_state=42)
    model.fit(Xtr, ytr, sample_weight=w)

    proba = model.predict_proba(Xte)[:, 1]
    pred = (proba >= 0.5).astype(int)
    print("\nROC-AUC:", round(roc_auc_score(yte, proba), 4))
    print("Confusion matrix [[TN FP],[FN TP]]:\n", confusion_matrix(yte, pred))
    print(classification_report(yte, pred, target_names=["Genuine", "Fraud"]))

    out = BASE / "model.joblib"
    joblib.dump({"model": model, "features": FEATURES}, out)
    print(f"Saved {out}")

if __name__ == "__main__":
    main()
