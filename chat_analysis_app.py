import streamlit as st
import re
import unicodedata
from datetime import datetime, timedelta
from io import BytesIO
import pandas as pd
import difflib

# ---------------- CONFIGURACION ------------------
PALABRAS_CLAVE = [
    "Recken", "Reckens", "Recken 19", "Recken 24", "Recken 17", "Recken 20",
    "Recken 31", "Recken 13", "Recken 33", "Recken 34", "R19", "R24", "R17", "R20",
    "R31", "R13", "R33", "R34", "R 19", "R 24", "R 17", "R 20", "R 31", "R 13", "R 33", "R 34",
    "Recken19", "Recken24", "Recken17", "Recken20", "Recken31", "Recken13", "Recken33", "Recken34",
    "VPK 1", "VPK 2", "VPK1", "VPK2", "vpk1","vpk2", "Vpk1","Vpk2", "Plato Vibrador", "Lavadora", "Lavadoras",
    "Lavadora 1", "Lavadora 2", "lavadora 1", "lavadora 2", "recken", "reckens", "r19", "r24","r17","r20","r31","r13",
    "r33", "r34", "plato vibrador", "Plato vibrador 1", "Plato vibrador 2", "plato", "Plato"
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
    "en producción", "en produccion", "en produción", "EN PRODUCCIÓN", "En produccion",
    "En Producción", "EN PRODUCCION", "EN PRODUCION"
]

IMAGE_OMITTED_MESSAGE = "image omitted"

# --------------- FUNCIONES ------------------
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
        "Motivo de paro": "No especificado",
        "Solución": "No especificada",
        "Hora de inicio": fecha_hora.strftime('%d/%m/%Y %H:%M:%S'),
        "Reportó": None,
        "Mensaje completo": mensaje
    }

    remitente_match = re.match(r'^\[\d{2}/\d{2}/\d{2}, \d{1,2}:\d{2}:\d{2}\s?[ap]\.m\.\] (.*?):', mensaje)
    if remitente_match:
        datos["Reportó"] = remitente_match.group(1).strip()

    linea_match = re.search(r'\*L[ií]nea\*\s*(.*?)(?:\n|$)', mensaje, flags=re.IGNORECASE | re.DOTALL)
    if linea_match:
        linea_detectada = linea_match.group(1).strip()
        for maquina in MAQUINAS_VALIDAS:
            if maquina.lower() in linea_detectada.lower():
                datos["Máquina"] = maquina
                break

    descripcion_match = re.search(r'\*Descripci[oó]n\*\s*(.*?)(?:\n|$)', mensaje, flags=re.IGNORECASE | re.DOTALL)
    if descripcion_match:
        descripcion = descripcion_match.group(1).strip()
        datos["Motivo de paro"] = descripcion
        datos["Solución"] = descripcion

    return datos

def contiene_frase_respuesta(texto):
    texto = texto.lower()
    for variante in VARIACIONES_EN_PRODUCCION:
        if difflib.SequenceMatcher(None, texto.lower(), variante.lower()).ratio() > 0.8:
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
        misma_palabra = actual.get("Palabra clave") == anterior.get("Palabra clave")
        mismo_equipo = actual["Máquina"] == anterior["Máquina"]

        if misma_persona or misma_palabra or mismo_equipo or not misma_persona:
            respuestas.append((anterior, actual))

    return respuestas

# ------------------ INTERFAZ ----------------------
st.set_page_config(page_title="Analizador Paros", layout="wide")
st.title("🧠 Análisis de chats de escalamiento (N2 y N3)")

# Carga fija de imágenes desde archivos
from PIL import Image
import os

# Configura las rutas relativas o absolutas
RUTA_LOGO = "assets/logo.png"
RUTA_PRODUCTO = "assets/producto.jpg"

# Cargar imágenes si existen
logo_empresa = Image.open(assets/LogoSchaeffler.png) if os.path.exists(assets/LogoSchaeffler.png) else None
imagen_producto = Image.open(assets/Cvt.jpg) if os.path.exists(assets/Cvt.jpg) else None

