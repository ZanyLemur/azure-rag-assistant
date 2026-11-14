import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    HnswParameters,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
)
from openai import RateLimitError
from pypdf import PdfReader

from app import config
from app.clients import credential, openai_client, search_client

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
VECTOR_DIMS = 1536          # text-embedding-3-small
CHUNK_SIZE = 1000           # characters
CHUNK_OVERLAP = 150
EMBED_BATCH = 16
UPLOAD_BATCH = 100


def create_index():
    index_client = SearchIndexClient(config.SEARCH_ENDPOINT, credential)
    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SearchableField(name="content", type=SearchFieldDataType.String),
        SimpleField(
            name="source", type=SearchFieldDataType.String,
            filterable=True, facetable=True,
        ),
        SimpleField(
            name="page", type=SearchFieldDataType.Int32,
            filterable=True, sortable=True,
        ),
        SearchField(
            name="content_vector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=VECTOR_DIMS,
            vector_search_profile_name="vec-profile",
        ),
    ]
    vector_search = VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(
                name="hnsw", parameters=HnswParameters(metric="cosine")
            )
        ],
        profiles=[
            VectorSearchProfile(
                name="vec-profile", algorithm_configuration_name="hnsw"
            )
        ],
    )
    index = SearchIndex(
        name=config.SEARCH_INDEX, fields=fields, vector_search=vector_search
    )
    index_client.create_or_update_index(index)
    print(f"Index '{config.SEARCH_INDEX}' ready")


def chunk_text(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    chunks = []
    step = CHUNK_SIZE - CHUNK_OVERLAP
    for start in range(0, len(text), step):
        piece = text[start:start + CHUNK_SIZE].strip()
        if len(piece) > 50:
            chunks.append(piece)
    return chunks


def embed_batch(texts: list[str]) -> list[list[float]]:
    for attempt in range(6):
        try:
            response = openai_client.embeddings.create(
                model=config.EMBED_DEPLOYMENT, input=texts
            )
            return [d.embedding for d in response.data]
        except RateLimitError:
            wait = 2 ** attempt
            print(f"  rate limited, waiting {wait}s")
            time.sleep(wait)
    raise RuntimeError("Embedding kept hitting rate limits")


def safe_id(*parts) -> str:
    return re.sub(r"[^A-Za-z0-9_\-=]", "-", "-".join(str(p) for p in parts))


def build_chunks(pdf_path: Path) -> list[dict]:
    reader = PdfReader(str(pdf_path))
    records = []
    for page_num, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        for i, chunk in enumerate(chunk_text(text)):
            records.append({
                "id": safe_id(pdf_path.stem, page_num, i),
                "content": chunk,
                "source": pdf_path.name,
                "page": page_num,
            })
    return records


def upload(records: list[dict]):
    for start in range(0, len(records), EMBED_BATCH):
        batch = records[start:start + EMBED_BATCH]
        vectors = embed_batch([r["content"] for r in batch])
        for record, vector in zip(batch, vectors):
            record["content_vector"] = vector
    for start in range(0, len(records), UPLOAD_BATCH):
        search_client.upload_documents(records[start:start + UPLOAD_BATCH])
        print(f"  uploaded {min(start + UPLOAD_BATCH, len(records))}/{len(records)}")


def main():
    create_index()
    pdfs = sorted(RAW_DIR.glob("*.pdf"))
    if not pdfs:
        print(f"No PDFs found in {RAW_DIR}")
        return
    for pdf in pdfs:
        print(f"Processing {pdf.name}...")
        records = build_chunks(pdf)
        print(f"  {len(records)} chunks")
        if records:
            upload(records)
    print("Done")


if __name__ == "__main__":
    main()