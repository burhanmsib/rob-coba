# modules/crud.py
import streamlit as st
import mysql.connector
from mysql.connector import Error

TABLE_NAME = "rob_coba"

# =============== KONEKSI DATABASE ===============
def get_db_connection():
    """Buat koneksi ke database menggunakan kredensial dari secrets.toml"""
    try:
        conn = mysql.connector.connect(
            host=st.secrets["mysql"]["host"],
            user=st.secrets["mysql"]["user"],
            password=st.secrets["mysql"]["password"],
            database=st.secrets["mysql"]["database"],
            port=st.secrets["mysql"].get("port", 3306),
            connection_timeout=10
        )
        return conn
    except Error as e:
        st.error(f"❌ Gagal terhubung ke database: {e}")
        return None


# =============== READ ===============
def fetch_all_data():
    """Ambil seluruh data dari tabel"""
    conn = get_db_connection()
    if not conn:
        return []
    cur = conn.cursor(dictionary=True)
    cur.execute(
        f"""
        SELECT `No`, `Tanggal`, `Lokasi`, `Kabupaten`, `Provinsi`,
               `Latitude`, `Longitude`, `Gambar`
        FROM `{TABLE_NAME}`
        ORDER BY `Tanggal` DESC, `No` DESC
        """
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def fetch_filtered_data(start_date=None, end_date=None, provinsi=None, kabupaten=None):
    """Ambil data berdasarkan filter opsional"""
    conn = get_db_connection()
    if not conn:
        return []
    cur = conn.cursor(dictionary=True)

    q = f"""
        SELECT `No`, `Tanggal`, `Lokasi`, `Kabupaten`, `Provinsi`,
               `Latitude`, `Longitude`, `Gambar`
        FROM `{TABLE_NAME}` WHERE 1=1
    """
    params = []

    if start_date:
        q += " AND `Tanggal` >= %s"
        params.append(start_date)
    if end_date:
        q += " AND `Tanggal` <= %s"
        params.append(end_date)
    if provinsi:
        q += " AND `Provinsi` LIKE %s"
        params.append(f"%{provinsi}%")
    if kabupaten and kabupaten.strip():
        q += " AND `Kabupaten` LIKE %s"
        params.append(f"%{kabupaten.strip()}%")

    q += " ORDER BY `Tanggal` DESC, `No` DESC"

    cur.execute(q, tuple(params))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


# =============== CREATE ===============
def insert_data(tanggal, lokasi, kabupaten, provinsi, latitude, longitude, gambar):
    """Tambahkan satu data baru ke tabel"""
    conn = get_db_connection()
    if not conn:
        return
    cur = conn.cursor()
    sql = f"""
        INSERT INTO `{TABLE_NAME}`
        (`Tanggal`, `Lokasi`, `Kabupaten`, `Provinsi`,
         `Latitude`, `Longitude`, `Gambar`)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    cur.execute(sql, (tanggal, lokasi, kabupaten, provinsi, latitude, longitude, gambar))
    conn.commit()
    cur.close()
    conn.close()


# =============== UPDATE ===============
def update_data(no_id, tanggal, lokasi, kabupaten, provinsi, latitude, longitude, gambar):
    """Perbarui data berdasarkan ID"""
    conn = get_db_connection()
    if not conn:
        return
    cur = conn.cursor()
    sql = f"""
        UPDATE `{TABLE_NAME}` SET
            `Tanggal`=%s, `Lokasi`=%s, `Kabupaten`=%s, `Provinsi`=%s,
            `Latitude`=%s, `Longitude`=%s, `Gambar`=%s
        WHERE `No`=%s
    """
    cur.execute(sql, (tanggal, lokasi, kabupaten, provinsi, latitude, longitude, gambar, no_id))
    conn.commit()
    cur.close()
    conn.close()


# =============== DELETE ===============
def delete_data(no_id):
    """Hapus data berdasarkan ID"""
    conn = get_db_connection()
    if not conn:
        return
    cur = conn.cursor()
    cur.execute(f"DELETE FROM `{TABLE_NAME}` WHERE `No`=%s", (no_id,))
    conn.commit()
    cur.close()
    conn.close()