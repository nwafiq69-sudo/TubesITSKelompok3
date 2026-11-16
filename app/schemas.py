"""Skema validasi masukan (Pydantic v2) = lapisan validasi pertama sebelum masuk engine."""
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

_ANGKA = ("question_count", "answered_questions", "correct_answers", "duration_seconds", "hint_count",
          "attempt_count", "streak_days", "game_level", "feedback_frequency")


class ProcessRequest(BaseModel):
    """Metrik satu kali pengerjaan kuis (endpoint POST /api/process)."""
    model_config = ConfigDict(extra="forbid")  # nama field salah (typo) ditolak

    question_count: int = Field(gt=0, le=200, description="Jumlah soal pada kuis")
    answered_questions: int = Field(ge=0, le=200, description="Jumlah soal yang dijawab")
    correct_answers: int = Field(ge=0, le=200, description="Jumlah jawaban benar")
    duration_seconds: float = Field(gt=0, le=86400, description="Durasi pengerjaan (detik)")
    hint_count: int = Field(ge=0, le=200, description="Jumlah hint yang dipakai")
    attempt_count: int = Field(ge=1, le=100, description="Percobaan ke-berapa")
    streak_days: int = Field(ge=0, le=3650, description="Streak belajar (hari)")
    game_level: int = Field(ge=1, le=5, description="Level kuis saat ini (1-5)")
    feedback_frequency: int = Field(ge=0, le=200, description="Berapa kali umpan balik dibuka")
    player_id: Optional[str] = Field(default=None, max_length=32,
                                     description="Opsional. Jika diisi, profil & leaderboard diperbarui")

    @field_validator(*_ANGKA, mode="before")
    @classmethod
    def harus_angka(cls, v, info):
        # tolak teks, boolean, dan null (Pydantic mode lax biasanya mengonversi "5" -> 5)
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise ValueError(f"'{info.field_name}' harus berupa angka")
        return v

    @model_validator(mode="after")
    def cek_konsistensi(self):
        if self.answered_questions > self.question_count:
            raise ValueError("answered_questions melebihi question_count")
        if self.correct_answers > self.answered_questions:
            raise ValueError("correct_answers melebihi answered_questions")
        return self


class PlayerCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=2, max_length=30)

    @field_validator("name")
    @classmethod
    def bersihkan(cls, v):
        v = " ".join(v.split())
        if len(v) < 2:
            raise ValueError("Nama minimal 2 karakter")
        return v


class CheckRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question_id: str = Field(min_length=1, max_length=10)
    selected_index: int = Field(ge=0, le=9)


class JawabanItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question_id: str = Field(min_length=1, max_length=10)
    selected_index: Optional[int] = Field(default=None, ge=0, le=9)
    hint_digunakan: bool = False


class QuizSubmitRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    player_id: str = Field(min_length=1, max_length=32)
    level: int = Field(ge=1, le=5)
    jawaban: List[JawabanItem] = Field(min_length=1, max_length=20)
    duration_seconds: float = Field(gt=0, le=86400)
    feedback_views: int = Field(ge=0, le=100)
