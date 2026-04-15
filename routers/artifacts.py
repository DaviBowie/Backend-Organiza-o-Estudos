import os
import asyncio
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from notebooklm import NotebookLMClient
from notebooklm.rpc.types import (
    AudioFormat,
    AudioLength,
    VideoFormat,
    VideoStyle,
    ReportFormat,
    QuizQuantity,
    QuizDifficulty,
    SlideDeckFormat,
    SlideDeckLength,
    InfographicOrientation,
    InfographicDetail,
)

from schemas.models import (
    DownloadResponse,
    GenerationResponse,
    GenerateAudioRequest,
    GenerateVideoRequest,
    GenerateQuizRequest,
    GenerateFlashcardsRequest,
    GenerateSlideDeckRequest,
    GenerateInfographicRequest,
    GenerateDataTableRequest,
    GenerateReportRequest,
)
from services.notebooklm import get_client

router = APIRouter()

PREFIX = "/{notebook_id}/artifacts"
GENERATION_TIMEOUT = 300.0  # 5 minutos


def _download_dir(notebook_id: str) -> Path:
    base = Path(os.getenv("DOWNLOAD_DIR", "./downloads"))
    d = base / notebook_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def _filename(artifact_type: str, ext: str) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{artifact_type}_{ts}.{ext}"


def _download_url(notebook_id: str, filename: str) -> str:
    return f"/files/{notebook_id}/{filename}"


def _map_audio_format(fmt: str) -> AudioFormat:
    return {
        "deep-dive": AudioFormat.DEEP_DIVE,
        "brief": AudioFormat.BRIEF,
        "critique": AudioFormat.CRITIQUE,
        "debate": AudioFormat.DEBATE,
    }.get(fmt, AudioFormat.DEEP_DIVE)


def _map_audio_length(length: str) -> AudioLength:
    return {
        "short": AudioLength.SHORT,
        "medium": AudioLength.DEFAULT,
        "long": AudioLength.LONG,
    }.get(length, AudioLength.DEFAULT)


def _map_video_format(fmt: str) -> VideoFormat:
    return {
        "explainer": VideoFormat.EXPLAINER,
        "brief": VideoFormat.BRIEF,
        "cinematic": VideoFormat.CINEMATIC,
    }.get(fmt, VideoFormat.EXPLAINER)


def _map_quiz_quantity(qty: str) -> QuizQuantity:
    return {
        "less": QuizQuantity.FEWER,
        "default": QuizQuantity.STANDARD,
        "more": QuizQuantity.STANDARD,
    }.get(qty, QuizQuantity.STANDARD)


def _map_quiz_difficulty(diff: str) -> QuizDifficulty:
    return {
        "easy": QuizDifficulty.EASY,
        "medium": QuizDifficulty.MEDIUM,
        "hard": QuizDifficulty.HARD,
    }.get(diff, QuizDifficulty.MEDIUM)


def _map_slide_format(fmt: str) -> SlideDeckFormat:
    return {
        "detailed": SlideDeckFormat.DETAILED_DECK,
        "presenter": SlideDeckFormat.PRESENTER_SLIDES,
    }.get(fmt, SlideDeckFormat.DETAILED_DECK)


def _map_slide_length(length: str) -> SlideDeckLength:
    return {
        "medium": SlideDeckLength.DEFAULT,
        "short": SlideDeckLength.SHORT,
    }.get(length, SlideDeckLength.DEFAULT)


def _map_infographic_orientation(orientation: str) -> InfographicOrientation:
    return {
        "portrait": InfographicOrientation.PORTRAIT,
        "landscape": InfographicOrientation.LANDSCAPE,
        "square": InfographicOrientation.SQUARE,
    }.get(orientation, InfographicOrientation.PORTRAIT)


def _map_infographic_detail(detail: str) -> InfographicDetail:
    return {
        "low": InfographicDetail.CONCISE,
        "medium": InfographicDetail.STANDARD,
        "high": InfographicDetail.DETAILED,
    }.get(detail, InfographicDetail.STANDARD)


def _map_report_format(fmt: str) -> ReportFormat:
    return {
        "briefing": ReportFormat.BRIEFING_DOC,
        "study-guide": ReportFormat.STUDY_GUIDE,
        "blog-post": ReportFormat.BLOG_POST,
        "custom": ReportFormat.CUSTOM,
    }.get(fmt, ReportFormat.STUDY_GUIDE)


