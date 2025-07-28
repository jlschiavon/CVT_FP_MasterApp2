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

def carga_ALDS(df):
    df = pd.read_csv(r"C:\Users\jorge\OneDrive - Instituto Tecnologico y de Estudios Superiores de Monterrey\Desktop\streamlit_reporte_ALDS\05 - Overview (Parts worked in stations per shift).csv", skiprows=14)
    df.dropna(how="all", axis=1, inplace=True)
    df.dropna(how="all", axis=0, inplace=True)
    df = df.loc[:, ~df.columns.str.contains("Unnamed")]
    df["Station"] = df["Station"].where(df["Station"].str.startswith("Reckstation", na=False)).ffill()

    partes = orden_partes
    ALDS = []

    for shift in shifts:
        df_shift = df[df["Shift"] == shift]
        for parte in partes:
            if parte not in df.columns:
                continue
            filtro = df_shift[parte] != 0
            total_serie = df_shift.loc[filtro, "Serie Parts"].sum() if filtro.any() else 0
            total_rework = df_shift.loc[filtro, "Rework Parts"].sum() if filtro.any() else 0
            ALDS.append({"Shift": shift, "Parte": parte, "ALDS Serie": total_serie, "ALDS Rework": total_rework})

    df_resultados = pd.DataFrame(ALDS).set_index(["Shift", "Parte"]).reindex(index_completo, fill_value=0).reset_index()


# ------------------ INTERFAZ ----------------------
from PIL import Image
import os
import base64

# Rutas fijas
RUTA_LOGO = "assets/LogoSchaeffler.png"
RUTA_PRODUCTO = "assets/producto.jpg"

# Función para codificar imágenes en base64
def obtener_base64(ruta_imagen):
    with open(ruta_imagen, "rb") as f:
        return base64.b64encode(f.read()).decode()

# Cargar imágenes si existen
img_base64_producto = obtener_base64(RUTA_PRODUCTO) if os.path.exists(RUTA_PRODUCTO) else None
logo_base64 = obtener_base64(RUTA_LOGO) if os.path.exists(RUTA_LOGO) else None

# HTML y estilos
if img_base64_producto or logo_base64:
    st.markdown("""
        <style>
            .titulo-principal {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                text-align: center;
                font-size: 2.2vw;
                font-weight: bold;
                padding: 1vh 0;
                z-index: 1001;
                background: rgba(255, 255, 255, 0.8);
            }

            .banner-superior {
                position: fixed;
                top: 20vh;
                left: 0;
                width: 100%;
                height: 10vh;
                background-size: cover;
                background-position: center;
                opacity: 0.7;
                z-index: 998;
            }

            .logo-fijo {
                position: fixed;
                top: 0.5vh;
                right: 4vw;
                width: 10vw;
                height: auto;
                z-index: 999;
                background-color: rgba(255, 255, 255, 0.8);
                border-radius: 8px;
                padding: 4px;
            }

            .contenido {
                margin-top: 25vh;
            }
        </style>
    """, unsafe_allow_html=True)

    # Mostrar título
    st.markdown('<div class="titulo-principal">CVT Machine Downtime Analyzer</div>', unsafe_allow_html=True)

    # Imagen de producto como banner
    if img_base64_producto:
        st.markdown(
            f'<div class="banner-superior" style="background-image: url(\'data:image/jpeg;base64,{img_base64_producto}\');"></div>',
            unsafe_allow_html=True
        )

    # Logo de la empresa
    if logo_base64:
        st.markdown(
            f'<img class="logo-fijo" src="data:image/png;base64,{logo_base64}"/>',
            unsafe_allow_html=True
        )

    # Abrimos contenedor para desplazar contenido hacia abajo
    st.markdown('<div class="contenido">', unsafe_allow_html=True)

st.markdown('<div class="titulo-principal">CUADRAJE</div>', unsafe_allow_html=True)

st.set_page_config(page_title="Analizador Paros", layout="wide")

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

st.markdown('</div>', unsafe_allow_html=True)
