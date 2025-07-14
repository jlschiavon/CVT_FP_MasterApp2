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
VARIACIONES_EN_PRODUCCION = [
    "en producción", "en produccion", "en produción", "EN PRODUCCIÓN", "En produccion",
    "En Producción", "EN PRODUCCION", "EN PRODUCION"
]

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
        if variante in texto:
            return True
    return False

def detectar_respuestas(datos):
    respuestas = []
    for i in range(1, len(datos)):
        actual = datos[i]
        anterior = datos[i - 1]

        palabras = actual["Mensaje completo"].split()
        if len(palabras) > 40:
            continue

        if not contiene_frase_respuesta(actual["Mensaje completo"]):
            continue

        hora_actual = datetime.strptime(actual["Hora de inicio"], "%d/%m/%Y %H:%M:%S")
        hora_anterior = datetime.strptime(anterior["Hora de inicio"], "%d/%m/%Y %H:%M:%S")
        delta = hora_actual - hora_anterior
        if delta.total_seconds() > 3 * 3600 or delta.total_seconds() < 5:
            continue

        misma_persona = actual["Reportó"] == anterior["Reportó"]
        misma_palabra = actual["Palabra clave"] == anterior["Palabra clave"]
        mismo_equipo = actual["Máquina"] == anterior["Máquina"]

        if misma_persona or misma_palabra or mismo_equipo:
            respuestas.append((anterior, actual))
    return respuestas

# ----------- INTERFAZ -----------
st.set_page_config(page_title="Analizador de Turno", layout="wide")
st.title("📊 Paros CVT - WhatsApp Nivel 2 y 3")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📥 Chat Nivel 2")
    archivo_n2 = st.file_uploader("Sube el archivo Nivel 2", type=["txt"], key="n2")

with col2:
    st.subheader("📥 Chat Nivel 3")
    archivo_n3 = st.file_uploader("Sube el archivo Nivel 3", type=["txt"], key="n3")

def procesar_chat(nombre_nivel, archivo):
    st.markdown(f"### 📂 {nombre_nivel}")

    fecha_actual = datetime.now()
    inicio_turno = datetime(fecha_actual.year, fecha_actual.month, fecha_actual.day, 7, 0, 0) - timedelta(days=1)
    fin_turno = datetime(fecha_actual.year, fecha_actual.month, fecha_actual.day, 6, 59, 59)

    mensajes = cargar_chat_whatsapp(archivo)
    mensajes_filtrados = filtrar_mensajes_en_rango(mensajes, inicio_turno, fin_turno)

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

            <div style='background-color:#343434; padding:10px; border-radius:10px; border:1px solid #444;'>
            <b>📩 Mensaje original:</b><br>{datos['Mensaje completo'].replace('\n', '<br>')}
            </div>
            """, unsafe_allow_html=True)

            respuestas_para_este = [r for o, r in respuestas if o["Mensaje completo"] == datos["Mensaje completo"]]
            if respuestas_para_este:
                st.markdown("🔗 **Posibles respuestas:**")
                for respuesta in respuestas_para_este:
                    st.markdown(f"""
                    <div style="border-left: 5px solid #4CAF50; padding-left: 10px; margin-bottom: 10px;">
                    <b>↪ {respuesta['Reportó']} ({respuesta['Hora de inicio']}):</b><br>
                    {respuesta['Mensaje completo'].replace('\n', '<br>')}
                    </div>
                    """, unsafe_allow_html=True)

    df = pd.DataFrame(datos_estructurados)[["Máquina", "Motivo de paro", "Solución", "Hora de inicio", "Reportó"]]
    output = BytesIO()
    df.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)
    st.download_button(
        label=f"📥 Descargar Excel ({nombre_nivel})",
        data=output,
        file_name=f"reporte_fallas_{nombre_nivel.lower().replace(' ', '_')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

if archivo_n2:
    procesar_chat("Nivel 2", archivo_n2)
if archivo_n3:
    procesar_chat("Nivel 3", archivo_n3)
