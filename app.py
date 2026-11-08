import streamlit as st
import time
from datetime import datetime
from block import Block
from blockchain import Blockchain
from pos import proof_of_stake

# 1. Page Configuration
st.set_page_config(
    page_title="AmalKita — Transparent Blockchain Crowdfunding",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 2. Modern Minimalist Design System (Inter / Manrope & Forest Green Palette)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* Base Styles */
html, body, [class*="css"], .stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    background-color: #F8FAF8 !important;
    color: #202923 !important;
}

/* Hide Streamlit default header decorations */
header[data-testid="stHeader"] {
    background-color: transparent !important;
}
#MainMenu, footer {
    visibility: hidden;
}

/* Layout container */
.main .block-container {
    max-width: 1140px !important;
    padding-top: 1.5rem !important;
    padding-bottom: 3rem !important;
}

/* Header Navbar */
.app-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 24px;
    background: #FFFFFF;
    border: 1px solid #E5E9E5;
    border-radius: 16px;
    margin-bottom: 24px;
    box-shadow: 0 1px 3px rgba(32, 41, 35, 0.04);
}
.brand-title {
    font-size: 20px;
    font-weight: 700;
    color: #245C46;
    letter-spacing: -0.3px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.status-pill {
    background-color: #E5F0E7;
    color: #245C46;
    font-size: 12px;
    font-weight: 600;
    padding: 6px 14px;
    border-radius: 20px;
    display: inline-flex;
    align-items: center;
    gap: 6px;
}
.status-dot {
    width: 7px;
    height: 7px;
    background-color: #245C46;
    border-radius: 50%;
}

/* Hero Section */
.hero-card {
    background: #FFFFFF;
    border: 1px solid #E5E9E5;
    border-radius: 20px;
    padding: 44px 36px;
    margin-bottom: 24px;
    box-shadow: 0 4px 20px rgba(32, 41, 35, 0.03);
}
.hero-badge {
    display: inline-block;
    background-color: #E5F0E7;
    color: #245C46;
    font-size: 12px;
    font-weight: 600;
    padding: 5px 12px;
    border-radius: 6px;
    margin-bottom: 16px;
    letter-spacing: 0.2px;
}
.hero-heading {
    font-size: 36px;
    font-weight: 700;
    color: #202923;
    line-height: 1.25;
    letter-spacing: -0.8px;
    margin-bottom: 12px;
}
.hero-highlight {
    color: #245C46;
}
.hero-subheading {
    font-size: 15px;
    color: #737B75;
    max-width: 620px;
    line-height: 1.6;
    margin-bottom: 0px;
}

/* Metric Cards */
.metric-box {
    background: #FFFFFF;
    border: 1px solid #E5E9E5;
    border-radius: 14px;
    padding: 20px 18px;
    text-align: left;
    box-shadow: 0 2px 6px rgba(32, 41, 35, 0.02);
}
.metric-value {
    font-size: 24px;
    font-weight: 700;
    color: #245C46;
    letter-spacing: -0.5px;
    margin-bottom: 4px;
}
.metric-label {
    font-size: 13px;
    color: #737B75;
    font-weight: 500;
}

/* Tab Navigation */
.stTabs [data-baseweb="tab-list"] {
    background-color: #FFFFFF !important;
    border: 1px solid #E5E9E5 !important;
    border-radius: 12px !important;
    padding: 4px !important;
    gap: 4px !important;
    margin-bottom: 20px !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px !important;
    padding: 8px 18px !important;
    color: #737B75 !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    border: none !important;
    background-color: transparent !important;
}
.stTabs [aria-selected="true"] {
    background-color: #245C46 !important;
    color: #FFFFFF !important;
    font-weight: 600 !important;
}

/* Campaign Card */
.campaign-card {
    background: #FFFFFF;
    border: 1px solid #E5E9E5;
    border-radius: 16px;
    overflow: hidden;
    margin-bottom: 20px;
    box-shadow: 0 2px 8px rgba(32, 41, 35, 0.03);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.campaign-img {
    width: 100%;
    height: 190px;
    object-fit: cover;
    display: block;
}
.campaign-content {
    padding: 22px;
}
.campaign-tag {
    display: inline-block;
    background-color: #E5F0E7;
    color: #245C46;
    font-size: 11px;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 6px;
    margin-bottom: 10px;
}
.campaign-title {
    font-size: 17px;
    font-weight: 700;
    color: #202923;
    line-height: 1.35;
    margin-bottom: 8px;
    letter-spacing: -0.2px;
}
.campaign-desc {
    font-size: 13px;
    color: #737B75;
    line-height: 1.55;
    margin-bottom: 16px;
    min-height: 40px;
}
.campaign-progress-bg {
    background-color: #E5E9E5;
    border-radius: 6px;
    height: 6px;
    overflow: hidden;
    margin-bottom: 8px;
}
.campaign-progress-bar {
    background-color: #245C46;
    height: 100%;
    border-radius: 6px;
}
.campaign-meta {
    display: flex;
    justify-content: space-between;
    font-size: 12px;
    color: #737B75;
}
.campaign-raised {
    font-weight: 700;
    color: #202923;
}

/* Surface Info Container */
.surface-card {
    background: #FFFFFF;
    border: 1px solid #E5E9E5;
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 2px 8px rgba(32, 41, 35, 0.02);
}
.surface-title {
    font-size: 16px;
    font-weight: 700;
    color: #202923;
    margin-bottom: 4px;
}
.surface-desc {
    font-size: 13px;
    color: #737B75;
    margin-bottom: 20px;
}

/* Blockchain Block Component */
.chain-block {
    background: #FFFFFF;
    border: 1px solid #E5E9E5;
    border-left: 4px solid #245C46;
    border-radius: 12px;
    padding: 18px 20px;
    margin-bottom: 12px;
    box-shadow: 0 1px 4px rgba(32, 41, 35, 0.02);
}
.chain-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
    font-size: 14px;
    font-weight: 700;
    color: #245C46;
}
.chain-time {
    font-size: 12px;
    font-weight: 400;
    color: #737B75;
}
.chain-detail {
    font-size: 13px;
    color: #202923;
    margin-bottom: 8px;
}
.chain-hash {
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace !important;
    font-size: 12px;
    color: #737B75;
    word-break: break-all;
    line-height: 1.4;
}

/* Button & Form Controls Customization */
button[kind="primary"] {
    background-color: #245C46 !important;
    border: 1px solid #245C46 !important;
    border-radius: 10px !important;
    padding: 9px 20px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    color: #FFFFFF !important;
    box-shadow: 0 1px 3px rgba(36, 92, 70, 0.12) !important;
    transition: all 0.15s ease-in-out !important;
}
button[kind="primary"]:hover {
    background-color: #1c4937 !important;
    border-color: #1c4937 !important;
}
button[kind="secondary"] {
    background-color: #FFFFFF !important;
    border: 1px solid #E5E9E5 !important;
    border-radius: 10px !important;
    font-weight: 500 !important;
    font-size: 14px !important;
    color: #202923 !important;
}
button[kind="secondary"]:hover {
    border-color: #A8BFA8 !important;
    color: #245C46 !important;
}

/* Inputs & Form Fields */
.stTextInput input, .stNumberInput input, .stSelectbox > div {
    border-radius: 10px !important;
    border: 1px solid #E5E9E5 !important;
    background-color: #FFFFFF !important;
    color: #202923 !important;
    font-size: 14px !important;
}
.stTextInput input:focus, .stNumberInput input:focus {
    border-color: #245C46 !important;
    box-shadow: 0 0 0 2px rgba(36, 92, 70, 0.12) !important;
}

/* Progress bar styling */
.stProgress > div > div > div > div {
    background-color: #245C46 !important;
}

/* Footer Section */
.app-footer {
    text-align: center;
    padding: 36px 0 16px 0;
    margin-top: 48px;
    border-top: 1px solid #E5E9E5;
    font-size: 13px;
    color: #737B75;
}
</style>
""", unsafe_allow_html=True)

# 3. Session State Management (Preserved 100% Functionality)
if "blockchain" not in st.session_state:
    st.session_state.blockchain = Blockchain()

if "campaigns" not in st.session_state:
    st.session_state.campaigns = [
        {
            "id": 1,
            "title": "Pendidikan Anak Pesisir & Pedalaman",
            "category": "Pendidikan",
            "target": 150000000,
            "raised": 98500000,
            "desc": "Penyediaan fasilitas ruang belajar, buku teks, dan sarana edukasi bagi 300+ anak.",
            "img": "https://images.unsplash.com/photo-1497375638960-ca368c7231e4?w=600&auto=format&fit=crop&q=80",
        },
        {
            "id": 2,
            "title": "Bantuan Pangan Bencana Banjir",
            "category": "Kemanusiaan",
            "target": 75000000,
            "raised": 72000000,
            "desc": "Distribusi paket pangan esensial dan perlengkapan darurat untuk keluarga terdampak.",
            "img": "https://images.unsplash.com/photo-1488521787991-ed7bbaae773c?w=600&auto=format&fit=crop&q=80",
        },
        {
            "id": 3,
            "title": "Layanan Medis Desa Terpencil",
            "category": "Kesehatan",
            "target": 200000000,
            "raised": 124000000,
            "desc": "Pemeriksaan kesehatan gratis, pasokan nutrisi, dan obat primer secara berkala.",
            "img": "https://images.unsplash.com/photo-1532938911079-1b06ac7ceec7?w=600&auto=format&fit=crop&q=80",
        },
        {
            "id": 4,
            "title": "Penanaman 10.000 Mangrove Pesisir",
            "category": "Lingkungan",
            "target": 50000000,
            "raised": 31200000,
            "desc": "Restorasi sabuk hijau pesisir guna mencegah abrasi dan menjaga habitat biota laut.",
            "img": "https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?w=600&auto=format&fit=crop&q=80",
        },
    ]

# 4. Header Bar Component
st.markdown("""
<div class="app-header">
    <div class="brand-title">
        <span>🌱</span> AmalKita
    </div>
    <div class="status-pill">
        <span class="status-dot"></span> Jaringan Blockchain Aktif
    </div>
</div>
""", unsafe_allow_html=True)

# 5. Modern Minimalist Hero Section
st.markdown("""
<div class="hero-card">
    <div class="hero-badge">Sistem Amal & Donasi Terdesentralisasi</div>
    <div class="hero-heading">Kebaikan Kecil, <span class="hero-highlight">Dampak Nyata.</span></div>
    <div class="hero-subheading">Platform penggalangan dana terpercaya berbasis buku besar blockchain terdistribusi. Setiap kontribusi tercatat akuntabel, transparan, dan tidak dapat dimanipulasi.</div>
</div>
""", unsafe_allow_html=True)

# 6. Trust & Impact Metric Cards
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown('<div class="metric-box"><div class="metric-value">Rp 2.4 M+</div><div class="metric-label">Total Dana Tersalurkan</div></div>', unsafe_allow_html=True)
with m2:
    st.markdown('<div class="metric-box"><div class="metric-value">1,920+</div><div class="metric-label">Partisipasi Donatur</div></div>', unsafe_allow_html=True)
with m3:
    st.markdown('<div class="metric-box"><div class="metric-value">48</div><div class="metric-label">Program Terselesaikan</div></div>', unsafe_allow_html=True)
with m4:
    st.markdown('<div class="metric-box"><div class="metric-value">100%</div><div class="metric-label">Integritas Kriptografi</div></div>', unsafe_allow_html=True)

st.write("")

# 7. Main Functional Tabs
tab_camp, tab_donasi, tab_chain, tab_pow, tab_pos = st.tabs([
    "Program Donasi",
    "Formulir Donasi",
    "Buku Besar Blockchain",
    "Konsensus PoW",
    "Konsensus PoS"
])

# ─── TAB 1: PROGRAM CAMPAIGN ───
with tab_camp:
    st.markdown("<div style='margin-bottom: 16px; font-weight:700; font-size:18px; color:#202923;'>Inisiatif Kemanusiaan Aktif</div>", unsafe_allow_html=True)

    c_rows = st.columns(2)
    for idx, c in enumerate(st.session_state.campaigns):
        with c_rows[idx % 2]:
            pct = min(100, int((c["raised"] / c["target"]) * 100))
            st.markdown(f"""
            <div class="campaign-card">
                <img class="campaign-img" src="{c['img']}" alt="{c['title']}">
                <div class="campaign-content">
                    <span class="campaign-tag">{c['category']}</span>
                    <div class="campaign-title">{c['title']}</div>
                    <div class="campaign-desc">{c['desc']}</div>
                    <div class="campaign-progress-bg">
                        <div class="campaign-progress-bar" style="width:{pct}%;"></div>
                    </div>
                    <div class="campaign-meta">
                        <div>Terkumpul: <span class="campaign-raised">Rp {c['raised']:,}</span></div>
                        <div><b>{pct}%</b> dari Rp {c['target']:,}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ─── TAB 2: DONASI FORM ───
with tab_donasi:
    d_col1, d_col2 = st.columns([5, 4], gap="large")

    with d_col1:
        st.markdown("""
        <div class="surface-card">
            <div class="surface-title">Kirimkan Donasi Anda</div>
            <div class="surface-desc">Transaksi Anda akan diverifikasi dan dicatat permanen ke dalam rantai blok.</div>
        """, unsafe_allow_html=True)

        camp_list = [c["title"] for c in st.session_state.campaigns]
        selected_camp = st.selectbox("Pilih Program Donasi", camp_list)
        donor_name = st.text_input("Nama Donatur", placeholder="Masukkan nama atau anonim")
        donor_nominal = st.number_input("Nominal Donasi (IDR)", min_value=10000, value=50000, step=10000)
        donor_msg = st.text_input("Pesan / Catatan Tambahan", placeholder="Pesan dukungan atau doa")

        if st.button("Konfirmasi & Simpan ke Blockchain", type="primary", use_container_width=True):
            if not donor_name:
                st.warning("Silakan cantumkan nama donatur terlebih dahulu.")
            else:
                # Add transaction data to blockchain
                tx_data = {
                    "Aktor": f"Donatur ({donor_name})",
                    "Aksi": "Kirim Donasi",
                    "Nominal": f"Rp {donor_nominal:,}",
                    "Program": selected_camp,
                    "Keterangan": donor_msg or "Donasi sosial kemanusiaan"
                }
                st.session_state.blockchain.add_block(tx_data)

                # Update target campaign
                for c in st.session_state.campaigns:
                    if c["title"] == selected_camp:
                        c["raised"] += donor_nominal
                        break

                st.success(f"Donasi sebesar Rp {donor_nominal:,} dari {donor_name} berhasil divalidasi dan dicatat!")
                st.balloons()

        st.markdown("</div>", unsafe_allow_html=True)

    with d_col2:
        st.markdown("""
        <div class="surface-card">
            <div class="surface-title">Prinsip Transparansi Sistem</div>
            <div class="surface-desc">Standar akuntabilitas yang diterapkan pada platform AmalKita:</div>
            <div style="font-size:13px; color:#202923; line-height: 1.8;">
                <p>• <b>Kekekalan Data (Immutability):</b> Setiap donasi yang tercatat memiliki identitas kriptografi SHA-256 yang saling terikat.</p>
                <p>• <b>Keterlacakan Alokasi:</b> Seluruh arus penarikan dana oleh lembaga pengelola memerlukan bukti transaksi terbuka.</p>
                <p>• <b>Validasi Desentralisasi:</b> Menghilangkan satu titik kegagalan melalui konsensus terstruktur.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ─── TAB 3: BLOCKCHAIN EXPLORER ───
with tab_chain:
    is_valid = st.session_state.blockchain.is_valid()
    status_label = "TERVALIDASI & AMAN" if is_valid else "INTEGRITAS TIDAK VALID"
    status_color = "#245C46" if is_valid else "#C62828"

    st.markdown(f"""
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
        <span style="font-weight:700; font-size:18px; color:#202923;">Riwayat Blok Transaksi</span>
        <span style="font-size:12px; font-weight:700; color:{status_color}; background-color:#E5F0E7; padding:4px 12px; border-radius:6px;">Status: {status_label}</span>
    </div>
    """, unsafe_allow_html=True)

    for b in reversed(st.session_state.blockchain.chain):
        st.markdown(f"""
        <div class="chain-block">
            <div class="chain-header">
                <span>Block #{b.index}</span>
                <span class="chain-time">{b.timestamp}</span>
            </div>
            <div class="chain-detail"><b>Payload Transaksi:</b> {b.data}</div>
            <div class="chain-hash"><b>Hash Saat Ini:</b> {b.hash}</div>
            <div class="chain-hash"><b>Previous Hash:</b> {b.previous_hash}</div>
        </div>
        """, unsafe_allow_html=True)

# ─── TAB 4: POW DEMO ───
with tab_pow:
    st.markdown("<div style='font-weight:700; font-size:18px; color:#202923; margin-bottom:4px;'>Simulasi Proof of Work (PoW)</div>", unsafe_allow_html=True)
    st.caption("Eksperimen komputasi konsensus Proof of Work menggunakan parameter difficulty SHA-256.")

    pow_diff = st.slider("Tingkat Kesulitan (Difficulty)", min_value=2, max_value=5, value=3)
    if st.button("Jalankan Eksperimen Mining", type="primary"):
        test_block = Block(
            index=99,
            data={"Aksi": "Validasi Donasi Massal", "Info": "Simulasi Konsensus PoW"},
            previous_hash=st.session_state.blockchain.chain[-1].hash
        )
        target = "0" * pow_diff
        start_time = time.time()

        with st.spinner("Menghitung hash yang memenuhi difficulty..."):
            test_block.hash = test_block.calculate_hash()
            while not test_block.hash.startswith(target):
                test_block.nonce += 1
                test_block.hash = test_block.calculate_hash()

        duration = time.time() - start_time
        st.success(f"Blok berhasil ditambang dalam {duration:.4f} detik!")
        st.json({
            "Difficulty": pow_diff,
            "Nonce Ditemukan": test_block.nonce,
            "Durasi Komputasi (Detik)": round(duration, 4),
            "Hash Valid": test_block.hash
        })

# ─── TAB 5: POS DEMO ───
with tab_pos:
    st.markdown("<div style='font-weight:700; font-size:18px; color:#202923; margin-bottom:4px;'>Simulasi Proof of Stake (PoS)</div>", unsafe_allow_html=True)
    st.caption("Mekanisme seleksi validator berdasarkan proporsi bobot saham jaminan (stake).")

    validators = {
        "Yayasan Amal": 40,
        "Auditor Independen": 30,
        "Vendor Bahan & Logistik": 20,
        "Perwakilan Donatur": 10
    }

    st.write("**Distribusi Bobot Stake:**")
    st.write(validators)

    sim_rounds = st.number_input("Jumlah Putaran Simulasi", min_value=5, max_value=100, value=20)
    if st.button("Mulai Simulasi Validator", type="primary"):
        summary = {k: 0 for k in validators}
        for _ in range(sim_rounds):
            selected = proof_of_stake(validators)
            summary[selected] += 1

        st.write("##### Ringkasan Terpilih:")
        for val, count in summary.items():
            pct = (count / sim_rounds) * 100
            st.write(f"- **{val}**: terpilih {count} kali ({pct:.1f}%)")
            st.progress(int(pct))

# 8. Clean Minimalist Footer
st.markdown("""
<div class="app-footer">
    <b>AmalKita</b> &bull; Platform Donasi Transparan Berbasis Blockchain &bull; Modern Minimalist Architecture
</div>
""", unsafe_allow_html=True)
