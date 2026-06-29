/**
 * FormattedMessage — renders an LLM reply with light markdown:
 *   **bold**, `- ` / `* ` / `• ` bullet lists, and line breaks.
 * No external dependency (avoids react-markdown). Safe: it only emits <strong>,
 * <ul>/<li>, and <p> from plain text — no raw HTML injection.
 */
import React from "react";

function renderInline(text: string, keyPrefix: string): React.ReactNode[] {
  // Split on **bold** segments
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    const m = part.match(/^\*\*([^*]+)\*\*$/);
    if (m) return <strong key={`${keyPrefix}-b${i}`}>{m[1]}</strong>;
    return <React.Fragment key={`${keyPrefix}-t${i}`}>{part}</React.Fragment>;
  });
}

export function FormattedMessage({ text }: { text: string }) {
  const lines = (text || "").split("\n");
  const blocks: React.ReactNode[] = [];
  let bullets: string[] = [];

  const flushBullets = () => {
    if (bullets.length) {
      blocks.push(
        <ul key={`ul-${blocks.length}`} className="list-disc pl-5 space-y-1 my-1">
          {bullets.map((b, i) => (
            <li key={i}>{renderInline(b, `li-${blocks.length}-${i}`)}</li>
          ))}
        </ul>
      );
      bullets = [];
    }
  };

  lines.forEach((line) => {
    const trimmed = line.trim();
    const bullet = trimmed.match(/^[-*•]\s+(.*)$/);
    if (bullet) {
      bullets.push(bullet[1]);
    } else if (trimmed === "") {
      flushBullets();
    } else {
      flushBullets();
      blocks.push(
        <p key={`p-${blocks.length}`} className="my-1">
          {renderInline(trimmed, `p-${blocks.length}`)}
        </p>
      );
    }
  });
  flushBullets();

  return <div className="text-sm leading-relaxed [&>p:first-child]:mt-0 [&>*:last-child]:mb-0">{blocks}</div>;
}
