import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import os
import glob
import base64

from logic import (
    BULAN_ORDER, BULAN_MAP,
    load_raw, build_dataset, train_models, forecast_next_month,
    rupiah, to_excel_bytes, generate_laporan_docx, generate_laporan_pdf,
    DOCX_OK, REPORTLAB_OK,
)
import plotly.graph_objects as go
import plotly.express as px

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def find_asset(basename):
    """Cari file di folder script berdasarkan nama saja, tidak peduli ekstensinya
    (mis. banner_kopi.jpg / .jpeg / .png / .webp semua akan ketemu)."""
    matches = sorted(glob.glob(os.path.join(SCRIPT_DIR, basename + ".*")))
    return matches[0] if matches else None

FAVICON = find_asset("favicon")
BANNER_LOGIN = find_asset("preview_banner_dashboard")
BANNER_MAIN = find_asset("preview_banner_dashboard")

st.set_page_config(
    page_title="Dashboard Prediksi Pendapatan - Sumatra Roastery Medan",
    page_icon=FAVICON if FAVICON else "☕",
    layout="wide",
)

PRIMARY = "#0F6B5C"
ACCENT = "#B5502D"
GRID = "#e5e0d8"

CREAM = "#FAF6F0"
CREAM_DARK = "#F0E8DC"
ESPRESSO = "#3B2A20"
ESPRESSO_SOFT = "#5C4633"
BORDER = "#D9C9B4"
GOLD = "#E0A526"
GOLD_DARK = "#C98A1B"

