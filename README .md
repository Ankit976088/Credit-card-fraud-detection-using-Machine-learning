# Credit Card Fraud Detection Using ML

A machine-learning project that demonstrates how transaction-related information can be assessed to identify potentially fraudulent activity before payment completion.

## Project Overview

The project uses a **Gradient Boosting Classifier** to estimate whether a transaction may be fraudulent. The trained model is used by a web application prototype to support a pre-authorization fraud-checking workflow.

> **Note:** This is an academic prototype. Predictions should not be used to authorize real financial transactions without proper validation, security controls, and testing.

## Features

- Machine-learning-based transaction risk assessment
- Gradient Boosting Classifier
- Model training using a transaction dataset
- Web interface built with HTML, CSS, and JavaScript
- Python backend for application logic
- Prototype workflow for checking transactions before payment completion

## Technologies Used

- Python
- Pandas and NumPy
- Scikit-learn
- Joblib (if used by the current training script)
- Flask (if used by the current backend)
- HTML, CSS, and JavaScript

## Repository Structure

The files currently uploaded to this GitHub repository are arranged at the repository root:

```text
Credit-card-fraud-detection-using-Machine-learning/
├── .gitignore
├── app.py
├── fraud_model.pkl
├── index.html
├── script.js
├── style.css
├── train_model.py
└── transactions.csv
```

## Setup and Run

Run these commands from the project root directory.

### 1. Clone the repository

```bash
git clone https://github.com/Ankit976088/Credit-card-fraud-detection-using-Machine-learning.git
cd Credit-card-fraud-detection-using-Machine-learning
```

### 2. Install dependencies

```bash
pip install pandas numpy scikit-learn joblib flask
```

Install only the packages required by your current code if your environment uses a different dependency list.

### 3. Train the model

```bash
python train_model.py
```

This reads the dataset configured in `train_model.py`, trains the Gradient Boosting Classifier, and saves the trained model to the output path configured in that script.

### 4. Start the backend

In the GitHub repository's current root-level layout, run:

```bash
python app.py
```

If your local project has the backend file inside a `backend` folder instead, use `python backend/app.py` from the project root.

### 5. Open the application

Open the local URL printed in the terminal. If the Flask application uses its default local address, it is commonly:

```text
http://127.0.0.1:5000
```

## How It Works

1. The training script loads the configured transaction dataset.
2. The script prepares the features and target label as implemented in the code.
3. A Gradient Boosting Classifier is trained and saved.
4. The backend loads the trained model and evaluates transaction-related features.
5. The application displays the prediction or risk result produced by the implemented workflow.

The exact input features, model output path, and prediction thresholds are defined by `train_model.py` and `app.py`.

## Dataset and Model

- `transactions.csv` — transaction dataset used by the project, subject to the path configured in the training script.
- `fraud_model.pkl` — saved model file currently listed in the repository. Confirm that its filename and format match the model output expected by `app.py` after training.

## Author

**Ankit Kumar**  
BCA — Artificial Intelligence and Data Science  
Graphic Era Hill University, Dehradun, Uttarakhand, India
