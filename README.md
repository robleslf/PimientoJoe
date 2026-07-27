<p align="center">
  <img src="img/pimentin.png" alt="Pimiento Joe Logo" width="130">
</p>

<h1 align="center">🌶️ PIMIENTO JOE</h1>

<p align="center">
  <strong>The Ultimate Bedtime Reader</strong>
</p>

---

## 📖 ¿Qué es Pimiento Joe?

**Pimiento Joe** es una aplicación de escritorio **para Linux**

Su objetivo es convertir fragmentos concretos de tus libros digitales (**PDF**, **EPUB** y **MOBI**) en archivos de audio **MP3** utilizando voces neuronales premium con una calidad extremadamente natural.

Ideal para escuchar capítulos o párrafos antes de dormir, descansar la vista y disfrutar de tus libros sin necesidad de mirar una pantalla.

---

# 🚀 Instalación para Usuarios

Si únicamente quieres utilizar la aplicación, descarga la última versión desde la sección de **Releases** de este repositorio.

## Opción A — Instalador `.deb` (Recomendado)

Compatible con:

- Ubuntu
- Debian
- Linux Mint
- Derivadas

Esta opción instala la aplicación en:

```text
/opt/pimiento_joe/
```

y crea automáticamente un acceso directo en el menú de aplicaciones.

### 1. Descarga

```
pimiento_1.0-1_amd64.deb
```

### 2. Instala

Puedes hacerlo con doble clic o desde la terminal:

```bash
sudo apt install ./pimiento_1.0-1_amd64.deb
```

### 3. Ejecuta

Busca **Pimiento Joe** en el menú de aplicaciones y ejecútalo.

> 💡 Puedes anclarlo al Dock o a Favoritos como cualquier otra aplicación.

---

## Opción B — Versión Portable

Perfecta para:

- Pendrives USB
- No modificar el sistema
- Llevar la aplicación a cualquier equipo

### 1. Descarga

```
PimientoJoe_portable.tar.gz
```

### 2. Extrae el contenido

```bash
tar -xzf PimientoJoe_portable.tar.gz
```

### 3. Ejecuta

Haz doble clic sobre:

```
PimientoJoe.desktop
```

La primera vez que se abra registrará automáticamente su icono de **Pimentín Vaquero** en el sistema.

---

# 🛠️ Guía para Desarrolladores

El proyecto está organizado siguiendo un diseño modular que separa claramente la interfaz gráfica de la lógica de negocio.

## Estructura

```text
PimientoJoe/
│
├── pimiento.py          # Interfaz gráfica (PyQt6)
├── lector.py            # Extracción de texto + generación MP3
├── requirements.txt     # Dependencias
├── compilar.sh          # Compilación automática
├── crear_deb.sh         # Generador del paquete .deb
├── desinstalar.sh       # Limpieza completa
└── README.md
```

---

# ⚙️ Compilar desde el código fuente

## 1. Clonar el repositorio

```bash
git clone https://github.com/robleslf/PimientoJoe.git

cd PimientoJoe
```

---

## 2. Dar permisos de ejecución

```bash
chmod +x compilar.sh crear_deb.sh desinstalar.sh
```

---

## 3. Compilar

```bash
./compilar.sh
```

El script realiza automáticamente:

- Creación del entorno virtual
- Actualización de `pip`
- Instalación de todas las dependencias
- Instalación de PyInstaller
- Compilación del ejecutable
- Generación del paquete portable

Al finalizar obtendrás:

```text
PimientoJoe_portable.tar.gz
```

---

## 4. Crear el paquete `.deb`

Opcionalmente puedes generar el instalador oficial para Debian/Ubuntu:

```bash
./crear_deb.sh
```

---

# 🧹 Desinstalación y limpieza

Para eliminar completamente todos los archivos generados durante el desarrollo:

```bash
./desinstalar.sh
```

Este script elimina automáticamente:

- Paquete `.deb`
- Carpeta `/opt/pimiento_joe`
- Acceso directo del sistema
- Iconos instalados
- Archivos temporales

Dejando el sistema completamente limpio.

---

# 📦 Tecnologías utilizadas

- Python 3
- PyQt6
- PyInstaller
- EbookLib
- PyMuPDF
- gTTS / Motor TTS neuronal
- Bash

---


# 📄 Licencia

Este proyecto se distribuye bajo la licencia que figura en este repositorio.

---

<p align="center">
🌶️ 
</p>
