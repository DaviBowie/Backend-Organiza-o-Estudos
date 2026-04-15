import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
import aiofiles
from notebooklm import NotebookLMClient

from schemas.models import AddUrlSourceRequest, AddYouTubeSourceRequest, AddTextSourceRequest
from services.notebooklm import get_client

router = APIRouter()

PREFIX = "/{notebook_id}/sources"


@router.get(PREFIX)
async def list_sources(
    notebook_id: str,
    client: NotebookLMClient = Depends(get_client),
):
    sources = await client.sources.list(notebook_id)
    return sources


@router.post(PREFIX + "/url", status_code=201)
async def add_url_source(
    notebook_id: str,
    body: AddUrlSourceRequest,
    client: NotebookLMClient = Depends(get_client),
):
    source = await client.sources.add_url(notebook_id, body.url, wait=True)
    return source


@router.post(PREFIX + "/youtube", status_code=201)
async def add_youtube_source(
    notebook_id: str,
    body: AddYouTubeSourceRequest,
    client: NotebookLMClient = Depends(get_client),
):
    source = await client.sources.add_youtube(notebook_id, body.url)
    return source


@router.post(PREFIX + "/text", status_code=201)
async def add_text_source(
    notebook_id: str,
    body: AddTextSourceRequest,
    client: NotebookLMClient = Depends(get_client),
):
    source = await client.sources.add_text(
        notebook_id, body.title, body.content, wait=True
    )
    return source


@router.post(PREFIX + "/file", status_code=201)
async def add_file_source(
    notebook_id: str,
    file: UploadFile = File(...),
    client: NotebookLMClient = Depends(get_client),
):
    suffix = Path(file.filename).suffix if file.filename else ""
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp_path = tmp.name

    try:
        async with aiofiles.open(tmp_path, "wb") as f:
            content = await file.read()
            await f.write(content)

        source = await client.sources.add_file(
            notebook_id,
            tmp_path,
            mime_type=file.content_type,
            wait=True,
        )
    finally:
        os.unlink(tmp_path)

    return source


@router.delete(PREFIX + "/{source_id}", status_code=204)
async def delete_source(
    notebook_id: str,
    source_id: str,
    client: NotebookLMClient = Depends(get_client),
):
    await client.sources.delete(notebook_id, source_id)


@router.get(PREFIX + "/{source_id}/fulltext")
async def get_source_fulltext(
    notebook_id: str,
    source_id: str,
    client: NotebookLMClient = Depends(get_client),
):
    fulltext = await client.sources.get_fulltext(notebook_id, source_id)
    if not fulltext:
        raise HTTPException(status_code=404, detail="Fonte não encontrada")
    return fulltext
