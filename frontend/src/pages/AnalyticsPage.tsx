import { useQuery } from "@tanstack/react-query";
import {
  ResponsiveContainer, LineChart, Line, BarChart, Bar, XAxis, YAxis,
  Tooltip, CartesianGrid, Legend, Cell,
} from "recharts";
import { TrendingUp, FileText, BarChart3, Activity } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { progressApi, resumeApi } from "@/services/api";

interface ScorePoint { overall_score: number; resume_score: number; skill_score: number; quiz_score: number; computed_at: string }

function fmtDate(v: string) {
  return new Date(v).toLocaleDateString("en", { month: "short", day: "numeric" });
}

export default function AnalyticsPage() {
  const { data: history } = useQuery<ScorePoint[]>({ queryKey: ["score-history"], queryFn: progressApi.history });
  const { data: score } = useQuery({ queryKey: ["career-score"], queryFn: progressApi.score });
  const { data: resumeHist } = useQuery({ queryKey: ["resume-history"], queryFn: resumeApi.history });

  const trend = (history ?? []).map((h) => ({ ...h, date: fmtDate(h.computed_at) }));
  const components = score?.components ?? { resume_score: 0, skill_score: 0, interview_score: 0, quiz_score: 0 };
  const barData = [
    { name: "Resume", value: components.resume_score, fill: "#3b82f6" },
    { name: "Skills", value: components.skill_score, fill: "#22c55e" },
    { name: "Interview", value: components.interview_score, fill: "#a855f7" },
    { name: "Quizzes", value: components.quiz_score, fill: "#f97316" },
  ];
  const resumeItems = (resumeHist?.items ?? []) as { ats_score: number | null; created_at: string; filename: string }[];
  const atsTrend = [...resumeItems]
    .filter((r) => r.ats_score != null)
    .reverse()
    .map((r) => ({ date: fmtDate(r.created_at), ats: r.ats_score }));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-2"><BarChart3 className="w-8 h-8 text-primary" /> Analytics</h1>
        <p className="text-muted-foreground mt-1">Track your career readiness and progress over time</p>
      </div>

      {/* Career readiness trend */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2"><TrendingUp className="w-5 h-5 text-primary" /> Career Readiness Over Time</CardTitle>
          <CardDescription>Overall score and each component as you progress</CardDescription>
        </CardHeader>
        <CardContent>
          {trend.length < 2 ? (
            <div className="h-64 flex items-center justify-center text-sm text-muted-foreground text-center">
              <div className="space-y-2">
                <Activity className="w-8 h-8 mx-auto opacity-30" />
                <p>Use a few features (resume, skills, quiz, interview) to build your trend.</p>
              </div>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={trend}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="overall_score" name="Overall" stroke="#8b5cf6" strokeWidth={2.5} dot={{ r: 3 }} />
                <Line type="monotone" dataKey="resume_score" name="Resume" stroke="#3b82f6" strokeWidth={1.5} dot={false} />
                <Line type="monotone" dataKey="skill_score" name="Skills" stroke="#22c55e" strokeWidth={1.5} dot={false} />
                <Line type="monotone" dataKey="quiz_score" name="Quizzes" stroke="#f97316" strokeWidth={1.5} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Current component breakdown */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Current Score Breakdown</CardTitle>
            <CardDescription>Where you stand right now</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={barData}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                  {barData.map((d, i) => <Cell key={i} fill={d.fill} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Resume ATS over time */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2"><FileText className="w-5 h-5 text-blue-500" /> Resume ATS History</CardTitle>
            <CardDescription>Your ATS score across uploads</CardDescription>
          </CardHeader>
          <CardContent>
            {atsTrend.length === 0 ? (
              <div className="h-64 flex items-center justify-center text-sm text-muted-foreground text-center">
                <div className="space-y-2">
                  <FileText className="w-8 h-8 mx-auto opacity-30" />
                  <p>Analyze a resume to see your ATS history.</p>
                </div>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={atsTrend}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                  <Tooltip formatter={(v: number) => [`${v}/100`, "ATS"]} />
                  <Line type="monotone" dataKey="ats" stroke="#3b82f6" strokeWidth={2} dot={{ r: 3 }} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
