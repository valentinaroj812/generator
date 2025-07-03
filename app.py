import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from fuzzywuzzy import process
import io

st.set_page_config(page_title="Generador de Equivalencias C21", layout="wide")
st.title("🔄 Generador Automático de Equivalencias - CENTURY 21")

excel_file = st.file_uploader("📤 Sube el archivo Excel generado por 21 Online", type=["xlsx"])
links_file = st.file_uploader("🔗 Sube el archivo .txt con todos los links de oficinas", type=["txt"])
min_score = st.slider("🎯 Score mínimo de coincidencia", 0, 100, 80)

def obtener_asesores_de_web(links):
    asesores_web = set()
    for url in links:
        try:
            r = requests.get(url, timeout=10)
            soup = BeautifulSoup(r.content, "html.parser")
            asesores = soup.select("div.agent-info h5")
            for a in asesores:
                nombre = a.text.strip()
                if nombre:
                    asesores_web.add(nombre)
        except Exception as e:
            st.warning(f"⚠️ Error en {url}: {e}")
    return list(asesores_web)

if excel_file and links_file:
    try:
        df = pd.read_excel(excel_file, skiprows=1)
        captadores = df["Asesor Captador"].dropna().astype(str).str.strip()
        colocadores = df["Asesor Colocador"].dropna().astype(str).str.strip()
        nombres_excel = pd.Series(pd.concat([captadores, colocadores]).unique())

        links = links_file.read().decode("utf-8").splitlines()
        links = [l.strip() for l in links if l.strip()]

        with st.spinner("🔍 Obteniendo asesores desde la web..."):
            nombres_web = obtener_asesores_de_web(links)

        if not nombres_web:
            st.error("❌ No se extrajo ningún asesor de los sitios web. Verifica los links y la estructura HTML.")
        else:
            st.success(f"✅ {len(nombres_web)} asesores encontrados desde los sitios web.")
            with st.expander("👀 Ver asesores extraídos"):
                st.write(nombres_web)

            resultados = []
            for nombre in nombres_excel:
                coincidencia = process.extractOne(nombre, nombres_web)
                if coincidencia:
                    match, score = coincidencia
                    resultados.append([nombre, match if score >= min_score else "", score])
                else:
                    resultados.append([nombre, "", 0])

            df_resultado = pd.DataFrame(resultados, columns=["Nombre en Excel", "Nombre en Web", "Score"])
            st.success("✅ Equivalencias generadas correctamente.")
            st.dataframe(df_resultado)

            buffer = io.BytesIO()
            df_resultado.to_csv(buffer, index=False)
            buffer.seek(0)
            st.download_button("📥 Descargar CSV", buffer, "equivalencias_nombres_sugeridas.csv")

    except Exception as e:
        st.error(f"❌ Error al procesar archivos: {e}")
else:
    st.info("Por favor, sube ambos archivos para comenzar.")
