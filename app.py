import streamlit as st
import google.generativeai as genai
import os

# ==============================================================================
# KONFIGURASI APLIKASI STREAMLIT
# ==============================================================================

# Mengatur konfigurasi dasar halaman seperti judul dan ikon.
st.set_page_config(page_title="Chatbot Ahli Fisika", page_icon="⚛️")

# Menambahkan judul utama dan deskripsi pada antarmuka web.
st.title("⚛️ Chatbot Ahli Fisika")
st.write("""
    Selamat datang! Saya adalah Chatbot Ahli Fisika.
    Anda bisa bertanya tentang rumus atau konsep Fisika.
    Saya akan memberikan jawaban singkat dan faktual, serta menolak pertanyaan non-fisika.
""")

# ==============================================================================
# PENGATURAN API KEY DAN MODEL
# ==============================================================================

# Mengambil API Key dari Streamlit Secrets atau environment variables.
# Ini adalah cara paling aman untuk menyimpan kredensial sensitif.
# Pastikan Anda sudah menambahkan [secrets] pada file .streamlit/secrets.toml
# dengan baris: GEMINI_API_KEY = "AIzaSy..."
try:
    API_KEY = os.environ.get("GEMINI_API_KEY") or st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("""
        **Error:** API Key Gemini tidak ditemukan.
        Harap tambahkan `GEMINI_API_KEY` ke Streamlit Secrets atau environment variables Anda
        untuk menjalankan aplikasi ini.
    """)
    st.stop()  # Hentikan eksekusi jika API Key tidak ada

MODEL_NAME = 'gemini-1.5-flash'

# ==============================================================================
# KONTEKS AWAL CHATBOT
# ==============================================================================

# Definisikan peran chatbot Anda di sini.
INITIAL_CHATBOT_CONTEXT = [
    {
        "role": "user",
        "parts": ["Kamu adalah ahli fisika. Tuliskan rumus tentang Fisika. Jawaban singkat. Tolak pertanyaan non-fisika."]
    },
    {
        "role": "model",
        "parts": ["Baik! Berikan rumus yang ingin anda ketahui."]
    }
]

# ==============================================================================
# FUNGSI UTAMA CHATBOT DENGAN STREAMLIT
# ==============================================================================

@st.cache_resource
def configure_gemini(api_key):
    """
    Mengkonfigurasi Gemini API dan menginisialisasi model.
    Menggunakan `@st.cache_resource` untuk memastikan inisialisasi hanya
    dilakukan satu kali, meningkatkan efisiensi aplikasi.
    """
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            MODEL_NAME,
            generation_config=genai.types.GenerationConfig(
                temperature=0.4,  # Kontrol kreativitas (0.0=faktual)
                max_output_tokens=500  # Batas maksimal panjang jawaban
            )
        )
        return model
    except Exception as e:
        st.error(f"Kesalahan saat mengkonfigurasi Gemini API atau menginisialisasi model: {e}")
        st.stop()

# Panggil fungsi untuk menginisialisasi model
model = configure_gemini(API_KEY)

# Inisialisasi riwayat chat di Streamlit's session state jika belum ada.
# st.session_state digunakan untuk mempertahankan data antar interaksi pengguna.
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    # Tambahkan konteks awal ke riwayat chat
    for message in INITIAL_CHATBOT_CONTEXT:
        st.session_state.chat_history.append(message)

# Setiap kali aplikasi di-rerun, sesi chat harus diinisialisasi ulang
# dengan riwayat penuh untuk mempertahankan konteks percakapan.
st.session_state.gemini_chat = model.start_chat(history=st.session_state.chat_history)

# Tampilkan semua pesan yang sudah ada dalam riwayat chat.
# Kita gunakan st.chat_message untuk format yang lebih menarik.
for message in st.session_state.chat_history:
    if message["role"] == "user":
        st.chat_message("user").write(message["parts"][0])
    elif message["role"] == "model":
        st.chat_message("assistant").write(message["parts"][0])

# Input pengguna dari kolom chat di bagian bawah.
user_input = st.chat_input("Tulis pertanyaan Anda di sini...")

if user_input:
    # Tampilkan pesan pengguna di UI
    st.chat_message("user").write(user_input)
    # Tambahkan pesan pengguna ke riwayat
    st.session_state.chat_history.append({"role": "user", "parts": [user_input]})

    # Gunakan spinner untuk menunjukkan bahwa chatbot sedang memproses.
    with st.spinner("Chatbot sedang berpikir..."):
        try:
            # Kirim pesan pengguna ke model Gemini melalui sesi chat.
            response = st.session_state.gemini_chat.send_message(user_input, request_options={"timeout": 60})

            if response and response.text:
                # Tampilkan balasan dari model
                st.chat_message("assistant").write(response.text)
                # Tambahkan balasan model ke riwayat
                st.session_state.chat_history.append({"role": "model", "parts": [response.text]})
            else:
                st.chat_message("assistant").write("Maaf, saya tidak bisa memberikan balasan. Respons API kosong atau tidak valid.")
        except Exception as e:
            # Tangani kesalahan saat komunikasi dengan API.
            st.chat_message("assistant").write(f"Maaf, terjadi kesalahan saat berkomunikasi dengan Gemini: {e}")
            st.chat_message("assistant").write("""
                Kemungkinan penyebab: masalah koneksi internet, API Key tidak valid/melebihi kuota, atau masalah internal server Gemini.
            """)

# Tombol opsional untuk menghapus riwayat chat.
if st.button("Hapus Riwayat Chat"):
    st.session_state.chat_history = []
    st.session_state.gemini_chat = model.start_chat(history=INITIAL_CHATBOT_CONTEXT)
    st.experimental_rerun()
