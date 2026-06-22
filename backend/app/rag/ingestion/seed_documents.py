"""
app/rag/ingestion/seed_documents.py
─────────────────────────────────────
All seed documents for the AI Career Copilot knowledge base.

Structure
──────────
Each collection is a list of SeedDocument objects:
  - content:  The actual text stored and embedded in ChromaDB
  - metadata: Filterable fields (role, category, difficulty, etc.)
  - doc_id:   Stable unique ID (deterministic — re-seeding won't duplicate)

Content design principles
──────────────────────────
  1. Each document chunk = one coherent, standalone piece of knowledge
     (a question+answer, a skill description, a resource description).
     Chunks that mix multiple topics fragment poorly in retrieval.

  2. Metadata is critical for filtered retrieval:
     - Resume/Skill Gap Agents filter by {"role": "AI Engineer"}
     - Interview Agent filters by {"interview_type": "technical"}
     - Study Planner filters by {"topic": "Docker"}

  3. Content is written to be directly usable in prompts:
     Gemini will read these chunks as context. They should be dense
     with useful information, not marketing fluff.

  4. We seed 5 collections × ~20 documents = ~100 initial documents.
     This is enough to demonstrate real RAG behaviour. In production,
     you would load hundreds of real job postings, course catalogues,
     and curated Q&A sets.
"""

from dataclasses import dataclass, field


@dataclass
class SeedDocument:
    content:  str
    metadata: dict
    doc_id:   str


# ── 1. Interview Questions ─────────────────────────────────────────────────────

