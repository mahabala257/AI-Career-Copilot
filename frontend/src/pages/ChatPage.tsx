import { useRef, useState, useEffect } from "react";
import { useMutation } from "@tanstack/react-query";
import { Send, Loader2, Bot, User as UserIcon, Mic, MicOff, Volume2, Sparkles } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { chatApi } from "@/services/api";
import { useAuthStore } from "@/stores/authStore";
import { useSpeechRecognition, speak, speechSupported } from "@/hooks/useSpeech";
import { apiErrorMessage } from "@/lib/apiError";
import { FormattedMessage } from "@/components/FormattedMessage";

interface ChatMsg {
  role: "user" | "assistant";
  text: string;
  agents?: string[];
  recommendations?: string[];
}

const SUGGESTIONS = [
  "What skills am I missing for an AI Engineer role?",
  "Give me 3 portfolio projects to build",
  "I have an interview at Google next week — help me prepare",
  "I keep failing interviews and feel like giving up",
];

export default function ChatPage() {
  const user = useAuthStore((s) => s.user);
  const [messages, setMessages] = useState<ChatMsg[]>([{
    role: "assistant",
    text: `Hi ${user?.name?.split(" ")[0] || "there"}! I'm your AI career assistant. Ask me anything — I'll route you to the right specialist (resume, skills, interview, projects, wellness, and more).`,
  }]);
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  const { listening, toggle, stop: stopMic, supported: micSupported, error: micError } = useSpeechRecognition(
    (t) => setInput((prev) => (prev.trim() ? prev.trim() + " " : "") + t)
  );

  const mutation = useMutation({
    mutationFn: (vars: { message: string; history: { role: string; content: string }[] }) =>
      chatApi.send({ message: vars.message, target_role: user?.target_role || undefined, history: vars.history }),
    onSuccess: (data) => {
      setMessages((m) => [...m, {
        role: "assistant",
        text: data.reply,
        agents: data.agents_used,
        recommendations: data.recommendations,
      }]);
    },
    onError: (e: unknown) => {
      setMessages((m) => [...m, { role: "assistant", text: apiErrorMessage(e, "Sorry — I hit an error. Please try again.") }]);
    },
  });

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, mutation.isPending]);

  const send = (text?: string) => {
    const msg = (text ?? input).trim();
    if (!msg || mutation.isPending) return;
    if (listening) stopMic();   // turn the mic off when the message is sent
    const history = messages.map((m) => ({ role: m.role, content: m.text }));
    setMessages((m) => [...m, { role: "user", text: msg }]);
    setInput("");
    mutation.mutate({ message: msg, history });
  };

  return (
    <div className="flex flex-col h-[calc(100vh-3rem)]">
      <div className="mb-4">
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <Bot className="w-8 h-8 text-primary" /> AI Career Assistant
        </h1>
        <p className="text-muted-foreground mt-1">
          One chat, all your agents — ask anything about your career.
        </p>
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto space-y-4 pr-1">
        {messages.map((m, i) => (
          <div key={i} className={`flex gap-3 ${m.role === "user" ? "flex-row-reverse" : ""}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
              m.role === "user" ? "bg-primary" : "bg-muted"
            }`}>
              {m.role === "user"
                ? <UserIcon className="w-4 h-4 text-primary-foreground" />
                : <Bot className="w-4 h-4 text-foreground" />}
            </div>
            <div className={`max-w-[80%] space-y-2 ${m.role === "user" ? "items-end" : ""}`}>
              <Card className={m.role === "user" ? "bg-primary text-primary-foreground" : ""}>
                <CardContent className="p-3 text-sm leading-relaxed">
                  {m.role === "assistant"
                    ? <FormattedMessage text={m.text} />
                    : <span className="whitespace-pre-wrap">{m.text}</span>}
                </CardContent>
              </Card>
              {m.role === "assistant" && (m.agents?.length || m.recommendations?.length || speechSupported) ? (
                <div className="space-y-2">
                  {!!m.agents?.length && (
                    <div className="flex flex-wrap gap-1 items-center">
                      <span className="text-xs text-muted-foreground">Handled by:</span>
                      {m.agents.map((a) => <Badge key={a} variant="secondary" className="text-xs">{a}</Badge>)}
                    </div>
                  )}
                  {!!m.recommendations?.length && (
                    <div className="space-y-1">
                      {m.recommendations.map((r, ri) => (
                        <div key={ri} className="flex items-start gap-1.5 text-xs text-muted-foreground">
                          <Sparkles className="w-3 h-3 text-yellow-500 mt-0.5 flex-shrink-0" />{r}
                        </div>
                      ))}
                    </div>
                  )}
                  {speechSupported && (
                    <Button variant="ghost" size="sm" className="h-6 text-xs gap-1" onClick={() => speak(m.text)}>
                      <Volume2 className="w-3 h-3" /> Listen
                    </Button>
                  )}
                </div>
              ) : null}
            </div>
          </div>
        ))}

        {mutation.isPending && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center flex-shrink-0">
              <Bot className="w-4 h-4" />
            </div>
            <Card><CardContent className="p-3 text-sm flex items-center gap-2 text-muted-foreground">
              <Loader2 className="w-4 h-4 animate-spin" /> Thinking…
            </CardContent></Card>
          </div>
        )}

        {messages.length <= 1 && !mutation.isPending && (
          <div className="flex flex-wrap gap-2 pt-2">
            {SUGGESTIONS.map((s) => (
              <button key={s} onClick={() => send(s)}
                className="text-xs px-3 py-1.5 rounded-full border text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors">
                {s}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Composer */}
      <div className="pt-3 mt-2 border-t">
        <div className="flex items-end gap-2">
          {micSupported && (
            <Button variant={listening ? "destructive" : "outline"} size="icon" className="flex-shrink-0" onClick={toggle} title="Speak">
              {listening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
            </Button>
          )}
          <Textarea
            placeholder="Ask anything about your career…"
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
        {micError && <p className="text-xs text-amber-600 mt-1">{micError}</p>}
      </div>
    </div>
  );
}
