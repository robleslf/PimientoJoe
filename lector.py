import os
import re
import sys
import subprocess
import fitz  # PyMuPDF

def resource_path(relative_path):
    """ Obtiene la ruta absoluta de los recursos, compatible con desarrollo y PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def abrir_documento(ruta):
    """ Abre un documento con PyMuPDF y retorna el documento y el total de páginas """
    if ruta.lower().endswith(('.azw', '.azw3')):
        raise ValueError("AmazonAZW")
    
    doc = fitz.open(ruta)
    return doc, len(doc)

def extraer_y_recortar_texto(doc, n1, n2, recorte_inicio="", recorte_fin=""):
    """ Extrae el texto de un rango de páginas y aplica el recorte inteligente """
    texto_completo = ""
    for i in range(n1 - 1, n2):
        pagina = doc.load_page(i)
        texto_completo += pagina.get_text() + "\n"

    # Limpiar espacios excesivos
    texto_completo = re.sub(r'\s+', ' ', texto_completo).strip()

    # Aplicar recortes si existen
    if recorte_inicio:
        idx_inicio = texto_completo.lower().find(recorte_inicio.lower())
        if idx_inicio != -1:
            texto_completo = texto_completo[idx_inicio:]
        else:
            raise ValueError(f"No encontré la frase de inicio: '{recorte_inicio}'")

    if recorte_fin:
        idx_fin = texto_completo.lower().find(recorte_fin.lower())
        if idx_fin != -1:
            texto_completo = texto_completo[:idx_fin + len(recorte_fin)]
        else:
            raise ValueError(f"No encontré la frase de fin: '{recorte_fin}'")

    if not texto_completo:
        raise ValueError("El texto seleccionado está vacío.")

    return texto_completo

def generar_nombre_salida(ruta_original, n1, n2):
    """ Genera el nombre de archivo WAV (calidad CD) de forma portátil """
    nombre_base = os.path.splitext(os.path.basename(ruta_original))[0]
    nombre_limpio = re.sub(r'[\s\W]+', '_', nombre_base)
    return f"{nombre_limpio}_pps_{n1}_{n2}.wav"

def generar_audio_offline(texto, nombre_archivo, length_scale, idioma_code):
    """ Ejecuta el motor neuronal local Piper TTS de forma 100% offline y portátil """
    piper_bin = resource_path("bin/piper/piper")
    
    # Mapeo de idiomas offline a su modelo ONNX empaquetado (NUEVO)
    voces_modelos = {
        "es_ES": "es_ES-davefx-medium.onnx",
        "en_US": "en_US-amy-medium.onnx",
        "zh_CN": "zh_CN-huayan-medium.onnx"
    }
    
    # Fallback por si llega algún código raro
    modelo_elegido = voces_modelos.get(idioma_code, "es_ES-davefx-medium.onnx")
    voice_model = resource_path(f"bin/piper/{modelo_elegido}")
    
    if not os.path.exists(piper_bin) or not os.path.exists(voice_model):
        raise FileNotFoundError(f"No se encontró el motor de voz Piper offline o el modelo de voz {modelo_elegido}.")

    # Asegurar permisos de ejecución al binario desempaquetado en caliente
    os.chmod(piper_bin, 0o755)
    
    # Truco de Linux: Indicamos al binario dónde buscar sus librerías dinámicas .so empaquetadas
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = resource_path("bin/piper")
    
    cmd = [
        piper_bin,
        "-m", voice_model,
        "-f", nombre_archivo,
        "--length_scale", str(length_scale)
    ]
    
    # Ejecutar el sintetizador local inyectando el texto por entrada estándar (stdin)
    process = subprocess.Popen(
        cmd, 
        stdin=subprocess.PIPE, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE, 
        text=True, 
        env=env
    )
    stdout, stderr = process.communicate(input=texto)
    
    if process.returncode != 0:
        raise RuntimeError(f"Fallo del motor de IA local (Código {process.returncode}): {stderr}")