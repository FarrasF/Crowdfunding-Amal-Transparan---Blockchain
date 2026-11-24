import streamlit as st
import time
from datetime import datetime
from block import Block
from blockchain import Blockchain
from pos import proof_of_stake

# ── Page config ──────────────────────────────────────────
st.set_page_config(
    page_title="AmalKita — Transparent Blockchain Crowdfunding",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Design system: earth-tone editorial CSS ──────────────
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,400;6..72,500;6..72,600;6..72,700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

:root {
  --bg:       #F4F1EA;
  --surface:  #EAE5D9;
  --card:     #FFFFFF;
  --border:   rgba(26,36,27,.14);
  --text:     #1A241B;
  --muted:    #4A5548;
  --pine:     #234E34;
  --pine-h:   #1B3D28;
  --clay:     #B85D3B;
  --accent:   #E5F0E7;
  --serif:    'Newsreader', Georgia, serif;
  --sans:     'Plus Jakarta Sans', system-ui, sans-serif;
}

/* ── global reset ── */
html, body, [class*="css"], .stApp {
  font-family: var(--sans) !important;
  background-color: var(--bg) !important;
  background-image:
    radial-gradient(ellipse at 15% 8%, rgba(35,78,52,.045) 0%, transparent 55%),
    radial-gradient(ellipse at 85% 75%, rgba(184,93,59,.035) 0%, transparent 50%),
    radial-gradient(circle at 50% 50%, rgba(35,78,52,.018) 0%, transparent 70%),
    url("data:image/svg+xml,%3Csvg width='60' height='60' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M30 0v60M0 30h60' stroke='%231A241B' stroke-width='.3' opacity='.04'/%3E%3C/svg%3E");
  background-attachment: fixed;
  color: var(--text) !important;
}
header[data-testid="stHeader"] { background: transparent !important; }
#MainMenu, footer { visibility: hidden; }

.main .block-container {
  max-width: 1080px !important;
  padding-top: 1.2rem !important;
  padding-bottom: 3rem !important;
}

/* ── typography helpers ── */
.ed-serif { font-family: var(--serif) !important; }
.tabnum   { font-variant-numeric: tabular-nums; }

/* ── header bar ── */
.hd-bar {
  display: flex; justify-content: space-between; align-items: center;
  padding: 14px 22px;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 10px;
  margin-bottom: 20px;
}
.hd-brand {
  font-family: var(--serif); font-size: 19px; font-weight: 700;
  color: var(--pine); letter-spacing: -.3px;
  display: flex; align-items: center; gap: 7px;
}
.hd-pill {
  font-size: 11px; font-weight: 600; color: var(--pine);
  background: var(--accent); padding: 4px 12px; border-radius: 6px;
  display: inline-flex; align-items: center; gap: 5px;
}
.hd-dot {
  width: 6px; height: 6px; background: var(--pine);
  border-radius: 50%; display: inline-block;
}

/* ── hero ── */
.hero {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 40px 34px 36px;
  margin-bottom: 22px;
}
.hero-kicker {
  font-family: var(--sans); font-size: 11px; font-weight: 600;
  text-transform: uppercase; letter-spacing: .8px;
  color: var(--pine); margin-bottom: 14px;
}
.hero h1 {
  font-family: var(--serif) !important; font-size: 34px; font-weight: 700;
  color: var(--text); line-height: 1.22; letter-spacing: -.6px;
  margin: 0 0 12px;
}
.hero h1 em {
  font-style: normal; color: var(--pine);
}
.hero p {
  font-size: 15px; color: var(--muted); line-height: 1.65;
  max-width: 600px; margin: 0;
}

/* ── metric row ── */
.met {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 18px 16px;
}
.met-val {
  font-family: var(--serif); font-size: 22px; font-weight: 700;
  color: var(--pine); letter-spacing: -.4px;
  font-variant-numeric: tabular-nums;
  margin-bottom: 2px;
}
.met-lbl {
  font-size: 12px; color: var(--muted); font-weight: 500;
}

/* ── tabs ── */
.stTabs [data-baseweb="tab-list"] {
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
  padding: 3px !important;
  gap: 2px !important;
}
.stTabs [data-baseweb="tab"] {
  border-radius: 7px !important;
  padding: 7px 16px !important;
  color: var(--muted) !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  border: none !important;
  background: transparent !important;
}
.stTabs [aria-selected="true"] {
  background: var(--pine) !important;
  color: #fff !important;
  font-weight: 600 !important;
}

/* ── campaign card ── */
.ccard {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 12px;
  overflow: hidden;
  margin-bottom: 18px;
}
.ccard img {
  width: 100%; height: 180px; object-fit: cover; display: block;
}
.ccard-body { padding: 20px; }
.ccard-tag {
  display: inline-block; font-size: 11px; font-weight: 600;
  color: var(--pine); background: var(--accent);
  padding: 2px 8px; border-radius: 4px; margin-bottom: 8px;
}
.ccard-title {
  font-family: var(--serif); font-size: 17px; font-weight: 600;
  color: var(--text); line-height: 1.32; margin-bottom: 6px;
}
.ccard-desc {
  font-size: 13px; color: var(--muted); line-height: 1.55;
  margin-bottom: 14px; min-height: 40px;
}
.ccard-bar-bg {
  background: var(--surface); border-radius: 4px; height: 5px;
  overflow: hidden; margin-bottom: 8px;
}
.ccard-bar {
  background: var(--pine); height: 100%; border-radius: 4px;
}
.ccard-row {
  display: flex; justify-content: space-between;
  font-size: 12px; color: var(--muted);
  font-variant-numeric: tabular-nums;
}
.ccard-row b { color: var(--text); }

/* ── surface panels ── */
.panel {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 22px;
}
.panel-title {
  font-family: var(--serif); font-size: 16px; font-weight: 600;
  color: var(--text); margin-bottom: 4px;
}
.panel-sub {
  font-size: 13px; color: var(--muted); margin-bottom: 16px;
}

/* ── chain block ── */
.blk {
  background: var(--card);
  border: 1px solid var(--border);
  border-left: 3px solid var(--pine);
  border-radius: 10px;
  padding: 16px 18px;
  margin-bottom: 10px;
}
.blk-head {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 8px;
}
.blk-id {
  font-family: var(--serif); font-size: 14px; font-weight: 700;
  color: var(--pine);
}
.blk-ts {
  font-size: 11px; color: var(--muted);
}
.blk-data {
  font-size: 13px; color: var(--text); margin-bottom: 8px; line-height: 1.5;
}
.blk-hash {
  font-family: ui-monospace, 'SFMono-Regular', Menlo, monospace !important;
  font-size: 11px; color: var(--muted);
  word-break: break-all; line-height: 1.45;
}

/* ── buttons ── */
button[kind="primary"] {
  background: var(--pine) !important;
  border: 1px solid var(--pine) !important;
  border-radius: 8px !important;
  font-weight: 600 !important; font-size: 14px !important;
  color: #fff !important;
  box-shadow: none !important;
}
button[kind="primary"]:hover {
  background: var(--pine-h) !important;
  border-color: var(--pine-h) !important;
}
button[kind="secondary"] {
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
  font-weight: 500 !important; font-size: 14px !important;
  color: var(--text) !important;
}
button[kind="secondary"]:hover {
  border-color: #A8BFA8 !important; color: var(--pine) !important;
}

/* ── inputs ── */
.stTextInput input, .stNumberInput input, .stTextArea textarea {
  border-radius: 8px !important;
  border: 1px solid var(--border) !important;
  background: var(--card) !important;
  font-size: 14px !important;
}
.stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {
  border-color: var(--pine) !important;
  box-shadow: 0 0 0 2px rgba(35,78,52,.10) !important;
}
.stSelectbox [data-baseweb="select"] > div {
  border-radius: 8px !important;
  border-color: rgba(26,36,27,.14) !important;
}

/* ── slider ── */
.stSlider [data-baseweb="slider"] [role="slider"] {
  background: var(--pine) !important;
}

/* ── progress bar ── */
.stProgress > div > div > div > div {
  background: var(--pine) !important;
}

/* ── verification badges ── */
.vbadge {
  display: inline-flex; align-items: center; gap: 5px;
  font-size: 12px; font-weight: 600;
  padding: 4px 10px; border-radius: 6px;
  border: 1px solid var(--border);
  background: var(--card); color: var(--muted);
}
.vbadge-ok { border-color: var(--pine); color: var(--pine); }

/* ── footer ── */
.ft {
  text-align: center; padding: 28px 0 12px;
  margin-top: 40px; border-top: 1px solid var(--border);
  font-size: 12px; color: var(--muted);
}
</style>""", unsafe_allow_html=True)


# ── Session state (100 % preserved) ─────────────────────
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


# ── Header bar ──────────────────────────────────────────
st.markdown("""<div class="hd-bar">
<div class="hd-brand"><span>🌱</span> AmalKita</div>
<div class="hd-pill"><span class="hd-dot"></span>Blockchain Aktif</div>
</div>""", unsafe_allow_html=True)


# ── Hero ────────────────────────────────────────────────
st.markdown("""<div class="hero">
<div class="hero-kicker">Crowdfunding &middot; Blockchain &middot; Transparan</div>
<h1>Kebaikan Kecil, <em>Dampak Nyata.</em></h1>
<p>Setiap kontribusi tercatat pada buku besar terdistribusi &mdash; akuntabel, transparan, dan tidak dapat dimanipulasi oleh siapa pun.</p>
</div>""", unsafe_allow_html=True)


# ── Metrics row ─────────────────────────────────────────
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown('<div class="met"><div class="met-val">Rp 2.4 M+</div><div class="met-lbl">Total Dana Tersalurkan</div></div>', unsafe_allow_html=True)
with m2:
    st.markdown('<div class="met"><div class="met-val">1,920</div><div class="met-lbl">Partisipasi Donatur</div></div>', unsafe_allow_html=True)
with m3:
    st.markdown('<div class="met"><div class="met-val">48</div><div class="met-lbl">Program Selesai</div></div>', unsafe_allow_html=True)
with m4:
    st.markdown('<div class="met"><div class="met-val">100 %</div><div class="met-lbl">Integritas Kriptografi</div></div>', unsafe_allow_html=True)

st.write("")


# ── Tabs (all original logic preserved) ─────────────────
tab_camp, tab_donasi, tab_chain, tab_pow, tab_pos = st.tabs([
    "Program Donasi",
    "Formulir Donasi",
    "Buku Besar Blockchain",
    "Konsensus PoW",
    "Konsensus PoS",
])


# ═══ TAB 1 — CAMPAIGNS ═══
with tab_camp:
    st.markdown('<div style="font-family:var(--serif);font-size:20px;font-weight:700;color:#1A241B;margin-bottom:14px;">Inisiatif Kemanusiaan Aktif</div>', unsafe_allow_html=True)

    c_rows = st.columns(2)
    for idx, c in enumerate(st.session_state.campaigns):
        with c_rows[idx % 2]:
            pct = min(100, int((c["raised"] / c["target"]) * 100))
            st.markdown(f'<div class="ccard">'
                f'<img src="{c["img"]}" alt="{c["title"]}">'
                f'<div class="ccard-body">'
                f'<span class="ccard-tag">{c["category"]}</span>'
                f'<div class="ccard-title">{c["title"]}</div>'
                f'<div class="ccard-desc">{c["desc"]}</div>'
                f'<div class="ccard-bar-bg"><div class="ccard-bar" style="width:{pct}%"></div></div>'
                f'<div class="ccard-row"><div>Terkumpul: <b>Rp {c["raised"]:,}</b></div>'
                f'<div><b>{pct}%</b> &middot; Target Rp {c["target"]:,}</div></div>'
                f'</div></div>', unsafe_allow_html=True)

    # Verification & standards
    st.write("")
    st.markdown('<div style="font-family:var(--serif);font-size:16px;font-weight:600;color:#1A241B;margin-bottom:10px;">Verifikasi & Standar</div>', unsafe_allow_html=True)
    with st.expander("Blockchain SHA-256 — Impact Verified", expanded=False):
        st.write("Setiap transaksi donasi di-hash dengan algoritma **SHA-256** dan dirangkai ke blok sebelumnya, "
                 "membentuk rantai tak-terputus. Manipulasi satu blok akan meng-invalidasi seluruh rantai sesudahnya.")
    with st.expander("Open Audit — Transparansi Publik", expanded=False):
        st.write("Seluruh catatan donasi dan penarikan dana dapat diaudit secara publik melalui tab **Buku Besar Blockchain**. "
                 "Tidak ada transaksi yang dapat disembunyikan atau dihapus setelah tercatat.")
    with st.expander("Desentralisasi Konsensus — PoW & PoS", expanded=False):
        st.write("Platform mendukung dua mekanisme konsensus: **Proof of Work** (keamanan komputasi) dan "
                 "**Proof of Stake** (seleksi validator berbasis jaminan). Keduanya dapat disimulasikan pada tab terkait.")


# ═══ TAB 2 — DONATION FORM ═══
with tab_donasi:
    d_col1, d_col2 = st.columns([5, 4], gap="large")

    with d_col1:
        st.markdown('<div class="panel">'
            '<div class="panel-title">Kirimkan Donasi Anda</div>'
            '<div class="panel-sub">Transaksi akan diverifikasi dan dicatat permanen ke rantai blok.</div>'
            '</div>', unsafe_allow_html=True)

        st.write("")
        camp_list = [c["title"] for c in st.session_state.campaigns] + ["✏️ Lainnya (input manual)"]
        selected_camp = st.selectbox("Pilih Program Donasi", camp_list)

        # Jika user memilih "Lainnya", tampilkan text input untuk nama program custom
        if selected_camp == "✏️ Lainnya (input manual)":
            custom_camp = st.text_input("Nama Program Donasi", placeholder="Contoh: Bantuan Gempa Cianjur")
            final_camp = custom_camp.strip()
        else:
            final_camp = selected_camp

        donor_name = st.text_input("Nama Donatur", placeholder="Masukkan nama atau anonim")
        donor_nominal = st.number_input("Nominal Donasi (IDR)", min_value=10000, value=50000, step=10000)
        donor_msg = st.text_input("Pesan / Catatan Tambahan", placeholder="Pesan dukungan atau doa")

        if st.button("Konfirmasi & Simpan ke Blockchain", type="primary", use_container_width=True):
            if not donor_name:
                st.warning("Silakan cantumkan nama donatur terlebih dahulu.")
            elif not final_camp:
                st.warning("Silakan isi nama program donasi terlebih dahulu.")
            else:
                tx_data = {
                    "Aktor": f"Donatur ({donor_name})",
                    "Aksi": "Kirim Donasi",
                    "Nominal": f"Rp {donor_nominal:,}",
                    "Program": final_camp,
                    "Keterangan": donor_msg or "Donasi sosial kemanusiaan"
                }
                st.session_state.blockchain.add_block(tx_data)

                for c in st.session_state.campaigns:
                    if c["title"] == final_camp:
                        c["raised"] += donor_nominal
                        break

                st.success(f"Donasi sebesar Rp {donor_nominal:,} dari {donor_name} berhasil dicatat ke program \"{final_camp}\"!")
                st.balloons()

    with d_col2:
        st.markdown('<div class="panel">'
            '<div class="panel-title">Prinsip Transparansi</div>'
            '<div class="panel-sub">Standar akuntabilitas AmalKita:</div>'
            '<div style="font-size:13px;color:#1A241B;line-height:1.75">'
            '<p style="margin:0 0 10px"><b style="color:#234E34">Immutability</b> &mdash; Catatan donasi memiliki identitas kriptografi SHA-256 yang saling terikat antar blok.</p>'
            '<p style="margin:0 0 10px"><b style="color:#234E34">Keterlacakan</b> &mdash; Seluruh arus penarikan dana memerlukan bukti transaksi terbuka di buku besar.</p>'
            '<p style="margin:0"><b style="color:#234E34">Desentralisasi</b> &mdash; Menghilangkan satu titik kegagalan melalui konsensus terstruktur.</p>'
            '</div></div>', unsafe_allow_html=True)


# ═══ TAB 3 — BLOCKCHAIN EXPLORER ═══
with tab_chain:
    is_valid = st.session_state.blockchain.is_valid()
    status_label = "TERVALIDASI" if is_valid else "TIDAK VALID"
    status_cls   = "vbadge vbadge-ok" if is_valid else "vbadge"

    st.markdown(f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">'
        f'<span style="font-family:var(--serif);font-size:20px;font-weight:700;color:#1A241B">Riwayat Blok Transaksi</span>'
        f'<span class="{status_cls}">{status_label}</span>'
        f'</div>', unsafe_allow_html=True)

    for b in reversed(st.session_state.blockchain.chain):
        st.markdown(
            f'<div class="blk">'
            f'<div class="blk-head"><span class="blk-id">Block #{b.index}</span><span class="blk-ts">{b.timestamp}</span></div>'
            f'<div class="blk-data"><b>Payload:</b> {b.data}</div>'
            f'<div class="blk-hash"><b>Hash:</b> {b.hash}</div>'
            f'<div class="blk-hash"><b>Prev:</b> {b.previous_hash}</div>'
            f'</div>', unsafe_allow_html=True)


# ═══ TAB 4 — POW ═══
with tab_pow:
    st.markdown('<div style="font-family:var(--serif);font-size:20px;font-weight:700;color:#1A241B;margin-bottom:4px">Simulasi Proof of Work</div>', unsafe_allow_html=True)
    st.caption("Eksperimen pencarian hash SHA-256 yang memenuhi syarat difficulty.")

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

        r1, r2 = st.columns(2)
        with r1:
            st.markdown(f'<div class="met"><div class="met-val tabnum">{test_block.nonce:,}</div><div class="met-lbl">Nonce Ditemukan</div></div>', unsafe_allow_html=True)
        with r2:
            st.markdown(f'<div class="met"><div class="met-val tabnum">{duration:.4f} s</div><div class="met-lbl">Waktu Komputasi</div></div>', unsafe_allow_html=True)

        with st.expander("Detail Hash", expanded=True):
            st.code(test_block.hash, language=None)


# ═══ TAB 5 — POS ═══
with tab_pos:
    st.markdown('<div style="font-family:var(--serif);font-size:20px;font-weight:700;color:#1A241B;margin-bottom:4px">Simulasi Proof of Stake</div>', unsafe_allow_html=True)
    st.caption("Seleksi validator berdasarkan proporsi bobot saham jaminan (stake).")

    validators = {
        "Yayasan Amal": 40,
        "Auditor Independen": 30,
        "Vendor Bahan & Logistik": 20,
        "Perwakilan Donatur": 10
    }

    st.write("**Distribusi Bobot Stake:**")
    total_s = sum(validators.values())
    for vname, vstake in validators.items():
        vpct = vstake / total_s * 100
        st.markdown(f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">'
            f'<span style="font-size:13px;font-weight:600;color:#1A241B;min-width:180px">{vname}</span>'
            f'<div style="flex:1;background:#EAE5D9;border-radius:3px;height:6px;overflow:hidden">'
            f'<div style="width:{vpct}%;height:100%;background:#234E34;border-radius:3px"></div></div>'
            f'<span style="font-size:12px;font-weight:600;color:#4A5548;min-width:30px;text-align:right">{vstake}</span>'
            f'</div>', unsafe_allow_html=True)

    st.write("")
    sim_rounds = st.number_input("Jumlah Putaran Simulasi", min_value=5, max_value=100, value=20)
    if st.button("Mulai Simulasi Validator", type="primary"):
        summary = {k: 0 for k in validators}
        for _ in range(sim_rounds):
            selected = proof_of_stake(validators)
            summary[selected] += 1

        st.markdown('<div style="font-family:var(--serif);font-size:16px;font-weight:600;color:#1A241B;margin:12px 0 8px">Hasil Seleksi</div>', unsafe_allow_html=True)
        for val, count in summary.items():
            pct = (count / sim_rounds) * 100
            st.write(f"**{val}** — terpilih {count}× ({pct:.1f}%)")
            st.progress(int(pct))


# ── Footer ──────────────────────────────────────────────
st.markdown('<div class="ft">AmalKita &middot; Transparansi Kemanusiaan Berbasis Blockchain</div>', unsafe_allow_html=True)
