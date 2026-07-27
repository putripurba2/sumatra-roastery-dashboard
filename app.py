import streamlit as st
import pandas as pd
import numpy as np
import time
import plotly.graph_objects as go
import plotly.express as px
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import lightgbm as lgb
import os
import glob
import base64

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_FAVICON_PATH = os.path.join(SCRIPT_DIR, "favicon.png")
_PAGE_ICON = _FAVICON_PATH if os.path.exists(_FAVICON_PATH) else "☕"

st.set_page_config(page_title="Dashboard Prediksi Pendapatan - Sumatra Roastery Medan", page_icon=_PAGE_ICON, layout="wide")

def inject_custom_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fraunces:wght@500;600;700&family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    h1, h2, h3 { font-family: 'Fraunces', Georgia, serif !important; }

    /* Header bar Streamlit (bar putih di paling atas) */
    header[data-testid="stHeader"] {
        background: #12201C !important;
    }
    div[data-testid="stToolbar"] { background: transparent !important; }
    div[data-testid="stDecoration"] { background: transparent !important; }

    /* Kotak input teks (username, password, dsb) */
    div[data-testid="stTextInput"] input {
        background: #1B2E27 !important;
        color: #F5EFE4 !important;
        border: 1px solid rgba(181,80,45,0.4) !important;
        border-radius: 8px !important;
    }
    div[data-testid="stTextInput"] input::placeholder { color: #7C8F86 !important; }
    div[data-testid="stTextInput"] label { color: #B9AC93 !important; }
    div[data-testid="stTextInput"] svg { fill: #B9AC93 !important; }

    /* Kotak angka & pilihan lain (kalau ada) */
    div[data-testid="stNumberInput"] input,
    div[data-baseweb="select"] > div {
        background: #1B2E27 !important;
        color: #F5EFE4 !important;
        border-color: rgba(181,80,45,0.4) !important;
    }

    /* Label umum widget (proporsi data training, dsb) */
    label { color: #B9AC93 !important; }

    /* Latar utama */
    .stApp { background: #12201C; }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: #0E1C17;
        border-right: 1px solid rgba(181,80,45,0.25);
    }
    section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 {
        color: #F5EFE4 !important;
        font-size: 20px !important;
    }

    /* Judul subbagian (st.subheader) */
    h2 {
        color: #F5EFE4 !important;
        border-bottom: 2px solid #B5502D;
        padding-bottom: 8px;
        margin-top: 28px !important;
    }

    /* Tab navigasi jadi pill segmented control */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: #0E1C17;
        padding: 6px;
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.06);
    }
    .stTabs [data-baseweb="tab"] {
        height: 42px;
        border-radius: 8px;
        color: #B9AC93;
        font-weight: 500;
        background: transparent;
    }
    .stTabs [aria-selected="true"] {
        background: #0F6B5C !important;
        color: #F5EFE4 !important;
        font-weight: 600;
    }

    /* Kartu metrik */
    div[data-testid="stMetric"] {
        background: #1B2E27;
        border: 1px solid rgba(181,80,45,0.25);
        border-radius: 12px;
        padding: 16px 18px;
    }
    div[data-testid="stMetricLabel"] { color: #B9AC93 !important; }
    div[data-testid="stMetricValue"] { color: #F5EFE4 !important; font-family: 'Fraunces', serif !important; }

    /* Tombol */
    .stButton button, .stDownloadButton button {
        background: #0F6B5C;
        color: #F5EFE4;
        border: none;
        border-radius: 8px;
        font-weight: 500;
    }
    .stButton button:hover, .stDownloadButton button:hover {
        background: #B5502D;
        color: #F5EFE4;
    }

    /* Kotak upload file */
    div[data-testid="stFileUploaderDropzone"] {
        background: #1B2E27;
        border: 1.5px dashed rgba(181,80,45,0.5);
        border-radius: 10px;
    }

    /* Slider aksen warna terracotta */
    div[data-testid="stSlider"] [role="slider"] { background-color: #B5502D !important; }
    div[data-testid="stSliderTrackFilled"] { background-color: #B5502D !important; }

    /* Kotak info/success/warning */
    div[data-testid="stAlert"] { border-radius: 10px; }

    /* Divider */
    hr { border-color: rgba(181,80,45,0.3) !important; }

    /* Expander */
    details { background: #1B2E27; border-radius: 10px; border: 1px solid rgba(255,255,255,0.06); }

    /* Footer bawaan Streamlit disembunyikan, footer kustom dipakai */
    footer[data-testid="stFooter"] { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

inject_custom_css()

def render_hero_banner():
    """Banner atas dashboard memakai foto asli produk Sumatra Roastery Medan. Muncul di halaman login maupun dashboard utama."""
    photo_path = os.path.join(SCRIPT_DIR, "banner_kopi.jpg")

    if os.path.exists(photo_path):
        with open(photo_path, "rb") as f:
            photo_b64 = base64.b64encode(f.read()).decode()
        img_tag = f'<img src="data:image/jpeg;base64,{photo_b64}" style="width:100%;height:100%;object-fit:cover;border-radius:16px 0 0 16px;display:block;min-height:220px;"/>'
    else:
        img_tag = '<div style="width:100%;height:100%;min-height:220px;background:#0B4F44;border-radius:16px 0 0 16px;"></div>'

    st.markdown(f"""
    <div style="display:flex; border-radius:16px; overflow:hidden; box-shadow:0 4px 18px rgba(0,0,0,0.18); margin-bottom:14px;">
      <div style="flex:0 0 260px;">
        {img_tag}
      </div>
      <div style="flex:1; background:linear-gradient(135deg, #0F6B5C, #0B4F44); padding:28px 36px; display:flex; flex-direction:column; justify-content:center;">
        <h1 style="color:#F5EFE4; font-family:'Fraunces',Georgia,serif; font-size:34px; font-weight:700; margin:0 0 6px 0; line-height:1.2;">
          Sumatra Roastery Medan
        </h1>
        <p style="color:#D9CBB4; font-family:'Inter',sans-serif; font-size:16px; margin:0 0 10px 0;">
          Usaha Kopi Specialty — Medan, Sumatera Utara
        </p>
        <p style="color:#B9AC93; font-family:'Inter',sans-serif; font-size:14px; margin:0 0 14px 0; max-width:420px; line-height:1.5;">
          Menghadirkan kopi specialty pilihan dari dataran tinggi Sumatra — mulai dari Arabika Gayo, Arabika Sumut, hingga Robusta — diracik dan disangrai langsung untuk penikmat kopi sejati.
        </p>
        <div style="width:220px; height:2px; background:#B5502D; opacity:0.8; margin-bottom:10px;"></div>
        <p style="color:#7C8F86; font-family:'Inter',sans-serif; font-size:12px; margin:0;">
          Dashboard Analisis Tren &amp; Prediksi Pendapatan — Random Forest vs LightGBM
        </p>
      </div>
    </div>
    """, unsafe_allow_html=True)


BULAN_ORDER = ['Januari','Februari','Maret','April','Mei','Juni','Juli','Agustus','September','Oktober','November','Desember']
BULAN_MAP = {b: i + 1 for i, b in enumerate(BULAN_ORDER)}

PRIMARY = "#0F6B5C"
ACCENT = "#B5502D"
GRID = "#e5e0d8"


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


render_hero_banner()

# ---------- LOGIN DUA PERAN ----------
CREDENTIALS = {
    "peneliti": {"password": "peneliti123", "role": "Peneliti"},
    "pemilik": {"password": "pemilik123", "role": "Pemilik/Pengelola"},
}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None

if not st.session_state.logged_in:
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
    st.dataframe(rekap_show.rename(columns={'kategori_tren': 'Kategori Tren'}), use_container_width=True, hide_index=True)

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

st.markdown("""
<div style="margin-top:32px; padding:18px 24px; background:#0E1C17; border-radius:12px;
            border:1px solid rgba(181,80,45,0.25); display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
  <span style="color:#B9AC93; font-family:'Inter',sans-serif; font-size:13px;">
    ☕ Sumatra Roastery Medan — Dashboard Analisis Tren &amp; Prediksi Pendapatan
  </span>
  <span style="color:#7C8F86; font-family:'Inter',sans-serif; font-size:12px;">
    Dibangun dengan Python, Streamlit, Scikit-learn &amp; LightGBM — sesuai BAB IV
  </span>
</div>
""", unsafe_allow_html=True)