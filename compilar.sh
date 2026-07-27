#!/bin/bash

# Pimiento Joe - Compilador Automático y Setup de Desarrollo (100% Offline Multi-idioma)
# Abortar inmediatamente si ocurre algún error inesperado
set -e

echo "🌶️  Iniciando Setup de Desarrollo y Compilación de PIMIENTO JOE..."

# 1. Verificar si Python 3 está instalado en el sistema
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 no está instalado en este sistema."
    echo "Por favor, ejecute: sudo apt update && sudo apt install python3 -y"
    exit 1
fi

# 2. Crear el entorno virtual de Python (env) si no existe
if [ ! -d "env" ]; then
    echo "📦 Creando un entorno virtual fresco 'env'..."
    if ! python3 -m venv env 2>/dev/null; then
        echo "❌ Error: Falta el paquete 'python3-venv' de Linux."
        echo "Por favor, ejecute: sudo apt update && sudo apt install python3-venv python3-full -y"
        echo "Y vuelva a lanzar este script."
        exit 1
    fi
    echo "✅ Entorno virtual 'env' creado con éxito."
else
    echo "✅ Entorno virtual 'env' detectado."
fi

# 3. Descargar el motor neuronal Piper TTS, las voces locales y LAME (Sugerencia 1 y 2)
if [ ! -d "bin/piper" ]; then
    echo "📥 Descargando motor de voz offline Piper TTS..."
    mkdir -p bin/piper
    
    # Descargar binario portable de Piper Linux x86_64
    wget -q --show-progress -O /tmp/piper.tar.gz "https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_x86_64.tar.gz"
    tar -xzf /tmp/piper.tar.gz -C bin/
    rm -f /tmp/piper.tar.gz
    
    echo "📥 Descargando modelo de voz neuronal en español (es_ES-davefx-medium) 🇪🇸..."
    wget -q --show-progress -O bin/piper/es_ES-davefx-medium.onnx "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/es/es_ES/davefx/medium/es_ES-davefx-medium.onnx?download=true"
    wget -q --show-progress -O bin/piper/es_ES-davefx-medium.onnx.json "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/es/es_ES/davefx/medium/es_ES-davefx-medium.onnx.json?download=true"

    echo "📥 Descargando modelo de voz neuronal en inglés (en_US-amy-medium) 🇺🇸..."
    wget -q --show-progress -O bin/piper/en_US-amy-medium.onnx "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/amy/medium/en_US-amy-medium.onnx?download=true"
    wget -q --show-progress -O bin/piper/en_US-amy-medium.onnx.json "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/amy/medium/en_US-amy-medium.onnx.json?download=true"

    echo "📥 Descargando modelo de voz neuronal en chino (zh_CN-huayan-medium) 🇨🇳..."
    wget -q --show-progress -O bin/piper/zh_CN-huayan-medium.onnx "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/zh/zh_CN/huayan/medium/zh_CN-huayan-medium.onnx?download=true"
    wget -q --show-progress -O bin/piper/zh_CN-huayan-medium.onnx.json "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/zh/zh_CN/huayan/medium/zh_CN-huayan-medium.onnx.json?download=true"

    echo "📥 Extrayendo decodificador de MP3 LAME..."
    # Intentamos descargar el paquete lame de ubuntu de forma segura sin instalarlo en tu PC
    apt-get download lame &>/dev/null || wget -q -O /tmp/lame.deb "http://archive.ubuntu.com/ubuntu/pool/universe/l/lame/lame_3.100-3_amd64.deb"
    mkdir -p /tmp/lame_ext
    dpkg-deb -x *.deb /tmp/lame_ext 2>/dev/null || dpkg-deb -x /tmp/lame.deb /tmp/lame_ext
    cp /tmp/lame_ext/usr/bin/lame bin/piper/lame
    rm -rf /tmp/lame_ext /tmp/lame.deb *.deb
    chmod +x bin/piper/lame

    echo "✅ Motor offline, voces y decodificador LAME listos en bin/piper/."
fi

# 4. Activar el entorno virtual seguro
echo "🔌 Activando entorno virtual seguro..."
source env/bin/activate

# 5. Actualizar el gestor de paquetes PIP
echo "🔄 Actualizando PIP..."
pip install --upgrade pip

# 6. Instalar todas las dependencias
if [ -f "requirements.txt" ]; then
    echo "📥 Instalando librerías y herramientas de compilación desde requirements.txt..."
    pip install -r requirements.txt
else
    echo "❌ Error crítico: No se encontró el archivo 'requirements.txt'."
    exit 1
fi

# 7. Compilar Pimiento Joe (Empaquetamos la carpeta de Piper, voces y LAME dentro de la app)
echo "🚀 Compilando ejecutable portable de PIMIENTO JOE OFFLINE..."
pyinstaller --onefile --windowed \
    --add-data "img/pimentin.png:img" \
    --add-data "bin/piper:bin/piper" \
    --icon="img/pimentin.png" \
    pimiento.py

# 8. Empaquetar la release de Jose Luis (Compresión limpia del binario portable)
echo "📦 Creando el archivo portable comprimido para compartir..."
tar -czf PimientoJoe_portable.tar.gz -C dist pimiento

echo "--------------------------------------------------------"
echo "✨ ¡PROCESO COMPLETADO CON ÉXITO! ✨"
echo "👉 Tu app de desarrollo ha sido compilada."
echo "👉 La versión portable para compartir está lista en: PimientoJoe_portable.tar.gz"
echo "--------------------------------------------------------"