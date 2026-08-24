import React from "react";
import { AbsoluteFill, Img, interpolate, useCurrentFrame } from "remotion";

const FADE_IN_FRAMES = 10;
const MAX_ZOOM = 1.12;

export const SceneImage: React.FC<{
  src: string;
  sceneIndex: number;
  durationInFrames: number;
}> = ({ src, sceneIndex, durationInFrames }) => {
  const frame = useCurrentFrame();

  const opacity = interpolate(frame, [0, FADE_IN_FRAMES], [0, 1], {
    extrapolateRight: "clamp",
  });

  // Alterna la direccion del Ken Burns (zoom in / zoom out) entre escenas.
  const zoomIn = sceneIndex % 2 === 0;
  const scale = interpolate(
    frame,
    [0, durationInFrames],
    zoomIn ? [1, MAX_ZOOM] : [MAX_ZOOM, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill style={{ opacity }}>
      <Img
        src={src}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          transform: `scale(${scale})`,
        }}
      />
    </AbsoluteFill>
  );
};
