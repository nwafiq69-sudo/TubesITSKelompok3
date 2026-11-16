# Praktikum Guided — Modul 9 & 10
## Student Performance: REST API dan Web App

# Praktikum Guided — Modul 9 & 10
## Student Performance: REST API dan Web App

Starter project ini menyiapkan kode inti untuk praktikum 100 menit dengan metode guided.
Mahasiswa mempelajari alur, menjalankan aplikasi, menguji endpoint, dan menelusuri data dari
form sampai response API.

## 1. Struktur folder

```text
student-ml-web-guided/
├── app.py
├── requirements.txt
├── README.md
├── model/
│   └── student_pass_pipeline.joblib  <-- salin dari hasil Modul 8
└── static/
    ├── index.html
    ├── style.css
    └── app.js
```

## 2. Persiapan model

Salin `student_pass_pipeline.joblib` hasil Modul 8 ke folder `model/`.
File model tidak disertakan karena harus berasal dari pipeline yang benar-benar dibuat
dan dievaluasi pada praktikum sebelumnya. Pastikan nama file dan 12 fitur cocok.

## 3. Membuat environment

### Windows PowerShell
```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
```

### Linux/macOS
```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 4. Instal dependency dan jalankan

```bash
python -m pip install --upgrade pip
cd student-ml-web-guided
pip install -r requirements.txt
pip install scikit-learn==1.6.1
```

Buka:
- Web app: http://127.0.0.1:8000/
- Health check: http://127.0.0.1:8000/health
- Swagger UI: http://127.0.0.1:8000/docs

## 5. Contoh payload untuk Swagger

```json
{
  "age": 17,
  "studytime": 3,
  "failures": 0,
  "schoolsup": "yes",
  "famsup": "yes",
  "activities": "yes",
  "higher": "yes",
  "internet": "yes",
  "famrel": 4,
  "freetime": 3,
  "goout": 2,
  "absences": 4
}
```

## 6. Kontrak API

| Method | Endpoint | Fungsi | Response umum |
|---|---|---|---|
| GET | `/health` | Memeriksa layanan | `{"status":"ok"}` |
| POST | `/predict` | Prediksi dari 12 fitur | `class_id`, `prediction`, `probability_tuntas`, `disclaimer` |

Validasi numerik: `age` 15–22; `studytime` 1–4; `failures` 0–4;
`famrel`, `freetime`, `goout` 1–5; `absences` 0–93.
Field kategori: `schoolsup`, `famsup`, `activities`, `higher`, `internet` bernilai `yes` atau `no`.

## 7. Alur kerja praktikum

| 1| Menghubungkan pipeline Modul 8 dengan deployment |
| 2| REST API, HTTP POST, JSON, FastAPI, Pydantic |
| 3| Menjalankan server dan uji GET `/health` serta POST `/predict` melalui Swagger |
| 4| Membaca response dan validasi input |
| 5| Frontend vs backend; HTML form, CSS, JavaScript |
| 6| Guided walkthrough: FormData → Number → JSON → Fetch API |
| 7| Menjalankan web app dan uji end-to-end |
| 8| Uji error sederhana dan lacak satu payload |
| 9| Rangkuman dan responsible use |

## 8. Checklist demonstrasi mahasiswa

1. Server berhasil berjalan.
2. `GET /health` mengembalikan status `ok`.
3. `POST /predict` berhasil pada Swagger.
4. Input di luar rentang ditolak oleh validasi Pydantic.
5. Form web mengirim data tanpa reload halaman.
6. Hasil prediksi dan probabilitas tampil.
7. Mahasiswa dapat menjelaskan alur input → JSON → API → model → response → UI.

## 9. Catatan teknis penting

- Versi scikit-learn saat inference harus kompatibel dengan versi saat pipeline disimpan.
  Jika muncul warning/error saat `joblib.load`, cocokkan versi library dari environment Modul 8.
- Jangan memuat file Joblib/Pickle dari sumber yang tidak dipercaya.
- Jika model tidak memiliki `predict_proba`, aplikasi tetap menampilkan kelas prediksi dan
  menandai probabilitas sebagai tidak tersedia.
- Bila frontend dan API disajikan oleh FastAPI pada origin lokal yang sama, konfigurasi CORS
  tidak diperlukan untuk skenario ini.
- Dataset Student Performance berasal dari dua sekolah di Portugal. Ini prototipe akademik,
  bukan alat untuk memberi label, menghukum, atau menentukan kelulusan siswa nyata.

Kode app.py adalah implementasi **FastAPI** (sebuah framework web Python) untuk membuat API yang mengintegrasikan model Machine Learning. Fungsinya adalah menerima data siswa dari pengguna (seperti dari browser atau aplikasi lain), memprosesnya menggunakan model, dan mengembalikan hasil prediksi apakah siswa tersebut akan "Tuntas" atau "Belum Tuntas" secara akademik.

# 1. Persiapan File dan Pemuatan Model
Kode diawali dengan `BASE_DIR` untuk menentukan direktori saat ini dan mencari file model `student_pass_pipeline.joblib`. Jika file tidak ditemukan, program akan langsung terhenti (`raise FileNotFoundError`).
Model kemudian dimuat menggunakan `joblib.load(MODEL_PATH)`. Pemuatan ini diletakkan di luar fungsi API agar model hanya dipanggil satu kali saat server pertama kali menyala, bukan diulang-ulang setiap kali ada pengguna yang meminta prediksi. Ini membuat server jauh lebih cepat dan hemat memori.

# 2. Inisialisasi Server dan File Statis
Objek `app = FastAPI(...)` dibuat sebagai pondasi server. Kemudian, `app.mount("/static", ...)` digunakan agar server FastAPI juga bisa bertindak sebagai web server tradisional yang menyajikan file aset frontend (seperti CSS, JavaScript, atau gambar) yang disimpan di dalam folder `static`.

# 3. Validasi Data Input dengan Pydantic
Kelas `StudentInput(BaseModel)` bertindak sebagai "penjaga gerbang" yang memastikan data yang dikirim (payload) bentuknya valid sebelum masuk ke model machine learning.

* `Field(ge=15, le=22)`: Memastikan angka berada dalam batas tertentu (misalnya, *age* harus *greater or equal* 15 dan *less or equal* 22).
* `Literal["yes", "no"]`: Memastikan input teks hanya berisi kata "yes" atau "no", mencegah error tipografi.
Jika pengguna mengirim data yang tidak sesuai (misal: usia 50), FastAPI akan otomatis memblokirnya dan mengirimkan pesan error kepada pengguna tanpa merusak server.

# 4. Rute (Endpoint) API
Terdapat tiga rute utama yang bisa diakses:

* `@app.get("/")`: Rute utama untuk menampilkan antarmuka web. Saat pengguna membuka alamat server, ini akan menyajikan halaman `index.html`.
* `@app.get("/health")`: Endpoint sederhana untuk memastikan server berjalan dengan baik (biasanya digunakan oleh sistem *monitoring*).
* `@app.post("/predict")`: Ini adalah "otak" dari API. Menerima data JSON (yang sudah divalidasi oleh `StudentInput`), lalu diubah menjadi format tabel `pandas.DataFrame` dengan perintah `model_dump()`. Data tersebut kemudian diprediksi oleh model (`model.predict`). Jika model mendukung probabilitas perhitungan (seperti *Logistic Regression*), persentasenya ikut diambil (`model.predict_proba`). Hasil akhirnya dikemas ulang menjadi JSON yang memuat keputusan, persentase tuntas, dan *disclaimer* untuk dikembalikan ke pengguna.