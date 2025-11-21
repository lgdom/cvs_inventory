import streamlit as st
import pandas as pd
import io

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Buscador Farmacia", page_icon="💊", layout="wide")

st.title("💊 Buscador de Existencias Tijuana")
st.markdown("Sube el inventario del día y busca por **Nombre, Clave o Sustancia**.")

# --- 1. CARGAR CATÁLOGO DE SUSTANCIAS (CACHEADO) ---
# Usamos cache para que no lo recargue cada vez que tocas un botón
@st.cache_data
def cargar_sustancias():
    # AQUÍ: Si despliegas la app, subirás este archivo junto con el código
    # Por ahora simulamos la carga o lo lees de una URL pública si tienes
    try:
        df = pd.read_csv('LISTASUSTANCIAS.csv', encoding='latin-1')
        
        # Limpieza rápida (igual que en el script anterior)
        df.columns = df.columns.str.strip().str.replace('ï»¿', '')
        if 'CLAVE' in df.columns:
            df = df.rename(columns={'CLAVE': 'CODIGO'})
        else:
             df.rename(columns={df.columns[0]: 'CODIGO'}, inplace=True)
             
        df['CODIGO'] = df['CODIGO'].astype(str).str.strip()
        return df[['CODIGO', 'SUSTANCIA ACTIVA']]
    except Exception as e:
        st.error(f"Error cargando sustancias: {e}")
        return pd.DataFrame()

# Cargamos sustancias (asumiendo que el archivo está en la misma carpeta de la app)
df_sub = cargar_sustancias()

# --- 2. SUBIR ARCHIVO DEL DÍA ---
uploaded_file = st.file_uploader("📤 Sube el Excel/CSV de hoy", type=['csv', 'xlsx'])

if uploaded_file is not None:
    try:
        # Lógica "Todo Terreno" para leer el archivo
        if uploaded_file.name.endswith('.csv'):
            try:
                df_inv = pd.read_csv(uploaded_file, header=1, encoding='latin-1')
            except:
                uploaded_file.seek(0)
                df_inv = pd.read_csv(uploaded_file, header=1, encoding='utf-8')
        else:
            df_inv = pd.read_excel(uploaded_file, header=1)

        # Seleccionar Tijuana y Limpiar
        # Buscamos columnas por índice para no fallar
        df_tj = df_inv.iloc[:, [0, 1, 5, 6]].copy()
        df_tj.columns = ['CODIGO', 'PRODUCTO', 'CORTA_CAD', 'EXISTENCIA']
        df_tj = df_tj.dropna(subset=['CODIGO'])
        df_tj['CODIGO'] = df_tj['CODIGO'].astype(str).str.strip()

        # Cruce con Sustancias
        df_final = pd.merge(df_tj, df_sub, on='CODIGO', how='left')
        df_final['SUSTANCIA ACTIVA'] = df_final['SUSTANCIA ACTIVA'].fillna('---')
        
        # Ordenar columnas bonitas
        df_final = df_final[['CODIGO', 'PRODUCTO', 'SUSTANCIA ACTIVA', 'EXISTENCIA', 'CORTA_CAD']]

        # --- 3. EL BUSCADOR INTERACTIVO ---
        busqueda = st.text_input("🔍 ¿Qué buscas?", placeholder="Ej: Paracetamol, V0102, S02...")

        if busqueda:
            # Filtro mágico (case insensitive)
            filtro = (
                df_final['CODIGO'].str.contains(busqueda, case=False, na=False) |
                df_final['PRODUCTO'].str.contains(busqueda, case=False, na=False) |
                df_final['SUSTANCIA ACTIVA'].str.contains(busqueda, case=False, na=False)
            )
            resultados = df_final[filtro]
            st.success(f"Encontrados: {len(resultados)}")
            st.dataframe(resultados, use_container_width=True)
        else:
            st.info("👆 Escribe arriba para filtrar. Mostrando primeros 10 registros:")
            st.dataframe(df_final.head(10), use_container_width=True)

    except Exception as e:
        st.error(f"Hubo un error procesando el archivo: {e}")

else:
    st.warning("Esperando archivo...")
