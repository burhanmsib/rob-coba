import streamlit as st
import pandas as pd
import time
from datetime import datetime
from modules import crud
from modules.utils import save_uploaded_file, safe_float, parse_date_safe, to_db_date_str
from modules.map_visualization import create_map
from modules.gdrive_utils import upload_to_gdrive
from login import login, logout
from pdf import generate_event_pdf, generate_multiple_events_pdf
import requests  # ✅ Penting untuk hosting cloud


# ======================== KONFIGURASI AWAL ========================
st.set_page_config(page_title="Peta Interaktif Banjir Rob BMKG", layout="wide")
st.markdown(
    "<h1 style='text-align: center; font-size: 64px;'>PETA INTERAKTIF BANJIR ROB BMKG</h1>",
    unsafe_allow_html=True
)


# ======================== SISTEM LOGIN ========================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = "user"

if not st.session_state.logged_in:
    login()
    st.stop()

role = st.session_state.role
st.sidebar.markdown(f"👤 Login sebagai: **{role.upper()}**")
logout()


# ======================== SIDEBAR FILTER ========================
menu = st.sidebar.radio("Menu", ["Dashboard", "Tambah Data", "Kelola Data"])
st.sidebar.markdown("---")
st.sidebar.subheader("Filter Data (Dashboard)")
start_date = st.sidebar.date_input("Tanggal Awal", value=None)
end_date = st.sidebar.date_input("Tanggal Akhir", value=None)
provinsi_filter = st.sidebar.text_input("Provinsi")
kabupaten_filter = st.sidebar.text_input("Kabupaten")


# ======================== HELPER ========================
def load_for_dashboard():
    """Ambil data dari database dengan filter"""
    if start_date or end_date or kabupaten_filter.strip() or provinsi_filter.strip():
        s = to_db_date_str(start_date) if start_date else None
        e = to_db_date_str(end_date) if end_date else None
        return crud.fetch_filtered_data(
            start_date=s,
            end_date=e,
            provinsi=provinsi_filter if provinsi_filter.strip() else None,
            kabupaten=kabupaten_filter if kabupaten_filter.strip() else None,
        )
    return crud.fetch_all_data()