INTERVIEW_QUESTIONS: list[SeedDocument] = [
    # AI Engineer - Technical
    SeedDocument(
        doc_id="iq_ai_001",
        content="Q: What is the difference between RAG and fine-tuning in LLMs?\nA: RAG (Retrieval-Augmented Generation) retrieves relevant documents at inference time and injects them into the prompt — best for dynamic, frequently-updated knowledge. Fine-tuning updates the model weights on domain-specific data — best for consistent tone, formatting, or task specialisation. Use RAG when knowledge changes frequently; use fine-tuning when you need consistent behaviour. They can be combined: fine-tune for style, RAG for facts.",
        metadata={"role": "AI Engineer", "interview_type": "technical", "difficulty": "medium", "topic": "LLMs", "category": "ai_ml"},
    ),
    SeedDocument(
        doc_id="iq_ai_002",
        content="Q: Explain the transformer architecture.\nA: The Transformer uses an encoder-decoder architecture with multi-head self-attention. Key components: (1) Tokeniser converts text to token IDs. (2) Embedding layer maps tokens to dense vectors. (3) Positional encoding adds position information (since attention is order-agnostic). (4) Multi-head attention: each head learns different relationships; outputs are concatenated and projected. (5) Feed-forward layers process each position independently. (6) Layer normalisation and residual connections stabilise training. Decoder adds cross-attention over encoder outputs.",
        metadata={"role": "AI Engineer", "interview_type": "technical", "difficulty": "hard", "topic": "Deep Learning", "category": "ai_ml"},
    ),
    SeedDocument(
        doc_id="iq_ai_003",
        content="Q: What is vector similarity search and how does ChromaDB use it?\nA: Vector similarity search finds the most semantically similar documents by computing the distance between embedding vectors. ChromaDB uses HNSW (Hierarchical Navigable Small World) graphs for approximate nearest-neighbour search. Embeddings are dense float vectors where similar meanings cluster together in high-dimensional space. Cosine similarity measures the angle between vectors (range -1 to 1; 1 = identical meaning). ChromaDB stores both the original text and its embedding, enabling semantic retrieval by meaning rather than keyword matching.",
        metadata={"role": "AI Engineer", "interview_type": "technical", "difficulty": "medium", "topic": "Vector Databases", "category": "ai_ml"},
    ),
    SeedDocument(
        doc_id="iq_ai_004",
        content="Q: Describe a multi-agent AI system and its orchestration.\nA: A multi-agent system has multiple specialised AI agents, each responsible for a specific task, coordinated by an orchestrator. Key concepts: (1) Supervisor agent analyses user intent and routes to specialised agents. (2) Agents share a common state object — outputs from one agent become inputs for another. (3) LangGraph implements this as a StateGraph with nodes (agents) and conditional edges (routing logic). (4) Memory: MemorySaver provides per-session persistence. Benefits: separation of concerns, parallel execution, easier testing per agent.",
        metadata={"role": "AI Engineer", "interview_type": "technical", "difficulty": "hard", "topic": "Agentic AI", "category": "ai_ml"},
    ),
    SeedDocument(
        doc_id="iq_ds_001",
        content="Q: Explain the bias-variance tradeoff.\nA: Bias is error from overly simplistic assumptions (underfitting — model misses patterns). Variance is error from sensitivity to training data noise (overfitting — model memorises noise). The tradeoff: decreasing bias (more complex model) typically increases variance and vice versa. Total error = Bias² + Variance + Irreducible Noise. Solutions: regularisation (L1/L2) reduces variance; adding features reduces bias; cross-validation detects the tradeoff; ensemble methods (bagging reduces variance, boosting reduces bias).",
        metadata={"role": "Data Scientist", "interview_type": "technical", "difficulty": "medium", "topic": "Machine Learning", "category": "ai_ml"},
    ),
    SeedDocument(
        doc_id="iq_se_001",
        content="Q: What is async/await in Python and when should you use it?\nA: async/await is Python's syntax for cooperative multitasking using coroutines. async def defines a coroutine; await suspends it until the awaited task completes, yielding control back to the event loop. Use it for I/O-bound tasks: HTTP requests, database queries, file reads — operations where the CPU is idle waiting for external resources. NOT for CPU-bound tasks (use multiprocessing instead). FastAPI is built on asyncio — all route handlers and database queries should be async for maximum throughput.",
        metadata={"role": "Software Engineer", "interview_type": "technical", "difficulty": "medium", "topic": "Python", "category": "backend"},
    ),
    # HR Questions
    SeedDocument(
        doc_id="iq_hr_001",
        content="Q: Tell me about yourself.\nGood answer structure: Present (current role/education + key skills) → Past (relevant experience/projects + what you learned) → Future (why this company/role aligns with your goals). Keep it 2-3 minutes. Example: 'I'm a final-year AI & Data Science student at [college]. I've built [project] using Python, LangGraph, and FastAPI, which gave me hands-on experience with multi-agent systems. Previously I interned at [company] where I [achievement]. I'm excited about this role because [specific reason].' Avoid reciting your resume verbatim.",
        metadata={"role": "general", "interview_type": "hr", "difficulty": "easy", "topic": "Introduction", "category": "hr"},
    ),
    SeedDocument(
        doc_id="iq_hr_002",
        content="Q: Where do you see yourself in 5 years?\nGood answer structure: Show ambition balanced with realism. Align with the company's growth trajectory. Mention wanting to deepen technical expertise + grow into leadership. Example for fresher: 'In 5 years, I see myself as a senior AI engineer who has shipped production AI systems at scale. I want to develop expertise in LLM deployment and MLOps, and eventually mentor junior engineers. I'm particularly interested in growing with [company] as you expand your AI capabilities.' Avoid: 'Running my own company' (signals flight risk) or 'I don't know' (signals no ambition).",
        metadata={"role": "general", "interview_type": "hr", "difficulty": "easy", "topic": "Career Goals", "category": "hr"},
    ),
    SeedDocument(
        doc_id="iq_hr_003",
        content="Q: Describe a challenging project and how you handled it.\nUse the STAR method: Situation (context), Task (your responsibility), Action (specific steps you took), Result (measurable outcome). Example: 'In my final year project, we were building a multi-agent AI system when the LangGraph API changed unexpectedly (S). I was responsible for the orchestration layer (T). I documented the breaking changes, refactored the state schema, and created integration tests to prevent future regressions (A). We delivered on time and the tests caught 3 bugs before demo day (R).' Always quantify results where possible.",
        metadata={"role": "general", "interview_type": "hr", "difficulty": "medium", "topic": "Behavioural", "category": "hr"},
    ),
]

# ── 2. Job Requirements ────────────────────────────────────────────────────────

