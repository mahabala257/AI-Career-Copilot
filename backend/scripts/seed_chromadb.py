"""
scripts/seed_chromadb.py
─────────────────────────
Standalone ChromaDB seeding script.

Usage:
    python scripts/seed_chromadb.py           # seed only empty collections
    python scripts/seed_chromadb.py --force   # re-seed all collections
    python scripts/seed_chromadb.py --status  # show current counts only
"""
import argparse
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("GOOGLE_API_KEY",  "fake-key-for-hash-mode")
os.environ.setdefault("DATABASE_URL",    "postgresql+asyncpg://x:x@localhost/x")

GREEN = "\033[92m"; YELLOW = "\033[93m"; RED = "\033[91m"
CYAN  = "\033[96m"; BOLD   = "\033[1m";  RESET = "\033[0m"


def run_seed(force: bool = False):
    from app.rag.ingestion.loader import get_ingestion_status, seed_all_collections

    print(f"\n{BOLD}AI Career Copilot — ChromaDB Seeding{RESET}")
    print(f"Mode: {'FORCE RE-SEED' if force else 'SKIP IF SEEDED'}\n")

    results = seed_all_collections(force=force)

    print(f"\n{BOLD}Results:{RESET}")
    for r in results:
        icon  = f"{GREEN}✓{RESET}" if r.success else f"{RED}✗{RESET}"
        print(f"  {icon} {r.collection:<30} upserted={r.upserted:>3}  total={r.total_docs:>3}")

    total = sum(r.upserted for r in results)
    print(f"\n{GREEN if total > 0 else YELLOW}{BOLD}Total upserted: {total} documents{RESET}\n")


def show_status():
    from app.rag.ingestion.loader import get_ingestion_status

    print(f"\n{BOLD}ChromaDB Collection Status:{RESET}\n")
    status = get_ingestion_status()
    for col, info in status.items():
        icon = f"{GREEN}✓{RESET}" if info["seeded"] else f"{YELLOW}⚠{RESET}"
        print(f"  {icon} {col:<30} count={info['count']:>3} / expected={info['expected']:>3}")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--force",  action="store_true", help="Re-seed all collections")
    parser.add_argument("--status", action="store_true", help="Show status only")
    args = parser.parse_args()

    if args.status:
        show_status()
    else:
        run_seed(force=args.force)
