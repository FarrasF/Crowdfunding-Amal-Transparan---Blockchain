"""AmalKita - antarmuka Streamlit untuk smart contract CrowdfundingKitabisa (Modul 11).

Semua data dibaca dari smart contract lewat web3.py. Semua aksi (buat, verifikasi, donasi,
tarik dana, tutup) dikirim sebagai transaksi yang DITANDATANGANI DI METAMASK oleh akun yang
sedang terhubung. Jika MetaMask belum terhubung, tersedia mode demo memakai akun Hardhat.
"""
import html
from uuid import uuid4

import streamlit as st
import streamlit.components.v2 as components
from web3 import Web3
from web3.logs import DISCARD

import contract_service as svc

st.set_page_config(page_title="AmalKita - Donasi Transparan di Blockchain", page_icon="🌱",
                   layout="wide", initial_sidebar_state="collapsed")

with open(svc.PROJECT_DIR / "theme.css", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

esc = html.escape

# Catatan yang tampil di UI: nama donatur bukan data blockchain
NAME_NOTE = ("Nama donatur adalah nama contoh yang dibuat otomatis dari alamat wallet dan bisa diubah "
             "di tab Wallet & Riwayat. Blockchain hanya menyimpan alamat wallet.")

# ==========================================
# KOMPONEN METAMASK: connect + tanda tangan transaksi
# ==========================================
WALLET_HTML = """<div class="wb"><button id="cw-btn" type="button"><span class="d"></span><span id="cw-txt">Hubungkan MetaMask</span></button><div id="cw-msg" role="status"></div></div>"""
WALLET_CSS = """
.wb { display:flex; flex-direction:column; align-items:flex-end; gap:4px; font-family:'Figtree',system-ui,sans-serif; }
button { display:inline-flex; align-items:center; gap:9px; background:#0B6B57; color:#fff; border:0; border-radius:999px;
  padding:10px 18px; font:700 14px 'Figtree',system-ui,sans-serif; cursor:pointer; transition:background .15s; }
button:hover { background:#08493C; }
button:focus-visible { outline:3px solid #F4B63F; outline-offset:2px; }
button[data-on="1"] { background:#E3F3EC; color:#08493C; }
.d { width:9px; height:9px; border-radius:50%; background:#F4B63F; }
button[data-on="1"] .d { background:#1FB36B; box-shadow:0 0 0 3px rgba(31,179,107,.2); }
#cw-msg { font-size:12px; color:#51645C; max-width:260px; text-align:right; }
#cw-msg:empty { display:none; }
"""
WALLET_JS = """
export default function (component) {
  const { parentElement, setStateValue, data } = component;
  const eth = window.ethereum;
  const btn = parentElement.querySelector("#cw-btn");
  const txt = parentElement.querySelector("#cw-txt");
  const msg = parentElement.querySelector("#cw-msg");
  const short = (a) => a.slice(0, 6) + "…" + a.slice(-4);
  const last = (window.__cwLast = window.__cwLast || {});
  const emit = (k, v) => { const s = JSON.stringify(v); if (last[k] !== s) { last[k] = s; setStateValue(k, v); } };
  const paint = (a) => { txt.textContent = a ? short(a) : "Hubungkan MetaMask"; btn.dataset.on = a ? "1" : "0"; };
  const onAccounts = (a) => { const addr = a && a.length ? a[0] : null; paint(addr); emit("address", addr); };
  const onChain = (c) => emit("chain_id", parseInt(c, 16));

  async function ensureChain() {
    const ch = data.chain;
    try {
      await eth.request({ method: "wallet_switchEthereumChain", params: [{ chainId: ch.chainId }] });
    } catch (e) {
      const code = e && (e.code || (e.data && e.data.originalError && e.data.originalError.code));
      if (code === 4902) await eth.request({ method: "wallet_addEthereumChain", params: [ch] });
      else throw e;
    }
  }

  btn.onclick = async () => {
    if (!eth) { msg.textContent = "MetaMask tidak terdeteksi di browser ini."; return; }
    try {
      msg.textContent = "Menunggu persetujuan di MetaMask…";
      if (btn.dataset.on === "1") {
        await eth.request({ method: "wallet_requestPermissions", params: [{ eth_accounts: {} }] });
      }
      const a = await eth.request({ method: "eth_requestAccounts" });
      try { await ensureChain(); } catch (e) { /* pengguna menolak ganti jaringan */ }
      onAccounts(a); onChain(await eth.request({ method: "eth_chainId" }));
      msg.textContent = "";
    } catch (err) {
      msg.textContent = "Koneksi dibatalkan.";
    }
  };

  if (eth) {
    eth.request({ method: "eth_accounts" }).then(onAccounts).catch(() => {});
    eth.request({ method: "eth_chainId" }).then(onChain).catch(() => {});
    if (eth.on) { eth.on("accountsChanged", onAccounts); eth.on("chainChanged", onChain); }
  } else {
    msg.textContent = "MetaMask tidak terdeteksi. Mode demo tetap bisa dipakai.";
  }

  // kirim transaksi yang diminta Python (sekali per id)
  const tx = data && data.tx;
  const sent = (window.__cwSent = window.__cwSent || {});
  if (tx && eth && !sent[tx.id]) {
    sent[tx.id] = true;
    (async () => {
      try {
        await ensureChain();
        const hash = await eth.request({ method: "eth_sendTransaction",
          params: [{ from: tx.from, to: tx.to, data: tx.data, value: tx.value }] });
        emit("tx_result", { id: tx.id, hash });
      } catch (e) {
        emit("tx_result", { id: tx.id, error: (e && e.message) || "Transaksi gagal", code: e && e.code });
      }
    })();
  } else if (tx && !eth && !sent[tx.id]) {
    sent[tx.id] = true;
    emit("tx_result", { id: tx.id, error: "MetaMask tidak terdeteksi", code: -1 });
  }

  return () => {
    if (eth && eth.removeListener) {
      eth.removeListener("accountsChanged", onAccounts);
      eth.removeListener("chainChanged", onChain);
    }
  };
}
"""
wallet_component = components.component("metamask_wallet", html=WALLET_HTML, css=WALLET_CSS, js=WALLET_JS)
CHAIN = {"chainId": hex(31337), "chainName": "Hardhat Local", "rpcUrls": [svc.RPC_URL],
         "nativeCurrency": {"name": "Ether", "symbol": "ETH", "decimals": 18}}

# ==========================================
# BILAH ATAS
# ==========================================
pending = st.session_state.get("pending")
nav_l, nav_m, nav_r = st.columns([2.2, 1.6, 1.5], vertical_alignment="center")
nav_l.markdown('<div class="brand"><span class="brand-mark"><svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.2" '
               'stroke-linecap="round" stroke-linejoin="round"><path d="M12 21v-8"/><path d="M12 13c0-4 3-6 7-6 0 4-3 6-7 6z"/>'
               '<path d="M12 15c0-3-2-5-6-5 0 3 2 5 6 5z"/></svg></span>AmalKita</div>', unsafe_allow_html=True)
nav_m.markdown('<span class="net"><i></i>Hardhat Local · smart contract</span>', unsafe_allow_html=True)
with nav_r:
    wallet = wallet_component(key="wallet", data={"chain": CHAIN, "tx": ({**pending["req"], "id": pending["id"]} if pending else None)},
                              on_address_change=lambda: None, on_chain_id_change=lambda: None,
                              on_tx_result_change=lambda: None)

# ==========================================
# KONEKSI KE BLOCKCHAIN
# ==========================================
w3 = svc.get_w3()
try:
    contract = svc.load_contract(w3)
except svc.ServiceError as e:
    st.error(str(e))
    st.stop()

ADMIN = contract.functions.owner().call()
NODE_ACCOUNTS = [Web3.to_checksum_address(a) for a in w3.eth.accounts]
NAMES = svc.load_names()


def nm(addr):
    return svc.who(addr, ADMIN, NAMES)


rp = svc.rupiah


def idr(n):
    return "Rp " + f"{int(n):,}".replace(",", ".")


def flash(kind, text):
    st.session_state["flash"] = (kind, text)


# ==========================================
# AKUN AKTIF: MetaMask (utama) atau akun demo Hardhat
# ==========================================
wallet_addr = Web3.to_checksum_address(wallet.address) if getattr(wallet, "address", None) else None
MM = wallet_addr is not None
if MM:
    SIGNER = wallet_addr
else:
    with st.container(border=True):
        st.caption("MetaMask belum terhubung. Klik **Hubungkan MetaMask** di kanan atas, atau pilih akun demo:")
        sidx = st.selectbox("Masuk sebagai", range(len(NODE_ACCOUNTS)), key="signer",
                            format_func=lambda i: f"{nm(NODE_ACCOUNTS[i])}  ·  {'Admin' if NODE_ACCOUNTS[i] == ADMIN else 'Donatur'}")
    SIGNER = NODE_ACCOUNTS[sidx]
IS_ADMIN = SIGNER == ADMIN
balance = svc.eth(w3, w3.eth.get_balance(SIGNER))


# ==========================================
# TRANSAKSI
# ==========================================
def finish_message(ok_msg, kind, r):
    msg = f"{ok_msg} (blok #{r['blockNumber']}, tx {r['transactionHash'].hex()[:12]}…)"
    if kind == "donate":
        ev = contract.events.ReceiptMinted().process_receipt(r, errors=DISCARD)
        if ev:
            msg += f" NFT bukti donasi #{ev[0]['args']['tokenId']} dicetak."
    return msg


def run_tx(fn, value_wei=0, ok_msg="Transaksi berhasil.", kind=None):
    """Cek dulu ke kontrak (tanpa biaya), lalu kirim lewat MetaMask atau akun demo. Pemanggil harus st.rerun()."""
    err = svc.preflight(w3, contract, fn, SIGNER, value_wei)
    if err:
        flash("err", err)
        return
    if MM:
        st.session_state["pending"] = {"id": uuid4().hex, "req": svc.tx_request(fn, SIGNER, contract.address, value_wei),
                                       "ok": ok_msg, "kind": kind}
    else:
        try:
            r = svc.send(w3, contract, fn, SIGNER, value_wei)
            flash("ok", finish_message(ok_msg, kind, r))
        except svc.ServiceError as e:
            flash("err", str(e))


# hasil tanda tangan dari MetaMask
res = getattr(wallet, "tx_result", None)
if pending and res and res.get("id") == pending["id"]:
    st.session_state.pop("pending", None)
    if res.get("hash"):
        try:
            flash("ok", finish_message(pending["ok"], pending["kind"], svc.confirm(w3, contract, res["hash"])))
        except svc.ServiceError as e:
            flash("err", str(e))
    elif res.get("code") == 4001:
        flash("err", "Transaksi dibatalkan di MetaMask.")
    else:
        flash("err", f"MetaMask: {res.get('error', 'transaksi gagal')}")
    st.rerun()

# ==========================================
# STATUS AKUN
# ==========================================
role_html = '<span class="role admin">Admin</span>' if IS_ADMIN else '<span class="role donor">Donatur</span>'
st.markdown(f'<div class="acct">Akun aktif <b>{esc(nm(SIGNER))}</b>{role_html}'
            f'<span>Saldo <b>{rp(balance)}</b></span>'
            f'<span>{"Tanda tangan lewat MetaMask" if MM else "Mode demo (tanpa MetaMask)"}</span></div>', unsafe_allow_html=True)

if MM and wallet.chain_id is not None and wallet.chain_id != w3.eth.chain_id:
    st.warning(f"MetaMask ada di jaringan Chain ID {wallet.chain_id}, bukan Hardhat Local ({w3.eth.chain_id}). "
               "Klik tombol MetaMask lalu setujui pergantian jaringan.")
if MM and balance < 1:
    with st.container(border=True):
        c1, c2 = st.columns([3, 1], vertical_alignment="center")
        c1.markdown(f"Saldo akun ini **{rp(balance)}** di jaringan lokal, jadi belum bisa berdonasi atau membayar gas. "
                    "Isi saldo uji senilai 10 ETH (hanya berlaku di Hardhat lokal).")
        if c2.button("Isi saldo uji", type="primary", key="faucet_top", use_container_width=True):
            try:
                svc.faucet(w3, SIGNER, 10)
                flash("ok", f"Saldo uji {rp(10)} ditambahkan ke akun ini.")
            except svc.ServiceError as e:
                flash("err", str(e))
            st.rerun()
if pending:
    with st.container(border=True):
        c1, c2 = st.columns([3, 1], vertical_alignment="center")
        c1.markdown("**Menunggu konfirmasi di MetaMask.** Buka ekstensi MetaMask, periksa detailnya, lalu setujui transaksi.")
        if c2.button("Batalkan", key="cancel_pending", use_container_width=True):
            st.session_state.pop("pending", None)
            flash("err", "Menunggu konfirmasi dibatalkan.")
            st.rerun()

fl = st.session_state.pop("flash", None)
if fl:
    (st.success if fl[0] == "ok" else st.error)(fl[1])

# ==========================================
# DATA DARI KONTRAK
# ==========================================
campaigns = svc.list_campaigns(w3, contract)
receipts = svc.list_receipts(w3, contract)
txs = svc.list_transactions(w3, contract)
by_id = {c["id"]: c for c in campaigns}
total_raised = sum(c["raised"] for c in campaigns)
total_withdrawn = sum(c["withdrawn"] for c in campaigns)
n_active = sum(1 for c in campaigns if c["status"] == 1)
n_pending = sum(1 for c in campaigns if c["status"] == 0)
n_donors = len({r["donor"] for r in receipts})
pct_out = min(100, total_withdrawn / total_raised * 100) if total_raised else 0

# ---------- tema visual per kampanye (dari kata di judul) ----------
ICONS = {
    "book": '<path d="M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2z"/><path d="M8 7h7M8 11h5"/>',
    "drop": '<path d="M12 3s6 6.5 6 11a6 6 0 0 1-12 0c0-4.5 6-11 6-11z"/>',
    "wave": '<path d="M2 12c2.5-3 5-3 7.5 0s5 3 7.5 0 3-2 5-1"/><path d="M2 18c2.5-3 5-3 7.5 0s5 3 7.5 0 3-2 5-1"/><path d="M12 3v5M9.5 5.5h5"/>',
    "heart": '<path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.5A4 4 0 0 1 19 10c0 5.6-7 10-7 10z"/>',
    "home": '<path d="M3 11l9-7 9 7"/><path d="M5 10v10h14V10"/><path d="M10 20v-6h4v6"/>',
    "leaf": '<path d="M12 21v-8"/><path d="M12 13c0-4 3-6 7-6 0 4-3 6-7 6z"/><path d="M12 15c0-3-2-5-6-5 0 3 2 5 6 5z"/>',
}
THEMES = [
    (("beasiswa", "pendidik", "sekolah", "santri", "buku", "belajar", "guru", "kuliah"), "#3B5BDB", "#7C9CFF", "book"),
    (("air", "sumur", "kekeringan"), "#0A8FA8", "#5FD0DD", "drop"),
    (("banjir", "bencana", "gempa", "longsor", "dapur", "pengungsi", "darurat"), "#D9480F", "#FFA94D", "wave"),
    (("sehat", "medis", "obat", "sakit", "operasi", "kesehatan", "gizi"), "#C2255C", "#FF8FB1", "heart"),
    (("masjid", "musala", "mushola", "gereja", "pura", "rumah", "huni", "bedah"), "#7048E8", "#B197FC", "home"),
]
FALLBACK = [("#0B6B57", "#4CC9A6"), ("#3B5BDB", "#7C9CFF"), ("#D9480F", "#FFA94D"), ("#C2255C", "#FF8FB1")]


def theme_of(c):
    t = c["title"].lower()
    for words, c1, c2, icon in THEMES:
        if any(w in t for w in words):
            return c1, c2, icon
    c1, c2 = FALLBACK[c["id"] % len(FALLBACK)]
    return c1, c2, "leaf"


AV = ["#0B6B57", "#3B5BDB", "#D9480F", "#C2255C", "#0A8FA8", "#7048E8", "#9A6A00"]


def avatar(name):
    ini = "".join(w[0] for w in name.split()[:2]).upper()
    return f'<span class="av" style="background:{AV[sum(map(ord, name)) % len(AV)]}">{esc(ini)}</span>'


# ==========================================
# HERO + STATISTIK
# ==========================================
st.markdown(f"""<div class="hero"><div class="hero-l"><h1>Donasi yang bisa kamu periksa sendiri.</h1>
<p>Setiap donasi, penarikan, dan penutupan kampanye tercatat di smart contract. Donatur menerima NFT sebagai bukti, dan semua angka di halaman ini dibaca langsung dari blockchain.</p>
<div class="hero-steps"><span class="c1">Admin memverifikasi</span><span class="c2">Donatur berdonasi</span><span class="c3">NFT bukti diterbitkan</span><span class="c4">Penarikan tercatat</span></div></div>
<div class="hero-r"><div class="k">Total dana terkumpul</div><div class="v"><small>Rp</small>{rp(total_raised)[3:]}</div>
<div class="split"><i class="out" style="width:{pct_out:.1f}%"></i><i class="held" style="width:{100 - pct_out:.1f}%"></i></div>
<div class="legend"><span><span class="dot" style="background:#F4B63F"></span>Tertahan di kontrak <b>{rp(total_raised - total_withdrawn)}</b></span>
<span><span class="dot" style="background:#6FD3B5"></span>Sudah ditarik <b>{rp(total_withdrawn)}</b></span></div>
<div class="rate">Kurs: 1 ETH = {idr(svc.ETH_IDR)}</div></div></div>""", unsafe_allow_html=True)

for col, (v, l, k) in zip(st.columns(4), [(len(campaigns), "Total kampanye", "s1"), (n_active, "Kampanye aktif", "s2"),
                                          (n_donors, "Donatur unik", "s3"), (len(receipts), "NFT bukti donasi", "s4")]):
    col.markdown(f'<div class="stat {k}"><b>{v}</b><span>{l}</span></div>', unsafe_allow_html=True)


def campaign_card(c):
    c1, c2, icon = theme_of(c)
    pct = min(100, int(c["raised"] / c["target"] * 100)) if c["target"] else 0
    left = svc.days_left(c["deadline"])
    when = f"Berakhir {svc.fmt_time(c['deadline'])} WIB" + (f" · sisa {left} hari" if c["status"] == 1 and left else "")
    return (f'<div class="ccard"><div class="cc-hd" style="--c1:{c1};--c2:{c2}"><svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="1.4" '
            f'stroke-linecap="round" stroke-linejoin="round">{ICONS[icon]}</svg><span class="chip {svc.STATUS_CLASS[c["status"]]}">{svc.STATUS_ID[c["status"]]}</span>'
            f'<span class="cc-no">#{c["id"]}</span></div><div class="cc-body"><div class="cc-title">{esc(c["title"])}</div>'
            f'<div class="cc-sub">{when}</div><div class="bar{" full" if pct >= 100 else ""}"><i style="width:{pct}%;background:linear-gradient(90deg,{c1},{c2})"></i></div>'
            f'<div class="cc-stats"><div><b>{rp(c["raised"])}</b><span>terkumpul</span></div>'
            f'<div><b style="color:{c1}">{pct}%</b><span>dari {rp(c["target"])}</span></div>'
            f'<div><b>{rp(c["available"])}</b><span>tersedia</span></div></div></div></div>')


def tx_row(t, with_campaign=True):
    icon = {"Donasi": ("+", ""), "Penarikan dana": ("−", "w"), "Kampanye dibuat": ("N", "n"),
            "Verifikasi": ("✓", ""), "Kampanye ditutup": ("T", "x")}[t["label"]]
    if t["label"] == "Verifikasi" and "Ditolak" in t["detail"]:
        icon = ("✕", "r")
    camp = f" · {esc(by_id[t['campaign']]['title'])}" if with_campaign and t["campaign"] in by_id else ""
    return (f'<div class="tx"><div class="tx-ic {icon[1]}">{icon[0]}</div><div><div class="tx-t"><b>{t["label"]}</b>{camp}<br>{esc(t["detail"])}</div>'
            f'<div class="tx-m">blok #{t["block"]}</div></div></div>')


st.write("")
tabs = st.tabs(["Ringkasan", "Program Donasi", "Donasi", "Kelola (Admin)", "NFT Bukti", "Wallet & Riwayat"],
               key="main_tabs", on_change="rerun")
t_dash, t_prog, t_don, t_admin, t_nft, t_wallet = tabs

# ═══ 1. RINGKASAN ═══
with t_dash:
    if n_pending:
        st.info(f"{n_pending} kampanye menunggu verifikasi admin. Buka tab Kelola (Admin).")
    a, b = st.columns([1.5, 1], gap="large")
    with a:
        st.markdown('<div class="sec" style="font-size:20px">Kampanye pilihan</div>', unsafe_allow_html=True)
        act = sorted([c for c in campaigns if c["status"] == 1], key=lambda c: c["raised"], reverse=True)
        st.markdown(campaign_card(act[0]) if act else '<div class="panel"><div class="sub">Belum ada kampanye aktif.</div></div>', unsafe_allow_html=True)
    with b:
        agg = {}
        for r in receipts:
            agg[r["donor"]] = agg.get(r["donor"], 0) + r["amount"]
        top5 = sorted(agg.items(), key=lambda kv: kv[1], reverse=True)[:5]
        mx = top5[0][1] if top5 else 1
        lb = "".join(f'<div class="lb">{avatar(nm(d))}<div class="lb-m"><b>{esc(nm(d))}</b><div class="mini"><i style="width:{v / mx * 100:.0f}%"></i></div></div>'
                     f'<span class="lb-v">{rp(v)}</span></div>' for d, v in top5) or '<div class="sub">Belum ada donatur.</div>'
        st.markdown(f'<div class="sec" style="font-size:20px">Donatur teratas</div><div class="panel">{lb}</div>', unsafe_allow_html=True)
        st.caption(NAME_NOTE)
    st.write("")
    a, b = st.columns([1, 1.5], gap="large")
    with a:
        rows = "".join(f'<div class="row"><span class="chip {svc.STATUS_CLASS[i]}">{svc.STATUS_ID[i]}</span>'
                       f'<b>{sum(1 for c in campaigns if c["status"] == i)} kampanye</b></div>' for i in range(4))
        st.markdown(f'<div class="panel"><h4>Status kampanye</h4><div class="sub">Dihitung dari kontrak</div>{rows}</div>', unsafe_allow_html=True)
    with b:
        feed = "".join(tx_row(t) for t in txs[:4]) or '<div class="sub">Belum ada aktivitas.</div>'
        st.markdown(f'<div class="panel"><h4>Aktivitas terbaru</h4><div class="sub">Dibaca dari event kontrak</div>{feed}</div>', unsafe_allow_html=True)
    st.write("")
    with st.expander("Detail teknis (alamat blockchain)"):
        st.markdown(f'<div class="addr">Kontrak: {contract.address}<br>Admin: {ADMIN}</div>', unsafe_allow_html=True)

# ═══ 2. PROGRAM DONASI + DETAIL ═══
with t_prog:
    st.markdown('<div class="sec">Program donasi</div><div class="sec-sub">Semua kampanye yang tercatat di smart contract.</div>', unsafe_allow_html=True)
    if not campaigns:
        st.info("Belum ada kampanye. Admin dapat membuatnya di tab Kelola.")
    else:
        flt = st.multiselect("Tampilkan status", svc.STATUS_ID, default=svc.STATUS_ID)
        shown = [c for c in campaigns if svc.STATUS_ID[c["status"]] in flt]
        cols = st.columns(2, gap="medium")
        for i, c in enumerate(shown):
            cols[i % 2].markdown(campaign_card(c), unsafe_allow_html=True)
        if not shown:
            st.info("Tidak ada kampanye dengan status itu.")
        st.markdown('<div class="sec" style="margin-top:14px">Detail kampanye</div>', unsafe_allow_html=True)
        sel = st.selectbox("Pilih kampanye", [c["id"] for c in campaigns], key="detail_id", format_func=lambda i: by_id[i]["title"])
        c = by_id[sel]
        d1, d2, d3 = st.columns(3)
        d1.metric("Target", rp(c["target"]))
        d2.metric("Terkumpul", rp(c["raised"]))
        d3.metric("Saldo tersedia", rp(c["available"]))
        st.write("")
        st.markdown(f'<div class="panel" style="height:auto">Penerima dana: <b>{esc(nm(c["creator"]))}</b>'
                    f'<div class="addr">{esc(c["creator"])}</div>'
                    f'Batas waktu: <b>{svc.fmt_time(c["deadline"])} WIB</b> · '
                    f'Status: <span class="chip {svc.STATUS_CLASS[c["status"]]}">{svc.STATUS_ID[c["status"]]}</span></div>', unsafe_allow_html=True)
        st.write("")
        st.markdown("**Donasi pada kampanye ini**")
        crec = [r for r in receipts if r["campaign_id"] == sel]
        if crec:
            st.dataframe([{"NFT": r["token_id"], "Donatur": nm(r["donor"]), "Alamat wallet": r["donor"],
                           "Jumlah": rp(r["amount"]), "Waktu": svc.fmt_time(r["minted_at"])} for r in crec],
                         width="stretch", hide_index=True)
        else:
            st.info("Belum ada donasi.")
        st.markdown("**Riwayat transaksi kampanye**")
        ctx = [t for t in txs if t["campaign"] == sel]
        st.markdown("".join(tx_row(t, False) for t in ctx) or '<div class="sec-sub">Belum ada transaksi.</div>', unsafe_allow_html=True)

# ═══ 3. DONASI ═══
PRESETS = {"Rp 50.000": 50_000, "Rp 100.000": 100_000, "Rp 250.000": 250_000, "Rp 500.000": 500_000,
           "Rp 1.000.000": 1_000_000, "Nominal lain": None}
with t_don:
    active = [c for c in campaigns if c["status"] == 1]
    st.markdown('<div class="sec">Berdonasi</div><div class="sec-sub">Donasi dikirim sebagai transaksi. Setelah berhasil, kamu otomatis menerima NFT bukti donasi.</div>', unsafe_allow_html=True)
    if IS_ADMIN:
        st.warning("Kamu masuk sebagai Admin. Kontrak melarang Admin berdonasi. Ganti ke akun Donatur (di MetaMask pilih Account 1 atau 2).")
    if not active:
        st.info("Belum ada kampanye aktif. Admin perlu membuat dan menyetujui kampanye dulu.")
    else:
        with st.form("form_donasi"):
            cid = st.selectbox("Kampanye", [c["id"] for c in active],
                               format_func=lambda i: f"{by_id[i]['title']}  ({rp(by_id[i]['raised'])} dari {rp(by_id[i]['target'])})")
            choice = st.radio("Pilih nominal", list(PRESETS), horizontal=True, index=1)
            custom = st.number_input("Nominal lain (Rp)", min_value=0, value=100_000, step=10_000)
            go = st.form_submit_button("Donasi sekarang", type="primary")
        st.caption(f"Kurs: 1 ETH = {idr(svc.ETH_IDR)}. MetaMask akan menampilkan jumlahnya dalam ETH.")
        if go:
            amount = PRESETS[choice] if PRESETS[choice] else int(custom)
            if amount <= 0:
                st.error("Nominal donasi harus lebih dari 0.")
            else:
                run_tx(contract.functions.donate(cid), svc.idr_to_wei(amount), f"Donasi {idr(amount)} berhasil", "donate")
                st.rerun()

# ═══ 4. KELOLA (ADMIN) ═══
with t_admin:
    if IS_ADMIN:
        st.success("Kamu masuk sebagai Admin.")
    else:
        st.warning("Akun aktif bukan Admin. Aksi di bawah tetap bisa dicoba, tetapi smart contract akan menolaknya.")
    st.markdown('<div class="sec" style="font-size:20px">Buat kampanye</div>', unsafe_allow_html=True)
    with st.form("form_buat"):
        title = st.text_input("Judul kampanye")
        c1, c2 = st.columns(2)
        target = c1.number_input("Target dana (Rp)", min_value=0, value=10_000_000, step=1_000_000)
        days = c2.number_input("Durasi (hari)", min_value=0, value=30, step=1)
        go = st.form_submit_button("Buat kampanye", type="primary")
    if go:
        if not title.strip():
            st.error("Judul tidak boleh kosong.")
        elif target <= 0 or days <= 0:
            st.error("Target dan durasi harus lebih dari 0.")
        else:
            run_tx(contract.functions.createCampaign(title.strip(), svc.idr_to_wei(target), int(days)), 0, "Kampanye dibuat (menunggu verifikasi)")
            st.rerun()

    st.divider()
    st.markdown('<div class="sec" style="font-size:20px">Verifikasi kampanye</div>', unsafe_allow_html=True)
    pend = [c for c in campaigns if c["status"] == 0]
    if not pend:
        st.info("Tidak ada kampanye yang menunggu verifikasi.")
    else:
        pid = st.selectbox("Kampanye menunggu verifikasi", [c["id"] for c in pend], key="verify_id", format_func=lambda i: by_id[i]["title"])
        v1, v2 = st.columns(2)
        if v1.button("Setujui kampanye", type="primary", key="btn_approve", use_container_width=True):
            run_tx(contract.functions.verifyCampaign(pid, True), 0, f"Kampanye “{by_id[pid]['title']}” disetujui")
            st.rerun()
        if v2.button("Tolak kampanye", key="btn_reject", use_container_width=True):
            run_tx(contract.functions.verifyCampaign(pid, False), 0, f"Kampanye “{by_id[pid]['title']}” ditolak")
            st.rerun()

    st.divider()
    st.markdown('<div class="sec" style="font-size:20px">Tarik dana</div>', unsafe_allow_html=True)
    wd = [c for c in campaigns if c["status"] in (1, 2)]
    if not wd:
        st.info("Belum ada kampanye aktif atau ditutup yang bisa ditarik dananya.")
    else:
        with st.form("form_tarik"):
            wid = st.selectbox("Kampanye", [c["id"] for c in wd], format_func=lambda i: f"{by_id[i]['title']}  (tersedia {rp(by_id[i]['available'])})")
            wamt = st.number_input("Jumlah (Rp)", min_value=0, value=100_000, step=50_000)
            purpose = st.text_input("Keterangan penggunaan dana")
            go = st.form_submit_button("Tarik dana", type="primary")
        if go:
            if wamt <= 0:
                st.error("Jumlah harus lebih dari 0.")
            elif not purpose.strip():
                st.error("Keterangan wajib diisi (dicatat permanen di blockchain).")
            else:
                w_wei = svc.idr_to_wei(wamt)
                avail_wei = contract.functions.availableBalance(wid).call()
                if 0 < w_wei - avail_wei <= svc.idr_to_wei(2):  # selisih pembulatan rupiah
                    w_wei = avail_wei
                run_tx(contract.functions.withdraw(wid, w_wei, purpose.strip()), 0, f"Penarikan {idr(wamt)} berhasil")
                st.rerun()

    st.divider()
    st.markdown('<div class="sec" style="font-size:20px">Tutup kampanye</div>', unsafe_allow_html=True)
    clo = [c for c in campaigns if c["status"] == 1]
    if not clo:
        st.info("Tidak ada kampanye aktif.")
    else:
        cl = st.selectbox("Kampanye", [c["id"] for c in clo], key="close_id", format_func=lambda i: by_id[i]["title"])
        if st.button("Tutup kampanye", key="btn_close"):
            run_tx(contract.functions.closeCampaign(cl), 0, f"Kampanye “{by_id[cl]['title']}” ditutup")
            st.rerun()

# ═══ 5. NFT ═══
with t_nft:
    st.markdown('<div class="sec">NFT bukti donasi</div><div class="sec-sub">Standar ERC-721. Satu NFT dicetak untuk setiap donasi.</div>', unsafe_allow_html=True)
    if not receipts:
        st.info("Belum ada NFT. NFT dicetak otomatis saat donasi berhasil.")
    else:
        mine = [r["token_id"] for r in receipts if r["owner"] == SIGNER]
        if mine:
            st.success("NFT milik kamu: " + ", ".join(f"#{i}" for i in mine))
        cols = st.columns(3, gap="medium")
        for i, r in enumerate(receipts):
            camp = by_id.get(r["campaign_id"])
            c1, c2, _ = theme_of(camp) if camp else ("#0B6B57", "#4CC9A6", "leaf")
            cols[i % 3].markdown(
                f'<div class="nft" style="--c1:{c1};--c2:{c2}"><div class="nft-top"><span>Bukti Donasi #{r["token_id"]}</span><span>ERC-721</span></div>'
                f'<div class="nft-amt">{rp(r["amount"])}</div><div class="nft-camp">{esc(camp["title"]) if camp else ""}</div>'
                f'<div class="nft-foot">{avatar(nm(r["donor"]))}<div><b>{esc(nm(r["donor"]))}</b><small>{svc.fmt_time(r["minted_at"])} WIB</small></div></div>'
                f'<div class="nft-own">Pemilik saat ini: {esc(nm(r["owner"]))}</div></div>', unsafe_allow_html=True)
        tid = st.selectbox("Lihat riwayat kepemilikan", [r["token_id"] for r in receipts], format_func=lambda i: f"NFT #{i}")
        for h in svc.receipt_history(contract, tid):
            frm = "—" if int(h["from"], 16) == 0 else nm(Web3.to_checksum_address(h["from"]))
            st.markdown(f'<div class="hist"><b>{esc(h["action"])}</b><small>{svc.fmt_time(h["time"])} WIB · dari {esc(frm)} ke {esc(nm(Web3.to_checksum_address(h["to"])))}</small></div>',
                        unsafe_allow_html=True)

# ═══ 6. WALLET & RIWAYAT ═══
with t_wallet:
    st.markdown('<div class="sec">Akun saya</div>', unsafe_allow_html=True)
    w1, w2, w3c = st.columns([2, 1.3, 1], vertical_alignment="center")
    w1.markdown(f'<div class="stat s1" style="display:flex;gap:12px;align-items:center">{avatar(nm(SIGNER))}<div><b style="font-size:20px">{esc(nm(SIGNER))}</b><span>{"Tanda tangan lewat MetaMask" if MM else "Mode demo"}</span></div></div>', unsafe_allow_html=True)
    w2.markdown(f'<div class="stat s2"><b style="font-size:20px">{rp(balance)}</b><span>Saldo</span></div>', unsafe_allow_html=True)
    w3c.markdown(f'<div class="stat s3"><b style="font-size:20px">{"Admin" if IS_ADMIN else "Donatur"}</b><span>Peran</span></div>', unsafe_allow_html=True)
    st.write("")
    st.caption("Alamat wallet akun aktif")
    st.code(SIGNER, language=None)
    with st.form("form_nama"):
        new_name = st.text_input("Nama tampilan", value=nm(SIGNER), help="Nama ini dipakai di seluruh aplikasi menggantikan kode alamat.")
        if st.form_submit_button("Simpan nama"):
            svc.save_name(SIGNER, new_name)
            flash("ok", "Nama tampilan disimpan.")
            st.rerun()
    st.caption(NAME_NOTE)
    if MM:
        if wallet_addr not in NODE_ACCOUNTS:
            st.info("Ini akun MetaMask biasa (bukan akun bawaan Hardhat). Isi saldo uji dulu bila saldonya 0.")
        if st.button("Isi saldo uji (10 ETH)", key="faucet_tab"):
            try:
                svc.faucet(w3, SIGNER, 10)
                flash("ok", f"Saldo uji {rp(10)} ditambahkan ke akun ini.")
            except svc.ServiceError as e:
                flash("err", str(e))
            st.rerun()
    else:
        st.info("MetaMask belum terhubung. Klik Hubungkan MetaMask di kanan atas halaman.")
    with st.expander("Detail teknis (alamat blockchain)"):
        st.markdown(f'<div class="addr">Akun aktif: {SIGNER}<br>Kontrak: {contract.address}<br>Admin: {ADMIN}</div>', unsafe_allow_html=True)
    st.write("")
    st.markdown('<div class="sec" style="font-size:20px">Riwayat donasi</div><div class="sec-sub">Semua donasi dari seluruh kampanye, lengkap dengan alamat wallet donatur.</div>', unsafe_allow_html=True)
    if receipts:
        st.dataframe([{"NFT": r["token_id"],
                       "Kampanye": by_id[r["campaign_id"]]["title"] if r["campaign_id"] in by_id else r["campaign_id"],
                       "Donatur": nm(r["donor"]), "Alamat wallet": r["donor"],
                       "Jumlah": rp(r["amount"]), "Waktu": svc.fmt_time(r["minted_at"])} for r in reversed(receipts)],
                     width="stretch", hide_index=True)
    else:
        st.info("Belum ada donasi.")
    st.write("")
    st.markdown('<div class="sec" style="font-size:20px">Riwayat transaksi</div><div class="sec-sub">Diambil dari event smart contract, terbaru di atas.</div>', unsafe_allow_html=True)
    st.markdown("".join(tx_row(t) for t in txs) or '<div class="sec-sub">Belum ada transaksi.</div>', unsafe_allow_html=True)
    st.button("Muat ulang data")

st.markdown('<div class="ft">AmalKita · data dibaca langsung dari smart contract</div>', unsafe_allow_html=True)