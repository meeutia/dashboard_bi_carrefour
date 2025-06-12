import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta
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
st.markdown('<div class="role-header">DASHBOARD ANALITIK</div>', unsafe_allow_html=True)

st.markdown(f'<div class="welcome-message">Selamat datang, Data Analis</div>', unsafe_allow_html=True)
# Filters
st.sidebar.markdown("## 🔍 Filter Data")


# Filter tanggal
date_range = st.sidebar.date_input(
    "Pilih Rentang Tanggal",
    value=[main_data['full_date'].min(), main_data['full_date'].max()],
    min_value=main_data['full_date'].min(),
    max_value=main_data['full_date'].max()
)

segments = ['Semua'] + list(main_data['segment'].dropna().unique())
selected_segment = st.sidebar.selectbox("Pilih Segment", segments)

# Apply filters

filtered_data = main_data.copy()

if len(date_range) == 2:
    filtered_data = filtered_data[
        (filtered_data['full_date'] >= pd.to_datetime(date_range[0])) &
        (filtered_data['full_date'] <= pd.to_datetime(date_range[1]))
    ]


if selected_segment != 'Semua':
    filtered_data = filtered_data[filtered_data['segment'] == selected_segment]




# ===============================
# PERHITUNGAN CONVERSION RATE
# ===============================
def calculate_conversion_rate(data):
    """
    Menghitung conversion rate berdasarkan:
    - Total unique customers yang melakukan pembelian
    - Estimasi total visitors (asumsi: 1 customer = 3-5 visits rata-rata)
    """
    # Hitung unique customers yang bertransaksi
    unique_customers = data['customer_id'].nunique()
    
    # Estimasi total visitors (asumsi konversi 15-25% adalah normal untuk retail)
    # Kita bisa menggunakan rumus: conversion_rate = customers / total_visitors
    # Atau estimasi berdasarkan frequency pembelian
    
    # Metode 1: Berdasarkan frekuensi pembelian per customer
    customer_frequency = data.groupby('customer_id')['order_id'].nunique()
    avg_frequency = customer_frequency.mean()
    
    # Asumsi: setiap customer visit 2-3x lebih banyak dari yang bertransaksi
    estimated_visitors = unique_customers * (avg_frequency + 2)
    conversion_rate = (unique_customers / estimated_visitors) * 100
    
    return min(conversion_rate, 100)  # Cap at 100%

# ===============================
# PERHITUNGAN CHURN RATE
# ===============================
def calculate_churn_rate(data):
    """
    Menghitung churn rate berdasarkan:
    - Customer yang tidak bertransaksi dalam 90 hari terakhir
    - Dari tanggal terakhir dalam dataset
    """
    # Ambil tanggal terakhir dalam dataset
    max_date = data['full_date'].max()
    
    # Tentukan periode churn (90 hari)
    churn_period = timedelta(days=90)
    churn_threshold = max_date - churn_period
    
    # Hitung last transaction date per customer
    customer_last_transaction = data.groupby('customer_id')['full_date'].max()
    
    # Hitung customer yang churn (tidak transaksi dalam 90 hari terakhir)
    churned_customers = customer_last_transaction[customer_last_transaction < churn_threshold]
    total_customers = len(customer_last_transaction)
    
    if total_customers == 0:
        return 0
    
    churn_rate = (len(churned_customers) / total_customers) * 100
    return churn_rate

# KPI Calculations
avg_discount = filtered_data['discount'].mean() * 100
conversion_rate = calculate_conversion_rate(filtered_data)
customer_lifetime_value = filtered_data.groupby('customer_id')['sales'].sum().mean()
churn_rate = calculate_churn_rate(filtered_data)

