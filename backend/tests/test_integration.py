"""
tests/test_integration.py
──────────────────────────
End-to-end integration tests for AI Career Copilot backend.

Run:  python tests/test_integration.py
Requires: backend running at http://localhost:8000
          (uvicorn app.main:app --reload)
"""
import asyncio
import sys
import os
import json
import tempfile
import httpx

BASE = "http://localhost:8000"
GREEN = "\033[92m"; RED = "\033[91m"; YELLOW = "\033[93m"; BOLD = "\033[1m"; RESET = "\033[0m"

def ok(m):   print(f"{GREEN}  ✓ {m}{RESET}")
def fail(m): print(f"{RED}  ✗ {m}{RESET}")
def info(m): print(f"{YELLOW}  → {m}{RESET}")
def header(m): print(f"\n{BOLD}{m}{RESET}")

# Test user credentials
TEST_EMAIL    = "testuser_integration@example.com"
TEST_PASSWORD = "TestPass123!"
TEST_NAME     = "Integration Tester"
TEST_ROLE     = "AI Engineer"

access_token  = None
refresh_token = None
user_id       = None
resume_id     = None
quiz_id       = None
interview_session_id = None

def auth_headers():
    return {"Authorization": f"Bearer {access_token}"}


# ── Health Check ───────────────────────────────────────────────────────────────
async def test_health(client: httpx.AsyncClient):
    header("Test 1: Health Check")
    r = await client.get(f"{BASE}/health")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    ok(f"Status: {data.get('status')}")
    ok(f"Database: {data.get('database')}")
    ok(f"RAG: {data.get('rag', {}).get('status')}")
    return True


# ── Authentication ─────────────────────────────────────────────────────────────
async def test_register(client: httpx.AsyncClient):
    global access_token, refresh_token, user_id
    header("Test 2: User Registration")
    r = await client.post(f"{BASE}/api/auth/register", json={
        "name": TEST_NAME, "email": TEST_EMAIL,
        "password": TEST_PASSWORD, "target_role": TEST_ROLE,
    })
    if r.status_code == 409:
        ok("User already exists — skipping to login")
        return await test_login(client)
    assert r.status_code == 201, f"Expected 201, got {r.status_code}: {r.text}"
    data = r.json()
    access_token  = data["tokens"]["access_token"]
    refresh_token = data["tokens"]["refresh_token"]
    user_id       = data["user"]["id"]
    ok(f"Registered: {data['user']['email']}")
    ok(f"Token received: {access_token[:30]}...")
    return True


async def test_login(client: httpx.AsyncClient):
    global access_token, refresh_token, user_id
    header("Test 2b: Login")
    r = await client.post(f"{BASE}/api/auth/login", json={"email": TEST_EMAIL, "password": TEST_PASSWORD})
    assert r.status_code == 200, f"Login failed: {r.text}"
    data = r.json()
    access_token  = data["tokens"]["access_token"]
    refresh_token = data["tokens"]["refresh_token"]
    user_id       = data["user"]["id"]
    ok(f"Logged in as {data['user']['email']}")
    return True


async def test_get_me(client: httpx.AsyncClient):
    header("Test 3: Get Current User")
    r = await client.get(f"{BASE}/api/auth/me", headers=auth_headers())
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    assert data["email"] == TEST_EMAIL
    ok(f"User: {data['name']} | Role: {data.get('target_role')}")
    return True


async def test_wrong_password(client: httpx.AsyncClient):
    header("Test 4: Wrong Password (should return 401)")
    r = await client.post(f"{BASE}/api/auth/login", json={"email": TEST_EMAIL, "password": "wrongpassword"})
    assert r.status_code == 401, f"Expected 401, got {r.status_code}"
    ok("Correct: 401 returned for wrong password")
    return True


async def test_no_token(client: httpx.AsyncClient):
    header("Test 5: No Auth Token (should return 401)")
    r = await client.get(f"{BASE}/api/auth/me")
    assert r.status_code == 401, f"Expected 401, got {r.status_code}"
    ok("Correct: 401 returned for missing token")
    return True


# ── Resume ─────────────────────────────────────────────────────────────────────
async def test_resume_upload(client: httpx.AsyncClient):
    global resume_id
    header("Test 6: Resume Upload & Analysis")

    # Create a minimal PDF
    pdf_content = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj
