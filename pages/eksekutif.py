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
        st.markdown("### Pertumbuhan Penjualan per Tahun")
        
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

col3, col4 = st.columns(2)

with col3:
    
        summary_data = filtered_data.groupby('region').agg({
            'sales': 'sum',
            'profit': 'sum',
            'quantity': 'sum',
            'order_id': 'nunique',
            'customer_id': 'nunique'
        }).reset_index()
        summary_data.columns = ['Region', 'Total Sales', 'Total Profit', 'Total Quantity', 'Total Orders', 'Unique Customers']

        st.subheader("Penjualan per Wilayah (Ranking)")

        # Sort berdasarkan total sales (descending)
        summary_data_sorted = summary_data.sort_values(by='Total Sales', ascending=False)

       
        fig = px.bar(
            summary_data_sorted,
            x='Total Sales',
            y='Region',
            orientation='h',
            color='Region',
            text='Total Sales',
            labels={'Total Sales': 'Total Penjualan'},
            height=500,
            color_discrete_sequence=['#1f77b4', '#ffcc00']  # Biru dan kuning
        )

        fig.update_traces(
            texttemplate='%{text:.2s}',
            textposition='outside'
        )

        fig.update_layout(
            yaxis={'categoryorder': 'total ascending'}
        )

        st.plotly_chart(fig, use_container_width=True)


   
with col4:
    st.markdown("### Persebaran Penjualan per State (USA)")
    
    # Prepare data for US state-level choropleth
    state_data = filtered_data[filtered_data['country'] == 'United States'].groupby('state').agg({
        'sales': 'sum',
        'profit': 'sum',
        'customer_id': 'nunique',
        'order_id': 'nunique'
    }).reset_index()
    
    if not state_data.empty:
        state_data['profit_margin'] = (state_data['profit'] / state_data['sales'] * 100).round(2)
        
        # Dictionary untuk mapping nama state ke kode
        state_code_map = {
            'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR',
            'California': 'CA', 'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE',
            'Florida': 'FL', 'Georgia': 'GA', 'Hawaii': 'HI', 'Idaho': 'ID',
            'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA', 'Kansas': 'KS',
            'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD',
            'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS',
            'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV',
            'New Hampshire': 'NH', 'New Jersey': 'NJ', 'New Mexico': 'NM', 'New York': 'NY',
            'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH', 'Oklahoma': 'OK',
            'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC',
            'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT',
            'Vermont': 'VT', 'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV',
            'Wisconsin': 'WI', 'Wyoming': 'WY', 'District of Columbia': 'DC'
        }
        
        # Map state names to codes
        state_data['state_code'] = state_data['state'].map(state_code_map)
        
        # Filter only states with valid codes
        valid_state_data = state_data[state_data['state_code'].notna()]
        
        if not valid_state_data.empty:
            # Create US state choropleth map
            fig_usa = px.choropleth(
                valid_state_data,
                locations='state_code',
                color='sales',
                hover_name='state',
                hover_data={
                    'sales': ':$,.0f',
                    'customer_id': ':,',
                    'order_id': ':,',
                    'profit_margin': ':.1f%',
                    'state_code': False
                },
                color_continuous_scale=[[0, '#1e3c72'], [1, '#ffd700']],
                locationmode='USA-states'
            )
            
            fig_usa.update_layout(
                height=400,
                geo_scope='usa',
                geo=dict(
                    showlakes=True,
                    lakecolor='rgb(255, 255, 255)'
                )
            )
            
            st.plotly_chart(fig_usa, use_container_width=True)
        else:
            st.warning("Choropleth map tidak dapat ditampilkan, menampilkan bar chart sebagai alternatif")
            
            top_states = state_data.sort_values('sales', ascending=False).head(15)
            
            fig_bar = px.bar(
                top_states,
                x='sales',
                y='state',
                orientation='h',
                title="Top 15 States - Total Penjualan",
                color='sales',
                color_continuous_scale='Reds'
            )
            fig_bar.update_layout(
                height=400,
                yaxis={'categoryorder': 'total ascending'}
            )
            st.plotly_chart(fig_bar, use_container_width=True)
            
    else:
        st.info("Data US State tidak tersedia atau kosong")

    st.markdown('</div>', unsafe_allow_html=True)