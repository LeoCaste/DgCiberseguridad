
import os
import time
import streamlit as st
import redis
import pandas as pd

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")

@st.cache_resource
def get_redis_client():
    return redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

r = get_redis_client()

st.set_page_config(page_title="GitHub Minero", layout="wide")

st.title(f"Ranking en Tiempo Real: Top-{top_n} Funciones en GitHub")


st.sidebar.header("Parámetros")
top_n = st.sidebar.slider("Cantidad de palabras a mostrar:", min_value=5, max_value=50, value=15)
lang_filter = st.sidebar.radio("Filtrar por Lenguaje", ["Global", "Python", "Java"])


redis_key = "word_ranking"
if lang_filter == "Python":
    redis_key = "word_ranking_python"
elif lang_filter == "Java":
    redis_key = "word_ranking_java"

data = r.zrevrange(redis_key, 0, top_n - 1, withscores=True)

if data:
    df = pd.DataFrame(data, columns=["Palabra", "Frecuencia"])
    df.set_index("Palabra", inplace=True)
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.dataframe(df, use_container_width=True)
        
    with col2:
        st.bar_chart(df)
else:
    st.info("Esperando datos del iner. (Esto puede tomar unos segundos la primera vez)")

time.sleep(2)
st.rerun()