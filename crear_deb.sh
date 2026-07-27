#!/bin/bash

# Pimiento Joe - Creador de Paquetes Debian Oficiales (.deb) en /opt
# Salir inmediatamente si ocurre un error
set -e

# Asegurarse de que la app ya está compilada
if [ ! -f "dist/pimiento" ]; then
    echo "❌ Error: Primero debes compilar la app ejecutable corriendo: ./compilar.sh"
    exit 1
fi

echo "📦 Creando estructura profesional .deb en /opt..."
DIR="pimiento_1.0-1_amd64"

# Limpiar restos anteriores
rm -rf "$DIR"
rm -f "pimiento_1.0-1_amd64.deb"

# Crear estructura estándar de directorios de instalación de Linux en /opt
mkdir -p "$DIR/DEBIAN"
mkdir -p "$DIR/opt/pimiento_joe"
mkdir -p "$DIR/usr/bin"
mkdir -p "$DIR/usr/share/applications"

# Copiar el ejecutable y el icono a /opt
cp dist/pimiento "$DIR/opt/pimiento_joe/pimiento"
cp img/pimentin.png "$DIR/opt/pimiento_joe/pimentin.png"

# Crear un enlace simbólico en /usr/bin apuntando a /opt
ln -s /opt/pimiento_joe/pimiento "$DIR/usr/bin/pimiento"

# Crear el archivo de metadatos de control de Debian
cat <<EOF > "$DIR/DEBIAN/control"
Package: pimiento
Version: 1.0-1
Section: utils
Priority: optional
Architecture: amd64
Maintainer: Felipe <felipe@ideacentre>
Description: Pimiento Joe - The Ultimate Bedtime Reader.
 Extract text from PDF, EPUB, and MOBI, and convert it to natural audio MP3.
EOF

# CREACIÓN DEL SCRIPT POSTRM DE DEBIAN (NUEVO: Limpieza absoluta de /opt al desinstalar)
cat <<EOF > "$DIR/DEBIAN/postrm"
#!/bin/sh
set -e
# Cuando el paquete se elimine o se purgue, borramos la carpeta /opt/pimiento_joe por completo
if [ "\$1" = "remove" ] || [ "\$1" = "purge" ]; then
    rm -rf /opt/pimiento_joe
fi
EOF
chmod +x "$DIR/DEBIAN/postrm" # Súper importante dar permisos al script interno

# Crear el acceso directo oficial del sistema apuntando a /opt
cat <<EOF > "$DIR/usr/share/applications/pimiento.desktop"
[Desktop Entry]
Type=Application
Name=Pimiento Joe
Exec=/opt/pimiento_joe/pimiento
Icon=/opt/pimiento_joe/pimentin.png
Terminal=false
StartupWMClass=pimiento
EOF

# Compilar el archivo .deb
echo "🛠️  Compilando paquete DEB oficial..."
dpkg-deb --build "$DIR"

# Limpiar directorio temporal
rm -rf "$DIR"

echo "--------------------------------------------------------"
echo "✨ ¡INSTALADOR DEBIAN (.deb) EN /opt LISTO! ✨"
echo "👉 Tu instalador oficial está en: pimiento_1.0-1_amd64.deb"
echo "--------------------------------------------------------"
