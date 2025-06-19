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


st.sidebar.markdown("## 🔍 Filter Data")

date_range = st.sidebar.date_input(
    "Pilih Rentang Tanggal",
    value=[main_data['full_date'].min(), main_data['full_date'].max()],
    min_value=main_data['full_date'].min(),
    max_value=main_data['full_date'].max()
)

segments = ['Semua'] + list(main_data['segment'].dropna().unique())
selected_segment = st.sidebar.selectbox("Pilih Segment", segments)

# ================================
# Filter Data Saat Ini
# ================================
filtered_data = main_data.copy()

if len(date_range) == 2:
    start_date = pd.to_datetime(date_range[0])
    end_date = pd.to_datetime(date_range[1])
    filtered_data = filtered_data[
        (filtered_data['full_date'] >= start_date) &
        (filtered_data['full_date'] <= end_date)
    ]

if selected_segment != 'Semua':
    filtered_data = filtered_data[filtered_data['segment'] == selected_segment]

# ================================
# Data Minggu Sebelumnya
# ================================
delta = end_date - start_date
previous_start = start_date - delta - timedelta(days=1)
previous_end = start_date - timedelta(days=1)

previous_data = main_data[
    (main_data['full_date'] >= previous_start) &
    (main_data['full_date'] <= previous_end)
]

if selected_segment != 'Semua':
    previous_data = previous_data[previous_data['segment'] == selected_segment]

# ================================
# KPI Functions
# ================================
def calculate_conversion_rate(data):
    unique_customers = data['customer_id'].nunique()
    customer_frequency = data.groupby('customer_id')['order_id'].nunique()
    avg_frequency = customer_frequency.mean()
    estimated_visitors = unique_customers * (avg_frequency + 2)
    if estimated_visitors == 0:
        return 0
    return min((unique_customers / estimated_visitors) * 100, 100)

def calculate_churn_rate(data):
    if data.empty:
        return 0
    max_date = data['full_date'].max()
    churn_threshold = max_date - timedelta(days=90)
    last_tx = data.groupby('customer_id')['full_date'].max()
    churned = last_tx[last_tx < churn_threshold]
    if len(last_tx) == 0:
        return 0
    return (len(churned) / len(last_tx)) * 100

def calculate_change(current, previous):
    if previous == 0:
        return 0
    return ((current - previous) / previous) * 100

def format_change(val):
    arrow = "⬆️" if val > 0 else "⬇️" if val < 0 else "➡️"
    return f"{arrow} {abs(val):.1f}%"

# ================================
# KPI Perhitungan Saat Ini dan Minggu Sebelumnya
# ================================
avg_discount = filtered_data['discount'].mean() * 100
conversion_rate = calculate_conversion_rate(filtered_data)
customer_lifetime_value = filtered_data.groupby('customer_id')['sales'].sum().mean()
churn_rate = calculate_churn_rate(filtered_data)

prev_avg_discount = previous_data['discount'].mean() * 100
prev_conversion_rate = calculate_conversion_rate(previous_data)
prev_customer_ltv = previous_data.groupby('customer_id')['sales'].sum().mean()
prev_churn_rate = calculate_churn_rate(previous_data)

# Perubahan KPI (%)
discount_change = calculate_change(avg_discount, prev_avg_discount)
conversion_change = calculate_change(conversion_rate, prev_conversion_rate)
ltv_change = calculate_change(customer_lifetime_value, prev_customer_ltv)
churn_change = calculate_change(churn_rate, prev_churn_rate)

# ================================
# Tampilkan KPI
# ================================
st.markdown("## Key Performance Indicators")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="kpi-analytics">
        <div class="kpi-label">Rata-rata Diskon</div>
        <div class="kpi-value">{avg_discount:.1f}%</div>
        <div class="kpi-change">{format_change(discount_change)}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="kpi-analytics">
        <div class="kpi-label">Conversion Rate</div>
        <div class="kpi-value">{conversion_rate:.1f}%</div>
        <div class="kpi-change">{format_change(conversion_change)}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="kpi-analytics">
        <div class="kpi-label">Customer LTV</div>
        <div class="kpi-value">${customer_lifetime_value:.0f}</div>
        <div class="kpi-change">{format_change(ltv_change)}</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="kpi-analytics">
        <div class="kpi-label">Churn Rate</div>
        <div class="kpi-value">{churn_rate:.1f}%</div>
        <div class="kpi-change">{format_change(churn_change)}</div>
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
       
        xaxis_title="Range Diskon",
        yaxis=dict(title="Total Sales ($)", side="left"),
        yaxis2=dict(title="Profit Margin (%)", side="right", overlaying="y"),
        legend=dict(x=0.7, y=1.3)
    )

    fig_discount.update_layout(height=400, template='plotly_white')
    st.plotly_chart(fig_discount, use_container_width=True)

with col2:
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


st.markdown("### 🛒 Pembelian Gabungan (Market Basket Network Graph)")

# Ambil data order_id dan product_name dari filtered_data
basket_data = filtered_data[['order_id', 'product_name']]
import networkx as nx
import matplotlib.pyplot as plt
import streamlit as st
# Buat Graph
G = nx.Graph()

# Tambahkan edge antar produk dalam satu order
for order_id, group in basket_data.groupby('order_id'):
    products = group['product_name'].unique().tolist()
    for i in range(len(products)):
        for j in range(i + 1, len(products)):
            if G.has_edge(products[i], products[j]):
                G[products[i]][products[j]]['weight'] += 1
            else:
                G.add_edge(products[i], products[j], weight=1)



# Layout dan visualisasi
fig, ax = plt.subplots(figsize=(8, 6))
pos = nx.spring_layout(G, k=0.5, seed=42)
edges = G.edges(data=True)
weights = [attr['weight'] for _, _, attr in edges]

nx.draw_networkx_nodes(G, pos, ax=ax, node_color="#1e3c72", node_size=1000, alpha=0.8)
nx.draw_networkx_edges(G, pos, ax=ax, width=weights, alpha=0.6)
nx.draw_networkx_labels(G, pos, ax=ax, font_color='white', font_size=10)
plt.title("Network Graph Produk yang Dibeli Bersamaan")
plt.axis('off')

st.pyplot(fig)



st.markdown("""
<script>
function animateValue(el, start, end, duration, isPercent=false, isDollar=false) {
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        let value = Math.floor(progress * (end - start) + start);
        if (isDollar) {
            el.innerHTML = "$" + value;
        } else if (isPercent) {
            el.innerHTML = value + "%";
        } else {
            el.innerHTML = value;
        }
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };
    window.requestAnimationFrame(step);
}

// Delay to wait for elements to be available
setTimeout(() => {
    document.querySelectorAll('.kpi-value').forEach(el => {
        let raw = el.innerText.trim();
        let isPercent = raw.includes('%');
        let isDollar = raw.includes('$');
        let end = parseFloat(raw.replace(/[%$]/g, ''));

        // Reset to zero before animating
        el.innerHTML = isDollar ? "$0" : (isPercent ? "0%" : "0");
        animateValue(el, 0, Math.round(end), 1500, isPercent, isDollar);
    });
}, 500); // delay 500ms to let Streamlit finish rendering
</script>
""", unsafe_allow_html=True)