JOB_REQUIREMENTS: list[SeedDocument] = [
    SeedDocument(
        doc_id="jr_ai_001",
        content="AI Engineer role requirements (2024 market):\nCore: Python (production-level), PyTorch or TensorFlow, LLM APIs (OpenAI/Gemini/Groq), LangChain/LangGraph for agent orchestration, Vector databases (ChromaDB/Pinecone/Weaviate), RAG pipeline design.\nBackend: FastAPI or Flask, REST API design, async Python, Docker containerisation.\nMLOps: Model versioning (MLflow), experiment tracking, basic CI/CD, cloud deployment (AWS SageMaker / GCP Vertex AI / Azure ML).\nData: SQL (PostgreSQL), Pandas, NumPy, data pipeline basics.\nNice to have: Kubernetes, Spark, fine-tuning (LoRA/QLoRA), LangFuse monitoring.",
        metadata={"role": "AI Engineer", "category": "job_requirements", "source": "job_market_2024"},
    ),
    SeedDocument(
        doc_id="jr_ds_001",
        content="Data Scientist role requirements (2024 market):\nCore: Python (Pandas, NumPy, Scikit-learn, Matplotlib/Seaborn), SQL (complex queries, window functions), Statistics (hypothesis testing, A/B testing, distributions), Machine Learning (supervised + unsupervised, model evaluation, feature engineering).\nDeep Learning: PyTorch or TensorFlow basics, CNNs, RNNs/LSTMs.\nTools: Jupyter notebooks, Git, Docker basics, one cloud platform.\nCommunication: Can explain ML results to non-technical stakeholders, data storytelling.\nNice to have: Spark/PySpark, Airflow, NLP basics, time series forecasting.",
        metadata={"role": "Data Scientist", "category": "job_requirements", "source": "job_market_2024"},
    ),
    SeedDocument(
        doc_id="jr_be_001",
        content="Backend Engineer (Python) role requirements (2024 market):\nCore: Python (FastAPI/Django/Flask), REST API design, SQL (PostgreSQL/MySQL), ORM (SQLAlchemy/Django ORM), authentication (JWT/OAuth2), async programming.\nInfrastructure: Docker, basic Kubernetes, CI/CD (GitHub Actions), cloud basics (AWS/GCP).\nDatabases: PostgreSQL, Redis for caching, basic message queues (RabbitMQ/Kafka).\nBest practices: Unit testing (pytest), code review, Git workflow, API documentation (OpenAPI/Swagger).\nNice to have: GraphQL, microservices, gRPC, WebSockets.",
        metadata={"role": "Backend Engineer", "category": "job_requirements", "source": "job_market_2024"},
    ),
    SeedDocument(
        doc_id="jr_ml_001",
        content="ML Engineer role requirements (2024 market):\nCore: Python, PyTorch/TensorFlow, model training pipelines, feature engineering, model evaluation metrics.\nMLOps: MLflow or Weights & Biases, model versioning, A/B testing, monitoring model drift.\nDeployment: FastAPI for model serving, Docker, basic Kubernetes, cloud ML platforms.\nData Engineering: ETL pipelines, SQL, Spark basics, data validation.\nLLM Specific (growing demand): LLM fine-tuning, RLHF basics, prompt engineering, RAG systems.\nSoft skills: Experimental mindset, communicating uncertainty to stakeholders.",
        metadata={"role": "ML Engineer", "category": "job_requirements", "source": "job_market_2024"},
    ),
    SeedDocument(
        doc_id="jr_fresher_001",
        content="What Indian tech companies look for in fresh graduates (TCS, Infosys, Wipro, Zoho, Freshworks):\nService companies (TCS/Infosys/Wipro): Strong programming fundamentals (Python/Java), data structures & algorithms, good aptitude test scores, communication skills, willingness to learn any tech stack.\nProduct/Startup companies (Zoho/Freshworks/Razorpay): Demonstrable projects on GitHub, problem-solving ability, specific tech stack match, curiosity and learning speed over experience.\nFor AI roles specifically: At least one end-to-end ML project, Python proficiency, basic ML knowledge (regression, classification, neural networks), exposure to any LLM API.",
        metadata={"role": "Fresher", "category": "job_requirements", "source": "india_market_2024"},
    ),
]

