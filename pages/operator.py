import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

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

st.markdown(f'<div class="welcome-message">Selamat datang, Operator</div>', unsafe_allow_html=True)

categories = ['Semua'] + list(main_data['category'].dropna().unique())
selected_category = st.sidebar.selectbox("Pilih Kategori", categories)

regions = ['Semua'] + list(main_data['region'].dropna().unique())
selected_region = st.sidebar.selectbox("Pilih Region", regions)

# Apply filters


filtered_data = main_data.copy()
if selected_category != 'Semua':
    filtered_data = filtered_data[filtered_data['category'] == selected_category]
if selected_region != 'Semua':
    filtered_data = filtered_data[filtered_data['region'] == selected_region]

#################
# Simulasi stok barang (karena tidak ada di database)
product_stock = filtered_data.groupby('product_name').agg({
    'quantity': 'sum',
    'sales': 'sum'
}).reset_index()

# KPI Cards
col1, col2 = st.columns(2)
    
total_products = len(product_stock)
    
with col1:
        st.markdown(f"""
        <div class="kpi-operational">
            <div class="kpi-label">Total Produk</div>
            <div class="kpi-value">{total_products:,}</div>
        </div>
        """, unsafe_allow_html=True)
    
with col2:
        st.markdown(f"""
        <div class="kpi-operational">
            <div class="kpi-label">Stok Rendah</div>
            <div class="kpi-value">{total_products:,}</div>
        </div>
        """, unsafe_allow_html=True)
    

# Charts
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown("### Stok Barang (model)")
    
    
with col2:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown("### 🏪 Penjualan per Region")
    
    region_sales = filtered_data.groupby('region')['sales'].sum().reset_index()
    
    fig_heatmap = px.treemap(
        region_sales,
        path=['region'],
        values='sales',
        color='sales',
        color_continuous_scale=[[0, '#1e3c72'], [1, '#ffd700']],
        title="Heatmap Penjualan per Region"
    )
    fig_heatmap.update_layout(height=400)
    st.plotly_chart(fig_heatmap, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Additional charts
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown("### Tren Penjualan Multi-Produk")
    
    # Ambil top 5 produk berdasarkan total sales
    top_products = filtered_data.groupby('product_name')['sales'].sum().nlargest(10).index.tolist()
    
    # Buat figure dengan plotly graph objects untuk multiple lines
    fig_multi_trend = go.Figure()
    
    # Warna yang berbeda untuk setiap produk
    colors = ['#1e3c72', '#ffd700', '#ff6b6b', '#2ed573', '#5742f5']
    
    for i, product in enumerate(top_products):
        product_trend = filtered_data[filtered_data['product_name'] == product].groupby(
            filtered_data['full_date'].dt.to_period('M')
        )['sales'].sum().reset_index()
        product_trend['full_date'] = product_trend['full_date'].dt.to_timestamp()
        
        fig_multi_trend.add_trace(go.Scatter(
            x=product_trend['full_date'],
            y=product_trend['sales'],
            mode='lines+markers',
            name=product[:20] + '...' if len(product) > 20 else product,  # Potong nama produk jika terlalu panjang
            line=dict(color=colors[i % len(colors)], width=2),
            marker=dict(size=6)
        ))
    
    fig_multi_trend.update_layout(
        title="Tren Penjualan Top 10 Produk",
        xaxis_title="Tanggal",
        yaxis_title="Penjualan",
        height=350,
        template='plotly_white',
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.01
        ),
        margin=dict(r=150)  # Beri ruang untuk legend
    )
    
    st.plotly_chart(fig_multi_trend, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown("### Produk Terlaris & Terendah")
    
    # Buat data untuk tabel produk performance
    product_performance = filtered_data.groupby('product_name').agg({
        'quantity': 'sum',
        'sales': 'sum'
    }).reset_index()
    
    # Ambil top 5 dan bottom 5
    top_5 = product_performance.nlargest(5, 'quantity').copy()
    bottom_5 = product_performance.nsmallest(5, 'quantity').copy()
    
    # Buat ranking dari 1 sampai total produk
    total_products = len(product_performance)
    product_performance_sorted = product_performance.sort_values('quantity', ascending=False).reset_index(drop=True)
    product_performance_sorted['Ranking'] = range(1, len(product_performance_sorted) + 1)
    
    # Ambil ranking untuk top 5
    top_5_with_rank = product_performance_sorted.head(5)
    
    # Ambil ranking untuk bottom 5
    bottom_5_with_rank = product_performance_sorted.tail(5)
    
    # Gabungkan
    combined_table = pd.concat([top_5_with_rank, bottom_5_with_rank])
    
    # Format tabel
    display_table = combined_table[['Ranking', 'product_name', 'quantity', 'sales']].copy()
    display_table.columns = ['Rank', 'Nama Produk', 'Qty Terjual', 'Total Sales']
    
    # Format angka
    display_table['Qty Terjual'] = display_table['Qty Terjual'].apply(lambda x: f"{x:,}")
    display_table['Total Sales'] = display_table['Total Sales'].apply(lambda x: f"${x:,.2f}")
    
    # Styling untuk tabel
    def highlight_ranking(row):
        rank = row['Rank']
        if rank <= 5:  
            return ['background-color: #c3d4f5; color: #1e3c72'] * len(row)
        else:  # Bottom 5 - merah muda
            return ['background-color: #f8d7da; color: #721c24'] * len(row)
    
    styled_table = display_table.style.apply(highlight_ranking, axis=1)
    
    # Tampilkan tabel
    st.dataframe(
        styled_table,
        use_container_width=True,
        hide_index=True,
        height=350
    )
    
    # Tambahkan informasi ringkas
    st.markdown("""
    <div style='font-size: 12px; color: #666; margin-top: 10px;'>
    💡 <strong>Info:</strong> Tabel menampilkan 5 produk terlaris (ranking 1-5) dan 5 produk dengan penjualan terendah berdasarkan quantity terjual.
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)