# Generar-Videos

Pipeline para producir videos verticales (9:16, estilo Reels / TikTok / Shorts) a partir de un tema
o de un guion escrito a mano, combinando varios servicios de IA.

Se puede usar de tres formas: una **pagina web**, un **asistente que te pregunta todo por
terminal**, o los **comandos sueltos**. Por debajo las tres usan el mismo motor, que tiene dos
etapas:

1. **Python** genera los assets (guion, imagenes, voz, musica, efectos, subtitulos) y escribe un
   `manifest.json` que describe el video.
2. **Remotion** (React) lee ese manifest y renderiza el `.mp4` final.

Las dos etapas estan separadas a proposito: podes regenerar assets sin volver a renderizar, y
retocar el render sin volver a gastar creditos de las APIs.

---

## 1. Instalacion

Requisitos: **Python 3.10+** y **Node.js 18+**.

```bash
# Dependencias de Python
pip install -r requirements.txt

# Dependencias de Remotion (una sola vez)
cd remotion
npm install
cd ..

# Dependencias de la pagina web (solo si vas a usar la interfaz web)
cd web
npm install
npm run build
cd ..
```

> Si al correr algo aparece `ModuleNotFoundError: No module named 'requests'` (o `PIL`), instalalos
> a mano: `pip install requests pillow`. Normalmente ya vienen como dependencias de `moviepy` y
> `apify-client`.

### Variables de entorno

Copia `.env.example` a `.env` y completa solo las claves de los servicios que vayas a usar:

| Variable | Para que sirve | Obligatoria |
|---|---|---|
| `OUTPUT_DIR` | Donde se guardan los assets. Debe quedar en `remotion/public/renders` para que Remotion los encuentre | recomendada |
| `OPENROUTER_API_KEY` | Guion generado por LLM | solo con `--real` o `create_occult_short.py` |
| `OPENROUTER_MODEL` | Modelo del guion (default `openai/gpt-4o-mini`) | no |
| `ELEVENLABS_API_KEY` | Voz premium y efectos de sonido | solo si los usas |
| `ELEVENLABS_VOICE_ID` | Voz por defecto de ElevenLabs | no |
| `KIEAI_API_KEY` | Imagenes (nano-banana) y musica (Suno) | solo si los usas |
| `APIFY_API_KEY` | Busqueda de fotos reales en Google Images | solo si lo usas |
| `GROQ_API_KEY` | Subtitulos por transcripcion con Whisper | no (no se usa por defecto) |
| `GOOGLE_API_KEY` | Imagenes via Gemini | no (proveedor alternativo) |
| `HUGGINGFACE_API_KEY` | Musica via MusicGen | no (proveedor alternativo) |

---

## 2. La pagina web (la forma principal de usarlo)

Levanta el servidor y abri la pagina. Desde ahi elegis los proveedores con un clic, escribis el
guion (o se lo dejas a la IA), y ves el progreso en vivo hasta que aparece el video listo para
reproducir y descargar.

```bash
python api.py
# despues abri http://127.0.0.1:8000
```

Para publicarla en internet (front en Vercel, backend en Railway/Render/Fly), esta todo listo y los
pasos estan en **[DEPLOY.md](DEPLOY.md)**.

La pagina te deja:

- Elegir entre **modo prueba** (gratis, sin APIs) y **modo real**.
- Ver cada proveedor con su etiqueta de **gratis** o **pago**. Los que necesitan una API key que no
  tenes en el `.env` aparecen deshabilitados, con el nombre de la variable que falta.
- Pedirle el guion a la IA, o escribirlo vos y armar las escenas una por una (descripcion de la
  imagen, duracion, texto en pantalla y efecto de sonido), agregando y quitando escenas a mano.
- Seguir el pipeline paso a paso (guion → imagenes → voz → musica → subtitulos → render) con el log
  en vivo, y descargar el MP4 al final.

Para trabajar sobre el codigo de la pagina con recarga automatica, en otra terminal:

```bash
cd web
npm run dev          # http://localhost:5173, proxea /api hacia el puerto 8000
```

Cuando termines de editarla, `npm run build` deja el resultado en `web/dist/`, que es lo que
`api.py` sirve directamente en el puerto 8000.

### Protegerla con una clave

Si el backend va a estar expuesto en internet, defini `APP_TOKEN` en el `.env`. Con eso la API
rechaza todo pedido sin esa clave, y la web la pide una vez y la recuerda en el navegador. Sin
clave, cualquiera que llegue a la URL puede gastarte los creditos de las APIs.

---

## 3. El asistente por terminal

Si preferis no abrir el navegador, `asistente.py` hace las mismas preguntas en la consola y termina
ofreciendote renderizar el MP4:

```bash
python asistente.py
```

Te va preguntando de a una cosa: modo, tema, quien escribe el guion, proveedores, escenas, texto de
cierre. Enter siempre toma la opcion por defecto, asi que se puede atravesar entero a los enters
para una prueba rapida.

---

## 4. Los comandos sueltos

### Paso 1: generar los assets

```bash
# Modo prueba: no llama a ninguna API ni gasta creditos (imagenes de color plano y audio mudo)
python main.py "eventos astronomicos de 2025"
```

```bash
# Modo real, todo gratis: guion con LLM + imagenes Pollinations + voz Edge-TTS
python main.py "eventos astronomicos de 2025" --real
```

Al terminar imprime algo asi:

```
Proyecto: ad573d32
Estado: Status.MANIFEST_READY
...
```

Ese `ad573d32` es el **id del proyecto**: la carpeta `remotion/public/renders/ad573d32/` con todos
los archivos generados.

### Paso 2: previsualizar o renderizar

```bash
cd remotion

# Previsualizar en el navegador (Remotion Studio)
npx remotion studio --props="{\"projectId\":\"ad573d32\"}"

# Renderizar el mp4 final
npx remotion render src/index.ts Video out/ad573d32.mp4 --props="{\"projectId\":\"ad573d32\"}"
```

El video queda en `remotion/out/`.

> En PowerShell las comillas internas se escapan con `\"`, tal como se muestra arriba. Como
> alternativa podes editar `remotion/props.json` y dejar ahi el `projectId`.

---

## 5. Opciones de `main.py`

```
python main.py "TEMA" [--real] [--visuals ...] [--voice ...] [--energetic-voice] [--music ...] [--sfx ...]
```

| Flag | Opciones | Default | Notas |
|---|---|---|---|
| `--real` | — | off | Sin este flag usa proveedores **mock** (gratis, sin APIs) |
| `--visuals` | `pollinations` \| `kieai` \| `apify` | `pollinations` | `pollinations` es gratis y sin key; `kieai` es pago y da mejor calidad; `apify` trae fotos reales de Google Images |
| `--voice` | `edge_tts` \| `elevenlabs` | `edge_tts` | `edge_tts` es gratis (voz `es-AR-TomasNeural`); `elevenlabs` requiere plan pago |
| `--energetic-voice` | — | off | Solo con `edge_tts`: voz mas rapida y animada, tipo vendedor |
| `--music` | `none` \| `kieai` | `none` | `kieai` usa Suno (pago) |
| `--sfx` | `none` \| `elevenlabs` | `none` | Efectos por escena; requiere que las escenas tengan `sfx_prompt` |

**Ojo:** el guion generado por LLM (`--real`) no define `sfx_prompt` ni `overlay_text`, asi que
`--sfx elevenlabs` no hara nada por esa via. Los efectos y los textos en pantalla se usan desde los
scripts dedicados (ver seccion 6).

### Combinaciones utiles

```bash
# Validar el pipeline completo sin gastar un peso
python main.py "mi tema"

# Lo mejor gratis
python main.py "mi tema" --real

# Calidad alta de imagen, voz gratis
python main.py "mi tema" --real --visuals kieai

# Todo pago: imagenes + voz + musica
python main.py "mi tema" --real --visuals kieai --voice elevenlabs --music kieai
```

