import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import os
import glob
import base64
import datetime
import calendar as cal_module

from logic import (
    BULAN_ORDER, BULAN_MAP,
    load_raw, build_dataset, train_models, forecast_next_month,
    rupiah, to_excel_bytes, generate_laporan_docx, generate_laporan_pdf,
    DOCX_OK, REPORTLAB_OK,
    build_calendar_matrix, get_periode_options, daily_weekly_estimate,
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
LOGO_PATH = find_asset("logo")

st.set_page_config(
    page_title="Dashboard Prediksi Pendapatan - Sumatra Roastery Medan",
    page_icon=FAVICON if FAVICON else "☕",
    layout="wide",
)

# =====================================================================
# PALET WARNA — tema baru: sidebar gelap + header atas + kartu KPI berwarna
# =====================================================================
PRIMARY = "#0F6B5C"          # hijau brand utama (dipakai untuk grafik & aksen)
PRIMARY_DARK = "#0B2E25"     # hijau tua untuk sidebar
PRIMARY_DARKER = "#071F19"   # hijau lebih tua untuk gradasi sidebar
SIDEBAR_ACTIVE = "#1FA37D"   # hijau terang untuk menu aktif
ACCENT = "#B5502D"
GOLD = "#E0A526"
GOLD_DARK = "#C98A1B"
BLUE = "#3B82C4"
PURPLE = "#8B5CF6"
GRID = "#E5EAE7"

BG_MAIN = "#EFF3F1"          # latar utama (abu-abu kehijauan lembut)
CARD_BG = "#FFFFFF"
CARD_BORDER = "#E4E9E6"

CREAM = "#FAF6F0"            # dipakai oleh login.py
CREAM_DARK = "#F0E8DC"
ESPRESSO = "#20302A"         # warna teks utama (dipakai juga oleh login.py)
ESPRESSO_SOFT = "#66756E"    # warna teks sekunder (dipakai juga oleh login.py)
BORDER = "#D9C9B4"           # dipakai oleh login.py

KPI_GREEN_BG, KPI_GREEN_ICON = "#DFF3E7", "#1FA37D"
KPI_PEACH_BG, KPI_PEACH_ICON = "#FBE8D7", "#E8873A"
KPI_BLUE_BG, KPI_BLUE_ICON = "#DEEBFA", BLUE
KPI_PURPLE_BG, KPI_PURPLE_ICON = "#EAE1FB", PURPLE

DONUT_COLORS = [PRIMARY, ACCENT, BLUE, PURPLE, GOLD, "#6EC6A5", "#E85D75"]

HARI_ID = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]


def rupiah_singkat(x):
    """Format ringkas untuk sel kalender kecil, mis. Rp 2,85 Jt."""
    juta = x / 1_000_000
    return f"Rp {juta:,.2f} Jt".replace(",", "#").replace(".", ",").replace("#", ".")


def render_month_calendar_grid(tahun, bulan_num, daily_avg):
    """Render grid kalender bulan (Senin-Minggu) bergaya kalender pada umumnya.
    Tanggal di luar bulan yang dipilih ditampilkan abu-abu tanpa angka (spillover
    dari bulan sebelum/sesudahnya). Karena data sumber hanya level bulanan, setiap
    tanggal dalam bulan ini menampilkan angka estimasi harian yang SAMA (bukan
    angka unik per tanggal)."""
    weeks = cal_module.Calendar(firstweekday=0).monthdatescalendar(int(tahun), int(bulan_num))
    nilai_singkat = rupiah_singkat(daily_avg)

    html = ['<table style="width:100%; border-collapse:collapse; font-family:inherit; table-layout:fixed;">']
    html.append('<tr>' + ''.join(
        f'<th style="background:{PRIMARY}; color:white; padding:6px 4px; font-size:12px;">{h}</th>'
        for h in ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]
    ) + '</tr>')

    for week in weeks:
        html.append('<tr>')
        for d in week:
            if d.month != int(bulan_num):
                html.append(
                    '<td style="background:#F5F7F6; color:#BFC9C3; padding:6px 4px; '
                    f'border:1px solid {GRID}; vertical-align:top; height:52px;">{d.day}</td>'
                )
            else:
                html.append(
                    f'<td style="background:#FFFFFF; padding:6px 4px; border:1px solid {GRID}; '
                    f'vertical-align:top; height:52px;">'
                    f'<div style="font-weight:700; color:{ESPRESSO}; font-size:13px;">{d.day}</div>'
                    f'<div style="font-size:10px; color:{PRIMARY}; font-weight:600;">{nilai_singkat}</div>'
                    '</td>'
                )
        html.append('</tr>')
    html.append('</table>')
    return ''.join(html)


