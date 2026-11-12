# Subir esto a produccion

La idea es que lo uses desde la web. Para eso hay que publicar **dos cosas**:

| Pieza | Que es | Donde va |
|---|---|---|
| `web/` | La landing de React | **Vercel** |
| `api.py` + `videogen/` + `remotion/` | El motor que genera y renderiza | **Railway, Render, Fly.io o un VPS** |

---

## Por que el backend no puede ir en Vercel

Vercel es excelente para el front, pero el motor no entra ahi. No es una cuestion de configuracion:

1. **Remotion necesita Chromium.** Una funcion de Vercel tiene un limite de 50 MB de tamanio y
   Chromium sola ya lo llena. La documentacion de Remotion lo dice explicitamente: no se pueden
   renderizar videos en funciones serverless de Vercel.
2. **No hay disco que persista.** El pipeline escribe imagenes, audio y el MP4 en `remotion/`, y
   despues los lee para renderizar y servir. En serverless el disco es efimero y cada pedido puede
   caer en otra instancia, asi que el job que arranco en una no existe en la siguiente.
3. **Los tiempos no cierran.** Un video con Pollinations tarda 3-4 minutos solo en las imagenes
   (limite de 1 imagen cada 45s), mas el render. Vercel hoy llega a 300s en Hobby y 800s en Pro con
   Fluid Compute: alcanza a veces, pero es jugar al limite.

Hacer que todo corra en Vercel implicaria reescribir el render para **Remotion Lambda** (AWS) y
mover los archivos a un storage tipo S3. Es un proyecto aparte, no un ajuste de configuracion.

La alternativa corta, que es la que resuelve este repo: **front en Vercel, backend en un host que
corra Docker.**

---

## Paso 1: el backend

El [Dockerfile](Dockerfile) de la raiz ya trae Python, Node, FFmpeg y las librerias de Chrome, y
descarga el navegador de Remotion durante el build para que el primer video no tarde de mas.

### Railway (lo mas simple)

1. Entra a railway.app → **New Project** → **Deploy from GitHub repo** → elegi este repo.
2. Railway lee [railway.json](railway.json) y construye con el `Dockerfile`. No hay que configurar
   build a mano. El healthcheck apunta a `/api/health`.
3. En **Variables**, carga:

   ```
   OPENROUTER_API_KEY=...
   ELEVENLABS_API_KEY=...
   KIEAI_API_KEY=...
   APP_TOKEN=una-clave-larga-inventada
   ALLOWED_ORIGINS=https://tu-proyecto.vercel.app
   MAX_CONCURRENT_JOBS=2
   ```

   `PORT` lo inyecta Railway solo; `api.py` ya lo lee.
4. En **Settings → Networking**, genera el dominio publico. Te queda algo como
   `https://generar-videos-production.up.railway.app`.
5. Verifica que responde: abri `https://tu-backend/api/health`. Tiene que devolver
   `{"ok":true,"auth_required":true}`.

> **Elegi un plan con disco y RAM suficientes.** El render de Remotion usa bastante CPU y memoria;
> con menos de 2 GB de RAM se puede quedar sin completar. Railway y Render cobran por uso, asi que
> un backend que renderiza videos no es gratis.

### Si el build falla

La imagen no se pudo construir localmente (hace falta virtualizacion habilitada en el BIOS para
correr Docker en Windows), asi que el primer `docker build` real va a ser el de Railway. Lo que si
quedo verificado antes de subirla:

- `npm ci` dentro de `remotion/` corre limpio, o sea que `package.json` y `package-lock.json` estan
  sincronizados. Esa desincronizacion es la causa numero uno de builds rotos.
- `npx remotion browser ensure` existe y funciona en la version instalada (Remotion 4.0.514).
- La lista de paquetes `apt` es la que publica Remotion para Debian, y la base esta pinneada a
  `bookworm` justamente para que esos nombres existan.

Si igual se cae, mira el log de Railway y fijate en que paso:

| Paso que falla | Causa tipica | Arreglo |
|---|---|---|
| `apt-get install` | Un paquete cambio de nombre en esa version de Debian | Ajustar ese nombre en el `Dockerfile` |
| `npm ci` | El lockfile quedo desactualizado | Correr `npm ci` local, commitear el lock |
| `remotion browser ensure` | Sin red o sin espacio en el builder | Reintentar el deploy |
| Arranca y muere | Falta RAM | Subir el plan del servicio |

### Render / Fly.io / un VPS

