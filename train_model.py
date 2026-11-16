"""Melatih model KNN & MLP + regresi engagement, lalu mengekspor ke .joblib.

Jalankan:  python train_model.py
Hasil   :  models/knn_status.joblib, models/mlp_status.joblib,
           models/engagement_reg.joblib, models/model_utama.joblib,
           models/hasil_evaluasi_model.csv
Logika sama dengan notebook ITS_Gamified_Colab.ipynb (Langkah 2-3).
"""
import os
import warnings

import joblib
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import GridSearchCV, GroupKFold, GroupShuffleSplit
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")
BASE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(BASE, "data", "dataset_gamified_its_1000.csv")
OUT = os.path.join(BASE, "models")

FITUR_A = ["accuracy", "completion_rate", "duration_per_q", "hint_count",
           "attempt_count", "streak_days", "game_level"]
FITUR_ENG = ["quiz_score", "completion_rate", "streak_days", "hint_count", "feedback_frequency"]
LABELS = ["Tuntas", "Perlu Remedial"]


def pipa(model):
    return Pipeline([("imputer", SimpleImputer(strategy="median")),
                     ("scaler", StandardScaler()),
                     ("model", model)])


def main():
    os.makedirs(OUT, exist_ok=True)
    df = pd.read_csv(CSV)
    df["duration_per_q"] = df["duration_seconds"] / df["question_count"]
    df["y"] = (df["learning_status"] == "Perlu Remedial").astype(int)

    # Split per siswa: tidak ada siswa yang sama di data latih & uji
    gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    idx_tr, idx_te = next(gss.split(df, df["y"], groups=df["student_id"]))
    tr, te = df.iloc[idx_tr], df.iloc[idx_te]
    gkf = GroupKFold(n_splits=5)

    knn = GridSearchCV(pipa(KNeighborsClassifier()),
                       {"model__n_neighbors": [3, 5, 7, 9, 11, 15],
                        "model__weights": ["uniform", "distance"]},
                       cv=gkf, scoring="accuracy")
    knn.fit(tr[FITUR_A], tr["y"], groups=tr["student_id"])
    mlp = GridSearchCV(pipa(MLPClassifier(max_iter=2000, random_state=42)),
                       {"model__hidden_layer_sizes": [(8,), (16, 8)],
                        "model__alpha": [1e-4, 1e-2]},
                       cv=gkf, scoring="accuracy")
    mlp.fit(tr[FITUR_A], tr["y"], groups=tr["student_id"])

    mayoritas = max(te["y"].mean(), 1 - te["y"].mean())
    rows = {"Baseline (kelas mayoritas)": {"Accuracy": mayoritas, "Precision": np.nan,
                                           "Recall": np.nan, "F1": np.nan, "CV acc (latih)": np.nan}}
    for nama, m in [("KNN", knn), ("MLP", mlp)]:
        p = m.predict(te[FITUR_A])
        rows[nama] = {"Accuracy": accuracy_score(te["y"], p),
                      "Precision": precision_score(te["y"], p),
                      "Recall": recall_score(te["y"], p),
                      "F1": f1_score(te["y"], p),
                      "CV acc (latih)": m.best_score_}
    hasil = pd.DataFrame(rows).T.round(3)
    hasil.to_csv(os.path.join(OUT, "hasil_evaluasi_model.csv"))
    print(hasil)
    print("Param terbaik KNN:", knn.best_params_)
    print("Param terbaik MLP:", mlp.best_params_)

    # Ekspor
    kandidat = {"KNN": knn, "MLP": mlp}
    nama_utama = max(kandidat, key=lambda k: kandidat[k].best_score_)  # dipilih dari CV, bukan data uji
    for nama, m in kandidat.items():
        joblib.dump({"pipeline": m.best_estimator_, "features": FITUR_A, "labels": LABELS, "name": nama},
                    os.path.join(OUT, f"{nama.lower()}_status.joblib"))
    joblib.dump({"pipeline": kandidat[nama_utama].best_estimator_, "features": FITUR_A,
                 "labels": LABELS, "name": nama_utama},
                os.path.join(OUT, "model_utama.joblib"))

    # Regresi estimasi engagement_score (tidak bisa dihitung langsung di aplikasi)
    dd = df.dropna(subset=FITUR_ENG)
    reg = LinearRegression().fit(dd[FITUR_ENG], dd["engagement_score"])
    print(f"Engagement R2 = {reg.score(dd[FITUR_ENG], dd['engagement_score']):.3f}",
          dict(zip(FITUR_ENG, reg.coef_.round(3))), "intercept", round(reg.intercept_, 2))
    joblib.dump({"model": reg, "features": FITUR_ENG}, os.path.join(OUT, "engagement_reg.joblib"))
    print("Model utama:", nama_utama, "-> tersimpan di", OUT)


if __name__ == "__main__":
    main()
