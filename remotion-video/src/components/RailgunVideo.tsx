import React from "react";
import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
  Sequence,
} from "remotion";
import { RAILGUN_ASCII, TOTAL_ASCII_CHARS } from "./AsciiArt";
import { Typewriter } from "./Typewriter";

const CYAN = "#00D9FF";
const DARK_BG = "#0a0a0f";
const TERMINAL_GREEN = "#00FF41";

// Scanline effect for terminal aesthetic
const Scanlines: React.FC = () => {
  return (
    <div
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: `repeating-linear-gradient(
          0deg,
          transparent,
          transparent 2px,
          rgba(0, 0, 0, 0.1) 2px,
          rgba(0, 0, 0, 0.1) 4px
        )`,
        pointerEvents: "none",
        zIndex: 100,
      }}
    />
  );
};

// Animated cursor block
const BlinkingCursor: React.FC<{ color?: string }> = ({ color = CYAN }) => {
  const frame = useCurrentFrame();
  const visible = Math.floor(frame / 15) % 2 === 0;

  return (
    <span
      style={{
        display: "inline-block",
        width: "12px",
        height: "22px",
        backgroundColor: visible ? color : "transparent",
        marginLeft: "4px",
        verticalAlign: "middle",
      }}
    />
  );
};

// ASCII Art with typewriter effect
const AsciiTypewriter: React.FC<{
  startFrame: number;
  charsPerFrame: number;
}> = ({ startFrame, charsPerFrame }) => {
  const frame = useCurrentFrame();

  const visibleChars = interpolate(
    frame,
    [startFrame, startFrame + TOTAL_ASCII_CHARS / charsPerFrame],
    [0, TOTAL_ASCII_CHARS],
    {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }
  );

  const displayText = RAILGUN_ASCII.slice(0, Math.floor(visibleChars));
  const isTyping = visibleChars < TOTAL_ASCII_CHARS;

  return (
    <pre
      style={{
        fontFamily: "'JetBrains Mono', 'Fira Code', 'Consolas', monospace",
        fontSize: "22px",
        lineHeight: "1.15",
        color: CYAN,
        margin: 0,
        padding: 0,
        whiteSpace: "pre",
        textShadow: `0 0 10px ${CYAN}50, 0 0 30px ${CYAN}25, 0 0 60px ${CYAN}10`,
        letterSpacing: "0.5px",
      }}
    >
      {displayText}
      {isTyping && (
        <span
          style={{
            backgroundColor: CYAN,
            color: DARK_BG,
          }}
        >
          █
        </span>
      )}
    </pre>
  );
};

// Subtitle that appears with a fade-in effect
const SubtitleItem: React.FC<{
  text: string;
  startFrame: number;
  color?: string;
  fontSize?: number;
}> = ({ text, startFrame, color = "#ffffff", fontSize = 18 }) => {
  const frame = useCurrentFrame();

  const opacity = interpolate(frame, [startFrame, startFrame + 15], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const translateY = interpolate(
    frame,
    [startFrame, startFrame + 15],
    [10, 0],
    {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }
  );

  return (
    <div
      style={{
        opacity,
        transform: `translateY(${translateY}px)`,
        fontFamily: "'JetBrains Mono', 'Fira Code', 'Consolas', monospace",
        fontSize: `${fontSize}px`,
        color,
        letterSpacing: "2px",
      }}
    >
      {text}
    </div>
  );
};

// Terminal prompt line
const TerminalPrompt: React.FC<{ visible: boolean }> = ({ visible }) => {
  const frame = useCurrentFrame();
  const cursorBlink = Math.floor(frame / 20) % 2 === 0;

  if (!visible) return null;

  return (
    <div
      style={{
        fontFamily: "'JetBrains Mono', 'Fira Code', 'Consolas', monospace",
        fontSize: "14px",
        color: TERMINAL_GREEN,
        marginBottom: "20px",
        opacity: 0.8,
      }}
    >
      <span style={{ color: "#888" }}>$</span> ./railgun --init
      {cursorBlink && (
        <span
          style={{
            display: "inline-block",
            width: "8px",
            height: "14px",
            backgroundColor: TERMINAL_GREEN,
            marginLeft: "4px",
            verticalAlign: "middle",
          }}
        />
      )}
    </div>
  );
};

// Grid background pattern
const GridBackground: React.FC = () => {
  const frame = useCurrentFrame();

  const opacity = interpolate(frame, [0, 30], [0, 0.15], {
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundImage: `
          linear-gradient(${CYAN}10 1px, transparent 1px),
          linear-gradient(90deg, ${CYAN}10 1px, transparent 1px)
        `,
        backgroundSize: "50px 50px",
        opacity,
      }}
    />
  );
};

