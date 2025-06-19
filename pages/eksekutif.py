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
st.sidebar.markdown("## 🔍 Filter Data")

date_range = st.sidebar.date_input(
    "Pilih Rentang Tanggal",
    value=[main_data['full_date'].min(), main_data['full_date'].max()],
    min_value=main_data['full_date'].min(),
    max_value=main_data['full_date'].max()
)

regions = ['Semua'] + list(main_data['region'].dropna().unique())
selected_region = st.sidebar.selectbox("Pilih Region", regions)

categories = ['Semua'] + list(main_data['category'].dropna().unique())
selected_category = st.sidebar.selectbox("Pilih Kategori Produk", categories)

segments = ['Semua'] + list(main_data['segment'].dropna().unique())
selected_segment = st.sidebar.selectbox("Pilih Segment Customer", segments)

# -------------------------------
# Apply Filter
# -------------------------------
filtered_data = main_data.copy()

if len(date_range) == 2:
    start_date = pd.to_datetime(date_range[0])
    end_date = pd.to_datetime(date_range[1])
    filtered_data = filtered_data[
        (filtered_data['full_date'] >= start_date) &
        (filtered_data['full_date'] <= end_date)
    ]

    # Data minggu sebelumnya
    delta = end_date - start_date
    prev_start = start_date - delta - timedelta(days=1)
    prev_end = start_date - timedelta(days=1)
    previous_data = main_data[
        (main_data['full_date'] >= prev_start) &
        (main_data['full_date'] <= prev_end)
    ]
else:
    previous_data = pd.DataFrame()  # Empty fallback

if selected_region != 'Semua':
    filtered_data = filtered_data[filtered_data['region'] == selected_region]
    previous_data = previous_data[previous_data['region'] == selected_region]

if selected_category != 'Semua':
    filtered_data = filtered_data[filtered_data['category'] == selected_category]
    previous_data = previous_data[previous_data['category'] == selected_category]

if selected_segment != 'Semua':
    filtered_data = filtered_data[filtered_data['segment'] == selected_segment]
    previous_data = previous_data[previous_data['segment'] == selected_segment]

# -------------------------------
# KPI Calculation
# -------------------------------
def calculate_change(current, previous):
    if previous == 0:
        return 0
    return ((current - previous) / previous) * 100

def format_change(change):
    arrow = "⬆️" if change > 0 else "⬇️" if change < 0 else "➡️"
    return f"{arrow} {abs(change):.1f}%"

# Current KPIs
total_sales = filtered_data['sales'].sum()
total_transactions = filtered_data['order_id'].nunique()
total_profit = filtered_data['profit'].sum()
avg_order_value = total_sales / total_transactions if total_transactions > 0 else 0

# Previous KPIs
prev_sales = previous_data['sales'].sum()
prev_transactions = previous_data['order_id'].nunique()
prev_profit = previous_data['profit'].sum()
prev_avg_order = prev_sales / prev_transactions if prev_transactions > 0 else 0

# Changes
sales_change = calculate_change(total_sales, prev_sales)
transactions_change = calculate_change(total_transactions, prev_transactions)
profit_change = calculate_change(total_profit, prev_profit)
aov_change = calculate_change(avg_order_value, prev_avg_order)

# -------------------------------
# Tampilkan KPI
# -------------------------------
st.markdown("## Key Performance Indicators")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-label">Total Penjualan</div>
        <div class="kpi-value">${total_sales:,.0f}</div>
        <div class="kpi-change">{format_change(sales_change)}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-label">Total Transaksi</div>
        <div class="kpi-value">{total_transactions:,}</div>
        <div class="kpi-change">{format_change(transactions_change)}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-label">Total Profit</div>
        <div class="kpi-value">${total_profit:,.0f}</div>
        <div class="kpi-change">{format_change(profit_change)}</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-label">Rata-rata Order</div>
        <div class="kpi-value">${avg_order_value:,.0f}</div>
        <div class="kpi-change">{format_change(aov_change)}</div>
    </div>
    """, unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown("### Tren Penjualan")
        # Kelompokkan per bulan (atau bisa diganti harian/mingguan)
        monthly_growth = filtered_data.groupby(filtered_data['full_date'].dt.to_period('M')).agg({
            'sales': 'sum'
        }).reset_index()

        monthly_growth['full_date'] = monthly_growth['full_date'].dt.to_timestamp()

        fig_growth = px.line(
            monthly_growth,
            x='full_date',
            y='sales',
            markers=True,
            labels={'full_date': 'Tanggal', 'sales': 'Total Penjualan'},
            color_discrete_sequence=['#1e3c72']
        )

        fig_growth.update_layout(height=400, template='plotly_white')
        st.plotly_chart(fig_growth, use_container_width=True)

        st.markdown('</div>', unsafe_allow_html=True)
    
# Profit Margin per Tahun (seluruh tahun)
with col2:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown("### Profit Margin")

    # Group data berdasarkan bulan dari kolom full_date
    margin_data = filtered_data.copy()
    margin_data['bulan'] = margin_data['full_date'].dt.to_period('M')

    # Hitung total sales dan profit per bulan
    margin_summary = margin_data.groupby('bulan').agg({
        'sales': 'sum',
        'profit': 'sum'
    }).reset_index()

    # Hitung profit margin
    margin_summary['profit_margin'] = (margin_summary['profit'] / margin_summary['sales']) * 100
    margin_summary['profit_margin'] = margin_summary['profit_margin'].round(2)

    # Ubah period ke timestamp agar bisa di-plot
    margin_summary['bulan'] = margin_summary['bulan'].dt.to_timestamp()

    # Visualisasi bar chart
    fig_margin_range = px.bar(
        margin_summary,
        x='bulan',
        y='profit_margin',
        color='profit_margin',
        color_continuous_scale=[[0, '#1e3c72'], [1, '#ffd700']],
        text='profit_margin'
    )

    fig_margin_range.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig_margin_range.update_layout(
        height=400,
        xaxis_title="Bulan",
        yaxis_title="Profit Margin (%)",
        template='plotly_white'
    )

    st.plotly_chart(fig_margin_range, use_container_width=True)


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