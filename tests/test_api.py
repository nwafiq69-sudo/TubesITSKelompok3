"""Tes end-to-end HTTP (FastAPI TestClient). Butuh: pip install -r requirements.txt  (fastapi, httpx)
Jalankan: python -m unittest tests.test_api -v   (atau: pytest tests)"""
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

try:
    from fastapi.testclient import TestClient
    from app.main import create_app
    ADA = True
except (ImportError, RuntimeError):  # fastapi/httpx belum terpasang
    ADA = False

VALID = {"question_count": 12, "answered_questions": 12, "correct_answers": 11, "duration_seconds": 540,
         "hint_count": 0, "attempt_count": 1, "streak_days": 3, "game_level": 3, "feedback_frequency": 3}


@unittest.skipUnless(ADA, "fastapi/httpx belum terpasang")
class TestAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.c = TestClient(create_app(os.path.join(cls.tmp.name, "test.db")))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def post(self, body, path="/api/process"):
        return self.c.post(path, json=body)

    def test_A01_health(self):
        r = self.c.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "ok")

    def test_A02_process_valid(self):
        r = self.post(VALID)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["klasifikasi"]["status_rule"], "Tuntas")

    def test_A03_typo_field_ditolak(self):
        body = {k: v for k, v in VALID.items() if k != "correct_answers"}
        body["correct_answer"] = 11
        r = self.post(body)
        self.assertEqual(r.status_code, 422)
        self.assertEqual(r.json()["status"], "error")

    def test_A04_field_hilang(self):
        r = self.post({k: v for k, v in VALID.items() if k != "duration_seconds"})
        self.assertEqual(r.status_code, 422)
        self.assertIn("duration_seconds", [e["field"] for e in r.json()["errors"]])

    def test_A05_durasi_negatif(self):
        self.assertEqual(self.post({**VALID, "duration_seconds": -10}).status_code, 422)

    def test_A06_benar_melebihi_dijawab(self):
        self.assertEqual(self.post({**VALID, "answered_questions": 10, "correct_answers": 11}).status_code, 422)

    def test_A07_level_9(self):
        self.assertEqual(self.post({**VALID, "game_level": 9}).status_code, 422)

    def test_A08_tipe_teks(self):
        self.assertEqual(self.post({**VALID, "hint_count": "banyak"}).status_code, 422)

    def test_A09_boolean_ditolak(self):
        self.assertEqual(self.post({**VALID, "hint_count": True}).status_code, 422)

    def test_A10_pemain_tidak_ada(self):
        self.assertEqual(self.post({**VALID, "player_id": "TIDAKADA"}).status_code, 404)

    def test_A11_alur_pemain_lengkap(self):
        p = self.post({"name": "Tes Pemain"}, "/api/players").json()
        pid = p["id"]
        kuis = self.c.get(f"/api/quiz/1?player_id={pid}").json()
        self.assertEqual(len(kuis["soal"]), 6)
        self.assertNotIn("answer", kuis["soal"][0])
        from app import questions
        jawaban = [{"question_id": s["id"], "selected_index": questions.BANK[s["id"]]["answer"],
                    "hint_digunakan": False} for s in kuis["soal"]]
        r = self.post({"player_id": pid, "level": 1, "jawaban": jawaban, "duration_seconds": 200,
                       "feedback_views": 3}, "/api/quiz/submit")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["hasil_kuis"]["skor"], 100.0)
        self.assertGreater(r.json()["pemain"]["total_xp"], 0)

    def test_A12_level_terkunci(self):
        pid = self.post({"name": "Pemain Baru"}, "/api/players").json()["id"]
        self.assertEqual(self.c.get(f"/api/quiz/4?player_id={pid}").status_code, 403)

    def test_A13_leaderboard(self):
        d = self.c.get("/api/leaderboard?limit=5").json()
        self.assertEqual(len(d["top"]), 5)
        self.assertGreaterEqual(d["total_pemain"], 200)

    def test_A14_check_jawaban(self):
        r = self.post({"question_id": "S001", "selected_index": 1}, "/api/quiz/check")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["benar"])

    def test_A15_halaman_utama_ada_disclaimer(self):
        r = self.c.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("Academic Disclaimer", r.text)


if __name__ == "__main__":
    unittest.main()
