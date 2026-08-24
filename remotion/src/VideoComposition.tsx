import React from "react";
import { AbsoluteFill, Audio, Sequence, staticFile } from "remotion";
import { SceneImage } from "./components/SceneImage";
import { Captions } from "./components/Captions";
import { ClosingCard } from "./components/ClosingCard";
import { HighlightSweep } from "./components/HighlightSweep";
import { VideoManifest } from "./manifest";

export const VideoComposition: React.FC<{
  projectId: string;
  manifest: VideoManifest;
}> = ({ projectId, manifest }) => {
  const base = `renders/${projectId}/`;
  const fps = manifest.fps;
  const totalDurationFrames = Math.round(
    manifest.scenes.reduce((sum, scene) => sum + scene.duration, 0) * fps
  );

  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      {manifest.scenes.map((scene, i) => {
        const startFrame = Math.round(scene.start * fps);
        const durationFrames = Math.round(scene.duration * fps);
        return (
          <Sequence key={scene.image} from={startFrame} durationInFrames={durationFrames}>
            <SceneImage
              src={staticFile(base + scene.image)}
              sceneIndex={i}
              durationInFrames={durationFrames}
            />
            {scene.highlight && <HighlightSweep fps={fps} />}
            {scene.sfx && (
              <Sequence from={Math.round(fps * 0.25)}>
                <Audio src={staticFile(base + scene.sfx)} volume={0.7} />
              </Sequence>
            )}
          </Sequence>
        );
      })}

      <Captions cues={manifest.subtitles} fps={fps} />

      {manifest.closingText && (
        <ClosingCard
          text={manifest.closingText}
          subtitle={manifest.closingSubtitle}
          seconds={manifest.closingTextSeconds}
          fps={fps}
          totalDurationFrames={totalDurationFrames}
          color={manifest.closingColor ?? undefined}
        />
      )}

      <Audio src={staticFile(base + manifest.voiceSrc)} />
      {manifest.musicSrc && <Audio src={staticFile(base + manifest.musicSrc)} volume={0.15} />}
    </AbsoluteFill>
  );
};
