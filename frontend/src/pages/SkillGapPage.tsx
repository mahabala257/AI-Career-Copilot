import { useState } from "react";
import { usePersistentState } from "@/hooks/usePersistentState";
import { useMutation } from "@tanstack/react-query";
import { Search, Loader2, AlertCircle, Target, Clock, BookOpen, ArrowRight } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { skillsApi } from "@/services/api";
import { useAuthStore } from "@/stores/authStore";
import type { SkillGapResponse } from "@/types";

const priorityColors: Record<string, "destructive" | "warning" | "info" | "secondary"> = {
  critical: "destructive", high: "warning", medium: "info", low: "secondary",
};

export default function SkillGapPage() {
  const user = useAuthStore((s) => s.user);
  const [targetRole, setTargetRole] = useState(user?.target_role || "");
  const [skillInput, setSkillInput] = useState("");
  const [skills, setSkills] = useState<string[]>(user?.current_skills || []);
  const [result, setResult] = usePersistentState<SkillGapResponse | null>("skillgap-result", null);

  const mutation = useMutation({
    mutationFn: () => skillsApi.analyze({ target_role: targetRole, current_skills: skills }),
    onSuccess: (data) => setResult(data),
  });

  const addSkill = () => {
    const s = skillInput.trim();
    if (s && !skills.includes(s)) { setSkills([...skills, s]); setSkillInput(""); }
  };

  const removeSkill = (s: string) => setSkills(skills.filter((x) => x !== s));

  const analysis = result?.analysis;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Skill Gap Analysis</h1>
        <p className="text-muted-foreground mt-1">Compare your skills against what the market requires for your target role</p>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Input */}
        <Card>
          <CardHeader><CardTitle className="text-lg">Your Profile</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Target Role *</Label>
              <Input placeholder="e.g. AI Engineer" value={targetRole} onChange={(e) => setTargetRole(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label>Your Current Skills</Label>
              <div className="flex gap-2">
                <Input placeholder="Add a skill..." value={skillInput} onChange={(e) => setSkillInput(e.target.value)} onKeyDown={(e) => e.key === "Enter" && addSkill()} />
                <Button size="sm" variant="outline" onClick={addSkill}>Add</Button>
              </div>
              <div className="flex flex-wrap gap-1 min-h-[40px]">
                {skills.map((s) => (
                  <Badge key={s} variant="secondary" className="cursor-pointer" onClick={() => removeSkill(s)}>
                    {s} ×
                  </Badge>
                ))}
                {skills.length === 0 && <p className="text-xs text-muted-foreground">Add skills above (or they'll be read from your resume analysis)</p>}
              </div>
            </div>
            <Button className="w-full" onClick={() => mutation.mutate()} disabled={!targetRole.trim() || mutation.isPending}>
              {mutation.isPending ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Analyzing...</> : <><Search className="w-4 h-4 mr-2" />Analyze Gaps</>}
            </Button>
            {mutation.isError && (
              <div className="flex items-center gap-2 p-3 rounded bg-destructive/10 text-destructive text-sm">
                <AlertCircle className="w-4 h-4" />{(mutation.error as any)?.response?.data?.detail || "Analysis failed."}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Results */}
        <div className="lg:col-span-2">
          {!analysis && !mutation.isPending && (
            <Card className="h-full min-h-[300px] flex items-center justify-center">
              <CardContent className="text-center space-y-3">
                <Target className="w-12 h-12 mx-auto text-muted-foreground/30" />
                <p className="text-muted-foreground">Enter your target role and click Analyze Gaps</p>
              </CardContent>
            </Card>
          )}

          {mutation.isPending && (
            <Card className="h-full min-h-[300px] flex items-center justify-center">
              <CardContent className="text-center space-y-3">
                <Loader2 className="w-10 h-10 animate-spin mx-auto text-primary" />
                <p className="text-muted-foreground">Analysing your skill gaps...</p>
              </CardContent>
            </Card>
          )}

          {analysis && (
            <div className="space-y-4">
              {/* Readiness */}
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold">Job Readiness for {analysis.target_role}</span>
                    <span className="text-2xl font-bold text-primary">{analysis.overall_readiness_percent}%</span>
                  </div>
                  <Progress value={analysis.overall_readiness_percent} className="h-3" />
                  <p className="text-xs text-muted-foreground mt-2">
                    Estimated {analysis.months_to_job_ready} months to job-ready with consistent effort
                  </p>
                </CardContent>
              </Card>

              <Tabs defaultValue="missing">
                <TabsList className="w-full">
                  <TabsTrigger value="missing" className="flex-1">Missing ({analysis.missing_skills?.length})</TabsTrigger>
                  <TabsTrigger value="matched" className="flex-1">Matched ({analysis.matched_skills?.length})</TabsTrigger>
                  <TabsTrigger value="actions" className="flex-1">Actions</TabsTrigger>
                </TabsList>

                <TabsContent value="missing" className="space-y-3 mt-4">
                  {analysis.missing_skills?.map((skill) => (
                    <Card key={skill.skill}>
                      <CardContent className="pt-4 pb-4">
                        <div className="flex items-start justify-between mb-2">
                          <div>
                            <span className="font-medium">{skill.skill}</span>
                            <Badge variant={priorityColors[skill.priority] || "secondary"} className="ml-2 text-xs">{skill.priority}</Badge>
                          </div>
                          <div className="flex items-center gap-1 text-xs text-muted-foreground">
                            <Clock className="w-3 h-3" />{skill.time_to_learn}
                          </div>
                        </div>
                        <p className="text-xs text-muted-foreground mb-2">{skill.why_important}</p>
                        {skill.learning_resources?.length > 0 && (
                          <div className="flex items-center gap-1">
                            <BookOpen className="w-3 h-3 text-muted-foreground" />
                            <span className="text-xs text-muted-foreground">{skill.learning_resources.slice(0, 2).join(", ")}</span>
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  ))}
                </TabsContent>

                <TabsContent value="matched" className="space-y-2 mt-4">
                  <div className="flex flex-wrap gap-2">
                    {analysis.skill_categories?.strong?.map((s) => <Badge key={s} variant="success">{s}</Badge>)}
                    {analysis.skill_categories?.developing?.map((s) => <Badge key={s} variant="info">{s}</Badge>)}
                  </div>
                  {analysis.matched_skills?.map((m) => (
                    <Card key={m.skill}>
                      <CardContent className="pt-3 pb-3 flex items-center justify-between">
                        <span className="text-sm font-medium">{m.skill}</span>
                        <div className="flex items-center gap-2 text-xs">
                          <span className="text-muted-foreground">You: {m.candidate_level}</span>
                          <ArrowRight className="w-3 h-3" />
                          <span className="text-primary">Need: {m.required_level}</span>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </TabsContent>

                <TabsContent value="actions" className="space-y-3 mt-4">
                  {analysis.immediate_actions?.map((a, i) => (
                    <div key={i} className="flex items-start gap-3 p-3 rounded-lg bg-muted/50">
                      <span className="w-6 h-6 rounded-full bg-primary text-primary-foreground text-xs flex items-center justify-center flex-shrink-0">{i + 1}</span>
                      <span className="text-sm">{a}</span>
                    </div>
                  ))}
                  <div className="pt-2">
                    <p className="text-sm font-medium mb-2">Priority Learning Order:</p>
                    <div className="flex flex-wrap gap-2">
                      {analysis.priority_order?.map((s, i) => (
                        <div key={s} className="flex items-center gap-1">
                          <span className="text-xs text-muted-foreground">{i + 1}.</span>
                          <Badge variant="outline">{s}</Badge>
                        </div>
                      ))}
                    </div>
                  </div>
                </TabsContent>
              </Tabs>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
