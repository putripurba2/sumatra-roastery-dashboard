import streamlit as st
import pandas as pd
import numpy as np
import time
import os
import glob
import base64
import plotly.graph_objects as go
import plotly.express as px
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import lightgbm as lgb

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def asset_path(filename):
    p = os.path.join(SCRIPT_DIR, filename)
    return p if os.path.exists(p) else None

FAVICON = asset_path("favicon.png")
BANNER_LOGIN = asset_path("preview_banner_dashboard.png")
BANNER_MAIN = asset_path("banner_kopi.jpg")

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

st.markdown(f"""
<style>
/* ---- Base app background & typography ---- */
.stApp {{
    background-color: {CREAM};
}}
html, body, [class*="css"] {{
    color: {ESPRESSO} !important;
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
}}

/* ---- Kill the stray white top toolbar ---- */
[data-testid="stHeader"] {{
    background-color: {CREAM};
}}
[data-testid="stToolbar"] {{
    background-color: transparent;
}}

/* ---- Sidebar ---- */
[data-testid="stSidebar"] {{
    background-color: {CREAM_DARK};
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

/* ---- Tabs ---- */
.stTabs [data-baseweb="tab-list"] {{
    gap: 4px;
    border-bottom: 3px solid {BORDER};
}}
.stTabs [data-baseweb="tab"] {{
    color: {ESPRESSO_SOFT} !important;
    font-weight: 700;
}}
.stTabs [aria-selected="true"] {{
    color: {PRIMARY} !important;
    border-bottom: 4px solid {PRIMARY} !important;
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

BULAN_ORDER = ['Januari','Februari','Maret','April','Mei','Juni','Juli','Agustus','September','Oktober','November','Desember']
BULAN_MAP = {b: i + 1 for i, b in enumerate(BULAN_ORDER)}


@st.cache_data
def load_raw(file):
    xls = pd.ExcelFile(file)
    daily = pd.read_excel(xls, sheet_name='Dataset Harian 2023-2025', header=3)
    per_jenis = pd.read_excel(xls, sheet_name='Pendapatan Per Jenis Kopi', header=2)
    rekap = pd.read_excel(xls, sheet_name='Rekap Bulanan', header=2)
    return daily, per_jenis, rekap


@st.cache_data
def build_dataset(daily, per_jenis, rekap):
    agg_harga = (
        daily.groupby(['Tahun', 'Bulan', 'Jenis Kopi'])
        .apply(lambda g: (g['Harga (Rp)'] * g['Jumlah Terjual']).sum() / g['Jumlah Terjual'].sum()
               if g['Jumlah Terjual'].sum() > 0 else g['Harga (Rp)'].mean())
        .reset_index(name='harga_rata2')
    )

    df = per_jenis.merge(agg_harga, on=['Tahun', 'Bulan', 'Jenis Kopi'], how='left')
    df['bulan_num'] = df['Bulan'].map(BULAN_MAP)
    df['periode'] = df['Tahun'] * 100 + df['bulan_num']
    df = df.sort_values(['Jenis Kopi', 'periode']).reset_index(drop=True)
    df['lag_1'] = df.groupby('Jenis Kopi')['Total Pendapatan (Rp)'].shift(1)

    rekap = rekap.copy()
    rekap['bulan_num'] = rekap['Bulan'].map(BULAN_MAP)
    rekap['periode'] = rekap['Tahun'] * 100 + rekap['bulan_num']
    avg_overall = rekap['Total Pendapatan (Rp)'].mean()
    rekap['kategori_tren'] = np.where(rekap['Total Pendapatan (Rp)'] >= avg_overall, 'Tinggi', 'Rendah')

    df = df.merge(rekap[['periode', 'kategori_tren']], on='periode', how='left')
    return df, rekap, avg_overall


@st.cache_data
def train_models(df, split_ratio):
    le_jenis = LabelEncoder()
    le_tren = LabelEncoder()
    df_model = df.dropna(subset=['lag_1']).copy()
    df_model['jenis_kopi_enc'] = le_jenis.fit_transform(df_model['Jenis Kopi'])
    df_model['kategori_tren_enc'] = le_tren.fit_transform(df_model['kategori_tren'])
    df_model = df_model.sort_values('periode').reset_index(drop=True)

    features = ['Tahun', 'bulan_num', 'jenis_kopi_enc', 'harga_rata2', 'lag_1', 'kategori_tren_enc']
    target = 'Total Pendapatan (Rp)'

    periodes = sorted(df_model['periode'].unique())
    split_periode = periodes[int(len(periodes) * split_ratio)]
    train = df_model[df_model['periode'] < split_periode]
    test = df_model[df_model['periode'] >= split_periode]

    X_train, y_train = train[features], train[target]
    X_test, y_test = test[features], test[target]

    results = {}
    preds = {}

    t0 = time.time()
    rf = RandomForestRegressor(n_estimators=200, random_state=42)
    rf.fit(X_train, y_train)
    rf_time = time.time() - t0
    pred_rf = rf.predict(X_test)
    results['Random Forest'] = dict(
        MAE=mean_absolute_error(y_test, pred_rf),
        RMSE=np.sqrt(mean_squared_error(y_test, pred_rf)),
        R2=r2_score(y_test, pred_rf),
        Training_Time=rf_time,
    )
    preds['Random Forest'] = pred_rf

    t0 = time.time()
    lgbm = lgb.LGBMRegressor(n_estimators=200, random_state=42, verbose=-1)
    lgbm.fit(X_train, y_train)
    lgb_time = time.time() - t0
    pred_lgb = lgbm.predict(X_test)
    results['LightGBM'] = dict(
        MAE=mean_absolute_error(y_test, pred_lgb),
        RMSE=np.sqrt(mean_squared_error(y_test, pred_lgb)),
        R2=r2_score(y_test, pred_lgb),
        Training_Time=lgb_time,
    )
    preds['LightGBM'] = pred_lgb

    fi = pd.DataFrame({
        'Fitur': features,
        'Random Forest': rf.feature_importances_ / rf.feature_importances_.sum(),
        'LightGBM': lgbm.feature_importances_ / lgbm.feature_importances_.sum(),
    })

    test_out = test[['Tahun', 'Bulan', 'Jenis Kopi', 'Total Pendapatan (Rp)']].copy()
    test_out['Prediksi Random Forest'] = pred_rf
    test_out['Prediksi LightGBM'] = pred_lgb

    return results, fi, test_out, split_periode


def rupiah(x):
    return f"Rp {x:,.0f}".replace(",", ".")


def to_excel_bytes(df, sheet_name="Data"):
    import io
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return buf.getvalue()


@st.cache_data
def forecast_next_month(df):
    """Latih model pakai SELURUH data (bukan hanya data training) lalu prediksi bulan setelah periode terakhir."""
    le_jenis = LabelEncoder()
    le_tren = LabelEncoder()
    df_model = df.dropna(subset=['lag_1']).copy()
    df_model['jenis_kopi_enc'] = le_jenis.fit_transform(df_model['Jenis Kopi'])
    df_model['kategori_tren_enc'] = le_tren.fit_transform(df_model['kategori_tren'])
    df_model = df_model.sort_values('periode').reset_index(drop=True)

    features = ['Tahun', 'bulan_num', 'jenis_kopi_enc', 'harga_rata2', 'lag_1', 'kategori_tren_enc']
    target = 'Total Pendapatan (Rp)'

    rf_full = RandomForestRegressor(n_estimators=200, random_state=42)
    rf_full.fit(df_model[features], df_model[target])
    lgb_full = lgb.LGBMRegressor(n_estimators=200, random_state=42, verbose=-1)
    lgb_full.fit(df_model[features], df_model[target])

    last_periode = df_model['periode'].max()
    last_tahun, last_bulan_num = last_periode // 100, last_periode % 100
    next_bulan_num = 1 if last_bulan_num == 12 else last_bulan_num + 1
    next_tahun = last_tahun + 1 if last_bulan_num == 12 else last_tahun
    next_bulan_nama = BULAN_ORDER[next_bulan_num - 1]

    last_kategori_tren = df_model.loc[df_model['periode'] == last_periode, 'kategori_tren_enc'].iloc[0]

    rows = []
    for jenis in df_model['Jenis Kopi'].unique():
        sub = df_model[df_model['Jenis Kopi'] == jenis].sort_values('periode')
        lag_1_next = sub[target].iloc[-1]
        harga_next = sub['harga_rata2'].tail(3).mean()
        jenis_enc = sub['jenis_kopi_enc'].iloc[-1]
        x_next = pd.DataFrame([{
            'Tahun': next_tahun, 'bulan_num': next_bulan_num, 'jenis_kopi_enc': jenis_enc,
            'harga_rata2': harga_next, 'lag_1': lag_1_next, 'kategori_tren_enc': last_kategori_tren,
        }])[features]
        pred_rf = rf_full.predict(x_next)[0]
        pred_lgb = lgb_full.predict(x_next)[0]
        rows.append({'Jenis Kopi': jenis, 'Pendapatan Bulan Terakhir (Rp)': lag_1_next,
                      'Prediksi Random Forest (Rp)': pred_rf, 'Prediksi LightGBM (Rp)': pred_lgb})

    forecast_df = pd.DataFrame(rows).sort_values('Prediksi Random Forest (Rp)', ascending=False).reset_index(drop=True)
    return forecast_df, next_bulan_nama, next_tahun


# ---------- LOGIN DUA PERAN ----------
CREDENTIALS = {
    "peneliti": {"password": "peneliti123", "role": "Peneliti"},
    "pemilik": {"password": "pemilik123", "role": "Pemilik/Pengelola"},
}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None

if not st.session_state.logged_in:
    st.title("☕ Dashboard Analisis Tren & Prediksi Pendapatan")
    st.caption("Sumatra Roastery Medan — Random Forest vs LightGBM")
    if BANNER_LOGIN:
        st.image(BANNER_LOGIN, use_container_width=True)
    st.subheader("🔒 Login")
    st.caption("Masukkan akun sesuai peran Anda untuk mengakses dashboard.")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Masuk")
    if submitted:
        user = CREDENTIALS.get(username.strip().lower())
        if user and user["password"] == password:
            st.session_state.logged_in = True
            st.session_state.role = user["role"]
            st.rerun()
        else:
            st.error("Username atau password salah.")
    st.stop()
@st.cache_data
def get_base64_image(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


if BANNER_MAIN:
    photo_b64 = get_base64_image(BANNER_MAIN)
    photo_ext = os.path.splitext(BANNER_MAIN)[1].lower().replace(".", "")
    if photo_ext == "jpg":
        photo_ext = "jpeg"

    GOLD = "#C9A24B"
    W, H = 1600, 480
    X0, Xb = 860, 780  # X0: titik lengkung di atas & bawah, Xb: puncak lengkungan ke kiri

    curve = (
        f"C {X0-50},{H*0.27:.1f} {Xb},{H*0.27:.1f} {Xb},{H/2:.1f} "
        f"C {Xb},{H*0.73:.1f} {X0-50},{H*0.73:.1f} {X0},{H}"
    )
    photo_d = f"M0,0 L{X0},0 {curve} L0,{H} Z"
    green_d = f"M{X0},0 {curve} L{W},{H} L{W},0 Z"
    gold_d = f"M{X0},0 {curve}"

    banner_html = f"""
    <div style="position:relative;width:100%;border-radius:22px;overflow:hidden;
                box-shadow:0 6px 18px rgba(0,0,0,.15);margin-bottom:8px;">
      <svg viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid slice"
           style="display:block;width:100%;height:auto;">
        <defs>
          <clipPath id="photoClip"><path d="{photo_d}" /></clipPath>
        </defs>

        <rect x="0" y="0" width="{W}" height="{H}" fill="{PRIMARY}" />

        <image href="data:image/{photo_ext};base64,{photo_b64}"
               x="0" y="0" width="{W}" height="{H}"
               preserveAspectRatio="xMidYMid slice" clip-path="url(#photoClip)" />

        <path d="{green_d}" fill="{PRIMARY}" />

        <!-- motif daun transparan -->
        <g opacity="0.16" stroke="#F4EFE2" fill="none" stroke-width="2.5">
          <path d="M1360,60 C1300,40 1250,70 1240,120 C1230,170 1270,200 1320,190
                   C1370,180 1400,130 1390,90 C1385,75 1375,65 1360,60 Z" />
          <path d="M1300,80 C1320,110 1330,140 1320,175" />
          <path d="M1480,140 C1430,120 1390,150 1385,195 C1380,240 1415,265 1460,258
                   C1505,250 1530,205 1520,165 C1515,150 1500,145 1480,140 Z" />
          <path d="M1430,155 C1450,180 1460,205 1450,235" />
        </g>

        <!-- motif biji kopi transparan -->
        <g opacity="0.14" stroke="#F4EFE2" fill="none" stroke-width="2.5">
          <ellipse cx="1430" cy="360" rx="46" ry="60" />
          <line x1="1430" y1="303" x2="1430" y2="417" />
          <ellipse cx="1500" cy="400" rx="42" ry="55" transform="rotate(15 1500 400)" />
          <line x1="1500" y1="348" x2="1500" y2="452" />
          <ellipse cx="1370" cy="410" rx="40" ry="52" transform="rotate(-12 1370 410)" />
          <line x1="1370" y1="360" x2="1370" y2="460" />
        </g>

        <!-- garis pembatas emas -->
        <path d="{gold_d}" fill="none" stroke="{GOLD}" stroke-width="7" stroke-linecap="round" />

        <foreignObject x="{Xb+70}" y="0" width="{W-Xb-120}" height="{H}">
          <div xmlns="http://www.w3.org/1999/xhtml" style="
              height:100%;display:flex;flex-direction:column;justify-content:center;
              font-family:'Segoe UI','Helvetica Neue',Arial,sans-serif;padding-right:10px;">
            <h1 style="color:#ffffff;font-size:44px;font-weight:800;line-height:1.15;margin:0 0 14px 0;">
              Dashboard Analisis Tren<br>&amp; Prediksi Pendapatan
            </h1>
            <p style="color:#F5EFE3;font-size:22px;margin:0 0 16px 0;">
              Sumatra Roastery Medan — Random Forest vs LightGBM
            </p>
            <div style="width:200px;height:3px;background:{ACCENT};margin:0 0 18px 0;"></div>
            <p style="color:#FFD9B0;font-size:17px;font-style:italic;margin:0;line-height:1.5;">
              Kopi asli Sumatra Roastery Medan — dari kebun hingga wawasan bisnis
            </p>
          </div>
        </foreignObject>
      </svg>
    </div>
    """
    st.markdown(banner_html, unsafe_allow_html=True)

else:
    st.title("☕ Dashboard Analisis Tren & Prediksi Pendapatan")
    st.caption("Sumatra Roastery Medan — Random Forest vs LightGBM")

with st.sidebar:
    st.success(f"Login sebagai: **{st.session_state.role}**")
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.role = None
        st.rerun()
    st.divider()

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

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 Data Aktual", "📈 Analisis Tren", "🔮 Prediksi & Evaluasi", "⭐ Feature Importance", "📅 Prediksi Bulan Depan"])

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
    daily_show = daily.head(50).copy()
    daily_show['Harga (Rp)'] = daily_show['Harga (Rp)'].apply(rupiah)
    daily_show['Pendapatan (Rp)'] = daily_show['Pendapatan (Rp)'].apply(rupiah)
    st.dataframe(daily_show, use_container_width=True, hide_index=True)
    st.download_button("⬇️ Download Excel — Data Transaksi Harian",
                        data=to_excel_bytes(daily_show, "Transaksi Harian"),
                        file_name="data_transaksi_harian.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

with tab2:
    st.subheader("Tren Pendapatan Bulanan (2023–2025)")
    colors = [PRIMARY if k == 'Tinggi' else ACCENT for k in rekap['kategori_tren']]
    labels = [f"{b[:3]} {t}" for b, t in zip(rekap['Bulan'], rekap['Tahun'])]

    fig = go.Figure()
    fig.add_trace(go.Bar(x=labels, y=rekap['Total Pendapatan (Rp)'], marker_color=colors, name="Pendapatan"))
    fig.add_hline(y=avg_overall, line_dash="dash", line_color="#888",
                  annotation_text=f"Rata-rata: {rupiah(avg_overall)}")
    fig.update_layout(height=460, plot_bgcolor="white", yaxis_title="Pendapatan (Rp)",
                       xaxis_tickangle=-60, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Rata-rata Pendapatan Bulanan", rupiah(avg_overall))
    c2.metric("Bulan Kategori Tinggi", int((rekap['kategori_tren'] == 'Tinggi').sum()))
    c3.metric("Bulan Kategori Rendah", int((rekap['kategori_tren'] == 'Rendah').sum()))

    st.subheader("Pendapatan per Jenis Kopi (Total 2023–2025)")
    jenis_total = per_jenis.groupby('Jenis Kopi')['Total Pendapatan (Rp)'].sum().sort_values(ascending=False).reset_index()
    fig2 = px.bar(jenis_total, x='Jenis Kopi', y='Total Pendapatan (Rp)', color_discrete_sequence=[PRIMARY])
    fig2.update_layout(height=380, plot_bgcolor="white")
    st.plotly_chart(fig2, use_container_width=True)

with tab3:
    st.subheader("Perbandingan Performa Model")
    res_df = pd.DataFrame(results).T
    res_df.columns = ['MAE', 'RMSE', 'R²', 'Training Time (detik)']
    best_model = res_df['MAE'].idxmin()
    st.dataframe(res_df.style.format({'MAE': '{:,.0f}', 'RMSE': '{:,.0f}', 'R²': '{:.4f}', 'Training Time (detik)': '{:.4f}'}),
                 use_container_width=True)
    st.success(f"Model dengan performa terbaik (MAE terendah): **{best_model}**")

    st.subheader("Aktual vs Prediksi pada Data Uji")
    jenis_pilih = st.selectbox("Pilih jenis kopi", sorted(test_out['Jenis Kopi'].unique()))
    sub = test_out[test_out['Jenis Kopi'] == jenis_pilih].copy()
    sub['label'] = sub['Bulan'].str[:3] + " " + sub['Tahun'].astype(str)

    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=sub['label'], y=sub['Total Pendapatan (Rp)'], name="Aktual", mode='lines+markers', line=dict(color="#333", width=3)))
    fig3.add_trace(go.Scatter(x=sub['label'], y=sub['Prediksi Random Forest'], name="Prediksi RF", mode='lines+markers', line=dict(color=PRIMARY, dash='dash')))
    fig3.add_trace(go.Scatter(x=sub['label'], y=sub['Prediksi LightGBM'], name="Prediksi LightGBM", mode='lines+markers', line=dict(color=ACCENT, dash='dot')))
    fig3.update_layout(height=420, plot_bgcolor="white", yaxis_title="Pendapatan (Rp)")
    st.plotly_chart(fig3, use_container_width=True)

    with st.expander("Lihat tabel hasil prediksi lengkap"):
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
    st.plotly_chart(fig4, use_container_width=True)
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
    st.plotly_chart(fig5, use_container_width=True)

    st.info("Catatan asumsi: harga rata-rata memakai rata-rata 3 bulan terakhir per jenis kopi, dan kategori tren memakai kategori bulan terakhir yang datanya tersedia (karena kategori tren bulan depan belum bisa diketahui sebelum pendapatan aktualnya terjadi).")

st.divider()
st.caption("Dashboard ini dijalankan di Google Colab menggunakan Python, Streamlit, Scikit-learn, dan LightGBM ")