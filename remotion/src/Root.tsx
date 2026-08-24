import React from "react";
import { Composition, staticFile } from "remotion";
import { VideoComposition } from "./VideoComposition";
import { VideoManifest } from "./manifest";

type Props = {
  projectId: string;
};

export const RemotionRoot: React.FC = () => {
  return (
    <Composition<Props, { projectId: string; manifest: VideoManifest }>
      id="Video"
      component={VideoComposition}
      durationInFrames={30 * 10}
      fps={30}
      width={1080}
      height={1920}
      defaultProps={{ projectId: "ad573d32" }}
      calculateMetadata={async ({ props }) => {
        if (!props.projectId) {
          throw new Error(
            "Falta projectId. Editalo en el panel de props de Remotion Studio (icono de props arriba) " +
              "con el id de la carpeta dentro de remotion/public/renders/, ej: {\"projectId\": \"c9194200\"}"
          );
        }
        const url = staticFile(`renders/${props.projectId}/manifest.json`);
        const response = await fetch(url);
        const rawText = await response.text();
        let manifest: VideoManifest;
        try {
          manifest = JSON.parse(rawText);
        } catch (err) {
          throw new Error(
            `No se pudo parsear manifest.json desde ${url} (status ${response.status}). ` +
              `Primeros 200 caracteres de la respuesta: ${rawText.slice(0, 200)}`
          );
        }

        const totalDurationS = manifest.scenes.reduce((sum, s) => sum + s.duration, 0);

        return {
          durationInFrames: Math.max(1, Math.round(totalDurationS * manifest.fps)),
          fps: manifest.fps,
          width: manifest.width,
          height: manifest.height,
          props: { projectId: props.projectId, manifest },
        };
      }}
    />
  );
};