# ── 3. Learning Resources ──────────────────────────────────────────────────────

LEARNING_RESOURCES: list[SeedDocument] = [
    SeedDocument(
        doc_id="lr_python_001",
        content="Python learning resources:\nBeginners: Python.org official tutorial (free), Automate the Boring Stuff (free online), CS50P from Harvard (free on edX).\nIntermediate: Real Python (realpython.com) — excellent articles on async, testing, packaging. Fluent Python book (advanced).\nFor AI/ML: Fast.ai's Practical Deep Learning (project-first approach, free). Python for Data Analysis by Wes McKinney.\nPractice: LeetCode Easy problems in Python, HackerRank Python domain, build 3 real projects.\nKey topics to master: List comprehensions, generators, decorators, async/await, type hints, dataclasses.",
        metadata={"topic": "Python", "category": "programming", "difficulty": "beginner_to_intermediate"},
    ),
    SeedDocument(
        doc_id="lr_ml_001",
        content="Machine Learning learning resources:\nFoundation: Andrew Ng's ML Specialisation on Coursera (gold standard, start here). StatQuest with Josh Starmer on YouTube (best visual explanations of ML concepts).\nPractical: Kaggle Learn (free, hands-on), Kaggle competitions (start with Titanic, House Prices).\nDeep Learning: Deep Learning Specialisation by Andrew Ng. Fast.ai Part 1 (practical, top-down approach).\nBooks: Hands-on Machine Learning with Scikit-Learn (Aurélien Géron) — the best practical ML book.\nProjects to build: House price prediction, image classifier, sentiment analyser, recommendation system.",
        metadata={"topic": "Machine Learning", "category": "ai_ml", "difficulty": "beginner_to_advanced"},
    ),
    SeedDocument(
        doc_id="lr_langchain_001",
        content="LangChain and LangGraph learning resources:\nLangChain: Official docs at python.langchain.com — start with the RAG tutorial. LangChain YouTube channel has weekly updates. Sam Witteveen's YouTube channel for practical LangChain projects.\nLangGraph: Official LangGraph docs (langgraph.dev). LangChain Academy on YouTube — free multi-agent course. Harrison Chase's talks on building agentic systems.\nProjects: Build a PDF Q&A chatbot (LangChain + ChromaDB), then a multi-agent research assistant (LangGraph), then deploy with FastAPI.\nKey concepts: Chains, agents, memory, tools, state graphs, conditional edges.",
        metadata={"topic": "LangChain", "category": "ai_frameworks", "difficulty": "intermediate"},
    ),
    SeedDocument(
        doc_id="lr_docker_001",
        content="Docker learning resources:\nBest video: TechWorld with Nana Docker tutorial on YouTube (3 hours, very comprehensive, free).\nOfficial: Docker Getting Started guide at docs.docker.com — best written tutorial.\nPractice path: (1) Install Docker Desktop. (2) Run hello-world container. (3) Write a Dockerfile for a Python Flask app. (4) Use docker-compose for multi-container app. (5) Push image to Docker Hub.\nKey commands: docker build, docker run, docker ps, docker stop, docker-compose up.\nProject: Dockerize your FastAPI backend — this alone adds significant value to your resume.",
        metadata={"topic": "Docker", "category": "devops", "difficulty": "beginner_to_intermediate"},
    ),
    SeedDocument(
        doc_id="lr_fastapi_001",
        content="FastAPI learning resources:\nOfficial tutorial: fastapi.tiangolo.com/tutorial — best written API tutorial available, covers everything.\nVideo: ArjanCodes FastAPI series on YouTube — clean, production-focused.\nCourse: TestDriven.io FastAPI courses (paid but excellent).\nKey features to learn: Path parameters, query parameters, request body (Pydantic), response models, async endpoints, dependency injection, JWT authentication, file upload.\nProjects: Build a CRUD REST API with PostgreSQL, add JWT auth, write pytest tests, containerize with Docker. This combination is what most backend job postings require.",
        metadata={"topic": "FastAPI", "category": "backend", "difficulty": "beginner_to_intermediate"},
    ),
    SeedDocument(
        doc_id="lr_dsa_001",
        content="Data Structures and Algorithms resources for placement preparation:\nPrimary: NeetCode.io (neetcode.io) — best structured DSA course, free roadmap, YouTube explanations. Start with Arrays, then Hash Maps, Two Pointers, Sliding Window.\nPractice: LeetCode — solve 75 Blind75 problems minimum for placement. Striver's A2Z DSA Sheet for comprehensive coverage.\nFor Indian placements: GeeksforGeeks company-wise questions for TCS, Infosys, Amazon, Microsoft.\nStudy schedule: 2 problems per day = 60 problems/month. Consistency beats intensity.\nWeakest areas for most students: Dynamic programming, graphs (BFS/DFS), binary search variations.",
        metadata={"topic": "Data Structures", "category": "algorithms", "difficulty": "beginner_to_advanced"},
    ),
]

