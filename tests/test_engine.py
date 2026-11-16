"""15 test case engine (sama dengan notebook) + validasi aturan.  Jalankan: python -m unittest discover tests -v"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import engine  # noqa: E402

CONTOH = {"question_count": 12, "answered_questions": 12, "correct_answers": 11, "duration_seconds": 540,
          "hint_count": 0, "attempt_count": 1, "streak_days": 3, "game_level": 3, "feedback_frequency": 3}


def base(**kw):
    d = dict(CONTOH)
    d.update(kw)
    return d


class TestEngineValid(unittest.TestCase):
    def test_T01_siswa_kuat(self):
        r = engine.proses_kuis(base())
        self.assertEqual(r["klasifikasi"]["status_rule"], "Tuntas")
        self.assertIn("High Achiever", r["gamifikasi"]["badge"])

    def test_T02_siswa_lemah(self):
        r = engine.proses_kuis(base(question_count=10, answered_questions=8, correct_answers=3,
                                    hint_count=4, streak_days=1, game_level=3))
        self.assertEqual(r["klasifikasi"]["status_rule"], "Perlu Remedial")
        self.assertEqual(r["umpan_balik"]["rekomendasi"], "Penguatan materi")
        self.assertEqual(r["gamifikasi"]["level_baru"], 2)

    def test_T03_batas_skor_75(self):
        r = engine.proses_kuis(base(question_count=8, answered_questions=8, correct_answers=6))
        self.assertEqual(r["klasifikasi"]["status_rule"], "Tuntas")

    def test_T04_skor_73_33(self):
        r = engine.proses_kuis(base(question_count=15, answered_questions=15, correct_answers=11))
        self.assertEqual(r["klasifikasi"]["status_rule"], "Perlu Remedial")

    def test_T12_streak_5_hari(self):
        r = engine.proses_kuis(base(streak_days=5))
        self.assertEqual(r["gamifikasi"]["rincian_xp"].get("bonus_streak"), 10)
        self.assertIn("Learning Streak", r["gamifikasi"]["badge"])

    def test_T13_percobaan_kedua(self):
        r = engine.proses_kuis(base(attempt_count=2))
        self.assertIn("Persistent Learner", r["gamifikasi"]["badge"])

    def test_T14_level_5_tetap_5(self):
        r = engine.proses_kuis(base(game_level=5, correct_answers=12, streak_days=4, feedback_frequency=4))
        self.assertEqual(r["umpan_balik"]["rekomendasi"], "Naikkan level")
        self.assertEqual(r["gamifikasi"]["level_baru"], 5)

    def test_T15_level_1_tetap_1(self):
        r = engine.proses_kuis(base(game_level=1, question_count=10, answered_questions=7,
                                    correct_answers=3, hint_count=4, streak_days=1))
        self.assertEqual(r["umpan_balik"]["rekomendasi"], "Penguatan materi")
        self.assertEqual(r["gamifikasi"]["level_baru"], 1)

    def test_total_xp_akumulatif(self):
        r = engine.proses_kuis(base(), total_xp_sebelumnya=60)
        self.assertEqual(r["gamifikasi"]["total_xp"], 60 + r["gamifikasi"]["xp_didapat"])

    def test_tidak_ada_jawaban_dijawab(self):
        r = engine.proses_kuis(base(answered_questions=0, correct_answers=0))
        self.assertEqual(r["hasil_kuis"]["akurasi"], 0.0)
        self.assertEqual(r["klasifikasi"]["status_rule"], "Perlu Remedial")


class TestEngineInvalid(unittest.TestCase):
    def assertDitolak(self, data):
        with self.assertRaises(ValueError):
            engine.proses_kuis(data)

    def test_T05_typo_field(self):
        d = {k: v for k, v in base().items() if k != "correct_answers"}
        d["correct_answer"] = 11
        self.assertDitolak(d)

    def test_T06_field_hilang(self):
        self.assertDitolak({k: v for k, v in base().items() if k != "duration_seconds"})

    def test_T07_durasi_negatif(self):
        self.assertDitolak(base(duration_seconds=-10))

    def test_T08_benar_melebihi_dijawab(self):
        self.assertDitolak(base(answered_questions=10, correct_answers=11))

    def test_T09_level_di_luar_rentang(self):
        self.assertDitolak(base(game_level=9))

    def test_T10_tipe_teks(self):
        self.assertDitolak(base(hint_count="banyak"))

    def test_T11_bukan_dict(self):
        self.assertDitolak(None)


class TestAturanDataset(unittest.TestCase):
    """Aturan dibandingkan dengan dataset asli (reproduksi validasi notebook)."""

    def test_aturan_cocok_dengan_dataset(self):
        import pandas as pd
        df = pd.read_csv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                      "data", "dataset_gamified_its_1000.csv"))
        self.assertGreaterEqual((df["quiz_score"].map(engine.status_rule) == df["learning_status"]).mean(), 0.999)
        rek = df.apply(lambda r: engine.rekomendasi_adaptif(r.engagement_score, r.accuracy,
                                                            r.learning_status, r.game_level), axis=1)
        self.assertGreaterEqual((rek.map(lambda t: t[0]) == df["adaptive_recommendation"]).mean(), 0.99)
        self.assertGreaterEqual((rek.map(lambda t: t[1]) == df["recommended_level"]).mean(), 0.99)

    def test_info_rank(self):
        from app.gamify import info_rank
        self.assertEqual(info_rank(0)["rank"], "Pemula")
        self.assertEqual(info_rank(75)["rank"], "Penjelajah")
        self.assertEqual(info_rank(75)["persen"], 25)
        self.assertEqual(info_rank(9999)["rank_berikutnya"], None)


if __name__ == "__main__":
    unittest.main()
