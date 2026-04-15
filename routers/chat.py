from fastapi import APIRouter, Depends
from notebooklm import NotebookLMClient

from schemas.models import AskQuestionRequest, AskResponse
from services.notebooklm import get_client

router = APIRouter()

PREFIX = "/{notebook_id}/chat"


@router.post(PREFIX + "/ask")
async def ask_question(
    notebook_id: str,
    body: AskQuestionRequest,
    client: NotebookLMClient = Depends(get_client),
):
    result = await client.chat.ask(
        notebook_id,
        body.question,
        conversation_id=body.conversation_id,
    )

    citations = []
    for ref in result.references:
        citations.append({
            "source_id": ref.source_id,
            "citation_number": ref.citation_number,
            "cited_text": ref.cited_text,
        })

    return AskResponse(
        answer=result.answer,
        conversation_id=result.conversation_id,
        citations=citations,
    )


@router.get(PREFIX + "/history")
async def get_chat_history(
    notebook_id: str,
    client: NotebookLMClient = Depends(get_client),
):
    notebook = await client.notebooks.get(notebook_id)
    return notebook