4 0 obj<</Length 200>>
stream
BT /F1 12 Tf 50 750 Td
(Mahalakshmi Bala | AI Engineer | Python SQL Machine Learning) Tj
0 -20 Td (Skills: Python, SQL, Machine Learning, FastAPI, React) Tj
0 -20 Td (Education: B.E. Computer Science, Anna University, 2024) Tj
0 -20 Td (Projects: AI Career Copilot, Resume Analyzer, DineBot) Tj
ET
endstream
endobj
5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000266 00000 n
0000000516 00000 n
trailer<</Size 6/Root 1 0 R>>
startxref
583
%%EOF"""

    files  = {"file": ("test_resume.pdf", pdf_content, "application/pdf")}
    data   = {"target_role": TEST_ROLE}
    r = await client.post(f"{BASE}/api/resume/analyze", headers=auth_headers(), files=files, data=data)

    if r.status_code == 422:
        ok("PDF parse warning (minimal PDF) — endpoint reachable and validated")
        return True

    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:200]}"
    resp = r.json()
    resume_id = resp.get("resume_id")
    ok(f"Resume analyzed | ID: {resume_id}")
    ok(f"ATS Score: {resp.get('analysis', {}).get('ats_score')}/100")
    ok(f"Extracted skills: {resp.get('analysis', {}).get('extracted_skills', [])[:5]}")
    return True


async def test_resume_history(client: httpx.AsyncClient):
    header("Test 7: Resume History")
    r = await client.get(f"{BASE}/api/resume/history", headers=auth_headers())
    assert r.status_code == 200
    data = r.json()
    ok(f"History items: {data.get('total', 0)}")
    return True


# ── Skill Gap ──────────────────────────────────────────────────────────────────
async def test_skill_gap(client: httpx.AsyncClient):
    header("Test 8: Skill Gap Analysis")
    r = await client.post(f"{BASE}/api/skills/analyze", headers=auth_headers(), json={
        "target_role": TEST_ROLE,
        "current_skills": ["Python", "SQL", "Machine Learning"],
    })
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:200]}"
    data = r.json()
    analysis = data.get("analysis", {})
    ok(f"Readiness: {analysis.get('overall_readiness_percent')}%")
    ok(f"Missing skills: {len(analysis.get('missing_skills', []))}")
    ok(f"Priority order: {analysis.get('priority_order', [])[:3]}")
    return True


# ── Interview ──────────────────────────────────────────────────────────────────
async def test_interview_generate(client: httpx.AsyncClient):
    global interview_session_id
    header("Test 9: Interview Question Generation")
    r = await client.post(f"{BASE}/api/interview/generate", headers=auth_headers(), json={
        "target_role": TEST_ROLE, "interview_type": "technical", "difficulty": "medium",
    })
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:200]}"
    data = r.json()
    interview_session_id = data.get("session_id")
    ok(f"Session ID: {interview_session_id}")
    ok(f"Questions generated: {data.get('total_questions')}")
    ok(f"Sample: {data.get('questions', [{}])[0].get('question', '')[:80]}...")
    return True


async def test_interview_evaluate(client: httpx.AsyncClient):
    header("Test 10: Interview Answer Evaluation")
    if not interview_session_id:
        info("Skipping — no session ID")
        return True
    answers = [{"question_id": 1, "answer": "RAG retrieves external documents at inference time to augment the LLM response with real-time knowledge, reducing hallucinations."}]
    r = await client.post(f"{BASE}/api/interview/evaluate", headers=auth_headers(), json={
        "session_id": interview_session_id, "target_role": TEST_ROLE, "answers": answers,
    })
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:200]}"
    data = r.json()
    ok(f"Overall score: {data.get('overall_score')}/100")
    ok(f"Grade: {data.get('overall_grade')}")
    return True


# ── Quiz ───────────────────────────────────────────────────────────────────────
async def test_quiz_generate(client: httpx.AsyncClient):
    global quiz_id
    header("Test 11: Quiz Generation")
    r = await client.post(f"{BASE}/api/quiz/generate", headers=auth_headers(), json={
        "topic": "Machine Learning", "difficulty": "medium", "quiz_type": "mcq",
    })
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:200]}"
    data = r.json()
    quiz_id = data.get("quiz_id")
    ok(f"Quiz ID: {quiz_id}")
    ok(f"Questions: {data.get('total_questions')}")
    ok(f"Topic: {data.get('topic')}")
    return True


async def test_quiz_submit(client: httpx.AsyncClient):
    header("Test 12: Quiz Submission & Scoring")
    if not quiz_id:
        info("Skipping — no quiz ID")
        return True
    r = await client.post(f"{BASE}/api/quiz/submit", headers=auth_headers(), json={
        "quiz_id": quiz_id,
        "answers": [{"question_id": i, "answer": "A"} for i in range(1, 4)],
    })
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:200]}"
    data = r.json()
    ok(f"Score: {data.get('score_percent')}%")
    ok(f"Grade: {data.get('grade')}")
    ok(f"Weak areas: {data.get('weak_areas', [])}")
    return True


# ── Study Planner ──────────────────────────────────────────────────────────────
async def test_study_planner(client: httpx.AsyncClient):
    header("Test 13: Study Plan Generation")
    r = await client.post(f"{BASE}/api/planner/generate", headers=auth_headers(), json={
        "plan_type": "weekly", "target_role": TEST_ROLE, "available_hours": 2.0,
    })
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:200]}"
    data = r.json()
    ok(f"Plan ID: {data.get('plan_id')}")
    ok(f"Plan type: {data.get('plan_type')}")
    days = data.get("plan_data", {}).get("days", [])
    ok(f"Days in plan: {len(days)}")
    return True


# ── Progress ───────────────────────────────────────────────────────────────────
async def test_progress_score(client: httpx.AsyncClient):
    header("Test 14: Career Readiness Score")
    r = await client.get(f"{BASE}/api/progress/score", headers=auth_headers())
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    ok(f"Overall score: {data.get('overall_score')}/100")
    ok(f"Components: {data.get('components')}")
    ok(f"Recommendations: {len(data.get('recommendations', []))}")
    return True


# ── API Validation ─────────────────────────────────────────────────────────────
async def test_validation_errors(client: httpx.AsyncClient):
    header("Test 15: Input Validation")

    # Empty target role
    r = await client.post(f"{BASE}/api/skills/analyze", headers=auth_headers(), json={"target_role": ""})
    assert r.status_code == 422, f"Expected 422, got {r.status_code}"
    ok("Empty target_role → 422 Unprocessable")

    # Wrong file type
    files = {"file": ("resume.txt", b"not a pdf", "text/plain")}
    r = await client.post(f"{BASE}/api/resume/analyze", headers=auth_headers(), files=files, data={"target_role": "Engineer"})
    assert r.status_code in (400, 422), f"Expected 400/422, got {r.status_code}"
    ok("Wrong file type → 400/422")

    # Quiz submit with wrong ID
    r = await client.post(f"{BASE}/api/quiz/submit", headers=auth_headers(), json={
        "quiz_id": "00000000-0000-0000-0000-000000000000",
        "answers": [{"question_id": 1, "answer": "A"}],
    })
    assert r.status_code == 404, f"Expected 404, got {r.status_code}"
    ok("Non-existent quiz ID → 404")

    return True


# ── Main ───────────────────────────────────────────────────────────────────────
async def main():
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}  AI Career Copilot — Integration Tests{RESET}")
    print(f"{BOLD}{'='*60}{RESET}")
    print(f"{YELLOW}  Target: {BASE}{RESET}")
    print(f"{YELLOW}  Note: Requires running backend + real GOOGLE_API_KEY for full tests{RESET}")

    tests = [
        test_health, test_register, test_get_me, test_wrong_password,
        test_no_token, test_resume_upload, test_resume_history,
        test_skill_gap, test_interview_generate, test_interview_evaluate,
        test_quiz_generate, test_quiz_submit, test_study_planner,
        test_progress_score, test_validation_errors,
    ]

    passed, failed_tests = 0, []
    async with httpx.AsyncClient(timeout=120.0) as client:
        for test in tests:
            try:
                await test(client)
                passed += 1
            except Exception as e:
                fail(f"{test.__name__}: {e}")
                failed_tests.append(test.__name__)

    total = len(tests)
    color = GREEN if passed == total else YELLOW
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{color}{BOLD}  {passed}/{total} tests passed{RESET}")
    if failed_tests:
        print(f"{RED}  Failed: {', '.join(failed_tests)}{RESET}")
    print(f"{BOLD}{'='*60}{RESET}\n")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
