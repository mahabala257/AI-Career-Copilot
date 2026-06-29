import type { AxiosError } from "axios";

/**
 * Turns any API/network error into a friendly, user-facing message.
 * Prefers the backend's `detail`, then handles rate-limit (503/429) and
 * timeouts (free AI tier can be slow), then a sensible fallback.
 */
export function apiErrorMessage(
  err: unknown,
  fallback = "Something went wrong. Please try again.",
): string {
  const e = err as AxiosError<{ detail?: string }>;
  const detail = e?.response?.data?.detail;
  if (detail) return detail;

  const status = e?.response?.status;
  if (status === 503 || status === 429) {
    return "The AI service is busy right now (free-tier rate limit). Please wait ~30 seconds and try again.";
  }
  if (e?.code === "ECONNABORTED" || /timeout/i.test(e?.message || "")) {
    return "That took too long — the free AI tier may be slow at the moment. Please try again.";
  }
  if (e?.message === "Network Error") {
    return "Can't reach the server. Make sure the backend is running, then try again.";
  }
  return fallback;
}