# KPI Cards
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="kpi-analytics">
        <div class="kpi-label">Rata-rata Diskon</div>
        <div class="kpi-value">{avg_discount:.1f}%</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="kpi-analytics">
        <div class="kpi-label">Conversion Rate</div>
        <div class="kpi-value">{conversion_rate:.1f}%</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="kpi-analytics">
        <div class="kpi-label">Customer LTV</div>
        <div class="kpi-value">${customer_lifetime_value:.0f}</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="kpi-analytics">
        <div class="kpi-label">Churn Rate</div>
        <div class="kpi-value">{churn_rate:.1f}%</div>
    </div>
    """, unsafe_allow_html=True)

# Detail Metrics (Optional - bisa ditampilkan di expander)
with st.expander("Detail Metrics"):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Customers", filtered_data['customer_id'].nunique())
        st.metric("Total Orders", filtered_data['order_id'].nunique())
    
    with col2:
        # Customer frequency analysis
        customer_freq = filtered_data.groupby('customer_id')['order_id'].nunique()
        st.metric("Avg Order Frequency", f"{customer_freq.mean():.1f}")
        st.metric("Repeat Customers", f"{(customer_freq > 1).sum()}")
    
    with col3:
        # Time-based metrics
        date_range = (filtered_data['full_date'].max() - filtered_data['full_date'].min()).days
        st.metric("Data Period (Days)", date_range)
        
        # Active customers (transaksi dalam 30 hari terakhir)
        max_date = filtered_data['full_date'].max()
        active_threshold = max_date - timedelta(days=30)
        active_customers = filtered_data[filtered_data['full_date'] >= active_threshold]['customer_id'].nunique()
        st.metric("Active Customers (30d)", active_customers)

# Charts
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown("### Efektivitas Diskon")

    # Buat bins untuk diskon
    main_data['discount_range'] = pd.cut(
        main_data['discount'], 
        bins=[0, 0.1, 0.2, 0.3, 0.4, 0.5, 1.0],
        labels=['0-10%', '10-20%', '20-30%', '30-40%', '40-50%', '50%+']
    )

    # Aggregate data per bin
    discount_analysis = main_data.groupby('discount_range').agg({
        'sales': ['sum', 'mean'],
        'profit': ['sum', 'mean'],
        'quantity': 'sum',
        'order_id': 'count'
    }).round(2)

    # Flatten column names
    discount_analysis.columns = ['total_sales', 'avg_sales', 'total_profit', 'avg_profit', 'total_qty', 'total_orders']
    discount_analysis = discount_analysis.reset_index()

    # Create Bar Chart Binned
    fig_discount = go.Figure()

    # Add bars untuk total sales
    fig_discount.add_trace(go.Bar(
        x=discount_analysis['discount_range'],
        y=discount_analysis['total_sales'],
        name='Total Sales',
        marker_color='#1e3c72',
        yaxis='y'
    ))

    # Add line untuk profit margin
    profit_margin = (discount_analysis['total_profit'] / discount_analysis['total_sales'] * 100)
    fig_discount.add_trace(go.Scatter(
        x=discount_analysis['discount_range'],
        y=profit_margin,
        mode='lines+markers',
        name='Profit Margin (%)',
        line=dict(color='#ffd700', width=3),
        yaxis='y2'
    ))

    # Update layout untuk dual axis
    fig_discount.update_layout(
        title="Efektivitas Diskon: Sales vs Profit Margin",
        xaxis_title="Range Diskon",
        yaxis=dict(title="Total Sales ($)", side="left"),
        yaxis2=dict(title="Profit Margin (%)", side="right", overlaying="y"),
        legend=dict(x=0.01, y=0.99)
    )

    fig_discount.update_layout(height=400, template='plotly_white')
    st.plotly_chart(fig_discount, use_container_width=True)

    # Insights for Bar Chart Binned
    st.markdown("**💡 Insights:**")
    best_range_idx = profit_margin.idxmax()
    best_range = discount_analysis.iloc[best_range_idx]['discount_range']
    best_margin = profit_margin.iloc[best_range_idx]

    st.markdown(f"• Range diskon **{best_range}** memberikan profit margin tertinggi: **{best_margin:.1f}%**")
    st.markdown(f"• Total transaksi dengan diskon: **{discount_analysis['total_orders'].sum():,}** orders")
    st.markdown('</div>', unsafe_allow_html=True)
    
with col2:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown("### Segmentasi Pelanggan")
    
    segment_data = filtered_data.groupby('segment').agg({
        'sales': 'sum',
        'customer_id': 'nunique'
    }).reset_index()
    
    fig_segment = px.pie(
        segment_data,
        values='sales',
        names='segment',
        color_discrete_sequence=['#1e3c72', '#ffd700', '#4a90e2']
    )
    fig_segment.update_layout(height=400)
    st.plotly_chart(fig_segment, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Additional analytics
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown("### Pola Musiman")
    
    seasonal_data = filtered_data.groupby(filtered_data['full_date'].dt.month).agg({
        'sales': 'sum',
        'quantity': 'sum'
    }).reset_index()
    seasonal_data['month_name'] = seasonal_data['full_date'].apply(
        lambda x: ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 
                  'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des'][x-1]
    )
    
    fig_seasonal = px.line(
        seasonal_data,
        x='month_name',
        y=['sales', 'quantity'],
        color_discrete_map={'sales': '#1e3c72', 'quantity': '#ffd700'}
    )
    fig_seasonal.update_layout(height=350, template='plotly_white')
    st.plotly_chart(fig_seasonal, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown("### Frekuensi Pembelian")
    
    # Histogram frekuensi pembelian per customer
    customer_frequency = filtered_data.groupby('customer_id')['order_id'].nunique().reset_index()
    customer_frequency.columns = ['customer_id', 'frequency']
    
    fig_frequency = px.histogram(
        customer_frequency,
        x='frequency',
        nbins=20,
        color_discrete_sequence=['#1e3c72']
    )
    fig_frequency.update_layout(
        height=350,
        template='plotly_white',
        xaxis_title="Frekuensi Pembelian",
        yaxis_title="Jumlah Customer"
    )
    st.plotly_chart(fig_frequency, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
