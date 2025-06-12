import streamlit as st
import psycopg2
import pandas as pd



users = {
    "operator@email.com": {"password": "operator123", "role": "operator"},
    "analitik@email.com": {"password": "analitik123", "role": "analitik"},
    "eksekutif@email.com": {"password": "eksekutif123", "role": "eksekutif"}
}

st.set_page_config(page_title="Login Page", page_icon=":lock:")

def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

local_css("styles.css")

# Fungsi koneksi database
@st.cache_resource
def init_connection():
    try:
        return psycopg2.connect(
            host="localhost",
            database="carrefour",
            user="postgres",
            password="12345678"
        )
    except Exception as e:
        st.error(f"Error koneksi database: {e}")
        return None

# Fungsi untuk memuat data
def load_data():
    conn = init_connection()
    if conn is None:
        return None

    try:
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
        
        main_data = pd.read_sql(main_query, conn)
        main_data['full_date'] = pd.to_datetime(main_data['full_date'])
        
        conn.close()
        return main_data
    
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

# Load data only if not already loaded
if 'data' not in st.session_state:
    st.session_state['data'] = load_data()

# Ensure that data is available before proceeding
if st.session_state['data'] is None:
    st.stop()
    
# Spacer biar turun ke bawah
st.markdown("<div style='height: 60px'></div>", unsafe_allow_html=True)

col1, col2 = st.columns([1.5, 1.2])

with col1:
    st.image("Onboarding.png", use_container_width=True)

with col2:
    st.markdown("<h2 style='text-align:center;'>Login</h2>", unsafe_allow_html=True)
    email = st.text_input("Email address")
    password = st.text_input("Password", type='password')
    login_btn = st.button("Login")

    if login_btn:
        if email in users and users[email]["password"] == password:
            st.session_state['user_role'] = users[email]['role']
            st.session_state['logged_in'] = True
            # Redirect ke page sesuai role
            if users[email]['role'] == "eksekutif":
                st.switch_page("pages/eksekutif.py")
            elif users[email]['role'] == "analitik":
                st.switch_page("pages/analitik.py")
            elif users[email]['role'] == "operator":
                st.switch_page("pages/operator.py")
        else:
            st.error("Email atau password salah.")

    st.markdown("<div class='small-text'>Hanya user terdaftar yang dapat login.</div>", unsafe_allow_html=True)
