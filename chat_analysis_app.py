import streamlit as st
import pandas as pd
import re
import unicodedata
from datetime import datetime, timedelta
from collections import Counter

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

# ---------- FUNCIONES UTILITARIAS ----------
def normalizar_unicode(texto):
    texto = unicodedata.normalize('NFKC', texto)
    texto = texto.replace('\u202F', ' ').replace('\u200e', '').replace('\u200d', '')
    return texto.strip()

def cargar_chat_whatsapp(archivo_subido):
    lineas_crudas = archivo_subido.read().decode('utf-8').splitlines()
    lineas_limpias = [normalizar_unicode(linea) for linea in lineas_crudas if linea.strip()]
    mensajes_completos = []
    mensaje_actual = ""
    patron_inicio = re.compile(r'^\[\d{2}/\d{2}/\d{2}, \d{1,2}:\d{2}:\d{2}\s?[ap]\.m\.\]\s?.*?:\s')

    for linea in lineas_limpias:
        if patron_inicio.match(linea):
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
    inicio = datetime(fecha_actual.year, fecha_actual.month, fecha_actual.day, 7, 0) - timedelta(days=1)
    fin = datetime(fecha_actual.year, fecha_actual.month, fecha_actual.day, 6, 59, 59)
    return [(fh, m, cumple_filtro(m)) for m in mensajes if (fh := extraer_fecha_hora_mensaje(m)) and inicio <= fh <= fin]

def extraer_datos_estructurados(mensaje, fecha_hora):
    datos = {
        "Máquina": None,
        "Motivo de paro": None,
        "Solución": None,
        "Hora de inicio": fecha_hora.strftime('%d/%m/%Y %H:%M:%S'),
        "Reportó": None,
        "Mensaje completo": mensaje
    }
    remitente = re.match(r'^\[.*?\] (.*?):', mensaje)
    if remitente:
        datos["Reportó"] = remitente.group(1).strip()
    linea = re.search(r'\*L[ií]nea\*\s*(.*?)(?:\n|$)', mensaje, re.IGNORECASE)
    if linea:
        for maq in MAQUINAS_VALIDAS:
            if maq.lower() in linea.group(1).lower():
                datos["Máquina"] = maq
                break
    desc = re.search(r'\*Descripci[oó]n\*\s*(.*?)(?:\n|$)', mensaje, re.IGNORECASE | re.DOTALL)
    if desc:
        datos["Motivo de paro"] = datos["Solución"] = desc.group(1).strip()
    return datos

# ---------------------- INTERFAZ STREAMLIT ----------------------
st.set_page_config(page_title="Analizador de Turno", layout="wide")
st.title("📊 Analizador de Mensajes de Turno - WhatsApp")
archivos = st.file_uploader("🔼 Sube archivos de chat (Nivel 2 y/o Nivel 3)", type=["txt"], accept_multiple_files=True)

if archivos:
    fecha_actual = datetime.now()
    inicio_turno = (fecha_actual - timedelta(days=1)).replace(hour=7, minute=0, second=0, microsecond=0)
    fin_turno = fecha_actual.replace(hour=6, minute=59, second=59, microsecond=0)
    st.info(f"🕐 Analizando desde: {inicio_turno.strftime('%d/%m/%Y %I:%M %p')} hasta {fin_turno.strftime('%d/%m/%Y %I:%M %p')}")

    todos_los_datos = []

    for archivo in archivos:
        mensajes = cargar_chat_whatsapp(archivo)
        mensajes_filtrados = filtrar_mensajes_turno_anterior(mensajes, fecha_actual)
        st.subheader(f"📁 Archivo: {archivo.name} - {len(mensajes_filtrados)} mensajes relevantes")

        for fecha_hora, mensaje, palabra in sorted(mensajes_filtrados, key=lambda x: x[0]):
            datos = extraer_datos_estructurados(mensaje, fecha_hora)
            datos["Palabra clave"] = palabra or "No relevante"
            todos_los_datos.append(datos)

    if todos_los_datos:
        df = pd.DataFrame(todos_los_datos)

        # Filtros
        maquinas = st.multiselect("🏭 Filtrar por Máquina", sorted(df["Máquina"].dropna().unique()))
        personas = st.multiselect("👤 Filtrar por Persona", sorted(df["Reportó"].dropna().unique()))

        if maquinas:
            df = df[df["Máquina"].isin(maquinas)]
        if personas:
            df = df[df["Reportó"].isin(personas)]

        # Conteo por máquina
        conteo = df["Máquina"].value_counts().rename_axis("Máquina").reset_index(name='Fallas')
        st.bar_chart(conteo.set_index("Máquina"))

        # Exportar
        st.download_button(
            label="📥 Descargar Excel",
            data=df.to_excel(index=False, engine='openpyxl'),
            file_name="resumen_turno.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # Mostrar resultados
        for _, row in df.iterrows():
            col1, col2 = st.columns([2, 3])
            with col1:
                st.markdown(f"""
                **📅 Hora:** {row['Hora de inicio']}  
                **👤 Reportó:** {row['Reportó']}  
                **🏭 Máquina:** {row['Máquina']}  
                **❌ Motivo de paro:** {row['Motivo de paro']}  
                **🛠 Solución:** {row['Solución']}  
                **🔑 Palabra clave:** {row['Palabra clave']}
                """)
            with col2:
                st.code(row['Mensaje completo'], language="markdown")
else:
    st.info("⬆️ Sube uno o dos archivos .txt exportados de WhatsApp para iniciar el análisis.")
