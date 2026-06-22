import axios, { type AxiosError } from "axios";
import { useAuthStore } from "@/stores/authStore";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 60000, // 60s for LLM calls
});

// Attach JWT on every request
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Auto-refresh on 401
let isRefreshing = false;
let failedQueue: Array<{ resolve: (v: string) => void; reject: (e: unknown) => void }> = [];

const processQueue = (error: unknown, token: string | null) => {
  failedQueue.forEach((p) => (error ? p.reject(error) : p.resolve(token!)));
  failedQueue = [];
};

api.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    const original = error.config as typeof error.config & { _retry?: boolean };
    if (error.response?.status === 401 && !original?._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then((token) => {
          original!.headers!.Authorization = `Bearer ${token}`;
          return api(original!);
        });
      }
      original!._retry = true;
      isRefreshing = true;
      try {
        const refreshToken = useAuthStore.getState().refreshToken;
        if (!refreshToken) throw new Error("No refresh token");
        const { data } = await axios.post(`${BASE_URL}/api/auth/refresh`, {
          refresh_token: refreshToken,
        });
        useAuthStore.getState().setTokens(data.access_token, data.refresh_token);
        processQueue(null, data.access_token);
        original!.headers!.Authorization = `Bearer ${data.access_token}`;
        return api(original!);
      } catch (e) {
        processQueue(e, null);
        useAuthStore.getState().logout();
        window.location.href = "/login";
        return Promise.reject(e);
      } finally {
        isRefreshing = false;
      }
    }
    return Promise.reject(error);
  }
);

// ── API functions ─────────────────────────────────────────────────────────────
export const authApi = {
  register: (d: { name: string; email: string; password: string; target_role?: string }) =>
    api.post("/api/auth/register", d).then((r) => r.data),
  login: (d: { email: string; password: string }) =>
    api.post("/api/auth/login", d).then((r) => r.data),
  me: () => api.get("/api/auth/me").then((r) => r.data),
  updateProfile: (d: { name?: string; target_role?: string; current_skills?: string[] }) =>
    api.patch("/api/auth/me", d).then((r) => r.data),
  logout: () => api.post("/api/auth/logout").then((r) => r.data),
};

export const resumeApi = {
  analyze: (file: File, targetRole: string) => {
    const form = new FormData();
    form.append("file", file);
    form.append("target_role", targetRole);
    return api.post("/api/resume/analyze", form, {
      headers: { "Content-Type": "multipart/form-data" },
    }).then((r) => r.data);
  },
  history: () => api.get("/api/resume/history").then((r) => r.data),
  getById: (id: string) => api.get(`/api/resume/${id}`).then((r) => r.data),
};

export const skillsApi = {
  analyze: (d: { target_role: string; current_skills?: string[]; generate_learning_path?: boolean }) =>
    api.post("/api/skills/analyze", d).then((r) => r.data),
  profile: () => api.get("/api/skills/profile").then((r) => r.data),
};

export const interviewApi = {
  generate: (d: { target_role: string; interview_type: string; difficulty: string }) =>
    api.post("/api/interview/generate", d).then((r) => r.data),
  evaluate: (d: { session_id: string; target_role: string; answers: Array<{ question_id: number; answer: string }> }) =>
    api.post("/api/interview/evaluate", d).then((r) => r.data),
  history: () => api.get("/api/interview/history").then((r) => r.data),
};

export const quizApi = {
  generate: (d: { topic?: string; difficulty?: string; quiz_type?: string }) =>
    api.post("/api/quiz/generate", d).then((r) => r.data),
  submit: (d: { quiz_id: string; answers: Array<{ question_id: number; answer: string }> }) =>
    api.post("/api/quiz/submit", d).then((r) => r.data),
};

export const plannerApi = {
  generate: (d: { plan_type: string; target_role?: string; available_hours?: number }) =>
    api.post("/api/planner/generate", d).then((r) => r.data),
  current: () => api.get("/api/planner/current").then((r) => r.data),
};

export const progressApi = {
  score: () => api.get("/api/progress/score").then((r) => r.data),
  history: () => api.get("/api/progress/history").then((r) => r.data),
};

export const linkedinApi = {
  optimize: (d: { headline?: string; about?: string; experience?: string; skills?: string[]; target_role: string }) =>
    api.post("/api/linkedin/optimize", d).then((r) => r.data),
  history: () => api.get("/api/linkedin/history").then((r) => r.data),
};

export const projectsApi = {
  recommend: (d: { target_role: string; experience_level?: string; time_available_weeks?: number }) =>
    api.post("/api/projects/recommend", d).then((r) => r.data),
  history: () => api.get("/api/projects/history").then((r) => r.data),
};

export const englishApi = {
  evaluate: (d: { spoken_text: string; context_type?: string; question?: string }) =>
    api.post("/api/english/evaluate", d).then((r) => r.data),
  generateScripts: (d: { experience_level?: string }) =>
    api.post("/api/english/scripts", d).then((r) => r.data),
  history: () => api.get("/api/english/history").then((r) => r.data),
};

export const companyApi = {
  research: (d: { company_name: string; target_role?: string }) =>
    api.post("/api/company/research", d).then((r) => r.data),
  history: () => api.get("/api/company/history").then((r) => r.data),
};

export const internshipApi = {
  research: (d: { target_role?: string; education_level?: string; college_tier?: string; available_from?: string }) =>
    api.post("/api/internship/research", d).then((r) => r.data),
  history: () => api.get("/api/internship/history").then((r) => r.data),
};

export const wellnessApi = {
  checkin: (d: { mood_message: string }) =>
    api.post("/api/wellness/checkin", d).then((r) => r.data),
  history: () => api.get("/api/wellness/history").then((r) => r.data),
};