async def _wait(client: NotebookLMClient, notebook_id: str, task_id: str):
    try:
        status = await client.artifacts.wait_for_completion(
            notebook_id, task_id, timeout=GENERATION_TIMEOUT
        )
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail={"error": "Timeout na geração do artefato", "detail": f"task_id={task_id}"},
        )
    if status.is_failed:
        raise HTTPException(
            status_code=500,
            detail={"error": "Falha na geração do artefato", "detail": status.error or ""},
        )
    return status


# ── Geração ───────────────────────────────────────────────────────────────────

@router.post(PREFIX + "/audio")
async def generate_audio(
    notebook_id: str,
    body: GenerateAudioRequest,
    client: NotebookLMClient = Depends(get_client),
):
    status = await client.artifacts.generate_audio(
        notebook_id,
        instructions=body.instructions or None,
        audio_format=_map_audio_format(body.format),
        audio_length=_map_audio_length(body.length),
        language=body.language,
    )
    await _wait(client, notebook_id, status.task_id)
    return GenerationResponse(status="completed", task_id=status.task_id, type="audio")


@router.post(PREFIX + "/video")
async def generate_video(
    notebook_id: str,
    body: GenerateVideoRequest,
    client: NotebookLMClient = Depends(get_client),
):
    status = await client.artifacts.generate_video(
        notebook_id,
        instructions=body.instructions or None,
        video_format=_map_video_format(body.format),
        language=body.language,
    )
    await _wait(client, notebook_id, status.task_id)
    return GenerationResponse(status="completed", task_id=status.task_id, type="video")


@router.post(PREFIX + "/quiz")
async def generate_quiz(
    notebook_id: str,
    body: GenerateQuizRequest,
    client: NotebookLMClient = Depends(get_client),
):
    status = await client.artifacts.generate_quiz(
        notebook_id,
        quantity=_map_quiz_quantity(body.quantity),
        difficulty=_map_quiz_difficulty(body.difficulty),
    )
    await _wait(client, notebook_id, status.task_id)
    return GenerationResponse(status="completed", task_id=status.task_id, type="quiz")


@router.post(PREFIX + "/flashcards")
async def generate_flashcards(
    notebook_id: str,
    body: GenerateFlashcardsRequest,
    client: NotebookLMClient = Depends(get_client),
):
    status = await client.artifacts.generate_flashcards(
        notebook_id,
        quantity=_map_quiz_quantity(body.quantity),
        difficulty=_map_quiz_difficulty(body.difficulty),
    )
    await _wait(client, notebook_id, status.task_id)
    return GenerationResponse(status="completed", task_id=status.task_id, type="flashcards")


@router.post(PREFIX + "/slide-deck")
async def generate_slide_deck(
    notebook_id: str,
    body: GenerateSlideDeckRequest,
    client: NotebookLMClient = Depends(get_client),
):
    status = await client.artifacts.generate_slide_deck(
        notebook_id,
        slide_format=_map_slide_format(body.format),
        slide_length=_map_slide_length(body.length),
        language=body.language,
    )
    await _wait(client, notebook_id, status.task_id)
    return GenerationResponse(status="completed", task_id=status.task_id, type="slide-deck")


@router.post(PREFIX + "/infographic")
async def generate_infographic(
    notebook_id: str,
    body: GenerateInfographicRequest,
    client: NotebookLMClient = Depends(get_client),
):
    status = await client.artifacts.generate_infographic(
        notebook_id,
        orientation=_map_infographic_orientation(body.orientation),
        detail_level=_map_infographic_detail(body.detail),
        language=body.language,
    )
    await _wait(client, notebook_id, status.task_id)
    return GenerationResponse(status="completed", task_id=status.task_id, type="infographic")


@router.post(PREFIX + "/mind-map")
async def generate_mind_map(
    notebook_id: str,
    client: NotebookLMClient = Depends(get_client),
):
    # generate_mind_map retorna dict diretamente, sem GenerationStatus
    data = await client.artifacts.generate_mind_map(notebook_id)
    return {"status": "completed", "task_id": None, "type": "mind-map", "data": data}


@router.post(PREFIX + "/data-table")
async def generate_data_table(
    notebook_id: str,
    body: GenerateDataTableRequest,
    client: NotebookLMClient = Depends(get_client),
):
    status = await client.artifacts.generate_data_table(
        notebook_id,
        instructions=body.instructions,
        language=body.language,
    )
    await _wait(client, notebook_id, status.task_id)
    return GenerationResponse(status="completed", task_id=status.task_id, type="data-table")


