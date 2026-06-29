/**
 * useSpeech.ts — browser voice helpers (Web Speech API).
 *
 * - useSpeechRecognition: microphone → text (speech-to-text). Free, on-device
 *   in Chrome/Edge; no backend or API key. Calls onFinal with each finalized
 *   phrase so the caller can append it to a textarea.
 * - speak / stopSpeaking: text-to-speech for reading feedback aloud.
 *
 * Gracefully reports `supported=false` on browsers without the API (e.g. Firefox),
 * so the UI can hide the mic button instead of breaking.
 */
import { useCallback, useEffect, useRef, useState } from "react";

export function useSpeechRecognition(onFinal?: (text: string) => void) {
  const [listening, setListening] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const recRef = useRef<any>(null);
  const cbRef = useRef(onFinal);
  cbRef.current = onFinal;
  // True while the user wants to keep dictating. Browsers auto-stop recognition
  // after a few seconds of silence (and a hard ~60s cap), so we restart on `onend`
  // until the user explicitly stops — giving continuous dictation. We guard
  // against tight restart loops (e.g. repeated network errors).
  const shouldListenRef = useRef(false);
  const lastStartRef = useRef(0);

  const supported =
    typeof window !== "undefined" &&
    !!((window as any).SpeechRecognition || (window as any).webkitSpeechRecognition);

  useEffect(() => {
    if (!supported) return;
    const SRClass = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    const rec = new SRClass();
    rec.continuous = true;
    rec.interimResults = false;
    rec.lang = "en-US";

    rec.onstart = () => { setListening(true); setError(null); };

    rec.onresult = (e: any) => {
      let finalText = "";
      for (let i = e.resultIndex; i < e.results.length; i++) {
        if (e.results[i].isFinal) finalText += e.results[i][0].transcript;
      }
      finalText = finalText.trim();
      if (finalText) cbRef.current?.(finalText);
    };

    rec.onerror = (e: any) => {
      const err = e?.error || "unknown";
      // Fatal errors → stop and report so the UI can guide the user.
      if (err === "not-allowed" || err === "service-not-allowed") {
        shouldListenRef.current = false;
        setError("Microphone blocked. Click the lock icon in the address bar and allow the mic, then retry.");
        setListening(false);
      } else if (err === "audio-capture") {
        shouldListenRef.current = false;
        setError("No microphone found. Please connect a mic and retry.");
        setListening(false);
      }
      // 'no-speech' / 'aborted' / 'network' are transient → onend restarts.
    };

    rec.onend = () => {
      // Auto-restart only if still wanted AND the session ran long enough to
      // avoid a tight error loop (which would otherwise hammer start/stop).
      if (shouldListenRef.current && Date.now() - lastStartRef.current > 400) {
        try { lastStartRef.current = Date.now(); rec.start(); return; } catch { /* fall through */ }
      }
      shouldListenRef.current = false;
      setListening(false);
    };

    recRef.current = rec;
    return () => {
      shouldListenRef.current = false;
      try { rec.stop(); } catch { /* ignore */ }
    };
  }, [supported]);

  const start = useCallback(() => {
    if (!recRef.current) return;
    shouldListenRef.current = true;
    setError(null);
    lastStartRef.current = Date.now();
    try {
      recRef.current.start();   // onstart sets listening=true
    } catch {
      // "already started" — recognition is already running; treat as listening.
      setListening(true);
    }
  }, []);

  const stop = useCallback(() => {
    shouldListenRef.current = false;
    try { recRef.current?.stop(); } catch { /* ignore */ }
    setListening(false);
  }, []);

  const toggle = useCallback(() => (listening ? stop() : start()), [listening, start, stop]);

  return { listening, start, stop, toggle, supported, error };
}

export function speak(text: string) {
  if (typeof window === "undefined" || !window.speechSynthesis || !text) return;
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.lang = "en-US";
  u.rate = 1;
  u.pitch = 1;
  window.speechSynthesis.speak(u);
}

export function stopSpeaking() {
  if (typeof window !== "undefined" && window.speechSynthesis) {
    window.speechSynthesis.cancel();
  }
}

export const speechSupported =
  typeof window !== "undefined" && !!window.speechSynthesis;
