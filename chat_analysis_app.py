import streamlit as st
import re
import unicodedata
from datetime import datetime, timedelta
from io import BytesIO
import pandas as pd
import difflib

# ---------- CONFIGURACIÓN ----------
PALABRAS_CLAVE = [
    "Recken", "Reckens", "Recken 19", "Recken 24", "Recken 17", "Recken 20",
    "Recken 31", "Recken 13", "Recken 33", "Recken 34", "R19", "R24", "R17", "R20",
    "R31", "R13", "R33", "R34", "R 19", "R 24", "R 17", "R 20", "R 31", "R 13", "R 33", "R 34",
    "Recken19", "Recken24", "Recken17", "Recken20", "Recken31", "Recken13", "Recken33", "Recken34",
    "VPK 1", "VPK 2", "VPK1", "VPK2", "Plato Vibrador", "Lavadora", "Lavadoras",
    "Lavadora 1", "Lavadora 2", "lavadora 1", "lavadora 2", "recken", "reckens", "r19",
    "plato vibrador", "Plato vibrador 1", "Plato vibrador 2"
]

MAQUINAS_VALIDAS = [
    "Recken 19", "Recken 24", "Recken 17", "Recken 20",
    "Recken 31", "Recken 13", "Recken 33", "Recken 34",
    "Lavadora 1", "Lavadora 2", "VPK 1", "VPK 2", "ALDS VPK",
    "Etiquetadora / cámara verificación etiquetas 1",
    "Etiquetadora / cámara verificación etiquetas 2",
    "Plato Vibrador 1", "Plato Vibrador 2"
]

VARIACIONES_EN_PRODUCCION = [
    "en producción", "en produccion", "en produción", "EN PRODUCCIÓN",
    "En produccion", "En Producción", "EN PRODUCCION", "EN PRODUCION"
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

def filtrar_mensajes_en_rango(mensajes, inicio, fin):
    mensajes_filtrados_final = []
    for mensaje in mensajes:
        fecha_hora = extraer_fecha_hora_mensaje(mensaje)
        if fecha_hora and inicio <= fecha_hora <= fin:
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

def contiene_frase_respuesta(texto):
    texto = texto.lower()
    for variante in VARIACIONES_EN_PRODUCCION:
        if difflib.SequenceMatcher(None, texto, variante.lower()).ratio() > 0.8:
            return True
        if variante.lower() in texto:
            return True
    return False

def detectar_respuestas(datos):
    respuestas = []
    for i in range(1, len(datos)):
        actual = datos[i]
        anterior = datos[i - 1]

        palabras = actual["Mensaje completo"].split()
        if len(palabras) > 100:
            continue

        if not contiene_frase_respuesta(actual["Mensaje completo"]):
            continue

        hora_actual = datetime.strptime(actual["Hora de inicio"], "%d/%m/%Y %H:%M:%S")
        hora_anterior = datetime.strptime(anterior["Hora de inicio"], "%d/%m/%Y %H:%M:%S")
        delta = hora_actual - hora_anterior
        if delta.total_seconds() > 12 * 3600 or delta.total_seconds() < 5:
            continue

        misma_persona = actual["Reportó"] == anterior["Reportó"]
        misma_palabra = actual["Palabra clave"] == anterior["Palabra clave"]
        mismo_equipo = actual["Máquina"] == anterior["Máquina"]

        if misma_persona or misma_palabra or mismo_equipo or not misma_persona:
            respuestas.append((anterior, actual))
    return respuestas

# ---------------------- INTERFAZ STREAMLIT ----------------------
st.set_page_config(page_title="Analizador de Turno", layout="wide")
st.title("📊 Paros CVT - WhatsApp Nivel 2 y 3")

archivo = st.file_uploader("🔼 Sube el archivo de chat (.txt exportado de WhatsApp)", type=["txt"])

st.sidebar.subheader("🕒 Rango de tiempo de análisis")
modo_rango = st.sidebar.radio("Selecciona un modo de filtrado:", ["📅 Día laboral anterior", "📆 Personalizado"])

if modo_rango == "📅 Día laboral anterior":
    fecha_actual = datetime.now()
    inicio_turno = datetime(fecha_actual.year, fecha_actual.month, fecha_actual.day, 7, 0, 0) - timedelta(days=1)
    fin_turno = datetime(fecha_actual.year, fecha_actual.month, fecha_actual.day, 6, 59, 59)
else:
    col1, col2 = st.sidebar.columns(2)
    fecha_inicio = col1.date_input("Fecha inicio")
    hora_inicio = col1.time_input("Hora inicio", value=datetime.now().replace(hour=7, minute=0).time())

    fecha_fin = col2.date_input("Fecha fin")
    hora_fin = col2.time_input("Hora fin", value=datetime.now().replace(hour=6, minute=59).time())

    inicio_turno = datetime.combine(fecha_inicio, hora_inicio)
    fin_turno = datetime.combine(fecha_fin, hora_fin)

st.sidebar.info(f"⏳ Analizando mensajes desde **{inicio_turno.strftime('%d/%m/%Y %H:%M')}** hasta **{fin_turno.strftime('%d/%m/%Y %H:%M')}**")

if archivo is not None:
    mensajes = cargar_chat_whatsapp(archivo)

    if not mensajes:
        st.warning("❌ No se encontraron mensajes válidos en el archivo.")
    else:
        mensajes_filtrados = filtrar_mensajes_en_rango(mensajes, inicio_turno, fin_turno)
        st.success(f"✅ Mensajes analizados: {len(mensajes_filtrados)} en el rango seleccionado.")

        datos_estructurados = []
        for fecha_hora, mensaje, palabra in sorted(mensajes_filtrados, key=lambda x: x[0]):
            datos = extraer_datos_estructurados(mensaje, fecha_hora)
            datos["Palabra clave"] = palabra
            datos["Mensaje completo"] = mensaje
            datos_estructurados.append(datos)

        respuestas = detectar_respuestas(datos_estructurados)

        for datos in datos_estructurados:
            with st.expander(f"📅 {datos['Hora de inicio']} | 👤 {datos['Reportó']}", expanded=False):
                st.markdown(f"""
                - 🏭 **Máquina:** {datos['Máquina'] or 'No detectada'}
                - ❌ **Motivo de paro:** {datos['Motivo de paro'] or 'No especificado'}
                - 🛠 **Solución:** {datos['Solución'] or 'No especificada'}
                - 🔑 **Palabra clave:** {datos['Palabra clave']}
                
                📩 **Mensaje original:**
                ```
                {datos['Mensaje completo']}
                ```
                ---""")

                respuestas_para_este = [r for o, r in respuestas if o["Mensaje completo"] == datos["Mensaje completo"]]
                if respuestas_para_este:
                    st.markdown("🔗 **Posibles respuestas:**")
                    for respuesta in respuestas_para_este:
                        st.markdown(f"""
                        <div style="border-left: 5px solid #4CAF50; padding-left: 10px; margin-bottom: 10px;">
                        <b>↪ {respuesta['Reportó']} ({respuesta['Hora de inicio']}):</b><br>
                        <code>{respuesta['Mensaje completo']}</code>
                        </div>
                        """, unsafe_allow_html=True)

        # Exportar a Excel
        df = pd.DataFrame(datos_estructurados)[["Máquina", "Motivo de paro", "Solución", "Hora de inicio", "Reportó"]]
        output = BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)

        st.download_button(
            label="📥 Descargar Excel",
            data=output,
            file_name="reporte_fallas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.info("⬆️ Por favor, sube un archivo para iniciar el análisis.")
