#!/bin/bash

# Pimiento Joe - Desinstalador Limpio
echo "🧹 Iniciando desinstalación completa de PIMIENTO JOE..."

# 1. Si se instaló como paquete oficial .deb, lo eliminamos con el sistema apt
if dpkg -s pimiento &>/dev/null; then
    echo "📦 Detectada instalación oficial por paquete .deb. Procediendo a eliminar..."
    sudo apt remove pimiento -y
fi

# 2. Borrar la carpeta de la app en /opt (si quedó algún residuo)
if [ -d "/opt/pimiento_joe" ]; then
    echo "🧹 Eliminando directorio de instalación en /opt..."
    sudo rm -rf "/opt/pimiento_joe"
fi

# 3. Eliminar el enlace simbólico
if [ -f "/usr/bin/pimiento" ]; then
    sudo rm -f "/usr/bin/pimiento"
fi

# 4. Borrar rastros del auto-registro local de usuario
echo "🧹 Eliminando iconos guardados en el sistema del usuario..."
rm -f "$HOME/.local/share/icons/pimentin_app.png"

echo "🧹 Eliminando accesos directos registrados en el menú de aplicaciones..."
rm -f "$HOME/.local/share/applications/pimiento.desktop"

# 5. Eliminar accesos directos locales de la release portable (si existen)
rm -f "PimientoJoe.desktop"
rm -f "dist/PimientoJoe.desktop"
rm -f "PimientoJoe_portable.tar.gz"

echo "--------------------------------------------------------"
echo "✨ ¡PIMIENTO JOE HA SIDO ELIMINADO POR COMPLETO! ✨"
echo "--------------------------------------------------------"
