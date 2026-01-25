import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  Sequence,
  Easing,
} from "remotion";

// Glitch effect component
const GlitchText: React.FC<{
  text: string;
  style?: React.CSSProperties;
  intensity?: number;
}> = ({ text, style, intensity = 1 }) => {
  const frame = useCurrentFrame();
  const glitchOffset = Math.sin(frame * 0.5) * 3 * intensity;
  const shouldGlitch = frame % 15 < 3;

  return (
    <div style={{ position: "relative", ...style }}>
      {/* Main text */}
      <span style={{ position: "relative", zIndex: 2 }}>{text}</span>
      {/* Cyan ghost */}
      {shouldGlitch && (
        <span
          style={{
            position: "absolute",
            left: glitchOffset,
            top: 0,
            color: "#00ffff",
            opacity: 0.7,
            zIndex: 1,
          }}
        >
          {text}
        </span>
      )}
      {/* Magenta ghost */}
      {shouldGlitch && (
        <span
          style={{
            position: "absolute",
            left: -glitchOffset,
            top: 0,
            color: "#ff00ff",
            opacity: 0.7,
            zIndex: 1,
          }}
        >
          {text}
        </span>
      )}
    </div>
  );
};

// Scan lines overlay
const ScanLines: React.FC = () => {
  const frame = useCurrentFrame();
  const offset = (frame * 2) % 4;

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
          rgba(0, 0, 0, 0.3) 2px,
          rgba(0, 0, 0, 0.3) 4px
        )`,
        backgroundPositionY: offset,
        pointerEvents: "none",
        zIndex: 100,
      }}
    />
  );
};

// Noise overlay
const NoiseOverlay: React.FC<{ opacity?: number }> = ({ opacity = 0.05 }) => {
  const frame = useCurrentFrame();

  return (
    <div
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        opacity,
        background: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' seed='${frame % 10}' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E")`,
        pointerEvents: "none",
        zIndex: 99,
      }}
    />
  );
};

