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

def generar_nombre_salida(ruta_original, n1, n2, formato="mp3"):
    """ Genera el nombre de archivo según el formato elegido por el usuario (NUEVO) """
    nombre_base = os.path.splitext(os.path.basename(ruta_original))[0]
    nombre_limpio = re.sub(r'[\s\W]+', '_', nombre_base)
    return f"{nombre_limpio}_pps_{n1}_{n2}.{formato}"

def generar_audio_offline(texto, nombre_archivo, length_scale, idioma_code, formato="mp3"):
    """ Ejecuta el motor neuronal local Piper TTS y adapta el renderizado según el formato (NUEVO) """
    piper_bin = resource_path("bin/piper/piper")
    lame_bin = resource_path("bin/piper/lame")
    
    # Mapeo de idiomas offline
    voces_modelos = {
        "es_ES": "es_ES-davefx-medium.onnx",
        "en_US": "en_US-amy-medium.onnx",
        "zh_CN": "zh_CN-huayan-medium.onnx"
    }
    
    modelo_elegido = voces_modelos.get(idioma_code, "es_ES-davefx-medium.onnx")
    voice_model = resource_path(f"bin/piper/{modelo_elegido}")
    
    if not os.path.exists(piper_bin) or not os.path.exists(voice_model):
        raise FileNotFoundError(f"No se encontró el motor de voz Piper offline o el modelo de voz {modelo_elegido}.")

    # Asegurar permisos de ejecución a los binarios desempaquetados
    os.chmod(piper_bin, 0o755)
    if os.path.exists(lame_bin):
        os.chmod(lame_bin, 0o755)
    
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = resource_path("bin/piper")
    
    # Si el formato es MP3, generamos un WAV temporal y luego comprimimos.
    # Si el formato es WAV, generamos directamente el archivo final.
    if formato == "mp3":
        temp_wav = nombre_archivo.replace(".mp3", ".wav")
    else:
        temp_wav = nombre_archivo
    
    cmd_piper = [
        piper_bin,
        "-m", voice_model,
        "-f", temp_wav,
        "--length_scale", str(length_scale)
    ]
    
    # 1. Ejecutar Piper para crear el WAV
    process = subprocess.Popen(
        cmd_piper, 
        stdin=subprocess.PIPE, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE, 
        text=True, 
        env=env
    )
    stdout, stderr = process.communicate(input=texto)
    
    if process.returncode != 0:
        raise RuntimeError(f"Fallo del motor de IA local (Código {process.returncode}): {stderr}")
        
    # 2. Si el formato elegido es MP3, convertimos el WAV usando LAME
    if formato == "mp3" and os.path.exists(lame_bin) and os.path.exists(temp_wav):
        cmd_lame = [
            lame_bin,
            "-b", "192", # Bitrate estándar de alta calidad (192 kbps)
            temp_wav,
            nombre_archivo
        ]
        process_lame = subprocess.Popen(cmd_lame, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process_lame.communicate()
        
        # Borrar el archivo WAV temporal
        try:
            os.remove(temp_wav)
        except Exception:
            pass
    elif formato == "mp3" and os.path.exists(temp_wav):
        # Fallback de seguridad (renombrar en caso de que no esté LAME)
        os.rename(temp_wav, nombre_archivo)