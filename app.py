import streamlit as st
import psycopg2
import pandas as pd
from sqlalchemy import create_engine

st.set_page_config(page_title="Login Page", page_icon=":lock:")

def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

local_css("styles.css")


with open('styles.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def init_connection():
    try:
        engine = create_engine("postgresql+psycopg2://postgres:root@localhost/carrefour")
        return engine
    except Exception as e:
        st.error(f"Error koneksi database: {e}")
        return None

def load_data():
    try:
        engine = init_connection()
        if engine is None:
            return None

        main_query = """
        SELECT 
            fs.*,
            dl.country, dl.city, dl.state, dl.region, dl.latitude, dl.longitude,
            dp.product_name, dp.category, dp.sub_category,
            dc.customer_name, dc.segment,
            dd.full_date, dd.day_of_week, dd.month, dd.quarter, dd.year,
            dsm.ship_mode
        FROM fact_sales fs
        LEFT JOIN dim_customer dc ON fs.customer_id = dc.customer_id
        LEFT JOIN dim_location dl ON dc.location_key = dl.location_key
        LEFT JOIN dim_product dp ON fs.product_id = dp.product_id
        LEFT JOIN dim_date dd ON fs.order_date_key = dd.date_key
        LEFT JOIN dim_ship_mode dsm ON fs.ship_mode_key = dsm.ship_mode_key
        """

        with engine.connect() as conn:
            df = pd.read_sql(main_query, conn)
            df['full_date'] = pd.to_datetime(df['full_date'])
            return df

    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

# Load data sekali, simpan di session
if 'data' not in st.session_state:
    st.session_state['data'] = load_data()

if st.session_state['data'] is None:
    st.stop()

col1, col2 = st.columns([1, 1])

with col1:
    st.title("")

    st.markdown("""
    <style>
    .animated-span {
        animation: colorChange 4s infinite;
        font-weight: bold;
    }

    @keyframes colorChange {
        0%   {color: #91b6fa;}
        25%  {color: #ff9a9e;}
        50%  {color: #f6d365;}
        75%  {color: #ffd700;}
        100% {color: #91b6fa;}
    }
    </style>

    <h1 style="font-family:Sans-Serif;">
        Visualisasi Dashboard Penjualan  
        <span class="animated-span">Carrefour USA</span> Berbasis Business Intelligence
    </h1>
    <p style="font-size:18px; color:#555;">
    Sebuah aplikasi interaktif yang menyajikan insight penjualan Carrefour USA melalui dashboard cerdas. Pengguna dapat mengeksplorasi tren penjualan, performa produk, dan perilaku pelanggan secara efisien dan informatif.
    </p>
    """, unsafe_allow_html=True)

    
    


    

    with open("styles.css") as css_file:
        css_styles = css_file.read()
        st.markdown(f"<style>{css_styles}</style>", unsafe_allow_html=True)

    if st.button("Mulai", key="start_button"):
       
        st.switch_page("pages/analitik.py") 

with col2:
    st.title("")
    st.image("assets/dashboard.svg", width=800)