// DNA Helix Animation (RAILGUN Logo style)
const DNAHelix: React.FC<{ scale?: number }> = ({ scale = 1 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const points = 12;
  const helixPoints = [];

  for (let i = 0; i < points; i++) {
    const angle = (i / points) * Math.PI * 2 + frame * 0.05;
    const x1 = Math.sin(angle) * 40 * scale;
    const x2 = Math.sin(angle + Math.PI) * 40 * scale;
    const y = (i / points) * 200 * scale - 100 * scale;

    helixPoints.push({ x1, x2, y, angle });
  }

  return (
    <svg
      width={120 * scale}
      height={220 * scale}
      viewBox={`${-60 * scale} ${-110 * scale} ${120 * scale} ${220 * scale}`}
      style={{ overflow: "visible" }}
    >
      {/* Circle outline */}
      <circle
        cx={0}
        cy={0}
        r={95 * scale}
        stroke="white"
        strokeWidth={3 * scale}
        fill="none"
      />

      {/* Diagonal line through circle */}
      <line
        x1={-70 * scale}
        y1={-70 * scale}
        x2={70 * scale}
        y2={70 * scale}
        stroke="white"
        strokeWidth={2 * scale}
      />

      {/* DNA strands */}
      {helixPoints.map((point, i) => (
        <g key={i}>
          {/* Left strand point */}
          <circle
            cx={point.x1 - 15 * scale}
            cy={point.y}
            r={4 * scale}
            fill="white"
            opacity={0.8 + Math.sin(point.angle) * 0.2}
          />
          {/* Right strand point */}
          <circle
            cx={point.x2 - 15 * scale}
            cy={point.y}
            r={4 * scale}
            fill="white"
            opacity={0.8 + Math.cos(point.angle) * 0.2}
          />
          {/* Connecting lines */}
          {i % 2 === 0 && (
            <line
              x1={point.x1 - 15 * scale}
              y1={point.y}
              x2={point.x2 - 15 * scale}
              y2={point.y}
              stroke="white"
              strokeWidth={2 * scale}
              opacity={0.6}
            />
          )}
        </g>
      ))}
    </svg>
  );
};

// Cyber grid background
const CyberGrid: React.FC = () => {
  const frame = useCurrentFrame();
  const perspectiveShift = frame * 0.5;

  return (
    <div
      style={{
        position: "absolute",
        bottom: 0,
        left: 0,
        right: 0,
        height: "50%",
        background: `
          linear-gradient(to top, rgba(0, 255, 255, 0.1) 0%, transparent 100%),
          repeating-linear-gradient(
            90deg,
            transparent,
            transparent 80px,
            rgba(0, 255, 255, 0.1) 80px,
            rgba(0, 255, 255, 0.1) 81px
          ),
          repeating-linear-gradient(
            0deg,
            transparent,
            transparent 40px,
            rgba(0, 255, 255, 0.05) 40px,
            rgba(0, 255, 255, 0.05) 41px
          )
        `,
        transform: `perspective(500px) rotateX(60deg) translateY(${perspectiveShift % 40}px)`,
        transformOrigin: "center bottom",
        opacity: 0.5,
      }}
    />
  );
};

// Floating particles
const Particles: React.FC = () => {
  const frame = useCurrentFrame();
  const particles = Array.from({ length: 30 }, (_, i) => ({
    id: i,
    x: ((i * 67) % 100),
    y: ((i * 37 + frame * 0.3) % 120) - 10,
    size: 2 + (i % 3),
    opacity: 0.3 + (i % 5) * 0.1,
  }));

  return (
    <>
      {particles.map((p) => (
        <div
          key={p.id}
          style={{
            position: "absolute",
            left: `${p.x}%`,
            top: `${p.y}%`,
            width: p.size,
            height: p.size,
            borderRadius: "50%",
            backgroundColor: p.id % 2 === 0 ? "#00ffff" : "#ff00ff",
            opacity: p.opacity,
            boxShadow: `0 0 ${p.size * 2}px ${p.id % 2 === 0 ? "#00ffff" : "#ff00ff"}`,
          }}
        />
      ))}
    </>
  );
};

// Glitch block effect
const GlitchBlocks: React.FC = () => {
  const frame = useCurrentFrame();
  const shouldShow = frame % 30 < 5;

  if (!shouldShow) return null;

  const blocks = Array.from({ length: 5 }, (_, i) => ({
    id: i,
    x: (frame * 13 + i * 200) % 1920,
    y: (frame * 7 + i * 150) % 1080,
    width: 50 + (i * 30) % 200,
    height: 5 + (i * 3) % 20,
    color: i % 2 === 0 ? "#00ffff" : "#ff00ff",
  }));

  return (
    <>
      {blocks.map((b) => (
        <div
          key={b.id}
          style={{
            position: "absolute",
            left: b.x,
            top: b.y,
            width: b.width,
            height: b.height,
            backgroundColor: b.color,
            opacity: 0.7,
            zIndex: 50,
          }}
        />
      ))}
    </>
  );
};

// Main video component
export const RailgunVideo: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  // Intro animation (frames 0-60)
  const introOpacity = interpolate(frame, [0, 30], [0, 1], {
    extrapolateRight: "clamp",
  });

  const logoScale = spring({
    frame,
    fps,
    from: 0,
    to: 1,
    config: { damping: 12, stiffness: 100 },
  });

  // Text reveal animation
  const textReveal = interpolate(frame, [45, 75], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Privacy messages animation
  const privacyTextOpacity = interpolate(frame, [90, 110], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Feature text animations
  const feature1Opacity = interpolate(frame, [120, 140], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const feature2Opacity = interpolate(frame, [160, 180], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const feature3Opacity = interpolate(frame, [200, 220], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Final call to action
  const ctaOpacity = interpolate(frame, [250, 270], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Pulse effect
  const pulse = Math.sin(frame * 0.1) * 0.1 + 1;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#0a0a0a",
        fontFamily: "'Inter', 'Helvetica Neue', Arial, sans-serif",
        overflow: "hidden",
      }}
    >
      {/* Background effects */}
      <CyberGrid />
      <Particles />

      {/* Glitch effects */}
      <GlitchBlocks />
      <NoiseOverlay opacity={0.03} />
      <ScanLines />

      {/* Main content */}
      <AbsoluteFill
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          opacity: introOpacity,
        }}
      >
        {/* Logo section */}
        <Sequence from={0} durationInFrames={300}>
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              transform: `scale(${logoScale})`,
            }}
          >
            {/* DNA Helix Logo */}
            <div
              style={{
                marginBottom: 40,
                filter: `drop-shadow(0 0 20px rgba(255, 255, 255, 0.3))`,
                transform: `scale(${pulse})`,
              }}
            >
              <DNAHelix scale={1.5} />
            </div>

            {/* RAILGUN text */}
            <div
              style={{
                clipPath: `inset(0 ${(1 - textReveal) * 100}% 0 0)`,
              }}
            >
              <GlitchText
                text="RAILGUN"
                style={{
                  fontSize: 120,
                  fontWeight: 800,
                  letterSpacing: "0.2em",
                  color: "white",
                  textShadow: `
                    0 0 10px rgba(255, 255, 255, 0.5),
                    0 0 20px rgba(0, 255, 255, 0.3),
                    0 0 40px rgba(0, 255, 255, 0.2)
                  `,
                }}
                intensity={1.5}
              />
            </div>
          </div>
        </Sequence>

        {/* Privacy tagline */}
        <Sequence from={90} durationInFrames={210}>
          <div
            style={{
              position: "absolute",
              top: "65%",
              opacity: privacyTextOpacity,
            }}
          >
            <GlitchText
              text="ON-CHAIN PRIVACY"
              style={{
                fontSize: 36,
                fontWeight: 600,
                letterSpacing: "0.3em",
                color: "#00ffff",
                textShadow: "0 0 20px rgba(0, 255, 255, 0.5)",
              }}
              intensity={0.5}
            />
          </div>
        </Sequence>

        {/* Feature highlights */}
        <Sequence from={120} durationInFrames={180}>
          <div
            style={{
              position: "absolute",
              bottom: 150,
              display: "flex",
              gap: 80,
              justifyContent: "center",
            }}
          >
            <div
              style={{
                opacity: feature1Opacity,
                textAlign: "center",
              }}
            >
              <div
                style={{
                  fontSize: 48,
                  color: "#ff00ff",
                  marginBottom: 10,
                }}
              >
                ZK
              </div>
              <div
                style={{
                  fontSize: 18,
                  color: "rgba(255, 255, 255, 0.7)",
                  letterSpacing: "0.1em",
                }}
              >
                ZERO KNOWLEDGE
              </div>
            </div>

            <div
              style={{
                opacity: feature2Opacity,
                textAlign: "center",
              }}
            >
              <div
                style={{
                  fontSize: 48,
                  color: "#00ffff",
                  marginBottom: 10,
                }}
              >
                SHIELD
              </div>
              <div
                style={{
                  fontSize: 18,
                  color: "rgba(255, 255, 255, 0.7)",
                  letterSpacing: "0.1em",
                }}
              >
                YOUR ASSETS
              </div>
            </div>

            <div
              style={{
                opacity: feature3Opacity,
                textAlign: "center",
              }}
            >
              <div
                style={{
                  fontSize: 48,
                  color: "#ff00ff",
                  marginBottom: 10,
                }}
              >
                PRIVATE
              </div>
              <div
                style={{
                  fontSize: 18,
                  color: "rgba(255, 255, 255, 0.7)",
                  letterSpacing: "0.1em",
                }}
              >
                TRANSACTIONS
              </div>
            </div>
          </div>
        </Sequence>

        {/* CTA */}
        <Sequence from={250} durationInFrames={50}>
          <div
            style={{
              position: "absolute",
              bottom: 50,
              opacity: ctaOpacity,
            }}
          >
            <GlitchText
              text="railgun.org"
              style={{
                fontSize: 28,
                fontWeight: 500,
                letterSpacing: "0.2em",
                color: "white",
                padding: "15px 40px",
                border: "2px solid rgba(0, 255, 255, 0.5)",
                background: "rgba(0, 255, 255, 0.1)",
                textShadow: "0 0 10px rgba(0, 255, 255, 0.5)",
              }}
              intensity={0.3}
            />
          </div>
        </Sequence>
      </AbsoluteFill>

      {/* Vignette effect */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background:
            "radial-gradient(ellipse at center, transparent 40%, rgba(0,0,0,0.8) 100%)",
          pointerEvents: "none",
          zIndex: 98,
        }}
      />
    </AbsoluteFill>
  );
};
