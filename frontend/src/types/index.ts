// ── Auth ────────────────────────────────────────────────────────────────────
export interface User {
  id: string;
  name: string;
  email: string;
  target_role: string | null;
  current_skills: string[] | null;
  is_active: boolean;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface AuthResponse {
  user: User;
  tokens: TokenResponse;
}

// ── Resume ───────────────────────────────────────────────────────────────────
export interface ScoreBreakdown {
  skills_match: number;
  experience_relevance: number;
  education_fit: number;
  keyword_optimization: number;
  formatting_clarity: number;
}

export interface ResumeAnalysis {
  ats_score: number;
  extracted_skills: string[];
  missing_skills: string[];
  top_matching_skills: string[];
  critical_missing: string[];
  strengths: string[];
  suggestions: string[];
  experience_level: string;
  improvement_priority: string;
  score_breakdown: ScoreBreakdown | null;
  education_match: number;
  keyword_density_score: number;
  format_score: number;
  target_role: string;
  error_reason?: string;
}

export interface ResumeAnalysisResponse {
  resume_id: string;
  filename: string;
  page_count: number;
  word_count: number;
  sections: string[];
  analysis: ResumeAnalysis;
  parse_warnings: string[];
  agent_error: string | null;
  analyzed_at: string;
}

export interface ResumeHistoryItem {
  resume_id: string;
  filename: string;
  ats_score: number | null;
  analyzed_at: string | null;
  created_at: string;
  skills_count: number;
  missing_count: number;
}

// ── Skill Gap ────────────────────────────────────────────────────────────────
export interface MissingSkill {
  skill: string;
  category: string;
  priority: "critical" | "high" | "medium" | "low";
  why_important: string;
  time_to_learn: string;
  learning_resources: string[];
}

export interface MatchedSkill {
  skill: string;
  candidate_level: string;
  required_level: string;
  gap: string;
}

export interface SkillCategories {
  strong: string[];
  developing: string[];
  missing_critical: string[];
  missing_nice_to_have: string[];
}

export interface SkillGapAnalysis {
  target_role: string;
  overall_readiness_percent: number;
  current_skills: string[];
  required_skills: string[];
  matched_skills: MatchedSkill[];
  missing_skills: MissingSkill[];
  priority_order: string[];
  skill_categories: SkillCategories;
  months_to_job_ready: number;
  immediate_actions: string[];
  strengths_to_highlight: string[];
  error_reason?: string;
}

export interface SkillGapResponse {
  analysis: SkillGapAnalysis;
  agent_error: string | null;
  analyzed_at: string;
}

// ── Interview ────────────────────────────────────────────────────────────────
export type InterviewType = "hr" | "technical" | "coding";
export type Difficulty = "easy" | "medium" | "hard";

export interface QuestionItem {
  id: number;
  question: string;
  category: string;
  difficulty: string;
  expected_answer?: string;
  key_concepts?: string[];
  follow_up_questions?: string[];
  estimated_answer_time_minutes?: number;
  what_interviewer_looks_for?: string;
  model_answer_structure?: string;
  tips?: string[];
  common_mistakes?: string[];
  title?: string;
  examples?: Array<{ input: string; output: string; explanation?: string }>;
  hints?: string[];
  optimal_solution?: { approach: string; time: string; space: string; code: string };
  companies_asked?: string[];
}

export interface InterviewResponse {
  session_id: string;
  session_type: InterviewType;
  role: string;
  difficulty: string;
  questions: QuestionItem[];
  total_questions: number;
  estimated_duration_minutes: number;
  preparation_tips: string[];
  preparation_resources: string[];
  agent_error: string | null;
  generated_at: string;
}

export interface EvaluationItem {
  question_id: number;
  score: number;
  grade: string;
  strengths: string[];
  improvements: string[];
  feedback: string;
}

export interface EvaluationResponse {
  overall_score: number;
  overall_grade: string;
  evaluations: EvaluationItem[];
  readiness_assessment: string;
  top_improvement_areas: string[];
  interview_tips: string[];
  evaluated_at: string;
}

// ── Quiz ─────────────────────────────────────────────────────────────────────
export interface QuizQuestion {
  id: number;
  question: string;
  options?: Record<string, string>;
  topic_area: string;
  difficulty: string;
  function_signature?: string;
  examples?: Array<{ input: string; output: string }>;
  hints?: string[];
  time_limit_minutes?: number;
}

export interface QuizGenerateResponse {
  quiz_id: string;
  quiz_type: string;
  topic: string;
  difficulty: string;
  questions: QuizQuestion[];
  total_questions: number;
  topic_areas_covered: string[];
  agent_error: string | null;
  generated_at: string;
}

export interface QuestionResult {
  question_id: number;
  user_answer: string;
  correct_answer: string;
  is_correct: boolean;
  topic_area: string;
}

export interface QuizScoreResponse {
  quiz_id: string;
  total_questions: number;
  correct_answers: number;
  score_percent: number;
  grade: string;
  question_results: QuestionResult[];
  weak_areas: string[];
  strong_areas: string[];
  improvement_recommendations: string[];
  next_quiz_focus: string[];
  encouragement: string;
  scored_at: string;
}

// ── Planner ──────────────────────────────────────────────────────────────────
export interface StudySession {
  session_number: number;
  time_block: string;
  duration_hours: number;
  topic: string;
  tasks: string[];
  resources: Array<{ type: string; title: string; url?: string }>;
  goal: string;
}

export interface StudyDay {
  day: string;
  day_number?: number;
  theme?: string;
  focus_skill?: string;
  study_hours: number;
  tasks: string[];
  resources?: Array<{ type: string; title: string }>;
  mini_project?: string;
  career_action?: string | null;
  difficulty?: string;
}

export interface StudyWeek {
  week_number: number;
  theme: string;
  primary_skill: string;
  secondary_skill?: string;
  daily_hours: number;
  key_tasks: string[];
  milestone: string;
  interview_prep?: string;
  career_action?: string;
}

export interface StudyPlanData {
  plan_type: "daily" | "weekly" | "monthly";
  target_role: string;
  sessions?: StudySession[];     // daily
  days?: StudyDay[];             // weekly
  weeks?: StudyWeek[];           // monthly
  week_theme?: string;
  month_theme?: string;
  weekly_milestone?: string;
  week_project?: string;
  focus_skill?: string;
  motivational_note?: string;
  career_action?: string;
}

export interface PlanResponse {
  plan_id: string;
  plan_type: string;
  target_role: string;
  plan_data: StudyPlanData;
  agent_error: string | null;
  generated_at: string;
}

// ── Progress ─────────────────────────────────────────────────────────────────
export interface CareerScore {
  overall_score: number;
  components: {
    resume_score: number;
    skill_score: number;
    interview_score: number;
    quiz_score: number;
  };
  recommendations: string[];
  computed_at: string;
}

export interface ScoreHistory {
  overall_score: number;
  resume_score: number;
  skill_score: number;
  quiz_score: number;
  computed_at: string;
}

// ── LinkedIn ──────────────────────────────────────────────────────────────────
export interface LinkedInSections {
  headline: { current: string; optimized: string; reasoning: string };
  about: { current_summary: string; optimized: string; hook_score: number; reasoning: string };
  experience_bullets: Array<{ original: string; rewritten: string; improvement: string }>;
  skills_reorder: { recommended_top_3: string[]; skills_to_add: string[]; skills_to_remove: string[]; reasoning: string };
}
export interface LinkedInOptimizationResult {
  current_score: number;
  optimized_score: number;
  score_breakdown: Record<string, number>;
  sections: LinkedInSections;
  keyword_density: { present_keywords: string[]; missing_high_value_keywords: string[]; keyword_score: number };
  top_3_changes: string[];
  creator_tips: string[];
  profile_completeness_tips: string[];
  error_reason?: string | null;
}
export interface LinkedInOptimizeResponse {
  optimization_id: string;
  target_role: string;
  result: LinkedInOptimizationResult;
  agent_error: string | null;
  optimized_at: string;
}

// ── Projects ──────────────────────────────────────────────────────────────────
export interface TechStack { backend: string[]; frontend: string[]; ai_ml: string[]; database: string[]; devops: string[] }
export interface RecommendedProject {
  rank: number;
  title: string;
  one_liner: string;
  description: string;
  why_this_impresses: string;
  skills_demonstrated: string[];
  skills_learned: string[];
  estimated_weeks: number;
  difficulty: string;
  tech_stack: TechStack;
  github_readme_sections: string[];
  interview_talking_points: string[];
  scale_question: string;
  demo_tip: string;
}
export interface ProjectRecommendationResult {
  portfolio_score: number;
  portfolio_assessment: string;
  recommended_projects: RecommendedProject[];
  projects_to_avoid: Array<{ project: string; reason: string }>;
  portfolio_target_score: number;
  portfolio_action_plan: string[];
  error_reason?: string | null;
}
export interface ProjectRecommendResponse {
  recommendation_id: string;
  target_role: string;
  experience_level: string;
  result: ProjectRecommendationResult;
  agent_error: string | null;
  generated_at: string;
}

// ── English ───────────────────────────────────────────────────────────────────
export interface EnglishScores { grammar: number; fluency: number; structure: number; vocabulary: number; conciseness: number; overall: number }
export interface EnglishIssue { type: string; found: string; suggestion: string; explanation: string }
export interface StarCompliance { situation: boolean; task: boolean; action: boolean; result: boolean; score: number; missing: string; tip: string }
export interface PracticeScripts { elevator_pitch_30s: string; self_intro_2min: string; hr_answers: Record<string, string> }
export interface EnglishEvaluationResult {
  original_text: string;
  corrected_text: string;
  scores: EnglishScores;
  issues: EnglishIssue[];
  annotations: Array<{ original: string; corrected: string; reason: string }>;
  star_compliance: StarCompliance;
  vocabulary_upgrades: Array<{ weak: string; strong: string; context: string }>;
  practice_scripts: PracticeScripts;
  top_3_improvements: string[];
  encouragement: string;
  error_reason?: string | null;
}
export interface EnglishEvaluateResponse {
  evaluation_id: string;
  context_type: string;
  result: EnglishEvaluationResult;
  agent_error: string | null;
  evaluated_at: string;
}
export interface ScriptGenerateResponse {
  scripts: PracticeScripts;
  generated_at: string;
}

// ── Company Research ─────────────────────────────────────────────────────────
export interface InterviewRound { round: string; focus: string; tips: string }
export interface KnownQuestion { type: string; example: string }
export interface SkillAlignment { matching_skills: string[]; missing_skills: string[]; alignment_score: number }
export interface PrepStrategyWeek { week: number; focus: string; daily_hours: number; resources: string[] }
export interface TypicalOpening {
  role: string;
  work_mode: string;
  employment_type: string;
  salary_range: string;
  required_skills: string[];
}
export interface CompanyResearchResult {
  company_name: string;
  company_type: string;
  overview: string;
  tech_stack: string[];
  engineering_culture: string;
  interview_style: string;
  interview_rounds: InterviewRound[];
  culture_values: string[];
  known_question_types: KnownQuestion[];
  skill_alignment: SkillAlignment;
  prep_strategy: PrepStrategyWeek[];
  typical_timeline: string;
  salary_range: string;
  pros: string[];
  cons: string[];
  glassdoor_rating: number | null;
  application_tips: string[];
  typical_openings: TypicalOpening[];
  error_reason?: string | null;
}
export interface CompanyResearchResponse {
  research_id: string;
  company_name: string;
  target_role: string;
  result: CompanyResearchResult;
  agent_error: string | null;
  researched_at: string;
}

// ── Internship Research ──────────────────────────────────────────────────────
export interface RecommendedInternship {
  company: string;
  program_name: string;
  company_type: string;
  application_window: string;
  stipend_range: string;
  duration: string;
  selection_process: string[];
  ppo_likelihood: string;
  required_skills: string[];
  nice_to_have: string[];
  college_tier_accepted: string;
  application_platform: string;
  fit_score: number;
}
export interface CoverLetterOutline { opening: string; body: string; closing: string }
export interface PreparationPriority { priority: number; skill: string; why: string; resource: string }
export interface InternshipResearchResult {
  student_profile_summary: string;
  recommended_companies: RecommendedInternship[];
  application_timeline: Record<string, string>;
  cover_letter_outline: CoverLetterOutline;
  skill_gaps_for_internships: string[];
  preparation_priorities: PreparationPriority[];
  top_platforms: string[];
  resume_tips_for_internships: string[];
  networking_tips: string[];
  common_mistakes: string[];
  error_reason?: string | null;
}
export interface InternshipResearchResponse {
  research_id: string;
  target_role: string;
  education_level: string;
  result: InternshipResearchResult;
  agent_error: string | null;
  researched_at: string;
}

// ── Wellness ──────────────────────────────────────────────────────────────────
export interface BurnoutRisk { level: string; signals: string[]; recommendation: string }
export interface AdjustedStudyPlan { recommendation: string; reason: string }
export interface CrisisResources { india: Record<string, string>; message: string }
export interface WellnessResult {
  emotional_validation: string;
  reframe: string;
  next_single_action: string;
  progress_acknowledgment: string;
  burnout_risk: BurnoutRisk;
  motivational_quote: string;
  weekly_reflection_prompt: string;
  adjusted_study_plan: AdjustedStudyPlan;
  career_perspective: string;
  professional_help_note: string | null;
  professional_help_flag: boolean;
  crisis_resources: CrisisResources | null;
  error_reason?: string | null;
}
export interface WellnessCheckinResponse {
  checkin_id: string;
  result: WellnessResult;
  agent_error: string | null;
  checked_in_at: string;
}
