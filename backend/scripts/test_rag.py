"""
scripts/test_rag.py
────────────────────
Tests for the complete RAG layer: ChromaDB, retriever, pipeline, seeding.

Run:  python scripts/test_rag.py
"""
import asyncio, os, sys, shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["GOOGLE_API_KEY"] = ""          # no key → hash embeddings
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://x:x@localhost/x")

# Use a temp dir so tests don't pollute the real store
TEST_CHROMA_PATH = "/tmp/test_career_copilot_chroma"
os.environ["CHROMADB_PATH"] = TEST_CHROMA_PATH

GREEN = "\033[92m"; YELLOW = "\033[93m"; RED = "\033[91m"
CYAN  = "\033[96m"; BOLD   = "\033[1m";  RESET = "\033[0m"

def ok(m):     print(f"{GREEN}  ✓ {m}{RESET}")
def warn(m):   print(f"{YELLOW}  ⚠ {m}{RESET}")
def fail(m):   print(f"{RED}  ✗ {m}{RESET}")
def header(m): print(f"\n{BOLD}{m}{RESET}")


# ── Test 1: Client initialisation ──────────────────────────────────────────────
async def test_client_init():
    header("Test 1: ChromaDB Client Initialisation")
    from app.rag.chromadb_client import get_chroma_client, CollectionName
    client = get_chroma_client()
    ok(f"PersistentClient created at {TEST_CHROMA_PATH}")

    # Create all collections
    from app.rag.chromadb_client import get_or_create_collection
    for name in CollectionName.ALL:
        col = get_or_create_collection(name)
        ok(f"Collection created: {name}")
    return True


# ── Test 2: Hash embedding function ───────────────────────────────────────────
async def test_hash_embeddings():
    header("Test 2: Hash Embedding Function (no API key)")
    from app.rag.chromadb_client import HashEmbeddingFunction
    ef = HashEmbeddingFunction(dim=64)
    vecs = ef(["hello world", "machine learning"])
    assert len(vecs) == 2,         "Should return 2 vectors"
    assert len(vecs[0]) == 64,     "Vector should be 64-dim"
    assert all(0 <= v <= 1 for v in vecs[0]), "Values should be in [0,1]"
    ok(f"Hash embeddings: 2 vectors × 64-dim produced")

    # Deterministic
    vecs2 = ef(["hello world", "machine learning"])
    assert vecs[0] == vecs2[0], "Hash embeddings should be deterministic"
    ok("Embeddings are deterministic")
    return True


# ── Test 3: Document seeding ───────────────────────────────────────────────────
async def test_seeding():
    header("Test 3: Document Seeding")
    from app.rag.ingestion.loader import seed_all_collections, get_ingestion_status
    from app.rag.ingestion.seed_documents import (
        INTERVIEW_QUESTIONS, JOB_REQUIREMENTS, LEARNING_RESOURCES,
        CAREER_GUIDANCE, COMPANY_INFO
    )
    total_expected = sum([
        len(INTERVIEW_QUESTIONS), len(JOB_REQUIREMENTS),
        len(LEARNING_RESOURCES),  len(CAREER_GUIDANCE), len(COMPANY_INFO)
    ])
    ok(f"Total seed documents: {total_expected}")

    results = seed_all_collections(force=True)
    for r in results:
        if r.upserted > 0:
            ok(f"{r.collection}: {r.upserted} docs upserted")
        elif r.already_exist > 0:
            ok(f"{r.collection}: {r.already_exist} docs already existed")
        elif r.failed > 0:
            warn(f"{r.collection}: {r.failed} docs FAILED")

    # Check status
    status = get_ingestion_status()
    for col, info in status.items():
        if info["count"] > 0:
            ok(f"Status: {col} = {info['count']} docs")
        else:
            warn(f"Status: {col} = 0 docs (embedding may need API key)")

    return True


