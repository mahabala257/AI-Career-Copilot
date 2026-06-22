import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import {
  FolderGit2, Loader2, AlertCircle, Star, Clock,
  Code2, ChevronDown, ChevronUp, Lightbulb, TrendingUp, Shield
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { projectsApi } from "@/services/api";
import { useAuthStore } from "@/stores/authStore";
import type { ProjectRecommendResponse, RecommendedProject } from "@/types";

const difficultyColor: Record<string, string> = {
  beginner:     "bg-green-100 text-green-700 border-green-200",
  intermediate: "bg-yellow-100 text-yellow-700 border-yellow-200",
  advanced:     "bg-red-100 text-red-700 border-red-200",
};

function ProjectCard({ project }: { project: RecommendedProject }) {
  const [expanded, setExpanded] = useState(false);
  const ts = project.tech_stack;
  const allTech = [...ts.backend, ...ts.frontend, ...ts.ai_ml, ...ts.database, ...ts.devops];

  return (
    <Card className="border-2 hover:border-primary/30 transition-colors">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-2 flex-1 min-w-0">
            <span className="flex-shrink-0 w-7 h-7 rounded-full bg-primary/10 text-primary text-sm font-bold flex items-center justify-center">
              {project.rank}
            </span>
            <CardTitle className="text-base leading-tight">{project.title}</CardTitle>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            <Badge
              variant="outline"
              className={`text-xs ${difficultyColor[project.difficulty] || difficultyColor.intermediate}`}
            >
              {project.difficulty}
            </Badge>
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <Clock className="w-3 h-3" />
              {project.estimated_weeks}w
            </div>
          </div>
        </div>
        <p className="text-sm text-muted-foreground leading-relaxed">{project.one_liner}</p>
      </CardHeader>

      <CardContent className="space-y-3">
        {/* Tech stack pills */}
        {allTech.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {allTech.slice(0, 8).map((t) => (
              <Badge key={t} variant="secondary" className="text-xs">{t}</Badge>
            ))}
            {allTech.length > 8 && (
              <Badge variant="secondary" className="text-xs">+{allTech.length - 8}</Badge>
            )}
          </div>
        )}

        {/* Why this impresses */}
        <div className="flex items-start gap-2 p-2.5 rounded bg-blue-50 dark:bg-blue-950/30 text-sm">
          <Star className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
          <span className="text-blue-800 dark:text-blue-200">{project.why_this_impresses}</span>
        </div>

        {/* Expand / collapse */}
        <Button
          variant="ghost" size="sm"
          className="w-full text-xs"
          onClick={() => setExpanded(!expanded)}
        >
          {expanded ? <><ChevronUp className="w-3 h-3 mr-1" />Less detail</> : <><ChevronDown className="w-3 h-3 mr-1" />More detail</>}
        </Button>

        {expanded && (
          <div className="space-y-3 pt-1 border-t">
            {project.description && (
              <div>
                <p className="text-xs font-semibold text-muted-foreground uppercase mb-1">What to Build</p>
                <p className="text-sm">{project.description}</p>
              </div>
            )}

            <div className="grid sm:grid-cols-2 gap-3">
              {project.skills_demonstrated.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-muted-foreground uppercase mb-1">Skills Demonstrated</p>
                  <div className="flex flex-wrap gap-1">
                    {project.skills_demonstrated.map((s) => (
                      <Badge key={s} variant="outline" className="text-xs border-green-400 text-green-700">{s}</Badge>
                    ))}
                  </div>
                </div>
              )}
              {project.skills_learned.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-muted-foreground uppercase mb-1">Skills You'll Learn</p>
                  <div className="flex flex-wrap gap-1">
                    {project.skills_learned.map((s) => (
                      <Badge key={s} variant="outline" className="text-xs border-purple-400 text-purple-700">{s}</Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {project.interview_talking_points.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-muted-foreground uppercase mb-1">Interview Talking Points</p>
                <ul className="space-y-1">
                  {project.interview_talking_points.map((p, i) => (
                    <li key={i} className="text-sm flex items-start gap-1.5">
                      <span className="text-primary">•</span> {p}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {project.scale_question && (
              <div className="p-2.5 rounded bg-muted/50 text-sm">
                <span className="font-semibold">System Design prep: </span>
                {project.scale_question}
              </div>
            )}

            {project.demo_tip && (
              <div className="flex items-start gap-2 p-2.5 rounded bg-yellow-50 dark:bg-yellow-950/30 text-sm">
                <Lightbulb className="w-4 h-4 text-yellow-500 mt-0.5 flex-shrink-0" />
                <span>{project.demo_tip}</span>
              </div>
            )}

            {project.github_readme_sections.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-muted-foreground uppercase mb-1">README Sections to Include</p>
                <div className="flex flex-wrap gap-1">
                  {project.github_readme_sections.map((s) => (
                    <Badge key={s} variant="secondary" className="text-xs">{s}</Badge>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default function ProjectRecommenderPage() {
  const user = useAuthStore((s) => s.user);
  const [targetRole, setTargetRole] = useState(user?.target_role || "");
  const [experienceLevel, setExperienceLevel] = useState("fresher");
  const [weeks, setWeeks] = useState("4");
  const [result, setResult] = useState<ProjectRecommendResponse | null>(null);

  const mutation = useMutation({
    mutationFn: () =>
      projectsApi.recommend({
        target_role: targetRole,
        experience_level: experienceLevel,
        time_available_weeks: parseInt(weeks) || 4,
      }),
    onSuccess: (data) => setResult(data),
  });

  const r = result?.result;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <FolderGit2 className="w-8 h-8 text-purple-600" /> Project Recommender
        </h1>
        <p className="text-muted-foreground mt-1">
          Get 3 specific, buildable portfolio projects that will impress hiring managers for your target role
        </p>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Input */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-lg">Your Details</CardTitle>
            <CardDescription>We'll tailor projects to close your skill gaps</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Target Role *</Label>
              <Input
                placeholder="e.g. AI Engineer"
                value={targetRole}
                onChange={(e) => setTargetRole(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label>Experience Level</Label>
              <Select value={experienceLevel} onValueChange={setExperienceLevel}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="fresher">Fresher / 0 years</SelectItem>
                  <SelectItem value="1-2 years">1–2 years</SelectItem>
                  <SelectItem value="2-3 years">2–3 years</SelectItem>
                  <SelectItem value="3-5 years">3–5 years</SelectItem>
                  <SelectItem value="5+ years">5+ years</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Time Available (weeks)</Label>
              <Input
                type="number"
                min={1}
                max={52}
                value={weeks}
                onChange={(e) => setWeeks(e.target.value)}
                placeholder="4"
              />
              <p className="text-xs text-muted-foreground">
                Total time budget across all 3 projects
              </p>
            </div>

            <div className="p-3 rounded bg-muted/50 text-xs text-muted-foreground space-y-1">
              <p className="font-semibold">💡 Tip</p>
              <p>Run Resume Analyzer and Skill Gap Analysis first — the agent reads those results to avoid recommending skills you already have.</p>
            </div>

            <Button
              className="w-full"
              onClick={() => mutation.mutate()}
              disabled={!targetRole.trim() || mutation.isPending}
            >
              {mutation.isPending
                ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Generating...</>
                : <><Code2 className="w-4 h-4 mr-2" />Get Project Ideas</>
              }
            </Button>
            {mutation.isError && (
              <div className="flex items-center gap-2 p-3 rounded bg-destructive/10 text-destructive text-sm">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                {(mutation.error as any)?.response?.data?.detail || "Failed. Please try again."}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Results */}
        <div className="lg:col-span-2 space-y-4">
          {!r ? (
            <Card className="h-48 flex items-center justify-center">
              <div className="text-center text-muted-foreground space-y-2">
                <FolderGit2 className="w-10 h-10 mx-auto opacity-20" />
                <p>Fill in your details and click Get Project Ideas</p>
              </div>
            </Card>
          ) : (
            <>
              {/* Portfolio score */}
              <Card>
                <CardContent className="pt-4">
                  <div className="flex items-center gap-4">
                    <div className="flex-1 space-y-1">
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Current Portfolio Score</span>
                        <span className="font-bold">{r.portfolio_score}/100</span>
                      </div>
                      <Progress value={r.portfolio_score} className="h-2" />
                    </div>
                    <div className="flex-1 space-y-1">
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Target after projects</span>
                        <span className="font-bold text-green-600">{r.portfolio_target_score}/100</span>
                      </div>
                      <Progress value={r.portfolio_target_score} className="h-2 [&>div]:bg-green-500" />
                    </div>
                  </div>
                  {r.portfolio_assessment && (
                    <p className="text-sm text-muted-foreground mt-3">{r.portfolio_assessment}</p>
                  )}
                  {r.portfolio_action_plan.length > 0 && (
                    <div className="mt-3 space-y-1">
                      {r.portfolio_action_plan.map((a, i) => (
                        <div key={i} className="flex items-center gap-2 text-sm">
                          <TrendingUp className="w-3.5 h-3.5 text-primary flex-shrink-0" />
                          {a}
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Project cards */}
              {r.recommended_projects.map((p) => (
                <ProjectCard key={p.rank} project={p} />
              ))}

              {/* Projects to avoid */}
              {r.projects_to_avoid.length > 0 && (
                <Card className="border-orange-200 dark:border-orange-800">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-base flex items-center gap-2">
                      <Shield className="w-4 h-4 text-orange-500" /> Projects to Avoid
                    </CardTitle>
                    <CardDescription>These are overused and won't differentiate you</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {r.projects_to_avoid.map((p, i) => (
                      <div key={i} className="flex items-start gap-2 text-sm">
                        <span className="text-orange-500 font-bold flex-shrink-0">✗</span>
                        <div>
                          <span className="font-medium line-through text-muted-foreground">{p.project}</span>
                          {p.reason && <span className="ml-2 text-muted-foreground">— {p.reason}</span>}
                        </div>
                      </div>
                    ))}
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
