import { useEffect, useRef, useState } from "react";
import {
  apiUrl,
  AuthError,
  createJob,
  fetchHealth,
  fetchJob,
  fetchProviders,
  getToken,
  setToken,
  type JobRequest,
  type JobStatus,
  type ProviderOption,
  type ProvidersResponse,
  type SceneInput,
} from "./api";

const PASOS = [
  { stage: "script", label: "Guion" },
  { stage: "visuals", label: "Imagenes" },
  { stage: "voice", label: "Voz" },
  { stage: "music", label: "Musica" },
  { stage: "subtitles", label: "Subtitulos" },
  { stage: "render", label: "Render" },
];

const ESCENA_VACIA: SceneInput = { description: "", duration_s: 4, sfx_prompt: "", overlay_text: "" };

function disponible(opcion: ProviderOption, keys: Record<string, boolean>): boolean {
  return !opcion.requires || keys[opcion.requires] === true;
}

type SelectorProps = {
  titulo: string;
  ayuda: string;
  opciones: ProviderOption[];
  valor: string;
  keys: Record<string, boolean>;
  onChange: (id: string) => void;
};

function SelectorProveedor({ titulo, ayuda, opciones, valor, keys, onChange }: SelectorProps) {
  return (
    <div className="selector">
      <div className="selector-head">
        <h3>{titulo}</h3>
        <p>{ayuda}</p>
      </div>
      <div className="opciones">
        {opciones.map((opcion) => {
          const activo = valor === opcion.id;
          const habilitado = disponible(opcion, keys);
          return (
            <button
              key={opcion.id}
              type="button"
              className={`opcion ${activo ? "activa" : ""} ${habilitado ? "" : "deshabilitada"}`}
              onClick={() => habilitado && onChange(opcion.id)}
              disabled={!habilitado}
              title={habilitado ? undefined : `Falta ${opcion.requires} en el .env`}
            >
              <span className="opcion-top">
                <span className="opcion-label">{opcion.label}</span>
                <span className={`tag ${opcion.cost}`}>{opcion.cost}</span>
              </span>
              {opcion.note && <span className="opcion-note">{opcion.note}</span>}
              {!habilitado && <span className="opcion-falta">Falta {opcion.requires} en el .env</span>}
            </button>
          );
        })}
      </div>
    </div>
  );
}

