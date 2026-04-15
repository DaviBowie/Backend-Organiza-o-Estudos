from fastapi import APIRouter, Depends, HTTPException
from notebooklm import NotebookLMClient

from schemas.models import CreateNotebookRequest, RenameNotebookRequest
from services.notebooklm import get_client

router = APIRouter()


@router.get("")
@router.get("/")
async def list_notebooks(client: NotebookLMClient = Depends(get_client)):
    notebooks = await client.notebooks.list()
    return notebooks


@router.post("", status_code=201)
@router.post("/", status_code=201)
async def create_notebook(
    body: CreateNotebookRequest,
    client: NotebookLMClient = Depends(get_client),
):
    notebook = await client.notebooks.create(body.title)
    return notebook


@router.get("/{notebook_id}")
async def get_notebook(
    notebook_id: str,
    client: NotebookLMClient = Depends(get_client),
):
    notebook = await client.notebooks.get(notebook_id)
    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook não encontrado")
    return notebook


@router.put("/{notebook_id}")
async def rename_notebook(
    notebook_id: str,
    body: RenameNotebookRequest,
    client: NotebookLMClient = Depends(get_client),
):
    notebook = await client.notebooks.rename(notebook_id, body.title)
    return notebook


@router.delete("/{notebook_id}", status_code=204)
async def delete_notebook(
    notebook_id: str,
    client: NotebookLMClient = Depends(get_client),
):
    await client.notebooks.delete(notebook_id)
