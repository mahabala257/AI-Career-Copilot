import { useState, useRef, useEffect } from "react";
import { usePersistentState } from "@/hooks/usePersistentState";
import { useMutation } from "@tanstack/react-query";
import {
  Mic, MicOff, Loader2, AlertCircle, CheckCircle2, XCircle,
  BookOpen, Copy, Check, ChevronRight, Star, Volume2, Send, Bot, MessageCircleQuestion
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
import { useSpeechRecognition, speak, stopSpeaking, speechSupported } from "@/hooks/useSpeech";
import { apiErrorMessage } from "@/lib/apiError";
import { FormattedMessage } from "@/components/FormattedMessage";
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

function SpeakButton({ text }: { text: string }) {
  if (!speechSupported || !text) return null;
  return (
    <Button
      type="button" variant="ghost" size="icon" className="h-7 w-7 flex-shrink-0"
      title="Read aloud"
      onClick={() => speak(text)}
    >
      <Volume2 className="w-3.5 h-3.5" />
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

function DoubtsChat() {
  const [messages, setMessages] = usePersistentState<{ role: "user" | "assistant"; text: string }[]>("english-doubts", [
    { role: "assistant", text: "Ask me anything about English or interview communication — grammar doubts, how to phrase something, how to improve fluency, whether a sentence sounds professional, and more. I'll remember our conversation, so feel free to follow up." },
  ]);
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const { listening, toggle, stop: stopMic, supported: micSupported } = useSpeechRecognition(
    (t) => setInput((p) => (p.trim() ? p.trim() + " " : "") + t)
  );

  const mutation = useMutation({
    mutationFn: (vars: { question: string; history: { role: string; content: string }[] }) =>
      englishApi.ask({ question: vars.question, history: vars.history }),
    onSuccess: (data) => setMessages((m) => [...m, { role: "assistant", text: data.answer }]),
    onError: (e: unknown) => {
      setMessages((m) => [...m, { role: "assistant", text: apiErrorMessage(e, "Sorry — I hit an error. Please try again.") }]);
    },
  });

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, mutation.isPending]);

  const send = (text?: string) => {
    const q = (text ?? input).trim();
    if (!q || mutation.isPending) return;
    if (listening) stopMic();
    const history = messages.map((m) => ({ role: m.role, content: m.text }));
    setMessages((m) => [...m, { role: "user", text: q }]);
    setInput("");
    mutation.mutate({ question: q, history });
  };

  return (
    <Card className="flex flex-col h-[calc(100vh-16rem)] min-h-[400px]">
      <CardContent className="flex flex-col flex-1 overflow-hidden p-4">
        <div ref={scrollRef} className="flex-1 overflow-y-auto space-y-4 pr-1">
          {messages.map((m, i) => (
            <div key={i} className={`flex gap-3 ${m.role === "user" ? "flex-row-reverse" : ""}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${m.role === "user" ? "bg-primary" : "bg-muted"}`}>
                {m.role === "user" ? <Mic className="w-4 h-4 text-primary-foreground" /> : <Bot className="w-4 h-4" />}
              </div>
              <div className="max-w-[80%] space-y-1">
                <div className={`rounded-lg p-3 text-sm leading-relaxed ${
                  m.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted"
                }`}>
                  {m.role === "assistant"
                    ? <FormattedMessage text={m.text} />
                    : <span className="whitespace-pre-wrap">{m.text}</span>}
                </div>
                {m.role === "assistant" && speechSupported && (
                  <Button variant="ghost" size="sm" className="h-6 text-xs gap-1" onClick={() => speak(m.text)}>
                    <Volume2 className="w-3 h-3" /> Listen
                  </Button>
                )}
              </div>
            </div>
          ))}
          {mutation.isPending && (
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center"><Bot className="w-4 h-4" /></div>
              <div className="rounded-lg p-3 text-sm bg-muted flex items-center gap-2 text-muted-foreground">
                <Loader2 className="w-4 h-4 animate-spin" /> Thinking…
              </div>
            </div>
          )}
        </div>

        <div className="pt-3 mt-2 border-t flex items-end gap-2">
          {micSupported && (
            <Button variant={listening ? "destructive" : "outline"} size="icon" className="flex-shrink-0" onClick={toggle} title="Speak">
              {listening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
            </Button>
          )}
          <Textarea
            placeholder="Ask an English or interview-communication question…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }}
            rows={1}
            className="resize-none min-h-[44px] max-h-32"
          />
          <Button className="flex-shrink-0" onClick={() => send()} disabled={!input.trim() || mutation.isPending}>
            <Send className="w-4 h-4" />
          </Button>
        </div>
        {listening && (
          <span className="flex items-center gap-1.5 text-xs text-red-500 mt-1">
            <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" /> Listening…
          </span>
        )}
      </CardContent>
    </Card>
  );
}

export default function EnglishCoachPage() {
  const user = useAuthStore((s) => s.user);
  const [mode, setMode] = usePersistentState<"evaluate" | "scripts" | "ask">("english-mode", "evaluate");
  const [spokenText, setSpokenText] = useState("");
  const [contextType, setContextType] = useState("interview_answer");
  const [question, setQuestion] = useState("");
  const [experienceLevel, setExperienceLevel] = useState("fresher");
  const [evalResult, setEvalResult] = usePersistentState<EnglishEvaluateResponse | null>("english-eval", null);
  const [scriptResult, setScriptResult] = usePersistentState<ScriptGenerateResponse | null>("english-scripts", null);

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

  // Voice input — appends recognized speech into the answer box
  const { listening, toggle, supported: micSupported } = useSpeechRecognition(
    (text) => setSpokenText((prev) => (prev ? prev.trim() + " " : "") + text)
  );

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
        <Button
          variant={mode === "ask" ? "default" : "outline"}
          onClick={() => setMode("ask")}
        >
          <MessageCircleQuestion className="w-4 h-4 mr-2" /> Ask a Doubt
        </Button>
      </div>

      {/* ── ASK A DOUBT MODE ──────────────────────────────────────────────── */}
      {mode === "ask" && <DoubtsChat />}

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
                <div className="flex items-center justify-between">
                  <Label>Your Answer *</Label>
                  {micSupported && (
                    <Button
                      type="button"
                      variant={listening ? "destructive" : "outline"}
                      size="sm"
                      className="h-7 gap-1.5"
                      onClick={toggle}
                    >
                      {listening
                        ? <><MicOff className="w-3.5 h-3.5" /> Stop</>
                        : <><Mic className="w-3.5 h-3.5" /> Speak</>}
                    </Button>
                  )}
                </div>
                <Textarea
                  placeholder="Paste your transcript, type your answer, or click Speak to dictate..."
                  value={spokenText}
                  onChange={(e) => setSpokenText(e.target.value)}
                  rows={10}
                  maxLength={5000}
                />
                <div className="flex items-center justify-between">
                  <p className="text-xs text-muted-foreground">{spokenText.length}/5000</p>
                  {listening && (
                    <span className="flex items-center gap-1.5 text-xs text-red-500">
                      <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" /> Listening…
                    </span>
                  )}
                </div>
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
            ) : (r.error_reason || !r.scores || !r.star_compliance) ? (
              <Card className="h-48 flex items-center justify-center border-amber-200 bg-amber-50">
                <div className="text-center text-amber-700 space-y-3 px-6">
                  <AlertCircle className="w-10 h-10 mx-auto opacity-50" />
                  <p className="text-sm">
                    Couldn&apos;t evaluate your answer{r.error_reason ? ` (${r.error_reason})` : ""}. Please try again in a moment.
                  </p>
                  <Button variant="outline" size="sm" onClick={() => evalMutation.mutate()} disabled={evalMutation.isPending}>Retry</Button>
                </div>
              </Card>
            ) : (
              <Tabs defaultValue="scores">
                <TabsList className="w-full">
                  <TabsTrigger value="scores" className="flex-1">Scores</TabsTrigger>
                  <TabsTrigger value="corrected" className="flex-1">Corrected</TabsTrigger>
                  <TabsTrigger value="issues" className="flex-1">
                    Issues {(r.issues?.length ?? 0) > 0 && <Badge variant="destructive" className="ml-1 h-4 px-1 text-xs">{r.issues.length}</Badge>}
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
                      {(r.top_3_improvements?.length ?? 0) > 0 && (
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
                          <div className="flex items-center gap-1">
                            {speechSupported && r.corrected_text && (
                              <Button
                                type="button" variant="ghost" size="icon" className="h-7 w-7"
                                title="Read aloud"
                                onClick={() => speak(r.corrected_text)}
                              >
                                <Volume2 className="w-3.5 h-3.5" />
                              </Button>
                            )}
                            <CopyButton text={r.corrected_text} />
                          </div>
                        </div>
                        <div className="p-3 rounded bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-800 text-sm whitespace-pre-wrap">
                          {r.corrected_text || "No corrected version generated."}
                        </div>
                      </div>
                      {(r.annotations?.length ?? 0) > 0 && (
                        <div className="space-y-2 pt-2 border-t">
                          <p className="text-sm font-semibold">Change Notes</p>
                          {r.annotations.map((a, i) => (
                            <div key={i} className="text-sm border-l-2 border-muted pl-3 py-1">
                              <span className="text-red-500 line-through break-words">{a.original}</span>
                              <span className="text-muted-foreground mx-1.5">→</span>
                              <span className="text-green-600 font-medium break-words">{a.corrected}</span>
                              {a.reason && (
                                <span className="block text-xs text-muted-foreground mt-0.5">{a.reason}</span>
                              )}
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
                      {(r.issues?.length ?? 0) === 0 ? (
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
                      {(r.vocabulary_upgrades?.length ?? 0) === 0 ? (
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
                            <div className="flex items-center gap-1">
                              <SpeakButton text={r.practice_scripts.elevator_pitch_30s} />
                              <CopyButton text={r.practice_scripts.elevator_pitch_30s} />
                            </div>
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
                            <div className="flex items-center gap-1">
                              <SpeakButton text={r.practice_scripts.self_intro_2min} />
                              <CopyButton text={r.practice_scripts.self_intro_2min} />
                            </div>
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
                        <div className="flex items-center gap-1">
                          <SpeakButton text={sc.elevator_pitch_30s} />
                          <CopyButton text={sc.elevator_pitch_30s} />
                        </div>
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
                        <div className="flex items-center gap-1">
                          <SpeakButton text={sc.self_intro_2min} />
                          <CopyButton text={sc.self_intro_2min} />
                        </div>
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
                            <div className="flex items-center gap-1">
                              <SpeakButton text={a} />
                              <CopyButton text={a} />
                            </div>
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
