import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { SubtitleCue } from "../manifest";

export const Captions: React.FC<{ cues: SubtitleCue[]; fps: number }> = ({ cues, fps }) => {
  const frame = useCurrentFrame();
  const t = frame / fps;
  const active = cues.find((cue) => t >= cue.start && t < cue.end);

  if (!active) return null;

  return (
    <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: "18%" }}>
      <div
        style={{
          fontFamily: "Arial, sans-serif",
          fontWeight: 800,
          fontSize: 58,
          color: "white",
          textAlign: "center",
          textShadow:
            "0 0 10px rgba(0,0,0,0.8), 2px 2px 0 black, -2px -2px 0 black, 2px -2px 0 black, -2px 2px 0 black",
          maxWidth: "85%",
          lineHeight: 1.25,
        }}
      >
        {active.text}
      </div>
    </AbsoluteFill>
  );
};
