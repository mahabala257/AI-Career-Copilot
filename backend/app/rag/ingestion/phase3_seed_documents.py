"""
app/rag/ingestion/phase3_seed_documents.py
───────────────────────────────────────────
Seed documents for Phase 3 RAG collections:

  company_information    — Tech stacks, interview processes, culture for top companies
  internship_information — Internship programs, timelines, stipends, selection processes
  wellness_resources     — Reframing techniques, burnout signals, motivational frameworks
"""

from app.rag.ingestion.seed_documents import SeedDocument


# ─────────────────────────────────────────────────────────────────────────────
# COLLECTION 1 — company_information
# ─────────────────────────────────────────────────────────────────────────────

COMPANY_INFORMATION: list[SeedDocument] = [

    SeedDocument(
        doc_id="ci_google_001",
        content=(
            "Google — Engineering Culture and Interview Process:\n\n"
            "Company type: Product-based, FAANG\n"
            "Tech stack: Go, Python, Java, C++, Kubernetes, Spanner, Bigtable, Borg\n\n"
            "Interview process (SWE): 1 recruiter screen → 1 phone technical → "
            "4-5 on-site (2 coding, 1 system design, 1 Googleyness/behavioral, 1 optional). "
            "Total: 5-7 rounds over 4-6 weeks.\n\n"
            "What they test: Data structures & algorithms (LeetCode hard level), "
            "system design at scale (billions of users), Googleyness (collaboration, "
            "ambiguity handling, impact focus).\n\n"
            "Engineering culture: 20% projects exist on paper but rarely in practice. "
            "Strong emphasis on data-driven decisions, code review culture, "
            "OKRs (Objectives and Key Results). Engineers own their projects end-to-end.\n\n"
            "Typical offers (India, 2024): SWE-L3: ₹25-45 LPA, SWE-L4: ₹45-80 LPA\n"
            "Glassdoor rating: 4.3/5\n\n"
            "Top prep tips: (1) LeetCode 100+ medium/hard problems minimum. "
            "(2) System Design Primer + Designing Data-Intensive Applications (book). "
            "(3) Practice explaining your thought process out loud. "
            "(4) Google values HOW you approach problems more than just the answer."
        ),
        metadata={"company": "google", "category": "interview_process",
                  "company_type": "product", "tier": "faang"},
    ),
    SeedDocument(
        doc_id="ci_microsoft_001",
        content=(
            "Microsoft — Engineering Culture and Interview Process:\n\n"
            "Company type: Product-based, FAANG\n"
            "Tech stack: C#, .NET, Python, TypeScript, Azure, SQL Server, "
            "C++, Rust (increasingly). Teams vary significantly by division.\n\n"
            "Interview process (SWE): 1 recruiter call → 1-2 technical screens → "
            "4-5 on-site (coding, design, behavioral). 'As Appropriate' interview "
            "with a senior engineer who makes the final hire/no-hire recommendation.\n\n"
            "What they test: Coding (medium LeetCode, focus on correctness over speed), "
            "OOP design, system design, behavioral (STAR format strongly expected).\n\n"
            "Culture: Growth Mindset (Satya Nadella's emphasis). Less cutthroat than Google. "
            "Work-life balance is better than most FAANG. Strong internal mobility.\n\n"
            "Typical offers (India, 2024): SDE-1: ₹30-50 LPA, SDE-2: ₹50-90 LPA\n"
            "Glassdoor rating: 4.2/5\n\n"
            "Top prep tips: (1) Microsoft values clean code and walking through your logic. "
            "(2) Prepare behavioral answers — more weight than at Google. "
            "(3) Know OOP principles deeply. (4) Azure knowledge helps but not required for SDE."
        ),
        metadata={"company": "microsoft", "category": "interview_process",
                  "company_type": "product", "tier": "faang"},
    ),
    SeedDocument(
        doc_id="ci_amazon_001",
        content=(
            "Amazon — Engineering Culture and Interview Process:\n\n"
            "Company type: Product-based, FAANG\n"
            "Tech stack: Java, Python, AWS (EC2, S3, DynamoDB, Lambda), "
            "React, Node.js. Heavily Java-based backend.\n\n"
            "Interview process: Online assessment (coding + debugging + work simulation) → "
            "3-5 virtual on-site loops. EACH round has 2 leadership principle (LP) questions "
            "and 1 coding/design question.\n\n"
            "Amazon Leadership Principles (LPs) — CRITICAL: Amazon is unique in that "
            "behavioral questions (using LPs) carry equal or MORE weight than coding. "
            "14 LPs include: Customer Obsession, Bias for Action, Dive Deep, "
            "Deliver Results, Invent & Simplify, Ownership.\n\n"
            "What they test: DSA (LeetCode medium), system design (at Amazon scale: "
            "millions of transactions), LP-based behavioral (STAR with quantified impact).\n\n"
            "Typical offers (India, 2024): SDE-1: ₹30-55 LPA, SDE-2: ₹55-100 LPA\n"
            "Glassdoor rating: 3.8/5 (lower due to high-pressure culture)\n\n"
            "Top prep tips: (1) Prepare 3-5 detailed STAR stories for each LP. "
            "(2) QUANTIFY everything — 'reduced latency by 40%' not 'made it faster'. "
            "(3) Amazon's bar for coding is high but LPs can make or break you."
        ),
        metadata={"company": "amazon", "category": "interview_process",
                  "company_type": "product", "tier": "faang"},
    ),
    SeedDocument(
        doc_id="ci_zoho_001",
        content=(
            "Zoho — Engineering Culture and Interview Process:\n\n"
            "Company type: Product-based, bootstrapped, India-HQ\n"
            "Tech stack: Java, C++, Python, JavaScript, Zoho's internal frameworks, "
            "ManageEngine tools. Strong proprietary tech culture.\n\n"
            "Interview process: Written test (aptitude + coding in C/C++/Java) → "
            "2-3 technical rounds → HR round. Tests are harder than typical service companies.\n\n"
            "What they test: Strong fundamentals (OS, networking, data structures, OOP), "
            "programming skills in system-level languages (C, C++, Java), "
            "problem-solving ability. Less emphasis on LeetCode, more on fundamentals.\n\n"
            "Culture: No VC funding, employee-first culture. Good work-life balance. "
            "Strong internal training (Zoho Schools of Learning). "
            "Most engineers spend 5+ years at Zoho — low attrition.\n\n"
            "Typical offers (India, 2024): Fresher: ₹6-10 LPA, Experienced: ₹12-25 LPA\n"
            "Glassdoor rating: 3.9/5\n\n"
            "Top prep tips: (1) Be VERY strong in C/C++ or Java fundamentals. "
            "(2) OS concepts (threads, processes, memory management) are tested. "
            "(3) Zoho values breadth of knowledge over LeetCode grinding. "
            "(4) Prepare for a long process — takes 3-6 weeks typically."
        ),
        metadata={"company": "zoho", "category": "interview_process",
                  "company_type": "product", "tier": "mid"},
    ),
    SeedDocument(
        doc_id="ci_razorpay_001",
        content=(
            "Razorpay — Engineering Culture and Interview Process:\n\n"
            "Company type: Fintech startup, unicorn, India-HQ\n"
            "Tech stack: Go, Python, Node.js, React, PostgreSQL, Redis, Kafka, AWS\n\n"
            "Interview process: Recruiter screen → 1-2 technical screens → "
            "3-4 on-site (coding, system design, engineering manager round). "
            "Total: 4-6 rounds in 3-4 weeks.\n\n"
            "What they test: DSA (LeetCode medium), distributed systems "
            "(payments must be reliable at scale), API design, fintech domain knowledge "
            "(not mandatory but impressive).\n\n"
            "Culture: High ownership, fast-paced. Engineers ship to production frequently. "
            "Strong product + engineering collaboration. Good stock options (post-IPO potential).\n\n"
            "Typical offers (India, 2024): SDE-1: ₹18-30 LPA, SDE-2: ₹30-55 LPA\n"
            "Glassdoor rating: 4.1/5\n\n"
            "Top prep tips: (1) Understand payment flows (payment gateway, settlements). "
            "(2) System design at fintech scale: idempotency, exactly-once semantics. "
            "(3) Know Go or be prepared to learn fast — dominant backend language."
        ),
        metadata={"company": "razorpay", "category": "interview_process",
                  "company_type": "startup", "tier": "unicorn"},
    ),
    SeedDocument(
        doc_id="ci_freshworks_001",
        content=(
            "Freshworks — Engineering Culture and Interview Process:\n\n"
            "Company type: Product-based SaaS, public company (NYSE: FRSH), India-HQ\n"
            "Tech stack: Ruby on Rails, React, Python, Go, PostgreSQL, Redis, AWS\n\n"
            "Interview process: Online coding test → 2 technical rounds → "
            "culture fit round → HR. Usually 3-4 weeks total.\n\n"
            "What they test: Web development fundamentals (REST APIs, databases), "
            "DSA (LeetCode easy-medium), product thinking, customer-centric mindset.\n\n"
            "Culture: SaaS company with strong product focus. Good benefits, "
            "work-life balance better than most. Chennai HQ with offices in Bangalore. "
            "Strong women in tech initiatives.\n\n"
            "Typical offers (India, 2024): SDE-1: ₹15-25 LPA, SDE-2: ₹28-45 LPA\n"
            "Glassdoor rating: 4.0/5\n\n"
            "Top prep tips: (1) Know Ruby basics or be enthusiastic about learning. "
            "(2) Customer empathy is important in behavioral rounds. "
            "(3) Good entry point for product company experience."
        ),
        metadata={"company": "freshworks", "category": "interview_process",
                  "company_type": "product", "tier": "mid"},
    ),
    SeedDocument(
        doc_id="ci_infosys_wipro_tcs_001",
        content=(
            "Infosys / Wipro / TCS — Service Company Interview Patterns:\n\n"
            "Company type: IT services (not product), India's largest employers\n"
            "Tech stack: Varies by client project. Java, Python, .NET, SAP, Oracle common.\n\n"
            "Interview process (all three similar):\n"
            "1. Online test: Aptitude (quant, verbal, logical reasoning) + coding (easy)\n"
            "2. Technical interview: Core CS (Java/OOP/SQL), basic DSA, project discussion\n"
            "3. HR round: Career goals, flexibility, salary negotiation\n\n"
            "What they look for: Communication skills, willingness to relocate/travel, "
            "basic programming skills, stability (they invest heavily in training freshers).\n\n"
            "Reality check: These are service companies. You work on CLIENT projects, "
            "not building products. Work varies from interesting to mundane depending on "
            "which client/project you're assigned. Good for initial experience and resume building.\n\n"
            "Typical offers (India, 2024 freshers): ₹3.6-7 LPA for campus, ₹6-12 LPA lateral\n"
            "Glassdoor ratings: TCS 3.8, Infosys 3.9, Wipro 3.7\n\n"
            "Exit opportunities: After 2-3 years, service company experience helps you "
            "move to product companies. Many use this as a stepping stone."
        ),
        metadata={"company": "infosys_wipro_tcs", "category": "interview_process",
                  "company_type": "service", "tier": "service"},
    ),
    SeedDocument(
        doc_id="ci_general_startup_001",
        content=(
            "Indian Tech Startup Interview Patterns (Series A-C, 50-500 employees):\n\n"
            "Examples: Meesho, Groww, CRED, Slice, Zetwerk, Licious\n\n"
            "What makes startup interviews different:\n"
            "1. SPEED: Entire process in 1-2 weeks. Startups can't wait months.\n"
            "2. CULTURE FIT: More important than at large companies. "
            "You'll meet founders/early team members.\n"
            "3. BREADTH: They want engineers who can do multiple things. "
            "Avoid saying 'that's not my area'.\n"
            "4. IMPACT: They want to know what YOU specifically built, not your team.\n\n"
            "Typical rounds: Intro call (30 min) → coding challenge (take-home or live) → "
            "technical deep dive → founder/engineering manager round\n\n"
            "What they test: Can you ship fast? Have you owned things end to end? "
            "Do you handle ambiguity well? Would you fit our culture?\n\n"
            "Salary: Base often lower than big companies but equity (ESOPs) can be valuable. "
            "Total comp at good startups: SDE-1: ₹15-30 LPA + equity\n\n"
            "Prep tips: (1) Research the startup's product deeply — know what they sell and why. "
            "(2) Have examples of shipping things fast. (3) Show genuine enthusiasm for the problem space."
        ),
        metadata={"company": "general_startup", "category": "interview_process",
                  "company_type": "startup", "tier": "startup"},
    ),
]


