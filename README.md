# Dashboard Analisis Tren & Prediksi Pendapatan Sumatra Roastery Medan

![Banner Dashboard](preview_banner_dashboard.jpg)

Aplikasi web berbasis **Streamlit** untuk menganalisis tren penjualan dan memprediksi pendapatan bulanan **Sumatra Roastery Medan** (toko bubuk kopi), dengan membandingkan dua model *machine learning*: **Random Forest** dan **LightGBM**.

- **Nama:** *putri yanti purba*
- **NIM:** *22040161*
- **Program Studi:** *Teknik Informatika*
- **Judul Skripsi:** *ANALISIS TREN DAN PREDIKSI PENDAPATAN PENJUALAN KOPI MENGGUNAKAN ALGORITMA RANDOM FOREST DAN LIGHTGBM PADA SUMATRA ROASTERY MEDAN*

---

## Fitur Utama

- Login dengan 2 peran: **Admin** dan **Pemilik/Pengelola** (akun tersimpan di database, password di-hash)
- **Input Dataset**: unggah file Excel (.xlsx) dan atur proporsi data training/testing (khusus Admin)
- **Data Aktual**: tabel transaksi harian + unduh Excel
- **Analisis Tren**: grafik tren pendapatan per bulan dan per jenis kopi
- **Prediksi & Evaluasi**: hasil prediksi Random Forest dan LightGBM vs data aktual
- **Feature Importance**: fitur yang paling berpengaruh pada tiap model
- **Perbandingan Model**: evaluasi MAE, RMSE, R² dan waktu training
- **Perkiraan Bulan Berikutnya**: prediksi pendapatan bulan depan per jenis kopi
- **Kalender**: heatmap kalender dengan tampilan Bulan / Minggu / Hari
- **Laporan** (khusus Pemilik/Pengelola): laporan penjualan berkop surat, dapat diunduh dalam format **Word (.docx)** dan **PDF**

## Teknologi

Python 3.9+, Streamlit, pandas, numpy, scikit-learn (Random Forest), LightGBM, Plotly, **SQLite** (database), openpyxl, python-docx, reportlab.

## Database (SQLite)

Data disimpan di file **`roastery.db`** (SQLite, bawaan Python, tanpa server).

| Tabel / View | Isi |
|---|---|
| `transaksi` | Transaksi penjualan: tahun, bulan (1-12), jenis kopi, varian, ukuran kemasan, harga, jumlah terjual, pendapatan |
| `users` | Akun login: username, password_hash (PBKDF2), role (`admin` / `pemilik`) |
| `rekap_bulanan` (view) | Total pendapatan per bulan, dihitung otomatis dari `transaksi` |
| `pendapatan_per_jenis` (view) | Total pendapatan per bulan per jenis kopi, dihitung otomatis |

Struktur lengkap ada di `schema.sql`. File Excel tidak lagi diperlukan untuk menjalankan aplikasi.

**Membangun ulang database dari Excel** (opsional, hanya jika data diperbarui): taruh `DATA_BERSIH.xlsx` di folder yang sama, lalu jalankan

```
python buat_database.py
```

Urutan sumber data aplikasi: (1) file yang diunggah Admin lewat menu Input Dataset, (2) `roastery.db`, (3) file `.xlsx` di folder `app.py` sebagai cadangan.

## Cara Menjalankan (Lokal)

```
pip install -r requirements.txt
streamlit run app.py
```

Buka `http://localhost:8501`.

## Deploy ke Streamlit Cloud

1. Buka (https://sumatra-roastery.streamlit.app/) lalu login dengan akun GitHub.
2. **Create app** -> pilih repository ini, branch `main`, file utama `app.py`.
3. **Deploy**. Link aplikasi berbentuk `https://nama-app.streamlit.app`.

## Akun Login Bawaan

| Peran | Username | Password |
|---|---|---|
| Admin | `admin` | `admin123` |
| Pemilik/Pengelola | `pemilik` | `pemilik123` |

Ganti password bawaan sebelum dipakai sungguhan: ubah daftar `USERS` di `buat_database.py`, lalu jalankan ulang `python buat_database.py`.

**Hak akses:** menu **Input Dataset** hanya untuk Admin, menu **Laporan** hanya untuk Pemilik/Pengelola.

## Model & Evaluasi

- **Algoritma:** Random Forest Regressor dan LightGBM Regressor (200 pohon, `random_state=42`)
- **Target:** Total Pendapatan (Rp) per jenis kopi per bulan
- **Fitur:** Tahun, nomor bulan, jenis kopi, harga rata-rata tertimbang, pendapatan bulan sebelumnya (`lag_1`), kategori tren (Tinggi/Rendah)
- **Pembagian data:** berdasarkan urutan waktu (bukan acak), default 80:20
- **Metrik:** MAE, RMSE, R², waktu training

> Nilai harian dan mingguan di menu Kalender adalah **estimasi** dari pembagian rata pendapatan bulanan, bukan hasil prediksi model.

## Struktur Repository

```
app.py                 tampilan dashboard
logic.py               pemuatan data (SQLite/Excel), model, laporan
login.py               halaman login (membaca tabel users)
roastery.db            database SQLite
schema.sql             struktur tabel
buat_database.py       membangun roastery.db dari Excel
requirements.txt       pustaka Python
logo.png, favicon.png, banner_kopi.jpg, preview_banner_dashboard.jpg
```

Identitas laporan (nama usaha, alamat, penanda tangan) dapat diubah di bagian atas `logic.py`.

---
© 2026 Sumatra Roastery Medan