st.markdown(f"""
<style>
/* ---- Base app background & typography ---- */
.stApp {{
    background: linear-gradient(135deg, #EAF2EF 0%, {CREAM} 45%, #FBEEE4 100%) !important;
    background-attachment: fixed;
}}
html, body, [class*="css"] {{
    color: {ESPRESSO} !important;
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
}}

/* ---- Kill the stray white top toolbar ---- */
[data-testid="stHeader"] {{
    background-color: transparent !important;
}}
[data-testid="stToolbar"] {{
    background-color: transparent;
}}

/* ---- Naikkan konten utama supaya sejajar dengan bagian atas sidebar ---- */
[data-testid="stMainBlockContainer"], .block-container {{
    padding-top: 1.5rem !important;
}}

/* ---- Sidebar ---- */
[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, #C9E6DF 0%, {CREAM_DARK} 55%, #F7D9BE 100%) !important;
    border-right: 1px solid {BORDER};
}}
[data-testid="stSidebar"] * {{
    color: {ESPRESSO} !important;
}}

/* ---- Headings, captions, labels, markdown text ---- */
h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown, .stCaption {{
    color: {ESPRESSO} !important;
}}
[data-testid="stCaptionContainer"] {{
    color: {ESPRESSO_SOFT} !important;
}}

/* ---- Text inputs & password fields ---- */
.stTextInput input, .stNumberInput input {{
    background-color: #FFFFFF !important;
    color: {ESPRESSO} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 6px;
}}
.stTextInput input::placeholder {{
    color: #A8998A !important;
}}
.stTextInput label, .stNumberInput label, .stSlider label, .stSelectbox label, .stFileUploader label {{
    color: {ESPRESSO} !important;
    font-weight: 600;
}}

/* ---- Selectbox ---- */
.stSelectbox div[data-baseweb="select"] > div {{
    background-color: #FFFFFF !important;
    color: {ESPRESSO} !important;
    border: 1px solid {BORDER} !important;
}}

/* ---- Buttons (target inner text explicitly so it doesn't get overridden) ---- */
.stButton button, .stFormSubmitButton button {{
    background-color: {ESPRESSO} !important;
    border: none !important;
    border-radius: 6px;
    font-weight: 600;
}}
.stButton button p, .stFormSubmitButton button p,
.stButton button div, .stFormSubmitButton button div,
.stButton button span, .stFormSubmitButton button span {{
    color: {CREAM} !important;
}}
.stButton button:hover, .stFormSubmitButton button:hover {{
    background-color: {ESPRESSO_SOFT} !important;
}}

/* ---- Download buttons (Unduh Laporan) ---- */
.stDownloadButton button {{
    background-color: #2E8F84 !important;
    border: none !important;
    border-radius: 6px;
    font-weight: 600;
}}
.stDownloadButton button p,
.stDownloadButton button div,
.stDownloadButton button span {{
    color: #FFFFFF !important;
}}
.stDownloadButton button:hover {{
    background-color: #256F66 !important;
}}

/* ---- Sembunyikan ikon link kecil di samping heading ---- */
[data-testid="stHeaderActionElements"] {{
    display: none !important;
}}

/* ---- Neutralize Chrome/browser autofill styling on inputs ---- */
input:-webkit-autofill,
input:-webkit-autofill:hover,
input:-webkit-autofill:focus {{
    -webkit-box-shadow: 0 0 0px 1000px #FFFFFF inset !important;
    -webkit-text-fill-color: {ESPRESSO} !important;
    caret-color: {ESPRESSO} !important;
}}

/* ---- Banner images: cap height so they never dominate the page ---- */
[data-testid="stImage"] img {{
    max-height: 300px;
    width: 100%;
    object-fit: cover;
    border-radius: 18px;
}}

/* ---- Slider track/thumb ---- */
[data-testid="stSlider"] [role="slider"] {{
    background-color: {PRIMARY} !important;
}}

/* ---- File uploader box ---- */
[data-testid="stFileUploaderDropzone"] {{
    background-color: #FFFFFF !important;
    border: 1.5px dashed {BORDER} !important;
}}
[data-testid="stFileUploaderDropzone"] * {{
    color: {ESPRESSO_SOFT} !important;
}}

/* ---- Tabs: bar berwarna, hanya tab aktif yang berbentuk kotak ---- */
[data-testid="stTabs"] {{
    background: transparent !important;
}}
.stTabs [data-baseweb="tab-list"],
.stTabs div[role="tablist"],
[data-testid="stTabs"] [data-baseweb="tab-list"],
[data-testid="stTabs"] div[role="tablist"] {{
    display: inline-flex !important;
    width: fit-content !important;
    max-width: 100%;
    gap: 4px !important;
    border-bottom: none !important;
    background: linear-gradient(135deg, #C9E6DF 0%, {CREAM_DARK} 55%, #F7D9BE 100%) !important;
    background-color: #DCEEE8 !important;
    border: 1px solid {BORDER} !important;
    border-radius: 14px !important;
    padding: 8px !important;
    box-shadow: 0 4px 12px rgba(59, 42, 32, 0.08);
    flex-wrap: nowrap;
}}
/* Bar navigasi utama (top-level) dipaksa melebar penuh lewat JS di bawah;
   sub-tab bersarang (mis. RF / LightGBM / Performa) sengaja dibiarkan
   sependek isinya (fit-content) sesuai aturan di atas. */
.stTabs [data-baseweb="tab"],
.stTabs [role="tab"] {{
    color: {ESPRESSO} !important;
    background: transparent !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 7px 10px !important;
    transition: background 0.15s ease, color 0.15s ease, box-shadow 0.15s ease;
    outline: none !important;
    box-shadow: none !important;
    text-decoration: none !important;
}}
.stTabs [data-baseweb="tab"]:focus,
.stTabs [role="tab"]:focus,
.stTabs [data-baseweb="tab"]:focus-visible,
.stTabs [role="tab"]:focus-visible {{
    outline: none !important;
}}
.stTabs [data-baseweb="tab"] *,
.stTabs [role="tab"] * {{
    font-weight: 700 !important;
    font-size: 0.78rem !important;
    white-space: nowrap !important;
}}
.stTabs [data-baseweb="tab"]:hover:not([aria-selected="true"]),
.stTabs [role="tab"]:hover:not([aria-selected="true"]) {{
    color: {ESPRESSO} !important;
    background: rgba(255, 255, 255, 0.45) !important;
}}
.stTabs [aria-selected="true"] {{
    color: #FFFFFF !important;
    background: linear-gradient(135deg, #4FA89D 0%, #2E7268 100%) !important;
    box-shadow: 0 3px 8px rgba(46, 143, 132, 0.35) !important;
    border-bottom: none !important;
}}
.stTabs [aria-selected="true"]:hover,
.stTabs [aria-selected="true"]:focus,
.stTabs [aria-selected="true"]:focus-visible {{
    color: #FFFFFF !important;
    background: linear-gradient(135deg, #4FA89D 0%, #2E7268 100%) !important;
    outline: none !important;
}}
.stTabs [aria-selected="true"] * {{
    color: #FFFFFF !important;
}}
.stTabs [data-baseweb="tab-highlight"] {{
    display: none !important;
}}
.stTabs [data-baseweb="tab-border"] {{
    display: none !important;
}}

/* ---- Metrics ---- */
[data-testid="stMetric"] {{
    background-color: #FFFFFF;
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 14px 16px;
}}
[data-testid="stMetricLabel"] {{
    color: {ESPRESSO_SOFT} !important;
}}
[data-testid="stMetricValue"] {{
    color: {ESPRESSO} !important;
}}

/* ---- Dataframes ---- */
[data-testid="stDataFrame"] {{
    border: 1px solid {BORDER};
    border-radius: 6px;
}}

/* ---- Expander ---- */
[data-testid="stExpander"] {{
    background-color: #FFFFFF;
    border: 1px solid {BORDER};
    border-radius: 8px;
}}
</style>
""", unsafe_allow_html=True)


# ---------- LOGIN DUA PERAN ----------
from login import require_login

