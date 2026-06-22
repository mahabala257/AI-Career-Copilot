import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import {
  Mic, Loader2, AlertCircle, CheckCircle2, XCircle,
  BookOpen, Copy, Check, ChevronRight, Star
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { englishApi } from "@/services/api";
import { useAuthStore } from "@/stores/authStore";
import type { EnglishEvaluateResponse, ScriptGenerateResponse } from "@/types";

function ScoreGauge({ label, value }: { label: string; value: number }) {
  const color = value >= 80 ? "bg-green-500" : value >= 60 ? "bg-yellow-500" : "bg-red-500";
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-semibold">{value}</span>
      </div>
      <div className="h-1.5 rounded-full bg-muted overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${value}%` }} />
      </div>
    </div>
  );
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <Button
      variant="ghost" size="icon" className="h-7 w-7 flex-shrink-0"
      onClick={() => { navigator.clipboard.writeText(text); setCopied(true); setTimeout(() => setCopied(false), 2000); }}
    >
      {copied ? <Check className="w-3.5 h-3.5 text-green-500" /> : <Copy className="w-3.5 h-3.5" />}
    </Button>
  );
}

const issueTypeColor: Record<string, string> = {
  filler_word:  "border-orange-300 bg-orange-50 dark:bg-orange-950/30",
  grammar:      "border-red-300 bg-red-50 dark:bg-red-950/30",
  vocabulary:   "border-blue-300 bg-blue-50 dark:bg-blue-950/30",
  structure:    "border-purple-300 bg-purple-50 dark:bg-purple-950/30",
  clarity:      "border-yellow-300 bg-yellow-50 dark:bg-yellow-950/30",
  conciseness:  "border-gray-300 bg-gray-50 dark:bg-gray-950/30",
};

