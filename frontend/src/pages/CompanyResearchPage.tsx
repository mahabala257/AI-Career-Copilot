import { useState } from "react";
import { usePersistentState } from "@/hooks/usePersistentState";
import { useMutation } from "@tanstack/react-query";
import {
  Building2, Loader2, AlertCircle, Star, DollarSign,
  ThumbsUp, ThumbsDown, Calendar, ChevronDown, ChevronUp
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { companyApi } from "@/services/api";
import { useAuthStore } from "@/stores/authStore";
import type { CompanyResearchResponse } from "@/types";

export default function CompanyResearchPage() {
  const user = useAuthStore((s) => s.user);
  const [companyName, setCompanyName] = useState("");
  const [targetRole, setTargetRole] = useState(user?.target_role || "");
  const [workMode, setWorkMode] = useState("Any");
  const [employmentType, setEmploymentType] = useState("Any");
  const [result, setResult] = usePersistentState<CompanyResearchResponse | null>("company-result", null);

  const mutation = useMutation({
    mutationFn: () => companyApi.research({
      company_name: companyName, target_role: targetRole,
      work_mode: workMode, employment_type: employmentType,
    }),
    onSuccess: (data) => setResult(data),
  });

  const r = result?.result;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <Building2 className="w-8 h-8 text-indigo-600" /> Company Research
        </h1>
        <p className="text-muted-foreground mt-1">
          Get a complete preparation guide for your target company — tech stack, interview rounds, and a week-by-week study plan
        </p>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-lg">Research a Company</CardTitle>
            <CardDescription>Tell us where you're interviewing</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Company Name *</Label>
              <Input
                placeholder="e.g. Google, Microsoft, Zoho"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label>Target Role</Label>
              <Input
                placeholder="e.g. SDE-1, AI Engineer"
                value={targetRole}
                onChange={(e) => setTargetRole(e.target.value)}
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label>Work Mode</Label>
                <Select value={workMode} onValueChange={setWorkMode}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Any">Any</SelectItem>
                    <SelectItem value="Remote">Remote</SelectItem>
                    <SelectItem value="Hybrid">Hybrid</SelectItem>
                    <SelectItem value="Onsite">Onsite</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Employment Type</Label>
                <Select value={employmentType} onValueChange={setEmploymentType}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Any">Any</SelectItem>
                    <SelectItem value="Full-time">Full-time</SelectItem>
                    <SelectItem value="Internship">Internship</SelectItem>
                    <SelectItem value="Contract">Contract</SelectItem>
                    <SelectItem value="Part-time">Part-time</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <Button
              className="w-full"
              onClick={() => mutation.mutate()}
              disabled={!companyName.trim() || mutation.isPending}
            >
              {mutation.isPending
                ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Researching...</>
                : <><Building2 className="w-4 h-4 mr-2" />Research Company</>
              }
            </Button>
            {mutation.isError && (
              <div className="flex items-center gap-2 p-3 rounded bg-destructive/10 text-destructive text-sm">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                {(mutation.error as any)?.response?.data?.detail || "Research failed. Please try again."}
              </div>
            )}
          </CardContent>
        </Card>

        <div className="lg:col-span-2 space-y-4">
          {!r ? (
            <Card className="h-48 flex items-center justify-center">
              <div className="text-center text-muted-foreground space-y-2">
                <Building2 className="w-10 h-10 mx-auto opacity-20" />
                <p>Enter a company name to get your prep guide</p>
              </div>
            </Card>
          ) : (r.error_reason || !r.skill_alignment) ? (
            <Card className="h-48 flex items-center justify-center border-amber-200 bg-amber-50">
              <div className="text-center text-amber-700 space-y-3 px-6">
                <AlertCircle className="w-10 h-10 mx-auto opacity-50" />
                <p className="text-sm">
                  Couldn&apos;t complete the company research{r.error_reason ? ` (${r.error_reason})` : ""}. Please try again in a moment.
                </p>
                <Button variant="outline" size="sm" onClick={() => mutation.mutate()} disabled={mutation.isPending}>Retry</Button>
              </div>
            </Card>
          ) : (
            <>
              <Card>
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-xl">{r.company_name}</CardTitle>
                    <div className="flex items-center gap-2">
                      {r.glassdoor_rating && (
                        <Badge variant="outline" className="flex items-center gap-1">
                          <Star className="w-3 h-3 fill-yellow-400 text-yellow-400" /> {r.glassdoor_rating}
                        </Badge>
                      )}
                      <Badge variant="secondary" className="capitalize">{r.company_type}</Badge>
                    </div>
                  </div>
                  <CardDescription>{r.overview}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {(r.tech_stack?.length ?? 0) > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {r.tech_stack.map((t) => <Badge key={t} variant="secondary">{t}</Badge>)}
                    </div>
                  )}
                  <div className="grid sm:grid-cols-2 gap-3 pt-2">
                    {r.salary_range && (
                      <div className="flex items-center gap-2 text-sm">
                        <DollarSign className="w-4 h-4 text-green-500" /> {r.salary_range}
                      </div>
                    )}
                    {r.typical_timeline && (
                      <div className="flex items-center gap-2 text-sm">
                        <Calendar className="w-4 h-4 text-blue-500" /> {r.typical_timeline}
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Skill alignment */}
              <Card>
                <CardContent className="pt-4">
                  <div className="flex items-center gap-3 mb-3">
                    <span className="text-sm font-medium flex-1">Skill Alignment</span>
                    <span className="font-bold text-lg">{r.skill_alignment.alignment_score}%</span>
                  </div>
                  <Progress value={r.skill_alignment.alignment_score} className="h-2 mb-3" />
                  <div className="grid sm:grid-cols-2 gap-3">
                    {(r.skill_alignment.matching_skills?.length ?? 0) > 0 && (
                      <div>
                        <p className="text-xs font-semibold text-green-600 mb-1">✓ You Have</p>
                        <div className="flex flex-wrap gap-1">
                          {r.skill_alignment.matching_skills.map((s) => (
                            <Badge key={s} variant="outline" className="text-xs border-green-400 text-green-700">{s}</Badge>
                          ))}
                        </div>
                      </div>
                    )}
                    {(r.skill_alignment.missing_skills?.length ?? 0) > 0 && (
                      <div>
                        <p className="text-xs font-semibold text-orange-600 mb-1">⚠ Need to Learn</p>
                        <div className="flex flex-wrap gap-1">
                          {r.skill_alignment.missing_skills.map((s) => (
                            <Badge key={s} variant="outline" className="text-xs border-orange-400 text-orange-700">{s}</Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              <Tabs defaultValue="interview">
                <TabsList className="w-full">
                  <TabsTrigger value="interview" className="flex-1">Interview</TabsTrigger>
                  <TabsTrigger value="questions" className="flex-1">Questions</TabsTrigger>
                  <TabsTrigger value="prep" className="flex-1">Prep Plan</TabsTrigger>
                  <TabsTrigger value="culture" className="flex-1">Culture</TabsTrigger>
                </TabsList>

                <TabsContent value="interview">
                  <Card>
                    <CardContent className="pt-4 space-y-3">
                      <p className="text-sm text-muted-foreground">{r.interview_style}</p>
                      {(r.interview_rounds || []).map((round, i) => (
                        <div key={i} className="p-3 rounded border space-y-1">
                          <div className="flex items-center justify-between">
                            <span className="font-medium text-sm">{round.round}</span>
                            <Badge variant="secondary" className="text-xs">{round.focus}</Badge>
                          </div>
                          {round.tips && <p className="text-xs text-muted-foreground">{round.tips}</p>}
                        </div>
                      ))}
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="questions">
                  <Card>
                    <CardContent className="pt-4 space-y-3">
                      {(r.known_question_types || []).map((q, i) => (
                        <div key={i} className="p-3 rounded bg-muted/50 space-y-1">
                          <Badge variant="outline" className="text-xs capitalize">{q.type.replace(/_/g, " ")}</Badge>
                          <p className="text-sm">{q.example}</p>
                        </div>
                      ))}
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="prep">
                  <Card>
                    <CardContent className="pt-4 space-y-3">
                      {(r.prep_strategy || []).map((week, i) => (
                        <div key={i} className="flex gap-3 p-3 rounded border">
                          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 text-primary font-bold flex items-center justify-center text-sm">
                            W{week.week}
                          </div>
                          <div className="flex-1 space-y-1">
                            <div className="flex items-center justify-between">
                              <span className="font-medium text-sm">{week.focus}</span>
                              <span className="text-xs text-muted-foreground">{week.daily_hours}h/day</span>
                            </div>
                            {week.resources.length > 0 && (
                              <div className="flex flex-wrap gap-1">
                                {week.resources.map((res) => (
                                  <Badge key={res} variant="secondary" className="text-xs">{res}</Badge>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                      {r.application_tips.length > 0 && (
                        <div className="pt-2 border-t space-y-1">
                          <p className="text-sm font-semibold">Application Tips</p>
                          {r.application_tips.map((tip, i) => (
                            <p key={i} className="text-sm text-muted-foreground">• {tip}</p>
                          ))}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="culture">
                  <Card>
                    <CardContent className="pt-4 space-y-4">
                      <p className="text-sm">{r.engineering_culture}</p>
                      {r.culture_values.length > 0 && (
                        <div className="flex flex-wrap gap-1">
                          {r.culture_values.map((v) => <Badge key={v}>{v}</Badge>)}
                        </div>
                      )}
                      <div className="grid sm:grid-cols-2 gap-4 pt-2">
                        {r.pros.length > 0 && (
                          <div className="space-y-1">
                            <p className="text-sm font-semibold flex items-center gap-1 text-green-600">
                              <ThumbsUp className="w-3.5 h-3.5" /> Pros
                            </p>
                            {r.pros.map((p, i) => <p key={i} className="text-sm">• {p}</p>)}
                          </div>
                        )}
                        {r.cons.length > 0 && (
                          <div className="space-y-1">
                            <p className="text-sm font-semibold flex items-center gap-1 text-orange-600">
                              <ThumbsDown className="w-3.5 h-3.5" /> Cons
                            </p>
                            {r.cons.map((c, i) => <p key={i} className="text-sm">• {c}</p>)}
                          </div>
                        )}
                      </div>
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
