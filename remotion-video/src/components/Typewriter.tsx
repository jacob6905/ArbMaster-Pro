import React from "react";
import { interpolate, useCurrentFrame } from "remotion";

interface TypewriterProps {
  text: string;
  startFrame: number;
  durationFrames: number;
  color?: string;
  fontSize?: number;
  showCursor?: boolean;
  cursorBlinkRate?: number;
}

export const Typewriter: React.FC<TypewriterProps> = ({
  text,
  startFrame,
  durationFrames,
  color = "#00D9FF",
  fontSize = 32,
  showCursor = true,
  cursorBlinkRate = 15,
}) => {
  const frame = useCurrentFrame();

  // Calculate how many characters should be visible
  const progress = interpolate(
    frame,
    [startFrame, startFrame + durationFrames],
    [0, text.length],
    {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }
  );

  const visibleChars = Math.floor(progress);
  const displayText = text.slice(0, visibleChars);
  const isTyping = frame >= startFrame && visibleChars < text.length;
  const isDone = visibleChars >= text.length;

  // Cursor blink logic
  const cursorVisible = isTyping || (isDone && Math.floor((frame - startFrame) / cursorBlinkRate) % 2 === 0);

  return (
    <div
      style={{
        fontFamily: "'JetBrains Mono', 'Fira Code', 'Consolas', monospace",
        fontSize: `${fontSize}px`,
        color: color,
        whiteSpace: "pre",
        textShadow: `0 0 10px ${color}60, 0 0 30px ${color}30`,
      }}
    >
      {displayText}
      {showCursor && cursorVisible && (
        <span
          style={{
            backgroundColor: color,
            marginLeft: "2px",
            animation: "none",
          }}
        >
          {" "}
        </span>
      )}
    </div>
  );
};

interface FadeInTypewriterProps extends TypewriterProps {
  fadeInDuration?: number;
}

export const FadeInTypewriter: React.FC<FadeInTypewriterProps> = ({
  fadeInDuration = 10,
  startFrame,
  ...props
}) => {
  const frame = useCurrentFrame();

  const opacity = interpolate(
    frame,
    [startFrame, startFrame + fadeInDuration],
    [0, 1],
    {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }
  );

  return (
    <div style={{ opacity }}>
      <Typewriter startFrame={startFrame} {...props} />
    </div>
  );
};
