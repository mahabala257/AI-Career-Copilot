import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { useAuthStore } from "@/stores/authStore";
import Layout from "@/components/layout/Layout";
import LoginPage from "@/pages/LoginPage";
import RegisterPage from "@/pages/RegisterPage";
import DashboardPage from "@/pages/DashboardPage";
import ResumeAnalyzerPage from "@/pages/ResumeAnalyzerPage";
import SkillGapPage from "@/pages/SkillGapPage";
import InterviewCenterPage from "@/pages/InterviewCenterPage";
import QuizCenterPage from "@/pages/QuizCenterPage";
import StudyPlannerPage from "@/pages/StudyPlannerPage";
import ProfilePage from "@/pages/ProfilePage";
import LinkedInOptimizerPage from "@/pages/LinkedInOptimizerPage";
import ProjectRecommenderPage from "@/pages/ProjectRecommenderPage";
import EnglishCoachPage from "@/pages/EnglishCoachPage";
import CompanyResearchPage from "@/pages/CompanyResearchPage";
import InternshipResearchPage from "@/pages/InternshipResearchPage";
import WellnessCoachPage from "@/pages/WellnessCoachPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 5 * 60 * 1000 },
    mutations: { retry: 0 },
  },
});

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
}

function PublicRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  return !isAuthenticated ? <>{children}</> : <Navigate to="/" replace />;
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login"    element={<PublicRoute><LoginPage /></PublicRoute>} />
          <Route path="/register" element={<PublicRoute><RegisterPage /></PublicRoute>} />
          <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
            <Route index element={<DashboardPage />} />
            <Route path="resume"    element={<ResumeAnalyzerPage />} />
            <Route path="skills"    element={<SkillGapPage />} />
            <Route path="interview" element={<InterviewCenterPage />} />
            <Route path="quiz"      element={<QuizCenterPage />} />
            <Route path="planner"   element={<StudyPlannerPage />} />
            <Route path="linkedin"  element={<LinkedInOptimizerPage />} />
            <Route path="projects"  element={<ProjectRecommenderPage />} />
            <Route path="english"   element={<EnglishCoachPage />} />
            <Route path="company"    element={<CompanyResearchPage />} />
            <Route path="internship" element={<InternshipResearchPage />} />
            <Route path="wellness"   element={<WellnessCoachPage />} />
            <Route path="profile"   element={<ProfilePage />} />
            <Route path="*"         element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
        <Toaster />
      </BrowserRouter>
    </QueryClientProvider>
  );
}
