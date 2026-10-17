"""
Pre-authorization fraud check.  Run:  python app.py   ->  http://127.0.0.1:5000

Flow:  user clicks PAY  ->  system builds features automatically (current time, customer
history, location distance, ...)  ->  ML model scores the transaction BEFORE it is completed
->  GENUINE: completed | SUSPICIOUS: held until OTP | FRAUDULENT: declined (never completed).
The user never selects "Fraud" or "Genuine".
"""
import math, time, uuid
from pathlib import Path
from datetime import datetime
import joblib, pandas as pd
from flask import Flask, request, jsonify, render_template

BASE = Path(__file__).resolve().parent

def find_frontend():
    """Find the folder that contains templates/index.html (works for flat or backend/frontend layouts)."""
    for folder in (BASE, BASE.parent / "frontend", BASE.parent, BASE / "frontend"):
        if (folder / "templates" / "index.html").exists():
            return folder
    raise FileNotFoundError("templates/index.html not found - put the templates/ and static/ folders "
                            "next to app.py or inside a 'frontend' folder beside 'backend'.")

def load_model():
    """Load model.joblib from backend/ (or its parent). If it does not exist yet, train it once."""
    for folder in (BASE, BASE.parent, BASE / "model"):
        if (folder / "model.joblib").exists():
            return joblib.load(folder / "model.joblib")
    print("model.joblib not found - training the model now (one-time, ~30 seconds)...")
    import subprocess, sys
    subprocess.run([sys.executable, str(BASE / "train_model.py")], check=True)
    return joblib.load(BASE / "model.joblib")

FRONTEND = find_frontend()
bundle = load_model()
model, FEATURES = bundle["model"], bundle["features"]
app = Flask(__name__, template_folder=FRONTEND / "templates", static_folder=FRONTEND / "static")

REVIEW, BLOCK = 0.35, 0.70
DEMO_OTP = "123456"

# ---- Simulated databases (replace with a real DB in production) -------------------------
CITIES = {  # name: (lat, lon, country)
    "Dehradun": (30.32, 78.03, "IN"), "Delhi": (28.61, 77.21, "IN"), "Mumbai": (19.08, 72.88, "IN"),
    "Bengaluru": (12.97, 77.59, "IN"), "Dubai": (25.20, 55.27, "AE"), "London": (51.51, -0.13, "GB"),
    "Lagos": (6.52, 3.38, "NG"),
}
CUSTOMERS = {
    "C1001": {"name": "Aarav (home: Dehradun)", "home": "Dehradun", "avg_amount": 1800},
    "C1002": {"name": "Meera (home: Mumbai)", "home": "Mumbai", "avg_amount": 4500},
}
LEDGER = []   # every attempted transaction and its final status

def km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2-la1)/2)**2 + math.cos(la1)*math.cos(la2)*math.sin((lo2-lo1)/2)**2
    return 6371 * 2 * math.asin(math.sqrt(h))

def build_features(t):
    """Turn a raw payment request into the model's features - fully automatic."""
    cust = CUSTOMERS[t["customer_id"]]
    home, here = CITIES[cust["home"]], CITIES[t["city"]]
    now = time.time()
    recent = [x for x in LEDGER if x["customer_id"] == t["customer_id"]
              and x["status"] == "COMPLETED" and now - x["ts"] < 86400]
    amount = float(t["amount"])
    return {
        "amount": amount,
        "hour": datetime.now().hour,
        "distance_from_home_km": km(home, here),
        "avg_amount_ratio": amount / cust["avg_amount"],
        "txn_last_24h": len(recent),
        "is_online": int(t["channel"] == "online"),
        "is_foreign": int(here[2] != home[2]),
        "used_pin_or_chip": int(t["channel"] == "chip"),
        "merchant_risk": int(t["merchant_risk"]),
    }

def score(feats):
    row = pd.DataFrame([[feats[f] for f in FEATURES]], columns=FEATURES)
    return float(model.predict_proba(row)[0, 1])

# ---- API ----------------------------------------------------------------------------------
@app.post("/pay")
def pay():
    """Pre-authorization: the transaction is scored first; it completes only if allowed."""
    t = request.get_json(force=True)
    try:
        if t["customer_id"] not in CUSTOMERS or t["city"] not in CITIES: raise ValueError("unknown customer/city")
        if float(t["amount"]) <= 0: raise ValueError("amount must be positive")
        feats = build_features(t)
    except (KeyError, ValueError, TypeError) as e:
        return jsonify(error=f"Invalid transaction: {e}"), 400

    p = score(feats)
    if p >= BLOCK:    status, label = "DECLINED", "FRAUDULENT"
    elif p >= REVIEW: status, label = "PENDING_OTP", "SUSPICIOUS"
    else:             status, label = "COMPLETED", "GENUINE"
    rec = {"id": uuid.uuid4().hex[:8], "ts": time.time(), "customer_id": t["customer_id"],
           "amount": float(t["amount"]), "city": t["city"], "status": status,
           "label": label, "probability": round(p*100, 1)}
    LEDGER.append(rec)
    return jsonify(**rec, features={k: round(v, 2) for k, v in feats.items()})

@app.post("/verify_otp")
def verify_otp():
    d = request.get_json(force=True)
    rec = next((x for x in LEDGER if x["id"] == d.get("id")), None)
    if not rec or rec["status"] != "PENDING_OTP": return jsonify(error="No pending transaction"), 400
    rec["status"] = "COMPLETED" if d.get("otp") == DEMO_OTP else "DECLINED"
    return jsonify(id=rec["id"], status=rec["status"])

@app.get("/ledger")
def ledger(): return jsonify(LEDGER[-10:][::-1])


@app.get("/")
def home(): return render_template("index.html", customers=CUSTOMERS, cities=CITIES)

if __name__ == "__main__":
    app.run(debug=True)
