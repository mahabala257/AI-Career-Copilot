"""
app/rag/ingestion/phase2_seed_documents.py
───────────────────────────────────────────
Seed documents for the three Phase 2 RAG collections:

  linkedin_templates    — Headline examples, About section templates,
                          STAR bullet rewrites, keyword lists by role
  project_templates     — 40+ project ideas with full metadata:
                          difficulty, stack, interview value, role fit
  english_templates     — Vocabulary upgrades, filler words, model HR
                          answers, STAR format examples, grammar patterns

Design principles (same as Phase 1 seed_documents.py):
  - Each chunk = one self-contained piece of knowledge
  - Metadata enables filtered retrieval (role, difficulty, context_type)
  - Content is written to be directly usable in prompts
  - doc_ids are stable — re-seeding with upsert() is always safe
"""

from app.rag.ingestion.seed_documents import SeedDocument


# ─────────────────────────────────────────────────────────────────────────────
# COLLECTION 1 — linkedin_templates
# ─────────────────────────────────────────────────────────────────────────────

LINKEDIN_TEMPLATES: list[SeedDocument] = [

    # ── Headline templates ────────────────────────────────────────────────────
    SeedDocument(
        doc_id="lt_headline_ai_001",
        content=(
            "LinkedIn Headline Template — AI/ML Engineer (Experienced):\n"
            "Pattern: [Primary Role] | [Top 3 Keywords] | [Value Statement]\n"
            "Example: 'AI Engineer | LangChain · FastAPI · LLMs | "
            "Building production-grade AI systems that ship'\n"
            "Why it works: (1) Role first — recruiters scan fast. "
            "(2) Pipe separators create visual hierarchy. "
            "(3) Keywords 'LangChain', 'FastAPI', 'LLMs' are searchable. "
            "(4) Value statement differentiates from generic 'AI Engineer at XYZ'.\n"
            "Anti-pattern: 'B.Tech CSE | Passionate about technology | "
            "Open to opportunities' — this matches zero recruiter searches."
        ),
        metadata={"section_type": "headline", "role_category": "ai_ml",
                  "experience_level": "mid", "category": "linkedin_template"},
    ),
    SeedDocument(
        doc_id="lt_headline_ai_002",
        content=(
            "LinkedIn Headline Template — AI/ML Engineer (Fresher):\n"
            "Pattern: [Role Target] | [Technical Skills] | [Differentiator]\n"
            "Example: 'Aspiring AI Engineer | Python · TensorFlow · NLP | "
            "Final Year CSE @ NIT Trichy | Published IEEE paper on Transformers'\n"
            "Why it works: Specific institution + achievement differentiates "
            "among thousands of 'aspiring AI engineers'.\n"
            "Example 2: 'ML Engineer Fresher | LLMs · RAG · FastAPI | "
            "Built 3 end-to-end AI projects | Actively interviewing'\n"
            "The phrase 'Actively interviewing' signals availability to recruiters."
        ),
        metadata={"section_type": "headline", "role_category": "ai_ml",
                  "experience_level": "fresher", "category": "linkedin_template"},
    ),
    SeedDocument(
        doc_id="lt_headline_backend_001",
        content=(
            "LinkedIn Headline Template — Backend/SWE Engineer:\n"
            "Example 1: 'Backend Engineer | Python · FastAPI · PostgreSQL | "
            "3 years @ fintech | System design enthusiast'\n"
            "Example 2: 'Full Stack Developer | React · Node.js · AWS | "
            "Building scalable SaaS products | Open to remote'\n"
            "Example 3 (Fresher): 'Software Engineer | Java · Spring Boot · SQL | "
            "BITS Pilani | 2 internships at product-based companies'\n"
            "Key insight: Mention your industry ('fintech', 'SaaS', 'B2B') "
            "because recruiters search by domain, not just stack."
        ),
        metadata={"section_type": "headline", "role_category": "backend",
                  "experience_level": "junior", "category": "linkedin_template"},
    ),
    SeedDocument(
        doc_id="lt_headline_data_001",
        content=(
            "LinkedIn Headline Template — Data Scientist/Analyst:\n"
            "Example 1: 'Data Scientist | Python · SQL · MLflow | "
            "Turning messy data into revenue insights | 4 yrs exp'\n"
            "Example 2: 'Data Analyst | Tableau · Python · dbt | "
            "Ex-Razorpay | Built dashboards tracking ₹500Cr in transactions'\n"
            "Example 3: 'ML Engineer | Recommendation Systems · PyTorch | "
            "Improved CTR by 22% @ edtech platform | Open to senior roles'\n"
            "Best practice: Quantify impact in the headline when possible — "
            "'22% CTR improvement' is searchable context and instantly credible."
        ),
        metadata={"section_type": "headline", "role_category": "data",
                  "experience_level": "mid", "category": "linkedin_template"},
    ),

    # ── About section templates ───────────────────────────────────────────────
    SeedDocument(
        doc_id="lt_about_ai_001",
        content=(
            "LinkedIn About Section Template — AI Engineer (Hook-first structure):\n\n"
            "HOOK (1-2 sentences — must make recruiter want to read more):\n"
            "'I build AI systems that don't just demo well — they ship to production "
            "and stay there. Over 3 years I've learned that the hardest problems in AI "
            "aren't model accuracy, they're reliability, latency, and trust.'\n\n"
            "SUBSTANCE (what you do + proof):\n"
            "'Currently at [Company] building [specific thing]. "
            "Previously: [Achievement with number]. Built [Project] that [result].'\n\n"
            "TECHNICAL IDENTITY (keywords for search):\n"
            "'Tech I work with daily: LangChain, FastAPI, ChromaDB, PostgreSQL, "
            "GCP, Python. Currently exploring: LLM evaluation, LLMOps, agent frameworks.'\n\n"
            "CALL TO ACTION:\n"
            "'If you're building AI products and need someone who cares about "
            "production quality, let's talk: [email or LinkedIn message invitation].'\n\n"
            "Anti-pattern: 'I am a passionate AI engineer looking for opportunities "
            "to grow and contribute to a dynamic team.' — says nothing, matches nothing."
        ),
        metadata={"section_type": "about", "role_category": "ai_ml",
                  "experience_level": "mid", "category": "linkedin_template"},
    ),
    SeedDocument(
        doc_id="lt_about_fresher_001",
        content=(
            "LinkedIn About Section Template — Fresher (Any Tech Role):\n\n"
            "HOOK: Lead with your strongest achievement, not your status.\n"
            "Bad: 'I am a final year B.Tech student seeking opportunities.'\n"
            "Good: 'I built a real-time fraud detection system that processes "
            "10,000 transactions/second — using Kafka, Python, and an XGBoost "
            "model I trained on 2M records. This is the kind of problem I love.'\n\n"
            "STRUCTURE FOR FRESHERS:\n"
            "1. Best project (2-3 sentences with tech + result)\n"
            "2. What you're learning right now (shows growth mindset)\n"
            "3. What you're looking for (specific, not 'any opportunity')\n"
            "4. How to reach you\n\n"
            "Keyword density tip: Naturally mention your top 6-8 skills in the "
            "About section — LinkedIn's search algorithm weights About heavily."
        ),
        metadata={"section_type": "about", "role_category": "general",
                  "experience_level": "fresher", "category": "linkedin_template"},
    ),

    # ── Experience bullet rewrites ────────────────────────────────────────────
    SeedDocument(
        doc_id="lt_experience_001",
        content=(
            "LinkedIn Experience Bullet Rewrite — STAR Format Guide:\n\n"
            "WEAK: 'Worked on machine learning project for customer churn prediction.'\n"
            "STRONG: 'Reduced customer churn by 18% by building an XGBoost churn "
            "prediction model (AUC 0.91) on 500K user records; automated retraining "
            "pipeline cut model refresh time from 3 days to 4 hours.'\n\n"
            "WEAK: 'Developed APIs using FastAPI.'\n"
            "STRONG: 'Designed and built 12 REST APIs using FastAPI and PostgreSQL, "
            "handling 50K requests/day; added Redis caching that cut P95 latency "
            "from 800ms to 120ms.'\n\n"
            "WEAK: 'Led a team of engineers.'\n"
            "STRONG: 'Led a 4-person backend team to deliver a B2B SaaS billing "
            "module in 6 weeks (2 weeks ahead of deadline); module now processes "
            "₹2Cr+ in monthly transactions.'\n\n"
            "Formula: [Action verb] + [What you did] + [How] + [Measurable result]"
        ),
        metadata={"section_type": "experience", "role_category": "general",
                  "experience_level": "mid", "category": "linkedin_template"},
    ),
    SeedDocument(
        doc_id="lt_experience_002",
        content=(
            "LinkedIn Experience — Strong Action Verbs by Category:\n\n"
            "BUILT/ENGINEERED: Architected, Engineered, Developed, Built, "
            "Implemented, Deployed, Shipped, Launched, Delivered\n\n"
            "IMPROVED: Optimised, Reduced (latency/cost/churn), Increased "
            "(accuracy/revenue/conversion), Accelerated, Streamlined, Automated\n\n"
            "LED: Led, Managed, Mentored, Coordinated, Spearheaded, Drove, Owned\n\n"
            "ANALYSED: Modelled, Analysed, Investigated, Evaluated, Designed, "
            "Researched, Benchmarked\n\n"
            "WEAK VERBS TO AVOID: Worked on, Helped with, Assisted in, "
            "Was responsible for, Participated in, Contributed to\n\n"
            "Why: Weak verbs hide your actual contribution. "
            "'Helped with ML model' → whose model? What did you do? "
            "'Trained XGBoost model achieving 94% accuracy' → clear ownership."
        ),
        metadata={"section_type": "experience", "role_category": "general",
                  "experience_level": "general", "category": "linkedin_template"},
    ),

    # ── Keyword density by role ───────────────────────────────────────────────
    SeedDocument(
        doc_id="lt_keywords_ai_001",
        content=(
            "High-value LinkedIn Keywords for AI/ML Engineer roles (2024-2025):\n\n"
            "MUST HAVE (recruiter search terms):\n"
            "Large Language Models, LLMs, RAG, Retrieval-Augmented Generation, "
            "LangChain, LangGraph, Vector Database, Embeddings, Fine-tuning, "
            "Prompt Engineering, Agentic AI, Multi-agent systems\n\n"
            "TECHNICAL DEPTH SIGNALS:\n"
            "MLflow, Weights & Biases, LLMOps, MLOps, Model Evaluation, "
            "A/B Testing, ChromaDB, Pinecone, Weaviate, FAISS\n\n"
            "INFRASTRUCTURE KEYWORDS:\n"
            "FastAPI, Docker, Kubernetes, AWS SageMaker, GCP Vertex AI, "
            "Airflow, Kafka, PostgreSQL, Redis\n\n"
            "HOW TO ADD THEM: Don't keyword-stuff. Add naturally in: "
            "(1) Skills section — most impactful for search ranking. "
            "(2) About section — 6-8 technical terms mentioned conversationally. "
            "(3) Project descriptions — where you used each tool."
        ),
        metadata={"section_type": "keywords", "role_category": "ai_ml",
                  "experience_level": "general", "category": "linkedin_template"},
    ),
    SeedDocument(
        doc_id="lt_keywords_backend_001",
        content=(
            "High-value LinkedIn Keywords for Backend/SWE Engineer roles:\n\n"
            "LANGUAGE KEYWORDS: Python, Java, Go, Node.js, TypeScript\n\n"
            "FRAMEWORK KEYWORDS: FastAPI, Spring Boot, Django, Express.js, "
            "gRPC, GraphQL, REST API, Microservices\n\n"
            "DATA KEYWORDS: PostgreSQL, MySQL, MongoDB, Redis, Elasticsearch, "
            "Kafka, RabbitMQ, SQL optimization\n\n"
            "INFRASTRUCTURE: Docker, Kubernetes, AWS, GCP, Azure, CI/CD, "
            "GitHub Actions, Terraform, Linux\n\n"
            "ARCHITECTURE SIGNALS: System Design, Distributed Systems, "
            "High Availability, Horizontal Scaling, Database sharding, "
            "Event-driven architecture, API Gateway\n\n"
            "PROFILE TIP: Reorder your Skills section so the most searchable "
            "terms appear in the top 3 (shown without expanding). "
            "LinkedIn shows Skills in the order you add them — manually reorder."
        ),
        metadata={"section_type": "keywords", "role_category": "backend",
                  "experience_level": "general", "category": "linkedin_template"},
    ),
    SeedDocument(
        doc_id="lt_scoring_001",
        content=(
            "LinkedIn Profile Scoring Criteria (0-100 scale):\n\n"
            "HEADLINE (20 points):\n"
            "- Contains target role title: +8\n"
            "- Contains 2+ searchable keywords: +7\n"
            "- Contains differentiator (achievement/specialisation): +5\n\n"
            "ABOUT SECTION (25 points):\n"
            "- Has a strong hook (not 'I am a...'): +10\n"
            "- Contains 6+ relevant keywords naturally: +8\n"
            "- Includes quantified achievement: +7\n\n"
            "EXPERIENCE BULLETS (30 points):\n"
            "- Uses strong action verbs (not 'worked on'): +10\n"
            "- At least 2 bullets have metrics/numbers: +12\n"
            "- STAR format evident: +8\n\n"
            "SKILLS SECTION (15 points):\n"
            "- Top 3 skills match target role: +10\n"
            "- 10+ relevant skills listed: +5\n\n"
            "COMPLETENESS (10 points):\n"
            "- Profile photo: +3\n"
            "- All sections filled: +4\n"
            "- Custom URL: +3"
        ),
        metadata={"section_type": "scoring", "role_category": "general",
                  "experience_level": "general", "category": "linkedin_template"},
    ),
]


