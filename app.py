import streamlit as st
import pandas as pd
from datetime import datetime
import io
from PIL import Image
import base64

# --- PENGATURAN DATABASE ---
# GANTI ID ini dengan ID Google Sheets kamu dari Langkah 1
SHEET_ID = "Database_Gudang" 
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

st.set_page_config(page_title="Portal Gudang", layout="centered")
st.title("📦 Portal Penerimaan Barang")

# Fungsi membaca data dari Google Sheets
@st.cache_data(ttl=5)
def load_data():
    try:
        return pd.read_csv(SHEET_URL)
    except:
        return pd.DataFrame(columns=["No PO", "No SJ", "Tanggal", "Vendor", "Foto Base64"])

# Menyimpan data di memori aplikasi
if 'db_aplikasi' not in st.session_state:
    st.session_state.db_aplikasi = load_data()

# Menu Navigasi ala Aplikasi HP
menu = st.radio("Pilih Menu:", ["➕ Input Barang", "🔍 Cari Data"], horizontal=True)

# --- MENU 1: INPUT BARANG ---
if menu == "➕ Input Barang":
    st.subheader("Form Input Surat Jalan")
    
    with st.form("form_penerimaan", clear_on_submit=True):
        no_po = st.text_input("No. PO (Purchase Order)")
        no_sj = st.text_input("No. SJ (Surat Jalan)")
        tanggal = st.date_input("Tanggal Penerimaan", datetime.now())
        vendor = st.text_input("Nama Vendor")
        
        # Fitur ini otomatis akan membuka KAMERA jika diklik dari Android
        foto_file = st.file_uploader("Ambil Foto SJ / Upload Gambar", type=["jpg", "jpeg", "png"])
        
        submitted = st.form_submit_button("SIMPAN KE PORTAL", use_container_width=True)
        
        if submitted:
            if not no_po or not no_sj or not vendor:
                st.error("⚠️ Semua kolom teks wajib diisi!")
            else:
                # Mengubah foto menjadi teks aman agar bisa disimpan di cloud
                foto_string = "-"
                if foto_file is not None:
                    bytes_data = foto_file.getvalue()
                    foto_string = base64.b64encode(bytes_data).decode()

                # Masukkan ke database
                data_baru = pd.DataFrame([{
                    "No PO": no_po,
                    "No SJ": no_sj,
                    "Tanggal": tanggal.strftime("%Y-%m-%d"),
                    "Vendor": vendor,
                    "Foto Base64": foto_string
                }])
                
                st.session_state.db_aplikasi = pd.concat([st.session_state.db_aplikasi, data_baru], ignore_index=True)
                st.success(f"✅ Sukses! Data SJ {no_sj} berhasil disimpan.")

# --- MENU 2: CARI DATA ---
elif menu == "🔍 Cari Data":
    st.subheader("Pencarian Cepat")
    
    df = st.session_state.db_aplikasi
    
    if df.empty:
        st.info("Belum ada data barang masuk yang tercatat.")
    else:
        # Kolom pencarian satu untuk semua (bisa ketik vendor, po, atau sj)
        kata_kunci = st.text_input("Ketik Nama Vendor / No PO / No SJ:")
        
        if kata_kunci:
            hasil_filter = df[
                df['No PO'].astype(str).str.contains(kata_kunci, case=False) |
                df['No SJ'].astype(str).str.contains(kata_kunci, case=False) |
                df['Vendor'].astype(str).str.contains(search, case=False)
            ]
        else:
            hasil_filter = df

        st.write(f"Menampilkan {len(hasil_filter)} data:")
        
        # Tampilan khusus HP (berbentuk list box yang bisa di-klik/expand)
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
