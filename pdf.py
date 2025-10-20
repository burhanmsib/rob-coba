from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import io
import requests
from PIL import Image as PILImage, UnidentifiedImageError


# =======================
# Fungsi: PDF SATU KEJADIAN
# =======================
def generate_event_pdf(record):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Justify", alignment=4, leading=15))

    elements = []

    # ======= Judul =======
    elements.append(Paragraph("🌊 LAPORAN KEJADIAN BANJIR ROB", styles["Title"]))
    elements.append(Spacer(1, 20))

    # ======= Informasi Kejadian =======
    info_text = f"""
    <b>Tanggal:</b> {record.get('Tanggal', '-') }<br/>
    <b>Lokasi:</b> {record.get('Lokasi', '-') }<br/>
    <b>Kabupaten:</b> {record.get('Kabupaten', '-') }<br/>
    <b>Provinsi:</b> {record.get('Provinsi', '-') }<br/>
    <b>Koordinat:</b> {record.get('Latitude', '-')}, {record.get('Longitude', '-') }
    """
    elements.append(Paragraph(info_text, styles["Justify"]))
    elements.append(Spacer(1, 20))

    # ======= Gambar (jika ada) =======
    img_url = record.get("Gambar", "")
    if img_url:
        try:
            img_data = load_image_from_url(img_url)
            if img_data:
                elements.append(Image(img_data, width=4 * inch, height=3 * inch))
            else:
                elements.append(Paragraph("⚠️ Gambar tidak dapat dimuat.", styles["Normal"]))
        except Exception as e:
            elements.append(Paragraph(f"⚠️ Gagal memuat gambar ({str(e)[:50]}...)", styles["Normal"]))
    else:
        elements.append(Paragraph("📷 Tidak ada dokumentasi foto untuk kejadian ini.", styles["Normal"]))

    doc.build(elements)
    buffer.seek(0)
    return buffer


# =======================
# Fungsi: PDF MULTI KEJADIAN
# =======================
def generate_multiple_events_pdf(records, tanggal):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"🌊 Laporan Kejadian Banjir Rob - {tanggal}", styles["Title"]))
    story.append(Spacer(1, 20))

    if not records:
        story.append(Paragraph("Tidak ada kejadian banjir rob pada tanggal ini.", styles["Normal"]))
    else:
        for rec in records:
            lokasi = rec.get("Lokasi", "-")
            kabupaten = rec.get("Kabupaten", "-")
            provinsi = rec.get("Provinsi", "-")
            latitude = rec.get("Latitude", "-")
            longitude = rec.get("Longitude", "-")
            gambar = rec.get("Gambar", "")

            story.append(Paragraph(f"<b>{lokasi}</b> — {kabupaten}, {provinsi}", styles["Heading3"]))
            story.append(Paragraph(f"Tanggal: {rec.get('Tanggal', '-')}", styles["Normal"]))
            story.append(Paragraph(f"Koordinat: {latitude}, {longitude}", styles["Normal"]))
            story.append(Spacer(1, 8))

            if gambar:
                try:
                    img_data = load_image_from_url(gambar)
                    if img_data:
                        story.append(Image(img_data, width=4 * inch, height=3 * inch))
                    else:
                        story.append(Paragraph("(⚠️ Gagal memuat gambar)", styles["Normal"]))
                except Exception:
                    story.append(Paragraph("(⚠️ Gagal memuat gambar)", styles["Normal"]))
            else:
                story.append(Paragraph("(📷 Tidak ada dokumentasi foto)", styles["Normal"]))

            story.append(Spacer(1, 20))

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


# =======================
# Fungsi Bantuan: Load Gambar
# =======================
def load_image_from_url(url):
    """
    Ambil gambar dari URL publik (termasuk Google Drive yang dibagikan).
    Tidak lagi mendukung path lokal.
    """
    if not url:
        return None

    try:
        # Konversi URL Google Drive agar bisa diakses langsung
        if "drive.google.com" in url:
            if "id=" in url:
                file_id = url.split("id=")[-1]
            elif "/d/" in url:
                file_id = url.split("/d/")[1].split("/")[0]
            else:
                file_id = None
            if file_id:
                url = f"https://drive.google.com/uc?export=view&id={file_id}"

        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        img_data = io.BytesIO(response.content)
        PILImage.open(img_data).verify()
        img_data.seek(0)
        return img_data

    except (requests.RequestException, UnidentifiedImageError):
        return None
    except Exception:
        return None
