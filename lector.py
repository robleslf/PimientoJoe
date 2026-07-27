import os
import re
import asyncio
import fitz  # PyMuPDF
import edge_tts

def abrir_documento(ruta):
    """ Abre un documento con PyMuPDF y retorna el documento y el total de páginas. """
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
    """ Genera el nombre de archivo MP3 según la convención del usuario """
    nombre_base = os.path.splitext(os.path.basename(ruta_original))[0]
    nombre_limpio = re.sub(r'[\s\W]+', '_', nombre_base)
    return f"{nombre_limpio}_pps_{n1}_{n2}.mp3"

async def generar_mp3_async(texto, nombre_archivo, voz, rate):
    """ Conecta de forma asíncrona con Edge-TTS para generar el audio """
    communicate = edge_tts.Communicate(texto, voz, rate=rate)
    await communicate.save(nombre_archivo)
