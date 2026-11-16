"""Bank soal kuis adaptif (5 level x 11 soal). Tambahkan soal baru dengan format yang sama."""
import random

JUMLAH_SOAL_PER_KUIS = 10

LEVEL_INFO = {
    1: "Dasar Pemrograman & Arsitektur ITS",
    2: "Percabangan & Logika Adaptif",
    3: "Perulangan & Evaluasi Belajar",
    4: "Fungsi, List & Student Modeling",
    5: "Algoritma, Machine Learning & Kompleksitas",
}


def _q(level, text, options, answer, hint, explanation, topic="Umum"):
    return {"level": level, "text": text, "options": options, "answer": answer,
            "hint": hint, "explanation": explanation, "topic": topic}


_RAW = [
    # ---------------- Level 1: Dasar Pemrograman & Arsitektur ITS
    _q(1, "Apa tipe data dari nilai pada `x = 3.14`?", ["int", "float", "str", "bool"], 1,
       "Perhatikan adanya tanda desimal.", "Bilangan dengan titik desimal bertipe float.", topic="Tipe Data"),
    _q(1, "Apa output dari `print(7 // 2)`?", ["3.5", "3", "4", "2"], 1,
       "`//` adalah pembagian bulat.", "`//` membuang bagian desimal sehingga 7 // 2 = 3.", topic="Operator Aritmatika"),
    _q(1, "Operator yang menghasilkan sisa bagi adalah ...", ["/", "//", "%", "**"], 2,
       "Dikenal juga sebagai modulo.", "Operator `%` (modulo) memberi sisa bagi, mis. 7 % 2 = 1.", topic="Operator Aritmatika"),
    _q(1, "Apa hasil `type(\"10\")`?", ["int", "str", "float", "list"], 1,
       "Lihat tanda kutipnya.", "Nilai dalam tanda kutip adalah string (str) walau isinya angka.", topic="Tipe Data"),
    _q(1, "Nama variabel yang valid di Python adalah ...", ["2nama", "nama-var", "nama_var", "class"], 2,
       "Tidak boleh diawali angka, mengandung tanda minus, atau memakai kata kunci.",
       "`nama_var` valid. Yang lain diawali angka, memakai tanda minus, atau kata kunci.", topic="Variabel & Sintaks"),
    _q(1, "Apa output dari `print(2 ** 3)`?", ["6", "8", "9", "5"], 1,
       "`**` adalah operator pangkat.", "2 ** 3 = 2 x 2 x 2 = 8.", topic="Operator Aritmatika"),
    _q(1, "Apa hasil dari `\"Hai\" + \"Dunia\"`?", ["HaiDunia", "Hai Dunia", "Error", "Hai+Dunia"], 0,
       "Operator + pada string berarti penggabungan.",
       "Penggabungan string tidak menambah spasi otomatis, hasilnya `HaiDunia`.", topic="String"),
    _q(1, "Fungsi untuk membaca masukan teks dari pengguna adalah ...",
       ["print()", "input()", "read()", "scan()"], 1,
       "Kebalikan dari print.", "`input()` membaca teks dari pengguna dan mengembalikannya sebagai string.", topic="Input & Output"),
    _q(1, "Manakah empat komponen arsitektur klasik dari sebuah Intelligent Tutoring System (ITS)?",
       ["Domain Model, Student Model, Pedagogical Model, User Interface",
        "Database, Compiler, Web Server, Load Balancer",
        "Firewall, Router, Switch, Gateway",
        "Frontend, Backend, DevOps, Testing"], 0,
       "Pikirkan model pengetahuan materi, model status siswa, model pedagogik tutor, dan antarmuka interaksi.",
       "Arsitektur klasik ITS terdiri atas 4 modul: Domain Model (materi), Student Model (status siswa), Pedagogical Model (strategi instruksional), dan User Interface (antarmuka).",
       topic="Arsitektur ITS"),
    _q(1, "Dalam ITS, komponen yang bertugas merepresentasikan pengetahuan dan penguasaan konsep siswa disebut ...",
       ["Student Model", "Domain Model", "Pedagogical Model", "Communication Model"], 0,
       "Fokus pada representasi profil kognitif dan riwayat performa pembelajar.",
       "Student Model melacak pengetahuan, kesalahan pemahaman (misconceptions), dan progres performa siswa secara adaptif.",
       topic="Arsitektur ITS"),
    _q(1, "Tujuan utama adaptasi pembelajaran dalam Intelligent Tutoring System (ITS) adalah ...",
       ["Menyesuaikan materi dan tingkat kesulitan dengan kebutuhan masing-masing pembelajar",
        "Memaksa semua siswa menyelesaikan soal dengan waktu yang persis sama",
        "Menghilangkan peran pendidik secara total",
        "Mengurangi materi kuliah menjadi sesingkat mungkin"], 0,
       "Personalisasi pengalaman belajar adalah inti dari adaptive learning engine.",
       "ITS bertujuan memberikan instruksi personal yang menyesuaikan gaya, kecepatan, dan kesulitan sesuai performa unik tiap siswa.",
       topic="Konsep ITS"),

    # ---------------- Level 2: Percabangan & Logika Adaptif
    _q(2, "Kata kunci untuk kondisi alternatif setelah `if` adalah ...",
       ["elseif", "else if", "elif", "otherwise"], 2,
       "Gabungan singkat dari else dan if.", "Python memakai `elif` untuk kondisi alternatif.", topic="Percabangan Python"),
    _q(2, "Apa output?\n```\nx = 5\nif x > 3:\n    print('A')\nelse:\n    print('B')\n```",
       ["A", "B", "AB", "Error"], 0,
       "Apakah 5 lebih besar dari 3?", "Kondisi x > 3 bernilai True, sehingga yang dicetak adalah A.", topic="Percabangan Python"),
    _q(2, "Operator logika untuk \"dan\" di Python adalah ...", ["&&", "and", "&", "||"], 1,
       "Python memakai kata, bukan simbol.", "Python memakai kata kunci `and`; `&&` bukan sintaks Python.", topic="Logika Boolean"),
    _q(2, "Apa hasil `print(10 > 5 and 3 > 4)`?", ["True", "False", "None", "Error"], 1,
       "`and` hanya True jika kedua sisi True.", "10 > 5 True, 3 > 4 False, maka True and False = False.", topic="Logika Boolean"),
    _q(2, "Operator pembanding \"sama dengan\" adalah ...", ["==", "=", "===", ":="], 0,
       "Satu tanda sama dengan dipakai untuk hal lain.", "`==` membandingkan, sedangkan `=` adalah penugasan.", topic="Operator Pembanding"),
    _q(2, "Kondisi yang tepat agar nilai 75 dinyatakan tuntas (KKM 75) adalah ...",
       ["nilai > 75", "nilai < 75", "nilai >= 75", "nilai == 100"], 2,
       "Nilai tepat 75 harus ikut lulus.", "`>=` mencakup nilai 75 sendiri, sedangkan `>` tidak.", topic="Kriteria Ketuntasan"),
    _q(2, "Apa hasil `print(not (5 > 3))`?", ["False", "True", "5", "Error"], 0,
       "Hitung dulu isi kurung, lalu balikkan.", "5 > 3 True, `not True` menjadi False.", topic="Logika Boolean"),
    _q(2, "Blok kode di dalam `if` pada Python ditandai dengan ...",
       ["Kurung kurawal { }", "Titik koma", "Indentasi (menjorok)", "end if"], 2,
       "Python mementingkan tata letak baris.", "Python memakai indentasi untuk menandai blok kode.", topic="Sintaks Python"),
    _q(2, "Dalam rule-based reasoning ITS, jika skor siswa >= 75, status pembelajaran siswa diklasifikasikan sebagai ...",
       ["Tuntas", "Perlu Remedial", "Drop Out", "Tidak Valid"], 0,
       "KKM sistem berada di nilai 75.", "Berdasarkan batas ketuntasan (KKM 75), skor >= 75 berstatus Tuntas, sedangkan < 75 adalah Perlu Remedial.", topic="Rule Engine ITS"),
    _q(2, "Pernyataan percabangan bersarang (nested if) digunakan ketika ...",
       ["Sebuah kondisi dievaluasi di dalam blok kondisi lain yang sudah terpenuhi",
        "Loop memerlukan interupsi darurat",
        "Program ingin menghentikan eksekusi tanpa syarat",
        "Fungsi tidak memiliki return value"], 0,
       "Kondisi berlapis di dalam blok if terdahulu.", "Nested if mengevaluasi kondisi spesifik setelah kondisi tingkat awal terpenuhi.", topic="Percabangan Lanjut"),
    _q(2, "Ekspresi ternary di Python ditulis dengan format ...",
       ["x if kondisi else y", "kondisi ? x : y", "if kondisi then x else y", "ifelse(kondisi, x, y)"], 0,
       "Gunakan klausa inline khas Python.", "Format ekspresi ternary Python adalah: `nilai_jika_true if kondisi else nilai_jika_false`.", topic="Sintaks Python"),

    # ---------------- Level 3: Perulangan & Evaluasi Belajar
    _q(3, "Apa output `for i in range(3): print(i)`?", ["1 2 3", "0 1 2", "0 1 2 3", "1 2"], 1,
       "range mulai dari 0 dan berhenti SEBELUM angka akhir.", "range(3) menghasilkan 0, 1, 2.", topic="Perulangan For"),
    _q(3, "Berapa kali badan loop `for i in range(5)` dijalankan?", ["4", "6", "5", "0"], 2,
       "Hitung jumlah nilai yang dihasilkan range(5).", "range(5) menghasilkan 0-4, yaitu 5 iterasi.", topic="Perulangan For"),
    _q(3, "Perulangan yang berjalan selama kondisinya True adalah ...", ["for", "while", "if", "def"], 1,
       "Namanya berarti \"selama\".", "`while` mengulang selama kondisinya bernilai True.", topic="Perulangan While"),
    _q(3, "Kata kunci untuk menghentikan loop seketika adalah ...", ["continue", "pass", "stop", "break"], 3,
       "Artinya \"memutus\".", "`break` langsung keluar dari loop terdekat.", topic="Kontrol Perulangan"),
    _q(3, "Apa output?\n```\ntotal = 0\nfor i in range(1, 4):\n    total += i\nprint(total)\n```",
       ["6", "10", "3", "4"], 0,
       "Jumlahkan 1 + 2 + 3.", "i bernilai 1, 2, 3 sehingga total = 6.", topic="Akumulator"),
    _q(3, "Fungsi `continue` di dalam loop adalah ...",
       ["Keluar dari program", "Melewati iterasi saat ini dan lanjut ke iterasi berikutnya",
        "Mengulang loop dari awal", "Menghentikan loop"], 1,
       "Bukan menghentikan loop, hanya melompat.", "`continue` melewati sisa badan loop untuk iterasi saat itu.", topic="Kontrol Perulangan"),
    _q(3, "Apa masalah kode `x = 0` lalu `while x < 3: print(x)`?",
       ["Tidak ada masalah", "Error sintaks", "Perulangan tak berhingga karena x tidak berubah",
        "Hanya mencetak sekali"], 2,
       "Apakah nilai x pernah bertambah?", "x selalu 0 sehingga kondisi tak pernah False: infinite loop.", topic="Debugging Perulangan"),
    _q(3, "`range(2, 10, 3)` menghasilkan ...", ["2, 4, 6, 8", "3, 6, 9", "2, 5, 8", "2, 5, 8, 11"], 2,
       "Argumen ketiga adalah langkah (step), batas akhir tidak ikut.", "Mulai 2, naik 3: 2, 5, 8 (11 melebihi batas).", topic="Range & Step"),
    _q(3, "Manakah konstruksi loop yang tepat untuk memproses seluruh jawaban dalam sebuah kuis?",
       ["for jawaban in daftar_jawaban:", "repeat until selesai:", "loop while forever:", "goto verifikasi;"], 0,
       "Python menggunakan loop for-in untuk mengiterasi koleksi.", "Konstruksi `for item in koleksi:` mengiterasi seluruh elemen jawaban secara teratur.", topic="Iterasi Koleksi"),
    _q(3, "Fitur learning streak pada platform ITS bertambah jika ...",
       ["Siswa menyelesaikan kuis secara konsisten di hari yang berurutan",
        "Siswa membuka web 100 kali dalam 1 jam",
        "Siswa menebak jawaban secara acak tanpa jeda",
        "Siswa mengulang soal yang sama 50 kali di menit yang sama"], 0,
       "Streak didasarkan pada konsistensi harian.", "Streak mengukur kebiasaan belajar harian berurutan tanpa jeda lebih dari satu hari.", topic="Gamifikasi & Streak"),
    _q(3, "Apa hasil dari list comprehension `[x * 2 for x in [1, 2, 3]]`?",
       ["[2, 4, 6]", "[1, 2, 3, 1, 2, 3]", "[2, 2, 2]", "Error"], 0,
       "Setiap elemen x dikalikan dua.", "List comprehension menghasilkan list baru berisi [1*2, 2*2, 3*2] = [2, 4, 6].", topic="List Comprehension"),

    # ---------------- Level 4: Fungsi, List & Student Modeling
    _q(4, "Kata kunci untuk mendefinisikan fungsi di Python adalah ...",
       ["function", "def", "func", "define"], 1,
       "Singkatan dari \"define\".", "Fungsi didefinisikan dengan `def nama_fungsi():`.", topic="Fungsi Python"),
    _q(4, "Apa hasil `len([1, 2, 3, 4])`?", ["3", "5", "4", "[4]"], 2,
       "Hitung jumlah elemen.", "len menghitung jumlah elemen list: 4.", topic="Struktur List"),
    _q(4, "Apa isi `a` setelah `a = [1, 2, 3]; a.append(4)`?",
       ["[1, 2, 3]", "[4, 1, 2, 3]", "[1, 2, 3, 4]", "[1, 2, 3, [4]]"], 2,
       "append menambah di bagian akhir.", "`append` menambahkan elemen di akhir list.", topic="Metode List"),
    _q(4, "Indeks elemen pertama pada list Python adalah ...", ["0", "1", "-1", "first"], 0,
       "Penomoran di Python tidak dimulai dari 1.", "Indeks list dimulai dari 0.", topic="Indeks List"),
    _q(4, "Apa output?\n```\ndef f(x):\n    return x * 2\nprint(f(4))\n```", ["4", "8", "16", "None"], 1,
       "Fungsi mengembalikan dua kali input.", "f(4) mengembalikan 4 * 2 = 8.", topic="Pemanggilan Fungsi"),
    _q(4, "Apa hasil `[1, 2, 3][-1]`?", ["1", "Error", "2", "3"], 3,
       "Indeks negatif dihitung dari belakang.", "Indeks -1 menunjuk elemen terakhir, yaitu 3.", topic="Indeks Negatif"),
    _q(4, "Perbedaan utama `return` dan `print` pada fungsi adalah ...",
       ["Tidak ada perbedaan", "return mengembalikan nilai ke pemanggil, print hanya menampilkan",
        "print mengembalikan nilai, return menampilkan", "return hanya untuk angka"], 1,
       "Satu bisa dipakai lagi dalam perhitungan, satu hanya tampil di layar.",
       "return menyerahkan nilai ke pemanggil fungsi, print hanya mencetak ke layar.", topic="Fungsi Python"),
    _q(4, "Apa output `lst = [5, 2, 9]; lst.sort(); print(lst)`?",
       ["[5, 2, 9]", "[2, 5, 9]", "[9, 5, 2]", "None"], 1,
       "sort mengurutkan menaik secara default.", "`sort()` mengurutkan list di tempat secara menaik.", topic="Metode List"),
    _q(4, "Struktur data Python yang paling tepat untuk menyimpan pemetaan nama metrik belajar ke nilainya (key-value) adalah ...",
       ["Dictionary (dict)", "Tuple", "Set", "String"], 0,
       "Struktur key-value dengan pencarian cepat.", "Dictionary menyimpan pasangan kunci-nilai (key-value), sangat cocok untuk metadata siswa.", topic="Struktur Data"),
    _q(4, "Dalam pemodelan pembelajar (Student Model), representasi Bayesian Knowledge Tracing (BKT) memperkirakan ...",
       ["Peluang siswa telah menguasai suatu keterampilan tertentu secara laten",
        "Kecepatan koneksi internet siswa saat ujian",
        "Banyaknya baris kode yang ditulis tutor",
        "Jumlah karakter pada nama siswa"], 0,
       "BKT memodelkan penguasaan konsep laten siswa seiring waktu.",
       "BKT menggunakan Hidden Markov Model untuk memperkirakan probabilitas penguasaan materi (mastery) dari urutan jawaban benar/salah.",
       topic="Student Modeling"),
    _q(4, "Apa hasil dari `list(filter(lambda x: x >= 75, [60, 75, 80, 70]))`?",
       ["[75, 80]", "[60, 70]", "[80]", "[60, 75, 80, 70]"], 0,
       "Filter hanya menyaring nilai yang memenuhi kriteria >= 75.", "`filter` menyaring nilai 75 dan 80 yang bernilai True pada kondisi >= 75.", topic="Fungsi Tingkat Tinggi"),

    # ---------------- Level 5: Algoritma, Machine Learning & Kompleksitas
    _q(5, "Kompleksitas waktu pencarian linear pada n elemen adalah ...",
       ["O(1)", "O(log n)", "O(n)", "O(n^2)"], 2,
       "Pada kasus terburuk semua elemen diperiksa.", "Linear search memeriksa maksimal n elemen: O(n).", topic="Kompleksitas Algoritma"),
    _q(5, "Syarat utama agar binary search dapat dipakai adalah data ...",
       ["Acak", "Terurut", "Unik semua", "Bilangan genap"], 1,
       "Pencarian membuang setengah data tiap langkah.", "Binary search membutuhkan data yang sudah terurut.", topic="Algoritma Pencarian"),
    _q(5, "Fungsi rekursif harus memiliki ...", ["Loop for", "Variabel global", "Base case", "Kelas"], 2,
       "Tanpa ini rekursi tak pernah berhenti.", "Base case adalah kondisi berhenti agar rekursi tidak tak berhingga.", topic="Algoritma Rekursif"),
    _q(5, "Apa hasil f(4)?\n```\ndef f(n):\n    return 1 if n <= 1 else n * f(n - 1)\n```",
       ["10", "24", "16", "12"], 1,
       "Ini fungsi faktorial.", "f(4) = 4 x 3 x 2 x 1 = 24.", topic="Algoritma Rekursif"),
    _q(5, "Kompleksitas waktu binary search adalah ...",
       ["O(n)", "O(n log n)", "O(1)", "O(log n)"], 3,
       "Data dibelah dua pada tiap langkah.", "Setiap langkah membuang separuh data: O(log n).", topic="Kompleksitas Algoritma"),
    _q(5, "Kompleksitas kasus terburuk bubble sort adalah ...",
       ["O(n)", "O(log n)", "O(n^2)", "O(1)"], 2,
       "Dua loop bersarang.", "Bubble sort membandingkan pasangan dalam dua loop: O(n^2).", topic="Algoritma Pengurutan"),
    _q(5, "Struktur data dengan prinsip FIFO adalah ...", ["Stack", "Queue", "Tree", "Graph"], 1,
       "Seperti antrean di loket.", "Queue: yang pertama masuk adalah yang pertama keluar (FIFO).", topic="Struktur Data"),
    _q(5, "Struktur data stack menerapkan prinsip ...", ["FIFO", "LIFO", "Acak", "Terurut"], 1,
       "Seperti tumpukan piring.", "Stack: yang terakhir masuk adalah yang pertama keluar (LIFO).", topic="Struktur Data"),
    _q(5, "Dalam algoritma K-Nearest Neighbors (KNN) untuk klasifikasi status belajar, label ditentukan berdasarkan ...",
       ["Mayoritas kelas dari k tetangga terdekat berdasarkan jarak fitur",
        "Bobot sinaptik hasil backpropagation bertahap",
        "Pohon keputusan dengan entropy terkecil",
        "Nilai centroid k-means yang acak"], 0,
       "KNN mengukur jarak kedekatan (Euclidean distance) ke k observasi data latih.",
       "KNN mencari k data siswa terdekat dalam ruang fitur dan mengambil kelas mayoritas (voting) sebagai hasil klasifikasi.",
       topic="Machine Learning (KNN)"),
    _q(5, "Multi-Layer Perceptron (MLP) yang digunakan pada evaluasi ITS merupakan jenis arsitektur ...",
       ["Artificial Neural Network feedforward dengan satu atau lebih hidden layers",
        "Linear regression tanpa activation function",
        "K-Means clustering unsupervised",
        "Algoritma genetika murni"], 0,
       "JST berlapis dengan fungsi aktivasi non-linear.",
       "MLP adalah jaringan saraf tiruan (feedforward ANN) dengan lapisan masukan, lapisan tersembunyi (hidden layer), dan lapisan keluaran dengan bobot yang dioptimalkan.",
       topic="Machine Learning (JST/MLP)"),
    _q(5, "Metrik evaluasi yang tepat untuk mengukur seberapa baik model mendeteksi siswa yang benar-benar membutuhkan remedial adalah ...",
       ["Recall", "Accuracy semata", "Loss tanpa normalisasi", "Throughput memori"], 0,
       "Recall mengukur proporsi kasus positif (perlu remedial) yang berhasil diidentifikasi.",
       "Recall meminimalkan false negatives sehingga siswa yang berisiko tertinggal dapat terdeteksi untuk mendapatkan remedial.",
       topic="Evaluasi Machine Learning"),
]

BANK = {}
for _i, _s in enumerate(_RAW, start=1):
    _s["id"] = f"S{_i:03d}"
    BANK[_s["id"]] = _s


def soal_untuk_level(level, jumlah=JUMLAH_SOAL_PER_KUIS, rng=None):
    """Mengambil soal acak untuk satu level, TANPA kunci jawaban & penjelasan."""
    rng = rng or random
    kandidat = [s for s in BANK.values() if s["level"] == level]
    if not kandidat:
        raise ValueError(f"Level {level} tidak punya soal")
    pilih = rng.sample(kandidat, min(jumlah, len(kandidat)))
    return [{"id": s["id"], "level": s["level"], "text": s["text"],
             "options": s["options"], "hint": s["hint"], "topic": s.get("topic", "Materi ITS")} for s in pilih]


def periksa(soal_id, indeks):
    """Memeriksa satu jawaban. Mengembalikan (benar, penjelasan, indeks_benar)."""
    s = BANK.get(soal_id)
    if s is None:
        raise KeyError(f"Soal {soal_id} tidak ditemukan")
    return indeks == s["answer"], s["explanation"], s["answer"]
