import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Brain, Loader2, CheckCircle, XCircle, Send } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { quizApi } from "@/services/api";
import type { QuizGenerateResponse, QuizScoreResponse } from "@/types";

export default function QuizCenterPage() {
  const [topic, setTopic] = useState("");
  const [difficulty, setDifficulty] = useState("medium");
  const [quiz, setQuiz] = useState<QuizGenerateResponse | null>(null);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [scoreResult, setScoreResult] = useState<QuizScoreResponse | null>(null);

  const generateMutation = useMutation({
    mutationFn: () => quizApi.generate({ topic, difficulty, quiz_type: "mcq" }),
    onSuccess: (data) => { setQuiz(data); setAnswers({}); setScoreResult(null); },
  });

  const submitMutation = useMutation({
    mutationFn: () => quizApi.submit({
      quiz_id: quiz!.quiz_id,
      answers: Object.entries(answers).map(([id, answer]) => ({ question_id: Number(id), answer })),
    }),
    onSuccess: setScoreResult,
  });

  const selectAnswer = (qId: number, opt: string) => setAnswers((prev) => ({ ...prev, [qId]: opt }));
  const answeredCount = Object.keys(answers).length;
  const totalQ = quiz?.questions?.length ?? 0;

  const gradeColor = (g: string) => g === "excellent" ? "text-green-600" : g === "good" ? "text-blue-600" : g === "satisfactory" ? "text-yellow-600" : "text-red-600";

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Quiz Center</h1>
        <p className="text-muted-foreground mt-1">Test your knowledge with AI-generated MCQ quizzes</p>
      </div>

      {/* Config */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid sm:grid-cols-3 gap-4">
            <div className="space-y-2 sm:col-span-1">
              <Label>Topic</Label>
              <Input placeholder="e.g. Machine Learning, Python" value={topic} onChange={(e) => setTopic(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label>Difficulty</Label>
              <Select value={difficulty} onValueChange={setDifficulty}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="easy">Easy</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="hard">Hard</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-end">
              <Button className="w-full" onClick={() => generateMutation.mutate()} disabled={generateMutation.isPending}>
                {generateMutation.isPending ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Generating...</> : <><Brain className="w-4 h-4 mr-2" />Generate Quiz</>}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Quiz */}
      {quiz && !scoreResult && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-semibold">{quiz.topic} — {quiz.difficulty}</h2>
              <p className="text-sm text-muted-foreground">{answeredCount}/{totalQ} answered</p>
            </div>
            <div className="flex items-center gap-3">
              <Progress value={(answeredCount / totalQ) * 100} className="w-32 h-2" />
              <Button size="sm" onClick={() => submitMutation.mutate()} disabled={answeredCount === 0 || submitMutation.isPending}>
                {submitMutation.isPending ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Scoring...</> : <><Send className="w-4 h-4 mr-2" />Submit</>}
              </Button>
            </div>
          </div>

          {quiz.questions.map((q, i) => (
            <Card key={q.id}>
              <CardHeader className="pb-3">
                <div className="flex gap-3">
                  <span className="w-6 h-6 rounded-full bg-primary/10 text-primary text-xs font-bold flex items-center justify-center flex-shrink-0 mt-0.5">{i + 1}</span>
                  <p className="text-sm font-medium">{q.question}</p>
                </div>
              </CardHeader>
              <CardContent>
                {q.options && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {Object.entries(q.options).map(([key, value]) => (
                      <button
                        key={key}
                        onClick={() => selectAnswer(q.id, key)}
                        className={`text-left p-3 rounded-lg border text-sm transition-colors ${answers[q.id] === key ? "border-primary bg-primary/5 font-medium" : "border-muted hover:border-primary/50 hover:bg-muted/50"}`}
                      >
                        <span className="font-bold text-primary mr-2">{key}.</span>{value}
                      </button>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Score Results */}
      {scoreResult && (
        <div className="space-y-4">
          {/* Score card */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <div className={`text-5xl font-bold ${gradeColor(scoreResult.grade)}`}>{scoreResult.score_percent}%</div>
                  <div className="text-muted-foreground text-sm">{scoreResult.correct_answers}/{scoreResult.total_questions} correct</div>
                </div>
                <div className="text-right space-y-1">
                  <Badge variant={scoreResult.score_percent >= 75 ? "success" : scoreResult.score_percent >= 60 ? "info" : "warning"}>
                    {scoreResult.grade}
                  </Badge>
                  <p className="text-sm text-muted-foreground">{scoreResult.encouragement}</p>
                </div>
              </div>
              <Progress value={scoreResult.score_percent} className="h-3" />
            </CardContent>
          </Card>

          {/* Weak/Strong areas */}
          <div className="grid sm:grid-cols-2 gap-4">
            {scoreResult.weak_areas?.length > 0 && (
              <Card>
                <CardHeader><CardTitle className="text-sm text-red-600">Weak Areas</CardTitle></CardHeader>
                <CardContent>{scoreResult.weak_areas.map((w) => <Badge key={w} variant="destructive" className="mr-1 mb-1">{w}</Badge>)}</CardContent>
              </Card>
            )}
            {scoreResult.strong_areas?.length > 0 && (
              <Card>
                <CardHeader><CardTitle className="text-sm text-green-600">Strong Areas</CardTitle></CardHeader>
                <CardContent>{scoreResult.strong_areas.map((s) => <Badge key={s} variant="success" className="mr-1 mb-1">{s}</Badge>)}</CardContent>
              </Card>
            )}
          </div>

          {/* Per-question results */}
          <Card>
            <CardHeader><CardTitle className="text-sm">Question Results</CardTitle></CardHeader>
            <CardContent className="space-y-2">
              {scoreResult.question_results?.map((r) => (
                <div key={r.question_id} className="flex items-center gap-3 py-1 border-b last:border-0">
                  {r.is_correct ? <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" /> : <XCircle className="w-4 h-4 text-red-500 flex-shrink-0" />}
                  <span className="text-sm text-muted-foreground flex-1">Q{r.question_id}</span>
                  <span className="text-xs">Your: <strong>{r.user_answer || "—"}</strong></span>
                  {!r.is_correct && <span className="text-xs text-green-600">Correct: <strong>{r.correct_answer}</strong></span>}
                  <Badge variant="secondary" className="text-xs">{r.topic_area}</Badge>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Recommendations */}
          {scoreResult.improvement_recommendations?.length > 0 && (
            <Card>
              <CardHeader><CardTitle className="text-sm">Study Recommendations</CardTitle></CardHeader>
              <CardContent className="space-y-2">
                {scoreResult.improvement_recommendations.map((r, i) => (
                  <div key={i} className="text-sm flex items-start gap-2">
                    <span className="text-primary mt-0.5">→</span>{r}
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          <Button variant="outline" onClick={() => { setQuiz(null); setScoreResult(null); }}>
            Take Another Quiz
          </Button>
        </div>
      )}

      {!quiz && !generateMutation.isPending && (
        <Card className="min-h-[200px] flex items-center justify-center">
          <CardContent className="text-center space-y-3">
            <Brain className="w-12 h-12 mx-auto text-muted-foreground/30" />
            <p className="text-muted-foreground">Enter a topic and generate your quiz</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
