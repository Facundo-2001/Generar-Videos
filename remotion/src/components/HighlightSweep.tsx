import React from "react";
import { interpolate, useCurrentFrame } from "remotion";

/** Barra estilo resaltador que se dibuja de izquierda a derecha, simulando
 * un marcador pasando sobre una linea de texto en la imagen de fondo. */
export const HighlightSweep: React.FC<{
  fps: number;
  topPercent?: number;
  delayFrames?: number;
}> = ({ fps, topPercent = 46, delayFrames = 6 }) => {
  const frame = useCurrentFrame();
  if (frame < delayFrames) return null;

  const localFrame = frame - delayFrames;
  const sweepFrames = Math.round(fps * 0.8);
  const widthPercent = interpolate(localFrame, [0, sweepFrames], [0, 84], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        position: "absolute",
        top: `${topPercent}%`,
        left: "8%",
        width: `${widthPercent}%`,
        height: "8%",
        backgroundColor: "#FFEB3B",
        opacity: 0.55,
        mixBlendMode: "multiply",
        borderRadius: 4,
      }}
    />
  );
};
