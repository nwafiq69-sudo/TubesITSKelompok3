"""Uji alur stateful: pemain, streak, level unlock, badge remedial, penilaian kuis, leaderboard."""
import os
import sys
import unittest
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from app import questions, service  # noqa: E402
from app.store import Store  # noqa: E402


def metrik(level=1, benar=6, total=6, hint=0, durasi=300, fb=0):
    return {"question_count": total, "answered_questions": total, "correct_answers": benar,
            "duration_seconds": durasi, "hint_count": hint, "attempt_count": 1, "streak_days": 0,
            "game_level": level, "feedback_frequency": fb}


class TestService(unittest.TestCase):
    def setUp(self):
        self.s = Store(":memory:")
        self.s.seed_dari_csv(os.path.join(ROOT, "data", "dataset_gamified_its_1000.csv"))
        self.p = self.s.buat_atau_ambil("Budi Santoso")

    def test_seed_200_siswa(self):
        self.assertEqual(self.s.leaderboard(limit=0)["total_pemain"], 201)  # 200 seed + Budi

    def test_login_nama_sama_profil_sama(self):
        self.assertEqual(self.s.buat_atau_ambil("  budi   santoso ")["id"], self.p["id"])

    def test_pemain_baru_awal(self):
        self.assertEqual((self.p["total_xp"], self.p["level"], self.p["max_unlocked"]), (0, 1, 1))

    def test_kuis_pertama_memberi_xp_dan_streak_1(self):
        r = service.jalankan(self.s, metrik(), self.p["id"], today=date(2026, 11, 16))
        self.assertGreater(r["gamifikasi"]["xp_didapat"], 0)
        self.assertEqual(r["gamifikasi"]["streak_hari"], 1)
        self.assertEqual(r["pemain"]["total_xp"], r["gamifikasi"]["xp_didapat"])
        self.assertEqual(r["pemain"]["jumlah_kuis"], 1)

    def test_streak_naik_hari_berurutan_dan_reset_jika_bolong(self):
        for hari, harap in [(16, 1), (17, 2), (17, 2), (18, 3), (25, 1)]:
            r = service.jalankan(self.s, metrik(), self.p["id"], today=date(2026, 11, hari))
            self.assertEqual(r["gamifikasi"]["streak_hari"], harap, f"hari {hari}")

    def test_badge_learning_streak_di_hari_ketiga(self):
        for hari in (16, 17, 18):
            r = service.jalankan(self.s, metrik(), self.p["id"], today=date(2026, 11, hari))
        self.assertIn("Learning Streak", r["gamifikasi"]["badge"])
        self.assertIn("Persistent Learner", r["gamifikasi"]["badge"])  # percobaan ke-3 di level 1

    def test_level_unlock_saat_performa_tinggi(self):
        # skor 100, akurasi 100, engagement tinggi (streak + feedback) -> naik ke level 2
        for hari in (16, 17, 18):
            r = service.jalankan(self.s, metrik(fb=3), self.p["id"], today=date(2026, 11, hari))
        self.assertEqual(r["umpan_balik"]["rekomendasi"], "Naikkan level")
        self.assertTrue(r["gamifikasi"]["level_terbuka_baru"] or r["pemain"]["level_terbuka"] >= 2)
        self.assertGreaterEqual(r["pemain"]["level_terbuka"], 2)

    def test_badge_remedial_cleared(self):
        service.jalankan(self.s, metrik(benar=2, hint=3), self.p["id"], today=date(2026, 11, 16))
        r = service.jalankan(self.s, metrik(benar=6), self.p["id"], today=date(2026, 11, 16))
        self.assertIn("Remedial Cleared", r["gamifikasi"]["badge"])
        self.assertIn("Remedial Cleared", r["gamifikasi"]["badge_baru"])

    def test_tidak_ada_badge_remedial_jika_sebelumnya_lulus(self):
        service.jalankan(self.s, metrik(benar=6), self.p["id"], today=date(2026, 11, 16))
        r = service.jalankan(self.s, metrik(benar=6), self.p["id"], today=date(2026, 11, 16))
        self.assertNotIn("Remedial Cleared", r["gamifikasi"]["badge"])

    def test_pemain_tidak_dikenal(self):
        with self.assertRaises(service.PemainTidakAda):
            service.jalankan(self.s, metrik(), "XXX", today=date(2026, 11, 16))

    def test_stateless_tanpa_player_id(self):
        r = service.jalankan(self.s, metrik())
        self.assertIsNone(r["pemain"])

    def test_leaderboard_diperbarui(self):
        before = self.s.leaderboard(limit=1, player_id=self.p["id"])["posisi_kamu"]["rank"]
        for hari in range(1, 6):
            service.jalankan(self.s, metrik(fb=3), self.p["id"], today=date(2026, 12, hari))
        after = self.s.leaderboard(limit=1, player_id=self.p["id"])["posisi_kamu"]
        self.assertLess(after["rank"], before)
        self.assertEqual(self.s.ambil(self.p["id"])["attempts"], 5)


class TestNilaiKuis(unittest.TestCase):
    def soal_level(self, level):
        return [s for s in questions.BANK.values() if s["level"] == level][:6]

    def test_semua_benar(self):
        ss = self.soal_level(2)
        jw = [{"question_id": s["id"], "selected_index": s["answer"], "hint_digunakan": False} for s in ss]
        data, review = service.nilai_kuis(2, jw, 200, 1)
        self.assertEqual((data["correct_answers"], data["answered_questions"], data["question_count"]), (6, 6, 6))
        self.assertTrue(all(r["benar"] for r in review))

    def test_sebagian_kosong_dan_hint(self):
        ss = self.soal_level(1)
        jw = [{"question_id": ss[0]["id"], "selected_index": ss[0]["answer"], "hint_digunakan": True},
              {"question_id": ss[1]["id"], "selected_index": (ss[1]["answer"] + 1) % 4, "hint_digunakan": False},
              {"question_id": ss[2]["id"], "selected_index": None, "hint_digunakan": True}]
        data, _ = service.nilai_kuis(1, jw, 90, 2)
        self.assertEqual((data["correct_answers"], data["answered_questions"], data["hint_count"]), (1, 2, 2))

    def test_soal_level_salah_ditolak(self):
        s = self.soal_level(3)[0]
        with self.assertRaises(ValueError):
            service.nilai_kuis(1, [{"question_id": s["id"], "selected_index": 0}], 10, 0)

    def test_soal_duplikat_ditolak(self):
        s = self.soal_level(1)[0]
        with self.assertRaises(ValueError):
            service.nilai_kuis(1, [{"question_id": s["id"], "selected_index": 0}] * 2, 10, 0)

    def test_soal_tidak_dikenal_ditolak(self):
        with self.assertRaises(ValueError):
            service.nilai_kuis(1, [{"question_id": "S999", "selected_index": 0}], 10, 0)

    def test_bank_soal_valid(self):
        for lv in range(1, 6):
            self.assertEqual(len(self.soal_level(lv)), 6)
        for s in questions.BANK.values():
            self.assertEqual(len(s["options"]), 4)
            self.assertIn(s["answer"], range(4))
        # soal yang dikirim ke klien tidak boleh membocorkan kunci
        for s in questions.soal_untuk_level(1):
            self.assertNotIn("answer", s)
            self.assertNotIn("explanation", s)


if __name__ == "__main__":
    unittest.main()
