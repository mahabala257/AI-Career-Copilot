import { useState } from "react";
import { usePersistentState } from "@/hooks/usePersistentState";
import { useMutation } from "@tanstack/react-query";
import {
  Linkedin, Loader2, AlertCircle, CheckCircle2, TrendingUp,
  Sparkles, ChevronDown, ChevronUp, Copy, Check
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { linkedinApi } from "@/services/api";
import { useAuthStore } from "@/stores/authStore";
import type { LinkedInOptimizeResponse } from "@/types";

function ScoreBar({ label, current, optimized }: { label: string; current: number; optimized: number }) {
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-sm">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-medium">{current} → <span className="text-green-600">{optimized}</span></span>
      </div>
      <div className="relative h-2 rounded-full bg-muted overflow-hidden">
        <div className="absolute h-full rounded-full bg-muted-foreground/40" style={{ width: `${current}%` }} />
        <div className="absolute h-full rounded-full bg-green-500 opacity-60" style={{ width: `${optimized}%` }} />
      </div>
    </div>
  );
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <Button variant="ghost" size="icon" className="h-7 w-7 flex-shrink-0" onClick={copy}>
      {copied ? <Check className="w-3.5 h-3.5 text-green-500" /> : <Copy className="w-3.5 h-3.5" />}
    </Button>
  );
}

function Section({ title, children, defaultOpen = false }: { title: string; children: React.ReactNode; defaultOpen?: boolean }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border rounded-lg overflow-hidden">
      <button
        className="flex items-center justify-between w-full px-4 py-3 text-left font-medium text-sm hover:bg-accent transition-colors"
        onClick={() => setOpen(!open)}
      >
        {title}
        {open ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
      </button>
      {open && <div className="px-4 pb-4 pt-1">{children}</div>}
    </div>
  );
}