# ── 4. Career Guidance ─────────────────────────────────────────────────────────

CAREER_GUIDANCE: list[SeedDocument] = [
    SeedDocument(
        doc_id="cg_resume_001",
        content="Resume writing tips for tech students and freshers:\n1. One page maximum for 0-2 years experience. Use clean, ATS-friendly formatting (no tables, no graphics).\n2. Lead with a 2-3 line summary targeting your specific role. Include keywords from job postings.\n3. Quantify everything: 'Built ML model' → 'Built ML model achieving 94% accuracy on 50K record dataset'.\n4. Projects section is critical for freshers — list GitHub link, tech stack used, problem solved, impact.\n5. Skills section: Group by category (Languages | Frameworks | Tools | Databases). Don't list everything — list what you can discuss in an interview.\n6. ATS optimization: Mirror exact keywords from job descriptions. 'Machine Learning' not 'ML'. 'Python programming' not just 'Python'.\n7. Common mistakes: Generic objective statement, listing every technology you've touched, no GitHub/portfolio link.",
        metadata={"category": "resume", "topic": "Resume Writing", "source": "career_guidance"},
    ),
    SeedDocument(
        doc_id="cg_linkedin_001",
        content="LinkedIn optimisation for tech job seekers:\n1. Headline: Don't use 'Student at X University'. Use 'AI Engineer | LangGraph | FastAPI | Python | Building AI Career Copilot'. Keywords matter for recruiter searches.\n2. About section: 3-4 paragraphs — Who you are, What you build, What you're looking for. Include top 5 skills naturally.\n3. Featured section: Pin your best GitHub project, a blog post, or a demo video.\n4. Connections: Connect with 50+ engineers and recruiters in your target companies. Personalise every connection request.\n5. Activity: Share one technical post per week — a lesson learned, a project update, a useful resource. Consistency builds visibility.\n6. Skills: Add 50 skills. LinkedIn shows your profile in searches for endorsed skills. Get peers to endorse you.",
        metadata={"category": "linkedin", "topic": "LinkedIn Optimization", "source": "career_guidance"},
    ),
    SeedDocument(
        doc_id="cg_jobsearch_001",
        content="Job search strategy for AI/ML roles in India (2024):\nWhere to apply: LinkedIn Jobs (best for product companies), Naukri.com (service companies), Cutshort (startups), Instahyre (funded startups), company career pages directly.\nWhen to apply: Set up job alerts for 'AI Engineer fresher', 'ML Engineer', 'Python Developer AI'. Apply within 24 hours of posting — response rates drop dramatically after 48 hours.\nReferrals: 40% of hires come through referrals. Message alumni from your college at target companies on LinkedIn.\nApplication volume: Apply to 5-10 positions per day. Track in a spreadsheet.\nTarget companies for AI freshers: TCS iON, Infosys Nia, Wipro AI, Freshworks, Razorpay, MathWorks, Siemens, Bosch India, NVIDIA India, Samsung R&D.",
        metadata={"category": "job_search", "topic": "Job Search", "source": "career_guidance"},
    ),
    SeedDocument(
        doc_id="cg_portfolio_001",
        content="Building a portfolio for AI/ML roles:\nMust-have projects: (1) End-to-end ML project with EDA + model + deployment. (2) NLP project (sentiment analysis, chatbot, or text classifier). (3) One agentic AI project using LangChain/LangGraph. (4) REST API with FastAPI + PostgreSQL.\nGitHub best practices: Each project needs a README with: what it does, tech stack, how to run it, screenshots/demo. Commit history shows consistent work — avoid single giant commits.\nDemo options: Deploy free on Render/Railway/Hugging Face Spaces. A live demo link doubles interview callbacks.\nBlog/Documentation: Write a short post about each project on Dev.to or Medium. Recruiters Google your name — make sure they find your work.",
        metadata={"category": "portfolio", "topic": "Portfolio Building", "source": "career_guidance"},
    ),
]

