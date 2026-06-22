import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { GraduationCap, Loader2, AlertCircle, Calendar, Briefcase } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { internshipApi } from "@/services/api";
import { useAuthStore } from "@/stores/authStore";
import type { InternshipResearchResponse } from "@/types";

export default function InternshipResearchPage() {
  const user = useAuthStore((s) => s.user);
  const [targetRole, setTargetRole] = useState(user?.target_role || "Software Engineer Intern");
  const [educationLevel, setEducationLevel] = useState("B.Tech 3rd year");
  const [collegeTier, setCollegeTier] = useState("Tier 2");
  const [availableFrom, setAvailableFrom] = useState("");
  const [result, setResult] = useState<InternshipResearchResponse | null>(null);

  const mutation = useMutation({
    mutationFn: () =>
      internshipApi.research({
        target_role: targetRole,
        education_level: educationLevel,
        college_tier: collegeTier,
        available_from: availableFrom,
      }),
    onSuccess: (data) => setResult(data),
  });

  const r = result?.result;
  const timelineEntries = r ? Object.entries(r.application_timeline) : [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <GraduationCap className="w-8 h-8 text-teal-600" /> Internship Research
        </h1>
        <p className="text-muted-foreground mt-1">
          Find realistic internship opportunities matched to your college tier and timeline
        </p>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-lg">Your Profile</CardTitle>
            <CardDescription>We'll recommend companies that are realistic for you</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Target Role</Label>
              <Input value={targetRole} onChange={(e) => setTargetRole(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label>Education Level</Label>
              <Select value={educationLevel} onValueChange={setEducationLevel}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="B.Tech 1st year">B.Tech 1st year</SelectItem>
                  <SelectItem value="B.Tech 2nd year">B.Tech 2nd year</SelectItem>
                  <SelectItem value="B.Tech 3rd year">B.Tech 3rd year</SelectItem>
                  <SelectItem value="B.Tech final year">B.Tech final year</SelectItem>
                  <SelectItem value="MBA 1st year">MBA 1st year</SelectItem>
                  <SelectItem value="M.Tech">M.Tech</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>College Tier</Label>
              <Select value={collegeTier} onValueChange={setCollegeTier}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="IIT/NIT">IIT / NIT</SelectItem>
                  <SelectItem value="Tier 2">Tier 2</SelectItem>
                  <SelectItem value="Tier 3">Tier 3</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">
                Honest tier helps us recommend companies you have a real shot at
              </p>
            </div>
            <div className="space-y-2">
              <Label>Available From <span className="text-muted-foreground">(optional)</span></Label>
              <Input
                placeholder="e.g. May 2025"
                value={availableFrom}
                onChange={(e) => setAvailableFrom(e.target.value)}
              />
            </div>
            <Button
              className="w-full"
              onClick={() => mutation.mutate()}
              disabled={!targetRole.trim() || mutation.isPending}
            >
              {mutation.isPending
                ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Researching...</>
                : <><GraduationCap className="w-4 h-4 mr-2" />Find Internships</>
              }
            </Button>
            {mutation.isError && (
              <div className="flex items-center gap-2 p-3 rounded bg-destructive/10 text-destructive text-sm">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                Research failed. Please try again.
              </div>
            )}
          </CardContent>
        </Card>

        <div className="lg:col-span-2 space-y-4">
          {!r ? (
            <Card className="h-48 flex items-center justify-center">
              <div className="text-center text-muted-foreground space-y-2">
                <GraduationCap className="w-10 h-10 mx-auto opacity-20" />
                <p>Fill in your profile to get internship recommendations</p>
              </div>
            </Card>
          ) : (
            <>
              {r.student_profile_summary && (
                <Card>
                  <CardContent className="pt-4">
                    <p className="text-sm text-muted-foreground">{r.student_profile_summary}</p>
                  </CardContent>
                </Card>
              )}

              <Tabs defaultValue="companies">
                <TabsList className="w-full">
                  <TabsTrigger value="companies" className="flex-1">Companies</TabsTrigger>
                  <TabsTrigger value="timeline" className="flex-1">Timeline</TabsTrigger>
                  <TabsTrigger value="prep" className="flex-1">Prep</TabsTrigger>
                  <TabsTrigger value="tips" className="flex-1">Tips</TabsTrigger>
                </TabsList>

                <TabsContent value="companies" className="space-y-3">
                  {r.recommended_companies.map((c, i) => (
                    <Card key={i}>
                      <CardHeader className="pb-2">
                        <div className="flex items-center justify-between">
                          <CardTitle className="text-base flex items-center gap-2">
                            <Briefcase className="w-4 h-4 text-teal-600" /> {c.company}
                          </CardTitle>
                          <Badge variant={c.fit_score >= 70 ? "default" : "secondary"}>
                            {c.fit_score}% fit
                          </Badge>
                        </div>
                        {c.program_name && <CardDescription>{c.program_name}</CardDescription>}
                      </CardHeader>
                      <CardContent className="space-y-2 text-sm">
                        <div className="grid sm:grid-cols-2 gap-2">
                          <div><span className="text-muted-foreground">Stipend:</span> {c.stipend_range}</div>
                          <div><span className="text-muted-foreground">Window:</span> {c.application_window}</div>
                          <div><span className="text-muted-foreground">Duration:</span> {c.duration}</div>
                          <div><span className="text-muted-foreground">PPO:</span> {c.ppo_likelihood}</div>
                        </div>
                        {c.required_skills.length > 0 && (
                          <div className="flex flex-wrap gap-1 pt-1">
                            {c.required_skills.map((s) => (
                              <Badge key={s} variant="outline" className="text-xs">{s}</Badge>
                            ))}
                          </div>
                        )}
                        {c.selection_process.length > 0 && (
                          <p className="text-xs text-muted-foreground pt-1">
                            Process: {c.selection_process.join(" → ")}
                          </p>
                        )}
                      </CardContent>
                    </Card>
                  ))}
                </TabsContent>

                <TabsContent value="timeline">
                  <Card>
                    <CardContent className="pt-4 space-y-3">
                      {timelineEntries.map(([key, value]) => (
                        <div key={key} className="flex gap-3">
                          <Calendar className="w-4 h-4 text-teal-600 mt-0.5 flex-shrink-0" />
                          <div>
                            <p className="text-sm font-semibold capitalize">{key.replace(/_/g, " ")}</p>
                            <p className="text-sm text-muted-foreground">{value}</p>
                          </div>
                        </div>
                      ))}
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="prep">
                  <Card>
                    <CardContent className="pt-4 space-y-3">
                      {r.skill_gaps_for_internships.length > 0 && (
                        <div className="space-y-1">
                          <p className="text-sm font-semibold">Skill Gaps to Close</p>
                          <div className="flex flex-wrap gap-1">
                            {r.skill_gaps_for_internships.map((s) => (
                              <Badge key={s} variant="outline" className="border-orange-400 text-orange-700">{s}</Badge>
                            ))}
                          </div>
                        </div>
                      )}
                      {r.preparation_priorities.map((p, i) => (
                        <div key={i} className="p-3 rounded border space-y-1">
                          <div className="flex items-center gap-2">
                            <Badge>{p.priority}</Badge>
                            <span className="font-medium text-sm">{p.skill}</span>
                          </div>
                          <p className="text-xs text-muted-foreground">{p.why}</p>
                          {p.resource && <p className="text-xs text-primary">{p.resource}</p>}
                        </div>
                      ))}
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="tips">
                  <Card>
                    <CardContent className="pt-4 space-y-4">
                      {r.resume_tips_for_internships.length > 0 && (
                        <div className="space-y-1">
                          <p className="text-sm font-semibold">Resume Tips</p>
                          {r.resume_tips_for_internships.map((t, i) => <p key={i} className="text-sm">• {t}</p>)}
                        </div>
                      )}
                      {r.networking_tips.length > 0 && (
                        <div className="space-y-1">
                          <p className="text-sm font-semibold">Networking Tips</p>
                          {r.networking_tips.map((t, i) => <p key={i} className="text-sm">• {t}</p>)}
                        </div>
                      )}
                      {r.common_mistakes.length > 0 && (
                        <div className="space-y-1">
                          <p className="text-sm font-semibold text-destructive">Common Mistakes to Avoid</p>
                          {r.common_mistakes.map((t, i) => <p key={i} className="text-sm">✗ {t}</p>)}
                        </div>
                      )}
                      {r.top_platforms.length > 0 && (
                        <div className="flex flex-wrap gap-1 pt-2 border-t">
                          {r.top_platforms.map((p) => <Badge key={p} variant="secondary">{p}</Badge>)}
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