---

## 6. Scripts dedicados

Ademas de `main.py` hay scripts con el guion, los prompts de imagen, los textos en pantalla y los
efectos ya escritos a mano. Dan mucho mas control que el LLM y se corren sin argumentos:

| Script | Que genera | APIs que necesita |
|---|---|---|
| `create_shinka_benefits_reel.py` | Reel de marketing "beneficios de tu propia tienda online" | ElevenLabs + Kie.ai |
| `create_shinka_reel.py` | Reel de marketing "sitio web propio" | ElevenLabs + Kie.ai |
| `create_occult_short.py` | Short de ocultismo/misterio, guion escrito por LLM con prompt propio | OpenRouter + ElevenLabs + Kie.ai |

```bash
python create_shinka_benefits_reel.py

# El de ocultismo si recibe un tema, y acepta tarjeta de cierre personalizada
python create_occult_short.py "el experimento Filadelfia"
python create_occult_short.py "el experimento Filadelfia" --cta "SEGUI PARA LA PARTE 2"
```

Los tres imprimen al final el comando de Remotion listo para copiar y pegar.

**Para crear tu propio video a medida**, lo mas practico es copiar
`create_shinka_benefits_reel.py` y editar sus constantes:

- `SCRIPT_TEXT`: lo que dice la voz en off, completo.
- `SCENES`: una `Scene` por imagen, con `description` (prompt de imagen, **en ingles**: los modelos
  lo entienden mejor), `duration_s`, y opcionalmente `overlay_text` (texto grande en pantalla) y
  `sfx_prompt` (efecto de sonido de esa escena).
- `MUSIC_MOOD`: descripcion del estilo musical, en ingles.

Las `duration_s` que pongas son **orientativas**: el sistema las reescala proporcionalmente para que
la suma coincida exactamente con lo que dura la voz grabada. Asi nunca queda pantalla negra ni se
corta la narracion. Igual conviene que sean realistas entre si, porque definen el reparto relativo
del tiempo entre escenas.

---

## 7. Que hay dentro de cada proyecto

Cada corrida crea `remotion/public/renders/<id>/` con:

```
scene_0.png, scene_1.png, ...   imagenes de cada escena
voice.mp3                       narracion
music.mp3                       musica de fondo (si se pidio)
sfx_0.mp3, sfx_1.mp3, ...       efectos puntuales (si se pidieron)
subtitles.srt                   subtitulos
manifest.json                   la "receta" del video que lee Remotion
```

El `manifest.json` es el contrato entre las dos etapas: tiene fps, resolucion, la lista de escenas
con sus tiempos exactos, los subtitulos ya parseados y los datos de la tarjeta de cierre. Si querés
ajustar algo chico (correr un subtitulo, cambiar un texto en pantalla, acortar una escena), podes
**editar el `manifest.json` a mano** y volver a renderizar, sin regenerar ningun asset.

---

## 8. Como esta armado el codigo

```
Dockerfile                  imagen del backend para produccion
DEPLOY.md                   como publicarlo (Vercel + Railway/Render/Fly)
api.py                      backend web (FastAPI) que usa el mismo pipeline
asistente.py                asistente interactivo por terminal
main.py                     CLI principal
create_*.py                 scripts con guion escrito a mano
web/
  src/App.tsx               la landing page entera (formulario + progreso)
  src/api.ts                tipos y llamadas al backend
  vercel.json               configuracion del deploy en Vercel
  dist/                     build que sirve api.py en el puerto 8000
videogen/
  config.py                 lee el .env
  models.py                 Scene, VideoProject, Status
  orchestrator.py           coordina el pipeline paso a paso
  manifest.py               escribe el manifest.json
  render.py                 render alternativo con moviepy (en desuso)
  providers/
    base.py                 las interfaces: Script, Visual, Voice, Music, Subtitle, SoundEffect
    mock.py                 implementaciones falsas para probar gratis
    ...                     un archivo por servicio real
remotion/
  src/Root.tsx              carga el manifest y calcula duracion/resolucion
  src/VideoComposition.tsx  arma las capas del video
  src/components/           imagen con movimiento, subtitulos, overlays, cierre
  public/renders/<id>/      los assets generados por Python
  out/                      los mp4 renderizados
```

