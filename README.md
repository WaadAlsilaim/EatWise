# EatWise
> **AI-powered food recognition app — personalized meal suggestions and real-time health alerts.**

EatWise is a mobile application that helps users make smarter, healthier food choices. Snap a photo of your groceries, and the app identifies the items, calculates calories, and delivers personalized meal recommendations tailored to your health goals and dietary needs — with real-time SFDA safety warnings.

---

## Features

- **Smart Food Recognition** — YOLOv8 + CLIP detect multiple items from a single photo
- **Calorie & Macro Tracking** — Protein, carbs, and fat breakdown per item
- **Personalized Meal Suggestions** — Recipes generated from your pantry based on your goal (weight loss / maintenance / muscle gain)
- **Activity Suggestions** — Movement recommendations paired with each meal
- **Allergy Alerts** — Flags dairy, gluten, nuts, shellfish, soy, and eggs
- **Health Condition Warnings** — Tailored alerts for blood pressure, diabetes, and more
- **SFDA Integration** — Real-time safety warnings from the Saudi Food and Drug Authority
- **Bilingual** — Full Arabic & English support

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Flutter |
| **Backend** | FastAPI + Uvicorn |
| **Database** | SQLite + SQLAlchemy ORM |
| **Authentication** | JWT + OTP |
| **Food Detection** | YOLOv8 |
| **Fallback Classification** | CLIP (OpenAI via `open-clip-torch`) |
| **API Docs** | Swagger UI |
| **Version Control** | GitHub |

---

## AI Models

### YOLOv8 — Primary Detection
Used for real-time food and product detection. Processes grocery images and identifies multiple items simultaneously with high speed and accuracy.

### CLIP (open-clip-torch) — Fallback Classification
A zero-shot classification model that activates when YOLOv8's confidence score falls below threshold. CLIP matches the image against text descriptions of food items to refine and correct uncertain predictions — no additional training data required.

---

## Project Structure

```
EatWise/
├── EatWise-Backend/        # FastAPI backend
│   ├── scripts/
│   │   └── init_db.py      # Database initialization script
│   ├── main.py
│   └── ...
├── android/                # Flutter Android build
├── ios/                    # Flutter iOS build
├── lib/                    # Flutter app source code
├── assets/images/          # App assets
├── test/                   # Unit tests
├── pubspec.yaml            # Flutter dependencies
└── README.md
```

---

## Getting Started

### Prerequisites

Make sure you have the following installed:

- [Flutter SDK](https://docs.flutter.dev/get-started/install) (v3.x or later)
- [Python](https://www.python.org/) 3.9+
- [pip](https://pip.pypa.io/en/stable/)
- [Git](https://git-scm.com/)

---

### 1. Clone the Repository

```bash
git clone https://github.com/WaadAlsilaim/EatWise.git
cd EatWise
```

---

### 2. Backend Setup (FastAPI)

```bash
cd EatWise-Backend
```

**Install Python dependencies:**

```bash
pip install -r requirements.txt
```

**Install CLIP:**

```bash
pip install open-clip-torch
```

**Initialize the database:**

```bash
python -m scripts.init_db
```

**Run the backend server:**

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`
Swagger docs at `http://localhost:8000/docs`

---

### 3. Frontend Setup (Flutter)

Navigate back to the root:

```bash
cd ..
```

**Install Flutter dependencies:**

```bash
flutter pub get
```

**Run on a connected device or emulator:**

```bash
flutter run
```

> **Note:** Make sure the backend URL in the Flutter app points to your local machine (e.g., `http://10.0.2.2:8000` for Android emulator).

---

## Database

EatWise uses **SQLite** as the primary database engine. The schema contains **22 relational tables** managing users, recipes, pantry items, nutrition data, health alerts, and saved meals.

To reset and re-initialize the database:

```bash
python -m scripts.init_db
```

---

## Security

- OTP-based phone authentication
- JWT token authorization
- AES-256 data encryption
- TLS in transit
- SFDA compliance checks

---

## License

This project was developed as a senior capstone project at Saudi Electronic University. All rights reserved © 2026 EatWise Team.
