import streamlit as st
import re
import unicodedata
from datetime import datetime, timedelta

# ---------- CONFIGURACIÓN ----------
PALABRAS_CLAVE = [
    "Recken", "Reckens", "Recken 19", "Recken 24", "Recken 17", "Recken 20",
    "Recken 31", "Recken 13", "Recken 33", "Recken 34", "R19", "R24", "R17", "R20",
    "R31", "R13", "R33", "R34", "R 19", "R 24", "R 17", "R 20", "R 31", "R 13", "R 33", "R 34",
    "Recken19", "Recken24", "Recken17", "Recken20", "Recken31", "Recken13", "Recken33", "Recken34",
    "VPK 1", "VPK 2", "VPK1", "VPK2", "Plato Vibrador", "Lavadora", "Lavadoras",
    "Lavadora 1", "Lavadora 2", "lavadora 1", "lavadora 2", "recken", "reckens", "r19", "plato vibrador", "Plato vibrador 1", "Plato vibrador 2"
]

MAQUINAS_VALIDAS = [
    "Recken 19", "Recken 24", "Recken 17", "Recken 20",
    "Recken 31", "Recken 13", "Recken 33", "Recken 34",
    "Lavadora 1", "Lavadora 2", "VPK 1", "VPK 2", "ALDS VPK",
    "Etiquetadora / cámara verificación etiquetas 1",
    "Etiquetadora / cámara verificación etiquetas 2",
    "Plato Vibrador 1", "Plato Vibrador 2"
]

IMAGE_OMITTED_MESSAGE = "image omitted"

def normalizar_unicode(texto):
    texto = unicodedata.normalize('NFKC', texto)
    texto = texto.replace('\u202F', ' ').replace('\u200e', '').replace('\u200d', '')
    return texto.strip()

def cargar_chat_whatsapp(archivo_subido):
    lineas_crudas = archivo_subido.read().decode('utf-8').splitlines()
    lineas_limpias = [normalizar_unicode(linea) for linea in lineas_crudas if linea.strip()]

    mensajes_completos = []
    mensaje_actual = ""
    mensaje_inicio_patron = re.compile(r'^\[\d{2}/\d{2}/\d{2}, \d{1,2}:\d{2}:\d{2}\s?[ap]\.m\.\]\s?.*?:\s')

    for linea in lineas_limpias:
        if mensaje_inicio_patron.match(linea):
            if mensaje_actual and IMAGE_OMITTED_MESSAGE.lower() not in mensaje_actual.lower():
                mensajes_completos.append(mensaje_actual)
            mensaje_actual = linea
        else:
            mensaje_actual += "\n" + linea

    if mensaje_actual and IMAGE_OMITTED_MESSAGE.lower() not in mensaje_actual.lower():
        mensajes_completos.append(mensaje_actual)

    return mensajes_completos

def extraer_fecha_hora_mensaje(mensaje):
    mensaje = normalizar_unicode(mensaje)
    match = re.match(r'^\[(\d{2}/\d{2}/\d{2}), (\d{1,2}:\d{2}:\d{2})\s?([ap]\.m\.)\]', mensaje)
    if match:
        fecha_str = match.group(1)
        hora_str = match.group(2)
        ampm = match.group(3).replace('.', '').upper()
        try:
            return datetime.strptime(f"{fecha_str} {hora_str} {ampm}", '%d/%m/%y %I:%M:%S %p')
        except ValueError:
            return None
    return None

def cumple_filtro(mensaje):
    contenido_lower = mensaje.lower()
    for palabra in PALABRAS_CLAVE:
        if palabra.lower() in contenido_lower:
            return palabra
    return None

def filtrar_mensajes_turno_anterior(mensajes, fecha_actual):
    inicio_turno = datetime(fecha_actual.year, fecha_actual.month, fecha_actual.day, 7, 0, 0) - timedelta(days=1)
    fin_turno = datetime(fecha_actual.year, fecha_actual.month, fecha_actual.day, 6, 59, 59)

    mensajes_filtrados_final = []

    for mensaje in mensajes:
        fecha_hora = extraer_fecha_hora_mensaje(mensaje)
        if fecha_hora and inicio_turno <= fecha_hora <= fin_turno:
            palabra_detectada = cumple_filtro(mensaje)
            if palabra_detectada:
                mensajes_filtrados_final.append((fecha_hora, mensaje, palabra_detectada))
    return mensajes_filtrados_final

def extraer_datos_estructurados(mensaje, fecha_hora):
    datos = {
        "Máquina": None,
        "Motivo de paro": None,
        "Solución": None,
        "Hora de inicio": fecha_hora.strftime('%d/%m/%Y %H:%M:%S'),
        "Reportó": None
    }

    remitente_match = re.match(r'^\[\d{2}/\d{2}/\d{2}, \d{1,2}:\d{2}:\d{2}\s?[ap]\.m\.\] (.*?):', mensaje)
    if remitente_match:
        datos["Reportó"] = remitente_match.group(1).strip()

    patrones = {
        "linea": r'\*L[ií]nea\*\s*(.*?)(?:\n|$)',
        "descripcion": r'\*Descripci[oó]n\*\s*(.*?)(?:\n|$)',
    }

    linea_match = re.search(patrones["linea"], mensaje, flags=re.IGNORECASE | re.DOTALL)
    if linea_match:
        linea_detectada = linea_match.group(1).strip()
        for maquina in MAQUINAS_VALIDAS:
            if maquina.lower() in linea_detectada.lower():
                datos["Máquina"] = maquina
                break

    descripcion_match = re.search(patrones["descripcion"], mensaje, flags=re.IGNORECASE | re.DOTALL)
    if descripcion_match:
        descripcion = descripcion_match.group(1).strip()
        datos["Motivo de paro"] = descripcion
        datos["Solución"] = descripcion

    return datos

# ---------------------- INTERFAZ STREAMLIT ----------------------
st.set_page_config(page_title="Analizador de Turno", layout="wide")
st.title("📊 Analizador de Mensajes de Turno - WhatsApp")

archivo = st.file_uploader("🔼 Sube el archivo de chat (.txt exportado de WhatsApp)", type=["txt"])

if archivo is not None:
    fecha_actual = datetime.now()
    mensajes = cargar_chat_whatsapp(archivo)

    if not mensajes:
        st.warning("❌ No se encontraron mensajes válidos en el archivo.")
    else:
        mensajes_filtrados = filtrar_mensajes_turno_anterior(mensajes, fecha_actual)
        st.success(f"✅ Mensajes analizados: {len(mensajes_filtrados)} en el turno anterior.")

        for fecha_hora, mensaje, palabra in sorted(mensajes_filtrados, key=lambda x: x[0]):
            datos = extraer_datos_estructurados(mensaje, fecha_hora)
            st.markdown(f"""
            #### 📅 {datos['Hora de inicio']} | 👤 {datos['Reportó']}
            - 🏭 **Máquina:** {datos['Máquina'] or 'No detectada'}
            - ❌ **Motivo de paro:** {datos['Motivo de paro'] or 'No especificado'}
            - 🛠 **Solución:** {datos['Solución'] or 'No especificada'}
            - 🔑 **Palabra clave:** {palabra}
            ---
            """)
else:
    st.info("⬆️ Por favor, sube un archivo para iniciar el análisis.")
