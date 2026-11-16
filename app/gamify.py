"""Utilitas gamifikasi di luar aturan inti dataset: rank XP, progress bar, streak harian."""
from datetime import date, timedelta

# (batas XP minimal, nama rank)
RANKS = [(0, "Pemula"), (50, "Penjelajah"), (150, "Pejuang"), (300, "Ahli"), (600, "Legenda")]


def info_rank(xp):
    """Rank saat ini + progress menuju rank berikutnya (untuk progress bar)."""
    xp = max(int(xp), 0)
    idx = 0
    for i, (batas, _) in enumerate(RANKS):
        if xp >= batas:
            idx = i
    nama = RANKS[idx][1]
    if idx == len(RANKS) - 1:
        return {"rank": nama, "rank_berikutnya": None, "xp_rank_ini": RANKS[idx][0],
                "xp_target": None, "persen": 100}
    batas_ini, batas_next = RANKS[idx][0], RANKS[idx + 1][0]
    persen = round((xp - batas_ini) / (batas_next - batas_ini) * 100)
    return {"rank": nama, "rank_berikutnya": RANKS[idx + 1][1], "xp_rank_ini": batas_ini,
            "xp_target": batas_next, "persen": persen}


def hitung_streak(streak_terakhir, last_active, today):
    """Streak untuk aktivitas HARI INI.
    - main lagi di hari yang sama -> streak tidak bertambah
    - main sehari setelah aktivitas terakhir -> streak + 1
    - jeda lebih dari sehari / pemain baru -> mulai lagi dari 1
    """
    if not last_active:
        return 1
    terakhir = date.fromisoformat(last_active)
    if terakhir == today:
        return max(int(streak_terakhir), 1)
    if terakhir == today - timedelta(days=1):
        return int(streak_terakhir) + 1
    return 1
