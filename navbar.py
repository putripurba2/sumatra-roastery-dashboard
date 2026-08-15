"""
Modul navbar atas untuk dashboard Sumatra Roastery.
Menampilkan "Login sebagai: <role>" di kiri dan tombol Logout di kanan.
Dipisah dari app.py supaya app.py tidak terlalu panjang.
"""
import streamlit as st


def render_navbar(colors: dict):
    """
    Render navbar horizontal di bagian atas konten utama.
    colors: dict berisi PRIMARY, CREAM, ESPRESSO (dikirim dari app.py
            supaya warnanya tetap konsisten satu tema).
    """
    PRIMARY = colors["PRIMARY"]
    CREAM = colors["CREAM"]
    ESPRESSO = colors["ESPRESSO"]

    st.markdown(f"""
    <style>
    .st-key-topnav {{
        background: {PRIMARY};
        padding: 10px 20px;
        border-radius: 10px;
        margin-bottom: 1rem;
    }}
    .st-key-topnav p, .st-key-topnav div, .st-key-topnav span {{
        color: #FFFFFF !important;
    }}
    .st-key-topnav [data-testid="column"]:first-child {{
        display: flex;
        align-items: center;
    }}
    .st-key-topnav .stButton button {{
        background-color: #FFFFFF !important;
        color: {ESPRESSO} !important;
        font-weight: 600;
    }}
    .st-key-topnav .stButton button p,
    .st-key-topnav .stButton button div,
    .st-key-topnav .stButton button span {{
        color: {ESPRESSO} !important;
    }}
    .st-key-topnav .stButton button:hover {{
        background-color: {CREAM} !important;
    }}
    </style>
    """, unsafe_allow_html=True)

    with st.container(key="topnav"):
        nav_left, nav_right = st.columns([5, 1])
        with nav_left:
            st.markdown(f"Login sebagai: **{st.session_state.role}**")
        with nav_right:
            if st.button("Logout", key="logout_top", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.role = None
                st.rerun()