# ─────────────────────────────────────────────────────────────────────────────
# COLLECTION 2 — project_templates
# ─────────────────────────────────────────────────────────────────────────────

PROJECT_TEMPLATES: list[SeedDocument] = [

    # ── AI/ML Projects ────────────────────────────────────────────────────────
    SeedDocument(
        doc_id="pt_ai_001",
        content=(
            "Project: AI-Powered Resume Screener\n"
            "Role fit: AI Engineer, ML Engineer, Backend Engineer\n"
            "Difficulty: Intermediate | Estimated time: 2-3 weeks\n\n"
            "What to build: FastAPI backend that accepts resume PDFs, extracts text "
            "with PyMuPDF, embeds with Gemini text-embedding-004, stores in ChromaDB, "
            "and scores against job descriptions using cosine similarity + Gemini analysis.\n\n"
            "Tech stack: Python, FastAPI, ChromaDB, Gemini API, PyMuPDF, Docker\n\n"
            "Why this impresses: Demonstrates RAG pipeline, LLM integration, async API design, "
            "and a real business problem. Every AI product company has this exact problem.\n\n"
            "Interview talking points: (1) How you chunked and embedded PDFs. "
            "(2) Why cosine similarity over keyword matching. "
            "(3) How you handled OCR/scanned PDFs. "
            "(4) How you'd scale to 10,000 resumes/day.\n\n"
            "GitHub README must include: Architecture diagram, API docs screenshot, "
            "sample output, and a live demo link (deploy free on Render)."
        ),
        metadata={"role_category": "ai_ml", "difficulty": "intermediate",
                  "primary_skill": "RAG", "time_weeks": 3, "industry": "hr_tech",
                  "category": "project_template"},
    ),
    SeedDocument(
        doc_id="pt_ai_002",
        content=(
            "Project: Multi-Agent Research Assistant (LangGraph)\n"
            "Role fit: AI Engineer, LLM Engineer\n"
            "Difficulty: Advanced | Estimated time: 3-4 weeks\n\n"
            "What to build: A LangGraph-based multi-agent system where: "
            "(1) Supervisor agent receives research query, "
            "(2) Web search agent fetches results (use SerpAPI or DuckDuckGo), "
            "(3) Summariser agent condenses each source, "
            "(4) Synthesis agent produces a final structured report with citations.\n\n"
            "Tech stack: Python, LangGraph, LangChain, FastAPI, Gemini API, "
            "SerpAPI/Tavily, Redis (for caching), Docker\n\n"
            "Why this impresses: Directly demonstrates multi-agent orchestration, "
            "state management, tool use, and production deployment. "
            "This is the exact architecture pattern FAANG AI teams are building.\n\n"
            "Interview talking points: (1) How you handle agent failures gracefully. "
            "(2) How you prevent infinite loops in the graph. "
            "(3) How you'd add human-in-the-loop approval. "
            "(4) Memory vs. stateless design tradeoffs."
        ),
        metadata={"role_category": "ai_ml", "difficulty": "advanced",
                  "primary_skill": "LangGraph", "time_weeks": 4, "industry": "general",
                  "category": "project_template"},
    ),
    SeedDocument(
        doc_id="pt_ai_003",
        content=(
            "Project: YouTube Video Q&A Chatbot (RAG)\n"
            "Role fit: AI Engineer, ML Engineer, Full Stack Developer\n"
            "Difficulty: Beginner-Intermediate | Estimated time: 1-2 weeks\n\n"
            "What to build: Given a YouTube URL, transcribe the video (use Whisper API "
            "or YouTube transcript API), chunk the transcript, embed with Gemini, "
            "store in ChromaDB, and serve a chat interface where users ask questions "
            "about the video content.\n\n"
            "Tech stack: Python, FastAPI, ChromaDB, Gemini API, YouTube Transcript API, "
            "React (frontend), Docker\n\n"
            "Why this impresses: Full-stack RAG pipeline with a real, demonstrable UI. "
            "Easy to show in interviews — paste any YouTube link and ask questions.\n\n"
            "Differentiator ideas: Add multi-video support, citation highlighting "
            "(answer includes timestamp), or voice input for questions."
        ),
        metadata={"role_category": "ai_ml", "difficulty": "beginner",
                  "primary_skill": "RAG", "time_weeks": 2, "industry": "edtech",
                  "category": "project_template"},
    ),
    SeedDocument(
        doc_id="pt_ai_004",
        content=(
            "Project: Automated Code Review Agent\n"
            "Role fit: AI Engineer, Backend Engineer, DevOps Engineer\n"
            "Difficulty: Intermediate | Estimated time: 2-3 weeks\n\n"
            "What to build: GitHub webhook listener (FastAPI) that triggers when a PR "
            "is opened, sends the diff to Gemini with a code review prompt, and posts "
            "structured feedback as a PR comment. Checks: security issues, performance "
            "anti-patterns, missing tests, naming conventions.\n\n"
            "Tech stack: Python, FastAPI, Gemini API, GitHub API (PyGithub), "
            "Docker, GitHub Actions\n\n"
            "Why this impresses: Combines LLM, webhook integration, GitHub API, "
            "and a DevOps workflow. This is a tool your interviewers probably wish existed.\n\n"
            "Impact to mention: 'Reviews PRs in under 30 seconds, catching 3-5 "
            "issues per PR that would otherwise reach code review.'"
        ),
        metadata={"role_category": "ai_ml", "difficulty": "intermediate",
                  "primary_skill": "LLM Integration", "time_weeks": 3, "industry": "devtools",
                  "category": "project_template"},
    ),

    # ── Backend/SWE Projects ──────────────────────────────────────────────────
    SeedDocument(
        doc_id="pt_backend_001",
        content=(
            "Project: Real-Time Stock Price Alert System\n"
            "Role fit: Backend Engineer, SDE-1/SDE-2, Fintech roles\n"
            "Difficulty: Intermediate | Estimated time: 2-3 weeks\n\n"
            "What to build: Users set price alerts (e.g. 'notify me when RELIANCE "
            "drops below ₹2400'). FastAPI backend polls Yahoo Finance every minute, "
            "checks conditions, and sends alerts via Telegram Bot API. "
            "Redis stores active alerts; PostgreSQL stores alert history.\n\n"
            "Tech stack: Python, FastAPI, Redis, PostgreSQL, Celery/APScheduler, "
            "Telegram Bot API, Docker, WebSockets (for live dashboard)\n\n"
            "Why this impresses: Demonstrates async background tasks, pub/sub with Redis, "
            "external API integration, and a real user-facing feature.\n\n"
            "Scale question prep: 'How would you handle 1M users with 10 alerts each?' "
            "Answer: Redis Sorted Sets for efficient condition checking, "
            "Kafka for alert fan-out, partition alerts by stock symbol."
        ),
        metadata={"role_category": "backend", "difficulty": "intermediate",
                  "primary_skill": "FastAPI", "time_weeks": 3, "industry": "fintech",
                  "category": "project_template"},
    ),
    SeedDocument(
        doc_id="pt_backend_002",
        content=(
            "Project: URL Shortener with Analytics\n"
            "Role fit: Backend Engineer, Full Stack, System Design prep\n"
            "Difficulty: Beginner | Estimated time: 1 week\n\n"
            "What to build: POST /shorten accepts a long URL, returns a short code "
            "(Base62 encoding). GET /:code redirects and logs: IP, user agent, "
            "referrer, timestamp. Dashboard shows click counts, geographic distribution, "
            "and device breakdown.\n\n"
            "Tech stack: Python/FastAPI (or Node.js/Express), PostgreSQL, Redis "
            "(cache hot URLs), React (dashboard)\n\n"
            "Why this impresses: Classic system design interview problem. "
            "Having a working implementation demonstrates you understand the concepts, "
            "not just theory.\n\n"
            "Must add for differentiation: Custom expiry, QR code generation, "
            "rate limiting (prevent abuse), and a public API with API keys."
        ),
        metadata={"role_category": "backend", "difficulty": "beginner",
                  "primary_skill": "System Design", "time_weeks": 1, "industry": "general",
                  "category": "project_template"},
    ),
    SeedDocument(
        doc_id="pt_backend_003",
        content=(
            "Project: Event-Driven Order Processing System\n"
            "Role fit: Backend Engineer, Microservices, E-commerce/Fintech roles\n"
            "Difficulty: Advanced | Estimated time: 4-5 weeks\n\n"
            "What to build: Microservices architecture with: "
            "(1) Order Service (FastAPI) — creates orders, publishes to Kafka. "
            "(2) Inventory Service — consumes Kafka events, reserves stock. "
            "(3) Payment Service — processes payment (mock), publishes result. "
            "(4) Notification Service — emails/SMS on order status changes. "
            "(5) API Gateway — single entry point.\n\n"
            "Tech stack: Python, FastAPI, Kafka, PostgreSQL (per service), "
            "Redis, Docker Compose, gRPC (inter-service), Nginx\n\n"
            "Why this impresses: Demonstrates exactly what SDE-2/SDE-3 interviews "
            "test: distributed systems, eventual consistency, failure handling, "
            "idempotency, and microservices design.\n\n"
            "This project alone can carry a backend interview at mid-to-senior level."
        ),
        metadata={"role_category": "backend", "difficulty": "advanced",
                  "primary_skill": "Microservices", "time_weeks": 5, "industry": "ecommerce",
                  "category": "project_template"},
    ),

    # ── Data Science/ML Projects ──────────────────────────────────────────────
    SeedDocument(
        doc_id="pt_data_001",
        content=(
            "Project: Customer Churn Prediction + MLflow Tracking\n"
            "Role fit: Data Scientist, ML Engineer, Analyst\n"
            "Difficulty: Intermediate | Estimated time: 2-3 weeks\n\n"
            "What to build: End-to-end ML pipeline: "
            "(1) EDA on a telecom/SaaS churn dataset (Kaggle). "
            "(2) Feature engineering: tenure buckets, product usage metrics, payment history. "
            "(3) Compare 3 models: Logistic Regression, Random Forest, XGBoost. "
            "(4) Track all experiments in MLflow (metrics, params, artifacts). "
            "(5) Deploy best model as FastAPI endpoint. "
            "(6) Streamlit dashboard for predictions.\n\n"
            "Tech stack: Python, pandas, scikit-learn, XGBoost, MLflow, FastAPI, "
            "Streamlit, Docker\n\n"
            "Interview prep: Be ready to explain: class imbalance handling (SMOTE), "
            "why F1 > accuracy for churn, feature importance, and production deployment."
        ),
        metadata={"role_category": "data", "difficulty": "intermediate",
                  "primary_skill": "MLflow", "time_weeks": 3, "industry": "saas",
                  "category": "project_template"},
    ),
    SeedDocument(
        doc_id="pt_data_002",
        content=(
            "Project: Real-Time Sentiment Analysis Dashboard\n"
            "Role fit: Data Scientist, ML Engineer, NLP Engineer\n"
            "Difficulty: Intermediate | Estimated time: 2 weeks\n\n"
            "What to build: Consume Twitter/Reddit API (or use stored dataset), "
            "run sentiment classification (fine-tuned BERT or Gemini API), "
            "aggregate by brand/hashtag/topic, display on a live Streamlit/Grafana dashboard.\n\n"
            "Tech stack: Python, Transformers (HuggingFace) or Gemini API, "
            "Kafka (streaming), PostgreSQL (time-series), Grafana or Streamlit\n\n"
            "Why this impresses: Combines NLP, real-time processing, and data visualization. "
            "Easy to demo live — type a tweet, see sentiment instantly.\n\n"
            "Differentiation: Add aspect-based sentiment (not just positive/negative "
            "but which aspect: price, quality, service). Shows deeper NLP knowledge."
        ),
        metadata={"role_category": "data", "difficulty": "intermediate",
                  "primary_skill": "NLP", "time_weeks": 2, "industry": "general",
                  "category": "project_template"},
    ),

    # ── Full Stack Projects ───────────────────────────────────────────────────
    SeedDocument(
        doc_id="pt_fullstack_001",
        content=(
            "Project: SaaS Invoice Generator with Subscription\n"
            "Role fit: Full Stack Developer, Product Engineer\n"
            "Difficulty: Advanced | Estimated time: 4-5 weeks\n\n"
            "What to build: Multi-tenant SaaS app: "
            "(1) React frontend with Tailwind CSS. "
            "(2) FastAPI/Node backend with JWT auth. "
            "(3) Invoice creation, PDF generation (ReportLab/Puppeteer). "
            "(4) Stripe/Razorpay integration for subscription billing. "
            "(5) Email delivery of invoices (SendGrid). "
            "(6) PostgreSQL with row-level multi-tenancy.\n\n"
            "Tech stack: React, TypeScript, FastAPI, PostgreSQL, Redis, "
            "Stripe API, SendGrid, Docker, AWS/Render\n\n"
            "Why this impresses: Real production features — auth, payments, "
            "PDF generation, email — not another todo app. "
            "Demonstrates you can build something people would actually pay for."
        ),
        metadata={"role_category": "fullstack", "difficulty": "advanced",
                  "primary_skill": "Full Stack", "time_weeks": 5, "industry": "saas",
                  "category": "project_template"},
    ),

    # ── Overused projects to avoid ────────────────────────────────────────────
    SeedDocument(
        doc_id="pt_avoid_001",
        content=(
            "Projects to Avoid on Your Portfolio (Overused / Low Signal):\n\n"
            "1. Todo App — Every tutorial builds this. Zero differentiation.\n"
            "   Fix: Build a Kanban board with real-time updates and collaboration instead.\n\n"
            "2. Weather App — Generic API consumption. No problem-solving signal.\n"
            "   Fix: Build a weather-based outfit recommender with GPT integration.\n\n"
            "3. Calculator — Shows basic UI only. No backend, no data, no architecture.\n"
            "   Fix: Build a financial calculator with loan amortisation, EMI breakdown, and charts.\n\n"
            "4. Basic CRUD with no problem: 'Library Management System' with no real scale challenge.\n"
            "   Fix: Add concurrent borrowing conflicts, late-return fines, SMS alerts — real problems.\n\n"
            "5. Chatbot that's just Gemini/GPT API wrapper with no RAG or customisation.\n"
            "   Fix: Add a knowledge base (ChromaDB), conversation memory, and a real domain focus.\n\n"
            "Rule of thumb: If a tutorial exists with the exact same title, add something new to it."
        ),
        metadata={"role_category": "general", "difficulty": "general",
                  "primary_skill": "portfolio_strategy", "time_weeks": 0, "industry": "general",
                  "category": "project_template"},
    ),
]


