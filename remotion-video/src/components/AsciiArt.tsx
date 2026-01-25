import React from "react";

// ASCII art for RAILGUN - large block letters style
export const RAILGUN_ASCII = `
██████╗  █████╗ ██╗██╗      ██████╗ ██╗   ██╗███╗   ██╗
██╔══██╗██╔══██╗██║██║     ██╔════╝ ██║   ██║████╗  ██║
██████╔╝███████║██║██║     ██║  ███╗██║   ██║██╔██╗ ██║
██╔══██╗██╔══██║██║██║     ██║   ██║██║   ██║██║╚██╗██║
██║  ██║██║  ██║██║███████╗╚██████╔╝╚██████╔╝██║ ╚████║
╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚══════╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝
`.trim();

// Line-by-line version for animation
export const RAILGUN_LINES = RAILGUN_ASCII.split("\n");

// Calculate total characters
export const TOTAL_ASCII_CHARS = RAILGUN_ASCII.length;

interface AsciiTextProps {
  text: string;
  visibleChars: number;
  color?: string;
}

export const AsciiText: React.FC<AsciiTextProps> = ({
  text,
  visibleChars,
  color = "#00D9FF",
}) => {
  const displayText = text.slice(0, Math.floor(visibleChars));
  const showCursor = visibleChars < text.length;

  return (
    <pre
      style={{
        fontFamily: "'JetBrains Mono', 'Fira Code', 'Consolas', monospace",
        fontSize: "18px",
        lineHeight: "1.1",
        color: color,
        margin: 0,
        padding: 0,
        whiteSpace: "pre",
        textShadow: `0 0 10px ${color}40, 0 0 20px ${color}20`,
      }}
    >
      {displayText}
      {showCursor && (
        <span
          style={{
            backgroundColor: color,
            color: "transparent",
          }}
        >
          █
        </span>
      )}
    </pre>
  );
};
