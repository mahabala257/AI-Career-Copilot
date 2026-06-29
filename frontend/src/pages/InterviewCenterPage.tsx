import { useState } from "react";
import { usePersistentState } from "@/hooks/usePersistentState";
import { useMutation } from "@tanstack/react-query";
import { MessageSquare, Loader2, ChevronDown, ChevronUp, Send, CheckCircle, Mic, MicOff, Volume2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { interviewApi } from "@/services/api";
import { useAuthStore } from "@/stores/authStore";
import { useSpeechRecognition, speak, speechSupported } from "@/hooks/useSpeech";
import type { InterviewResponse, EvaluationResponse, QuestionItem } from "@/types";

function QuestionCard({ q, index, answer, onAnswer }: { q: QuestionItem; index: number; answer?: string; onAnswer: (id: number, ans: string) => void }) {
  const [expanded, setExpanded] = useState(index === 0);
  const { listening, toggle, supported: micSupported } = useSpeechRecognition(
    (text) => onAnswer(q.id, ((answer || "").trim() ? answer!.trim() + " " : "") + text)
  );
  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-start gap-3 cursor-pointer" onClick={() => setExpanded(!expanded)}>
            <span className="w-6 h-6 rounded-full bg-primary/10 text-primary text-xs font-bold flex items-center justify-center flex-shrink-0 mt-0.5">{index + 1}</span>
            <p className="text-sm font-medium">{q.question}</p>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            {speechSupported && (
              <Button
                type="button" variant="ghost" size="icon" className="h-7 w-7"
                title="Read question aloud"
                onClick={() => speak(q.question)}
              >
                <Volume2 className="w-3.5 h-3.5" />
              </Button>
            )}
            {q.difficulty && <Badge variant="outline" className="text-xs">{q.difficulty}</Badge>}
            <button type="button" onClick={() => setExpanded(!expanded)}>
              {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>
          </div>
        </div>
      </CardHeader>
      {expanded && (
        <CardContent className="space-y-3">
          {q.key_concepts?.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {q.key_concepts.map((k) => <Badge key={k} variant="secondary" className="text-xs">{k}</Badge>)}
            </div>
          )}
          {q.tips?.length > 0 && (
            <p className="text-xs text-muted-foreground">💡 {q.tips[0]}</p>
          )}
          <div className="space-y-1">
            <div className="flex items-center justify-between">
              <Label className="text-xs">Your Answer</Label>
              {micSupported && (
                <Button
                  type="button"
                  variant={listening ? "destructive" : "outline"}
                  size="sm"
                  className="h-6 gap-1.5 text-xs"
                  onClick={toggle}
                >
                  {listening ? <><MicOff className="w-3 h-3" /> Stop</> : <><Mic className="w-3 h-3" /> Speak</>}
                </Button>
              )}
            </div>
            <Textarea
              rows={3} placeholder="Type your answer, or click Speak to dictate..."
              value={answer || ""}
              onChange={(e) => onAnswer(q.id, e.target.value)}
              className="text-sm"
            />
            {listening && (
              <span className="flex items-center gap-1.5 text-xs text-red-500">
                <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" /> Listening…
              </span>
            )}
          </div>
        </CardContent>
      )}
    </Card>
  );
}

