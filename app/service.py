"""Lapisan layanan: menggabungkan engine (ML + aturan), bank soal, dan penyimpanan pemain.

Dipisahkan dari FastAPI agar seluruh alur bisa diuji tanpa server (tests/test_service.py).
"""
from datetime import date

from . import engine, questions
from .gamify import hitung_streak, info_rank


class PemainTidakAda(LookupError):
    pass


def ringkasan_pemain(store, p):
    lb = store.leaderboard(limit=0, player_id=p["id"])
    pos = lb["posisi_kamu"]
    return {
        "id": p["id"], "name": p["name"], "total_xp": p["total_xp"], "level": p["level"],
        "level_terbuka": p["max_unlocked"], "level_pernah_dikerjakan": store.level_pernah_dikerjakan(p["id"]),
        "streak": p["streak"], "badges": p["badges"],
        "rata_rata_skor": p["avg_score"], "jumlah_kuis": p["attempts"],
        "rank_xp": info_rank(p["total_xp"]),
        "peringkat": pos["rank"] if pos else None, "total_pemain": lb["total_pemain"],
    }


def jalankan(store, data, player_id=None, today=None):
    """Memproses satu hasil kuis.

    - Tanpa player_id : stateless, murni menghitung (dipakai untuk uji & integrasi eksternal).
    - Dengan player_id: streak_days & attempt_count dihitung SERVER dari riwayat pemain,
      game_level dianggap level kuis yang dikerjakan, lalu profil/leaderboard diperbarui.
    """
    if player_id is None:
        hasil = engine.proses_kuis(data)
        hasil["pemain"] = None
        return hasil

    p = store.ambil(player_id)
    if p is None:
        raise PemainTidakAda(f"Pemain '{player_id}' tidak ditemukan")
    today = today or date.today()
    level_kuis = int(data["game_level"])
    streak = hitung_streak(p["streak"], p["last_active"], today)
    data = dict(data, streak_days=streak, attempt_count=store.jumlah_percobaan(player_id, level_kuis) + 1)
    sebelumnya = store.status_terakhir(player_id, level_kuis)

    hasil = engine.proses_kuis(data, total_xp_sebelumnya=p["total_xp"])
    badge_ekstra = []
    if sebelumnya == "Perlu Remedial" and hasil["klasifikasi"]["status_rule"] == "Tuntas":
        badge_ekstra.append("Remedial Cleared")
        hasil["gamifikasi"]["badge"].append("Remedial Cleared")

    baru = store.catat(player_id, level_kuis, hasil, streak, today.isoformat(), badge_ekstra)
    hasil["gamifikasi"]["badge_baru"] = [b for b in hasil["gamifikasi"]["badge"] if b not in p["badges"]]
    hasil["gamifikasi"]["level_terbuka_baru"] = baru["max_unlocked"] > p["max_unlocked"]
    hasil["gamifikasi"]["streak_hari"] = streak
    hasil["pemain"] = ringkasan_pemain(store, baru)
    return hasil


def nilai_kuis(level, jawaban, duration_seconds, feedback_views):
    """Menilai kuis di sisi server. jawaban = [{question_id, selected_index|None, hint_digunakan}]"""
    if not jawaban:
        raise ValueError("Daftar jawaban kosong")
    ids = [j["question_id"] for j in jawaban]
    if len(set(ids)) != len(ids):
        raise ValueError("Ada soal yang dikirim dua kali")
    benar = dijawab = hint = 0
    review = []
    for j in jawaban:
        soal = questions.BANK.get(j["question_id"])
        if soal is None:
            raise ValueError(f"Soal {j['question_id']} tidak dikenal")
        if soal["level"] != level:
            raise ValueError(f"Soal {j['question_id']} bukan soal level {level}")
        idx = j.get("selected_index")
        if idx is not None:
            if not 0 <= idx < len(soal["options"]):
                raise ValueError(f"Pilihan jawaban untuk {j['question_id']} di luar rentang")
            dijawab += 1
            ok, _, kunci = questions.periksa(j["question_id"], idx)
            benar += int(ok)
        else:
            ok, kunci = False, soal["answer"]
        hint += int(bool(j.get("hint_digunakan")))
        review.append({"question_id": j["question_id"], "benar": ok, "jawaban_benar": kunci})
    data = {
        "question_count": len(jawaban), "answered_questions": dijawab, "correct_answers": benar,
        "duration_seconds": max(float(duration_seconds), 1.0), "hint_count": hint,
        "attempt_count": 1, "streak_days": 0, "game_level": level,
        "feedback_frequency": min(int(feedback_views), len(jawaban)),
    }
    return data, review
