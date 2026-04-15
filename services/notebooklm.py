from notebooklm import NotebookLMClient


async def get_client():
    """
    FastAPI dependency que fornece um NotebookLMClient por request.
    Usa async with para garantir que cookies de sessão sejam gerenciados
    corretamente pelo context manager da biblioteca.
    """
    async with await NotebookLMClient.from_storage() as client:
        yield client