require_login({
    "PRIMARY": PRIMARY,
    "ACCENT": ACCENT,
    "CREAM": CREAM,
    "ESPRESSO": ESPRESSO,
    "ESPRESSO_SOFT": ESPRESSO_SOFT,
    "BORDER": BORDER,
})
@st.cache_data
def get_base64_image(path, _mtime):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

with st.sidebar:
    st.markdown(f"Login sebagai: **{st.session_state.role}**")
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.role = None
        st.rerun()
    st.divider()

def render_hero_banner():
    """Render banner foto hero. Dipanggil hanya di dalam tab Dashboard,
    supaya banner hilang saat pindah ke tab lain."""
    if BANNER_MAIN:
        photo_b64 = get_base64_image(BANNER_MAIN, os.path.getmtime(BANNER_MAIN))
        photo_ext = os.path.splitext(BANNER_MAIN)[1].replace(".", "")
        if photo_ext == "jpg":
            photo_ext = "jpeg"

        banner_height = 360

        banner_html = f"""
        <html>
        <head>
        <style>
            html, body {{
                margin:0;
                padding:0;
                width:100%;
                background:transparent;
                overflow:hidden;
            }}
            .hero-banner{{
                position:relative;
                width:100%;
                height:{banner_height}px;
                border-radius:18px;
                overflow:hidden;
                background:#0d3b2e;
                box-sizing:border-box;
            }}
            .hero-image{{
                position:absolute;
                left:0;
                top:0;
                width:100%;
                height:100%;
                object-fit:cover;
                object-position:center;
                display:block;
            }}
        </style>
        </head>
        <body>
            <div class="hero-banner">
                <img class="hero-image" src="data:image/{photo_ext};base64,{photo_b64}">
            </div>
        </body>
        </html>
        """

        components.html(banner_html, height=banner_height, scrolling=False)
    else:
        st.title("☕ Dashboard Analisis Tren & Prediksi Pendapatan")
        st.caption("Sumatra Roastery Medan — Random Forest vs LightGBM")
        st.warning(
            "File banner `preview_banner_dashboard.*` tidak ditemukan di folder aplikasi "
            f"({SCRIPT_DIR}). Pastikan file gambar ini sudah di-upload/push ke repository "
            "yang sama dengan app.py, sejajar (bukan di dalam subfolder lain)."
        )


IS_PENELITI = st.session_state.role == "Peneliti"

with st.sidebar:
    st.header("Data & Pengaturan")
    uploaded = None
    split_ratio = 0.8
    if IS_PENELITI:
        uploaded = st.file_uploader("Unggah dataset (.xlsx)", type=["xlsx"])
        split_ratio = st.slider("Proporsi data training", 0.6, 0.9, 0.8, 0.05)
    else:
        st.caption("Data & pengaturan hanya dapat diubah oleh Peneliti. Anda melihat hasil analisis terkini.")
    st.caption("Sesuai BAB III: time-based split 80:20")

def find_local_dataset():
    candidates = glob.glob(os.path.join(SCRIPT_DIR, "*.xlsx"))
    return candidates[0] if candidates else None

data_path = uploaded if uploaded is not None else find_local_dataset()

if data_path is None:
    st.warning("Tidak ada file .xlsx ditemukan di folder yang sama dengan app.py. Unggah dataset lewat sidebar di kiri.")
    st.stop()

try:
    daily, per_jenis, rekap_raw = load_raw(data_path)
except Exception as e:
    st.error(f"Gagal membaca dataset: {e}")
    st.stop()

df, rekap, avg_overall = build_dataset(daily, per_jenis, rekap_raw)
results, fi, test_out, split_periode = train_models(df, split_ratio)
forecast_df, next_bulan_nama, next_tahun = forecast_next_month(df)

IS_PEMILIK = st.session_state.role == "Pemilik/Pengelola"

if IS_PEMILIK:
    tab0, tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🏠 Dashboard", "📋 Data Aktual", "📈 Analisis Tren", "🔮 Prediksi & Evaluasi", "⭐ Feature Importance", "📅 Perkiraan Bulan Berikutnya", "📄 Laporan"])
else:
    tab0, tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏠 Dashboard", "📋 Data Aktual", "📈 Analisis Tren", "🔮 Prediksi & Evaluasi", "⭐ Feature Importance", "📅 Perkiraan Bulan Berikutnya"])
    tab6 = None