El orquestador avanza en este orden y va marcando el estado: **guion → imagenes → efectos → voz →
musica → subtitulos → manifest**. Si algo falla, no revienta: deja el proyecto en estado `FAILED`
con el mensaje en `project.error`, y `main.py` lo imprime y sale con codigo 1.

Cada categoria de proveedor es una interfaz abstracta, asi que agregar un servicio nuevo es escribir
una clase en `videogen/providers/` que implemente el metodo correspondiente de `base.py` y
engancharla en la funcion `_build_*_provider` de `main.py`. Para que aparezca en la pagina web,
sumalo ademas al diccionario `PROVIDERS` de `api.py`: la UI se dibuja sola a partir de ese catalogo.

La pagina web y el asistente no duplican logica: los dos arman el mismo `VideoOrchestrator` llamando
a `construir_orquestador()` de `asistente.py`. El orquestador acepta un callback `on_event` opcional,
que es como el backend reporta el progreso en vivo.

Los subtitulos, por defecto, **no** se transcriben del audio: se calculan a partir del texto del
guion, repartiendo el tiempo por cantidad de caracteres. Es a proposito, para que nombres propios y
marcas (por ejemplo "ShinkaStudio.dev") aparezcan siempre escritos bien. El proveedor de
transcripcion con Whisper (`groq_subtitles.py`) sigue disponible si alguna vez lo necesitas.

---

## 9. Problemas comunes

**La pagina web dice "No se pudo hablar con el backend"**
El servidor no esta levantado o esta en otro puerto. Corre `python api.py` y recarga.

**Abro http://127.0.0.1:8000 y veo un 404**
Falta compilar la pagina: `cd web && npm install && npm run build`. `api.py` sirve `web/dist/`, y
solo la monta si esa carpeta existe cuando arranca, asi que despues de compilar hay que reiniciarlo.

**`Faltan variables de entorno en .env: ...`**
Falta una clave en `.env`. El mensaje dice cual.

**`Falta projectId` al abrir Remotion Studio**
Pasa el `--props` con el id, o editalo en `remotion/props.json`, o usá el panel de props dentro del
Studio.

**`TimeoutError: trying to connect to the browser` al renderizar**
Ya esta contemplado en `remotion/remotion.config.ts` (fuerza IPv4). Si igual pasa, verifica que el
Chrome de Remotion este instalado: `npx remotion browser ensure`.

**Pollinations tarda mucho / avisa "limite del tier gratuito"**
Es normal. El tier anonimo permite 1 imagen cada ~45 segundos por IP, asi que un video de 5 escenas
tarda unos 3-4 minutos solo en las imagenes. El provider espera y reintenta solo; no hace falta
hacer nada. Si necesitas que sea rapido, usa `--visuals kieai` (pago) o conseguite una pollen key
gratuita en https://enter.pollinations.ai.

**`403, message='Invalid response status'` al generar la voz con Edge-TTS**
Microsoft bloquea las versiones viejas de la libreria. Se arregla actualizandola:
`pip install --upgrade edge-tts`.

**Las imagenes de Pollinations salen pobres o genericas**
Es el costo de ser gratis. Para calidad de produccion usa `--visuals kieai`, o escribi los prompts a
mano en un script dedicado.

**Imagenes de Apify en un video comercial**
Son fotos de terceros con derechos de autor propios. No son libres de uso solo por aparecer en la
busqueda: para marketing real conviene un banco de fotos con licencia clara.

**El video dura distinto de lo que esperaba**
La duracion total la define la voz, no las `duration_s` del guion. Para un video mas corto, acorta
el texto narrado.
