import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

const POP_IN_FRAMES = 12;

/** Cartel corto tipo "Estas perdiendo plata" que aparece sobre el tercio
 * superior de la escena (las captions ya ocupan la parte inferior). */
export const SceneOverlayText: React.FC<{ text: string }> = ({ text }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const scale = spring({ frame, fps, config: { damping: 12, stiffness: 180 }, durationInFrames: POP_IN_FRAMES });
  const opacity = interpolate(frame, [0, POP_IN_FRAMES * 0.6], [0, 1], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "center", paddingTop: "12%" }}>
      <div
        style={{
          opacity,
          transform: `scale(${scale})`,
          fontFamily: "Arial, sans-serif",
          fontWeight: 800,
          fontSize: 56,
          color: "white",
          textAlign: "center",
          backgroundColor: "rgba(0,0,0,0.55)",
          borderRadius: 20,
          padding: "14px 32px",
          maxWidth: "85%",
          lineHeight: 1.2,
        }}
      >
        {text}
      </div>
    </AbsoluteFill>
  );
};