export default function EnglishCoachPage() {
  const user = useAuthStore((s) => s.user);
  const [mode, setMode] = useState<"evaluate" | "scripts">("evaluate");
  const [spokenText, setSpokenText] = useState("");
  const [contextType, setContextType] = useState("interview_answer");
  const [question, setQuestion] = useState("");
  const [experienceLevel, setExperienceLevel] = useState("fresher");
  const [evalResult, setEvalResult] = useState<EnglishEvaluateResponse | null>(null);
  const [scriptResult, setScriptResult] = useState<ScriptGenerateResponse | null>(null);

  const evalMutation = useMutation({
    mutationFn: () => englishApi.evaluate({ spoken_text: spokenText, context_type: contextType, question }),
    onSuccess: (data) => setEvalResult(data),
  });

  const scriptMutation = useMutation({
    mutationFn: () => englishApi.generateScripts({ experience_level: experienceLevel }),
    onSuccess: (data) => setScriptResult(data),
  });

  const r   = evalResult?.result;
  const sc  = scriptResult?.scripts;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <Mic className="w-8 h-8 text-pink-600" /> English Coach
        </h1>
        <p className="text-muted-foreground mt-1">
          Fix grammar, eliminate filler words, improve STAR structure, and get personalised practice scripts
        </p>
      </div>

      {/* Mode toggle */}
      <div className="flex gap-2">
        <Button
          variant={mode === "evaluate" ? "default" : "outline"}
          onClick={() => setMode("evaluate")}
        >
          Evaluate My Answer
        </Button>
        <Button
          variant={mode === "scripts" ? "default" : "outline"}
          onClick={() => setMode("scripts")}
        >
          Generate Practice Scripts
        </Button>
      </div>

      {/* ── EVALUATE MODE ──────────────────────────────────────────────────── */}
      {mode === "evaluate" && (
        <div className="grid lg:grid-cols-3 gap-6">
          <Card className="lg:col-span-1">
            <CardHeader>
              <CardTitle className="text-lg">Submit Your Answer</CardTitle>
              <CardDescription>Paste a transcript or type your answer</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Context Type</Label>
                <Select value={contextType} onValueChange={setContextType}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="interview_answer">Interview Answer</SelectItem>
                    <SelectItem value="self_intro">Self Introduction</SelectItem>
                    <SelectItem value="email">Professional Email</SelectItem>
                    <SelectItem value="presentation">Presentation Script</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Question Being Answered <span className="text-muted-foreground">(optional)</span></Label>
                <Input
                  placeholder="e.g. Tell me about yourself"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label>Your Answer *</Label>
                <Textarea
                  placeholder="Paste your transcript or type your answer here..."
                  value={spokenText}
                  onChange={(e) => setSpokenText(e.target.value)}
                  rows={10}
                  maxLength={5000}
                />
                <p className="text-xs text-muted-foreground">{spokenText.length}/5000</p>
              </div>
              <Button
                className="w-full"
                onClick={() => evalMutation.mutate()}
                disabled={spokenText.trim().length < 20 || evalMutation.isPending}
              >
                {evalMutation.isPending
                  ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Evaluating...</>
                  : <><Mic className="w-4 h-4 mr-2" />Evaluate</>
                }
              </Button>
              {spokenText.trim().length > 0 && spokenText.trim().length < 20 && (
                <p className="text-xs text-muted-foreground text-center">Please write at least 20 characters</p>
              )}
              {evalMutation.isError && (
                <div className="flex items-center gap-2 p-3 rounded bg-destructive/10 text-destructive text-sm">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  {(evalMutation.error as any)?.response?.data?.detail || "Evaluation failed. Please try again."}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Results */}
          <div className="lg:col-span-2 space-y-4">
            {!r ? (
              <Card className="h-48 flex items-center justify-center">
                <div className="text-center text-muted-foreground space-y-2">
                  <Mic className="w-10 h-10 mx-auto opacity-20" />
                  <p>Submit your answer to see the evaluation</p>
                </div>
              </Card>
            ) : (
              <Tabs defaultValue="scores">
                <TabsList className="w-full">
                  <TabsTrigger value="scores" className="flex-1">Scores</TabsTrigger>
                  <TabsTrigger value="corrected" className="flex-1">Corrected</TabsTrigger>
                  <TabsTrigger value="issues" className="flex-1">
                    Issues {r.issues.length > 0 && <Badge variant="destructive" className="ml-1 h-4 px-1 text-xs">{r.issues.length}</Badge>}
                  </TabsTrigger>
                  <TabsTrigger value="star" className="flex-1">STAR</TabsTrigger>
                  <TabsTrigger value="vocab" className="flex-1">Vocab</TabsTrigger>
                  <TabsTrigger value="scripts" className="flex-1">Scripts</TabsTrigger>
                </TabsList>

                {/* Scores */}
                <TabsContent value="scores">
                  <Card>
                    <CardContent className="pt-4 space-y-4">
                      <div className="flex items-center justify-center">
                        <div className="text-center">
                          <p className="text-6xl font-bold" style={{
                            color: r.scores.overall >= 80 ? "#22c55e" : r.scores.overall >= 60 ? "#f59e0b" : "#ef4444"
                          }}>
                            {r.scores.overall}
                          </p>
                          <p className="text-sm text-muted-foreground">Overall Score</p>
                        </div>
                      </div>
                      <div className="space-y-3 pt-2">
                        <ScoreGauge label="Grammar"     value={r.scores.grammar} />
                        <ScoreGauge label="Fluency"     value={r.scores.fluency} />
                        <ScoreGauge label="Structure"   value={r.scores.structure} />
                        <ScoreGauge label="Vocabulary"  value={r.scores.vocabulary} />
                        <ScoreGauge label="Conciseness" value={r.scores.conciseness} />
                      </div>
                      {r.encouragement && (
                        <div className="flex items-start gap-2 p-3 rounded bg-green-50 dark:bg-green-950/30 text-sm">
                          <Star className="w-4 h-4 text-yellow-500 mt-0.5 flex-shrink-0" />
                          <span>{r.encouragement}</span>
                        </div>
                      )}
                      {r.top_3_improvements.length > 0 && (
                        <div className="space-y-1.5 pt-2 border-t">
                          <p className="text-sm font-semibold">Top 3 Things to Fix:</p>
                          {r.top_3_improvements.map((imp, i) => (
                            <div key={i} className="flex items-center gap-2 text-sm">
                              <ChevronRight className="w-3.5 h-3.5 text-primary flex-shrink-0" />
                              {imp}
                            </div>
                          ))}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </TabsContent>

                {/* Corrected text */}
                <TabsContent value="corrected">
                  <Card>
                    <CardContent className="pt-4 space-y-4">
                      {r.original_text && (
                        <div className="space-y-1">
                          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Your Original</p>
                          <div className="p-3 rounded bg-muted/50 text-sm whitespace-pre-wrap text-muted-foreground">
                            {r.original_text}
                          </div>
                        </div>
                      )}
                      <div className="space-y-1">
                        <div className="flex items-center justify-between">
                          <p className="text-xs font-semibold text-green-600 uppercase tracking-wide">Corrected Version ✓</p>
                          <CopyButton text={r.corrected_text} />
                        </div>
                        <div className="p-3 rounded bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-800 text-sm whitespace-pre-wrap">
                          {r.corrected_text || "No corrected version generated."}
                        </div>
                      </div>
                      {r.annotations.length > 0 && (
                        <div className="space-y-2 pt-2 border-t">
                          <p className="text-sm font-semibold">Change Notes</p>
                          {r.annotations.map((a, i) => (
                            <div key={i} className="flex items-start gap-2 text-sm">
                              <span className="font-mono text-red-500 line-through flex-shrink-0">{a.original}</span>
                              <span className="text-muted-foreground">→</span>
                              <span className="font-mono text-green-600 flex-shrink-0">{a.corrected}</span>
                              <span className="text-muted-foreground text-xs">({a.reason})</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </TabsContent>

                {/* Issues */}
                <TabsContent value="issues">
                  <Card>
                    <CardContent className="pt-4 space-y-3">
                      {r.issues.length === 0 ? (
                        <div className="flex items-center gap-2 text-green-600">
                          <CheckCircle2 className="w-5 h-5" />
                          <span className="text-sm font-medium">No significant issues found!</span>
                        </div>
                      ) : (
                        r.issues.map((issue, i) => (
                          <div
                            key={i}
                            className={`p-3 rounded border text-sm space-y-1 ${issueTypeColor[issue.type] || issueTypeColor.clarity}`}
                          >
                            <div className="flex items-center gap-2">
                              <Badge variant="outline" className="text-xs capitalize">{issue.type.replace(/_/g, " ")}</Badge>
                              <span className="font-mono font-medium">"{issue.found}"</span>
                            </div>
                            <p className="font-medium">→ {issue.suggestion}</p>
                            {issue.explanation && (
                              <p className="text-xs text-muted-foreground">{issue.explanation}</p>
                            )}
                          </div>
                        ))
                      )}
                    </CardContent>
                  </Card>
                </TabsContent>

                {/* STAR */}
                <TabsContent value="star">
                  <Card>
                    <CardContent className="pt-4 space-y-4">
                      <div className="grid grid-cols-2 gap-3">
                        {(["situation", "task", "action", "result"] as const).map((key) => (
                          <div
                            key={key}
                            className={`p-3 rounded border flex items-center gap-2 ${
                              r.star_compliance[key]
                                ? "bg-green-50 border-green-300 dark:bg-green-950/30"
                                : "bg-red-50 border-red-300 dark:bg-red-950/30"
                            }`}
                          >
                            {r.star_compliance[key]
                              ? <CheckCircle2 className="w-4 h-4 text-green-600 flex-shrink-0" />
                              : <XCircle className="w-4 h-4 text-red-500 flex-shrink-0" />
                            }
                            <span className="capitalize font-medium text-sm">{key}</span>
                          </div>
                        ))}
                      </div>
                      <div className="space-y-1">
                        <div className="flex justify-between text-sm">
                          <span>STAR Compliance Score</span>
                          <span className="font-bold">{r.star_compliance.score}/100</span>
                        </div>
                        <Progress value={r.star_compliance.score} className="h-2" />
                      </div>
                      {r.star_compliance.missing && (
                        <div className="p-3 rounded bg-orange-50 dark:bg-orange-950/30 text-sm space-y-1">
                          <p className="font-semibold text-orange-700">Missing: {r.star_compliance.missing}</p>
                          {r.star_compliance.tip && <p className="text-orange-600">{r.star_compliance.tip}</p>}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </TabsContent>

                {/* Vocab */}
                <TabsContent value="vocab">
                  <Card>
                    <CardContent className="pt-4 space-y-3">
                      {r.vocabulary_upgrades.length === 0 ? (
                        <p className="text-sm text-muted-foreground">No vocabulary issues detected.</p>
                      ) : (
                        r.vocabulary_upgrades.map((v, i) => (
                          <div key={i} className="flex items-start gap-3 p-3 rounded bg-muted/50 text-sm">
                            <div className="flex-1">
                              <span className="text-red-500 line-through">{v.weak}</span>
                              <span className="mx-2 text-muted-foreground">→</span>
                              <span className="text-green-600 font-medium">{v.strong}</span>
                            </div>
                            {v.context && <p className="text-xs text-muted-foreground">{v.context}</p>}
                          </div>
                        ))
                      )}
                    </CardContent>
                  </Card>
                </TabsContent>

                {/* Practice Scripts */}
                <TabsContent value="scripts">
                  <Card>
                    <CardContent className="pt-4 space-y-4">
                      {r.practice_scripts?.elevator_pitch_30s && (
                        <div className="space-y-1">
                          <div className="flex items-center justify-between">
                            <p className="text-sm font-semibold">30-Second Elevator Pitch</p>
                            <CopyButton text={r.practice_scripts.elevator_pitch_30s} />
                          </div>
                          <div className="p-3 rounded bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800 text-sm whitespace-pre-wrap">
                            {r.practice_scripts.elevator_pitch_30s}
                          </div>
                        </div>
                      )}
                      {r.practice_scripts?.self_intro_2min && (
                        <div className="space-y-1">
                          <div className="flex items-center justify-between">
                            <p className="text-sm font-semibold">2-Minute Self Introduction</p>
                            <CopyButton text={r.practice_scripts.self_intro_2min} />
                          </div>
                          <div className="p-3 rounded bg-purple-50 dark:bg-purple-950/30 border border-purple-200 dark:border-purple-800 text-sm whitespace-pre-wrap">
                            {r.practice_scripts.self_intro_2min}
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </TabsContent>
              </Tabs>
            )}
          </div>
        </div>
      )}

      {/* ── SCRIPTS MODE ──────────────────────────────────────────────────── */}
      {mode === "scripts" && (
        <div className="grid lg:grid-cols-3 gap-6">
          <Card className="lg:col-span-1">
            <CardHeader>
              <CardTitle className="text-lg">Generate Scripts</CardTitle>
              <CardDescription>
                Get a personalised elevator pitch, self-introduction, and HR answers for your profile
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Experience Level</Label>
                <Select value={experienceLevel} onValueChange={setExperienceLevel}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="fresher">Fresher</SelectItem>
                    <SelectItem value="1-2 years">1–2 years</SelectItem>
                    <SelectItem value="2-3 years">2–3 years</SelectItem>
                    <SelectItem value="3-5 years">3–5 years</SelectItem>
                    <SelectItem value="5+ years">5+ years</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="p-3 rounded bg-muted/50 text-xs text-muted-foreground space-y-1">
                <p className="font-semibold">💡 Tip</p>
                <p>Run Resume Analyzer first so the agent can use your actual skills and projects in the scripts.</p>
              </div>
              <Button
                className="w-full"
                onClick={() => scriptMutation.mutate()}
                disabled={scriptMutation.isPending}
              >
                {scriptMutation.isPending
                  ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Generating...</>
                  : <><BookOpen className="w-4 h-4 mr-2" />Generate Scripts</>
                }
              </Button>
              {scriptMutation.isError && (
                <div className="flex items-center gap-2 p-3 rounded bg-destructive/10 text-destructive text-sm">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  Generation failed. Please try again.
                </div>
              )}
            </CardContent>
          </Card>

          <div className="lg:col-span-2 space-y-4">
            {!sc ? (
              <Card className="h-48 flex items-center justify-center">
                <div className="text-center text-muted-foreground space-y-2">
                  <BookOpen className="w-10 h-10 mx-auto opacity-20" />
                  <p>Click Generate Scripts to get your personalised scripts</p>
                </div>
              </Card>
            ) : (
              <>
                {sc.elevator_pitch_30s && (
                  <Card>
                    <CardHeader className="pb-2">
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-base">⚡ 30-Second Elevator Pitch</CardTitle>
                        <CopyButton text={sc.elevator_pitch_30s} />
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="p-3 rounded bg-blue-50 dark:bg-blue-950/30 border border-blue-200 text-sm whitespace-pre-wrap">
                        {sc.elevator_pitch_30s}
                      </div>
                    </CardContent>
                  </Card>
                )}
                {sc.self_intro_2min && (
                  <Card>
                    <CardHeader className="pb-2">
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-base">🎤 2-Minute Self Introduction</CardTitle>
                        <CopyButton text={sc.self_intro_2min} />
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="p-3 rounded bg-purple-50 dark:bg-purple-950/30 border border-purple-200 text-sm whitespace-pre-wrap">
                        {sc.self_intro_2min}
                      </div>
                    </CardContent>
                  </Card>
                )}
                {sc.hr_answers && Object.keys(sc.hr_answers).length > 0 && (
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-base">💬 HR Question Answers</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {Object.entries(sc.hr_answers).map(([q, a]) => (
                        <div key={q} className="space-y-1 pb-3 border-b last:border-0">
                          <div className="flex items-center justify-between">
                            <p className="text-sm font-semibold capitalize">{q.replace(/_/g, " ")}</p>
                            <CopyButton text={a} />
                          </div>
                          <div className="p-3 rounded bg-muted/50 text-sm whitespace-pre-wrap">{a}</div>
                        </div>
                      ))}
                    </CardContent>
                  </Card>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