@router.post(PREFIX + "/report")
async def generate_report(
    notebook_id: str,
    body: GenerateReportRequest,
    client: NotebookLMClient = Depends(get_client),
):
    status = await client.artifacts.generate_report(
        notebook_id,
        report_format=_map_report_format(body.format),
        custom_prompt=body.custom_prompt or None,
        language=body.language,
    )
    await _wait(client, notebook_id, status.task_id)
    return GenerationResponse(status="completed", task_id=status.task_id, type="report")


# ── Downloads ─────────────────────────────────────────────────────────────────

@router.get(PREFIX + "/download/audio")
async def download_audio(
    notebook_id: str,
    client: NotebookLMClient = Depends(get_client),
):
    filename = _filename("audio", "mp3")
    output = str(_download_dir(notebook_id) / filename)
    await client.artifacts.download_audio(notebook_id, output)
    return DownloadResponse(filename=filename, url=_download_url(notebook_id, filename))


@router.get(PREFIX + "/download/video")
async def download_video(
    notebook_id: str,
    client: NotebookLMClient = Depends(get_client),
):
    filename = _filename("video", "mp4")
    output = str(_download_dir(notebook_id) / filename)
    await client.artifacts.download_video(notebook_id, output)
    return DownloadResponse(filename=filename, url=_download_url(notebook_id, filename))


@router.get(PREFIX + "/download/quiz")
async def download_quiz(
    notebook_id: str,
    format: str = Query(default="json", pattern="^(json|markdown|html)$"),
    client: NotebookLMClient = Depends(get_client),
):
    ext = {"json": "json", "markdown": "md", "html": "html"}[format]
    filename = _filename("quiz", ext)
    output = str(_download_dir(notebook_id) / filename)
    await client.artifacts.download_quiz(notebook_id, output, output_format=format)
    return DownloadResponse(filename=filename, url=_download_url(notebook_id, filename))


@router.get(PREFIX + "/download/flashcards")
async def download_flashcards(
    notebook_id: str,
    format: str = Query(default="json", pattern="^(json|markdown|html)$"),
    client: NotebookLMClient = Depends(get_client),
):
    ext = {"json": "json", "markdown": "md", "html": "html"}[format]
    filename = _filename("flashcards", ext)
    output = str(_download_dir(notebook_id) / filename)
    await client.artifacts.download_flashcards(notebook_id, output, output_format=format)
    return DownloadResponse(filename=filename, url=_download_url(notebook_id, filename))


@router.get(PREFIX + "/download/slide-deck")
async def download_slide_deck(
    notebook_id: str,
    format: str = Query(default="pdf", pattern="^(pdf|pptx)$"),
    client: NotebookLMClient = Depends(get_client),
):
    filename = _filename("slide_deck", format)
    output = str(_download_dir(notebook_id) / filename)
    await client.artifacts.download_slide_deck(notebook_id, output, output_format=format)
    return DownloadResponse(filename=filename, url=_download_url(notebook_id, filename))


@router.get(PREFIX + "/download/infographic")
async def download_infographic(
    notebook_id: str,
    client: NotebookLMClient = Depends(get_client),
):
    filename = _filename("infographic", "png")
    output = str(_download_dir(notebook_id) / filename)
    await client.artifacts.download_infographic(notebook_id, output)
    return DownloadResponse(filename=filename, url=_download_url(notebook_id, filename))


@router.get(PREFIX + "/download/mind-map")
async def download_mind_map(
    notebook_id: str,
    client: NotebookLMClient = Depends(get_client),
):
    filename = _filename("mind_map", "json")
    output = str(_download_dir(notebook_id) / filename)
    await client.artifacts.download_mind_map(notebook_id, output)
    return DownloadResponse(filename=filename, url=_download_url(notebook_id, filename))


@router.get(PREFIX + "/download/data-table")
async def download_data_table(
    notebook_id: str,
    client: NotebookLMClient = Depends(get_client),
):
    filename = _filename("data_table", "csv")
    output = str(_download_dir(notebook_id) / filename)
    await client.artifacts.download_data_table(notebook_id, output)
    return DownloadResponse(filename=filename, url=_download_url(notebook_id, filename))


@router.get(PREFIX + "/download/report")
async def download_report(
    notebook_id: str,
    client: NotebookLMClient = Depends(get_client),
):
    filename = _filename("report", "md")
    output = str(_download_dir(notebook_id) / filename)
    await client.artifacts.download_report(notebook_id, output)
    return DownloadResponse(filename=filename, url=_download_url(notebook_id, filename))