function EvalResults({ evalResult }: { evalResult: EvaluationResponse }) {
  return (
    <div className="space-y-4">
      <Card>
        <CardContent className="pt-6 text-center">
          <div className="text-5xl font-bold text-primary">{evalResult.overall_score}</div>
          <div className="text-muted-foreground text-sm">/ 100</div>
          <Badge variant={evalResult.overall_score >= 70 ? "success" : "warning"} className="mt-2">
            {evalResult.overall_grade}
          </Badge>
          <p className="text-sm mt-3 text-muted-foreground">{evalResult.readiness_assessment}</p>
        </CardContent>
      </Card>
      {evalResult.top_improvement_areas?.length > 0 && (
        <Card>
          <CardHeader><CardTitle className="text-sm">Focus Areas</CardTitle></CardHeader>
          <CardContent>
            {evalResult.top_improvement_areas.map((area, i) => (
              <div key={i} className="flex items-center gap-2 text-sm py-1">
                <span className="w-4 h-4 rounded-full bg-orange-100 text-orange-600 text-xs flex items-center justify-center">{i + 1}</span>
                {area}
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default function InterviewCenterPage() {
  const user = useAuthStore((s) => s.user);
  const [targetRole, setTargetRole] = useState(user?.target_role || "");
  const [interviewType, setInterviewType] = useState<"hr" | "technical" | "coding">("technical");
  const [difficulty, setDifficulty] = useState<"easy" | "medium" | "hard">("medium");
  const [session, setSession] = usePersistentState<InterviewResponse | null>("interview-session", null);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [evalResult, setEvalResult] = usePersistentState<EvaluationResponse | null>("interview-eval", null);

  const generateMutation = useMutation({
    mutationFn: () => interviewApi.generate({ target_role: targetRole, interview_type: interviewType, difficulty }),
    onSuccess: (data) => { setSession(data); setAnswers({}); setEvalResult(null); },
  });

  const evaluateMutation = useMutation({
    mutationFn: () => interviewApi.evaluate({
      session_id: session!.session_id,
      target_role: targetRole,
      answers: Object.entries(answers).map(([id, answer]) => ({ question_id: Number(id), answer })),
    }),
    onSuccess: setEvalResult,
  });

  const handleAnswer = (id: number, ans: string) => setAnswers((prev) => ({ ...prev, [id]: ans }));
  const answeredCount = Object.values(answers).filter((a) => a.trim()).length;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Interview Center</h1>
        <p className="text-muted-foreground mt-1">AI-generated interview questions with answer evaluation</p>
      </div>

      {/* Config */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid sm:grid-cols-4 gap-4">
            <div className="space-y-2 sm:col-span-2">
              <Label>Target Role</Label>
              <Input placeholder="e.g. AI Engineer" value={targetRole} onChange={(e) => setTargetRole(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label>Type</Label>
              <Select value={interviewType} onValueChange={(v: any) => setInterviewType(v)}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="technical">Technical</SelectItem>
                  <SelectItem value="hr">HR / Behavioural</SelectItem>
                  <SelectItem value="coding">Coding</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Difficulty</Label>
              <Select value={difficulty} onValueChange={(v: any) => setDifficulty(v)}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="easy">Easy</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="hard">Hard</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <Button className="mt-4" onClick={() => generateMutation.mutate()} disabled={!targetRole.trim() || generateMutation.isPending}>
            {generateMutation.isPending ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Generating...</> : <><MessageSquare className="w-4 h-4 mr-2" />Generate Questions</>}
          </Button>
        </CardContent>
      </Card>

      {/* Generation error */}
      {generateMutation.isError && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6 text-sm text-red-700">
            Could not generate interview questions right now. Please try again in a moment.
          </CardContent>
        </Card>
      )}

      {/* AI returned no questions */}
      {session && !evalResult && (session.questions?.length ?? 0) === 0 && (
        <Card>
          <CardContent className="pt-6 text-center space-y-3">
            <MessageSquare className="w-10 h-10 mx-auto text-muted-foreground/30" />
            <p className="text-muted-foreground text-sm">
              The AI couldn't generate questions{session.agent_error ? ` (${session.agent_error})` : ""}. Please try again.
            </p>
            <Button variant="outline" size="sm" onClick={() => generateMutation.mutate()} disabled={generateMutation.isPending}>Retry</Button>
          </CardContent>
        </Card>
      )}

      {/* Questions + Results */}
      {session && !evalResult && (session.questions?.length ?? 0) > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              {answeredCount}/{session.questions.length} answered · ~{session.estimated_duration_minutes} min
            </p>
            <Button size="sm" onClick={() => evaluateMutation.mutate()} disabled={answeredCount === 0 || evaluateMutation.isPending}>
              {evaluateMutation.isPending ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Evaluating...</> : <><Send className="w-4 h-4 mr-2" />Submit for Evaluation</>}
            </Button>
          </div>
          {session.questions.map((q, i) => (
            <QuestionCard key={q.id} q={q} index={i} answer={answers[q.id]} onAnswer={handleAnswer} />
          ))}
        </div>
      )}

      {evalResult && (
        <div className="grid lg:grid-cols-2 gap-6">
          <EvalResults evalResult={evalResult} />
          <Card>
            <CardHeader><CardTitle className="text-sm">Interview Tips</CardTitle></CardHeader>
            <CardContent>
              {evalResult.interview_tips?.map((t, i) => (
                <div key={i} className="flex items-start gap-2 text-sm py-1">
                  <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />{t}
                </div>
              ))}
              <Button variant="outline" className="w-full mt-4" onClick={() => { setSession(null); setEvalResult(null); }}>
                Start New Session
              </Button>
            </CardContent>
          </Card>
        </div>
      )}

      {!session && !generateMutation.isPending && (
        <Card className="min-h-[200px] flex items-center justify-center">
          <CardContent className="text-center space-y-3">
            <MessageSquare className="w-12 h-12 mx-auto text-muted-foreground/30" />
            <p className="text-muted-foreground">Set your role and generate interview questions to begin</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
