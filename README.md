# Praktikum Guided — Gamified ITS
## Student Performance: REST API dan Web App

Proyek ini merupakan aplikasi **Intelligent Tutoring System (ITS)** edukatif berbasis web. Aplikasi menerima hasil kuis, menentukan status belajar, memperkirakan engagement, lalu memberikan XP, badge, rekomendasi level adaptif, dan umpan balik. Prediksi status menggunakan model machine learning, sedangkan ketuntasan akhir ditentukan oleh aturan KKM.

## 1. Struktur folder

```text
TubesITSKelompok3/
├── app/
│   ├── engine.py          # Validasi, prediksi, aturan status dan gamifikasi
│   ├── gamify.py          # Rank XP dan streak
│   ├── main.py            # REST API FastAPI dan penyajian frontend
│   ├── questions.py       # Bank soal untuk 5 level
│   ├── schemas.py         # Validasi request dengan Pydantic
│   ├── service.py         # Alur kuis, pemain, streak, XP dan badge
│   └── store.py           # Penyimpanan SQLite
├── data/
│   └── dataset_gamified_its_1000.csv
├── docs/screenshots/      # Tangkapan layar antarmuka
├── models/                # Model ITS (.joblib)
├── static/
│   ├── index.html         # Struktur halaman web
│   ├── style.css          # Tampilan dan layout responsif
│   └── app.js             # Interaksi frontend dan Fetch API
├── tests/                 # Pengujian engine, layanan, dan API
├── train_model.py         # Melatih dan mengekspor model
├── requirements.txt
└── README.md
```

## 2. Model dan dataset

File model sudah tersedia di folder `models/`, termasuk model klasifikasi utama dan model estimasi engagement. Dataset `data/dataset_gamified_its_1000.csv` berisi 1.000 catatan performa dari 200 mahasiswa unik. Database SQLite dibuat otomatis saat aplikasi dijalankan dan diisi dengan data awal untuk leaderboard.

Pelatihan ulang model bersifat opsional. Jalankan perintah berikut jika ingin melatih ulang model menggunakan dependensi di environment aktif:

```bash
python train_model.py
```

## 3. Persiapan environment

Pastikan Python dan pip sudah tersedia.

### Windows PowerShell

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

### Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 4. Instalasi dan menjalankan aplikasi

Jalankan dari direktori proyek:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Buka alamat berikut di browser:

- Web app: <http://127.0.0.1:8000/>
- Health check: <http://127.0.0.1:8000/health>
- Swagger UI: <http://127.0.0.1:8000/docs>

Untuk menghentikan server, tekan `Ctrl+C` pada terminal.

## 5. Contoh payload untuk Swagger

Pilih `POST /api/process`, klik **Try it out**, lalu masukkan JSON berikut:

```json
{
  "question_count": 12,
  "answered_questions": 12,
  "correct_answers": 11,
  "duration_seconds": 540,
  "hint_count": 0,
  "attempt_count": 1,
  "streak_days": 3,
  "game_level": 3,
  "feedback_frequency": 3
}
```

Response memuat ringkasan skor dan akurasi, status dari aturan, estimasi remedial model, estimasi engagement, XP, badge, level baru, dan pesan umpan balik.

## 6. Kontrak API

| Method | Endpoint | Fungsi |
|---|---|---|
| GET | `/health` | Memeriksa status layanan, model, jumlah soal, dan pemain. |
| GET | `/api/meta` | Mengambil informasi level, badge, rank, dataset, dan evaluasi model. |
| POST | `/api/process` | Memproses metrik kuis; opsional memperbarui profil jika diberi `player_id`. |
| POST | `/api/players` | Membuat pemain atau mengambil profil berdasarkan nama. |
| GET | `/api/players/{id}` | Mengambil profil pemain beserta riwayat kuis. |
| GET | `/api/quiz/{level}?player_id={id}` | Mengambil 10 soal acak untuk level yang sudah terbuka. |
| POST | `/api/quiz/check` | Memeriksa satu jawaban dan mengembalikan umpan balik serta penjelasan. |
| POST | `/api/quiz/submit` | Menilai jawaban kuis dan memperbarui XP, badge, streak, profil, dan level. |
| GET | `/api/leaderboard` | Mengambil leaderboard; mendukung parameter `limit` dan `player_id`. |

### Contoh membuat atau mengambil pemain

```json
{
  "name": "Budi Santoso"
}
```

Kirim ke `POST /api/players`. Gunakan `id` dari response sebagai `player_id` untuk mengambil soal dan mengirim hasil kuis.

### Validasi input utama `/api/process`

