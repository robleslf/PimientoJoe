import sys
import os
import re
import asyncio
import threading
import subprocess  # Para inyectar comandos de sistema de forma segura
import fitz  # PyMuPDF
import edge_tts
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QPushButton, QLabel, QFileDialog, QFrame, 
                             QStackedWidget, QHBoxLayout, QSpinBox, QMessageBox,
                             QLineEdit, QTextEdit, QComboBox, QSlider)
from PyQt6.QtGui import QPixmap, QIcon, QImage, QPainter
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QSize

# IMPORTAMOS NUESTRO BACKEND
import lector

# Colores noventeros
DARK_BG = "#1e1e24"
NEON_GREEN = "#39FF14"
DEEP_PURPLE = "#5b2c6f"
ORANGE_ACCENT = "#ff5733"
BLOOD_RED = "#d90429"

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

RUTA_ICONO = resource_path("img/pimentin.png")

# --- LÓGICA DE AUTO-REGISTRO PORTABLE CON MAGIA DE CONFIANZA (NUEVO) ---
def auto_registrar_desktop_linux():
    """ Registra el icono y fuerza a Linux a confiar en los lanzadores automáticamente """
    if getattr(sys, 'frozen', False):
        try:
            executable_path = os.path.abspath(sys.executable)
            
            # 1. Guardar el icono en el sistema local
            dest_icon_dir = os.path.expanduser("~/.local/share/icons")
            os.makedirs(dest_icon_dir, exist_ok=True)
            dest_icon_path = os.path.join(dest_icon_dir, "pimentin_app.png")
            
            if os.path.exists(RUTA_ICONO):
                import shutil
                shutil.copy(RUTA_ICONO, dest_icon_path)
                
            # Lanzador del sistema local
            desktop_dir = os.path.expanduser("~/.local/share/applications")
            os.makedirs(desktop_dir, exist_ok=True)
            desktop_file_path = os.path.join(desktop_dir, "pimiento.desktop")
            
            # Lanzador local portátil (el que verá Jose Luis al lado de la app)
            local_desktop_path = os.path.join(os.path.dirname(executable_path), "PimientoJoe.desktop")

            # Escribimos y damos permisos a ambos
            for path in [desktop_file_path, local_desktop_path]:
                with open(path, "w") as f:
                    f.write(f"""[Desktop Entry]
Type=Application
Name=Pimiento Joe
Exec="{executable_path}"
Icon={dest_icon_path}
Terminal=false
StartupWMClass=pimiento
""")
                # Permiso de ejecución de archivo en Linux (+x)
                os.chmod(path, 0o755)
                
                # INYECTAR CONFIANZA SILENCIOSA EN LINUX (NUEVO - EVITA CLIC DERECHO DEL AMIGO)
                # Ejecutamos ambos parámetros para asegurar compatibilidad con versiones antiguas y modernas de Ubuntu
                try:
                    subprocess.run(["gio", "set", path, "metadata::trusted", "yes"], capture_output=True)
                    subprocess.run(["gio", "set", path, "metadata::trusted", "true"], capture_output=True)
                except Exception:
                    pass

        except Exception:
            pass

class AvisadorAudio(QObject):
    finalizado = pyqtSignal(str)
    error = pyqtSignal(str)

class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(500, 400)

        layout = QVBoxLayout()
        self.setLayout(layout)

        frame = QFrame()
        frame.setStyleSheet(f"QFrame {{ background-color: {DARK_BG}; border: 4px solid {NEON_GREEN}; border-radius: 15px; }}")
        frame_layout = QVBoxLayout(frame)

        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if os.path.exists(RUTA_ICONO):
            pixmap = QPixmap(RUTA_ICONO).scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.logo_label.setPixmap(pixmap)
        
        title = QLabel("PIMIENTO JOE")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"QLabel {{ font-family: 'Impact'; font-size: 45px; color: {NEON_GREEN}; }}")
        
        subtitle = QLabel("THE ULTIMATE BEDTIME READER")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(f"QLabel {{ font-family: 'Courier New'; font-size: 14px; font-weight: bold; color: {ORANGE_ACCENT}; }}")

        frame_layout.addWidget(self.logo_label)
        frame_layout.addWidget(title)
        frame_layout.addWidget(subtitle)
        layout.addWidget(frame)

class WelcomeWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("WelcomeWidget")
        
    def paintEvent(self, event):
        super().paintEvent(event)
        if os.path.exists(RUTA_ICONO):
            painter = QPainter(self)
            painter.setOpacity(0.06) 
            
            pixmap = QPixmap(RUTA_ICONO)
            ancho_marca = 320 
            pix_scaled = pixmap.scaledToWidth(ancho_marca, Qt.TransformationMode.SmoothTransformation)
            
            x = self.width() - pix_scaled.width() - 15
            y = self.height() - pix_scaled.height() - 15
            
            painter.drawPixmap(x, y, pix_scaled)
            painter.end()

class PimientoJoeApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pimiento Joe - Lector Multiformato")
        
        self.STYLE_BIENVENIDA_NORMAL = f"""
            QFrame#WelcomeWidget {{
                border: 3px dashed {NEON_GREEN};
                border-radius: 12px;
                background-color: #23232a;
            }}
        """
        self.STYLE_BIENVENIDA_DRAG = f"""
            QFrame#WelcomeWidget {{
                border: 3px solid {NEON_GREEN};
                border-radius: 12px;
                background-color: {DEEP_PURPLE};
            }}
        """

        self.voces_map = {
            "🇪🇸 Español (España) - Elvira": "es-ES-ElviraNeural",
            "🇲🇽 Español (México) - Dalia": "es-MX-DaliaNeural",
            "🇨🇳 Chino (Mandarín) - Xiaoxiao": "zh-CN-XiaoxiaoNeural",
            "🇺🇸 Inglés (EE.UU.) - Aria": "en-US-AriaNeural",
            "🇬🇧 Inglés (R.Unido) - Sonia": "en-GB-SoniaNeural",
            "🇫🇷 Francés - Denise": "fr-FR-DeniseNeural",
            "🇩🇪 Alemán - Amala": "de-DE-AmalaNeural",
            "🇮🇹 Italiano - Elsa": "it-IT-ElsaNeural"
        }

        self.velocidad_map = {
            "🐢 Muy Despacio (Nivel 1)": "-30%",
            "🚶 Despacio (Nivel 2)": "-15%",
            "🏠 Normal (Nivel 3)": "+0%",
            "⚡ Rápido (Nivel 4)": "+15%",
            "🚀 Muy Rápido (Nivel 5)": "+30%"
        }

        self.setAcceptDrops(True)
        
        if os.path.exists(RUTA_ICONO):
            self.setWindowIcon(QIcon(RUTA_ICONO))

        self.setStyleSheet(f"""
            QMainWindow {{ background-color: {DARK_BG}; }}
            QLabel {{ color: white; font-size: 14px; font-weight: bold; }}
            QPushButton {{
                background-color: {DEEP_PURPLE}; color: {NEON_GREEN};
                font-family: 'Impact'; font-size: 18px;
                border: 2px solid {NEON_GREEN}; border-radius: 8px; padding: 10px;
            }}
            QPushButton:hover {{ background-color: {NEON_GREEN}; color: {DARK_BG}; }}
            QSpinBox {{
                background-color: {DARK_BG}; color: {NEON_GREEN};
                font-size: 16px; border: 2px solid {NEON_GREEN}; padding: 5px;
            }}
            QLineEdit {{
                background-color: #2b2b36; color: white;
                font-size: 14px; border: 1px solid {NEON_GREEN}; border-radius: 4px;
                padding: 6px;
            }}
            QTextEdit {{
                background-color: #151518; color: #e0e0e0;
                font-family: 'monospace', 'Courier New'; font-size: 13px;
                border: 2px solid {DEEP_PURPLE}; border-radius: 8px;
                padding: 10px;
            }}
            QComboBox {{
                background-color: #2b2b36; color: {NEON_GREEN};
                border: 2px solid {NEON_GREEN}; border-radius: 4px;
                padding: 5px; font-weight: bold; font-size: 14px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {DARK_BG}; color: {NEON_GREEN};
                selection-background-color: {DEEP_PURPLE};
            }}
            QSlider::groove:horizontal {{
                border: 1px solid {NEON_GREEN};
                height: 6px;
                background: #151518;
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {ORANGE_ACCENT};
                border: 1px solid white;
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {NEON_GREEN};
            }}
        """)
        
        self.ruta_archivo = None
        self.doc = None  
        self.pagina_actual = 0
        self.total_paginas = 0
        
        # CONFIGURACIÓN DEL ANIMADOR ESPACIAL CON TEXTO DE TIEMPO
        self.timer_espacial = QTimer()
        self.timer_espacial.timeout.connect(self.actualizar_animacion_espacial)
        self.contador_frame = 0
        self.frames_espacio = [
            "⚡ Conectando con el espacio exterior (Edge TTS)... (esto puede llevar un tiempo) 🛸      ",
            "⚡ Conectando con el espacio exterior (Edge TTS)... (esto puede llevar un tiempo)  🛸     ",
            "⚡ Conectando con el espacio exterior (Edge TTS)... (esto puede llevar un tiempo)   🛸    ",
            "⚡ Conectando con el espacio exterior (Edge TTS)... (esto puede llevar un tiempo)    🛸   ",
            "⚡ Conectando con el espacio exterior (Edge TTS)... (esto puede llevar un tiempo)     🛸  ",
            "⚡ Conectando con el espacio exterior (Edge TTS)... (esto puede llevar un tiempo)      🛸 ",
            "⚡ Conectando con el espacio exterior (Edge TTS)... (esto puede llevar un tiempo)       🛸",
            "⚡ Conectando con el espacio exterior (Edge TTS)... (esto puede llevar un tiempo)      👾 ",
            "⚡ Conectando con el espacio exterior (Edge TTS)... (esto puede llevar un tiempo)     👾  ",
            "⚡ Conectando con el espacio exterior (Edge TTS)... (esto puede llevar un tiempo)    👾   ",
            "⚡ Conectando con el espacio exterior (Edge TTS)... (esto puede llevar un tiempo)   👾    ",
            "⚡ Conectando con el espacio exterior (Edge TTS)... (esto puede llevar un tiempo)  👾     ",
            "⚡ Conectando con el espacio exterior (Edge TTS)... (esto puede llevar un tiempo) 👾      "
        ]
        
        self.avisador = AvisadorAudio()
        self.avisador.finalizado.connect(self.audio_completado)
        self.avisador.error.connect(self.audio_error)

        self.init_ui()
        self.ajustar_tamano_pantalla()

    def ajustar_tamano_pantalla(self):
        pantalla = self.screen().availableGeometry()
        ancho_pantalla = pantalla.width()
        alto_pantalla = pantalla.height()

        ancho_ideal = min(1100, int(ancho_pantalla * 0.90))
        alto_ideal = min(850, int(alto_pantalla * 0.85))

        self.resize(ancho_ideal, alto_ideal)

        x = pantalla.left() + int((ancho_pantalla - ancho_ideal) / 2)
        y = pantalla.top() + int((alto_pantalla - alto_ideal) / 2)
        self.move(x, y)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.btn_cargar = QPushButton("⚡ CARGAR LIBRO ⚡")
        self.btn_cargar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cargar.clicked.connect(self.cargar_archivo_dialogo)
        main_layout.addWidget(self.btn_cargar)

        info_archivo_layout = QHBoxLayout()
        self.lbl_archivo = QLabel("Ningún libro seleccionado...")
        self.lbl_archivo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_archivo.setStyleSheet(f"color: {ORANGE_ACCENT}; font-style: italic;")
        info_archivo_layout.addWidget(self.lbl_archivo, stretch=1)
        
        self.btn_cerrar_libro = QPushButton("❌ CERRAR LIBRO")
        self.btn_cerrar_libro.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cerrar_libro.setStyleSheet(f"QPushButton {{ background-color: {DARK_BG}; color: {BLOOD_RED}; border: 1px dashed {BLOOD_RED}; font-size: 11px; padding: 4px 8px; }} QPushButton:hover {{ background-color: {BLOOD_RED}; color: white; }}")
        self.btn_cerrar_libro.clicked.connect(self.cerrar_libro_actual)
        self.btn_cerrar_libro.hide() 
        info_archivo_layout.addWidget(self.btn_cerrar_libro)
        
        main_layout.addLayout(info_archivo_layout)

        # --- CONTENEDOR DEL VISOR (PANTALLA DIVIDIDA) ---
        self.visor_widget = QWidget()
        visor_layout = QVBoxLayout(self.visor_widget)
        
        split_layout = QHBoxLayout()
        
        self.lbl_pagina_img = QLabel("Cargando...")
        self.lbl_pagina_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_pagina_img.setStyleSheet("border: 2px dashed #555; background-color: #2b2b36; border-radius: 8px;")
        self.lbl_pagina_img.setMinimumHeight(400)
        split_layout.addWidget(self.lbl_pagina_img, stretch=1)

        derecha_widget = QWidget()
        derecha_layout = QVBoxLayout(derecha_widget)
        derecha_layout.setContentsMargins(0, 0, 0, 0)
        
        self.acciones_sel_layout = QHBoxLayout()
        self.btn_sel_inicio = QPushButton("✂️ USAR COMO INICIO")
        self.btn_sel_inicio.setEnabled(False) 
        self.btn_sel_inicio.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_sel_inicio.clicked.connect(self.aplicar_seleccion_inicio)
        
        self.btn_sel_fin = QPushButton("✂️ USAR COMO FIN")
        self.btn_sel_fin.setEnabled(False) 
        self.btn_sel_fin.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_sel_fin.clicked.connect(self.aplicar_seleccion_fin)
        
        self.acciones_sel_layout.addWidget(self.btn_sel_inicio)
        self.acciones_sel_layout.addWidget(self.btn_sel_fin)
        derecha_layout.addLayout(self.acciones_sel_layout)
        
        self.txt_pagina_text = QTextEdit()
        self.txt_pagina_text.setReadOnly(True)
        self.txt_pagina_text.setPlaceholderText("El texto seleccionable aparecerá aquí...")
        self.txt_pagina_text.selectionChanged.connect(self.comprobar_seleccion_texto)
        derecha_layout.addWidget(self.txt_pagina_text)
        
        split_layout.addWidget(derecha_widget, stretch=1)
        visor_layout.addLayout(split_layout, stretch=1)

        # Controles navegación
        nav_layout = QHBoxLayout()
        self.btn_prev = QPushButton("◀ ANTERIOR")
        self.btn_prev.clicked.connect(self.pagina_anterior)
        
        self.lbl_contador_pag = QLabel("Página: 0 / 0")
        self.lbl_contador_pag.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.btn_next = QPushButton("SIGUIENTE ▶")
        self.btn_next.clicked.connect(self.pagina_siguiente)
        
        nav_layout.addWidget(self.btn_prev)
        nav_layout.addWidget(self.lbl_contador_pag)
        nav_layout.addWidget(self.btn_next)
        visor_layout.addLayout(nav_layout)

        # Barra de Deslizamiento Rápido de Página
        slider_layout = QHBoxLayout()
        slider_layout.addWidget(QLabel("🧭 Navegación rápida:"))
        self.slider_paginas = QSlider(Qt.Orientation.Horizontal)
        self.slider_paginas.setMinimum(1)
        self.slider_paginas.valueChanged.connect(self.ir_a_pagina_slider)
        slider_layout.addWidget(self.slider_paginas, stretch=1)
        
        self.lbl_slider_contador = QLabel("0 / 0")
        self.lbl_slider_contador.setStyleSheet(f"color: {NEON_GREEN}; font-size: 14px;")
        slider_layout.addWidget(self.lbl_slider_contador)
        visor_layout.addLayout(slider_layout)

        # Controles selección numérica
        selec_layout = QHBoxLayout()
        selec_layout.addWidget(QLabel("Generar desde pág:"))
        self.spin_n1 = QSpinBox()
        self.spin_n1.setMinimum(1)
        selec_layout.addWidget(self.spin_n1)
        
        self.btn_fijar_inicio = QPushButton("👈 PÁG. INICIO")
        self.btn_fijar_inicio.setStyleSheet(f"QPushButton {{ background-color: {DARK_BG}; color: {ORANGE_ACCENT}; border: 2px dashed {ORANGE_ACCENT}; font-size: 13px; padding: 4px 8px; }} QPushButton:hover {{ background-color: {ORANGE_ACCENT}; color: {DARK_BG}; }}")
        self.btn_fijar_inicio.clicked.connect(self.fijar_inicio)
        selec_layout.addWidget(self.btn_fijar_inicio)
        
        selec_layout.addWidget(QLabel("   hasta pág:"))
        self.spin_n2 = QSpinBox()
        self.spin_n2.setMinimum(1)
        selec_layout.addWidget(self.spin_n2)
        
        self.btn_fijar_fin = QPushButton("👈 PÁG. FIN")
        self.btn_fijar_fin.setStyleSheet(f"QPushButton {{ background-color: {DARK_BG}; color: {ORANGE_ACCENT}; border: 2px dashed {ORANGE_ACCENT}; font-size: 13px; padding: 4px 8px; }} QPushButton:hover {{ background-color: {ORANGE_ACCENT}; color: {DARK_BG}; }}")
        self.btn_fijar_fin.clicked.connect(self.fijar_fin)
        selec_layout.addWidget(self.btn_fijar_fin)
        
        visor_layout.addLayout(selec_layout)

        # Configuración de Voz y Velocidad
        idioma_layout = QHBoxLayout()
        idioma_layout.addWidget(QLabel("🗣️ Voz:"))
        self.combo_idioma = QComboBox()
        self.combo_idioma.addItems(self.voces_map.keys())
        idioma_layout.addWidget(self.combo_idioma)

        idioma_layout.addWidget(QLabel("  ⏱️ Velocidad:"))
        self.combo_velocidad = QComboBox()
        self.combo_velocidad.addItems(self.velocidad_map.keys())
        self.combo_velocidad.setCurrentIndex(2) 
        idioma_layout.addWidget(self.combo_velocidad)
        visor_layout.addLayout(idioma_layout)

        # Controles para Recorte Inteligente
        recorte_layout = QHBoxLayout()
        recorte_layout.addWidget(QLabel("✂️ Recortar texto desde (opcional):"))
        self.txt_recorte_inicio = QLineEdit()
        self.txt_recorte_inicio.setPlaceholderText("Selecciona texto arriba y clica en usar como inicio...")
        self.txt_recorte_inicio.textChanged.connect(self.auto_fijar_pagina_inicio)
        recorte_layout.addWidget(self.txt_recorte_inicio)

        recorte_layout.addWidget(QLabel(" hasta:"))
        self.txt_recorte_fin = QLineEdit()
        self.txt_recorte_fin.setPlaceholderText("Selecciona texto arriba y clica en usar como fin...")
        self.txt_recorte_fin.textChanged.connect(self.auto_fijar_pagina_fin)
        recorte_layout.addWidget(self.txt_recorte_fin)
        visor_layout.addLayout(recorte_layout)
        
        # --- PANTALLA DE BIENVENIDA CON MARCA DE AGUA EXCLUSIVA ---
        self.placeholder_widget = WelcomeWidget() 
        self.placeholder_widget.setStyleSheet(self.STYLE_BIENVENIDA_NORMAL)
        
        place_layout = QVBoxLayout(self.placeholder_widget)
        place_layout.setAlignment(Qt.AlignmentFlag.AlignCenter) 
        
        # Texto limpio sin el cartel de AZW3
        self.lbl_bienvenida = QLabel(
            "💡 Haz clic en 'Cargar Libro' arriba\n"
            "O ARRASTRA TU ARCHIVO DIRECTAMENTE AQUÍ PARA EMPEZAR\n\n"
            "Soporta: PDF, EPUB y MOBI"
        )
        self.lbl_bienvenida.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_bienvenida.setStyleSheet("""
            QLabel {
                color: #e0e0e0;
                font-family: 'Impact', 'Courier New';
                font-size: 18px;
                background-color: transparent;
                border: none;
            }
        """)
        place_layout.addWidget(self.lbl_bienvenida)
        
        self.visor_stack = QStackedWidget()
        self.visor_stack.addWidget(self.placeholder_widget) 
        self.visor_stack.addWidget(self.visor_widget)       
        
        main_layout.addWidget(self.visor_stack, stretch=1)

        # Estado de la generación de audio (Soportará animación)
        self.lbl_estado = QLabel("")
        self.lbl_estado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_estado.setStyleSheet(f"color: {NEON_GREEN}; font-size: 16px; font-weight: bold;")
        main_layout.addWidget(self.lbl_estado)

        # Botón de Generar
        self.btn_generar = QPushButton("🎧 GENERAR AUDIO MP3 🎧")
        self.btn_generar.setStyleSheet(f"QPushButton {{ background-color: {ORANGE_ACCENT}; color: white; border: 2px solid white; font-size: 20px; }} QPushButton:hover {{ background-color: #ff3300; }}")
        self.btn_generar.hide()
        self.btn_generar.clicked.connect(self.iniciar_generacion_audio)
        main_layout.addWidget(self.btn_generar)

        # Botón Salir
        self.btn_salir = QPushButton("❌ SALIR DE PIMIENTO JOE ❌")
        self.btn_salir.setStyleSheet(f"QPushButton {{ background-color: {BLOOD_RED}; color: white; border: 2px solid white; }} QPushButton:hover {{ background-color: #ff0000; }}")
        self.btn_salir.clicked.connect(self.close)
        main_layout.addWidget(self.btn_salir)

        self.comprobar_seleccion_texto()

    # --- LÓGICA DE ARRASTRAR Y SOLTAR ---
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            ruta = event.mimeData().urls()[0].toLocalFile()
            if ruta.lower().endswith(('.pdf', '.epub', '.mobi')):
                event.acceptProposedAction()
                self.placeholder_widget.setStyleSheet(self.STYLE_BIENVENIDA_DRAG)
                
    def dragLeaveEvent(self, event):
        self.placeholder_widget.setStyleSheet(self.STYLE_BIENVENIDA_NORMAL)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            ruta = event.mimeData().urls()[0].toLocalFile()
            self.cargar_libro_desde_ruta(ruta)
            event.acceptProposedAction()

    # --- LÓGICA DE CARGA CENTRALIZADA ---
    def cargar_archivo_dialogo(self):
        filtros = "Libros soportados (*.pdf *.epub *.mobi);;Archivos de Amazon (*.azw3 *.azw)"
        archivo, _ = QFileDialog.getOpenFileName(self, "Selecciona un libro para Pimiento Joe", "", filtros)
        if archivo:
            self.cargar_libro_desde_ruta(archivo)

    def cargar_libro_desde_ruta(self, ruta):
        if ruta.lower().endswith(('.azw', '.azw3')):
            QMessageBox.information(
                self,
                "Información de Amazon AZW",
                "Los archivos .azw y .azw3 de Amazon suelen venir protegidos con DRM (bloqueo de copia).\n\n"
                "Para leerlos en Pimiento Joe, te recomiendo abrirlos un segundo en Calibre y convertirlos a EPUB o MOBI. "
                "¡Es súper rápido y Pimiento Joe los leerá de maravilla!"
            )
            return  

        self.ruta_archivo = ruta
        nombre = os.path.basename(ruta)
        self.lbl_archivo.setText(f"Libro cargado: {nombre}")
        
        try:
            self.doc, self.total_paginas = lector.abrir_documento(ruta)
            self.pagina_actual = 0
            
            self.spin_n1.setMaximum(self.total_paginas)
            self.spin_n2.setMaximum(self.total_paginas)
            self.spin_n1.setValue(1)
            self.spin_n2.setValue(1)
            
            # Seteamos el rango del Slider al cargar el libro
            self.slider_paginas.setMaximum(self.total_paginas)
            self.slider_paginas.setValue(1)

            self.mostrar_pagina()
            
            self.visor_stack.setCurrentIndex(1)
            self.btn_generar.show()
            self.btn_cerrar_libro.show() 
            
        except Exception as e:
            QMessageBox.critical(self, "Error de formato", f"No se pudo abrir el archivo:\n{str(e)}")
            self.lbl_archivo.setText("Error al cargar el libro.")
            self.visor_stack.setCurrentIndex(0)
            self.btn_cerrar_libro.hide()

    def cerrar_libro_actual(self):
        self.doc = None
        self.ruta_archivo = None
        self.lbl_archivo.setText("Ningún libro seleccionado...")
        self.txt_recorte_inicio.clear()
        self.txt_recorte_fin.clear()
        self.btn_generar.hide()
        self.btn_cerrar_libro.hide()
        self.placeholder_widget.setStyleSheet(self.STYLE_BIENVENIDA_NORMAL)
        self.visor_stack.setCurrentIndex(0) 

    def mostrar_pagina(self):
        if not self.doc: return
        pagina = self.doc.load_page(self.pagina_actual)
        
        pix = pagina.get_pixmap()
        formato = QImage.Format.Format_RGB888
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, formato)
        pixmap = QPixmap.fromImage(img)
        self.lbl_pagina_img.setPixmap(pixmap.scaled(self.lbl_pagina_img.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        
        texto_pagina = pagina.get_text()
        self.txt_pagina_text.setText(texto_pagina)
        
        # Sincronizamos textos de los contadores
        self.lbl_contador_pag.setText(f"Página: {self.pagina_actual + 1} / {self.total_paginas}")
        self.lbl_slider_contador.setText(f"{self.pagina_actual + 1} / {self.total_paginas}")
        
        # Sincronizamos la posición del Slider bloqueando señales
        self.slider_paginas.blockSignals(True)
        self.slider_paginas.setValue(self.pagina_actual + 1)
        self.slider_paginas.blockSignals(False)

    def pagina_anterior(self):
        if self.pagina_actual > 0:
            self.pagina_actual -= 1
            self.mostrar_pagina()

    def pagina_siguiente(self):
        if self.pagina_actual < self.total_paginas - 1:
            self.pagina_actual += 1
            self.mostrar_pagina()

    # IR A PÁGINA MEDIANTE DESLIZADOR
    def ir_a_pagina_slider(self, valor):
        if self.doc:
            self.pagina_actual = valor - 1
            self.mostrar_pagina()

    def fijar_inicio(self):
        self.spin_n1.setValue(self.pagina_actual + 1)
        
    def fijar_fin(self):
        self.spin_n2.setValue(self.pagina_actual + 1)

    def auto_fijar_pagina_inicio(self, texto):
        if texto.strip() and self.doc:
            self.spin_n1.setValue(self.pagina_actual + 1)

    def auto_fijar_pagina_fin(self, texto):
        if texto.strip() and self.doc:
            self.spin_n2.setValue(self.pagina_actual + 1)

    def comprobar_seleccion_texto(self):
        cursor = self.txt_pagina_text.textCursor()
        tiene_seleccion = cursor.hasSelection()
        
        self.btn_sel_inicio.setEnabled(tiene_seleccion)
        self.btn_sel_fin.setEnabled(tiene_seleccion)
        
        if tiene_seleccion:
            estilo_activo = f"QPushButton {{ background-color: {DEEP_PURPLE}; color: {NEON_GREEN}; border: 2px solid {NEON_GREEN}; font-size: 13px; font-weight: bold; padding: 5px; }}"
            self.btn_sel_inicio.setStyleSheet(estilo_activo)
            self.btn_sel_fin.setStyleSheet(estilo_activo)
        else:
            estilo_apagado = "QPushButton { background-color: #2b2b36; color: #666666; border: 1px solid #444444; font-size: 13px; padding: 5px; }"
            self.btn_sel_inicio.setStyleSheet(estilo_apagado)
            self.btn_sel_fin.setStyleSheet(estilo_apagado)

    def aplicar_seleccion_inicio(self):
        texto = self.txt_pagina_text.textCursor().selectedText()
        texto_limpio = texto.replace('\u2029', ' ').strip()
        self.txt_recorte_inicio.setText(texto_limpio)
        self.spin_n1.setValue(self.pagina_actual + 1)

    def aplicar_seleccion_fin(self):
        texto = self.txt_pagina_text.textCursor().selectedText()
        texto_limpio = texto.replace('\u2029', ' ').strip()
        self.txt_recorte_fin.setText(texto_limpio)
        self.spin_n2.setValue(self.pagina_actual + 1)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.visor_stack.currentIndex() == 1 and self.doc:
            self.mostrar_pagina()

    # --- LÓGICA DE AUDIO (MIGRADA AL BACKEND) ---
    def iniciar_generacion_audio(self):
        n1 = self.spin_n1.value()
        n2 = self.spin_n2.value()
        recorte_inicio = self.txt_recorte_inicio.text().strip()
        recorte_fin = self.txt_recorte_fin.text().strip()

        idioma_elegido = self.combo_idioma.currentText()
        voz_activa = self.voces_map[idioma_elegido]

        velocidad_elegida = self.combo_velocidad.currentText()
        velocidad_rate = self.velocidad_map[velocidad_elegida]

        if n1 > n2:
            QMessageBox.warning(self, "¡Error noventero!", "La página de inicio no puede ser mayor que la página de fin.")
            return

        self.btn_generar.setEnabled(False)
        self.btn_cargar.setEnabled(False)
        
        # Iniciar animación espacial con el OVNI
        self.contador_frame = 0
        self.timer_espacial.start(150) 

        hilo = threading.Thread(
            target=self.proceso_audio_background, 
            args=(n1, n2, recorte_inicio, recorte_fin, voz_activa, velocidad_rate)
        )
        hilo.start()

    def proceso_audio_background(self, n1, n2, recorte_inicio, recorte_fin, voz, rate):
        try:
            texto_completo = lector.extraer_y_recortar_texto(self.doc, n1, n2, recorte_inicio, recorte_fin)
            nombre_salida = lector.generar_nombre_salida(self.ruta_archivo, n1, n2)
            asyncio.run(lector.generar_mp3_async(texto_completo, nombre_salida, voz, rate))
            self.avisador.finalizado.emit(nombre_salida)
        except Exception as e:
            self.avisador.error.emit(str(e))

    # --- ACTUALIZADOR DE ANIMACIÓN ESPACIAL EN TIEMPO REAL ---
    def actualizar_animacion_espacial(self):
        self.lbl_estado.setText(self.frames_espacio[self.contador_frame])
        self.contador_frame = (self.contador_frame + 1) % len(self.frames_espacio)

    # --- PINTADO DE LA MARCA DE AGUA CONTINUA EN EL FONDO ---
    def paintEvent(self, event):
        super().paintEvent(event)
        # Si el libro está cargado, dibujamos la marca de agua fantasmal de fondo
        if self.visor_stack.currentIndex() == 1 and os.path.exists(RUTA_ICONO):
            painter = QPainter(self)
            painter.setOpacity(0.06)  
            pixmap = QPixmap(RUTA_ICONO)
            ancho_marca = 200  
            pix_scaled = pixmap.scaledToWidth(ancho_marca, Qt.TransformationMode.SmoothTransformation)
            
            # Esquina inferior derecha
            x = self.width() - pix_scaled.width() - 20
            y = self.height() - pix_scaled.height() - 90
            
            painter.drawPixmap(x, y, pix_scaled)
            painter.end()

    def audio_completado(self, archivo):
        self.timer_espacial.stop() 
        self.lbl_estado.setText("")
        self.btn_generar.setEnabled(True)
        self.btn_cargar.setEnabled(True)
        QMessageBox.information(
            self, 
            "¡Listo para dormir!", 
            f"El fragmento exacto se ha generado:\n\n👉 {archivo}"
        )

    def audio_error(self, error_msg):
        self.timer_espacial.stop() 
        self.lbl_estado.setText("")
        self.btn_generar.setEnabled(True)
        self.btn_cargar.setEnabled(True)
        QMessageBox.critical(self, "Error de recorte/red", f"No se pudo crear el audio:\n{error_msg}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # FORZAR A GNOME/LINUX A USAR NUESTRO ICONO EN EL DOCK DE ABAJO
    app.setApplicationName("pimiento")
    app.setDesktopFileName("pimiento") # CLAVE: Enlaza la app en ejecución con pimiento.desktop
    
    if os.path.exists(RUTA_ICONO):
        app.setWindowIcon(QIcon(RUTA_ICONO))
        
    # AUTO-REGISTRAR LANZADOR EN LA MÁQUINA DONDE SE ABRA
    auto_registrar_desktop_linux()
        
    splash = SplashScreen()
    splash.show()
    main_app = PimientoJoeApp()
    QTimer.singleShot(3000, splash.close)
    QTimer.singleShot(3000, main_app.show)
    sys.exit(app.exec())