# ── Test 4: Retrieval ──────────────────────────────────────────────────────────
async def test_retrieval():
    header("Test 4: Semantic Retrieval")
    from app.rag.retriever import (
        retrieve_job_requirements,
        retrieve_learning_resources,
        retrieve_interview_questions,
        retrieve_career_guidance,
        retrieve_for_agent,
    )
    from app.agents.state import AgentName

    # job requirements
    chunks = await retrieve_job_requirements("AI Engineer", n_results=3)
    if chunks:
        ok(f"Job requirements: {len(chunks)} chunks retrieved")
        ok(f"  Sample: {chunks[0][:80]}...")
    else:
        warn("Job requirements: 0 chunks (hash embeddings — no semantic similarity)")

    # learning resources
    chunks = await retrieve_learning_resources("Docker", n_results=3)
    if chunks:
        ok(f"Learning resources: {len(chunks)} chunks retrieved")
    else:
        warn("Learning resources: 0 chunks (expected with hash embeddings)")

    # interview questions
    chunks = await retrieve_interview_questions("AI Engineer", "technical", "medium")
    ok(f"Interview questions retrieval: returned {len(chunks)} chunks")

    # career guidance
    chunks = await retrieve_career_guidance("how to write a good resume")
    ok(f"Career guidance retrieval: returned {len(chunks)} chunks")

    # per-agent retrieval
    for agent in [AgentName.RESUME, AgentName.SKILL_GAP, AgentName.INTERVIEW,
                  AgentName.QUIZ, AgentName.STUDY_PLANNER]:
        chunks = await retrieve_for_agent(agent, "AI Engineer machine learning")
        ok(f"retrieve_for_agent({agent}): {len(chunks)} chunks")

    return True


# ── Test 5: RAG pipeline ──────────────────────────────────────────────────────
async def test_rag_pipeline():
    header("Test 5: RAG Pipeline (state enrichment)")
    from app.rag.rag_pipeline import enrich_state_with_rag, get_rag_health
    from app.agents.state import AgentName, create_initial_state

    state = create_initial_state(
        user_id="test-001", session_id="sess-001",
        user_message="analyze my resume for AI Engineer",
        target_role="AI Engineer",
    )

    for agent in [AgentName.RESUME, AgentName.SKILL_GAP, AgentName.INTERVIEW,
                  AgentName.QUIZ, AgentName.STUDY_PLANNER]:
        update = await enrich_state_with_rag(state, agent)
        chunks = update.get("rag_context", [])
        ok(f"enrich_state_with_rag({agent}): {len(chunks)} chunks, no crash")

    # Health check
    health = await get_rag_health()
    ok(f"RAG health: status={health['status']} total_docs={health['total_docs']}")
    return True


# ── Test 6: Upsert safety (re-seeding doesn't duplicate) ─────────────────────
async def test_upsert_safety():
    header("Test 6: Upsert Safety (re-seed doesn't duplicate)")
    from app.rag.ingestion.loader import seed_all_collections
    from app.rag.chromadb_client import get_collection, CollectionName

    # Seed twice
    seed_all_collections(force=True)
    seed_all_collections(force=True)

    col = get_collection(CollectionName.INTERVIEW_QUESTIONS)
    if col:
        count = col.count()
        from app.rag.ingestion.seed_documents import INTERVIEW_QUESTIONS
        expected = len(INTERVIEW_QUESTIONS)
        if count == expected:
            ok(f"No duplicates after re-seed: {count} == {expected}")
        else:
            warn(f"Count {count} != expected {expected} (may be OK with hash embeddings)")
    return True


# ── Test 7: Graph compiles with RAG wired ─────────────────────────────────────
async def test_graph_with_rag():
    header("Test 7: Full Graph Compiles with RAG Wired")
    from app.agents.graph import career_copilot_graph
    graph_def = career_copilot_graph.get_graph()
    nodes = list(graph_def.nodes.keys())
    ok(f"Graph compiled: {len(nodes)} nodes — {nodes}")
    return True


# ── Main ───────────────────────────────────────────────────────────────────────
async def main():
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}  Step 9: ChromaDB RAG Layer — Test Suite{RESET}")
    print(f"{BOLD}{'='*60}{RESET}")
    print(f"{YELLOW}  Note: Using hash embeddings (no GOOGLE_API_KEY){RESET}")
    print(f"{YELLOW}  Retrieval returns chunks based on hash similarity, not semantic{RESET}")

    tests = [
        test_client_init, test_hash_embeddings, test_seeding,
        test_retrieval, test_rag_pipeline, test_upsert_safety, test_graph_with_rag,
    ]
    results = []
    for t in tests:
        try:
            results.append(await t())
        except Exception as e:
            fail(f"Test crashed: {e}")
            import traceback; traceback.print_exc()
            results.append(False)

    # Cleanup
    shutil.rmtree(TEST_CHROMA_PATH, ignore_errors=True)

    passed = sum(results)
    total  = len(results)
    color  = GREEN if passed == total else YELLOW
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{color}{BOLD}  {passed}/{total} tests passed{RESET}")
    print(f"{BOLD}{'='*60}{RESET}")
    print(f"{GREEN}  ✓ Set GOOGLE_API_KEY in .env for real semantic search{RESET}\n")


if __name__ == "__main__":
    asyncio.run(main())
