"""Penyimpanan SQLite untuk profil pemain, riwayat percobaan, dan leaderboard.

Saat pertama kali dijalankan, tabel pemain diisi (seed) dari dataset: 200 siswa dengan
total_xp, level, dan badge dari percobaan terakhir mereka.
"""
import json
import os
import sqlite3
import threading
import uuid
from datetime import datetime

import pandas as pd

_LOCK = threading.Lock()

# Tiga profil contoh pada podium dapat dipilih sebagai pemain tanpa membuat akun duplikat.
FEATURED_PLAYERS = {
    "arif anggraini": "STD047",
    "naufal lestari": "STD139",
    "dimas wijaya": "STD057",
}

SKEMA = """
CREATE TABLE IF NOT EXISTS players (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, total_xp INTEGER NOT NULL DEFAULT 0,
    level INTEGER NOT NULL DEFAULT 1, max_unlocked INTEGER NOT NULL DEFAULT 1,
    streak INTEGER NOT NULL DEFAULT 0, last_active TEXT, badges TEXT NOT NULL DEFAULT '[]',
    avg_score REAL NOT NULL DEFAULT 0, attempts INTEGER NOT NULL DEFAULT 0,
    is_seed INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT, player_id TEXT NOT NULL, level INTEGER NOT NULL,
    score REAL NOT NULL, status TEXT NOT NULL, xp INTEGER NOT NULL, created_at TEXT NOT NULL
);
"""


