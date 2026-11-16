# Gamified ITS: Adaptive Level & Engagement Engine

Tugas Besar Praktikum Intelligent Tutor System (S1 Sistem Informasi, Universitas Bengkulu).
Rule-Based Reasoning + Klasifikasi Status Pembelajar (KNN / MLP) + gamifikasi (XP, badge, streak, level adaptif, leaderboard).

## Menjalankan
```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python train_model.py                  # melatih ulang model -> folder models/ (disarankan, agar cocok dengan versi scikit-learn-mu)
uvicorn app.main:app --reload          # buka http://127.0.0.1:8000  (dokumentasi API: /docs)
```
Database `data/its.db` dibuat otomatis dan diisi 200 siswa dari dataset (untuk leaderboard).

## Pengujian
```bash
python -m unittest discover tests -v   # engine + layanan (37 tes) + API (15 tes, jika fastapi/httpx terpasang)
```

## Struktur
| Path | Isi |
|---|---|
| `train_model.py` | Preprocessing, GridSearch KNN & MLP (split per siswa), regresi engagement, ekspor `.joblib` |
| `app/engine.py` | Validasi, prediksi model, aturan status/badge/XP/level adaptif, `proses_kuis()` |
| `app/service.py` | Alur stateful: streak harian, level unlock, badge *Remedial Cleared*, penilaian kuis |
| `app/store.py`, `gamify.py` | SQLite (profil, riwayat, leaderboard), rank XP & streak |
| `app/questions.py` | Bank soal 5 level x 8 soal |
| `app/schemas.py`, `main.py` | Skema Pydantic + REST API FastAPI |
| `static/` | Frontend HTML5/CSS3/JS (Fetch API, tanpa reload) |

## Endpoint
| Method | Path | Fungsi |
|---|---|---|
| GET | `/health` | Status layanan & model |
| POST | `/api/process` | Memproses metrik kuis (stateless; dengan `player_id` profil ikut diperbarui) |
| POST | `/api/players` | Masuk/buat pemain |
| GET | `/api/players/{id}` | Profil + riwayat |
| GET | `/api/quiz/{level}?player_id=` | Ambil 6 soal (tanpa kunci jawaban); level terkunci -> 403 |
| POST | `/api/quiz/check` | Umpan balik instan per soal |
| POST | `/api/quiz/submit` | Penilaian server + XP/badge/level adaptif |
| GET | `/api/leaderboard` | Papan peringkat |

Contoh:
```bash
curl -X POST localhost:8000/api/process -H "Content-Type: application/json" -d '{
 "question_count":12,"answered_questions":12,"correct_answers":11,"duration_seconds":540,
 "hint_count":0,"attempt_count":1,"streak_days":3,"game_level":3,"feedback_frequency":3}'
```

## Aturan gamifikasi
* **Status**: skor >= 75 -> Tuntas, selain itu Perlu Remedial.
* **XP** = skor x 0,20 + 5 (akurasi >= 85) + 5 (selesai 100%) + 2 XP/hari streak (maks 10) - hint (maks 4).
* **Badge**: Quiz Finisher, High Achiever (skor >= 90), Persistent Learner (percobaan >= 2), Learning Streak (streak >= 3), Remedial Cleared (lulus setelah sebelumnya remedial di level yang sama).
* **Level adaptif**: engagement >= 75 & akurasi >= 85 -> naik; Remedial & engagement < 65 -> turun; selain itu tetap.
* **Rank XP**: Pemula (0), Penjelajah (50), Pejuang (150), Ahli (300), Legenda (600).

## Catatan & keterbatasan
* Label `learning_status` pada dataset adalah turunan skor (>= 75), sehingga akurasi model fitur kinerja sangat tinggi. Status akhir tetap ditentukan aturan; model dipakai sebagai pendukung (peluang remedial).
* `engagement_score` di dataset ternyata fungsi linear tepat dari skor, kelengkapan, streak, hint, dan frekuensi umpan balik (R² = 1,0), sehingga diestimasi dengan regresi linear. Karena itu membuka penjelasan soal menaikkan engagement.
* Durasi di dataset ~50 detik/soal; pengguna web biasanya lebih cepat, sehingga probabilitas model bisa kurang representatif. Itu sebabnya status memakai aturan, bukan model.
* Prototipe edukatif, bukan untuk keputusan akademik nyata (Academic Disclaimer tampil di halaman web).