export default function LinkedInOptimizerPage() {
  const user = useAuthStore((s) => s.user);
  const [targetRole, setTargetRole] = useState(user?.target_role || "");
  const [headline, setHeadline] = useState("");
  const [about, setAbout] = useState("");
  const [experience, setExperience] = useState("");
  const [skillInput, setSkillInput] = useState("");
  const [skills, setSkills] = useState<string[]>([]);
  const [result, setResult] = usePersistentState<LinkedInOptimizeResponse | null>("linkedin-result", null);

  const mutation = useMutation({
    mutationFn: () =>
      linkedinApi.optimize({ headline, about, experience, skills, target_role: targetRole }),
    onSuccess: (data) => setResult(data),
  });

  const addSkill = () => {
    const s = skillInput.trim();
    if (s && !skills.includes(s)) { setSkills([...skills, s]); setSkillInput(""); }
  };

  const r = result?.result;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <Linkedin className="w-8 h-8 text-blue-600" /> LinkedIn Optimizer
        </h1>
        <p className="text-muted-foreground mt-1">
          Rewrite your headline, About section, and experience bullets to attract recruiters for your target role
        </p>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Input Panel */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-lg">Your LinkedIn Profile</CardTitle>
            <CardDescription>Paste your current sections — leave blank what you don't have yet</CardDescription>
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
              <Label>Current Headline</Label>
              <Input
                placeholder="e.g. B.Tech CSE | Looking for opportunities"
                value={headline}
                onChange={(e) => setHeadline(e.target.value)}
                maxLength={220}
              />
              <p className="text-xs text-muted-foreground">{headline.length}/220</p>
            </div>
            <div className="space-y-2">
              <Label>About / Summary Section</Label>
              <Textarea
                placeholder="Paste your current About section..."
                value={about}
                onChange={(e) => setAbout(e.target.value)}
                rows={4}
                maxLength={2600}
              />
              <p className="text-xs text-muted-foreground">{about.length}/2600</p>
            </div>
            <div className="space-y-2">
              <Label>Experience Section</Label>
              <Textarea
                placeholder="Paste your experience bullets or job descriptions..."
                value={experience}
                onChange={(e) => setExperience(e.target.value)}
                rows={4}
                maxLength={5000}
              />
            </div>
            <div className="space-y-2">
              <Label>Current Skills (LinkedIn)</Label>
              <div className="flex gap-2">
                <Input
                  placeholder="Add skill..."
                  value={skillInput}
                  onChange={(e) => setSkillInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && addSkill()}
                />
                <Button size="sm" variant="outline" onClick={addSkill}>Add</Button>
              </div>
              <div className="flex flex-wrap gap-1 min-h-[32px]">
                {skills.map((s) => (
                  <Badge
                    key={s} variant="secondary"
                    className="cursor-pointer"
                    onClick={() => setSkills(skills.filter((x) => x !== s))}
                  >
                    {s} ×
                  </Badge>
                ))}
              </div>
            </div>

            <Button
              className="w-full"
              onClick={() => mutation.mutate()}
              disabled={!targetRole.trim() || (!headline && !about && !experience) || mutation.isPending}
            >
              {mutation.isPending
                ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Optimizing...</>
                : <><Sparkles className="w-4 h-4 mr-2" />Optimize Profile</>
              }
            </Button>
            {mutation.isError && (
              <div className="flex items-center gap-2 p-3 rounded bg-destructive/10 text-destructive text-sm">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                {(mutation.error as any)?.response?.data?.detail || "Optimization failed. Please try again."}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Results Panel */}
        <div className="lg:col-span-2 space-y-4">
          {!r ? (
            <Card className="h-48 flex items-center justify-center">
              <div className="text-center text-muted-foreground space-y-2">
                <Linkedin className="w-10 h-10 mx-auto opacity-20" />
                <p>Paste your LinkedIn sections and click Optimize</p>
              </div>
            </Card>
          ) : (r.error_reason || !r.sections || !r.score_breakdown || !r.keyword_density) ? (
            <Card className="h-48 flex items-center justify-center border-amber-200 bg-amber-50">
              <div className="text-center text-amber-700 space-y-3 px-6">
                <AlertCircle className="w-10 h-10 mx-auto opacity-50" />
                <p className="text-sm">
                  The optimizer couldn&apos;t produce a full result{r.error_reason ? ` (${r.error_reason})` : ""}. Please try again in a moment.
                </p>
                <Button variant="outline" size="sm" onClick={() => mutation.mutate()} disabled={mutation.isPending}>Retry</Button>
              </div>
            </Card>
          ) : (
            <>
              {/* Score Summary */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-lg flex items-center gap-2">
                    <TrendingUp className="w-5 h-5 text-green-500" /> Profile Score Improvement
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-center gap-8 py-2">
                    <div className="text-center">
                      <p className="text-4xl font-bold text-muted-foreground">{r.current_score}</p>
                      <p className="text-sm text-muted-foreground">Current</p>
                    </div>
                    <div className="text-2xl text-muted-foreground">→</div>
                    <div className="text-center">
                      <p className="text-4xl font-bold text-green-600">{r.optimized_score}</p>
                      <p className="text-sm text-muted-foreground">Optimized</p>
                    </div>
                    <div className="text-center">
                      <p className="text-4xl font-bold text-blue-600">
                        +{r.optimized_score - r.current_score}
                      </p>
                      <p className="text-sm text-muted-foreground">Gain</p>
                    </div>
                  </div>

                  {Object.keys(r.score_breakdown).length > 0 && (
                    <div className="space-y-2 pt-2">
                      {Object.entries(r.score_breakdown).map(([key, val]) => (
                        <div key={key} className="flex justify-between text-sm">
                          <span className="capitalize text-muted-foreground">{key.replace(/_/g, " ")}</span>
                          <span className="font-medium">{val}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {r.top_3_changes.length > 0 && (
                    <div className="pt-2 space-y-1">
                      <p className="text-sm font-semibold">Top 3 changes to make:</p>
                      {r.top_3_changes.map((c, i) => (
                        <div key={i} className="flex items-start gap-2 text-sm">
                          <CheckCircle2 className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                          <span>{c}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>

              <Tabs defaultValue="headline">
                <TabsList className="w-full">
                  <TabsTrigger value="headline" className="flex-1">Headline</TabsTrigger>
                  <TabsTrigger value="about" className="flex-1">About</TabsTrigger>
                  <TabsTrigger value="experience" className="flex-1">Experience</TabsTrigger>
                  <TabsTrigger value="skills" className="flex-1">Skills</TabsTrigger>
                  <TabsTrigger value="keywords" className="flex-1">Keywords</TabsTrigger>
                </TabsList>

                {/* Headline Tab */}
                <TabsContent value="headline">
                  <Card>
                    <CardContent className="pt-4 space-y-4">
                      {r.sections.headline.current && (
                        <div className="space-y-1">
                          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Current</p>
                          <p className="p-3 rounded bg-muted/50 text-sm line-through text-muted-foreground">
                            {r.sections.headline.current}
                          </p>
                        </div>
                      )}
                      <div className="space-y-1">
                        <div className="flex items-center justify-between">
                          <p className="text-xs font-semibold text-green-600 uppercase tracking-wide">Optimized ✓</p>
                          <CopyButton text={r.sections.headline.optimized} />
                        </div>
                        <p className="p-3 rounded bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-800 text-sm font-medium">
                          {r.sections.headline.optimized}
                        </p>
                      </div>
                      {r.sections.headline.reasoning && (
                        <p className="text-sm text-muted-foreground italic">{r.sections.headline.reasoning}</p>
                      )}
                    </CardContent>
                  </Card>
                </TabsContent>

                {/* About Tab */}
                <TabsContent value="about">
                  <Card>
                    <CardContent className="pt-4 space-y-4">
                      <div className="flex items-center gap-3">
                        <Badge variant="outline">Hook Score</Badge>
                        <Progress value={r.sections.about.hook_score} className="flex-1 h-2" />
                        <span className="text-sm font-medium">{r.sections.about.hook_score}/100</span>
                      </div>
                      <div className="space-y-1">
                        <div className="flex items-center justify-between">
                          <p className="text-xs font-semibold text-green-600 uppercase tracking-wide">Optimized About Section ✓</p>
                          <CopyButton text={r.sections.about.optimized} />
                        </div>
                        <div className="p-3 rounded bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-800 text-sm whitespace-pre-wrap">
                          {r.sections.about.optimized}
                        </div>
                      </div>
                      {r.sections.about.reasoning && (
                        <p className="text-sm text-muted-foreground italic">{r.sections.about.reasoning}</p>
                      )}
                    </CardContent>
                  </Card>
                </TabsContent>

                {/* Experience Tab */}
                <TabsContent value="experience">
                  <Card>
                    <CardContent className="pt-4 space-y-4">
                      {r.sections.experience_bullets.length === 0 ? (
                        <p className="text-sm text-muted-foreground">No experience bullets to rewrite — paste your experience section in the input.</p>
                      ) : (
                        r.sections.experience_bullets.map((b, i) => (
                          <div key={i} className="space-y-2 pb-4 border-b last:border-0">
                            {b.original && (
                              <div className="p-3 rounded bg-muted/50 text-sm text-muted-foreground line-through">
                                {b.original}
                              </div>
                            )}
                            <div className="flex items-start gap-2">
                              <div className="flex-1 p-3 rounded bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-800 text-sm">
                                {b.rewritten}
                              </div>
                              <CopyButton text={b.rewritten} />
                            </div>
                            {b.improvement && (
                              <p className="text-xs text-muted-foreground">{b.improvement}</p>
                            )}
                          </div>
                        ))
                      )}
                    </CardContent>
                  </Card>
                </TabsContent>

                {/* Skills Tab */}
                <TabsContent value="skills">
                  <Card>
                    <CardContent className="pt-4 space-y-4">
                      {r.sections.skills_reorder.recommended_top_3.length > 0 && (
                        <div className="space-y-2">
                          <p className="text-sm font-semibold">Pin These 3 Skills First</p>
                          <p className="text-xs text-muted-foreground">LinkedIn shows your top 3 skills without expanding. Make them count.</p>
                          <div className="flex gap-2 flex-wrap">
                            {r.sections.skills_reorder.recommended_top_3.map((s) => (
                              <Badge key={s} className="bg-blue-600">{s}</Badge>
                            ))}
                          </div>
                        </div>
                      )}
                      {r.sections.skills_reorder.skills_to_add.length > 0 && (
                        <div className="space-y-2">
                          <p className="text-sm font-semibold text-green-600">Add These Skills</p>
                          <div className="flex gap-2 flex-wrap">
                            {r.sections.skills_reorder.skills_to_add.map((s) => (
                              <Badge key={s} variant="outline" className="border-green-500 text-green-600">+ {s}</Badge>
                            ))}
                          </div>
                        </div>
                      )}
                      {r.sections.skills_reorder.skills_to_remove.length > 0 && (
                        <div className="space-y-2">
                          <p className="text-sm font-semibold text-destructive">Remove These (Low Signal)</p>
                          <div className="flex gap-2 flex-wrap">
                            {r.sections.skills_reorder.skills_to_remove.map((s) => (
                              <Badge key={s} variant="outline" className="border-destructive text-destructive line-through">
                                {s}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                      {r.sections.skills_reorder.reasoning && (
                        <p className="text-sm text-muted-foreground italic">{r.sections.skills_reorder.reasoning}</p>
                      )}
                    </CardContent>
                  </Card>
                </TabsContent>

                {/* Keywords Tab */}
                <TabsContent value="keywords">
                  <Card>
                    <CardContent className="pt-4 space-y-4">
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <p className="text-sm font-semibold">Keyword Score</p>
                          <span className="font-bold">{r.keyword_density.keyword_score}/100</span>
                        </div>
                        <Progress value={r.keyword_density.keyword_score} className="h-2" />
                      </div>
                      {r.keyword_density.present_keywords.length > 0 && (
                        <div className="space-y-2">
                          <p className="text-sm font-semibold text-green-600">✓ Keywords Present</p>
                          <div className="flex flex-wrap gap-1">
                            {r.keyword_density.present_keywords.map((k) => (
                              <Badge key={k} variant="secondary" className="text-green-700 bg-green-100">{k}</Badge>
                            ))}
                          </div>
                        </div>
                      )}
                      {r.keyword_density.missing_high_value_keywords.length > 0 && (
                        <div className="space-y-2">
                          <p className="text-sm font-semibold text-orange-600">⚠ High-Value Keywords Missing</p>
                          <div className="flex flex-wrap gap-1">
                            {r.keyword_density.missing_high_value_keywords.map((k) => (
                              <Badge key={k} variant="secondary" className="text-orange-700 bg-orange-100">{k}</Badge>
                            ))}
                          </div>
                          <p className="text-xs text-muted-foreground">Add these naturally to your About section and Skills list.</p>
                        </div>
                      )}
                      {r.creator_tips.length > 0 && (
                        <div className="space-y-1 pt-2 border-t">
                          <p className="text-sm font-semibold">Creator Tips</p>
                          {r.creator_tips.map((tip, i) => (
                            <p key={i} className="text-sm text-muted-foreground">• {tip}</p>
                          ))}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </TabsContent>
              </Tabs>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