# ── 5. Company Information ─────────────────────────────────────────────────────

COMPANY_INFO: list[SeedDocument] = [
    SeedDocument(
        doc_id="ci_tcs_001",
        content="TCS (Tata Consultancy Services) — hiring process and tech stack:\nHiring process: (1) NQT (National Qualifier Test) — aptitude, reasoning, verbal, coding. Cutoff ~60-70%. (2) Technical interview — core CS fundamentals, 1-2 coding problems (easy LeetCode level), project discussion. (3) HR interview — standard questions.\nTech stack: Java, Python, C++, SQL, React, Angular, Spring Boot, Microservices.\nFor AI roles (TCS iON, TCS Research): Additional ML/DL screening, Python proficiency test, case study on AI application.\nPreparation tips: Strong aptitude + DSA basics. Know your resume projects well. SQL queries (joins, aggregations). TCS CodeVita for competitive coding track.",
        metadata={"company": "TCS", "category": "company_info", "country": "India"},
    ),
    SeedDocument(
        doc_id="ci_zoho_001",
        content="Zoho Corporation — hiring process and tech stack:\nHiring process: (1) Written test — very strong focus on programming logic, algorithms, and aptitude. Multiple rounds. (2) Technical interviews (2-3 rounds) — deep dive into your projects, coding problems, system design basics. Very thorough. (3) HR round.\nTech stack: In-house stack including Java, C++, Python, React, their own database systems.\nCulture: Known for building everything in-house. Values deep technical knowledge and long-term thinking. Less interested in framework knowledge, more in problem-solving fundamentals.\nPreparation tips: Strong fundamentals (OOP, OS, DBMS, networking). Real project experience with depth. Be prepared to discuss any line of code you wrote. Zoho hires for potential, not pedigree.",
        metadata={"company": "Zoho", "category": "company_info", "country": "India"},
    ),
    SeedDocument(
        doc_id="ci_google_001",
        content="Google India — hiring process for SWE/AI roles:\nHiring process: (1) Online assessment — 2 LeetCode-style problems, 90 minutes. (2) Phone screen — 1 coding problem + discussion. (3) Onsite (4-5 rounds): Coding (2 rounds), System Design (1 round for SWE-II+), Behavioural (Googleyness), Role-specific.\nTech stack: Python, C++, Java, Go, internal tools (Colossus, Spanner, MapReduce descendants).\nFor AI/ML roles: Additional ML system design round. Deep knowledge of ML fundamentals expected. Research papers on recent ML advances.\nPreparation: 3-6 months intensive LeetCode (Medium/Hard). System Design resources: Designing Data-Intensive Applications book, Grokking System Design. STAR format for behavioural questions.",
        metadata={"company": "Google", "category": "company_info", "country": "India"},
    ),
    SeedDocument(
        doc_id="ci_freshworks_001",
        content="Freshworks — hiring process and tech stack:\nHiring process: (1) Online coding assessment — 2-3 problems (Medium difficulty). (2) Technical interview — projects deep-dive, coding, system design basics. (3) Cultural fit interview.\nTech stack: Ruby on Rails, Python, React, Java, Kafka, Redis, PostgreSQL, AWS.\nFor data/AI roles: Python, ML frameworks, SQL proficiency, experience with large-scale data processing.\nInternship: Strong intern→FTE conversion. Projects are given real ownership from day 1.\nCulture: Fast-moving, customer-obsessed product company. Values ownership, speed, and impact. Strong Chennai engineering team. Good for freshers who want startup-like ownership at scale.",
        metadata={"company": "Freshworks", "category": "company_info", "country": "India"},
    ),
]