# ======================== DASHBOARD ========================
if menu == "Dashboard":
    st.subheader("📍 Peta Kejadian Banjir Rob")

    data = load_for_dashboard()

    if not data:
        st.info("Belum ada data atau tidak ada yang cocok dengan filter.")
    else:
        # ✅ Auto zoom berdasarkan filter provinsi/kabupaten
        create_map(data, provinsi_filter=provinsi_filter, kabupaten_filter=kabupaten_filter)

        df = pd.DataFrame(data)
        st.subheader("📋 Tabel Data")
        st.dataframe(df, use_container_width=True)

        # ====== DOWNLOAD SEMUA DATA (CSV) ======
        st.download_button(
            label="📥 Download Semua Data (CSV)",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="data_banjir_rob.csv",
            mime="text/csv",
            key="download_csv_all"
        )
        
        # ====== SOROTAN TERBARU ======
        st.subheader("📰 Sorotan Terbaru")
        latest = df.sort_values("Tanggal", ascending=False).head(3)
        
        for _, row in latest.iterrows():
            c1, c2 = st.columns([2, 1])
            with c1:
                st.markdown(
                    f"**{row['Lokasi']}** — {row['Kabupaten']}, {row['Provinsi']}  \n📅 {row['Tanggal']}"
                )
                pdf_buffer = generate_event_pdf(row)
                st.download_button(
                    label="📄 Download Laporan PDF",
                    data=pdf_buffer,
                    file_name=f"laporan_{row['Tanggal']}_{row['Lokasi']}.pdf",
                    mime="application/pdf",
                    key=f"pdf_{row['No']}"
                )
        
            with c2:
                img_url = row.get("Gambar", "")
        
                # ✅ Langkah 1: Ubah link Drive agar bisa tampil langsung
                if img_url and "drive.google.com" in img_url:
                    if "uc?id=" not in img_url:
                        if "/d/" in img_url:
                            file_id = img_url.split("/d/")[1].split("/")[0]
                            img_url = f"https://drive.google.com/uc?export=view&id={file_id}"
        
                # ✅ Langkah 2: Cek apakah bisa diakses
                if img_url:
                    try:
                        headers = {"User-Agent": "Mozilla/5.0"}
                        response = requests.get(img_url, headers=headers, timeout=8)
                        if response.status_code == 200:
                            st.image(img_url, use_container_width=True, caption=row["Lokasi"])
                        else:
                            st.caption("⚠️ Gambar tidak tersedia.")
                    except Exception as e:
                        st.caption(f"⚠️ Gagal memuat gambar: {e}")
                else:
                    st.caption("📷 Tidak ada dokumentasi foto.")

        # ====== DOWNLOAD BERDASARKAN TANGGAL ======
        st.subheader("📅 Download Laporan Berdasarkan Tanggal")
        tanggal_spesifik = st.date_input("Pilih Tanggal Kejadian")

        if tanggal_spesifik:
            df["Tanggal_norm"] = pd.to_datetime(df["Tanggal"], errors="coerce").dt.date
            tanggal_spesifik = pd.to_datetime(tanggal_spesifik).date()
            df_filtered = df[df["Tanggal_norm"] == tanggal_spesifik]

            if df_filtered.empty:
                st.warning(f"⚠️ Tidak ada data untuk tanggal {tanggal_spesifik}.")
            else:
                lokasi_opsi = df_filtered["Lokasi"].unique().tolist()
                lokasi_pilih = st.selectbox("Pilih Lokasi Kejadian", lokasi_opsi)

                rec = df_filtered[df_filtered["Lokasi"] == lokasi_pilih].iloc[0]
                st.markdown(f"""
                **📍 Lokasi:** {rec['Lokasi']}  
                🏙 {rec['Kabupaten']}, {rec['Provinsi']}  
                📅 {rec['Tanggal']}  
                🌐 Koordinat: {rec['Latitude']}, {rec['Longitude']}
                """)

                img_url = rec.get("Gambar", "")
                if img_url:
                    try:
                        headers = {"User-Agent": "Mozilla/5.0"}
                        response = requests.get(img_url, headers=headers, timeout=8)
                        if response.status_code == 200:
                            st.image(img_url, width=350)
                        else:
                            st.caption("⚠️ Gambar tidak tersedia.")
                    except Exception:
                        st.caption("⚠️ Gagal memuat gambar.")
                else:
                    st.caption("📷 Tidak ada dokumentasi foto.")

                pdf_buffer = generate_event_pdf(rec)
                st.download_button(
                    label="📄 Download Laporan PDF (1 Lokasi)",
                    data=pdf_buffer,
                    file_name=f"laporan_{rec['Tanggal']}_{rec['Lokasi']}.pdf",
                    mime="application/pdf",
                    key=f"pdf_single_{rec['No']}"
                )

                pdf_all = generate_multiple_events_pdf(
                    df_filtered.to_dict(orient="records"), tanggal_spesifik
                )
                st.download_button(
                    label="📄 Download Semua Laporan PDF (Tanggal Ini)",
                    data=pdf_all,
                    file_name=f"laporan_semua_{tanggal_spesifik}.pdf",
                    mime="application/pdf",
                    key=f"pdf_multi_{tanggal_spesifik}"
                )


# ======================== TAMBAH DATA ========================
elif menu == "Tambah Data":
    if role != "fod":
        st.warning("⚠️ Menu ini hanya untuk FOD.")
    else:
        st.subheader("➕ Tambah Data Banjir Rob")

        with st.form("form_tambah"):
            tgl = st.date_input("Tanggal")
            lokasi = st.text_input("Lokasi")
            kabupaten = st.text_input("Kabupaten")
            provinsi = st.text_input("Provinsi")

            col1, col2 = st.columns(2)
            with col1:
                latitude = st.number_input("Latitude", format="%.8f")
            with col2:
                longitude = st.number_input("Longitude", format="%.8f")

            st.markdown("**📸 Dokumentasi Foto** (pilih salah satu)")
            gambar_link = st.text_input("Link Gambar (URL)")
            gambar_upload = st.file_uploader("Upload Foto (jpg/png)", type=["jpg", "jpeg", "png"])

            submitted = st.form_submit_button("💾 Simpan Data")

            if submitted:
                if gambar_upload is not None and gambar_link.strip():
                    st.error("❌ Pilih salah satu saja: Upload gambar ATAU masukkan link gambar.")
                    st.stop()

                gambar_final = ""
                if gambar_upload is not None:
                    temp_path = save_uploaded_file(gambar_upload)
                    gambar_final = upload_to_gdrive(temp_path, gambar_upload.name)
                elif gambar_link.strip():
                    gambar_final = gambar_link.strip()

                crud.insert_data(
                    tanggal=to_db_date_str(tgl),
                    lokasi=lokasi,
                    kabupaten=kabupaten,
                    provinsi=provinsi,
                    latitude=safe_float(latitude),
                    longitude=safe_float(longitude),
                    gambar=gambar_final
                )
                st.success("✅ Data berhasil ditambahkan.")


