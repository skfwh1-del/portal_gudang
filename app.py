import streamlit as st
import pandas as pd
from datetime import datetime
import io
from PIL import Image
import base64
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

# --- PENGATURAN DATABASE & EMAIL ---
# 1. Ganti dengan ID Google Sheets kamu
SHEET_ID = "Database_Gudang" 
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

# 2. PENGATURAN EMAIL TUJUAN (Email Pribadi Kamu)
EMAIL_TUJUAN = "tapiaregan49@gmail.com"

# 3. PENGATURAN EMAIL PENGIRIM (Sistem)
# Untuk keamanan, disarankan menggunakan App Password dari Google Gmail
EMAIL_PENGIRIM = "tapiaregan49@gmail.com"
PASSWORD_PENGIRIM = "warehousedihati1." 

st.set_page_config(page_title="Portal Gudang", layout="centered")
st.title("📦 Portal Penerimaan Barang")

# Fungsi Kirim Email Notifikasi
def kirim_email_notifikasi(no_po, no_sj, tanggal, vendor, foto_file):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_PENGIRIM
        msg['To'] = EMAIL_TUJUAN
        msg['Subject'] = f"🚨 LAPORAN: Penerimaan Barang Baru - SJ: {no_sj}"

        body = f"""
        <h3>Laporan Penerimaan Barang Baru</h3>
        <p>Halo, berikut adalah detail barang masuk yang baru saja dicatat:</p>
        <table border="1" cellpadding="5" style="border-collapse: collapse;">
            <tr><td><b>No. PO</b></td><td>{no_po}</td></tr>
            <tr><td><b>No. Surat Jalan (SJ)</b></td><td>{no_sj}</td></tr>
            <tr><td><b>Tanggal</b></td><td>{tanggal}</td></tr>
            <tr><td><b>Vendor</b></td><td>{vendor}</td></tr>
        </table>
        <p><i>Pesan ini dikirim otomatis oleh sistem Portal Gudang.</i></p>
        """
        msg.attach(MIMEText(body, 'html'))

        # Lampirkan Foto jika ada
        if foto_file is not None:
            foto_file.seek(0)
            img_data = foto_file.read()
            image = MIMEImage(img_data, name=foto_file.name)
            msg.attach(image)

        # Koneksi ke Server SMTP Gmail
        server = smtplib.SMTP('smtp.gmail.com', 547)
        server.starttls()
        server.login(EMAIL_PENGIRIM, PASSWORD_PENGIRIM)
        server.sendmail(EMAIL_PENGIRIM, EMAIL_TUJUAN, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        st.sidebar.error(f"Gagal mengirim email: {e}")
        return False

# Fungsi membaca data dari Google Sheets
@st.cache_data(ttl=5)
def load_data():
    try:
        return pd.read_csv(SHEET_URL)
    except:
        return pd.DataFrame(columns=["No PO", "No SJ", "Tanggal", "Vendor", "Foto Base64"])

if 'db_aplikasi' not in st.session_state:
    st.session_state.db_aplikasi = load_data()

menu = st.radio("Pilih Menu:", ["➕ Input Barang", "🔍 Cari Data"], horizontal=True)

if menu == "➕ Input Barang":
    st.subheader("Form Input Surat Jalan")
    
    with st.form("form_penerimaan", clear_on_submit=True):
        no_po = st.text_input("No. PO (Purchase Order)")
        no_sj = st.text_input("No. SJ (Surat Jalan)")
        tanggal = st.date_input("Tanggal Penerimaan", datetime.now())
        vendor = st.text_input("Nama Vendor")
        foto_file = st.file_uploader("Ambil Foto SJ / Upload Gambar", type=["jpg", "jpeg", "png"])
        
        submitted = st.form_submit_button("SIMPAN KE PORTAL", use_container_width=True)
        
        if submitted:
            if not no_po or not no_sj or not vendor:
                st.error("⚠️ Semua kolom teks wajib diisi!")
            else:
                foto_string = "-"
                if foto_file is not None:
                    bytes_data = foto_file.getvalue()
                    foto_string = base64.b64encode(bytes_data).decode()

                # Simpan ke Database Internal
                data_baru = pd.DataFrame([{
                    "No PO": no_po,
                    "No SJ": no_sj,
                    "Tanggal": tanggal.strftime("%Y-%m-%d"),
                    "Vendor": vendor,
                    "Foto Base64": foto_string
                }])
                st.session_state.db_aplikasi = pd.concat([st.session_state.db_aplikasi, data_baru], ignore_index=True)
                
                # JALANKAN FUNGSI KIRIM EMAIL
                st.info("Sedang mengirim email verifikasi...")
                email_sukses = kirim_email_notifikasi(no_po, no_sj, tanggal.strftime("%Y-%m-%d"), vendor, foto_file)
                
                if email_sukses:
                    st.success(f"✅ Sukses! Data disimpan & Verifikasi terkirim ke {EMAIL_TUJUAN}")
                else:
                    st.warning(f"⚠️ Data tersimpan, namun verifikasi email gagal dikirim.")

elif menu == "🔍 Cari Data":
    st.subheader("Pencarian Cepat")
    df = st.session_state.db_aplikasi
    
    if df.empty:
        st.info("Belum ada data barang masuk yang tercatat.")
    else:
        kata_kunci = st.text_input("Ketik Nama Vendor / No PO / No SJ:")
        if kata_kunci:
            hasil_filter = df[
                df['No PO'].astype(str).str.contains(kata_kunci, case=False) |
                df['No SJ'].astype(str).str.contains(kata_kunci, case=False) |
                df['Vendor'].astype(str).str.contains(kata_kunci, case=False)
            ]
        else:
            hasil_filter = df

        st.write(f"Menampilkan {len(hasil_filter)} data:")
        for indeks, baris in hasil_filter.iterrows():
            with st.expander(f"📦 {baris['No SJ']} - {baris['Vendor']}"):
                st.write(f"**No. PO :** {baris['No PO']}")
                st.write(f"**Tanggal:** {baris['Tanggal']}")
                if baris['Foto Base64'] != "-":
                    try:
                        foto_bytes = base64.b64decode(baris['Foto Base64'])
                        gambar = Image.open(io.BytesIO(foto_bytes))
                        st.image(gambar, caption=f"Foto SJ: {baris['No SJ']}", use_container_width=True)
                    except:
                        st.error("Gagal menampilkan foto.")
                else:
                    st.caption("Tidak ada lampiran foto SJ.")