components.html("""
<script>
function attachTabAutoScroll() {
    try {
        const doc = window.parent.document;
        const containers = doc.querySelectorAll('[data-testid="stTabs"]');
        containers.forEach(function(container) {
            if (container.dataset.autoscrollBound) return;
            container.dataset.autoscrollBound = "1";
            container.addEventListener('click', function(e) {
                setTimeout(function() {
                    const rect = container.getBoundingClientRect();
                    const y = rect.top + doc.defaultView.scrollY - 70;
                    doc.defaultView.scrollTo({top: y, behavior: 'smooth'});
                }, 80);
            });
        });
    } catch (err) {
        // akses cross-origin diblokir browser, abaikan
    }
}

function stretchTopLevelTabBar() {
    try {
        const doc = window.parent.document;

        // Batas kiri = tepi kanan sidebar (0 kalau sidebar sedang disembunyikan).
        const sidebarEl = doc.querySelector('[data-testid="stSidebar"]');
        let leftBoundary = 0;
        if (sidebarEl) {
            const sbRect = sidebarEl.getBoundingClientRect();
            if (sbRect.width > 0) leftBoundary = sbRect.right;
        }

        // Batas kanan = tepi kanan area konten utama yang sesungguhnya
        // (bukan lebar jendela browser mentah — itu ternyata lebih lebar dari
        // area yang benar-benar dipakai, makanya sebelumnya berhenti sebelum
        // garis ikon titik-tiga di kanan atas).
        let mainEl = doc.querySelector('[data-testid="stMain"]') || doc.querySelector('section.main');
        if (!mainEl) {
            const appViewContainer = doc.querySelector('[data-testid="stAppViewContainer"]');
            if (appViewContainer) {
                const kids = appViewContainer.querySelectorAll(':scope > section, :scope > div');
                for (let i = 0; i < kids.length; i++) {
                    const testid = kids[i].getAttribute('data-testid');
                    if (testid === 'stSidebar' || testid === 'stHeader') continue;
                    mainEl = kids[i];
                    break;
                }
            }
        }
        let rightBoundary = doc.documentElement.clientWidth;
        if (mainEl) {
            const mr = mainEl.getBoundingClientRect();
            if (mr.right > 0) rightBoundary = mr.right;
        }

        const allTabsBlocks = doc.querySelectorAll('[data-testid="stTabs"]');
        allTabsBlocks.forEach(function(block) {
            // Lewati sub-tab yang bersarang di dalam tab lain (mis. RF/LightGBM/Performa)
            // — itu sengaja dibiarkan sependek isinya, tidak di-stretch.
            const parentBlock = block.parentElement ? block.parentElement.closest('[data-testid="stTabs"]') : null;
            if (parentBlock) return;

            const tabList = block.querySelector('[data-baseweb="tab-list"]') || block.querySelector('[role="tablist"]');
            if (!tabList) return;

            // Reset dulu supaya pengukuran lebar alami akurat (mis. saat resize window).
            tabList.style.removeProperty('margin-left');
            tabList.style.removeProperty('margin-right');
            tabList.style.removeProperty('width');

            const tabRect = tabList.getBoundingClientRect();
            const leftGap = tabRect.left - leftBoundary;
            const rightGap = rightBoundary - tabRect.right;
            if (Math.abs(leftGap) < 1 && Math.abs(rightGap) < 1) return;

            tabList.style.setProperty('box-sizing', 'border-box', 'important');
            tabList.style.setProperty('margin-left', (-leftGap) + 'px', 'important');
            tabList.style.setProperty('margin-right', (-rightGap) + 'px', 'important');
            tabList.style.setProperty('width', (tabRect.width + leftGap + rightGap) + 'px', 'important');
        });
    } catch (err) {
        // akses cross-origin diblokir browser, abaikan
    }
}

attachTabAutoScroll();
stretchTopLevelTabBar();
setInterval(attachTabAutoScroll, 800);
setInterval(stretchTopLevelTabBar, 500);
window.addEventListener('resize', stretchTopLevelTabBar);
</script>
""", height=1)

with tab0:
    render_hero_banner()
    st.markdown(f"### Selamat datang, **{st.session_state.role}** 👋")
    st.write(
        "Dashboard ini menyajikan analisis tren pendapatan penjualan kopi serta prediksi "
        "pendapatan bulanan **Sumatra Roastery Medan** menggunakan dua algoritma machine "
        "learning, yaitu **Random Forest** dan **LightGBM**, lengkap dengan perbandingan "
        "performa dan variabel yang paling berpengaruh terhadap hasil prediksi."
    )

    total_pendapatan_all = rekap['Total Pendapatan (Rp)'].sum()
    periode_awal_label = f"{rekap['Bulan'].iloc[0][:3]} {rekap['Tahun'].iloc[0]}"
    periode_akhir_label = f"{rekap['Bulan'].iloc[-1][:3]} {rekap['Tahun'].iloc[-1]}"
    best_model_home = pd.DataFrame(results).T['MAE'].idxmin()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Pendapatan Historis", rupiah(total_pendapatan_all))
    c2.metric("Rata-rata Pendapatan / Bulan", rupiah(avg_overall))
    c3.metric("Periode Data", f"{periode_awal_label} – {periode_akhir_label}")
    c4.metric("Model Terbaik (MAE terendah)", best_model_home)

    st.divider()

    st.markdown("#### 🧭 Panduan Navigasi")
    panduan = """
- **📋 Data Aktual** — data mentah dan rekap pendapatan yang menjadi dasar seluruh analisis.
- **📈 Analisis Tren** — grafik tren pendapatan bulanan dan kontribusi tiap jenis kopi.
- **🔮 Prediksi & Evaluasi** — hasil prediksi Random Forest & LightGBM dibandingkan dengan data aktual, beserta metrik evaluasinya.
- **⭐ Feature Importance** — variabel yang paling berpengaruh terhadap hasil prediksi.
- **📅 Perkiraan Bulan Berikutnya** — estimasi pendapatan untuk periode berikutnya.
"""
    if IS_PEMILIK:
        panduan += "- **📄 Laporan** — unduh ringkasan laporan penjualan dalam format Word atau PDF.\n"
    st.markdown(panduan)

    st.info("Gunakan menu tab di bagian atas untuk berpindah antar bagian dashboard.")

