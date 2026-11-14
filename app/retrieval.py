from azure.search.documents.models import VectorizedQuery

from app import config
from app.clients import openai_client, search_client


def embed(text: str) -> list[float]:
    response = openai_client.embeddings.create(
        model=config.EMBED_DEPLOYMENT, input=text
    )
    return response.data[0].embedding


def retrieve(question: str, top_k: int = 5) -> list[dict]:
    vector_query = VectorizedQuery(
        vector=embed(question),
        k_nearest_neighbors=top_k,
        fields="content_vector",   # your vector field name
    )
    results = search_client.search(
        search_text=question,       # keyword half of hybrid search
        vector_queries=[vector_query],
        select=["content", "source", "page"],  # your field names
        top=top_k,
    )
    return [
        {
            "content": r["content"],
            "source": r["source"],
            "page": r.get("page"),
        }
        for r in results
    ]