# ─────────────────────────────────────────────────────────────────────────────
# COLLECTION 3 — english_templates
# ─────────────────────────────────────────────────────────────────────────────

ENGLISH_TEMPLATES: list[SeedDocument] = [

    # ── Filler words and replacements ─────────────────────────────────────────
    SeedDocument(
        doc_id="et_fillers_001",
        content=(
            "Common Filler Words in Professional English — With Fixes:\n\n"
            "FILLER → REPLACEMENT:\n"
            "'basically' → Remove it entirely. It adds nothing.\n"
            "'you know' → Remove. It seeks approval and weakens statements.\n"
            "'like' (used as filler) → Replace with a pause or remove.\n"
            "'uh', 'um', 'er' → Replace with a 1-2 second silent pause. "
            "Silence reads as confidence, not uncertainty.\n"
            "'and stuff' → Be specific: name the actual items.\n"
            "'kind of', 'sort of' → Remove or commit. Say what you mean directly.\n"
            "'honestly' → Implies other things you said were dishonest.\n"
            "'to be honest' → Same issue. Remove.\n"
            "'I think' → Replace with 'In my experience' or 'Based on X, I believe'.\n"
            "'actually' → Often condescending. Remove or rephrase.\n\n"
            "PRACTICE: Record yourself answering 'Tell me about yourself'. "
            "Count fillers. Target: under 2 per minute."
        ),
        metadata={"template_type": "filler_words", "context": "interview",
                  "proficiency_target": "professional", "category": "english_template"},
    ),

    # ── Vocabulary upgrades ───────────────────────────────────────────────────
    SeedDocument(
        doc_id="et_vocab_001",
        content=(
            "Professional Vocabulary Upgrades for Tech Interviews:\n\n"
            "WEAK → STRONG:\n"
            "'I worked on' → 'I engineered / I architected / I owned'\n"
            "'I helped with' → 'I contributed to / I was responsible for'\n"
            "'I did' → 'I delivered / I shipped / I implemented'\n"
            "'I made it faster' → 'I reduced latency by X% / I improved throughput by X'\n"
            "'I fixed bugs' → 'I resolved X critical production issues reducing error rate by Y%'\n"
            "'I learned' → 'I upskilled in / I deepened my expertise in'\n"
            "'My team built' → 'The team I was part of shipped / I contributed to building'\n"
            "'It was difficult' → 'The key challenge was X, which I addressed by Y'\n"
            "'I think I did okay' → 'The outcome was X, measured by Y'\n"
            "'I don't know' → 'I haven't worked with that specific tool yet, "
            "but I've solved similar problems using X, and I'd approach it by Y'\n\n"
            "CONFIDENCE LANGUAGE:\n"
            "Instead of: 'I just did...', 'I only...', 'I was just an intern...'\n"
            "Say: 'As part of my role, I...', 'During my internship, I delivered...'"
        ),
        metadata={"template_type": "vocab_upgrade", "context": "interview",
                  "proficiency_target": "professional", "category": "english_template"},
    ),
    SeedDocument(
        doc_id="et_vocab_002",
        content=(
            "Grammar Patterns Common in Indian English — With Corrections:\n\n"
            "1. TENSE CONSISTENCY:\n"
            "Wrong: 'I was working there and then I join the new team.'\n"
            "Right: 'I was working there and then I joined the new team.'\n\n"
            "2. ARTICLES (a/an/the):\n"
            "Wrong: 'I built API for the project.'\n"
            "Right: 'I built an API for the project.'\n\n"
            "3. PREPOSITIONS:\n"
            "Wrong: 'I am good in Python.' → Right: 'I am good at Python.'\n"
            "Wrong: 'I did internship at Google.' → Right: 'I did an internship at Google.'\n\n"
            "4. SINGULAR/PLURAL:\n"
            "Wrong: 'I have 3 year of experience.' → Right: '3 years of experience.'\n\n"
            "5. DOUBLE NEGATIVES:\n"
            "Wrong: 'I don't know nothing about that.' → Right: 'I don't know anything about that.'\n\n"
            "6. REDUNDANT PHRASES:\n"
            "'Revert back' → 'Revert' (revert already means 'go back')\n"
            "'More better' → 'Better'\n"
            "'Prepone' → 'Move forward' / 'Reschedule earlier' (not standard English)"
        ),
        metadata={"template_type": "grammar", "context": "general",
                  "proficiency_target": "professional", "category": "english_template"},
    ),

    # ── STAR format examples ──────────────────────────────────────────────────
    SeedDocument(
        doc_id="et_star_001",
        content=(
            "STAR Format — Complete Example for 'Tell me about a challenge you overcame':\n\n"
            "SITUATION (set context — 1-2 sentences):\n"
            "'During my final year internship at Freshworks, our team was tasked with "
            "migrating a legacy monolithic billing system to microservices. "
            "Two weeks before the deadline, we discovered the old system had undocumented "
            "business logic that 40% of our enterprise clients depended on.'\n\n"
            "TASK (your specific responsibility):\n"
            "'As the backend developer, I was responsible for ensuring the new system "
            "maintained 100% functional parity with the legacy system.'\n\n"
            "ACTION (what YOU did — use 'I', not 'we'):\n"
            "'I wrote a data reconciliation script that ran both systems in parallel "
            "and flagged discrepancies. I documented 23 undocumented rules by reading "
            "the old code and interviewing the original developers.'\n\n"
            "RESULT (measurable outcome):\n"
            "'We migrated on time with zero client-reported issues. "
            "The reconciliation script later became part of our standard migration toolkit.'\n\n"
            "STAR check: Does your answer have all 4 parts? Is the Result measurable?"
        ),
        metadata={"template_type": "hr_answer", "context": "interview",
                  "proficiency_target": "professional", "category": "english_template"},
    ),
    SeedDocument(
        doc_id="et_star_002",
        content=(
            "Model Answer — 'Tell me about yourself' (2-minute version for tech roles):\n\n"
            "STRUCTURE: Role → Achievement → Transition → Now → Why this company\n\n"
            "EXAMPLE:\n"
            "'I'm a backend engineer with 3 years of experience building data-intensive "
            "APIs, mostly in the fintech space.\n\n"
            "My most significant project was at PhonePe, where I built the settlement "
            "reconciliation service that processes ₹500Cr in daily transactions. "
            "I reduced reconciliation time from 4 hours to 18 minutes by redesigning "
            "the batch processing pipeline with Kafka and parallel DB writes.\n\n"
            "Before that, I did two internships — Razorpay and a YC-backed startup — "
            "which is where I learned to ship fast without compromising reliability.\n\n"
            "Right now I'm deepening my AI skills — I've been building with LangGraph "
            "and deployed a multi-agent system that does automated due diligence for a side project.\n\n"
            "I'm here because [Company] is working on [specific product/problem], "
            "which is exactly the intersection of distributed systems and AI I want to specialise in.'\n\n"
            "Key principles: Specific > vague. Numbers > adjectives. Why THIS company = mandatory."
        ),
        metadata={"template_type": "hr_answer", "context": "interview",
                  "proficiency_target": "professional", "category": "english_template"},
    ),
    SeedDocument(
        doc_id="et_star_003",
        content=(
            "Model HR Answers — Common Interview Questions:\n\n"
            "Q: What is your greatest strength?\n"
            "WEAK: 'I am a hard worker and quick learner.'\n"
            "STRONG: 'My strongest skill is taking an ambiguous problem and breaking it "
            "into a working system quickly. At my last role, when we had an unexpected "
            "requirement 3 days before launch, I designed and shipped the feature in 2 days "
            "by cutting scope intelligently — which is still running in production.'\n\n"
            "Q: Where do you see yourself in 5 years?\n"
            "WEAK: 'I want to grow in the company and take on more responsibilities.'\n"
            "STRONG: 'In 5 years I want to be the person my team goes to for the hardest "
            "distributed systems problems. I want to have shipped at least one system "
            "at 10M+ users scale. Whether that's at this company or requires moving, "
            "I'll follow where the hardest problems are. Given your scale, this seems like the place.'\n\n"
            "Q: Why should we hire you?\n"
            "Formula: [Specific skill you have] + [Proof] + [How it solves their problem]"
        ),
        metadata={"template_type": "hr_answer", "context": "interview",
                  "proficiency_target": "professional", "category": "english_template"},
    ),
    SeedDocument(
        doc_id="et_structure_001",
        content=(
            "Answer Structure Frameworks for Different Question Types:\n\n"
            "BEHAVIORAL (Tell me about a time when...):\n"
            "→ Use STAR. 90 seconds max. Result must be measurable.\n\n"
            "TECHNICAL (How does X work? Explain Y):\n"
            "→ ELI5 first → Technical depth → Real-world example → Tradeoffs\n"
            "Example: 'At a high level, X does Y [simple]. Technically, it works by "
            "[mechanism]. I used it to [real example]. The main tradeoff is [honest limitation].'\n\n"
            "HYPOTHETICAL (What would you do if...):\n"
            "→ Clarify → Approach → Tradeoffs → Decision\n"
            "'Before I answer, can I ask [clarifying question]? "
            "Given that, I'd approach it by [method] because [reasoning]. "
            "The risk is [honest risk], which I'd mitigate by [mitigation].'\n\n"
            "OPINION (What do you think about X?):\n"
            "→ Take a position → Back it with evidence → Acknowledge counterargument\n"
            "'I believe X is better than Y in most cases because [evidence]. "
            "That said, Y makes more sense when [specific scenario].'"
        ),
        metadata={"template_type": "hr_answer", "context": "interview",
                  "proficiency_target": "professional", "category": "english_template"},
    ),
    SeedDocument(
        doc_id="et_elevator_001",
        content=(
            "Elevator Pitch Templates (30 seconds) by Role:\n\n"
            "AI ENGINEER:\n"
            "'I build AI systems that actually work in production. "
            "I've spent 2 years shipping LLM-powered products — most recently "
            "a multi-agent system that reduced manual data processing by 70% at [company]. "
            "I specialize in RAG pipelines and agentic workflows with LangGraph.'\n\n"
            "BACKEND ENGINEER:\n"
            "'I design and build the systems that handle the hard parts — "
            "high traffic, complex data flows, distributed consistency. "
            "3 years in fintech, where I built APIs processing ₹1Cr+ daily. "
            "I care most about reliability and clean architecture.'\n\n"
            "DATA SCIENTIST:\n"
            "'I turn messy business data into decisions. "
            "My last model reduced customer acquisition cost by 25% "
            "by identifying the highest-LTV user segments before spending on ads. "
            "I work across the stack — SQL, Python, dashboards, and production APIs.'\n\n"
            "FRESHER (ANY ROLE):\n"
            "'I'm a [final year / recent grad] from [college] in CSE. "
            "My strongest work is [project with one-sentence result]. "
            "I'm looking for my first role where I can [specific thing], and "
            "I'm particularly interested in [company/team] because [specific reason].'"
        ),
        metadata={"template_type": "hr_answer", "context": "interview",
                  "proficiency_target": "professional", "category": "english_template"},
    ),
]