with tab1:
    st.subheader("Rekap Pendapatan Bulanan")
    rekap_show = rekap[['Tahun', 'Bulan', 'Total Pendapatan (Rp)', 'kategori_tren']].copy()
    rekap_show['Total Pendapatan (Rp)'] = rekap_show['Total Pendapatan (Rp)'].apply(rupiah)
    rekap_show = rekap_show.rename(columns={'kategori_tren': 'Kategori Tren'})
    st.dataframe(rekap_show, use_container_width=True, hide_index=True)

    st.subheader("Pendapatan per Jenis Kopi per Bulan")
    per_jenis_show = per_jenis.copy()
    per_jenis_show['Total Pendapatan (Rp)'] = per_jenis_show['Total Pendapatan (Rp)'].apply(rupiah)
    per_jenis_show['% dari Total Bulan'] = (per_jenis_show['% dari Total Bulan'] * 100).round(2).astype(str) + '%'
    st.dataframe(per_jenis_show, use_container_width=True, hide_index=True)

    st.subheader("Data Transaksi Harian")
    daily_show = daily.copy()
    daily_show['Harga (Rp)'] = daily_show['Harga (Rp)'].apply(rupiah)
    daily_show['Pendapatan (Rp)'] = daily_show['Pendapatan (Rp)'].apply(rupiah)
    st.dataframe(daily_show, use_container_width=True, hide_index=True, height=400)
    st.download_button("⬇️ Download Excel — Data Transaksi Harian",
                        data=to_excel_bytes(daily_show, "Transaksi Harian"),
                        file_name="data_transaksi_harian.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

with tab2:
    st.subheader("Tren Pendapatan Bulanan (2023–2025)")
    labels = [f"{b[:3]} {t}" for b, t in zip(rekap['Bulan'], rekap['Tahun'])]
    nilai_tinggi = np.where(rekap['kategori_tren'] == 'Tinggi', rekap['Total Pendapatan (Rp)'], np.nan)
    nilai_rendah = np.where(rekap['kategori_tren'] == 'Rendah', rekap['Total Pendapatan (Rp)'], np.nan)

    fig = go.Figure()
    fig.add_trace(go.Bar(x=labels, y=nilai_tinggi, marker_color=PRIMARY,
                          name="Tinggi (≥ rata-rata)"))
    fig.add_trace(go.Bar(x=labels, y=nilai_rendah, marker_color=ACCENT,
                          name="Rendah (< rata-rata)"))
    fig.add_hline(y=avg_overall, line_dash="dash", line_color="#888",
                  annotation_text=f"Rata-rata: {rupiah(avg_overall)}")
    fig.update_layout(height=460, plot_bgcolor="white", yaxis_title="Pendapatan (Rp)",
                       xaxis_tickangle=-60, showlegend=True,
                       legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    c1, c2, c3 = st.columns(3)
    c1.metric("Rata-rata Pendapatan Bulanan", rupiah(avg_overall))
    c2.metric("Bulan Kategori Tinggi", int((rekap['kategori_tren'] == 'Tinggi').sum()))
    c3.metric("Bulan Kategori Rendah", int((rekap['kategori_tren'] == 'Rendah').sum()))

    st.subheader("Pendapatan per Jenis Kopi (Total 2023–2025)")
    jenis_total = per_jenis.groupby('Jenis Kopi')['Total Pendapatan (Rp)'].sum().sort_values(ascending=False).reset_index()
    fig2 = px.bar(jenis_total, x='Jenis Kopi', y='Total Pendapatan (Rp)', color_discrete_sequence=[PRIMARY])
    fig2.update_layout(height=380, plot_bgcolor="white")
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

with tab3:
    st.subheader("🔮 Prediksi & Evaluasi Model")
    st.caption("Hasil prediksi tiap model ditampilkan terpisah, lalu dibandingkan performanya di sub-tab terakhir.")

    subtab_rf, subtab_lgb, subtab_perf = st.tabs(["🌲 Random Forest", "💡 LightGBM", "📊 Performa Dua Model"])

    # ---------- Sub-tab: Random Forest ----------
    with subtab_rf:
        st.markdown("#### Hasil Prediksi Random Forest — Data Uji")
        jenis_rf = st.selectbox("Pilih jenis kopi", sorted(test_out['Jenis Kopi'].unique()), key="jenis_rf")
        sub_rf = test_out[test_out['Jenis Kopi'] == jenis_rf].copy()
        sub_rf['label'] = sub_rf['Bulan'].str[:3] + " " + sub_rf['Tahun'].astype(str)

        fig_rf = go.Figure()
        fig_rf.add_trace(go.Scatter(x=sub_rf['label'], y=sub_rf['Total Pendapatan (Rp)'], name="Aktual",
                                     mode='lines+markers', line=dict(color="#333", width=3)))
        fig_rf.add_trace(go.Scatter(x=sub_rf['label'], y=sub_rf['Prediksi Random Forest'], name="Prediksi Random Forest",
                                     mode='lines+markers', line=dict(color=PRIMARY, dash='dash')))
        fig_rf.update_layout(height=420, plot_bgcolor="white", yaxis_title="Pendapatan (Rp)")
        st.plotly_chart(fig_rf, use_container_width=True, config={"displayModeBar": False})

        with st.expander("Lihat tabel hasil prediksi Random Forest"):
            rf_show = test_out[['Tahun', 'Bulan', 'Jenis Kopi', 'Total Pendapatan (Rp)', 'Prediksi Random Forest']].copy()
            rf_show['Total Pendapatan (Rp)'] = rf_show['Total Pendapatan (Rp)'].apply(rupiah)
            rf_show['Prediksi Random Forest'] = rf_show['Prediksi Random Forest'].apply(rupiah)
            st.dataframe(rf_show, use_container_width=True, hide_index=True)

    # ---------- Sub-tab: LightGBM ----------
    with subtab_lgb:
        st.markdown("#### Hasil Prediksi LightGBM — Data Uji")
        jenis_lgb = st.selectbox("Pilih jenis kopi", sorted(test_out['Jenis Kopi'].unique()), key="jenis_lgb")
        sub_lgb = test_out[test_out['Jenis Kopi'] == jenis_lgb].copy()
        sub_lgb['label'] = sub_lgb['Bulan'].str[:3] + " " + sub_lgb['Tahun'].astype(str)

        fig_lgb = go.Figure()
        fig_lgb.add_trace(go.Scatter(x=sub_lgb['label'], y=sub_lgb['Total Pendapatan (Rp)'], name="Aktual",
                                      mode='lines+markers', line=dict(color="#333", width=3)))
        fig_lgb.add_trace(go.Scatter(x=sub_lgb['label'], y=sub_lgb['Prediksi LightGBM'], name="Prediksi LightGBM",
                                      mode='lines+markers', line=dict(color=ACCENT, dash='dot')))
        fig_lgb.update_layout(height=420, plot_bgcolor="white", yaxis_title="Pendapatan (Rp)")
        st.plotly_chart(fig_lgb, use_container_width=True, config={"displayModeBar": False})

        with st.expander("Lihat tabel hasil prediksi LightGBM"):
            lgb_show = test_out[['Tahun', 'Bulan', 'Jenis Kopi', 'Total Pendapatan (Rp)', 'Prediksi LightGBM']].copy()
            lgb_show['Total Pendapatan (Rp)'] = lgb_show['Total Pendapatan (Rp)'].apply(rupiah)
            lgb_show['Prediksi LightGBM'] = lgb_show['Prediksi LightGBM'].apply(rupiah)
            st.dataframe(lgb_show, use_container_width=True, hide_index=True)

    # ---------- Sub-tab: Perbandingan Performa ----------
    with subtab_perf:
        st.markdown("#### Perbandingan Performa Model")
        res_df = pd.DataFrame(results).T
        res_df.columns = ['MAE', 'RMSE', 'R²', 'Training Time (detik)']
        best_model = res_df['MAE'].idxmin()
        st.dataframe(res_df.style.format({'MAE': '{:,.0f}', 'RMSE': '{:,.0f}', 'R²': '{:.4f}', 'Training Time (detik)': '{:.4f}'}),
                     use_container_width=True)
        st.success(f"Model dengan performa terbaik (MAE terendah): **{best_model}**")

        st.markdown("#### Aktual vs Prediksi — Kedua Model (Data Uji)")
        jenis_perf = st.selectbox("Pilih jenis kopi", sorted(test_out['Jenis Kopi'].unique()), key="jenis_perf")
        sub_perf = test_out[test_out['Jenis Kopi'] == jenis_perf].copy()
        sub_perf['label'] = sub_perf['Bulan'].str[:3] + " " + sub_perf['Tahun'].astype(str)

        fig_perf = go.Figure()
        fig_perf.add_trace(go.Scatter(x=sub_perf['label'], y=sub_perf['Total Pendapatan (Rp)'], name="Aktual",
                                       mode='lines+markers', line=dict(color="#333", width=3)))
        fig_perf.add_trace(go.Scatter(x=sub_perf['label'], y=sub_perf['Prediksi Random Forest'], name="Prediksi RF",
                                       mode='lines+markers', line=dict(color=PRIMARY, dash='dash')))
        fig_perf.add_trace(go.Scatter(x=sub_perf['label'], y=sub_perf['Prediksi LightGBM'], name="Prediksi LightGBM",
                                       mode='lines+markers', line=dict(color=ACCENT, dash='dot')))
        fig_perf.update_layout(height=420, plot_bgcolor="white", yaxis_title="Pendapatan (Rp)")
        st.plotly_chart(fig_perf, use_container_width=True, config={"displayModeBar": False})

        with st.expander("Lihat tabel hasil prediksi lengkap (kedua model)"):
            test_show = test_out.copy()
            for col in ['Total Pendapatan (Rp)', 'Prediksi Random Forest', 'Prediksi LightGBM']:
                test_show[col] = test_show[col].apply(rupiah)
            st.dataframe(test_show, use_container_width=True, hide_index=True)

with tab4:
    st.subheader("Feature Importance — Random Forest vs LightGBM")
    fi_sorted = fi.sort_values('Random Forest', ascending=True)
    fig4 = go.Figure()
    fig4.add_trace(go.Bar(y=fi_sorted['Fitur'], x=fi_sorted['Random Forest'], name='Random Forest', orientation='h', marker_color=PRIMARY))
    fig4.add_trace(go.Bar(y=fi_sorted['Fitur'], x=fi_sorted['LightGBM'], name='LightGBM', orientation='h', marker_color=ACCENT))
    fig4.update_layout(height=420, barmode='group', plot_bgcolor="white", xaxis_title="Tingkat Kepentingan (dinormalisasi)")
    st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})
    st.caption("Fitur `lag_1` (pendapatan bulan sebelumnya) dan `jenis_kopi_enc` konsisten menjadi variabel paling berpengaruh pada kedua model.")

