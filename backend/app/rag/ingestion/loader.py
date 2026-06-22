"""
app/rag/ingestion/loader.py
────────────────────────────
ChromaDB ingestion pipeline.

Responsibilities
─────────────────
  1. Load all SeedDocument objects from seed_documents.py
  2. Embed them using the configured embedding function (Gemini or hash fallback)
  3. Insert into the correct ChromaDB collection
  4. Handle re-seeding safely (upsert not duplicate)
  5. Report what was loaded

When is this called?
─────────────────────
  - Once on first deploy:  `python scripts/seed_chromadb.py`
  - During FastAPI startup: if collections are empty, auto-seed runs
  - Manually to refresh:   `python scripts/seed_chromadb.py --force`

Upsert safety
──────────────
ChromaDB's collection.upsert() updates if the doc_id already exists,
inserts if it doesn't. This means re-running the seed script is safe —
it will update changed documents without creating duplicates.
"""

import logging
from dataclasses import dataclass

from app.rag.chromadb_client import (
    CollectionName,
    get_chroma_client,
    get_embedding_function,
)
from app.rag.ingestion.seed_documents import (
    CAREER_GUIDANCE,
    COMPANY_INFO,
    INTERVIEW_QUESTIONS,
    JOB_REQUIREMENTS,
    LEARNING_RESOURCES,
    SeedDocument,
)
from app.rag.ingestion.phase2_seed_documents import (
    LINKEDIN_TEMPLATES,
    PROJECT_TEMPLATES,
    ENGLISH_TEMPLATES,
)
from app.rag.ingestion.phase3_seed_documents import (
    COMPANY_INFORMATION,
    INTERNSHIP_INFORMATION,
    WELLNESS_RESOURCES,
)

logger = logging.getLogger(__name__)

# Map collection name → seed document list
COLLECTION_SEED_MAP: dict[str, list[SeedDocument]] = {
    CollectionName.INTERVIEW_QUESTIONS: INTERVIEW_QUESTIONS,
    CollectionName.JOB_REQUIREMENTS:    JOB_REQUIREMENTS,
    CollectionName.LEARNING_RESOURCES:  LEARNING_RESOURCES,
    CollectionName.CAREER_GUIDANCE:     CAREER_GUIDANCE,
    CollectionName.COMPANY_INFO:        COMPANY_INFO,
    # Phase 2
    CollectionName.LINKEDIN_TEMPLATES:  LINKEDIN_TEMPLATES,
    CollectionName.PROJECT_TEMPLATES:   PROJECT_TEMPLATES,
    CollectionName.ENGLISH_TEMPLATES:   ENGLISH_TEMPLATES,
    # Phase 3
    CollectionName.COMPANY_INFORMATION:    COMPANY_INFORMATION,
    CollectionName.INTERNSHIP_INFORMATION: INTERNSHIP_INFORMATION,
    CollectionName.WELLNESS_RESOURCES:     WELLNESS_RESOURCES,
}


@dataclass
class IngestionResult:
    collection:    str
    total_docs:    int
    upserted:      int
    already_exist: int
    failed:        int
    success:       bool


def seed_all_collections(force: bool = False) -> list[IngestionResult]:
    """
    Seed all ChromaDB collections from the seed documents.

    Args:
        force: If True, upsert all docs even if collections already have data.
               If False, skip collections that already have documents.

    Returns:
        List of IngestionResult, one per collection.
    """
    results = []
    ef = get_embedding_function()
    client = get_chroma_client()

    for col_name, docs in COLLECTION_SEED_MAP.items():
        result = _seed_collection(
            client=client,
            collection_name=col_name,
            documents=docs,
            embedding_function=ef,
            force=force,
        )
        results.append(result)
        _log_result(result)

    total_upserted = sum(r.upserted for r in results)
    total_docs = sum(r.total_docs for r in results)
    logger.info(
        f"[Ingestion] Complete: {total_upserted}/{total_docs} documents "
        f"across {len(results)} collections"
    )
    return results


def _seed_collection(
    client,
    collection_name: str,
    documents: list[SeedDocument],
    embedding_function,
    force: bool,
) -> IngestionResult:
    """Seed one collection with upsert safety."""

    if not documents:
        return IngestionResult(
            collection=collection_name,
            total_docs=0, upserted=0, already_exist=0, failed=0, success=True,
        )

    try:
        # get_or_create with cosine similarity space
        col = client.get_or_create_collection(
            name=collection_name,
            embedding_function=embedding_function,
            metadata={"hnsw:space": "cosine"},
        )

        existing_count = col.count()

        # Skip if already seeded and not forcing
        if existing_count >= len(documents) and not force:
            logger.info(
                f"[Ingestion] '{collection_name}' already has {existing_count} docs — skipping"
            )
            return IngestionResult(
                collection=collection_name,
                total_docs=len(documents),
                upserted=0,
                already_exist=existing_count,
                failed=0,
                success=True,
            )

        # Batch upsert in chunks of 50 to avoid memory issues
        BATCH_SIZE = 50
        upserted = 0
        failed = 0

        for i in range(0, len(documents), BATCH_SIZE):
            batch = documents[i : i + BATCH_SIZE]
            try:
                col.upsert(
                    ids       = [doc.doc_id for doc in batch],
                    documents = [doc.content for doc in batch],
                    metadatas = [doc.metadata for doc in batch],
                )
                upserted += len(batch)
                logger.debug(
                    f"[Ingestion] '{collection_name}' batch {i//BATCH_SIZE + 1}: "
                    f"upserted {len(batch)} docs"
                )
            except Exception as e:
                logger.error(
                    f"[Ingestion] Batch failed for '{collection_name}' "
                    f"at index {i}: {e}"
                )
                failed += len(batch)

        return IngestionResult(
            collection=collection_name,
            total_docs=len(documents),
            upserted=upserted,
            already_exist=existing_count,
            failed=failed,
            success=failed == 0,
        )

    except Exception as e:
        logger.error(f"[Ingestion] Collection '{collection_name}' failed: {e}")
        return IngestionResult(
            collection=collection_name,
            total_docs=len(documents),
            upserted=0, already_exist=0, failed=len(documents), success=False,
        )


def get_ingestion_status() -> dict[str, dict]:
    """
    Return document counts for all collections.
    Used by /health endpoint and admin dashboard.
    """
    client = get_chroma_client()
    status = {}

    for col_name in COLLECTION_SEED_MAP:
        try:
            col = client.get_collection(col_name)
            count = col.count()
            expected = len(COLLECTION_SEED_MAP[col_name])
            status[col_name] = {
                "count":    count,
                "expected": expected,
                "seeded":   count >= expected,
            }
        except Exception:
            status[col_name] = {
                "count": 0, "expected": len(COLLECTION_SEED_MAP[col_name]), "seeded": False,
            }

    return status


def _log_result(result: IngestionResult) -> None:
    symbol = "✓" if result.success else "✗"
    logger.info(
        f"[Ingestion] {symbol} {result.collection}: "
        f"upserted={result.upserted} already={result.already_exist} "
        f"failed={result.failed} total={result.total_docs}"
    )
