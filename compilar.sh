#!/bin/bash

# Pimiento Joe - Compilador Automático y Setup de Desarrollo
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

# 3. Activar el entorno virtual seguro
echo "🔌 Activando entorno virtual seguro..."
source env/bin/activate

# 4. Actualizar el gestor de paquetes PIP
echo "🔄 Actualizando PIP..."
pip install --upgrade pip

# 5. Instalar todas las dependencias
if [ -f "requirements.txt" ]; then
    echo "📥 Instalando librerías y herramientas de compilación desde requirements.txt..."
    pip install -r requirements.txt
else
    echo "❌ Error crítico: No se encontró el archivo 'requirements.txt'."
    exit 1
fi

# 6. Compilar Pimiento Joe en un binario portable único
echo "🚀 Compilando ejecutable portable de PIMIENTO JOE..."
pyinstaller --onefile --windowed --add-data "img/pimentin.png:img" --icon="img/pimentin.png" pimiento.py

# 7. NUEVO: Empaquetar la release de Jose Luis en un .tar.gz que sí mantiene los permisos de Linux (Sugerencia 3)
echo "📦 Creando el archivo portable comprimido para Jose Luis..."
tar -czf PimientoJoe_portable.tar.gz -C dist pimiento PimientoJoe.desktop

echo "--------------------------------------------------------"
echo "✨ ¡PROCESO COMPLETADO CON ÉXITO! ✨"
echo "👉 Tu app de desarrollo ha sido compilada."
echo "👉 El instalador para Jose Luis está en: PimientoJoe_portable.tar.gz"
echo "--------------------------------------------------------"