# ─────────────────────────────────────────────────────────────────────────────
# COLLECTION 2 — internship_information
# ─────────────────────────────────────────────────────────────────────────────

INTERNSHIP_INFORMATION: list[SeedDocument] = [

    SeedDocument(
        doc_id="ii_microsoft_intern_001",
        content=(
            "Microsoft India Internship Program:\n\n"
            "Program name: Microsoft Explore (freshers) / Regular SWE Intern (2nd-3rd year)\n"
            "Duration: 2 months (May-June) for most roles\n"
            "Stipend: ₹80,000 - ₹1,00,000/month (among highest in India)\n"
            "Locations: Hyderabad (primary), Bangalore\n\n"
            "Application window: August - October for summer internships\n"
            "College eligibility: IIT/NIT/BITS/IIIT tier colleges primarily for campus. "
            "Off-campus possible via LinkedIn but competitive.\n\n"
            "Selection process: Online coding test (2 DSA problems, medium difficulty) → "
            "2 technical interview rounds → 1 HR round\n\n"
            "PPO likelihood: Very high — 60-70% of interns who perform well get PPO\n\n"
            "What they look for: Strong DSA fundamentals, collaborative mindset, "
            "communication skills, curiosity about technology.\n\n"
            "Skills needed: Data structures, algorithms, OOP, one strong programming language "
            "(C++, Java, Python), basic system design concepts\n\n"
            "How to apply: Microsoft Careers website, campus placements at tier 1 colleges, "
            "or LinkedIn when off-campus postings open (usually September-November)"
        ),
        metadata={"company": "microsoft", "program_type": "summer",
                  "education_level": "undergraduate", "country": "india",
                  "stipend_tier": "high", "category": "internship"},
    ),
    SeedDocument(
        doc_id="ii_google_intern_001",
        content=(
            "Google India Internship Program (STEP and SWE Intern):\n\n"
            "Programs: STEP Internship (1st-2nd year undergrad) / "
            "SWE Intern (3rd year+/postgrad)\n"
            "Duration: 10-12 weeks (May-July)\n"
            "Stipend: ₹1,00,000 - ₹1,50,000/month + housing allowance (highest in India)\n"
            "Location: Bangalore (primary), Hyderabad\n\n"
            "Application window: STEP opens July-August. SWE Intern opens September-November.\n"
            "College eligibility: Primarily IITs for campus. Off-campus via Google Careers.\n\n"
            "Selection process: 1-2 coding interviews (LeetCode medium-hard), "
            "1 Googleyness interview for SWE interns\n\n"
            "PPO likelihood: Moderate-high — strong performers (~50%) get return offers\n\n"
            "What they look for: Strong problem-solving, clean code, "
            "thinking out loud during interviews, passion for computing.\n\n"
            "Skills needed: Advanced DSA (graphs, DP, trees), "
            "ability to code in interview conditions, communication\n\n"
            "How to apply: Google Careers (careers.google.com), "
            "campus recruiting at IIT/BITS/NIT, GHCI conference for women"
        ),
        metadata={"company": "google", "program_type": "summer",
                  "education_level": "undergraduate", "country": "india",
                  "stipend_tier": "high", "category": "internship"},
    ),
    SeedDocument(
        doc_id="ii_razorpay_intern_001",
        content=(
            "Razorpay Summer Internship Program:\n\n"
            "Program: SDE / Product Intern\n"
            "Duration: 2 months (May-June)\n"
            "Stipend: ₹50,000 - ₹80,000/month\n"
            "Location: Bangalore\n\n"
            "Application window: October - December (apply early, spots fill fast)\n"
            "College eligibility: Open to all tiers via off-campus. "
            "Campus visits to select colleges.\n\n"
            "Selection process: Online coding test → 2 technical interviews → culture fit\n\n"
            "PPO likelihood: High — Razorpay converts most interns who perform well\n\n"
            "What they look for: Product curiosity (understand payment flows), "
            "strong coding (Go/Python preferred), high ownership mentality.\n\n"
            "Skills needed: API development, DSA basics, database concepts, "
            "understanding of payment/fintech (bonus)\n\n"
            "How to apply: Razorpay Careers website, LinkedIn, Internshala, "
            "referrals (most effective — connect with Razorpay engineers on LinkedIn)"
        ),
        metadata={"company": "razorpay", "program_type": "summer",
                  "education_level": "undergraduate", "country": "india",
                  "stipend_tier": "high", "category": "internship"},
    ),
    SeedDocument(
        doc_id="ii_tier2_options_001",
        content=(
            "Internship Options for Tier 2/3 College Students in India:\n\n"
            "Reality: FAANG internships are extremely competitive for Tier 2/3 students. "
            "Less than 1% of Tier 2 students and almost no Tier 3 students get them. "
            "Here are realistic and excellent alternatives:\n\n"
            "EXCELLENT OPTIONS FOR TIER 2 STUDENTS:\n"
            "1. Zoho — Tests fundamentals not pedigree. Good stipend (₹20,000-40,000/month). "
            "Apply via Zoho Careers website.\n"
            "2. Freshworks — Internship portal + campus visits to select colleges. "
            "₹30,000-50,000/month.\n"
            "3. Walmart Global Tech India — Open to all tiers. Strong DSA + system design. "
            "₹40,000-70,000/month.\n"
            "4. Tata Digital / Tata 1mg — Product company under TCS umbrella. "
            "₹20,000-40,000/month.\n"
            "5. Series B/C startups — Best learning environment. "
            "Platforms: Internshala, AngelList, WorkAtAStartup.\n\n"
            "FOR TIER 3 STUDENTS:\n"
            "1. Service companies (Infosys InStep, TCS Research, Wipro). "
            "Free training, stipend ₹10,000-20,000/month.\n"
            "2. Startups under 50 people — Apply cold via email. "
            "Small teams give real responsibilities.\n"
            "3. Build 2-3 strong personal projects + GitHub — "
            "This matters more than your college for off-campus applications.\n\n"
            "KEY INSIGHT: Your projects and GitHub matter MORE than your college for off-campus. "
            "A Tier 3 student with 3 strong deployed projects beats a Tier 1 student with none."
        ),
        metadata={"company": "general", "program_type": "summer",
                  "education_level": "undergraduate", "country": "india",
                  "stipend_tier": "medium", "category": "internship"},
    ),
    SeedDocument(
        doc_id="ii_application_timeline_001",
        content=(
            "India Campus Internship Application Timeline (Summer Internships):\n\n"
            "APRIL-MAY (1 year before):\n"
            "- Build/strengthen GitHub profile with 2-3 deployed projects\n"
            "- Start DSA practice on LeetCode (50+ problems before you apply)\n"
            "- Connect with seniors who interned at target companies\n\n"
            "JULY-AUGUST:\n"
            "- Google STEP and some Microsoft programs open applications\n"
            "- Update resume with summer projects\n"
            "- Apply to Google STEP if 1st/2nd year\n\n"
            "SEPTEMBER-OCTOBER:\n"
            "- PRIME APPLICATION SEASON for most companies\n"
            "- Microsoft, Amazon, Flipkart, Razorpay, Freshworks all open here\n"
            "- Apply to ALL target companies simultaneously — don't wait\n"
            "- Campus placement season begins at IITs/NITs\n\n"
            "NOVEMBER-DECEMBER:\n"
            "- Late applications: Zoho, smaller startups, service companies\n"
            "- Off-campus applications still possible on LinkedIn/Internshala\n\n"
            "JANUARY-FEBRUARY:\n"
            "- Most campus processes conclude\n"
            "- Off-campus still open at many startups\n"
            "- If no offer yet: cold apply to 50+ startups via email + LinkedIn\n\n"
            "MISTAKE TO AVOID: Waiting until November to start applying. "
            "The best opportunities close in October."
        ),
        metadata={"company": "general", "program_type": "summer",
                  "education_level": "undergraduate", "country": "india",
                  "stipend_tier": "general", "category": "internship_timeline"},
    ),
    SeedDocument(
        doc_id="ii_skills_preparation_001",
        content=(
            "Skills Required for Competitive Tech Internships in India:\n\n"
            "MINIMUM BAR (must have for any product company):\n"
            "- Data Structures: Arrays, Strings, Linked Lists, Stacks, Queues, Trees, Graphs\n"
            "- Algorithms: Sorting, Binary Search, BFS/DFS, Dynamic Programming (basics)\n"
            "- One strong language: Python or Java or C++ (know it deeply, not surface-level)\n"
            "- Basic SQL: SELECT, JOIN, GROUP BY, subqueries\n"
            "- Git: commit, branch, merge, pull request workflow\n\n"
            "DIFFERENTIATORS (stand out above minimum bar):\n"
            "- 2-3 deployed projects with real users or impressive scale\n"
            "- Web development: REST API (FastAPI/Django/Node), basic React\n"
            "- Cloud: at least one of AWS/GCP/Azure basics (free tier)\n"
            "- System design basics: database choice, caching, load balancing concepts\n\n"
            "FOR AI/ML INTERNSHIPS SPECIFICALLY:\n"
            "- Python (non-negotiable), NumPy, Pandas, Matplotlib\n"
            "- One ML framework: scikit-learn minimum, PyTorch/TensorFlow preferred\n"
            "- Statistics basics: mean, variance, distributions, hypothesis testing\n"
            "- One ML project deployed (even simple Flask API for a model)\n\n"
            "TIMELINE TO PREPARE:\n"
            "- 3 months before applying: Start LeetCode + one framework\n"
            "- 2 months before: Build a project end-to-end and deploy it\n"
            "- 1 month before: Mock interviews + company-specific prep"
        ),
        metadata={"company": "general", "program_type": "general",
                  "education_level": "undergraduate", "country": "india",
                  "stipend_tier": "general", "category": "internship_skills"},
    ),
]


