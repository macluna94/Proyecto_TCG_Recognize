import os
import json
import sqlite3
import pandas as pd
import streamlit as st
import requests
from PIL import Image

# Configuración básica de la página
st.set_page_config(page_title="TCG Recognize", page_icon="🃏", layout="wide")

API_URL = "http://127.0.0.1:8000/api/v1/scan"
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
DB_PATH = os.path.join(DATA_DIR, "tcg_recognize.db")
METADATA_PATH = os.path.join(DATA_DIR, "metadata_set.json")

def load_history():
    """Conecta a la base de datos SQLite y devuelve el historial."""
    if not os.path.exists(DB_PATH):
        return pd.DataFrame()
    
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT scanned_at, image_path, card_name, card_number, match_type, match_score FROM scan_history ORDER BY scanned_at DESC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if not df.empty:
        df['scanned_at'] = pd.to_datetime(df['scanned_at']).dt.strftime('%Y-%m-%d %H:%M')
    return df

def load_metadata_urls():
    """Carga el JSON del set y extrae un mapa de {numero_carta: url_imagen}."""
    if not os.path.exists(METADATA_PATH):
        return {}
    with open(METADATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        return {str(card.get("number")): card.get("image_url") for card in data}

st.title("🃏 TCG Recognize - Gestión de Colección")

# Crear sistema de pestañas
tab1, tab2, tab3, tab4 = st.tabs([
    "🔍 Escáner", 
    "📊 Dashboard", 
    "📜 Historial", 
    "📖 Álbum de Colección"
])

# ==========================================
# PESTAÑA 1: ESCÁNER
# ==========================================
with tab1:
    st.write("Sube una foto de tu carta de Pokémon (Set *30th Celebration*) para escanearla.")
    uploaded_file = st.file_uploader("Arrastra tu carta aquí o selecciona un archivo", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Imagen original", width=350)

        if st.button("🔍 Escanear Carta", type="primary"):
            with st.spinner("Procesando imagen..."):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                try:
                    response = requests.post(API_URL, files=files)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("success"):
                            st.success("¡Carta identificada con éxito!")
                            card_info = data["match"]["card"]
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric(label="Nombre", value=card_info["name"])
                                st.metric(label="Número", value=card_info["number"])
                            with col2:
                                st.metric(label="Rareza", value=card_info.get("rarity", "N/A"))
                                st.metric(label="Precisión", value=f"{data['match']['score']}%")
                        else:
                            st.warning("No se logró emparejar la carta con suficiente confianza.")
                    else:
                        st.error("Error en el servidor de visión.")
                except requests.exceptions.ConnectionError:
                    st.error("No se pudo conectar con el backend.")

# ==========================================
# PESTAÑA 2: DASHBOARD
# ==========================================
with tab2:
    df = load_history()
    if df.empty:
        st.info("Aún no hay cartas escaneadas en tu colección.")
    else:
        df_success = df[df['match_type'] != 'none']
        st.subheader("Resumen de Colección")
        col1, col2, col3 = st.columns(3)
        total_scans = len(df)
        unique_cards = df_success['card_number'].nunique() if not df_success.empty else 0
        TOTAL_SET_CARDS = 50 
        col1.metric("Cartas Totales Escaneadas", total_scans)
        col2.metric("Cartas Únicas", unique_cards)
        col3.metric("Progreso del Set", f"{(unique_cards / TOTAL_SET_CARDS) * 100:.1f}%")

        if not df_success.empty:
            st.subheader("Top Duplicados")
            st.bar_chart(df_success['card_name'].value_counts().head(5))

# ==========================================
# PESTAÑA 3: HISTORIAL
# ==========================================
with tab3:
    df = load_history()
    if df.empty:
        st.info("El historial está vacío.")
    else:
        st.subheader("Registro detallado")
        search = st.text_input("Buscar carta:")
        if search:
            df = df[df['card_name'].str.contains(search, case=False, na=False)]
        st.dataframe(df[['scanned_at', 'card_name', 'card_number', 'match_score', 'match_type']], use_container_width=True, hide_index=True)

# ==========================================
# PESTAÑA 4: ÁLBUM VISUAL CON ARTE OFICIAL
# ==========================================
with tab4:
    df = load_history()
    url_map = load_metadata_urls() # Cargamos el mapeo de imágenes de Scrydex
    
    if df.empty:
        st.info("Tu álbum está vacío.")
    else:
        df_success = df[df['match_type'] != 'none']
        if df_success.empty:
            st.info("Aún no tienes cartas identificadas.")
        else:
            df_unique = df_success.drop_duplicates(subset=['card_number'], keep='first')
            df_unique['card_num_int'] = df_unique['card_number'].str.extract('(\d+)').astype(float)
            df_unique = df_unique.sort_values('card_num_int')
            
            st.header("📖 Álbum: 30th Celebration")
            st.write(f"Visualizando **{len(df_unique)}** cartas únicas con su arte digital oficial.")
            st.markdown("---")
            
            cols_per_row = 4
            df_unique = df_unique.reset_index(drop=True)
            
            for i in range(0, len(df_unique), cols_per_row):
                cols = st.columns(cols_per_row)
                for j in range(cols_per_row):
                    if i + j < len(df_unique):
                        row = df_unique.iloc[i + j]
                        with cols[j]:
                            # Buscar la URL en el JSON usando el número de la carta guardado en BD
                            card_url = url_map.get(str(row['card_number']))
                            
                            if card_url:
                                st.image(card_url, use_container_width=True)
                            else:
                                st.warning("Arte digital no disponible")
                                
                            st.markdown(f"**{row['card_name']}**")
                            st.caption(f"#{row['card_number']}")