// Main Video Composition
export const RailgunVideo: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  // Timeline (at 30fps, 12 seconds = 360 frames)
  const ASCII_START = 15; // Start after brief pause
  const ASCII_DURATION = 90; // ~3 seconds for ASCII art
  const TAGLINE_START = ASCII_START + ASCII_DURATION + 20; // After ASCII completes
  const SUBTITLE_START = TAGLINE_START + 45; // After tagline

  // Background glow animation
  const glowIntensity = interpolate(
    frame,
    [0, 60, 120, 180, 240, 300, 360],
    [0, 0.3, 0.5, 0.4, 0.6, 0.5, 0.3],
    {
      extrapolateRight: "clamp",
    }
  );

  // Overall fade in
  const fadeIn = interpolate(frame, [0, 20], [0, 1], {
    extrapolateRight: "clamp",
  });

  // Terminal prompt visibility
  const showPrompt = frame >= 5;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: DARK_BG,
        opacity: fadeIn,
      }}
    >
      {/* Grid background */}
      <GridBackground />

      {/* Radial glow behind ASCII art */}
      <div
        style={{
          position: "absolute",
          top: "35%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          width: "800px",
          height: "400px",
          background: `radial-gradient(ellipse at center, ${CYAN}${Math.floor(
            glowIntensity * 30
          )
            .toString(16)
            .padStart(2, "0")} 0%, transparent 70%)`,
          filter: "blur(40px)",
        }}
      />

      {/* Main content container */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          height: "100%",
          padding: "40px",
        }}
      >
        {/* Terminal prompt */}
        <TerminalPrompt visible={showPrompt} />

        {/* ASCII Art with typewriter effect */}
        <Sequence from={ASCII_START}>
          <AsciiTypewriter startFrame={0} charsPerFrame={5} />
        </Sequence>

        {/* Tagline */}
        <Sequence from={TAGLINE_START}>
          <div style={{ marginTop: "40px", textAlign: "center" }}>
            <Typewriter
              text="Privacy without compromise"
              startFrame={0}
              durationFrames={40}
              color="#ffffff"
              fontSize={28}
              showCursor={false}
            />
          </div>
        </Sequence>

        {/* Subtitle items appearing sequentially */}
        <div
          style={{
            marginTop: "30px",
            display: "flex",
            gap: "30px",
            alignItems: "center",
          }}
        >
          <Sequence from={SUBTITLE_START}>
            <SubtitleItem text="zkSNARKs" startFrame={0} color={CYAN} />
          </Sequence>

          <Sequence from={SUBTITLE_START + 15}>
            <SubtitleItem
              text="•"
              startFrame={0}
              color="#666"
              fontSize={24}
            />
          </Sequence>

          <Sequence from={SUBTITLE_START + 20}>
            <SubtitleItem text="DeFi" startFrame={0} color={CYAN} />
          </Sequence>

          <Sequence from={SUBTITLE_START + 35}>
            <SubtitleItem
              text="•"
              startFrame={0}
              color="#666"
              fontSize={24}
            />
          </Sequence>

          <Sequence from={SUBTITLE_START + 40}>
            <SubtitleItem text="Cross-chain" startFrame={0} color={CYAN} />
          </Sequence>
        </div>
      </div>

      {/* Scanlines overlay */}
      <Scanlines />

      {/* Vignette effect */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background:
            "radial-gradient(ellipse at center, transparent 50%, rgba(0,0,0,0.5) 100%)",
          pointerEvents: "none",
        }}
      />
    </AbsoluteFill>
  );
};
