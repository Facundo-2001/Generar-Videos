export type SceneManifest = {
  image: string;
  start: number;
  duration: number;
  highlight?: boolean;
  overlayText?: string | null;
  sfx?: string | null;
};

export type SubtitleCue = {
  start: number;
  end: number;
  text: string;
};

export type VideoManifest = {
  fps: number;
  width: number;
  height: number;
  voiceSrc: string;
  musicSrc: string | null;
  scenes: SceneManifest[];
  subtitles: SubtitleCue[];
  closingText: string | null;
  closingSubtitle: string | null;
  closingTextSeconds: number;
  closingColor?: string | null;
};