st.markdown(f"""
<style>
/* ============ Dasar ============ */
.stApp {{
    background: {BG_MAIN} !important;
}}
html, body, [class*="css"] {{
    color: {ESPRESSO} !important;
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
}}
[data-testid="stHeader"] {{ background-color: transparent !important; }}
[data-testid="stToolbar"] {{ background-color: transparent; }}
[data-testid="stMainBlockContainer"], .block-container {{
    padding-top: 1.3rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
}}
[data-testid="stHeaderActionElements"] {{ display: none !important; }}

/* ============ Sidebar gelap ============ */
[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, {PRIMARY_DARK} 0%, {PRIMARY_DARKER} 100%) !important;
    border-right: none;
}}
[data-testid="stSidebar"] * {{ color: #EAF3EF !important; }}
[data-testid="stSidebarUserContent"] {{ padding: 1.1rem 1rem 1.2rem 1rem !important; }}

.sidebar-brand {{
    display: flex; align-items: center; gap: 12px;
    padding: 4px 2px 18px 2px;
    margin-bottom: 10px;
    border-bottom: 1px solid rgba(255,255,255,0.14);
}}
.sidebar-brand img {{
    width: 46px; height: 46px; border-radius: 50%;
    border: 2px solid rgba(255,255,255,0.55); object-fit: cover; background: #fff;
    flex-shrink: 0;
}}
.sidebar-brand-fallback {{
    width: 46px; height: 46px; border-radius: 50%;
    background: {SIDEBAR_ACTIVE}; display: flex; align-items: center; justify-content: center;
    font-size: 22px; flex-shrink: 0;
}}
.sidebar-brand-title {{ font-weight: 800; font-size: 0.92rem; line-height: 1.25; color: #FFFFFF !important; }}
.sidebar-brand-sub {{ font-size: 0.7rem; color: #B9D6C9 !important; margin-top: 2px; }}

[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] {{ gap: 3px !important; }}
[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label {{
    background: transparent;
    border: 1px solid transparent;
    border-radius: 10px;
    padding: 10px 12px !important;
    margin-bottom: 0 !important;
    width: 100%;
    transition: background 0.15s ease;
}}
[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label:hover {{
    background: rgba(255,255,255,0.08);
}}
[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label p {{
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    white-space: normal !important;
    color: #DCEEE6 !important;
}}
[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) {{
    background: {SIDEBAR_ACTIVE} !important;
    box-shadow: 0 4px 10px rgba(0,0,0,0.25);
}}
[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) p {{
    color: #FFFFFF !important; font-weight: 700 !important;
}}

.sidebar-footer-role {{ font-size: 0.8rem; color: #BFDCCF !important; margin-bottom: 8px; }}
[data-testid="stSidebar"] hr {{ border-color: rgba(255,255,255,0.14) !important; }}
[data-testid="stSidebar"] .stButton button {{
    background: transparent !important;
    border: 1px solid rgba(255,255,255,0.4) !important;
    color: #FFFFFF !important;
}}
[data-testid="stSidebar"] .stButton button:hover {{ background: rgba(255,255,255,0.14) !important; }}
[data-testid="stSidebar"] .stButton button p {{ color: #FFFFFF !important; }}

/* ============ Header putih di atas tiap halaman ============ */
.page-header {{
    display: flex; align-items: center; justify-content: space-between;
    background: {CARD_BG}; border: 1px solid {CARD_BORDER}; border-radius: 16px;
    padding: 16px 22px; margin-bottom: 18px;
    box-shadow: 0 2px 10px rgba(20,40,32,0.05);
    flex-wrap: wrap; gap: 10px;
}}
.page-header-left {{ display: flex; align-items: center; gap: 14px; }}
.page-header-icon {{
    width: 44px; height: 44px; border-radius: 12px; background: {PRIMARY};
    display: flex; align-items: center; justify-content: center; font-size: 20px; flex-shrink: 0;
}}
.page-header-title {{ font-size: 1.25rem; font-weight: 800; color: {ESPRESSO} !important; line-height: 1.2; }}
.page-header-subtitle {{ font-size: 0.82rem; color: {ESPRESSO_SOFT} !important; margin-top: 2px; }}
.page-header-right {{ display: flex; align-items: center; gap: 10px; }}
.header-pill {{
    background: {BG_MAIN}; border: 1px solid {CARD_BORDER}; border-radius: 999px;
    padding: 7px 14px; font-size: 0.78rem; font-weight: 600; color: {ESPRESSO} !important; white-space: nowrap;
}}
.header-pill-role {{ background: #DFF3E7; border-color: #BFE6D3; color: {PRIMARY} !important; }}

/* ============ Kartu KPI berwarna ============ */
.kpi-card {{
    border-radius: 16px; padding: 16px 18px; min-height: 118px;
    box-shadow: 0 2px 10px rgba(20,40,32,0.05);
    display: flex; flex-direction: column; justify-content: space-between;
}}
.kpi-icon {{
    width: 34px; height: 34px; border-radius: 10px; color: #FFFFFF;
    display: flex; align-items: center; justify-content: center; font-size: 16px; margin-bottom: 8px;
}}
.kpi-label {{ font-size: 0.78rem; font-weight: 600; color: {ESPRESSO_SOFT} !important; }}
.kpi-value {{ font-size: 1.35rem; font-weight: 800; margin-top: 2px; color: {ESPRESSO} !important; }}
.kpi-sub {{ font-size: 0.72rem; color: {ESPRESSO_SOFT} !important; margin-top: 4px; }}

/* ============ Kartu putih generik (pembungkus grafik/tabel) ============ */
[data-testid="stVerticalBlockBorderWrapper"] {{
    background: {CARD_BG} !important; border: 1px solid {CARD_BORDER} !important;
    border-radius: 16px !important; padding: 6px 8px !important;
    box-shadow: 0 2px 10px rgba(20,40,32,0.05);
}}

/* ============ Teks umum ============ */
h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown, .stCaption {{ color: {ESPRESSO} !important; }}
[data-testid="stCaptionContainer"] {{ color: {ESPRESSO_SOFT} !important; }}

/* ============ Input & form ============ */
.stTextInput input, .stNumberInput input {{
    background-color: #FFFFFF !important; color: {ESPRESSO} !important;
    border: 1px solid {CARD_BORDER} !important; border-radius: 8px;
}}
.stTextInput input::placeholder {{ color: #9AA8A1 !important; }}
.stTextInput label, .stNumberInput label, .stSlider label, .stSelectbox label, .stFileUploader label,
.stMultiSelect label {{ color: {ESPRESSO} !important; font-weight: 600; }}
.stSelectbox div[data-baseweb="select"] > div, .stMultiSelect div[data-baseweb="select"] > div {{
    background-color: #FFFFFF !important; color: {ESPRESSO} !important; border: 1px solid {CARD_BORDER} !important;
}}

/* ============ Tombol ============ */
.stButton button, .stFormSubmitButton button {{
    background-color: {PRIMARY} !important; border: none !important; border-radius: 8px; font-weight: 600;
}}
.stButton button p, .stFormSubmitButton button p,
.stButton button div, .stFormSubmitButton button div,
.stButton button span, .stFormSubmitButton button span {{ color: #FFFFFF !important; }}
.stButton button:hover, .stFormSubmitButton button:hover {{ background-color: {PRIMARY_DARK} !important; }}

.stDownloadButton button {{ background-color: {BLUE} !important; border: none !important; border-radius: 8px; font-weight: 600; }}
.stDownloadButton button p, .stDownloadButton button div, .stDownloadButton button span {{ color: #FFFFFF !important; }}
.stDownloadButton button:hover {{ background-color: #2E6BA3 !important; }}

/* ============ Autofill browser ============ */
input:-webkit-autofill, input:-webkit-autofill:hover, input:-webkit-autofill:focus {{
    -webkit-box-shadow: 0 0 0px 1000px #FFFFFF inset !important;
    -webkit-text-fill-color: {ESPRESSO} !important; caret-color: {ESPRESSO} !important;
}}

/* ============ Gambar ============ */
[data-testid="stImage"] img {{ max-height: 300px; width: 100%; object-fit: cover; border-radius: 18px; }}

/* ============ Slider ============ */
[data-testid="stSlider"] [role="slider"] {{ background-color: {PRIMARY} !important; }}

/* ============ Uploader ============ */
[data-testid="stFileUploaderDropzone"] {{ background-color: #FFFFFF !important; border: 1.5px dashed {CARD_BORDER} !important; }}
[data-testid="stFileUploaderDropzone"] * {{ color: {ESPRESSO_SOFT} !important; }}

/* ============ Tabs ============ */
[data-testid="stTabs"] {{ background: transparent !important; }}
.stTabs [data-baseweb="tab-list"], .stTabs div[role="tablist"],
[data-testid="stTabs"] [data-baseweb="tab-list"], [data-testid="stTabs"] div[role="tablist"] {{
    display: flex !important; width: 100% !important; gap: 4px !important; border-bottom: none !important;
    background: {CARD_BG} !important; border: 1px solid {CARD_BORDER} !important; border-radius: 14px !important;
    padding: 8px !important; box-shadow: 0 2px 8px rgba(20,40,32,0.05); flex-wrap: nowrap;
}}
.stTabs [data-baseweb="tab"], .stTabs [role="tab"] {{
    color: {ESPRESSO} !important; background: transparent !important; border: none !important; border-radius: 10px !important;
    padding: 7px 10px !important; transition: background 0.15s ease, color 0.15s ease;
    outline: none !important; box-shadow: none !important; text-decoration: none !important;
}}
.stTabs [data-baseweb="tab"]:focus, .stTabs [role="tab"]:focus,
.stTabs [data-baseweb="tab"]:focus-visible, .stTabs [role="tab"]:focus-visible {{ outline: none !important; }}
.stTabs [data-baseweb="tab"] *, .stTabs [role="tab"] * {{ font-weight: 700 !important; font-size: 0.88rem !important; white-space: nowrap !important; }}
.stTabs [data-baseweb="tab"]:hover:not([aria-selected="true"]), .stTabs [role="tab"]:hover:not([aria-selected="true"]) {{
    color: {ESPRESSO} !important; background: {BG_MAIN} !important;
}}
.stTabs [aria-selected="true"] {{
    color: #FFFFFF !important; background: {PRIMARY} !important;
    box-shadow: 0 3px 8px rgba(15,107,92,0.35) !important; border-bottom: none !important;
}}
.stTabs [aria-selected="true"]:hover, .stTabs [aria-selected="true"]:focus, .stTabs [aria-selected="true"]:focus-visible {{
    color: #FFFFFF !important; background: {PRIMARY} !important; outline: none !important;
}}
.stTabs [aria-selected="true"] * {{ color: #FFFFFF !important; }}
.stTabs [data-baseweb="tab-highlight"] {{ display: none !important; }}
.stTabs [data-baseweb="tab-border"] {{ display: none !important; }}
[data-testid="stTabs"] [role="tabpanel"] [data-baseweb="tab-list"],
[data-testid="stTabs"] [role="tabpanel"] div[role="tablist"] {{ display: inline-flex !important; width: auto !important; max-width: fit-content !important; }}

/* ============ Metric bawaan Streamlit ============ */
[data-testid="stMetric"] {{
    background-color: {CARD_BG}; border: 1px solid {CARD_BORDER}; border-radius: 12px; padding: 14px 16px;
}}
[data-testid="stMetricLabel"] {{ color: {ESPRESSO_SOFT} !important; }}
[data-testid="stMetricValue"] {{ color: {ESPRESSO} !important; }}

/* ============ Dataframe & expander ============ */
[data-testid="stDataFrame"] {{ border: 1px solid {CARD_BORDER}; border-radius: 10px; }}
[data-testid="stExpander"] {{ background-color: {CARD_BG}; border: 1px solid {CARD_BORDER}; border-radius: 12px; }}
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


def format_tanggal_indo(dt):
    return f"{HARI_ID[dt.weekday()]}, {dt.day} {BULAN_ORDER[dt.month - 1]} {dt.year}"


def render_page_header(icon, title, subtitle):
    """Header putih di puncak setiap halaman: ikon+judul+subjudul di kiri,
    tanggal hari ini & peran login di kanan (menggantikan blok 'Login sebagai' lama)."""
    tanggal_str = format_tanggal_indo(datetime.date.today())
    role = st.session_state.role
    st.markdown(f"""
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-header-icon">{icon}</div>
        <div>
          <div class="page-header-title">{title}</div>
          <div class="page-header-subtitle">{subtitle}</div>
        </div>
      </div>
      <div class="page-header-right">
        <div class="header-pill">📅 {tanggal_str}</div>
        <div class="header-pill header-pill-role">👤 {role}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)


