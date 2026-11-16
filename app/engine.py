"""Mesin inti ITS Gamified: validasi, model ML, rule-based reasoning, XP, badge, level adaptif.

Modul ini TIDAK bergantung pada FastAPI sehingga bisa diuji langsung (tests/test_engine.py).
Aturan diturunkan dari dataset dan divalidasi di notebook (Langkah 4).
"""
import os
from functools import lru_cache

import joblib
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.environ.get("ITS_MODEL_DIR", os.path.join(BASE, "models"))

KKM = 75          # batas ketuntasan
MAX_LEVEL = 5
WAJIB = ["question_count", "answered_questions", "correct_answers", "duration_seconds",
         "hint_count", "attempt_count", "streak_days", "game_level", "feedback_frequency"]

UMPAN_BALIK = {
    "Naikkan level": "Hebat! Performa dan keterlibatanmu tinggi, level berikutnya sudah terbuka.",
    "Pertahankan level": "Progresmu bagus. Pertahankan ritme belajar dan jaga streak untuk naik level.",
    "Penguatan materi": "Kamu perlu penguatan materi. Pelajari ulang modul pada level di bawahnya sebelum lanjut.",
}

BADGE_INFO = {
    "Quiz Finisher": "Menyelesaikan sebuah kuis",
    "High Achiever": "Skor kuis 90 atau lebih",
    "Persistent Learner": "Mengerjakan kuis lebih dari sekali",
    "Learning Streak": "Belajar 3 hari berturut-turut",
    "Remedial Cleared": "Lulus kuis setelah sebelumnya perlu remedial",
}


# ----------------------------------------------------------------- model
@lru_cache(maxsize=1)
def muat_model():
    """Memuat model klasifikasi utama + regresi engagement dari file .joblib."""
    try:
        utama = joblib.load(os.path.join(MODEL_DIR, "model_utama.joblib"))
        eng = joblib.load(os.path.join(MODEL_DIR, "engagement_reg.joblib"))
    except Exception as e:  # file hilang atau versi scikit-learn berbeda
        raise RuntimeError("Gagal memuat model .joblib. Jalankan `python train_model.py` untuk "
                           f"melatih ulang model di lingkungan ini. Detail: {e}") from e
    return utama, eng


# ----------------------------------------------------------------- validasi
def validasi(data):
    """Lapisan validasi kedua (lapisan pertama: skema Pydantic). Melempar ValueError."""
    if not isinstance(data, dict):
        raise ValueError("Input harus berupa objek (dict/JSON)")
    hilang = [k for k in WAJIB if k not in data]
    if hilang:
        raise ValueError(f"Field wajib tidak ada: {hilang}")
    for k in WAJIB:
        v = data[k]
        if isinstance(v, bool) or not isinstance(v, (int, float)) or v != v:
            raise ValueError(f"Field '{k}' harus berupa angka, diterima: {v!r}")
        if v < 0:
            raise ValueError(f"Field '{k}' tidak boleh negatif")
    if data["question_count"] <= 0:
        raise ValueError("question_count harus > 0")
    if data["answered_questions"] > data["question_count"]:
        raise ValueError("answered_questions melebihi question_count")
    if data["correct_answers"] > data["answered_questions"]:
        raise ValueError("correct_answers melebihi answered_questions")
    if data["duration_seconds"] <= 0:
        raise ValueError("duration_seconds harus > 0")
    if not 1 <= data["game_level"] <= MAX_LEVEL:
        raise ValueError(f"game_level harus 1-{MAX_LEVEL}")


# ----------------------------------------------------------------- aturan
def status_rule(score):
    return "Tuntas" if score >= KKM else "Perlu Remedial"


def beri_badge(score, attempt_count, streak_days):
    b = ["Quiz Finisher"]
    if score >= 90:
        b.append("High Achiever")
    if attempt_count >= 2:
        b.append("Persistent Learner")
    if streak_days >= 3:
        b.append("Learning Streak")
    return b


def rekomendasi_adaptif(engagement, accuracy, status, game_level):
    if engagement >= 75 and accuracy >= 85:
        return "Naikkan level", min(game_level + 1, MAX_LEVEL)
    if status == "Perlu Remedial" and engagement < 65:
        return "Penguatan materi", max(game_level - 1, 1)
    return "Pertahankan level", game_level


def hitung_xp(score, accuracy, completion, streak_days, hint_count):
    r = {"skor": round(score * 0.20)}
    if accuracy >= 85:
        r["bonus_akurasi"] = 5
    if completion >= 100:
        r["bonus_selesai"] = 5
    if streak_days >= 2:
        r["bonus_streak"] = min(int(streak_days), 5) * 2
    if hint_count > 0:
        r["penalti_hint"] = -min(int(hint_count), 4)
    return max(sum(r.values()), 0), r


def estimasi_engagement(score, completion, streak, hint, feedback):
    _, eng = muat_model()
    x = pd.DataFrame([[score, completion, streak, hint, feedback]], columns=eng["features"])
    return float(min(max(eng["model"].predict(x)[0], 0), 100))


# ----------------------------------------------------------------- fungsi utama
def proses_kuis(data, total_xp_sebelumnya=0):
    """validasi -> metrik -> prediksi model -> aturan -> engagement -> XP -> badge -> level -> umpan balik."""
    validasi(data)
    utama, _ = muat_model()
    q, ans, ok = data["question_count"], data["answered_questions"], data["correct_answers"]
    score = round(ok / q * 100, 2)
    accuracy = round(ok / ans * 100, 2) if ans else 0.0
    completion = round(ans / q * 100, 2)

    fitur = pd.DataFrame([{
        "accuracy": accuracy, "completion_rate": completion,
        "duration_per_q": data["duration_seconds"] / q,
        "hint_count": data["hint_count"], "attempt_count": data["attempt_count"],
        "streak_days": data["streak_days"], "game_level": data["game_level"]}])[utama["features"]]
    p_remedial = float(utama["pipeline"].predict_proba(fitur)[0][1])

    status = status_rule(score)
    eng = estimasi_engagement(score, completion, data["streak_days"], data["hint_count"],
                              data["feedback_frequency"])
    rek, level_baru = rekomendasi_adaptif(eng, accuracy, status, int(data["game_level"]))
    xp, rincian = hitung_xp(score, accuracy, completion, data["streak_days"], data["hint_count"])
    badge = beri_badge(score, data["attempt_count"], data["streak_days"])

    return {
        "hasil_kuis": {"skor": score, "akurasi": accuracy, "kelengkapan": completion},
        "klasifikasi": {"model": utama["name"], "prob_perlu_remedial": round(p_remedial, 3),
                        "prediksi_model": "Perlu Remedial" if p_remedial >= 0.5 else "Tuntas",
                        "status_rule": status},
        "engagement_estimasi": round(eng, 1),
        "gamifikasi": {"xp_didapat": xp, "rincian_xp": rincian,
                       "total_xp": total_xp_sebelumnya + xp, "badge": badge,
                       "level_lama": int(data["game_level"]), "level_baru": level_baru},
        "umpan_balik": {"rekomendasi": rek, "pesan": UMPAN_BALIK[rek]},
    }
