import streamlit as st
import pandas as pd
import io

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Buscador Farmacia", page_icon="⚡", layout="wide")

st.title("⚡ Buscador Rápido de Existencias")
st.markdown("Sube el inventario y busca al instante.")

# --- 1. CARGAR CATÁLOGO DE SUSTANCIAS (CACHEADO) ---
@st.cache_data
def cargar_sustancias():
    try:
        # Asegúrate de subir este archivo al mismo lugar que app.py
        df = pd.read_csv('LISTASUSTANCIAS.csv', encoding='latin-1')
        
        # Limpieza de cabeceras
        df.columns = df.columns.str.strip().str.replace('ï»¿', '')
        
        if 'CLAVE' in df.columns:
            df = df.rename(columns={'CLAVE': 'CODIGO'})
        elif len(df.columns) > 0:
             df.rename(columns={df.columns[0]: 'CODIGO'}, inplace=True)
             
        df['CODIGO'] = df['CODIGO'].astype(str).str.strip()
        return df[['CODIGO', 'SUSTANCIA ACTIVA']]
    except Exception as e:
        st.error(f"Error cargando sustancias: {e}")
        return pd.DataFrame()

df_sub = cargar_sustancias()

# --- 2. SUBIR Y PROCESAR ARCHIVO (CACHEADO TEMPORALMENTE) ---
# Usamos el estado de sesión para no recargar el excel si solo cambias la búsqueda
if 'df_final' not in st.session_state:
    st.session_state.df_final = None

uploaded_file = st.file_uploader("📤 Sube el Excel/CSV de hoy", type=['csv', 'xlsx'])

if uploaded_file is not None:
    # Solo procesamos si el archivo cambió o no se ha cargado
    if st.session_state.df_final is None:
        try:
            with st.spinner('Procesando inventario...'):
                # Lectura Todo Terreno
                if uploaded_file.name.endswith('.csv'):
                    try:
                        df_inv = pd.read_csv(uploaded_file, header=1, encoding='latin-1')
                    except:
                        uploaded_file.seek(0)
                        df_inv = pd.read_csv(uploaded_file, header=1, encoding='utf-8')
                else:
                    df_inv = pd.read_excel(uploaded_file, header=1)

                # Limpieza Tijuana
                df_tj = df_inv.iloc[:, [0, 1, 5, 6]].copy()
                df_tj.columns = ['CODIGO', 'PRODUCTO', 'CORTA_CAD', 'EXISTENCIA']
                df_tj = df_tj.dropna(subset=['CODIGO'])
                df_tj['CODIGO'] = df_tj['CODIGO'].astype(str).str.strip()

                # Cruce
                df_merged = pd.merge(df_tj, df_sub, on='CODIGO', how='left')
                df_merged['SUSTANCIA ACTIVA'] = df_merged['SUSTANCIA ACTIVA'].fillna('---')
                
                # --- OPTIMIZACIÓN DE VELOCIDAD ---
                # 1. Creamos una columna "ÍNDICE" con todo el texto junto
                # 2. Lo convertimos a MINÚSCULAS de una vez (pre-procesamiento)
                # Esto evita que Python tenga que convertir cada vez que buscas.
                df_merged['SEARCH_INDEX'] = (
                    df_merged['CODIGO'].astype(str) + " " + 
                    df_merged['PRODUCTO'].astype(str) + " " + 
                    df_merged['SUSTANCIA ACTIVA'].astype(str)
                ).str.lower()

                # Guardamos columnas limpias para mostrar
                cols_mostrar = ['CODIGO', 'PRODUCTO', 'SUSTANCIA ACTIVA', 'EXISTENCIA', 'CORTA_CAD', 'SEARCH_INDEX']
                st.session_state.df_final = df_merged[cols_mostrar]
                
        except Exception as e:
            st.error(f"Error procesando archivo: {e}")

# --- 3. EL BUSCADOR VELOZ ---
if st.session_state.df_final is not None:
    df = st.session_state.df_final
    
    # Input de búsqueda
    busqueda = st.text_input("🔍 ¿Qué buscas?", placeholder="Escribe nombre, clave o sustancia...")

    if busqueda:
        # Búsqueda optimizada: Solo busca en la columna 'SEARCH_INDEX'
        # y convertimos lo que escribes a minúsculas una sola vez.
        mask = df['SEARCH_INDEX'].str.contains(busqueda.lower(), na=False)
        resultados = df[mask]
        
        # Mostramos resultados (sin la columna fea de índice)
        st.success(f"Encontrados: {len(resultados)}")
        st.dataframe(
            resultados.drop(columns=['SEARCH_INDEX']), 
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("👆 Esperando búsqueda...")
        # Mostrar primeros 10 sin el índice
        st.dataframe(
            df.head(10).drop(columns=['SEARCH_INDEX']), 
            use_container_width=True,
            hide_index=True
        )