# ─────────────────────────────────────────────────────────────────────────────
# COLLECTION 3 — wellness_resources
# ─────────────────────────────────────────────────────────────────────────────

WELLNESS_RESOURCES: list[SeedDocument] = [

    SeedDocument(
        doc_id="wr_rejection_001",
        content=(
            "Reframing Job Rejection — Evidence-Based Perspective:\n\n"
            "THE STATISTICS: Top tech companies reject 95-99% of applicants. "
            "Google rejects over 99% of applications. This means rejection is the "
            "NORMAL outcome, not evidence of failure.\n\n"
            "WHAT REJECTION ACTUALLY TELLS YOU:\n"
            "- Interview performance is partly random (bad day, hard interviewer, wrong problem)\n"
            "- Cultural fit is subjective — rejected by Google doesn't mean rejected by Zoho\n"
            "- 'Rejected' often means 'not right for THIS role at THIS time' not 'not good enough'\n\n"
            "PRODUCTIVE REFRAME: Each rejection is calibration data. It tells you:\n"
            "1. Which skills to strengthen (if technical)\n"
            "2. Which companies to target differently (if cultural mismatch)\n"
            "3. How to improve your interview communication\n\n"
            "WHAT RESEARCHERS FOUND: People who land jobs after rejection typically "
            "submitted 40-60 applications. If you've only sent 5-10, you're still early "
            "in the process, not failing.\n\n"
            "IMMEDIATE ACTION after rejection: Email the recruiter asking for specific feedback. "
            "Many won't reply, but some will. That feedback is invaluable.\n\n"
            "RECOVERY TIMELINE: Allow yourself 24-48 hours to feel disappointed. "
            "After that, shift to the next application. Dwelling longer than 48 hours "
            "on a single rejection actively harms your confidence in future interviews."
        ),
        metadata={"content_type": "reframe", "situation": "rejection",
                  "tone": "empathetic", "category": "wellness"},
    ),
    SeedDocument(
        doc_id="wr_burnout_001",
        content=(
            "Burnout Recognition and Recovery for Job Seekers:\n\n"
            "BURNOUT SIGNALS IN JOB SEARCH CONTEXT:\n"
            "- Feeling dread before every application or interview prep session\n"
            "- Score plateau: quiz/practice scores stopped improving for 7+ days\n"
            "- Applying jobs without reading the description properly\n"
            "- Comparing yourself to peers constantly\n"
            "- Sleep disruption due to job search anxiety\n"
            "- Losing interest in the field you're preparing for\n\n"
            "BURNOUT LEVELS AND RESPONSES:\n\n"
            "LOW RISK (1-2 signals): Reduce daily hours by 30%. Add one non-career activity daily.\n\n"
            "MEDIUM RISK (3-4 signals): Take a 2-day complete break. No LeetCode, "
            "no applications, no career content. Return with a reduced daily target (1-2 hours max).\n\n"
            "HIGH RISK (5+ signals or feeling hopeless): Take a full week off. "
            "Talk to someone you trust. Consider speaking with a counsellor. "
            "Your career will still be there after you recover. Pushing through "
            "high burnout makes performance WORSE, not better.\n\n"
            "RECOVERY STRATEGIES:\n"
            "1. Physical exercise — 30 minutes daily reduces cortisol significantly\n"
            "2. Social connection — isolation amplifies burnout\n"
            "3. Small wins — switch from hard problems to easy ones temporarily\n"
            "4. Progress journaling — write what you DID accomplish each day\n"
            "5. Timeline perspective — most people who are consistent land a role in 3-6 months"
        ),
        metadata={"content_type": "strategy", "situation": "burnout",
                  "tone": "direct", "category": "wellness"},
    ),
    SeedDocument(
        doc_id="wr_imposter_001",
        content=(
            "Imposter Syndrome in Tech — Practical Reframes:\n\n"
            "WHAT IMPOSTER SYNDROME ACTUALLY IS: The feeling that you're not good enough "
            "and will be 'found out' — despite evidence to the contrary. "
            "Studies show 70% of people experience it, including senior engineers and "
            "executives. It's extremely common in tech, especially for:\n"
            "- Career changers\n"
            "- Students from non-IIT/NIT backgrounds\n"
            "- Women in tech\n"
            "- First-generation tech professionals\n\n"
            "USEFUL REFRAMES:\n"
            "1. 'Everyone knows more than me' → Wrong. Everyone SEEMS to know more in public. "
            "In private, they Google the same things you do.\n\n"
            "2. 'I got lucky in interviews' → Preparation looks like luck from the outside. "
            "If you prepared, you earned it.\n\n"
            "3. 'I don't deserve to apply to [Company]' → Companies don't care about deserve. "
            "They care about whether you can do the job. Let them decide.\n\n"
            "4. 'My college is not good enough' → College tier matters less after your "
            "first job. Projects, skills, and work ethic matter more.\n\n"
            "PRACTICAL TOOL — The Evidence List: Write down 10 things you know how to do "
            "that you didn't know 1 year ago. Read this list when imposter syndrome hits.\n\n"
            "WHEN IT'S NOT IMPOSTER SYNDROME: If you genuinely haven't prepared, "
            "that's not imposter syndrome — that's accurate self-assessment. "
            "The fix is preparation, not reframing."
        ),
        metadata={"content_type": "reframe", "situation": "imposter_syndrome",
                  "tone": "direct", "category": "wellness"},
    ),
    SeedDocument(
        doc_id="wr_comparison_001",
        content=(
            "Comparison Trap — Why You're Comparing Your Chapter 1 to Someone's Chapter 10:\n\n"
            "THE PROBLEM WITH COMPARISON IN JOB SEARCH:\n"
            "- LinkedIn shows curated wins, not the 50 rejections before the offer\n"
            "- 'My friend got placed at Google' — you don't know how many times they applied\n"
            "- Different starting points: family connections, coaching, luck all play roles\n"
            "- Academic performance ≠ job performance. Different skill sets.\n\n"
            "WHAT PRODUCTIVE COMPARISON LOOKS LIKE:\n"
            "Compare yourself to yourself 3 months ago, not to others.\n"
            "Questions to ask: Am I faster at DSA problems than 3 months ago? "
            "Do I understand system design better? Have I built more projects?\n\n"
            "TIMELINE REFRAME: The average software engineer lands their first job "
            "3-8 months after starting serious preparation. If you're at month 2, "
            "you're not behind — you're on track.\n\n"
            "SOCIAL MEDIA BREAK: If comparing yourself to LinkedIn posts is causing distress, "
            "a 2-week social media break is clinically shown to reduce anxiety and improve focus.\n\n"
            "WHAT ACTUALLY PREDICTS SUCCESS: Consistency over intensity. "
            "1 hour of focused practice daily for 6 months beats "
            "10-hour cramming sessions that lead to burnout."
        ),
        metadata={"content_type": "reframe", "situation": "comparison",
                  "tone": "empathetic", "category": "wellness"},
    ),
    SeedDocument(
        doc_id="wr_motivation_frameworks_001",
        content=(
            "Motivation Frameworks for Long Job Search Periods:\n\n"
            "WHY MOTIVATION FAILS (and what to use instead):\n"
            "Motivation is emotion-dependent. When you feel bad, motivation disappears. "
            "SYSTEMS replace the need for motivation:\n\n"
            "SYSTEM 1 — TIME BLOCKING (not task lists):\n"
            "Block specific hours: 'Monday 9-10am = LeetCode, no exceptions.' "
            "Don't decide each day whether to practice. The schedule decides.\n\n"
            "SYSTEM 2 — MINIMUM VIABLE COMMITMENT:\n"
            "On bad days, commit to only 20 minutes. "
            "Often you'll continue past 20 minutes (starting is the hardest part). "
            "If you don't, 20 minutes still beats zero.\n\n"
            "SYSTEM 3 — PROGRESS TRACKING:\n"
            "Track problems solved, applications sent, concepts learned — not feelings. "
            "On low-motivation days, seeing 'I solved 127 LeetCode problems' provides "
            "evidence-based confidence that feelings don't.\n\n"
            "SYSTEM 4 — ACCOUNTABILITY PARTNERS:\n"
            "Find someone preparing for similar roles. "
            "Daily check-ins (even a WhatsApp message: 'done 1hr today') "
            "dramatically improve consistency.\n\n"
            "SYSTEM 5 — REWARD ARCHITECTURE:\n"
            "After each study session: do something you enjoy for 30 minutes. "
            "Brain learns: 'study session → reward.' Motivation follows."
        ),
        metadata={"content_type": "strategy", "situation": "motivation",
                  "tone": "direct", "category": "wellness"},
    ),
    SeedDocument(
        doc_id="wr_quotes_001",
        content=(
            "Motivational Quotes for Job Seekers — Curated for Authenticity:\n\n"
            "On Persistence:\n"
            "\"It does not matter how slowly you go as long as you do not stop.\" — Confucius\n\n"
            "On Rejection:\n"
            "\"I have not failed. I've just found 10,000 ways that won't work.\" — Thomas Edison\n\n"
            "On Process:\n"
            "\"You don't rise to the level of your goals. You fall to the level of your systems.\" "
            "— James Clear\n\n"
            "On Comparison:\n"
            "\"The only person you should try to be better than is the person you were yesterday.\"\n\n"
            "On Starting:\n"
            "\"The secret of getting ahead is getting started.\" — Mark Twain\n\n"
            "On Bad Days:\n"
            "\"Even the darkest night will end and the sun will rise.\" — Victor Hugo\n\n"
            "On Effort:\n"
            "\"Hard work beats talent when talent doesn't work hard.\" — Tim Notke\n\n"
            "On Long Journeys:\n"
            "\"One day at a time. One problem at a time.\"\n\n"
            "Career-specific perspective:\n"
            "\"Your first job is not your last job. It's just your first.\" "
            "Every senior engineer you admire started with rejection letters."
        ),
        metadata={"content_type": "quote", "situation": "general",
                  "tone": "empathetic", "category": "wellness"},
    ),
    SeedDocument(
        doc_id="wr_india_mental_health_001",
        content=(
            "Mental Health Resources for Students and Job Seekers in India:\n\n"
            "CRISIS RESOURCES (available now):\n"
            "- iCall (TISS): 9152987821 | Monday-Saturday, 8am-10pm\n"
            "- Vandrevala Foundation: 1860-2662-345 | 24/7, free\n"
            "- iCALL WhatsApp: wa.me/919152987821\n"
            "- AASRA: 9820466627 | 24/7\n\n"
            "NON-CRISIS COUNSELLING:\n"
            "- YourDOST: yourdost.com — affordable online counselling\n"
            "- MindPeers: mindpeers.co — workplace/student mental health\n"
            "- Most universities have free counselling services — check your institution.\n\n"
            "WHEN TO SEEK HELP (not just when in crisis):\n"
            "- Persistent sadness lasting more than 2 weeks\n"
            "- Anxiety that stops you from doing basic daily tasks\n"
            "- Sleep disruption for more than 1 week\n"
            "- Loss of interest in things you previously enjoyed\n"
            "- Feeling hopeless about the future\n\n"
            "STIGMA NOTE: Seeking mental health support is a sign of strength, not weakness. "
            "It's a skill — learning to manage your mental health is as learnable as coding. "
            "Many top performers use therapists and coaches routinely."
        ),
        metadata={"content_type": "crisis_resource", "situation": "crisis",
                  "tone": "gentle", "category": "wellness"},
    ),
]
