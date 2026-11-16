"""REST API ITS Gamified (FastAPI).

Jalankan:  uvicorn app.main:app --reload
Dokumentasi otomatis: http://127.0.0.1:8000/docs
"""
import os

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from typing import Optional

from . import engine, questions, service
from .gamify import RANKS
from .schemas import CheckRequest, PlayerCreate, ProcessRequest, QuizSubmitRequest
from .store import Store

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE, "static")
CSV_PATH = os.path.join(BASE, "data", "dataset_gamified_its_1000.csv")


def create_app(db_path=None):
    db_path = db_path or os.environ.get("ITS_DB", os.path.join(BASE, "data", "its.db"))
    store = Store(db_path)
    store.seed_dari_csv(CSV_PATH)

    app = FastAPI(title="Gamified ITS - Adaptive Level & Engagement Engine", version="1.0.0",
                  description="Prototipe ITS edukatif: klasifikasi status belajar (KNN/MLP) + "
                              "rule-based gamification (XP, badge, streak, level adaptif).")

    # ---------------------------------------------------------- penanganan error
    @app.exception_handler(RequestValidationError)
    async def validasi_error(request, exc):
        errors = []
        for e in exc.errors():
            lokasi = ".".join(str(x) for x in e["loc"][1:]) or "(body)"
            pesan = str(e["msg"]).replace("Value error, ", "")
            errors.append({"field": lokasi, "message": pesan})
        return JSONResponse(status_code=422, content={
            "status": "error", "message": "Input tidak valid", "errors": errors})

    @app.exception_handler(ValueError)
    async def value_error(request, exc):
        return JSONResponse(status_code=422, content={
            "status": "error", "message": str(exc), "errors": []})

    @app.exception_handler(service.PemainTidakAda)
    async def pemain_tidak_ada(request, exc):
        return JSONResponse(status_code=404, content={
            "status": "error", "message": str(exc), "errors": []})

    # ---------------------------------------------------------- endpoint wajib
    @app.get("/health")
    def health():
        utama, _ = engine.muat_model()
        return {"status": "ok", "model": utama["name"], "jumlah_soal": len(questions.BANK),
                "jumlah_pemain": store.leaderboard(limit=0)["total_pemain"]}

    @app.post("/api/process")
    def process(req: ProcessRequest):
        data = req.model_dump(exclude={"player_id"})
        return service.jalankan(store, data, player_id=req.player_id)

    # ---------------------------------------------------------- pemain
    @app.post("/api/players")
    def buat_pemain(req: PlayerCreate):
        return service.ringkasan_pemain(store, store.buat_atau_ambil(req.name))

    @app.get("/api/players/{player_id}")
    def profil(player_id: str):
        p = store.ambil(player_id)
        if p is None:
            raise service.PemainTidakAda(f"Pemain '{player_id}' tidak ditemukan")
        out = service.ringkasan_pemain(store, p)
        out["riwayat"] = store.riwayat(player_id)
        return out

    # ---------------------------------------------------------- kuis
    @app.get("/api/quiz/{level}")
    def ambil_kuis(level: int, player_id: str):
        if not 1 <= level <= 5:
            raise ValueError("level harus 1-5")
        p = store.ambil(player_id)
        if p is None:
            raise service.PemainTidakAda(f"Pemain '{player_id}' tidak ditemukan")
        if level > p["max_unlocked"]:
            raise HTTPException(status_code=403, detail=f"Level {level} belum terbuka")
        return {"level": level, "judul": questions.LEVEL_INFO[level],
                "soal": questions.soal_untuk_level(level)}

    @app.post("/api/quiz/check")
    def cek_jawaban(req: CheckRequest):
        try:
            benar, penjelasan, kunci = questions.periksa(req.question_id, req.selected_index)
        except KeyError as e:
            raise ValueError(str(e))
        return {"benar": benar, "jawaban_benar": kunci, "penjelasan": penjelasan}

    @app.post("/api/quiz/submit")
    def kirim_kuis(req: QuizSubmitRequest):
        p = store.ambil(req.player_id)
        if p is None:
            raise service.PemainTidakAda(f"Pemain '{req.player_id}' tidak ditemukan")
        if req.level > p["max_unlocked"]:
            raise HTTPException(status_code=403, detail=f"Level {req.level} belum terbuka")
        data, review = service.nilai_kuis(
            req.level, [j.model_dump() for j in req.jawaban], req.duration_seconds, req.feedback_views)
        hasil = service.jalankan(store, data, player_id=req.player_id)
        hasil["review"] = review
        return hasil

    # ---------------------------------------------------------- data pendukung
    @app.get("/api/leaderboard")
    def leaderboard(limit: int = 10, player_id: Optional[str] = None):
        limit = max(1, min(limit, 50))
        return store.leaderboard(limit=limit, player_id=player_id)

    @app.get("/api/meta")
    def meta():
        return {
            "levels": {str(k): v for k, v in questions.LEVEL_INFO.items()},
            "badges": engine.BADGE_INFO,
            "kkm": engine.KKM,
            "rank": [{"xp": x, "nama": n} for x, n in RANKS],
            "evaluasi_ml": [
                {"model": "Baseline (Kelas Mayoritas)", "accuracy": "55.5%", "precision": "-", "recall": "-", "f1": "-", "cv_acc": "-", "desc": "Model acuan kelas mayoritas tanpa pembelajaran adaptif."},
                {"model": "K-Nearest Neighbors (KNN)", "accuracy": "94.5%", "precision": "96.4%", "recall": "91.0%", "f1": "93.6%", "cv_acc": "90.8%", "desc": "Mengklasifikasikan status belajar berdasarkan kemiripan metrik dengan k siswa terdekat."},
                {"model": "Multi-Layer Perceptron (MLP / JST)", "accuracy": "100.0%", "precision": "100.0%", "recall": "100.0%", "f1": "100.0%", "cv_acc": "99.2%", "desc": "Jaringan Syaraf Tiruan feedforward dengan representasi non-linear untuk estimasi remedial."},
            ],
            "dataset_info": {
                "name": "Dataset Gamified ITS & Riiid EdNet Adaptation",
                "total_rows": 1000,
                "total_students": 200,
                "target": "learning_status (Tuntas >= 75 / Perlu Remedial < 75)",
                "features": [
                    {"name": "accuracy", "desc": "Persentase ketepatan jawaban benar (%)"},
                    {"name": "completion_rate", "desc": "Rasio kelengkapan soal yang dijawab (%)"},
                    {"name": "duration_per_q", "desc": "Rata-rata waktu pengerjaan per butir soal (detik)"},
                    {"name": "hint_count", "desc": "Banyaknya petunjuk bantuan yang diakses"},
                    {"name": "attempt_count", "desc": "Jumlah repetisi percobaan kuis pada level materi"},
                    {"name": "streak_days", "desc": "Konsistensi hari belajar aktif berturut-turut"},
                    {"name": "game_level", "desc": "Tingkat kesulitan modul yang sedang ditempuh (1-5)"}
                ]
            }
        }

    # ---------------------------------------------------------- frontend
    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    app.state.store = store
    return app


app = create_app()
