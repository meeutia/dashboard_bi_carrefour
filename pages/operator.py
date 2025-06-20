import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from prophet import Prophet
from prophet.plot import plot_plotly
import matplotlib.pyplot as plt
from datetime import timedelta
from matplotlib.colors import LinearSegmentedColormap
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

from sqlalchemy import create_engine

engine = create_engine("postgresql+psycopg2://postgres:root@localhost/carrefour")

if 'data' not in st.session_state:
    st.error("Data belum dimuat! Silakan login terlebih dahulu.")
    st.stop()

main_data = st.session_state['data']
st.set_page_config(
    page_title="Dashboard Penjualan Carrefour",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load CSS
# CSS Styling
with open('styles.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Konversi kolom tanggal
main_data['full_date'] = pd.to_datetime(main_data['full_date'])

# Sidebar Filters
categories = ['Semua'] + list(main_data['category'].dropna().unique()) 
selected_category = st.sidebar.selectbox("Pilih Kategori", categories)

regions = ['Semua'] + list(main_data['region'].dropna().unique()) 
selected_region = st.sidebar.selectbox("Pilih Region", regions)

selected_date = st.sidebar.date_input("Pilih Tanggal", None)

date_range = st.sidebar.date_input(
    "Pilih Rentang Tanggal",
    [main_data['full_date'].min(), main_data['full_date'].max()]
)

# Filter data utama
filtered_data = main_data.copy()

if selected_category != 'Semua':
    filtered_data = filtered_data[filtered_data['category'] == selected_category]

if selected_region != 'Semua':
    filtered_data = filtered_data[filtered_data['region'] == selected_region]

if selected_date:
    filtered_data = filtered_data[filtered_data['full_date'].dt.date == selected_date]

if len(date_range) == 2:
    start, end = date_range
    filtered_data = filtered_data[
        (filtered_data['full_date'].dt.date >= start) & 
        (filtered_data['full_date'].dt.date <= end)
    ]
else:
    start, end = main_data['full_date'].min().date(), main_data['full_date'].max().date()

# Data minggu lalu
previous_start = start - timedelta(days=7)
previous_end = end - timedelta(days=7)
previous_data = main_data.copy()

if selected_category != 'Semua':
    previous_data = previous_data[previous_data['category'] == selected_category]

if selected_region != 'Semua':
    previous_data = previous_data[previous_data['region'] == selected_region]

previous_data = previous_data[
    (previous_data['full_date'].dt.date >= previous_start) & 
    (previous_data['full_date'].dt.date <= previous_end)
]

# Kalkulasi KPI
product_stock = filtered_data.groupby('product_name').agg({
    'quantity': 'sum',
    'sales': 'sum'
}).reset_index()

total_orders = filtered_data['order_id'].nunique()
total_products = len(product_stock)

previous_product_stock = previous_data.groupby('product_name').agg({
    'quantity': 'sum',
    'sales': 'sum'
}).reset_index()

previous_total_orders = previous_data['order_id'].nunique()
previous_total_products = len(previous_product_stock)

# Fungsi perubahan
def calculate_change(current, previous):
    if previous == 0:
        return 0
    return ((current - previous) / previous) * 100

def format_change(change):
    arrow = "⬆️" if change > 0 else "⬇️" if change < 0 else "➡️"
    return f"{arrow} {abs(change):.1f}%"

# Tampilkan KPI
st.markdown("## Key Performance Indicators")

col1, col2 = st.columns(2)

with col1:
    change_product = calculate_change(total_products, previous_total_products)
    st.markdown(f"""
    <div class="kpi-operational">
        <div class="kpi-label">Total Produk</div>
        <div class="kpi-value">{total_products:,}</div>
        <div class="kpi-change">{format_change(change_product)}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    change_order = calculate_change(total_orders, previous_total_orders)
    st.markdown(f"""
    <div class="kpi-operational">
        <div class="kpi-label">Total Order</div>
        <div class="kpi-value">{total_orders:,}</div>
        <div class="kpi-change">{format_change(change_order)}</div>
    </div>
    """, unsafe_allow_html=True)

# Charts
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)

    st.markdown("### Penjualan Produk")

    selected_view = st.selectbox(
    "",
    ["Top 10 Produk Terlaris", "Bottom 10 Produk Terendah"]
)

    # Proses data
    product_sales = (
        filtered_data.groupby('product_name')['sales']
        .sum()
        .sort_values(ascending=(selected_view == "Bottom 10 Produk Terendah"))
        .head(10)
        .reset_index()
    )

    # Warna dan judul disesuaikan
    color_scale = 'reds' if selected_view == "Bottom 10 Produk Terendah" else 'blues'

    # Buat chart horizontal
    fig = px.bar(
        product_sales.sort_values('sales'),
        x='sales',
        y='product_name',
        orientation='h',
        labels={'sales': 'Penjualan', 'product_name': 'Produk'},
        color='sales',
        color_continuous_scale=[[0, '#1e3c72'], [1, '#ffd700']],
    )

    fig.update_layout(
        height=400,
        xaxis_title="Total Penjualan",
        yaxis_title="",
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)




  


    
with col2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)

        st.markdown("### Penjualan per Region")
        region_sales = filtered_data.groupby('region')['sales'].sum().reset_index()
        region_sales['sales'] = region_sales['sales'].round().astype(int)
        
        fig_bar = px.bar(
            region_sales,
            x='region',
            y='sales',
            color='sales',
            labels={'sales': 'Total Penjualan', 'region': 'Region'},
            color_continuous_scale=[[0, '#1e3c72'], [1, '#ffd700']],

        )
        
        fig_bar.update_layout(
            height=400,
            xaxis_title='Region',
            yaxis_title='Total Penjualan',
            showlegend=False
        )
        
        st.plotly_chart(fig_bar, use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

# Additional charts
col1, col2 = st.columns(2)

with col1:
    st.markdown("### Pengiriman Terpopuler berdasarkan Ship Mode")

    # Koneksi DB dan query
    conn = engine.raw_connection()
    cursor = conn.cursor()

    query = """
    SELECT 
        dsm.ship_mode, 
        COUNT(*) AS total
    FROM fact_sales fs
    LEFT JOIN dim_ship_mode dsm ON fs.ship_mode_key = dsm.ship_mode_key
    GROUP BY dsm.ship_mode;
    """

    cursor.execute(query)
    results = cursor.fetchall()

    ship_modes = [r[0] for r in results]
    frequences = [r[1] for r in results]

    # Gradien warna dari biru tua ke emas
    cmap = LinearSegmentedColormap.from_list("custom", ["#1e3c72", "#ffd700"])
    n = len(frequences)
    colors = [cmap(i / (n - 1)) for i in range(n)]

    # Plot donut chart
    fig, ax = plt.subplots()
    ax.pie(
        frequences,
        labels=ship_modes,
        autopct='%1.1f%%',
        startangle=90,
        wedgeprops={'width': 1},  # Donut style
        colors=colors
    )

    st.pyplot(fig)

with col2:
    st.markdown("### Distribusi Penjualan Berdasarkan Kategori Produk")

    category_sales = (
        filtered_data.groupby('category')['sales']
        .sum()
        .reset_index()
        .sort_values(by='sales', ascending=False)
    )

    fig = px.pie(
        category_sales,
        names='category',
        values='sales',
        hole=0.4,
        color_discrete_sequence=['#1f77b4', '#ffcc00']  # Biru dan Kuning
    )

    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("### Tren Penjualan Multi-Produk")

# Ambil tanggal dari rentang filter
start_date = pd.to_datetime(date_range[0])
end_date = pd.to_datetime(date_range[1])

# Filter ulang berdasarkan rentang tanggal (jaga-jaga)
filtered_trend_data = filtered_data[
    (filtered_data['full_date'] >= start_date) &
    (filtered_data['full_date'] <= end_date)
]

# Ambil top 10 produk berdasarkan total sales dari data yang sudah difilter
top_products = (
    filtered_trend_data.groupby('product_name')['sales']
    .sum()
    .nlargest(10)
    .index
    .tolist()
)

# Buat figure dengan plotly graph objects untuk multiple lines
fig_multi_trend = go.Figure()

# Warna yang berbeda untuk setiap produk
colors = ['#1e3c72', '#ffd700', '#ff6b6b', '#2ed573', '#5742f5', '#8e44ad', '#e67e22', '#16a085', '#c0392b', '#34495e']

# Loop per produk
for i, product in enumerate(top_products):
    product_trend = filtered_trend_data[filtered_trend_data['product_name'] == product].groupby(
        filtered_trend_data['full_date'].dt.to_period('M')
    )['sales'].sum().reset_index()
    product_trend['full_date'] = product_trend['full_date'].dt.to_timestamp()

    fig_multi_trend.add_trace(go.Scatter(
        x=product_trend['full_date'],
        y=product_trend['sales'],
        mode='lines+markers',
        name=product[:20] + '...' if len(product) > 20 else product,
        line=dict(color=colors[i % len(colors)], width=2),
        marker=dict(size=6)
    ))

fig_multi_trend.update_layout(
    xaxis_title="Tanggal",
    yaxis_title="Penjualan",
    height=400,
    template='plotly_white',
    title="📈 Tren Penjualan Top 10 Produk",
    legend=dict(
        orientation="v",
        yanchor="top",
        y=1,
        xanchor="left",
        x=1.01
    ),
    margin=dict(r=150)
)

st.plotly_chart(fig_multi_trend, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)




st.markdown("### Stok Barang (model)")
query = """

    SELECT 
        dp.product_id, 
        dp.product_name, 
        DATE_TRUNC('month', dd.full_date) AS bulan, 
        SUM(fs.sales) AS total_penjualan, 
        AVG(fs.quantity) AS rata_rata_stok
    FROM fact_sales fs
    LEFT JOIN dim_product dp ON fs.product_id = dp.product_id
    LEFT JOIN dim_date dd ON fs.order_date_key = dd.date_key
    GROUP BY dp.product_id, dp.product_name, DATE_TRUNC('month', dd.full_date)
    ORDER BY dp.product_id, bulan;


        """
df = pd.read_sql(query, engine)


    # Load data hasil query ke df
df['bulan'] = pd.to_datetime(df['bulan'])
df['bulan_num'] = df['bulan'].dt.month + (df['bulan'].dt.year - df['bulan'].dt.year.min()) * 12

    # Simpan hasil prediksi
hasil_prediksi = []

    # Loop setiap produk
for produk_id in df['product_id'].unique():
    df_produk = df[df['product_id'] == produk_id].copy()

    if len(df_produk) < 4:
            # Skip produk dengan data terlalu sedikit
        continue

    X = df_produk[['bulan_num', 'total_penjualan']]
    y = df_produk['rata_rata_stok']

        # Train model
    model = RandomForestRegressor()
    model.fit(X, y)

        # Prediksi bulan depan
    bulan_terakhir = df_produk['bulan_num'].max()
    penjualan_terakhir = df_produk[df_produk['bulan_num'] == bulan_terakhir]['total_penjualan'].values[0]
    prediksi_stok = model.predict([[bulan_terakhir + 1, penjualan_terakhir]])[0]

    hasil_prediksi.append({
            'product_id': produk_id,
            'product_name': df_produk['product_name'].iloc[0],
            'prediksi_stok_bulan_depan': int(round(prediksi_stok))  # ubah jadi bilangan bulat
        })


    # Tampilkan hasil
df_hasil = pd.DataFrame(hasil_prediksi)
st.dataframe(df_hasil)
    