| Field | Aturan |
|---|---|
| `question_count` | Angka bulat dari 1 sampai 200. |
| `answered_questions` | Angka bulat dari 0 sampai 200, tidak melebihi jumlah soal. |
| `correct_answers` | Angka bulat dari 0 sampai 200, tidak melebihi jumlah yang dijawab. |
| `duration_seconds` | Angka lebih besar dari 0 dan paling lama 86.400 detik. |
| `hint_count` | Angka bulat dari 0 sampai 200. |
| `attempt_count` | Angka bulat dari 1 sampai 100. |
| `streak_days` | Angka bulat dari 0 sampai 3.650 hari. |
| `game_level` | Angka bulat dari 1 sampai 5. |
| `feedback_frequency` | Angka bulat dari 0 sampai 200. |
| `player_id` | Opsional, maksimal 32 karakter. Jika diisi, profil ikut diperbarui. |

Field yang salah eja atau field tambahan ditolak. Request yang tidak valid mengembalikan HTTP 422; pemain tidak ditemukan mengembalikan HTTP 404; level yang belum terbuka mengembalikan HTTP 403.

## 7. Alur kerja praktikum

| Langkah | Materi/kegiatan |
|---:|---|
| 1 | Memahami struktur frontend, backend, model, dataset, dan database. |
| 2 | Menjalankan server FastAPI dan membuka web app. |
| 3 | Memeriksa `GET /health` dan dokumentasi Swagger. |
| 4 | Mengirim JSON ke `POST /api/process` dan membaca response. |
| 5 | Menelusuri validasi input menggunakan Pydantic. |
| 6 | Membuat pemain, mengambil kuis, memeriksa jawaban, dan mengirim kuis. |
| 7 | Mengamati perubahan skor, status, XP, badge, streak, level, profil, dan leaderboard. |
| 8 | Menguji input typo, field yang hilang, nilai di luar batas, dan level terkunci. |
| 9 | Menjelaskan alur formulir web → Fetch API → REST API → service → model/aturan → response → antarmuka. |

## 8. Checklist demonstrasi

1. Server berjalan tanpa error dan halaman utama dapat dibuka.
2. `GET /health` memberikan status `ok`.
3. Payload valid berhasil diproses melalui Swagger.
4. Input tidak valid ditolak dan menghasilkan pesan validasi.
5. Pemain dapat dibuat atau diambil berdasarkan nama.
6. Kuis hanya dapat diambil pada level yang telah terbuka.
7. Jawaban kuis dinilai di sisi server.
8. Hasil kuis memperbarui XP, badge, streak, profil, dan riwayat sesuai aturan.
9. Mahasiswa dapat menjelaskan alur data dari form sampai response API.

## 9. Aturan status dan gamifikasi

- **Status belajar:** skor minimal 75 berarti **Tuntas**; skor di bawah 75 berarti **Perlu Remedial**.
- **XP:** dasar skor adalah 20% dari skor; bonus 5 XP untuk akurasi minimal 85%, bonus 5 XP untuk penyelesaian 100%, bonus streak 2 XP per hari (maksimal 10 XP), dan penalti 1 XP per hint (maksimal 4 XP).
- **Badge:** `Quiz Finisher`, `High Achiever` (skor ≥ 90), `Persistent Learner` (percobaan ≥ 2), `Learning Streak` (streak ≥ 3 hari), dan `Remedial Cleared` (lulus setelah remedial di level yang sama).
- **Level adaptif:** naik jika engagement ≥ 75 dan akurasi ≥ 85; turun jika status remedial dan engagement < 65; selain itu level dipertahankan. Level dibatasi dari 1 sampai 5.
- **Rank XP:** Pemula (0), Penjelajah (50), Pejuang (150), Ahli (300), dan Legenda (600).

## 10. Pengujian

Jalankan pengujian yang tersedia dengan perintah:

```bash
python -m unittest discover tests -v
```

Pengujian mencakup validasi engine, aturan XP dan badge, alur layanan pemain/kuis, serta endpoint API. Untuk pengujian API, dependency `httpx` disertakan di `requirements.txt`.

## 11. Catatan teknis dan batasan

- `learning_status` pada dataset merupakan turunan skor dengan batas 75. Status akhir karena itu ditentukan oleh aturan; model menjadi pendukung estimasi remedial.
- `engagement_score` pada dataset dapat diestimasi dari skor, kelengkapan, streak, hint, dan frekuensi umpan balik. Membuka penjelasan soal dapat menambah engagement.
- Durasi pada data pelatihan sekitar 50 detik per soal; waktu pengerjaan pengguna dapat berbeda, sehingga probabilitas model perlu ditafsirkan sebagai estimasi.
- Jika model gagal dimuat, latih ulang model dengan `python train_model.py` pada environment proyek.
- Aplikasi ini adalah prototipe edukatif untuk praktikum. Prediksi dan rekomendasi merupakan pendukung belajar, bukan dasar keputusan akademik formal.
akademik nyata (Academic Disclaimer tampil di halaman web).