# CSS para imagen superior y logo flotante
st.markdown(
    """
    <style>
    .product-image-container img {
        width: 100%;
        height: 10vh;
        object-fit: cover;
        border-radius: 8px;
        margin-bottom: 10px;
    }

    .logo-container {
        position: fixed;
        top: 15px;
        right: 25px;
        width: 100px;
        height: auto;
        z-index: 1000;
        background-color: white;
        padding: 5px;
        border-radius: 8px;
        box-shadow: 0 0 10px rgba(0,0,0,0.2);
    }

    .logo-container img {
        width: 100%;
        height: auto;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Mostrar imagen del producto (horizontal superior)
if imagen_producto:
    st.markdown('<div class="product-image-container">', unsafe_allow_html=True)
    st.image(imagen_producto, use_column_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Mostrar logo flotante (fijo en scroll)
if logo_empresa:
    st.markdown('<div class="logo-container">', unsafe_allow_html=True)
    st.image(logo_empresa)
    st.markdown('</div>', unsafe_allow_html=True)



archivo_n2 = st.file_uploader("📤 Chat Nivel 2", type=["txt"], key="chatn2")
archivo_n3 = st.file_uploader("📤 Chat Nivel 3", type=["txt"], key="chatn3")

# -------------- RANGO TIEMPO --------------
st.sidebar.subheader("🕒 Rango de análisis")
modo = st.sidebar.radio("Modo de filtro:", ["📅 Día laboral anterior", "📆 Personalizado"])
if modo == "📅 Día laboral anterior":
    hoy = datetime.now()
    inicio_turno = datetime(hoy.year, hoy.month, hoy.day, 7) - timedelta(days=1)
    fin_turno = datetime(hoy.year, hoy.month, hoy.day, 6, 59, 59)
else:
    c1, c2 = st.sidebar.columns(2)
    f_ini = c1.date_input("Fecha inicio")
    h_ini = c1.time_input("Hora inicio", value=datetime.now().replace(hour=7, minute=0).time())
    f_fin = c2.date_input("Fecha fin")
    h_fin = c2.time_input("Hora fin", value=datetime.now().replace(hour=6, minute=59).time())
    inicio_turno = datetime.combine(f_ini, h_ini)
    fin_turno = datetime.combine(f_fin, h_fin)

st.sidebar.info(f"Analizando del {inicio_turno.strftime('%d/%m/%Y %H:%M')} al {fin_turno.strftime('%d/%m/%Y %H:%M')}")

# ---------------- FUNCION PRINCIPAL ------------------
def procesar_chat(nombre_nivel, archivo):
    if archivo is None:
        return

    st.header(f"📁 Análisis {nombre_nivel}")
    mensajes = cargar_chat_whatsapp(archivo)
    mensajes_filtrados = filtrar_mensajes_en_rango(mensajes, inicio_turno, fin_turno)
    st.success(f"✅ Mensajes analizados: {len(mensajes_filtrados)}")

    datos_estructurados = []
    for fecha_hora, mensaje, palabra in sorted(mensajes_filtrados, key=lambda x: x[0]):
        datos = extraer_datos_estructurados(mensaje, fecha_hora)
        datos["Palabra clave"] = palabra
        datos_estructurados.append(datos)

    respuestas = detectar_respuestas(datos_estructurados)

    for datos in datos_estructurados:
        with st.expander(f"📅 {datos['Hora de inicio']} | 👤 {datos['Reportó']}", expanded=False):
            st.markdown(f"""
            - 🏭 **Máquina:** {datos['Máquina'] or 'No detectada'}
            - ❌ **Motivo de paro:** {datos['Motivo de paro'] or 'No especificado'}
            - 🛠 **Solución:** {datos['Solución'] or 'No especificada'}
            - 🔑 **Palabra clave:** {datos.get('Palabra clave', 'Ninguna')}
            
            📩 **Mensaje original:**
            <div style='border:1px solid #ddd; padding:10px; border-radius:6px; background:#343434;'>
            {datos['Mensaje completo'].replace(chr(10), '<br>')}
            </div>
            """, unsafe_allow_html=True)

            respuestas_para_este = [r for o, r in respuestas if o['Mensaje completo'] == datos['Mensaje completo']]
            if respuestas_para_este:
                st.markdown("🔗 **Posibles respuestas:**")
                for respuesta in respuestas_para_este:
                    st.markdown(f"""
                    <div style="border-left: 5px solid #4CAF50; padding-left: 10px; margin-bottom: 10px;">
                    <b>↪ {respuesta['Reportó']} ({respuesta['Hora de inicio']}):</b><br>
                    <code>{respuesta['Mensaje completo']}</code>
                    </div>
                    """, unsafe_allow_html=True)

    df = pd.DataFrame(datos_estructurados)
    df = df[["Máquina", "Motivo de paro", "Solución", "Hora de inicio", "Reportó"]]
    output = BytesIO()
    df.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)

    st.download_button(
        label=f"📥 Descargar Excel ({nombre_nivel})",
        data=output,
        file_name=f"reporte_{nombre_nivel.lower().replace(' ', '_')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ------------- PROCESAMIENTO ------------
procesar_chat("Nivel 2", archivo_n2)
procesar_chat("Nivel 3", archivo_n3)