# ======================== KELOLA DATA ========================
elif menu == "Kelola Data":
    if role != "fod":
        st.warning("⚠️ Menu ini hanya untuk FOD.")
    else:
        st.subheader("🛠 Kelola Data Banjir Rob")

        st.markdown("### Filter Berdasarkan Tanggal")
        colf1, colf2 = st.columns(2)
        with colf1:
            start_fod = st.date_input("Tanggal Awal", value=None, key="fod_start")
        with colf2:
            end_fod = st.date_input("Tanggal Akhir", value=None, key="fod_end")

        if st.button("🔎 Terapkan Filter"):
            s = to_db_date_str(start_fod) if start_fod else None
            e = to_db_date_str(end_fod) if end_fod else None
            data = crud.fetch_filtered_data(start_date=s, end_date=e)
        else:
            data = crud.fetch_all_data()

        if not data:
            st.info("Belum ada data atau tidak ditemukan hasil sesuai filter.")
        else:
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)

            id_list = [r["No"] for r in data]
            selected_id = st.selectbox("Pilih No untuk update/hapus", id_list)

            rec = next((r for r in data if r["No"] == selected_id), None)
            if rec:
                st.markdown("### ✏️ Update Data")

                with st.form(f"form_update_{selected_id}"):
                    tgl_default = parse_date_safe(rec.get("Tanggal"))
                    tgl_u = st.date_input("Tanggal", value=tgl_default)
                    lokasi_u = st.text_input("Lokasi", rec.get("Lokasi", ""))
                    kabupaten_u = st.text_input("Kabupaten", rec.get("Kabupaten", ""))
                    provinsi_u = st.text_input("Provinsi", rec.get("Provinsi", ""))

                    c1, c2 = st.columns(2)
                    with c1:
                        latitude_u = st.number_input(
                            "Latitude", value=safe_float(rec.get("Latitude")), format="%.8f"
                        )
                    with c2:
                        longitude_u = st.number_input(
                            "Longitude", value=safe_float(rec.get("Longitude")), format="%.8f"
                        )

                    st.markdown("**📷 Dokumentasi Foto**")
                    gambar_link_u = st.text_input("Link Gambar (URL)", rec.get("Gambar", "") or "")
                    gambar_upload_u = st.file_uploader(
                        "Upload Foto Baru (opsional)", type=["jpg", "jpeg", "png"], key=f"up_{selected_id}"
                    )

                    update_btn = st.form_submit_button("💾 Simpan Perubahan")

                    if update_btn:
                        gambar_final_u = rec.get("Gambar", "") or ""

                        if gambar_upload_u is not None:
                            temp_path = save_uploaded_file(gambar_upload_u)
                            gambar_final_u = upload_to_gdrive(temp_path, gambar_upload_u.name)
                        elif gambar_link_u.strip():
                            gambar_final_u = gambar_link_u.strip()
                        elif not gambar_link_u.strip() and gambar_upload_u is None:
                            gambar_final_u = ""

                        crud.update_data(
                            no_id=selected_id,
                            tanggal=to_db_date_str(tgl_u),
                            lokasi=lokasi_u,
                            kabupaten=kabupaten_u,
                            provinsi=provinsi_u,
                            latitude=safe_float(latitude_u),
                            longitude=safe_float(longitude_u),
                            gambar=gambar_final_u
                        )
                        st.success("✅ Data berhasil diperbarui.")
                        time.sleep(1)
                        st.rerun()

                st.markdown("### 🗑 Hapus Data")
                if st.button("🗑 Hapus Data Ini", type="primary", key=f"del_{selected_id}"):
                    crud.delete_data(selected_id)
                    st.success(f"✅ Data No {selected_id} telah dihapus.")

                    st.rerun()

