import streamlit as st
import google.generativeai as genai
import os

# --- KONFIGURASI APLIKASI STREAMLIT ---
st.set_page_config(page_title="Chatbot Ahli Obat", page_icon="💊")

st.title("💊 Chatbot Ahli Obat")
st.write("Tanyakan tentang cara minum obat. Saya akan memberikan jawaban singkat dan faktual, serta menolak pertanyaan non-obat.")

# --- PENGATURAN API KEY DAN MODEL ---

# Ambil API Key dari Streamlit Secrets atau environment variable
# Penting: Jangan letakkan API Key langsung di kode Anda!
# Untuk Streamlit Cloud, Anda akan menyimpan ini di file .streamlit/secrets.toml
# Contoh isi secrets.toml:
# GEMINI_API_KEY = "AIzaSy..."
try:
    API_KEY = os.environ.get("GEMINI_API_KEY") or st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("API Key Gemini tidak ditemukan. Harap tambahkan `GEMINI_API_KEY` ke Streamlit Secrets atau environment variables Anda.")
    st.stop() # Hentikan eksekusi aplikasi jika API Key tidak ada

MODEL_NAME = 'gemini-1.5-flash'

# --- KONTEKS AWAL CHATBOT ---
INITIAL_CHATBOT_CONTEXT = [
    {
        "role": "user",
        "parts": ["Kamu adalah ahli OBAT. Masukkan cara minum obat.Jawaban singkat dan faktual. Tolak pertanyaan non-obat."]
    },
    {
        "role": "model",
        "parts": ["Baik! saya jelaskan cara minumnya!."]
    }
]

# --- FUNGSI UTAMA CHATBOT ---

@st.cache_resource
def configure_gemini(api_key):
    """Mengkonfigurasi Gemini API dan menginisialisasi model."""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            MODEL_NAME,
            generation_config=genai.types.GenerationConfig(
                temperature=0.4,
                max_output_tokens=500
            )
        )
        return model
    except Exception as e:
        st.error(f"Kesalahan saat mengkonfigurasi Gemini API atau menginisialisasi model: {e}")
        st.stop()

model = configure_gemini(API_KEY)

# Inisialisasi riwayat chat di Streamlit's session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    # Tambahkan konteks awal ke riwayat chat hanya sekali
    for message in INITIAL_CHATBOT_CONTEXT:
        st.session_state.chat_history.append(message)
    # Start the chat session with the initial context
    st.session_state.gemini_chat = model.start_chat(history=INITIAL_CHATBOT_CONTEXT)
else:
    # Re-initialize the chat session with the current history
    st.session_state.gemini_chat = model.start_chat(history=st.session_state.chat_history)


# Tampilkan riwayat chat sebelumnya
for message in st.session_state.chat_history:
    if message["role"] == "user":
        st.chat_message("user").write(message["parts"][0])
    elif message["role"] == "model" and message["parts"][0] != "Baik! saya jelaskan cara minumnya!.": # Jangan tampilkan balasan pembuka sebagai pesan model
        st.chat_message("assistant").write(message["parts"][0])


# Input pengguna
user_input = st.chat_input("Tulis pertanyaan Anda di sini...")

if user_input:
    st.chat_message("user").write(user_input)
    st.session_state.chat_history.append({"role": "user", "parts": [user_input]})

    with st.spinner("Chatbot sedang berpikir..."):
        try:
            response = st.session_state.gemini_chat.send_message(user_input, request_options={"timeout": 60})

            if response and response.text:
                st.chat_message("assistant").write(response.text)
                st.session_state.chat_history.append({"role": "model", "parts": [response.text]})
            else:
                st.chat_message("assistant").write("Maaf, saya tidak bisa memberikan balasan. Respons API kosong atau tidak valid.")
        except Exception as e:
            st.chat_message("assistant").write(f"Maaf, terjadi kesalahan saat berkomunikasi dengan Gemini: {e}")
            st.chat_message("assistant").write("Kemungkinan penyebab: masalah koneksi internet, API Key tidak valid/melebihi kuota, atau masalah internal server Gemini.")

# Opsional: Tombol untuk menghapus riwayat chat
if st.button("Hapus Riwayat Chat"):
    st.session_state.chat_history = []
    st.session_state.gemini_chat = model.start_chat(history=INITIAL_CHATBOT_CONTEXT)
    st.experimental_rerun()