class Store:
    def __init__(self, path):
        self.path = path
        if path != ":memory:":
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        self._mem = sqlite3.connect(":memory:", check_same_thread=False) if path == ":memory:" else None
        c = self._conn()
        c.executescript(SKEMA)
        c.commit()
        if self._mem is None:
            c.close()

    # koneksi: satu koneksi per operasi (atau satu koneksi bersama untuk :memory:)
    def _conn(self):
        if self._mem is not None:
            return self._mem
        c = sqlite3.connect(self.path)
        c.row_factory = sqlite3.Row
        return c

    def _run(self, sql, args=(), one=False, commit=False):
        with _LOCK:
            c = self._conn()
            c.row_factory = sqlite3.Row
            cur = c.execute(sql, args)
            rows = cur.fetchone() if one else cur.fetchall()
            if commit:
                c.commit()
            if self._mem is None:
                c.close()
            return rows

    # ------------------------------------------------------------ seed
    def seed_dari_csv(self, csv_path):
        df = pd.read_csv(csv_path).sort_values(["student_id", "quiz_start_time"])
        now = datetime.now().isoformat(timespec="seconds")
        seed_all = self._run("SELECT COUNT(*) AS n FROM players", one=True)["n"] == 0
        profiles = df if seed_all else df[df["student_id"].isin(FEATURED_PLAYERS.values())]
        inserted = 0
        with _LOCK:
            c = self._conn()
            for sid, g in profiles.groupby("student_id"):
                if c.execute("SELECT 1 FROM players WHERE id=?", (sid,)).fetchone():
                    continue
                akhir = g.iloc[-1]
                badges = set()
                for b in g["badge_earned"].dropna():
                    badges.update(x.strip() for x in str(b).split(";") if x.strip())
                streak = 0 if pd.isna(akhir["streak_days"]) else int(akhir["streak_days"])
                c.execute(
                    "INSERT INTO players (id,name,total_xp,level,max_unlocked,streak,last_active,badges,"
                    "avg_score,attempts,is_seed,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,1,?)",
                    (sid, akhir["student_name"], int(akhir["total_xp"]), int(akhir["recommended_level"]),
                     int(max(g["recommended_level"].max(), g["game_level"].max())), streak,
                     str(akhir["quiz_date"]), json.dumps(sorted(badges)),
                     round(float(g["quiz_score"].mean()), 2), len(g), now))
                inserted += 1

            # Profil podium juga memiliki riwayat yang bisa ditampilkan di dashboard.
            for sid, g in df[df["student_id"].isin(FEATURED_PLAYERS.values())].groupby("student_id"):
                if not c.execute("SELECT 1 FROM players WHERE id=?", (sid,)).fetchone():
                    continue
                for _, attempt in g.iterrows():
                    finished_at = datetime.fromisoformat(str(attempt["quiz_submit_time"])).isoformat(timespec="seconds")
                    exists = c.execute(
                        "SELECT 1 FROM attempts WHERE player_id=? AND created_at=?",
                        (sid, finished_at),
                    ).fetchone()
                    if not exists:
                        c.execute(
                            "INSERT INTO attempts (player_id,level,score,status,xp,created_at) VALUES (?,?,?,?,?,?)",
                            (sid, int(attempt["game_level"]), float(attempt["quiz_score"]),
                             str(attempt["learning_status"]), int(attempt["xp_earned"]), finished_at),
                        )
            c.commit()
            if self._mem is None:
                c.close()
        return inserted

    # ------------------------------------------------------------ pemain
    @staticmethod
    def _ke_dict(row):
        if row is None:
            return None
        d = dict(row)
        d["badges"] = json.loads(d["badges"])
        d["is_seed"] = bool(d["is_seed"])
        return d

    def buat_atau_ambil(self, nama):
        """Login nama yang sama melanjutkan profil; tiga nama podium memakai data contoh."""
        nama = " ".join(nama.split())
        featured_id = FEATURED_PLAYERS.get(nama.casefold())
        if featured_id:
            featured = self.ambil(featured_id)
            if featured:
                return featured
        row = self._run("SELECT * FROM players WHERE lower(name)=lower(?) AND is_seed=0", (nama,), one=True)
        if row:
            return self._ke_dict(row)
        pid = "P" + uuid.uuid4().hex[:6].upper()
        self._run("INSERT INTO players (id,name,created_at) VALUES (?,?,?)",
                  (pid, nama, datetime.now().isoformat(timespec="seconds")), commit=True)
        return self.ambil(pid)

    def ambil(self, player_id):
        return self._ke_dict(self._run("SELECT * FROM players WHERE id=?", (player_id,), one=True))

    def jumlah_percobaan(self, player_id, level):
        return self._run("SELECT COUNT(*) AS n FROM attempts WHERE player_id=? AND level=?",
                         (player_id, level), one=True)["n"]

    def status_terakhir(self, player_id, level):
        row = self._run("SELECT status FROM attempts WHERE player_id=? AND level=? ORDER BY id DESC LIMIT 1",
                        (player_id, level), one=True)
        return row["status"] if row else None

    def riwayat(self, player_id, limit=10):
        rows = self._run("SELECT level,score,status,xp,created_at FROM attempts WHERE player_id=? "
                         "ORDER BY id DESC LIMIT ?", (player_id, limit))
        return [dict(r) for r in rows]

    def level_pernah_dikerjakan(self, player_id):
        rows = self._run("SELECT DISTINCT level FROM attempts WHERE player_id=? ORDER BY level", (player_id,))
        return [r["level"] for r in rows]

    def catat(self, player_id, level_kuis, hasil, streak, today_iso, badge_baru=None):
        """Menyimpan hasil satu kuis ke profil pemain. Mengembalikan profil terbaru."""
        p = self.ambil(player_id)
        g = hasil["gamifikasi"]
        skor = hasil["hasil_kuis"]["skor"]
        badges = sorted(set(p["badges"]) | set(g["badge"]) | set(badge_baru or []))
        n_baru = p["attempts"] + 1
        avg = round((p["avg_score"] * p["attempts"] + skor) / n_baru, 2)
        self._run(
            "UPDATE players SET total_xp=?, level=?, max_unlocked=?, streak=?, last_active=?, badges=?, "
            "avg_score=?, attempts=? WHERE id=?",
            (p["total_xp"] + g["xp_didapat"], g["level_baru"], max(p["max_unlocked"], g["level_baru"]),
             streak, today_iso, json.dumps(badges), avg, n_baru, player_id), commit=True)
        self._run("INSERT INTO attempts (player_id,level,score,status,xp,created_at) VALUES (?,?,?,?,?,?)",
                  (player_id, level_kuis, skor, hasil["klasifikasi"]["status_rule"], g["xp_didapat"],
                   datetime.now().isoformat(timespec="seconds")), commit=True)
        return self.ambil(player_id)

    # ------------------------------------------------------------ leaderboard
    def leaderboard(self, limit=10, player_id=None):
        """Urut: total XP, lalu rata-rata skor. Mengembalikan top-N + posisi pemain."""
        rows = self._run("SELECT id,name,total_xp,level,avg_score,attempts FROM players "
                         "ORDER BY total_xp DESC, avg_score DESC, name ASC")
        semua = [dict(r) for r in rows]
        for i, r in enumerate(semua, start=1):
            r["rank"] = i
        posisi = next((r for r in semua if r["id"] == player_id), None)
        return {"top": semua[:limit], "total_pemain": len(semua), "posisi_kamu": posisi}
