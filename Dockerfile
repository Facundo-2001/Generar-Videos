# Imagen del backend (api.py): Python para el pipeline + Node para Remotion +
# FFmpeg y las librerias de sistema que necesita el Chrome headless del render.
#
# Sirve tal cual en Railway, Render, Fly.io o cualquier VPS con Docker.
# NO sirve para Vercel: ahi solo va el front (carpeta web/), porque una funcion
# serverless no puede cargar Chromium ni guardar los archivos entre pedidos.

# Bookworm pinneado a proposito: en Debian trixie varios paquetes de Chrome
# cambiaron de nombre (libasound2 -> libasound2t64) y el build se rompe.
FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    NODE_VERSION=20 \
    REMOTION_DISABLE_HEADLESS_WARNING=1

# Node + FFmpeg + las librerias de Chrome Headless Shell.
#
# La lista de libs es la que publica Remotion para Debian. Las fuentes no son
# opcionales: sin ninguna fuente instalada, Chrome dibuja el texto invisible y
# NO tira error, asi que los subtitulos saldrian en blanco.
#   - fonts-liberation: Liberation Sans es el equivalente metrico de Arial, que
#     es la familia que piden los componentes de Remotion de este proyecto.
#   - fonts-dejavu-core: respaldo generico para sans-serif.
#   - fonts-noto-color-emoji: los overlays de los reels usan emojis
#     (🛒 📊 💰 🎨 📈 🚀 🌐 👇 💸); sin esta fuente salen como cuadraditos.
# ffmpeg lo necesita moviepy del lado de Python (mide la duracion de la voz).
RUN apt-get update && apt-get install -y --no-install-recommends \
      curl ca-certificates gnupg ffmpeg \
      libnss3 libdbus-1-3 libatk1.0-0 libgbm-dev libasound2 libxrandr2 \
      libxkbcommon-dev libxfixes3 libxcomposite1 libxdamage1 \
      libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 \
      fonts-liberation fonts-dejavu-core fonts-noto-color-emoji \
  && curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | bash - \
  && apt-get install -y --no-install-recommends nodejs \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Dependencias de Python primero, para aprovechar la cache de capas.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Dependencias de Remotion.
COPY remotion/package.json remotion/package-lock.json ./remotion/
RUN cd remotion && npm ci

# El codigo.
COPY videogen/ ./videogen/
COPY remotion/src/ ./remotion/src/
COPY remotion/remotion.config.ts remotion/tsconfig.json ./remotion/
COPY main.py asistente.py api.py ./

# Carpeta donde el pipeline deja los assets de cada proyecto.
RUN mkdir -p remotion/public/renders remotion/out

# Bajamos el Chrome Headless Shell en el build, no en el primer render:
# si no, el primer video tarda varios minutos de mas.
RUN cd remotion && npx remotion browser ensure

EXPOSE 8000
CMD ["python", "api.py"]
