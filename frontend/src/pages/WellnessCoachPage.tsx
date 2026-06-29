import { useState } from "react";
import { usePersistentState } from "@/hooks/usePersistentState";
import { useMutation } from "@tanstack/react-query";
import { Heart, Loader2, AlertCircle, Sparkles, Phone, AlertTriangle, Mic, MicOff, Volume2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { wellnessApi } from "@/services/api";
import { useSpeechRecognition, speak, speechSupported } from "@/hooks/useSpeech";
import type { WellnessCheckinResponse } from "@/types";

const burnoutColor: Record<string, string> = {
  low:    "bg-green-100 text-green-700 border-green-300",
  medium: "bg-yellow-100 text-yellow-700 border-yellow-300",
  high:   "bg-red-100 text-red-700 border-red-300",
};

export default function WellnessCoachPage() {
  const [moodMessage, setMoodMessage] = useState("");
  const [result, setResult] = usePersistentState<WellnessCheckinResponse | null>("wellness-result", null);

  const { listening, toggle, stop: stopMic, supported: micSupported } = useSpeechRecognition(
    (t) => setMoodMessage((p) => (p.trim() ? p.trim() + " " : "") + t)
  );

  const mutation = useMutation({
    mutationFn: () => { if (listening) stopMic(); return wellnessApi.checkin({ mood_message: moodMessage }); },
    onSuccess: (data) => setResult(data),
  });

  const r = result?.result;
  const isCrisis = r?.professional_help_flag;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <Heart className="w-8 h-8 text-rose-500" /> Wellness Check-in
        </h1>
        <p className="text-muted-foreground mt-1">
          A space to share how you're feeling during your career journey — not therapy, but a supportive mentor
        </p>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-lg">How are you feeling?</CardTitle>
            <CardDescription>Be honest — this is a judgment-free space</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Your thoughts</span>
              {micSupported && (
                <Button
                  type="button"
                  variant={listening ? "destructive" : "outline"}
                  size="sm"
                  className="h-7 gap-1.5"
                  onClick={toggle}
                >
                  {listening ? <><MicOff className="w-3.5 h-3.5" /> Stop</> : <><Mic className="w-3.5 h-3.5" /> Speak</>}
                </Button>
              )}
            </div>
            <Textarea
              placeholder="e.g. I've failed 3 interviews this month and I'm starting to feel like giving up... (or click Speak to talk)"
              value={moodMessage}
              onChange={(e) => setMoodMessage(e.target.value)}
              rows={8}
              maxLength={2000}
            />
            <div className="flex items-center justify-between">
              <p className="text-xs text-muted-foreground">{moodMessage.length}/2000</p>
              {listening && (
                <span className="flex items-center gap-1.5 text-xs text-red-500">
                  <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" /> Listening…
                </span>
              )}
            </div>
            <Button
              className="w-full"
              onClick={() => mutation.mutate()}
              disabled={moodMessage.trim().length < 3 || mutation.isPending}
            >
              {mutation.isPending
                ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Listening...</>
                : <><Heart className="w-4 h-4 mr-2" />Share How I Feel</>
              }
            </Button>
            {mutation.isError && (
              <div className="flex items-center gap-2 p-3 rounded bg-destructive/10 text-destructive text-sm">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                Something went wrong. Please try again.
              </div>
            )}
            <div className="p-3 rounded bg-muted/50 text-xs text-muted-foreground">
              This tool provides career-context support, not professional mental health treatment.
              If you're in crisis, please use the resources below or contact a mental health professional.
            </div>
          </CardContent>
        </Card>

        <div className="lg:col-span-2 space-y-4">
          {!r ? (
            <Card className="h-48 flex items-center justify-center">
              <div className="text-center text-muted-foreground space-y-2">
                <Heart className="w-10 h-10 mx-auto opacity-20" />
                <p>Share what's on your mind whenever you're ready</p>
              </div>
            </Card>
          ) : isCrisis ? (
            // ── Crisis response — distinct, prominent UI ──────────────────────
            <Card className="border-2 border-red-400 bg-red-50 dark:bg-red-950/20">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-red-700">
                  <AlertTriangle className="w-5 h-5" /> Please Reach Out for Support
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-red-800 dark:text-red-200">{r.emotional_validation}</p>
                <p className="font-semibold text-red-900 dark:text-red-100">{r.next_single_action}</p>

                {r.crisis_resources && (
                  <div className="p-4 rounded-lg bg-white dark:bg-background border border-red-300 space-y-2">
                    <p className="font-semibold flex items-center gap-2">
                      <Phone className="w-4 h-4" /> Crisis Helplines (India)
                    </p>
                    {Object.entries(r.crisis_resources.india).map(([name, number]) => (
                      <div key={name} className="flex justify-between text-sm">
                        <span>{name}</span>
                        <a href={`tel:${number}`} className="font-mono font-bold text-red-600">{number}</a>
                      </div>
                    ))}
                    <p className="text-xs text-muted-foreground pt-2">{r.crisis_resources.message}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          ) : (
            // ── Normal supportive response ─────────────────────────────────────
            <>
              <Card>
                <CardContent className="pt-4 space-y-4">
                  {speechSupported && (
                    <div className="flex justify-end">
                      <Button
                        variant="ghost" size="sm" className="h-7 gap-1 text-xs"
                        onClick={() => speak([r.emotional_validation, r.reframe, r.next_single_action].filter(Boolean).join(". "))}
                      >
                        <Volume2 className="w-3.5 h-3.5" /> Listen
                      </Button>
                    </div>
                  )}
                  <p className="text-sm leading-relaxed">{r.emotional_validation}</p>
                  {r.reframe && (
                    <div className="p-3 rounded bg-blue-50 dark:bg-blue-950/30 text-sm">
                      <p className="font-semibold text-blue-700 dark:text-blue-300 mb-1">A different angle</p>
                      {r.reframe}
                    </div>
                  )}
                  {r.progress_acknowledgment && (
                    <div className="flex items-start gap-2 p-3 rounded bg-green-50 dark:bg-green-950/30 text-sm">
                      <Sparkles className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                      {r.progress_acknowledgment}
                    </div>
                  )}
                </CardContent>
              </Card>

              {r.next_single_action && (
                <Card className="border-primary/30">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-base">Your One Action for Today</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm font-medium">{r.next_single_action}</p>
                  </CardContent>
                </Card>
              )}

              {/* Burnout risk */}
              {r.burnout_risk && (
                <Card>
                  <CardContent className="pt-4 space-y-3">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold">Burnout Risk</span>
                      <Badge className={burnoutColor[r.burnout_risk.level] || burnoutColor.low}>
                        {r.burnout_risk.level}
                      </Badge>
                    </div>
                    {(r.burnout_risk.signals?.length ?? 0) > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {r.burnout_risk.signals.map((s) => (
                          <Badge key={s} variant="outline" className="text-xs">{s}</Badge>
                        ))}
                      </div>
                    )}
                    {r.burnout_risk.recommendation && (
                      <p className="text-sm text-muted-foreground">{r.burnout_risk.recommendation}</p>
                    )}
                    {r.adjusted_study_plan?.recommendation && (
                      <div className="p-3 rounded bg-orange-50 dark:bg-orange-950/30 text-sm space-y-1">
                        <p className="font-semibold text-orange-700">Schedule Adjustment</p>
                        <p>{r.adjusted_study_plan.recommendation}</p>
                        <p className="text-xs text-muted-foreground">{r.adjusted_study_plan.reason}</p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}

              {r.career_perspective && (
                <Card>
                  <CardContent className="pt-4">
                    <p className="text-sm text-muted-foreground leading-relaxed">{r.career_perspective}</p>
                  </CardContent>
                </Card>
              )}

              {r.motivational_quote && (
                <Card className="bg-gradient-to-br from-rose-50 to-orange-50 dark:from-rose-950/20 dark:to-orange-950/20">
                  <CardContent className="pt-4">
                    <p className="text-center italic font-medium">"{r.motivational_quote}"</p>
                  </CardContent>
                </Card>
              )}

              {r.weekly_reflection_prompt && (
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm text-muted-foreground">Something to sit with this week</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm font-medium">{r.weekly_reflection_prompt}</p>
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
