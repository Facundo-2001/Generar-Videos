import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";

export const ClosingCard: React.FC<{
  text: string;
  subtitle?: string | null;
  seconds: number;
  fps: number;
  totalDurationFrames: number;
  color?: string;
}> = ({ text, subtitle, seconds, fps, totalDurationFrames, color = "#4DE8FF" }) => {
  const frame = useCurrentFrame();
  const startFrame = totalDurationFrames - Math.round(seconds * fps);

  if (frame < startFrame) return null;

  const localFrame = frame - startFrame;
  const opacity = interpolate(localFrame, [0, fps * 0.6], [0, 1], {
    extrapolateRight: "clamp",
  });
  const pulse = 1 + 0.03 * Math.sin(localFrame / 10);

  return (
    <AbsoluteFill
      style={{
        backgroundColor: `rgba(0,0,0,${0.55 * opacity})`,
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 24 }}>
        {subtitle && (
          <div
            style={{
              opacity,
              fontFamily: "Arial, sans-serif",
              fontWeight: 700,
              fontSize: 46,
              color: "white",
              textAlign: "center",
              padding: "0 10%",
            }}
          >
            {subtitle}
          </div>
        )}
        <div
          style={{
            opacity,
            transform: `scale(${pulse})`,
            fontFamily: "Arial, sans-serif",
            fontWeight: 800,
            fontSize: 90,
            color,
            textShadow: `0 0 20px ${color}, 0 0 40px ${color}, 0 0 60px ${color}`,
            textAlign: "center",
            padding: "0 8%",
          }}
        >
          {text}
        </div>
      </div>
    </AbsoluteFill>
  );
};
