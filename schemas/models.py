from pydantic import BaseModel
from typing import Any


# ── Notebook Requests ────────────────────────────────────────────────────────

class CreateNotebookRequest(BaseModel):
    title: str


class RenameNotebookRequest(BaseModel):
    title: str


# ── Source Requests ───────────────────────────────────────────────────────────

class AddUrlSourceRequest(BaseModel):
    url: str


class AddYouTubeSourceRequest(BaseModel):
    url: str


class AddTextSourceRequest(BaseModel):
    title: str
    content: str


# ── Chat Requests ─────────────────────────────────────────────────────────────

class AskQuestionRequest(BaseModel):
    question: str
    conversation_id: str | None = None


# ── Artifact Generation Requests ──────────────────────────────────────────────

class GenerateAudioRequest(BaseModel):
    instructions: str = ""
    format: str = "deep-dive"   # deep-dive | brief | critique | debate
    length: str = "medium"      # short | medium | long
    language: str = "pt"


class GenerateVideoRequest(BaseModel):
    instructions: str = ""
    format: str = "explainer"   # explainer | brief | cinematic
    style: str = ""
    language: str = "pt"


class GenerateQuizRequest(BaseModel):
    quantity: str = "default"   # default | more | less
    difficulty: str = "medium"  # easy | medium | hard


class GenerateFlashcardsRequest(BaseModel):
    quantity: str = "default"
    difficulty: str = "medium"


class GenerateSlideDeckRequest(BaseModel):
    format: str = "detailed"    # detailed | presenter
    length: str = "medium"
    language: str = "pt"


class GenerateInfographicRequest(BaseModel):
    orientation: str = "landscape"  # portrait | landscape | square
    detail: str = "medium"         # low | medium | high
    language: str = "pt"


class GenerateDataTableRequest(BaseModel):
    instructions: str
    language: str = "pt"


class GenerateReportRequest(BaseModel):
    format: str = "study-guide"    # briefing | study-guide | blog-post | custom
    custom_prompt: str = ""
    language: str = "pt"


# ── Responses ─────────────────────────────────────────────────────────────────

class DownloadResponse(BaseModel):
    filename: str
    url: str   # ex: /files/{notebook_id}/{filename}


class GenerationResponse(BaseModel):
    status: str
    task_id: str
    type: str


class AskResponse(BaseModel):
    answer: str
    conversation_id: str | None = None
    citations: list[Any] = []