export default function App() {
  const [catalogo, setCatalogo] = useState<ProvidersResponse | null>(null);
  const [errorCatalogo, setErrorCatalogo] = useState<string | null>(null);
  const [pideClave, setPideClave] = useState(false);
  const [clave, setClave] = useState("");

  const [modo, setModo] = useState<"prueba" | "real">("prueba");
  const [tema, setTema] = useState("");
  const [origenGuion, setOrigenGuion] = useState<"ia" | "yo">("ia");
  const [guion, setGuion] = useState("");
  const [escenas, setEscenas] = useState<SceneInput[]>([{ ...ESCENA_VACIA }]);
  const [visuals, setVisuals] = useState("pollinations");
  const [voice, setVoice] = useState("edge_tts");
  const [vozEnergica, setVozEnergica] = useState(false);
  const [music, setMusic] = useState("none");
  const [estiloMusica, setEstiloMusica] = useState("upbeat modern pop, instrumental");
  const [sfx, setSfx] = useState("none");
  const [cierre, setCierre] = useState("");
  const [renderizar, setRenderizar] = useState(true);

  const [job, setJob] = useState<JobStatus | null>(null);
  const [enviando, setEnviando] = useState(false);
  const [errorEnvio, setErrorEnvio] = useState<string | null>(null);
  const logRef = useRef<HTMLDivElement>(null);

  async function cargarCatalogo() {
    setErrorCatalogo(null);
    try {
      const salud = await fetchHealth();
      if (salud.auth_required && !getToken()) {
        setPideClave(true);
        return;
      }
      setCatalogo(await fetchProviders());
      setPideClave(false);
    } catch (err) {
      if (err instanceof AuthError) {
        setPideClave(true);
        setErrorCatalogo("La clave de acceso no es correcta.");
      } else {
        setErrorCatalogo((err as Error).message);
      }
    }
  }

  useEffect(() => {
    void cargarCatalogo();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function guardarClave() {
    setToken(clave.trim());
    setClave("");
    void cargarCatalogo();
  }

  // Polling del job mientras esta corriendo.
  useEffect(() => {
    if (!job || job.state !== "running") return;
    const id = setInterval(async () => {
      try {
        setJob(await fetchJob(job.id));
      } catch {
        /* reintentamos en el proximo tick */
      }
    }, 1500);
    return () => clearInterval(id);
  }, [job]);

  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight });
  }, [job?.events.length]);

  const keys = catalogo?.configured_keys ?? {};
  const corriendo = job?.state === "running";
  const guionPropio = origenGuion === "yo";
  const puedeEnviar =
    tema.trim().length > 0 &&
    (!guionPropio || (guion.trim().length > 0 && escenas.every((e) => e.description.trim().length > 0))) &&
    !corriendo &&
    !enviando &&
    !pideClave;

  function actualizarEscena(indice: number, cambios: Partial<SceneInput>) {
    setEscenas((previas) => previas.map((escena, i) => (i === indice ? { ...escena, ...cambios } : escena)));
  }

  async function generar() {
    setErrorEnvio(null);
    setEnviando(true);
    const request: JobRequest = {
      mode: modo,
      topic: tema.trim(),
      script_source: origenGuion,
      script: guionPropio ? guion.trim() : null,
      scenes: guionPropio
        ? escenas.map((escena) => ({
            description: escena.description.trim(),
            duration_s: escena.duration_s,
            sfx_prompt: sfx !== "none" ? escena.sfx_prompt?.trim() || null : null,
            overlay_text: escena.overlay_text?.trim() || null,
          }))
        : [],
      visuals,
      voice,
      energetic_voice: voice === "edge_tts" && vozEnergica,
      music,
      music_mood: estiloMusica,
      sfx,
      closing_text: cierre.trim() || null,
      render: renderizar,
    };
    try {
      const { job_id } = await createJob(request);
      setJob(await fetchJob(job_id));
    } catch (err) {
      if (err instanceof AuthError) {
        setPideClave(true);
        setErrorEnvio("Hace falta la clave de acceso.");
      } else {
        setErrorEnvio((err as Error).message);
      }
    } finally {
      setEnviando(false);
    }
  }

  const pasoActual = PASOS.findIndex((paso) => paso.stage === job?.stage);

  return (
    <div className="page">
      <header className="hero">
        <span className="pill">Reels · TikTok · Shorts</span>
        <h1>
          De una idea a un video vertical, <em>sin editar nada</em>
        </h1>
        <p>
          Elegi los proveedores, escribi el guion (o dejaselo a la IA) y el pipeline arma las
          imagenes, la voz en off, la musica y los subtitulos. El MP4 sale listo en 1080x1920.
        </p>
      </header>

      {pideClave && (
        <div className="clave">
          <h2>Clave de acceso</h2>
          <p>Este backend esta protegido. Pega la clave para poder generar videos.</p>
          <div className="clave-fila">
            <input
              className="campo"
              type="password"
              placeholder="Clave de acceso"
              value={clave}
              onChange={(e) => setClave(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && guardarClave()}
            />
            <button type="button" onClick={guardarClave} disabled={!clave.trim()}>
              Entrar
            </button>
          </div>
        </div>
      )}

      {errorCatalogo && (
        <div className="aviso error">
          No se pudo hablar con el backend: {errorCatalogo}
          <br />
          En local, levantalo con <code>python api.py</code>. En produccion, revisa que
          <code>VITE_API_URL</code> apunte al backend y que ese host este arriba.
        </div>
      )}

      <main className="columnas">
        <section className="panel">
          <div className="bloque">
            <h2>1. Como trabajamos</h2>
            <div className="toggle">
              <button
                type="button"
                className={modo === "prueba" ? "activo" : ""}
                onClick={() => setModo("prueba")}
              >
                Prueba
                <small>Gratis, sin APIs. Imagenes de color y audio mudo.</small>
              </button>
              <button
                type="button"
                className={modo === "real" ? "activo" : ""}
                onClick={() => setModo("real")}
              >
                Real
                <small>Usa los proveedores de IA que elijas abajo.</small>
              </button>
            </div>
          </div>

          <div className="bloque">
            <h2>2. El tema</h2>
            <input
              className="campo"
              placeholder="Ej: eventos astronomicos de 2026"
              value={tema}
              onChange={(e) => setTema(e.target.value)}
            />
          </div>

          <div className="bloque">
            <h2>3. El guion</h2>
            <div className="toggle">
              <button
                type="button"
                className={origenGuion === "ia" ? "activo" : ""}
                onClick={() => setOrigenGuion("ia")}
              >
                Lo escribe la IA
                <small>A partir del tema, con OpenRouter.</small>
              </button>
              <button
                type="button"
                className={origenGuion === "yo" ? "activo" : ""}
                onClick={() => setOrigenGuion("yo")}
              >
                Lo escribo yo
                <small>Control total del texto y de cada escena.</small>
              </button>
            </div>

            {guionPropio && (
              <div className="guion-propio">
                <label>
                  Texto de la voz en off
                  <textarea
                    className="campo"
                    rows={5}
                    placeholder="Lo que dice la narracion, completo."
                    value={guion}
                    onChange={(e) => setGuion(e.target.value)}
                  />
                </label>

                <div className="escenas-head">
                  <h3>Escenas ({escenas.length})</h3>
                  <p>Describi cada imagen en ingles: los generadores la entienden mejor.</p>
                </div>

                {escenas.map((escena, i) => (
                  <div className="escena" key={i}>
                    <div className="escena-top">
                      <span className="escena-num">{i + 1}</span>
                      <input
                        className="campo"
                        placeholder="A cat looking at the stars, cinematic, 9:16"
                        value={escena.description}
                        onChange={(e) => actualizarEscena(i, { description: e.target.value })}
                      />
                      <input
                        className="campo chico"
                        type="number"
                        min={0.5}
                        step={0.5}
                        value={escena.duration_s}
                        onChange={(e) => actualizarEscena(i, { duration_s: Number(e.target.value) || 4 })}
                      />
                      <button
                        type="button"
                        className="quitar"
                        onClick={() => setEscenas((p) => p.filter((_, j) => j !== i))}
                        disabled={escenas.length === 1}
                        aria-label={`Quitar escena ${i + 1}`}
                      >
                        ×
                      </button>
                    </div>
                    <div className="escena-extra">
                      <input
                        className="campo"
                        placeholder="Texto en pantalla (opcional)"
                        value={escena.overlay_text ?? ""}
                        onChange={(e) => actualizarEscena(i, { overlay_text: e.target.value })}
                      />
                      {sfx !== "none" && (
                        <input
                          className="campo"
                          placeholder="Efecto de sonido en ingles (opcional)"
                          value={escena.sfx_prompt ?? ""}
                          onChange={(e) => actualizarEscena(i, { sfx_prompt: e.target.value })}
                        />
                      )}
                    </div>
                  </div>
                ))}

                <button
                  type="button"
                  className="agregar"
                  onClick={() => setEscenas((p) => [...p, { ...ESCENA_VACIA }])}
                >
                  + Agregar escena
                </button>
              </div>
            )}
          </div>

          {modo === "real" && catalogo && (
            <div className="bloque">
              <h2>4. Los proveedores</h2>
              <SelectorProveedor
                titulo="Imagenes"
                ayuda="Una imagen por escena, en 9:16."
                opciones={catalogo.providers.visuals}
                valor={visuals}
                keys={keys}
                onChange={setVisuals}
              />
              <SelectorProveedor
                titulo="Voz en off"
                ayuda="Narra el guion completo."
                opciones={catalogo.providers.voice}
                valor={voice}
                keys={keys}
                onChange={setVoice}
              />
              {voice === "edge_tts" && (
                <label className="check">
                  <input
                    type="checkbox"
                    checked={vozEnergica}
                    onChange={(e) => setVozEnergica(e.target.checked)}
                  />
                  Voz rapida y animada, tipo vendedor
                </label>
              )}
              <SelectorProveedor
                titulo="Musica de fondo"
                ayuda="Instrumental, en loop por debajo de la voz."
                opciones={catalogo.providers.music}
                valor={music}
                keys={keys}
                onChange={setMusic}
              />
              {music !== "none" && (
                <input
                  className="campo"
                  placeholder="Estilo musical en ingles"
                  value={estiloMusica}
                  onChange={(e) => setEstiloMusica(e.target.value)}
                />
              )}
              <SelectorProveedor
                titulo="Efectos de sonido"
                ayuda="Un efecto puntual por escena."
                opciones={catalogo.providers.sfx}
                valor={sfx}
                keys={keys}
                onChange={setSfx}
              />
              {sfx !== "none" && !guionPropio && (
                <div className="aviso">
                  Los efectos necesitan que vos escribas el guion: el guion de la IA no define
                  efectos por escena.
                </div>
              )}
            </div>
          )}

          <div className="bloque">
            <h2>{modo === "real" ? "5" : "4"}. Ultimos detalles</h2>
            <input
              className="campo"
              placeholder="Texto de cierre (ej: shinkastudio.dev)"
              value={cierre}
              onChange={(e) => setCierre(e.target.value)}
            />
            <label className="check">
              <input
                type="checkbox"
                checked={renderizar}
                onChange={(e) => setRenderizar(e.target.checked)}
              />
              Renderizar el MP4 al terminar
            </label>
          </div>

          <button className="generar" onClick={generar} disabled={!puedeEnviar}>
            {corriendo ? "Generando..." : enviando ? "Enviando..." : "Generar video"}
          </button>
          {errorEnvio && <div className="aviso error">{errorEnvio}</div>}
        </section>

        <aside className="panel progreso">
          <h2>Progreso</h2>
          {!job && <p className="vacio">Todavia no generaste nada. Completa el formulario y dale a generar.</p>}

          {job && (
            <>
              <ol className="pasos">
                {PASOS.map((paso, i) => {
                  const estado =
                    job.state === "done" || i < pasoActual ? "hecho" : i === pasoActual ? "actual" : "pendiente";
                  return (
                    <li key={paso.stage} className={estado}>
                      <span className="punto" />
                      {paso.label}
                    </li>
                  );
                })}
              </ol>

              {job.render_progress !== null && job.render_progress < 100 && (
                <div className="barra">
                  <div className="barra-fill" style={{ width: `${job.render_progress}%` }} />
                </div>
              )}

              <div className="log" ref={logRef}>
                {job.events.map((evento, i) => (
                  <p key={i}>
                    <span className="log-stage">{evento.stage}</span>
                    {evento.message}
                  </p>
                ))}
              </div>

              {job.state === "error" && <div className="aviso error">{job.error}</div>}

              {job.state === "done" && job.video_url && (
                <div className="resultado">
                  <video src={apiUrl(job.video_url, true)} controls playsInline />
                  <a className="descargar" href={apiUrl(job.video_url, true)} download>
                    Descargar MP4
                  </a>
                  <p className="meta">
                    Proyecto <code>{job.project_id}</code> · {job.scene_count} escenas
                  </p>
                </div>
              )}

              {job.state === "done" && !job.video_url && (
                <div className="aviso">
                  Piezas generadas sin renderizar. Para el MP4:
                  <code>
                    cd remotion &amp;&amp; npx remotion render src/index.ts Video out/{job.project_id}.mp4
                    --props=public/renders/{job.project_id}/props.json
                  </code>
                </div>
              )}

              {job.script_text && (
                <details className="guion-final">
                  <summary>Ver el guion</summary>
                  <p>{job.script_text}</p>
                </details>
              )}
            </>
          )}
        </aside>
      </main>
    </div>
  );
}
