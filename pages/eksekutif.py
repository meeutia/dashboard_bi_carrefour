import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Pastikan data sudah ada dalam session state
if 'data' not in st.session_state:
    st.error("Data belum dimuat! Silakan login terlebih dahulu.")
    st.stop()

main_data = st.session_state['data']
# Konfigurasi halaman
st.set_page_config(
    page_title="Dashboard Penjualan Carrefour",
    layout="wide",
    initial_sidebar_state="expanded"
)
with open('styles.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


# Convert date columns
main_data['full_date'] = pd.to_datetime(main_data['full_date'])

# Header
st.markdown('<div class="role-header">👔 DASHBOARD EKSEKUTIF</div>', unsafe_allow_html=True)

st.markdown(f'<div class="welcome-message">Selamat datang, Eksekutif</div>', unsafe_allow_html=True)
# Filters
# Sidebar untuk filter
st.sidebar.markdown("## 🔍 Filter Data")

# Filter tanggal
date_range = st.sidebar.date_input(
    "Pilih Rentang Tanggal",
    value=[main_data['full_date'].min(), main_data['full_date'].max()],
    min_value=main_data['full_date'].min(),
    max_value=main_data['full_date'].max()
)

# Filter region
regions = ['Semua'] + list(main_data['region'].dropna().unique())
selected_region = st.sidebar.selectbox("Pilih Region", regions)

# Filter kategori produk
categories = ['Semua'] + list(main_data['category'].dropna().unique())
selected_category = st.sidebar.selectbox("Pilih Kategori Produk", categories)

# Filter segment customer
segments = ['Semua'] + list(main_data['segment'].dropna().unique())
selected_segment = st.sidebar.selectbox("Pilih Segment Customer", segments)

# Apply filters
filtered_data = main_data.copy()

if len(date_range) == 2:
    filtered_data = filtered_data[
        (filtered_data['full_date'] >= pd.to_datetime(date_range[0])) &
        (filtered_data['full_date'] <= pd.to_datetime(date_range[1]))
    ]

if selected_region != 'Semua':
    filtered_data = filtered_data[filtered_data['region'] == selected_region]

if selected_category != 'Semua':
    filtered_data = filtered_data[filtered_data['category'] == selected_category]

if selected_segment != 'Semua':
    filtered_data = filtered_data[filtered_data['segment'] == selected_segment]

# KPI Cards
st.markdown("## Key Performance Indicators")

col1, col2, col3, col4 = st.columns(4)

total_sales = filtered_data['sales'].sum()
total_transactions = filtered_data['order_id'].nunique()
total_profit = filtered_data['profit'].sum()
avg_order_value = total_sales / total_transactions if total_transactions > 0 else 0

with col1:
    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-label">Total Penjualan</div>
        <div class="kpi-value">${total_sales:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-label">Total Transaksi</div>
        <div class="kpi-value">{total_transactions:,}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-label">Total Profit</div>
        <div class="kpi-value">${total_profit:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-label">Rata-rata Order</div>
        <div class="kpi-value">${avg_order_value:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

# Row 1: Tren Penjualan dan Profit Margin per Kategori untuk seluruh tahun
col1, col2 = st.columns(2)

with col1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown("### Tren Penjualan per Bulan")
        
        monthly_data = filtered_data.groupby(filtered_data['full_date'].dt.to_period('M')).agg({
            'sales': 'sum',
            'profit': 'sum'
        }).reset_index()
        monthly_data['full_date'] = monthly_data['full_date'].dt.to_timestamp()
        
        fig_trend = px.line(
            monthly_data, 
            x='full_date', 
            y=['sales', 'profit'],
            color_discrete_map={'sales': '#1e3c72', 'profit': '#ffd700'}
        )
        fig_trend.update_layout(height=400, template='plotly_white')
        st.plotly_chart(fig_trend, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
# Profit Margin per Tahun (seluruh tahun)
with col2:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown("### Profit Margin per Tahun")
    
    # Grouping data berdasarkan tahun
    yearly_data = filtered_data.groupby('year').agg({
        'sales': 'sum',
        'profit': 'sum'
    }).reset_index()
    
    # Menghitung profit margin
    yearly_data['profit_margin'] = (yearly_data['profit'] / yearly_data['sales'] * 100).round(2)
    
    # Membuat bar chart untuk profit margin per tahun
    fig_margin_yearly = px.bar(
        yearly_data,
        x='year',
        y='profit_margin',
        title="Profit Margin per Year (%)",
        color='profit_margin',
        color_continuous_scale=[[0, '#1e3c72'], [1, '#ffd700']],
        text='profit_margin'
    )
    
    fig_margin_yearly.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig_margin_yearly.update_layout(
        height=400,
        xaxis_title="Tahun",
        yaxis_title="Profit Margin (%)",
        template='plotly_white'
    )
    
    st.plotly_chart(fig_margin_yearly, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Row 2: Regional Performance
st.markdown("## Data Tabel Detail")

# Selectbox untuk memilih jenis tabel
table_option = st.selectbox(
    "Pilih jenis analisis detail:",
    ["Summary by Region", "Summary by Category", "Summary by Customer Segment", "Monthly Performance"]
)

if table_option == "Summary by Region":
    summary_data = filtered_data.groupby('region').agg({
        'sales': 'sum',
        'profit': 'sum',
        'quantity': 'sum',
        'order_id': 'nunique',
        'customer_id': 'nunique'
    }).reset_index()
    summary_data.columns = ['Region', 'Total Sales', 'Total Profit', 'Total Quantity', 'Total Orders', 'Unique Customers']

elif table_option == "Summary by Category":
    summary_data = filtered_data.groupby('category').agg({
        'sales': 'sum',
        'profit': 'sum',
        'quantity': 'sum',
        'order_id': 'nunique'
    }).reset_index()
    summary_data.columns = ['Category', 'Total Sales', 'Total Profit', 'Total Quantity', 'Total Orders']

elif table_option == "Summary by Customer Segment":
    summary_data = filtered_data.groupby('segment').agg({
        'sales': 'sum',
        'profit': 'sum',
        'quantity': 'sum',
        'customer_id': 'nunique'
    }).reset_index()
    summary_data.columns = ['Segment', 'Total Sales', 'Total Profit', 'Total Quantity', 'Unique Customers']

else:  # Monthly Performance
    summary_data = filtered_data.groupby(filtered_data['full_date'].dt.to_period('M')).agg({
        'sales': 'sum',
        'profit': 'sum',
        'quantity': 'sum',
        'order_id': 'nunique'
    }).reset_index()
    summary_data['full_date'] = summary_data['full_date'].astype(str)
    summary_data.columns = ['Month', 'Total Sales', 'Total Profit', 'Total Quantity', 'Total Orders']

st.dataframe(summary_data, use_container_width=True)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p>Dashboard Business Intelligence Carrefour | Dibuat Kelompok 4</p>
        <p>Last updated: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
    </div>
    """, 
    unsafe_allow_html=True
)
