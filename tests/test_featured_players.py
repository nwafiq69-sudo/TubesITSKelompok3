"""Tiga profil podium harus dapat dipilih tanpa membuat akun kosong atau riwayat duplikat."""
import os
import unittest

from app.store import Store


CSV = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "dataset_gamified_its_1000.csv")
FEATURED = (
    ("Arif Anggraini", "STD047", 198, 97.0),
    ("Naufal Lestari", "STD139", 181, 94.0),
    ("Dimas Wijaya", "STD057", 176, 92.67),
)


class TestFeaturedPlayers(unittest.TestCase):
    def test_tiga_nama_memakai_profil_dan_riwayat_dataset(self):
        store = Store(":memory:")
        self.assertEqual(store.seed_dari_csv(CSV), 200)
        for name, player_id, xp, average in FEATURED:
            with self.subTest(name=name):
                player = store.buat_atau_ambil("  " + name.upper() + "  ")
                self.assertEqual((player["id"], player["total_xp"], player["level"], player["avg_score"]),
                                 (player_id, xp, 5, average))
                self.assertEqual(len(store.riwayat(player_id)), 5)
        self.assertEqual(store.seed_dari_csv(CSV), 0)
        self.assertEqual(store.leaderboard(limit=0)["total_pemain"], 200)
        self.assertTrue(all(len(store.riwayat(player_id)) == 5 for _, player_id, _, _ in FEATURED))

    def test_database_yang_sudah_ada_mendapat_tiga_profil(self):
        store = Store(":memory:")
        store.buat_atau_ambil("Pemain Lama")
        self.assertEqual(store.seed_dari_csv(CSV), 3)
        self.assertEqual(store.leaderboard(limit=0)["total_pemain"], 4)
        self.assertEqual(store.buat_atau_ambil("Arif Anggraini")["id"], "STD047")


if __name__ == "__main__":
    unittest.main()
