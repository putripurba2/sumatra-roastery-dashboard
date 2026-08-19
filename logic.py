"""
Modul logika data untuk dashboard Sumatra Roastery.
Berisi: pemuatan & pembentukan dataset, training model (Random Forest & LightGBM),
pembuatan laporan (Excel/Word/PDF), dan prediksi bulan berikutnya.
Dipisah dari app.py supaya app.py fokus ke tampilan (UI) saja.
"""
import streamlit as st
import pandas as pd
import numpy as np
import time
import io
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import lightgbm as lgb

try:
    from docx import Document
    from docx.shared import Pt
    DOCX_OK = True
except ImportError:
    DOCX_OK = False

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    REPORTLAB_OK = True
except ImportError:
    REPORTLAB_OK = False


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
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return buf.getvalue()


def generate_laporan_docx(periode_text, jenis_text, total_pendapatan, total_qty, rata_harga, ringkasan_jenis):
    doc = Document()
    doc.add_heading('Laporan Penjualan — Sumatra Roastery Medan', level=1)
    doc.add_paragraph(f"Periode: {periode_text}")
    doc.add_paragraph(f"Jenis Kopi: {jenis_text}")
    doc.add_paragraph(f"Tanggal Cetak: {pd.Timestamp.now().strftime('%d %B %Y')}")

    doc.add_heading('Ringkasan', level=2)
    doc.add_paragraph(f"Total Pendapatan: {rupiah(total_pendapatan)}")
    doc.add_paragraph(f"Total Unit Terjual: {int(total_qty):,}".replace(",", "."))
    doc.add_paragraph(f"Rata-rata Harga: {rupiah(rata_harga)}")

    doc.add_heading('Rincian per Jenis Kopi', level=2)
    table = doc.add_table(rows=1, cols=3)
    table.style = 'Light Grid Accent 1'
    hdr = table.rows[0].cells
    hdr[0].text, hdr[1].text, hdr[2].text = 'Jenis Kopi', 'Total Pendapatan (Rp)', 'Jumlah Terjual'
    for _, row in ringkasan_jenis.iterrows():
        cells = table.add_row().cells
        cells[0].text = str(row['Jenis Kopi'])
        cells[1].text = rupiah(row['Total Pendapatan (Rp)'])
        cells[2].text = str(int(row['Jumlah Terjual']))

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def generate_laporan_pdf(periode_text, jenis_text, total_pendapatan, total_qty, rata_harga, ringkasan_jenis):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = [
        Paragraph("Laporan Penjualan — Sumatra Roastery Medan", styles['Title']),
        Spacer(1, 12),
        Paragraph(f"Periode: {periode_text}", styles['Normal']),
        Paragraph(f"Jenis Kopi: {jenis_text}", styles['Normal']),
        Paragraph(f"Tanggal Cetak: {pd.Timestamp.now().strftime('%d %B %Y')}", styles['Normal']),
        Spacer(1, 12),
        Paragraph("Ringkasan", styles['Heading2']),
        Paragraph(f"Total Pendapatan: {rupiah(total_pendapatan)}", styles['Normal']),
        Paragraph(f"Total Unit Terjual: {int(total_qty):,}".replace(",", "."), styles['Normal']),
        Paragraph(f"Rata-rata Harga: {rupiah(rata_harga)}", styles['Normal']),
        Spacer(1, 12),
        Paragraph("Rincian per Jenis Kopi", styles['Heading2']),
        Spacer(1, 6),
    ]

    data = [['Jenis Kopi', 'Total Pendapatan (Rp)', 'Jumlah Terjual']]
    for _, row in ringkasan_jenis.iterrows():
        data.append([row['Jenis Kopi'], rupiah(row['Total Pendapatan (Rp)']), str(int(row['Jumlah Terjual']))])
    tbl = Table(data, hAlign='LEFT')
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0F6B5C")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
    ]))
    elements.append(tbl)
    doc.build(elements)
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