def kpi_card(icon, label, value, sub, bg, icon_bg):
    st.markdown(f"""
    <div class="kpi-card" style="background:{bg};">
        <div class="kpi-icon" style="background:{icon_bg};">{icon}</div>
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)


IS_PENELITI = st.session_state.role == "Peneliti"
IS_PEMILIK = st.session_state.role == "Pemilik/Pengelola"

MENU_OPTIONS = [
    "🏠 Dashboard",
    "📥 Input Dataset",
    "📋 Data Aktual",
    "📈 Analisis Tren",
    "🔮 Prediksi & Evaluasi",
    "⭐ Feature Importance",
    "📅 Perkiraan Bulan Berikutnya",
    "🗓️ Kalender",
]
if IS_PEMILIK:
    MENU_OPTIONS.append("📄 Laporan")

with st.sidebar:
    if LOGO_PATH:
        logo_b64 = get_base64_image(LOGO_PATH, os.path.getmtime(LOGO_PATH))
        st.markdown(f"""
        <div class="sidebar-brand">
            <img src="data:image/png;base64,{logo_b64}">
            <div>
                <div class="sidebar-brand-title">SUMATRA ROASTERY<br>MEDAN</div>
                <div class="sidebar-brand-sub">Dashboard Analisis &amp; Prediksi</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="sidebar-brand">
            <div class="sidebar-brand-fallback">☕</div>
            <div>
                <div class="sidebar-brand-title">SUMATRA ROASTERY<br>MEDAN</div>
                <div class="sidebar-brand-sub">Dashboard Analisis &amp; Prediksi</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    menu = st.radio("Navigasi", MENU_OPTIONS, label_visibility="collapsed", key="main_menu")
    st.divider()
    st.markdown(f'<div class="sidebar-footer-role">Login sebagai: <b>{st.session_state.role}</b></div>', unsafe_allow_html=True)
    if st.button("Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.role = None
        st.rerun()

uploaded = None
split_ratio = 0.8

if menu == "📥 Input Dataset":
    render_page_header("📥", "Input Dataset", "Unggah dataset penjualan (.xlsx) dan atur proporsi data training/testing.")
    with st.container(border=True):
        if IS_PENELITI:
            uploaded = st.file_uploader("Unggah dataset (.xlsx)", type=["xlsx"], key="input_dataset_file")
            split_ratio = st.slider(
                "Proporsi data training", 0.6, 0.9,
                st.session_state.get("input_split_ratio", 0.8), 0.05,
                key="input_split_ratio",
            )
            st.caption("Sesuai BAB III: time-based split 80:20 (nilai default).")
            if uploaded is not None:
                st.success(f"Dataset '{uploaded.name}' berhasil diunggah dan sedang digunakan oleh dashboard.")
            else:
                st.info(
                    "Belum ada dataset yang diunggah — dashboard memakai dataset lokal bawaan "
                    "(file .xlsx yang berada satu folder dengan app.py)."
                )
        else:
            st.warning(
                "Input dataset & pengaturan model hanya dapat diubah oleh akun Peneliti. "
                "Anda melihat hasil analisis berdasarkan dataset yang sedang aktif."
            )
            st.caption("Sesuai BAB III: time-based split 80:20")
else:
    if IS_PENELITI:
        uploaded = st.session_state.get("input_dataset_file")
        split_ratio = st.session_state.get("input_split_ratio", 0.8)


def find_local_dataset():
    candidates = glob.glob(os.path.join(SCRIPT_DIR, "*.xlsx"))
    return candidates[0] if candidates else None


data_path = uploaded if uploaded is not None else find_local_dataset()

if data_path is None:
    st.warning(
        "Tidak ada file .xlsx ditemukan di folder yang sama dengan app.py. "
        "Unggah dataset lewat menu \"📥 Input Dataset\" di sidebar kiri."
    )
    st.stop()

try:
    daily, per_jenis, rekap_raw = load_raw(data_path)
except Exception as e:
    st.error(f"Gagal membaca dataset: {e}")
    st.stop()

df, rekap, avg_overall = build_dataset(daily, per_jenis, rekap_raw)
results, fi, test_out, split_periode = train_models(df, split_ratio)
forecast_df, next_bulan_nama, next_tahun = forecast_next_month(df)
total_rf = forecast_df['Prediksi Random Forest (Rp)'].sum()
total_lgb = forecast_df['Prediksi LightGBM (Rp)'].sum()

if menu == "📥 Input Dataset":
    st.write("")
    with st.container(border=True):
        st.markdown("##### 📊 Ringkasan Dataset Aktif")
        nama_sumber = uploaded.name if uploaded is not None else os.path.basename(data_path)
        c1, c2, c3 = st.columns(3)
        c1.metric("Jumlah Baris Transaksi Harian", f"{len(daily):,}".replace(",", "."))
        c2.metric("Jumlah Bulan Terekam", int(rekap.shape[0]))
        c3.metric(
            "Periode Data",
            f"{rekap['Bulan'].iloc[0][:3]} {rekap['Tahun'].iloc[0]} – {rekap['Bulan'].iloc[-1][:3]} {rekap['Tahun'].iloc[-1]}",
        )
        st.caption(f"Sumber dataset yang sedang aktif: `{nama_sumber}`")

# =====================================================================
# 🏠 DASHBOARD
# =====================================================================
if menu == "🏠 Dashboard":
    render_page_header("🏠", "Dashboard", "Sistem Prediksi Pendapatan Penjualan Kopi — Sumatra Roastery Medan")

    rekap_sorted = rekap.sort_values('periode').reset_index(drop=True)
    total_pendapatan_all = rekap_sorted['Total Pendapatan (Rp)'].sum()

    last_val = rekap_sorted['Total Pendapatan (Rp)'].iloc[-1]
    prev_val = rekap_sorted['Total Pendapatan (Rp)'].iloc[-2] if len(rekap_sorted) > 1 else last_val
    delta_pct = ((last_val - prev_val) / prev_val * 100) if prev_val else 0
    panah = "↑" if delta_pct >= 0 else "↓"

    jenis_total_all = per_jenis.groupby('Jenis Kopi')['Total Pendapatan (Rp)'].sum().sort_values(ascending=False)
    top_jenis_nama = jenis_total_all.index[0]
    top_jenis_pct = jenis_total_all.iloc[0] / jenis_total_all.sum() * 100

    idx_tertinggi = rekap_sorted['Total Pendapatan (Rp)'].idxmax()
    bulan_tertinggi = rekap_sorted.loc[idx_tertinggi, 'Bulan']
    tahun_tertinggi = rekap_sorted.loc[idx_tertinggi, 'Tahun']
    nilai_tertinggi = rekap_sorted.loc[idx_tertinggi, 'Total Pendapatan (Rp)']

    prediksi_avg = (total_rf + total_lgb) / 2
    prediksi_delta = ((prediksi_avg - last_val) / last_val * 100) if last_val else 0
    panah_prediksi = "↑" if prediksi_delta >= 0 else "↓"

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        kpi_card("💰", "Total Pendapatan (Data Aktual)", rupiah(total_pendapatan_all),
                  f"{panah} {abs(delta_pct):.1f}% dari bulan sebelumnya", KPI_GREEN_BG, KPI_GREEN_ICON)
    with k2:
        kpi_card("☕", "Penjualan Terbanyak", top_jenis_nama,
                  f"{top_jenis_pct:.1f}% dari total pendapatan", KPI_PEACH_BG, KPI_PEACH_ICON)
    with k3:
        kpi_card("📈", "Pendapatan Tertinggi", rupiah(nilai_tertinggi),
                  f"{bulan_tertinggi} {tahun_tertinggi}", KPI_BLUE_BG, KPI_BLUE_ICON)
    with k4:
        kpi_card("📅", "Prediksi Bulan Berikutnya", rupiah(prediksi_avg),
                  f"{panah_prediksi} {abs(prediksi_delta):.1f}% dari bulan terakhir", KPI_PURPLE_BG, KPI_PURPLE_ICON)

    st.write("")
    col_tren, col_model = st.columns([2, 1])
    with col_tren:
        with st.container(border=True):
            st.markdown("##### Tren Pendapatan Penjualan")
            labels_tren = [f"{b[:3]} {t}" for b, t in zip(rekap_sorted['Bulan'], rekap_sorted['Tahun'])]
            fig_tren = go.Figure()
            fig_tren.add_trace(go.Bar(x=labels_tren, y=rekap_sorted['Total Pendapatan (Rp)'],
                                       name="Pendapatan", marker_color=KPI_GREEN_ICON))
            fig_tren.add_trace(go.Scatter(x=labels_tren, y=rekap_sorted['Total Pendapatan (Rp)'],
                                           name="Tren", mode='lines', line=dict(color=PRIMARY_DARK, width=2)))
            fig_tren.update_layout(height=320, plot_bgcolor="white", margin=dict(t=10, b=10),
                                    yaxis_title="Pendapatan (Rp)", xaxis_tickangle=-45,
                                    legend=dict(orientation='h', y=1.15))
            st.plotly_chart(fig_tren, use_container_width=True, config={"displayModeBar": False})

    with col_model:
        with st.container(border=True):
            st.markdown("##### Ringkasan Model")
            res_df_home = pd.DataFrame(results).T
            res_df_home.columns = ['MAE', 'RMSE', 'R2', 'Training_Time']
            best_model_home = res_df_home['MAE'].idxmin()
            for nama_model in res_df_home.index:
                row = res_df_home.loc[nama_model]
                st.markdown(f"**{nama_model}**")
                mc1, mc2 = st.columns(2)
                mc1.metric("MAE", rupiah(row['MAE']))
                mc2.metric("RMSE", rupiah(row['RMSE']))
                mc3, mc4 = st.columns(2)
                mc3.metric("R²", f"{row['R2']:.3f}")
                mc4.metric("Waktu Latih", f"{row['Training_Time']:.1f} dtk")
                st.markdown("<hr style='margin:6px 0;'>", unsafe_allow_html=True)
            st.success(f"🏆 **{best_model_home}** memiliki performa lebih baik (MAE & error terendah).")

    st.write("")
    col_tabel, col_donut, col_fi = st.columns([1.3, 1, 1])
    with col_tabel:
        with st.container(border=True):
            st.markdown("##### Data Penjualan Terbaru")
            daily_terbaru = daily.copy()
            daily_terbaru['bulan_num'] = daily_terbaru['Bulan'].map(BULAN_MAP)
            daily_terbaru['periode'] = daily_terbaru['Tahun'] * 100 + daily_terbaru['bulan_num']
            daily_terbaru = daily_terbaru.sort_values('periode', ascending=False).head(5)
            tabel_show = daily_terbaru[['Tahun', 'Bulan', 'Jenis Kopi', 'Varian Kopi', 'Harga (Rp)', 'Pendapatan (Rp)']].copy()
            tabel_show['Harga (Rp)'] = tabel_show['Harga (Rp)'].apply(rupiah)
            tabel_show['Pendapatan (Rp)'] = tabel_show['Pendapatan (Rp)'].apply(rupiah)
            st.dataframe(tabel_show, use_container_width=True, hide_index=True)
            st.caption("Baris terbaru menurut periode (Tahun/Bulan) pada data transaksi harian.")

    with col_donut:
        with st.container(border=True):
            st.markdown("##### Proporsi Jenis Kopi")
            donut_df = jenis_total_all.reset_index()
            fig_donut = go.Figure(data=[go.Pie(
                labels=donut_df['Jenis Kopi'], values=donut_df['Total Pendapatan (Rp)'],
                hole=0.6, marker=dict(colors=DONUT_COLORS),
            )])
            fig_donut.update_layout(height=300, margin=dict(t=10, b=10, l=0, r=0),
                                     showlegend=True, legend=dict(orientation='h', y=-0.25, font=dict(size=9)))
            st.plotly_chart(fig_donut, use_container_width=True, config={"displayModeBar": False})

    with col_fi:
        with st.container(border=True):
            st.markdown("##### Feature Importance")
            fi_top = fi[['Fitur', 'Random Forest']].sort_values('Random Forest', ascending=True).tail(5)
            fig_fi_home = go.Figure(go.Bar(
                x=fi_top['Random Forest'], y=fi_top['Fitur'], orientation='h', marker_color=PRIMARY,
            ))
            fig_fi_home.update_layout(height=300, margin=dict(t=10, b=10), plot_bgcolor="white",
                                       xaxis_title="Tingkat Kepentingan")
            st.plotly_chart(fig_fi_home, use_container_width=True, config={"displayModeBar": False})

    st.write("")
    col_forecast, col_kalender = st.columns([1, 1.2])
    with col_forecast:
        with st.container(border=True):
            st.markdown(f"##### Perkiraan Pendapatan {next_bulan_nama} {next_tahun}")
            st.markdown(f"<div class='kpi-value' style='font-size:1.7rem;'>{rupiah(prediksi_avg)}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='kpi-sub'>{panah_prediksi} {abs(prediksi_delta):.1f}% dari pendapatan bulan terakhir</div>", unsafe_allow_html=True)
            st.write("")
            fc1, fc2 = st.columns(2)
            fc1.metric("Random Forest", rupiah(total_rf))
            fc2.metric("LightGBM", rupiah(total_lgb))
            st.caption("Rincian lengkap per jenis kopi ada di menu 📅 Perkiraan Bulan Berikutnya.")

    with col_kalender:
        with st.container(border=True):
            bulan_terakhir = rekap_sorted['Bulan'].iloc[-1]
            tahun_terakhir = rekap_sorted['Tahun'].iloc[-1]
            st.markdown(f"##### Kalender — {bulan_terakhir} {tahun_terakhir}")
            _, daily_avg_home, _ = daily_weekly_estimate(
                tahun_terakhir, BULAN_MAP[bulan_terakhir], rekap_sorted['Total Pendapatan (Rp)'].iloc[-1],
            )
            st.markdown(render_month_calendar_grid(tahun_terakhir, BULAN_MAP[bulan_terakhir], daily_avg_home),
                        unsafe_allow_html=True)
            st.caption("Buka menu 🗓️ Kalender untuk navigasi & rincian mingguan lengkap.")

# =====================================================================
# 📋 DATA AKTUAL
# =====================================================================
elif menu == "📋 Data Aktual":
    render_page_header("📋", "Data Aktual", "Data yang diterima & sudah diolah (preprocessing) — menjadi dasar seluruh analisis.")

    with st.container(border=True):
        st.markdown("##### Rekap Pendapatan Bulanan")
        rekap_show = rekap[['Tahun', 'Bulan', 'Total Pendapatan (Rp)', 'kategori_tren']].copy()
        rekap_show['Total Pendapatan (Rp)'] = rekap_show['Total Pendapatan (Rp)'].apply(rupiah)
        rekap_show = rekap_show.rename(columns={'kategori_tren': 'Kategori Tren'})
        st.dataframe(rekap_show, use_container_width=True, hide_index=True)

    st.write("")
    with st.container(border=True):
        st.markdown("##### Pendapatan per Jenis Kopi per Bulan")
        per_jenis_show = per_jenis.copy()
        per_jenis_show['Total Pendapatan (Rp)'] = per_jenis_show['Total Pendapatan (Rp)'].apply(rupiah)
        per_jenis_show['% dari Total Bulan'] = (per_jenis_show['% dari Total Bulan'] * 100).round(2).astype(str) + '%'
        st.dataframe(per_jenis_show, use_container_width=True, hide_index=True)

    st.write("")
    with st.container(border=True):
        st.markdown("##### Data Transaksi Harian")
        daily_show = daily.copy()
        daily_show['Harga (Rp)'] = daily_show['Harga (Rp)'].apply(rupiah)
        daily_show['Pendapatan (Rp)'] = daily_show['Pendapatan (Rp)'].apply(rupiah)
        st.dataframe(daily_show, use_container_width=True, hide_index=True, height=400)
        st.download_button("⬇️ Download Excel — Data Transaksi Harian",
                            data=to_excel_bytes(daily_show, "Transaksi Harian"),
                            file_name="data_transaksi_harian.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# =====================================================================
# 📈 ANALISIS TREN
# =====================================================================
elif menu == "📈 Analisis Tren":
    render_page_header("📈", "Analisis Tren", "Tren pendapatan bulanan dan kontribusi tiap jenis kopi.")

    with st.container(border=True):
        st.markdown("##### Tren Pendapatan Bulanan (2023–2025)")
        labels = [f"{b[:3]} {t}" for b, t in zip(rekap['Bulan'], rekap['Tahun'])]
        nilai_tinggi = np.where(rekap['kategori_tren'] == 'Tinggi', rekap['Total Pendapatan (Rp)'], np.nan)
        nilai_rendah = np.where(rekap['kategori_tren'] == 'Rendah', rekap['Total Pendapatan (Rp)'], np.nan)

        fig = go.Figure()
        fig.add_trace(go.Bar(x=labels, y=nilai_tinggi, marker_color=PRIMARY, name="Tinggi (≥ rata-rata)"))
        fig.add_trace(go.Bar(x=labels, y=nilai_rendah, marker_color=ACCENT, name="Rendah (< rata-rata)"))
        fig.add_hline(y=avg_overall, line_dash="dash", line_color="#888",
                      annotation_text=f"Rata-rata: {rupiah(avg_overall)}")
        fig.update_layout(height=440, plot_bgcolor="white", yaxis_title="Pendapatan (Rp)",
                           xaxis_tickangle=-60, showlegend=True,
                           legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        c1, c2, c3 = st.columns(3)
        c1.metric("Rata-rata Pendapatan Bulanan", rupiah(avg_overall))
        c2.metric("Bulan Kategori Tinggi", int((rekap['kategori_tren'] == 'Tinggi').sum()))
        c3.metric("Bulan Kategori Rendah", int((rekap['kategori_tren'] == 'Rendah').sum()))

    st.write("")
    with st.container(border=True):
        st.markdown("##### Pendapatan per Jenis Kopi (Total 2023–2025)")
        jenis_total = per_jenis.groupby('Jenis Kopi')['Total Pendapatan (Rp)'].sum().sort_values(ascending=False).reset_index()
        fig2 = px.bar(jenis_total, x='Jenis Kopi', y='Total Pendapatan (Rp)', color_discrete_sequence=[PRIMARY])
        fig2.update_layout(height=380, plot_bgcolor="white")
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

# =====================================================================
# 🔮 PREDIKSI & EVALUASI
# =====================================================================
elif menu == "🔮 Prediksi & Evaluasi":
    render_page_header("🔮", "Prediksi & Evaluasi", "Latih Random Forest & LightGBM, hasilkan prediksi, dan bandingkan performanya.")

    subtab_rf, subtab_lgb, subtab_perf = st.tabs(["🌲 Random Forest", "💡 LightGBM", "📊 Performa Model"])

    with subtab_rf:
        with st.container(border=True):
            st.markdown("##### Hasil Prediksi Random Forest — Data Uji")
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

    with subtab_lgb:
        with st.container(border=True):
            st.markdown("##### Hasil Prediksi LightGBM — Data Uji")
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

    with subtab_perf:
        with st.container(border=True):
            st.markdown("##### Perbandingan Performa Model")
            res_df = pd.DataFrame(results).T
            res_df.columns = ['MAE', 'RMSE', 'R²', 'Training Time (detik)']
            best_model = res_df['MAE'].idxmin()
            st.dataframe(res_df.style.format({'MAE': '{:,.0f}', 'RMSE': '{:,.0f}', 'R²': '{:.4f}', 'Training Time (detik)': '{:.4f}'}),
                         use_container_width=True)
            st.success(f"Model dengan performa terbaik (MAE terendah): **{best_model}**")

        st.write("")
        with st.container(border=True):
            st.markdown("##### Aktual vs Prediksi — Kedua Model (Data Uji)")
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

# =====================================================================
# ⭐ FEATURE IMPORTANCE
# =====================================================================
elif menu == "⭐ Feature Importance":
    render_page_header("⭐", "Feature Importance", "Variabel yang paling berpengaruh terhadap hasil prediksi.")
    with st.container(border=True):
        st.markdown("##### Feature Importance — Random Forest vs LightGBM")
        fi_sorted = fi.sort_values('Random Forest', ascending=True)
        fig4 = go.Figure()
        fig4.add_trace(go.Bar(y=fi_sorted['Fitur'], x=fi_sorted['Random Forest'], name='Random Forest', orientation='h', marker_color=PRIMARY))
        fig4.add_trace(go.Bar(y=fi_sorted['Fitur'], x=fi_sorted['LightGBM'], name='LightGBM', orientation='h', marker_color=ACCENT))
        fig4.update_layout(height=420, barmode='group', plot_bgcolor="white", xaxis_title="Tingkat Kepentingan (dinormalisasi)")
        st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})
        st.caption("Fitur `lag_1` (pendapatan bulan sebelumnya) dan `jenis_kopi_enc` konsisten menjadi variabel paling berpengaruh pada kedua model.")

# =====================================================================
# 📅 PERKIRAAN BULAN BERIKUTNYA
# =====================================================================
elif menu == "📅 Perkiraan Bulan Berikutnya":
    render_page_header("📅", "Perkiraan Bulan Berikutnya", f"Prediksi pendapatan untuk {next_bulan_nama} {next_tahun}, dilatih ulang dari seluruh data historis.")

    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        c1.metric(f"Total Prediksi {next_bulan_nama} {next_tahun} (Random Forest)", rupiah(total_rf))
        c2.metric(f"Total Prediksi {next_bulan_nama} {next_tahun} (LightGBM)", rupiah(total_lgb))
        c3.metric("Rata-rata Pendapatan Historis / Bulan", rupiah(avg_overall))

    st.write("")
    with st.container(border=True):
        st.markdown("##### Rincian Prediksi per Jenis Kopi")
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

# =====================================================================
# 🗓️ KALENDER
# =====================================================================
elif menu == "🗓️ Kalender":
    render_page_header("🗓️", "Kalender", "Periode/tanggal data dalam tampilan kalender heatmap.")

    with st.container(border=True):
        st.markdown("##### Kalender Pendapatan Bulanan (Heatmap Tahunan)")
        cal_matrix = build_calendar_matrix(rekap)
        fig_cal = go.Figure(data=go.Heatmap(
            z=cal_matrix.values,
            x=cal_matrix.columns,
            y=[str(y) for y in cal_matrix.index],
            colorscale=[[0, "#EAF2EF"], [1, PRIMARY]],
            hovertemplate="%{y} %{x}<br>Rp %{z:,.0f}<extra></extra>",
            colorbar=dict(title="Rp"),
        ))
        fig_cal.update_layout(height=260, plot_bgcolor="white", xaxis_title=None, yaxis_title=None)
        st.plotly_chart(fig_cal, use_container_width=True, config={"displayModeBar": False})
        st.caption("Warna lebih gelap = pendapatan lebih tinggi pada bulan tersebut. Sel kosong menandakan tidak ada data pada periode itu.")

    st.write("")

    # ---------------------------------------------------------------
    # Navigasi kalender bergaya "My Calendar" (panah kiri/kanan + Hari Ini)
    # ---------------------------------------------------------------
    opsi_periode = get_periode_options(rekap, (total_rf + total_lgb) / 2, next_bulan_nama, next_tahun)
    opsi_periode_sorted = sorted(opsi_periode, key=lambda o: (o['Tahun'], o['bulan_num']))

    if 'kalender_idx' not in st.session_state:
        st.session_state['kalender_idx'] = len(opsi_periode_sorted) - 1
    st.session_state['kalender_idx'] = max(0, min(st.session_state['kalender_idx'], len(opsi_periode_sorted) - 1))

    with st.container(border=True):
        st.markdown("##### 📅 Kalender Penjualan")
        nav1, nav2, nav3, nav4 = st.columns([1, 4, 1, 1.6])
        with nav1:
            if st.button("←", key="kalender_prev", use_container_width=True):
                st.session_state['kalender_idx'] = max(0, st.session_state['kalender_idx'] - 1)
        with nav3:
            if st.button("→", key="kalender_next", use_container_width=True):
                st.session_state['kalender_idx'] = min(len(opsi_periode_sorted) - 1, st.session_state['kalender_idx'] + 1)
        with nav4:
            if st.button("Hari ini", key="kalender_today", use_container_width=True):
                st.session_state['kalender_idx'] = len(opsi_periode_sorted) - 1

        sel = opsi_periode_sorted[st.session_state['kalender_idx']]
        with nav2:
            st.markdown(
                f"<div style='text-align:center; font-size:1.5rem; font-weight:800; color:{ESPRESSO}; padding-top:2px;'>"
                f"{sel['Bulan']} {sel['Tahun']} <span style='font-size:0.9rem; font-weight:600; color:{PRIMARY};'>({sel['tipe']})</span></div>",
                unsafe_allow_html=True,
            )

        tampilan = st.radio("Tampilan", ["Bulan", "Minggu", "Hari"], horizontal=True,
                             key="kalender_tampilan", label_visibility="collapsed")
        if tampilan != "Bulan":
            st.info(
                "Tampilan Minggu/Hari belum bisa ditampilkan datanya karena data sumber hanya mencatat "
                "transaksi pada level bulanan (lihat BAB III). Kalender tetap ditampilkan pada level Bulan."
            )

    st.write("")

    # ---------------------------------------------------------------
    # Kartu KPI + gauge
    # ---------------------------------------------------------------
    is_aktual = sel['tipe'] == 'Aktual'
    if is_aktual:
        daily_bulan_sel = daily[(daily['Tahun'] == sel['Tahun']) & (daily['Bulan'] == sel['Bulan'])]
        jumlah_transaksi = len(daily_bulan_sel)
        jenis_terjual = daily_bulan_sel['Jenis Kopi'].nunique()
    else:
        jumlah_transaksi = None
        jenis_terjual = None

    with st.container(border=True):
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Jumlah Transaksi", f"{jumlah_transaksi:,}" if jumlah_transaksi is not None else "—")
        k2.metric("Jenis Kopi Terjual", f"{jenis_terjual}" if jenis_terjual is not None else "—")
        k3.metric(f"Total Pendapatan ({sel['tipe']})", rupiah(sel['Total Pendapatan (Rp)']))
        with k4:
            batas_atas = max(rekap['Total Pendapatan (Rp)'].max(), sel['Total Pendapatan (Rp)']) * 1.15
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=sel['Total Pendapatan (Rp)'],
                number={'valueformat': ',.0f', 'prefix': 'Rp '},
                gauge={
                    'axis': {'range': [0, batas_atas]},
                    'bar': {'color': PRIMARY},
                    'steps': [
                        {'range': [0, avg_overall], 'color': '#F4D9C6'},
                        {'range': [avg_overall, batas_atas], 'color': '#D7E8E1'},
                    ],
                    'threshold': {'line': {'color': ACCENT, 'width': 3}, 'thickness': 0.8, 'value': avg_overall},
                },
                title={'text': "Pendapatan vs Rata-rata", 'font': {'size': 12}},
            ))
            fig_gauge.update_layout(height=170, margin=dict(l=10, r=10, t=40, b=0))
            st.plotly_chart(fig_gauge, use_container_width=True, config={"displayModeBar": False})
        st.caption("Garis oranye pada gauge menandakan rata-rata pendapatan bulanan historis keseluruhan periode.")

    st.write("")

    # ---------------------------------------------------------------
    # Dua grafik: tren bulanan (historis) & per jenis kopi (bulan terpilih)
    # ---------------------------------------------------------------
    chart1, chart2 = st.columns(2)
    with chart1:
        with st.container(border=True):
            st.markdown("##### Pendapatan per Bulan (Tren Historis)")
            rekap_plot = rekap.sort_values('periode').copy()
            rekap_plot['label'] = rekap_plot['Bulan'].str[:3] + " " + rekap_plot['Tahun'].astype(str)
            rekap_plot['kumulatif'] = rekap_plot['Total Pendapatan (Rp)'].cumsum()
            warna_bar = [ACCENT if (r['Tahun'] == sel['Tahun'] and r['Bulan'] == sel['Bulan']) else PRIMARY
                         for _, r in rekap_plot.iterrows()]
            fig_a = go.Figure()
            fig_a.add_trace(go.Bar(x=rekap_plot['label'], y=rekap_plot['Total Pendapatan (Rp)'],
                                    name="Pendapatan", marker_color=warna_bar, yaxis='y1'))
            fig_a.add_trace(go.Scatter(x=rekap_plot['label'], y=rekap_plot['kumulatif'], name="Kumulatif",
                                        mode='lines', line=dict(color=ESPRESSO, width=2), yaxis='y2'))
            fig_a.update_layout(height=340, plot_bgcolor="white",
                                yaxis=dict(title="Pendapatan (Rp)"),
                                yaxis2=dict(title="Kumulatif (Rp)", overlaying='y', side='right'),
                                legend=dict(orientation='h', y=1.15))
            st.plotly_chart(fig_a, use_container_width=True, config={"displayModeBar": False})
            st.caption("Batang oranye menandakan bulan yang sedang dipilih di navigasi kalender.")

    with chart2:
        with st.container(border=True):
            st.markdown(f"##### Pendapatan per Jenis Kopi — {sel['Bulan']} {sel['Tahun']}")
            if is_aktual:
                jenis_bulan = df[(df['Tahun'] == sel['Tahun']) & (df['Bulan'] == sel['Bulan'])][['Jenis Kopi', 'Total Pendapatan (Rp)']].copy()
            else:
                jenis_bulan = forecast_df[['Jenis Kopi']].copy()
                jenis_bulan['Total Pendapatan (Rp)'] = (forecast_df['Prediksi Random Forest (Rp)'] + forecast_df['Prediksi LightGBM (Rp)']) / 2
            jenis_bulan = jenis_bulan.sort_values('Total Pendapatan (Rp)', ascending=False).reset_index(drop=True)
            jenis_bulan['kumulatif'] = jenis_bulan['Total Pendapatan (Rp)'].cumsum()
            fig_b = go.Figure()
            fig_b.add_trace(go.Bar(x=jenis_bulan['Jenis Kopi'], y=jenis_bulan['Total Pendapatan (Rp)'],
                                    name="Pendapatan", marker_color=ACCENT, yaxis='y1'))
            fig_b.add_trace(go.Scatter(x=jenis_bulan['Jenis Kopi'], y=jenis_bulan['kumulatif'], name="Kumulatif",
                                        mode='lines', line=dict(color=ESPRESSO, width=2), yaxis='y2'))
            fig_b.update_layout(height=340, plot_bgcolor="white",
                                yaxis=dict(title="Pendapatan (Rp)"),
                                yaxis2=dict(title="Kumulatif (Rp)", overlaying='y', side='right'),
                                legend=dict(orientation='h', y=1.15), xaxis_tickangle=-25)
            st.plotly_chart(fig_b, use_container_width=True, config={"displayModeBar": False})
            if not is_aktual:
                st.caption("Nilai untuk bulan prediksi merupakan rata-rata prediksi Random Forest dan LightGBM.")

    st.write("")

    num_days, daily_avg, weekly_df = daily_weekly_estimate(sel['Tahun'], sel['bulan_num'], sel['Total Pendapatan (Rp)'])

    st.info(
        "Data sumber dan model prediksi (Random Forest & LightGBM) bekerja di level **bulanan**. "
        "Angka harian/mingguan di bawah ini **bukan hasil prediksi model**, melainkan diturunkan dari "
        "pendapatan bulanan (aktual atau prediksi) dengan membagi rata sesuai jumlah hari dalam bulan."
    )

    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        c1.metric(f"Total Pendapatan {sel['Bulan']} {sel['Tahun']} ({sel['tipe']})", rupiah(sel['Total Pendapatan (Rp)']))
        c2.metric("Estimasi Harian (rata-rata)", rupiah(daily_avg))
        c3.metric("Jumlah Hari dalam Bulan", f"{num_days} hari")

    st.write("")
    with st.container(border=True):
        st.markdown(f"##### Tampilan Kalender — {sel['Bulan']} {sel['Tahun']}")
        st.caption(
            "Karena data sumber hanya mencatat transaksi di level bulanan, setiap tanggal pada bulan ini "
            "menampilkan angka estimasi harian yang sama (bukan angka unik per tanggal). Tanggal abu-abu "
            "adalah tanggal dari bulan sebelum/sesudahnya."
        )
        st.markdown(render_month_calendar_grid(sel['Tahun'], sel['bulan_num'], daily_avg), unsafe_allow_html=True)

    st.write("")
    with st.container(border=True):
        st.markdown("##### Estimasi Pendapatan per Minggu")
        weekly_show = weekly_df.copy()
        weekly_show['Estimasi Pendapatan (Rp)'] = weekly_show['Estimasi Pendapatan (Rp)'].apply(rupiah)
        st.dataframe(weekly_show, use_container_width=True, hide_index=True)

        fig_week = px.bar(weekly_df, x='Minggu ke', y='Estimasi Pendapatan (Rp)',
                           text=weekly_df['Estimasi Pendapatan (Rp)'].apply(rupiah),
                           color_discrete_sequence=[ACCENT])
        fig_week.update_traces(textposition='outside')
        fig_week.update_layout(height=360, plot_bgcolor="white", yaxis_title="Estimasi Pendapatan (Rp)")
        st.plotly_chart(fig_week, use_container_width=True, config={"displayModeBar": False})