with tab5:
    st.subheader(f"Prediksi Pendapatan {next_bulan_nama} {next_tahun}")
    st.caption("Model dilatih ulang menggunakan seluruh data historis (Januari 2023 – bulan terakhir data) agar prediksi memanfaatkan informasi terbaru yang tersedia.")

    total_rf = forecast_df['Prediksi Random Forest (Rp)'].sum()
    total_lgb = forecast_df['Prediksi LightGBM (Rp)'].sum()

    c1, c2, c3 = st.columns(3)
    c1.metric(f"Total Prediksi {next_bulan_nama} {next_tahun} (Random Forest)", rupiah(total_rf))
    c2.metric(f"Total Prediksi {next_bulan_nama} {next_tahun} (LightGBM)", rupiah(total_lgb))
    c3.metric("Rata-rata Pendapatan Historis / Bulan", rupiah(avg_overall))

    st.subheader("Rincian Prediksi per Jenis Kopi")
    show_df = forecast_df.copy()
    for col in ['Pendapatan Bulan Terakhir (Rp)', 'Prediksi Random Forest (Rp)', 'Prediksi LightGBM (Rp)']:
        show_df[col] = show_df[col].apply(rupiah)
    st.dataframe(show_df, use_container_width=True, hide_index=True)

    fig5 = go.Figure()
    fig5.add_trace(go.Bar(x=forecast_df['Jenis Kopi'], y=forecast_df['Prediksi Random Forest (Rp)'], name='Prediksi RF', marker_color=PRIMARY))
    fig5.add_trace(go.Bar(x=forecast_df['Jenis Kopi'], y=forecast_df['Prediksi LightGBM (Rp)'], name='Prediksi LightGBM', marker_color=ACCENT))
    fig5.update_layout(height=420, barmode='group', plot_bgcolor="white", yaxis_title="Prediksi Pendapatan (Rp)")
    st.plotly_chart(fig5, use_container_width=True, config={"displayModeBar": False})

    st.info("Catatan asumsi: harga rata-rata memakai rata-rata 3 bulan terakhir per jenis kopi, dan kategori tren memakai kategori bulan terakhir yang datanya tersedia (karena kategori tren bulan depan belum bisa diketahui sebelum pendapatan aktualnya terjadi).")

