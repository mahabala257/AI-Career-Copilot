import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { RadialBarChart, RadialBar, ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";
import { TrendingUp, FileText, MessageSquare, Brain, Calendar, ArrowRight, Target, Star } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { progressApi } from "@/services/api";
import { useAuthStore } from "@/stores/authStore";

const quickActions = [
  { label: "Analyze Resume",     icon: FileText,        to: "/resume",    color: "bg-blue-500",   desc: "Upload & get ATS score" },
  { label: "Find Skill Gaps",    icon: TrendingUp,      to: "/skills",    color: "bg-green-500",  desc: "See what to learn next" },
  { label: "Mock Interview",     icon: MessageSquare,   to: "/interview", color: "bg-purple-500", desc: "Practice questions" },
  { label: "Take a Quiz",        icon: Brain,           to: "/quiz",      color: "bg-orange-500", desc: "Test your knowledge" },
  { label: "Study Plan",         icon: Calendar,        to: "/planner",   color: "bg-pink-500",   desc: "Get a daily schedule" },
];

function ScoreGauge({ score }: { score: number }) {
  const color = score >= 75 ? "#22c55e" : score >= 60 ? "#f59e0b" : score >= 45 ? "#3b82f6" : "#8b5cf6";
  const data = [{ value: score, fill: color }, { value: 100 - score, fill: "#f1f5f9" }];
  return (
    <div className="relative flex items-center justify-center h-48">
      <ResponsiveContainer width="100%" height="100%">
        <RadialBarChart cx="50%" cy="50%" innerRadius="60%" outerRadius="80%" startAngle={180} endAngle={0} data={data}>
          <RadialBar dataKey="value" cornerRadius={6} />
        </RadialBarChart>
      </ResponsiveContainer>
      <div className="absolute inset-0 flex flex-col items-center justify-center mt-8">
        <span className="text-4xl font-bold">{score}</span>
        <span className="text-sm text-muted-foreground">/ 100</span>
      </div>
    </div>
  );
}

function gradeInfo(score: number) {
  if (score >= 90) return { label: "Excellent",       color: "success" as const };
  if (score >= 75) return { label: "Good",            color: "info" as const };
  if (score >= 60) return { label: "Developing",      color: "warning" as const };
  if (score >= 45) return { label: "Early Stage",     color: "secondary" as const };
  return             { label: "Getting Started",  color: "secondary" as const };
}

export default function DashboardPage() {
  const user = useAuthStore((s) => s.user);
  const navigate = useNavigate();

  const { data: scoreData, isLoading } = useQuery({
    queryKey: ["career-score"],
    queryFn: progressApi.score,
    refetchInterval: 30000,
  });

  const { data: historyData } = useQuery({
    queryKey: ["score-history"],
    queryFn: progressApi.history,
  });

  const score = scoreData?.overall_score ?? 0;
  const components = scoreData?.components ?? { resume_score: 0, skill_score: 0, interview_score: 0, quiz_score: 0 };
  const recommendations = scoreData?.recommendations ?? [];
  const grade = gradeInfo(score);

  const componentItems = [
    { label: "Resume",    value: components.resume_score,    color: "bg-blue-500" },
    { label: "Skills",    value: components.skill_score,     color: "bg-green-500" },
    { label: "Interview", value: components.interview_score, color: "bg-purple-500" },
    { label: "Quizzes",   value: components.quiz_score,      color: "bg-orange-500" },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Welcome back, {user?.name?.split(" ")[0]} 👋</h1>
        <p className="text-muted-foreground mt-1">
          {user?.target_role ? `Working towards: ${user.target_role}` : "Set your target role to get personalised guidance"}
        </p>
      </div>

      {/* Score + History row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Career Readiness Score */}
        <Card className="lg:col-span-1">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center justify-between text-lg">
              Career Readiness
              {isLoading ? <Skeleton className="h-5 w-20" /> : <Badge variant={grade.color}>{grade.label}</Badge>}
            </CardTitle>
            <CardDescription>Overall career preparation score</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? <Skeleton className="h-48 w-full" /> : <ScoreGauge score={score} />}
            <div className="space-y-3 mt-4">
              {componentItems.map(({ label, value, color }) => (
                <div key={label} className="space-y-1">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">{label}</span>
                    <span className="font-medium">{value}/100</span>
                  </div>
                  <div className="h-2 bg-secondary rounded-full overflow-hidden">
                    <div className={`h-full ${color} rounded-full transition-all`} style={{ width: `${value}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Score Trend */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-lg">Score Trend</CardTitle>
            <CardDescription>Your career readiness over time</CardDescription>
          </CardHeader>
          <CardContent>
            {!historyData || historyData.length < 2 ? (
              <div className="h-48 flex items-center justify-center text-muted-foreground text-sm">
                <div className="text-center space-y-2">
                  <Target className="w-8 h-8 mx-auto opacity-40" />
                  <p>Complete assessments to see your progress trend</p>
                </div>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={180}>
                <LineChart data={historyData}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                  <XAxis dataKey="computed_at" tickFormatter={(v) => new Date(v).toLocaleDateString("en", { month: "short", day: "numeric" })} tick={{ fontSize: 11 }} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                  <Tooltip formatter={(v: number) => [`${v}/100`, "Score"]} />
                  <Line type="monotone" dataKey="overall_score" stroke="#8b5cf6" strokeWidth={2} dot={{ r: 3 }} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-lg font-semibold mb-3">Quick Actions</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
          {quickActions.map(({ label, icon: Icon, to, color, desc }) => (
            <Card
              key={to}
              className="cursor-pointer hover:shadow-md transition-all hover:-translate-y-0.5 group"
              onClick={() => navigate(to)}
            >
              <CardContent className="p-4 text-center space-y-2">
                <div className={`w-10 h-10 rounded-xl ${color} flex items-center justify-center mx-auto`}>
                  <Icon className="w-5 h-5 text-white" />
                </div>
                <p className="font-medium text-sm">{label}</p>
                <p className="text-xs text-muted-foreground">{desc}</p>
                <ArrowRight className="w-3 h-3 mx-auto opacity-0 group-hover:opacity-100 transition-opacity text-primary" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Recommendations */}
      {recommendations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Star className="w-5 h-5 text-yellow-500" /> Priority Actions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {recommendations.map((rec: string, i: number) => (
                <div key={i} className="flex items-start gap-3 p-3 rounded-lg bg-muted/50">
                  <span className="w-5 h-5 rounded-full bg-primary text-primary-foreground text-xs flex items-center justify-center flex-shrink-0 mt-0.5">{i + 1}</span>
                  <span className="text-sm">{rec}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
