"""
Modul halaman login untuk dashboard Sumatra Roastery.
Dipisah dari app.py supaya app.py tidak terlalu panjang.
"""
import streamlit as st

CREDENTIALS = {
    "peneliti": {"password": "peneliti123", "role": "Peneliti"},
    "pemilik": {"password": "pemilik123", "role": "Pemilik/Pengelola"},
}


def require_login(colors: dict):
    """
    Tampilkan halaman login (card di tengah + background gradient) jika
    user belum login. Kalau sudah login, fungsi ini langsung return
    tanpa menampilkan apa-apa, sehingga app.py bisa lanjut jalan seperti biasa.

    colors: dict berisi PRIMARY, ACCENT, CREAM, ESPRESSO, ESPRESSO_SOFT, BORDER
            (dikirim dari app.py supaya warnanya tetap konsisten satu tema).
    """
    PRIMARY = colors["PRIMARY"]
    ACCENT = colors["ACCENT"]
    CREAM = colors["CREAM"]
    ESPRESSO = colors["ESPRESSO"]
    ESPRESSO_SOFT = colors["ESPRESSO_SOFT"]
    BORDER = colors["BORDER"]

    TEAL = "#2E8F84"
    TEAL_DARK = "#1B6F63"
    TEAL_LIGHT = "#3DAF95"

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.role = None

    # Sudah login -> tidak perlu render apa pun, biarkan app.py lanjut
    if st.session_state.logged_in:
        return

    st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(135deg, {PRIMARY} 0%, {CREAM} 55%, {ACCENT} 100%) !important;
        background-attachment: fixed;
    }}
    [data-testid="stHeader"] {{
        background-color: transparent !important;
    }}
    [data-testid="stMainBlockContainer"] {{
        padding-top: 4rem !important;
    }}
    [data-testid="stForm"] {{
        background-color: #FFFFFF;
        border-radius: 20px;
        padding: 2.6rem 2.4rem 1.6rem 2.4rem;
        box-shadow: 0 25px 50px rgba(59, 42, 32, 0.28);
        border: 1px solid {BORDER};
    }}
    .login-icon-badge {{
        width: 64px;
        height: 64px;
        border-radius: 50%;
        background: linear-gradient(135deg, {TEAL} 0%, {TEAL_DARK} 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 0.9rem auto;
        font-size: 30px;
        box-shadow: 0 8px 18px rgba(46, 143, 132, 0.35);
    }}
    .login-title {{
        text-align: center;
        font-size: 1.4rem;
        font-weight: 800;
        color: {TEAL_DARK};
        letter-spacing: 1px;
        margin-bottom: 0.15rem;
    }}
    .login-subtitle {{
        text-align: center;
        font-size: 0.85rem;
        color: {ESPRESSO_SOFT};
        margin-bottom: 1.8rem;
    }}
    .login-footer {{
        text-align: center;
        font-size: 0.75rem;
        color: #A8998A;
        margin-top: 1.2rem;
    }}
    [data-testid="stForm"] .stTextInput input:focus {{
        border-color: {TEAL} !important;
        box-shadow: 0 0 0 1px {TEAL} !important;
    }}
    [data-testid="stForm"] .stFormSubmitButton button {{
        background: linear-gradient(135deg, {TEAL} 0%, {TEAL_DARK} 100%) !important;
    }}
    [data-testid="stForm"] .stFormSubmitButton button:hover {{
        background: {TEAL_DARK} !important;
    }}
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.1, 1])
    with col2:
        with st.form("login_form"):
            st.markdown('<div class="login-icon-badge">☕</div>', unsafe_allow_html=True)
            st.markdown('<div class="login-title">SUMATRA ROASTERY</div>', unsafe_allow_html=True)
            st.markdown('<div class="login-subtitle">Dashboard Analisis & Prediksi Pendapatan</div>', unsafe_allow_html=True)
            username = st.text_input("Username", placeholder="Masukkan Username")
            password = st.text_input("Password", type="password", placeholder="Masukkan Password")
            submitted = st.form_submit_button("➜ Login", use_container_width=True)
        st.markdown('<div class="login-footer">© 2026 Sumatra Roastery Medan</div>', unsafe_allow_html=True)

    if submitted:
        user = CREDENTIALS.get(username.strip().lower())
        if user and user["password"] == password:
            st.session_state.logged_in = True
            st.session_state.role = user["role"]
            st.rerun()
        else:
            with col2:
                st.error("Username atau password salah.")

    # Belum login (atau baru salah password) -> hentikan app.py di sini
    st.stop()