Mismo Dockerfile. En Render: **New → Web Service → Docker**. En Fly: `fly launch --dockerfile`. En
un VPS: `docker build -t generar-videos . && docker run -p 8000:8000 --env-file .env generar-videos`.

---

## Paso 2: el front en Vercel

1. Entra a vercel.com → **Add New → Project** → importa este repo.
2. **Importante:** en la configuracion del proyecto, poné **Root Directory = `web`**. El repo tiene
   el proyecto de Python en la raiz; si no se lo decis, Vercel no encuentra la app.
3. Framework: Vite (lo detecta solo gracias a [web/vercel.json](web/vercel.json)).
4. En **Environment Variables**, agrega:

   ```
   VITE_API_URL=https://tu-backend.up.railway.app
   ```

   Es una variable de **build**: si la cambias despues, hay que volver a deployar para que tome
   efecto.
5. Deploy. Te queda `https://tu-proyecto.vercel.app`.

### Paso 3: cerrar el circulo

Volve al backend y asegurate de que `ALLOWED_ORIGINS` tenga **exactamente** la URL de Vercel
(sin barra final). Si no coincide, el navegador bloquea los pedidos por CORS y la pagina va a decir
que no puede hablar con el backend.

Despues abri la web, pega el `APP_TOKEN` en la pantalla de **Clave de acceso** y listo.

---

## La clave de acceso

Si `APP_TOKEN` esta seteado, la API exige esa clave en todos los endpoints salvo `/api/health`. La
web la pide una vez y la guarda en el navegador.

**Ponela siempre en produccion.** Sin clave, cualquiera que encuentre la URL puede generar videos
con tus creditos de OpenRouter, ElevenLabs y Kie.ai.

No es un sistema de usuarios: es una sola clave compartida, pensada para que uses la herramienta vos
y tu equipo. Si alguna vez la necesitas para clientes, ahi si hace falta login de verdad.

---

## Alternativa sin pagar hosting: tu propia maquina

Si solo queres la comodidad de la web y no te molesta que el motor corra en tu PC:

```bash
python api.py                              # backend local
npx cloudflared tunnel --url http://localhost:8000
```

Cloudflare te da una URL publica temporal. Poné esa URL en `VITE_API_URL` de Vercel y en
`ALLOWED_ORIGINS` del backend. Funciona igual, con dos limitaciones: la PC tiene que estar
encendida, y la URL del tunel cambia cada vez que lo reinicias (salvo que configures un tunel con
nombre).

---

## Variables de entorno, resumidas

**Backend** (Railway/Render/Fly):

| Variable | Para que | Obligatoria |
|---|---|---|
| `APP_TOKEN` | Clave de acceso de la web | muy recomendada |
| `ALLOWED_ORIGINS` | URL del front, separadas por coma | si |
| `OPENROUTER_API_KEY` | Guion con IA | si usas guion automatico |
| `ELEVENLABS_API_KEY` | Voz premium y efectos | si los usas |
| `KIEAI_API_KEY` | Imagenes nano-banana y musica Suno | si los usas |
| `APIFY_API_KEY` | Fotos reales de Google Images | si lo usas |
| `MAX_CONCURRENT_JOBS` | Cuantos videos a la vez (default 2) | no |
| `PORT` | Lo inyecta el host | no |

**Front** (Vercel):

| Variable | Para que |
|---|---|
| `VITE_API_URL` | URL publica del backend |

---

## Cosas a tener en cuenta

- **Los jobs viven en memoria.** Si el backend se reinicia, se pierde el estado de los que estaban
  corriendo. Los archivos ya generados quedan en disco, pero la web no los va a listar.
- **Los videos se acumulan.** Cada proyecto deja imagenes, audio y un MP4 en `remotion/`. Conviene
  borrar los viejos cada tanto, o el disco del host se llena.
- **El disco de los hosts suele ser efimero.** En Railway y Render, si no montas un volumen
  persistente, los videos desaparecen en cada redeploy. Descargalos cuando los generas, o agrega un
  volumen.
- **Pollinations es lento en produccion tambien** (1 imagen cada ~45s por IP). Si la web la van a
  usar seguido, `kieai` vale la pena.
- **Las fuentes del contenedor importan.** Los componentes de Remotion piden `Arial`, que en Debian
  no existe: por eso la imagen instala `fonts-liberation` (equivalente metrico de Arial) y
  `fonts-noto-color-emoji` para los emojis de los overlays. Si alguna vez tocas la lista de
  paquetes, no saques las fuentes: Chrome renderiza el texto invisible sin avisar.
