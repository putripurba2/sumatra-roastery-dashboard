-- Skema database Sumatra Roastery Dashboard (SQLite)

CREATE TABLE IF NOT EXISTS transaksi (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    tahun          INTEGER NOT NULL,
    bulan          INTEGER NOT NULL,   -- 1-12
    jenis_kopi     TEXT    NOT NULL,
    varian_kopi    TEXT,
    ukuran_kemasan TEXT,
    harga          INTEGER NOT NULL,
    jumlah_terjual INTEGER NOT NULL,
    pendapatan     INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    username      TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL        -- 'admin' atau 'pemilik'
);

CREATE INDEX IF NOT EXISTS idx_transaksi_periode ON transaksi (tahun, bulan);
CREATE INDEX IF NOT EXISTS idx_transaksi_jenis   ON transaksi (jenis_kopi);

-- Pengganti sheet "Rekap Bulanan" (dihitung otomatis, tidak disimpan ganda)
CREATE VIEW IF NOT EXISTS rekap_bulanan AS
SELECT tahun, bulan, SUM(pendapatan) AS total_pendapatan
FROM transaksi GROUP BY tahun, bulan;

-- Pengganti sheet "Pendapatan Per Jenis Kopi"
CREATE VIEW IF NOT EXISTS pendapatan_per_jenis AS
SELECT tahun, bulan, jenis_kopi, SUM(pendapatan) AS total_pendapatan
FROM transaksi GROUP BY tahun, bulan, jenis_kopi;