if IS_PEMILIK and tab6 is not None:
    with tab6:
        st.subheader("Laporan Penjualan")
        st.caption(
            "Pilih filter jenis kopi dan rentang periode, lalu unduh ringkasan laporan dalam format Word atau PDF. "
            "(Data sumber berupa transaksi per bulan, sehingga filter periode di sini berbentuk rentang bulan, bukan tanggal harian.)"
        )

        daily_periode = daily.copy()
        daily_periode['bulan_num'] = daily_periode['Bulan'].map(BULAN_MAP)
        daily_periode['periode'] = daily_periode['Tahun'] * 100 + daily_periode['bulan_num']

        jenis_list = sorted(daily_periode['Jenis Kopi'].unique())
        periode_sorted = sorted(daily_periode['periode'].unique())
        periode_label = {p: f"{BULAN_ORDER[(p % 100) - 1]} {p // 100}" for p in periode_sorted}

        jenis_filter = st.multiselect("Pilih jenis kopi", options=jenis_list, default=jenis_list)

        colp1, colp2 = st.columns(2)
        with colp1:
            periode_awal = st.selectbox("Dari bulan", periode_sorted, format_func=lambda p: periode_label[p],
                                         index=0, key="lap_periode_awal")
        with colp2:
            periode_akhir = st.selectbox("Sampai bulan", periode_sorted, format_func=lambda p: periode_label[p],
                                          index=len(periode_sorted) - 1, key="lap_periode_akhir")

        if periode_awal > periode_akhir:
            st.error("Bulan awal tidak boleh setelah bulan akhir. Silakan sesuaikan pilihan di atas.")
        elif not jenis_filter:
            st.warning("Pilih minimal satu jenis kopi untuk menampilkan laporan.")
        else:
            mask = (
                (daily_periode['periode'] >= periode_awal)
                & (daily_periode['periode'] <= periode_akhir)
                & (daily_periode['Jenis Kopi'].isin(jenis_filter))
            )
            df_filtered = daily_periode[mask].copy()

            if df_filtered.empty:
                st.warning("Tidak ada data untuk kombinasi filter yang dipilih.")
            else:
                total_pendapatan = df_filtered['Pendapatan (Rp)'].sum()
                total_qty = df_filtered['Jumlah Terjual'].sum()
                rata_harga = (
                    (df_filtered['Harga (Rp)'] * df_filtered['Jumlah Terjual']).sum() / total_qty
                    if total_qty > 0 else 0
                )

                st.markdown("#### Ringkasan Penjualan")
                c1, c2, c3 = st.columns(3)
                c1.metric("Total Pendapatan", rupiah(total_pendapatan))
                c2.metric("Total Unit Terjual", f"{int(total_qty):,}".replace(",", "."))
                c3.metric("Rata-rata Harga", rupiah(rata_harga))

                ringkasan_jenis = (
                    df_filtered.groupby('Jenis Kopi')
                    .agg(**{'Total Pendapatan (Rp)': ('Pendapatan (Rp)', 'sum'),
                            'Jumlah Terjual': ('Jumlah Terjual', 'sum')})
                    .reset_index()
                    .sort_values('Total Pendapatan (Rp)', ascending=False)
                )

                ringkasan_show = ringkasan_jenis.copy()
                ringkasan_show['Total Pendapatan (Rp)'] = ringkasan_show['Total Pendapatan (Rp)'].apply(rupiah)
                st.dataframe(ringkasan_show, use_container_width=True, hide_index=True)

                st.markdown("#### Unduh Laporan")
                periode_text = f"{periode_label[periode_awal]} – {periode_label[periode_akhir]}"
                jenis_text = "Semua Jenis Kopi" if len(jenis_filter) == len(jenis_list) else ", ".join(jenis_filter)
                file_tag = f"{periode_awal}_{periode_akhir}"

                if DOCX_OK:
                    docx_bytes = generate_laporan_docx(periode_text, jenis_text, total_pendapatan,
                                                         total_qty, rata_harga, ringkasan_jenis)
                    st.download_button(
                        "⬇️ Unduh Laporan (Word)", data=docx_bytes,
                        file_name=f"laporan_penjualan_{file_tag}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    )
                else:
                    st.warning("Modul `python-docx` belum terpasang. Tambahkan `python-docx` ke requirements.txt.")

                if REPORTLAB_OK:
                    pdf_bytes = generate_laporan_pdf(periode_text, jenis_text, total_pendapatan,
                                                       total_qty, rata_harga, ringkasan_jenis)
                    st.download_button(
                        "⬇️ Unduh Laporan (PDF)", data=pdf_bytes,
                        file_name=f"laporan_penjualan_{file_tag}.pdf",
                        mime="application/pdf",
                    )
                else:
                    st.warning("Modul `reportlab` belum terpasang. Tambahkan `reportlab` ke requirements.txt.")

st.divider()
st.caption("Dashboard ini dijalankan di Google Colab menggunakan Python, Streamlit, Scikit-learn, dan LightGBM ")