# =====================================================================
# 📄 LAPORAN (khusus Pemilik)
# =====================================================================
elif IS_PEMILIK and menu == "📄 Laporan":
    render_page_header("📄", "Laporan", "Unduh ringkasan laporan penjualan dalam format Word atau PDF.")

    with st.container(border=True):
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
                                                         total_qty, rata_harga, ringkasan_jenis,
                                                         logo_path=LOGO_PATH)
                    st.download_button(
                        "⬇️ Unduh Laporan (Word)", data=docx_bytes,
                        file_name=f"laporan_penjualan_{file_tag}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    )
                else:
                    st.warning("Modul `python-docx` belum terpasang. Tambahkan `python-docx` ke requirements.txt.")

                if REPORTLAB_OK:
                    pdf_bytes = generate_laporan_pdf(periode_text, jenis_text, total_pendapatan,
                                                       total_qty, rata_harga, ringkasan_jenis,
                                                       logo_path=LOGO_PATH)
                    st.download_button(
                        "⬇️ Unduh Laporan (PDF)", data=pdf_bytes,
                        file_name=f"laporan_penjualan_{file_tag}.pdf",
                        mime="application/pdf",
                    )
                else:
                    st.warning("Modul `reportlab` belum terpasang. Tambahkan `reportlab` ke requirements.txt.")

st.divider()
st.caption("Dashboard ini dijalankan di Google Colab menggunakan Python, Streamlit, Scikit-learn, dan LightGBM ")