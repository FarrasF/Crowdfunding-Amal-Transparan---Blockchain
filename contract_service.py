"""Lapisan web3.py: semua komunikasi dengan smart contract CrowdfundingKitabisa."""
import json
import hashlib
from decimal import Decimal, ROUND_FLOOR
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

from eth_abi import decode as abi_decode
from web3 import Web3
from web3.exceptions import ContractCustomError, ContractLogicError, Web3RPCError

RPC_URL = "http://127.0.0.1:8545"
PROJECT_DIR = Path(__file__).parent
DEPLOYMENT_PATH = PROJECT_DIR / "deployment.json"
ARTIFACT_PATH = (PROJECT_DIR / "artifacts" / "contracts" / "CrowdfundingKitabisa.sol"
                 / "CrowdfundingKitabisa.json")

STATUS_LABEL = ["PENDING", "ACTIVE", "CLOSED", "REJECTED"]
STATUS_ID = ["Menunggu verifikasi", "Aktif", "Ditutup", "Ditolak"]
STATUS_CLASS = ["st-pending", "st-active", "st-closed", "st-rejected"]

# Pesan ramah untuk custom error di smart contract
ERROR_MESSAGES = {
    "OnlyOwner": "Ditolak: fungsi ini hanya boleh dijalankan oleh Admin.",
    "OwnerCannotDonate": "Ditolak: Admin tidak boleh berdonasi.",
    "CampaignNotFound": "Kampanye #{id} tidak ditemukan.",
    "InvalidInput": "Input tidak valid (judul kosong, nilai 0, atau keterangan kosong).",
    "InvalidStatus": "Status kampanye saat ini ({current}) tidak mengizinkan aksi ini.",
    "CampaignExpired": "Kampanye sudah melewati batas waktu.",
    "InsufficientBalance": "Saldo kampanye tidak cukup (diminta {requested_eth}, tersedia {available_eth}).",
    "TransferFailed": "Transfer ETH gagal.",
    "ReceiptNotFound": "NFT bukti donasi #{tokenId} tidak ditemukan.",
}


class ServiceError(Exception):
    """Kesalahan yang aman ditampilkan langsung ke pengguna."""


def get_w3() -> Web3:
    return Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={"timeout": 10}))


def load_contract(w3: Web3):
    if not w3.is_connected():
        raise ServiceError("Tidak dapat terhubung ke Hardhat Network. Jalankan: npx hardhat node")
    if not DEPLOYMENT_PATH.exists():
        raise ServiceError("File deployment.json tidak ditemukan. Deploy kontrak dulu.")
    if not ARTIFACT_PATH.exists():
        raise ServiceError("Artifact kontrak tidak ditemukan. Jalankan: npx hardhat compile")
    address = Web3.to_checksum_address(json.loads(DEPLOYMENT_PATH.read_text())["address"])
    if len(w3.eth.get_code(address)) == 0:
        raise ServiceError("Kontrak tidak ditemukan di node ini (node di-restart?). Deploy ulang.")
    abi = json.loads(ARTIFACT_PATH.read_text())["abi"]
    return w3.eth.contract(address=address, abi=abi)


def eth(w3: Web3, wei: int) -> float:
    return float(w3.from_wei(wei, "ether"))


def short(addr: str) -> str:
    return f"{addr[:6]}…{addr[-4:]}"


try:
    _TZ = ZoneInfo("Asia/Jakarta")
except Exception:  # noqa: BLE001  (tzdata tidak terpasang)
    _TZ = None


def fmt_time(ts: int) -> str:
    return datetime.fromtimestamp(ts, _TZ).strftime("%d %b %Y %H:%M")


def days_left(deadline: int) -> int:
    return max(0, -(-(deadline - int(time.time())) // 86400))


# ---------- decode error ----------
def _error_table(contract):
    table = {}
    for item in contract.abi:
        if item.get("type") == "error":
            types = [i["type"] for i in item["inputs"]]
            sig = f'{item["name"]}({",".join(types)})'
            sel = Web3.keccak(text=sig)[:4].hex().removeprefix("0x")
            table[sel] = (item["name"], item["inputs"])
    return table


def explain_error(w3, contract, exc: Exception) -> str:
    data = None
    if isinstance(exc, ContractCustomError):
        data = exc.args[0] if exc.args else None
    else:
        data = getattr(exc, "data", None)
        if isinstance(data, dict):
            data = data.get("data")
        if not data:
            for a in exc.args:
                if isinstance(a, dict) and a.get("data"):
                    data = a["data"]
                elif isinstance(a, dict) and isinstance(a.get("data"), dict):
                    data = a["data"].get("data")
        if not data and getattr(exc, "rpc_response", None):
            data = (exc.rpc_response.get("error") or {}).get("data")
    if isinstance(data, str) and data.startswith("0x") and len(data) >= 10:
        raw = data.removeprefix("0x")
        entry = _error_table(contract).get(raw[:8])
        if entry:
            name, inputs = entry
            vals = {}
            if inputs:
                decoded = abi_decode([i["type"] for i in inputs], bytes.fromhex(raw[8:]))
                vals = {i["name"]: v for i, v in zip(inputs, decoded)}
            if "current" in vals:
                vals["current"] = STATUS_LABEL[vals["current"]]
            if "requested" in vals:
                vals["requested_eth"] = rupiah(eth(w3, vals["requested"]))
                vals["available_eth"] = rupiah(eth(w3, vals["available"]))
            return ERROR_MESSAGES.get(name, name).format(**vals)
    return f"Transaksi ditolak: {exc}"


# ---------- baca data ----------
def parse_campaign(w3, c):
    return {
        "id": c[0], "creator": c[1], "title": c[2],
        "target": eth(w3, c[3]), "deadline": c[4],
        "raised": eth(w3, c[5]), "withdrawn": eth(w3, c[6]),
        "status": c[7], "status_label": STATUS_LABEL[c[7]],
    }


def list_campaigns(w3, contract):
    n = contract.functions.totalCampaigns().call()
    out = []
    for i in range(1, n + 1):
        c = parse_campaign(w3, contract.functions.getCampaign(i).call())
        c["available"] = eth(w3, contract.functions.availableBalance(i).call())
        out.append(c)
    return out


def list_receipts(w3, contract):
    n = contract.functions.totalReceipts().call()
    out = []
    for t in range(1, n + 1):
        d, owner = contract.functions.getReceipt(t).call()
        out.append({"token_id": d[0], "campaign_id": d[1], "donor": d[2],
                    "amount": eth(w3, d[3]), "minted_at": d[4], "owner": owner})
    return out


def receipt_history(contract, token_id):
    return [{"action": h[0], "from": h[1], "to": h[2], "time": h[3]}
            for h in contract.functions.getReceiptHistory(token_id).call()]


def list_transactions(w3, contract):
    """Riwayat transaksi dari event log kontrak (terbaru di atas)."""
    ev = contract.events
    specs = [("Kampanye dibuat", ev.CampaignCreated), ("Verifikasi", ev.CampaignVerified),
             ("Donasi", ev.DonationReceived), ("Penarikan dana", ev.FundsWithdrawn),
             ("Kampanye ditutup", ev.CampaignClosed)]
    rows = []
    admin = contract.functions.owner().call()
    names = load_names()
    for label, event in specs:
        for log in event.get_logs(from_block=0):
            a = log["args"]
            if label == "Donasi":
                detail = f"{who(a['donor'], admin, names)} berdonasi {rupiah(eth(w3, a['amount']))}"
            elif label == "Penarikan dana":
                detail = f"Admin menarik {rupiah(eth(w3, a['amount']))}. Keterangan: {a['purpose']}"
            elif label == "Verifikasi":
                detail = "Disetujui (ACTIVE)" if a["status"] == 1 else "Ditolak (REJECTED)"
            elif label == "Kampanye dibuat":
                detail = f"Target {rupiah(eth(w3, a['target']))}"
            else:
                detail = "Kampanye ditutup"
            rows.append({"block": log["blockNumber"], "idx": log["logIndex"], "label": label,
                         "campaign": a["id"], "detail": detail, "tx": log["transactionHash"].hex()})
    rows.sort(key=lambda r: (r["block"], r["idx"]), reverse=True)
    return rows


# ---------- kirim transaksi ----------
def send(w3, contract, fn, sender: str, value_wei: int = 0):
    """Kirim transaksi dari akun node Hardhat (unlocked). Mengembalikan receipt."""
    try:
        tx_hash = fn.transact({"from": sender, "value": value_wei})
        return w3.eth.wait_for_transaction_receipt(tx_hash, timeout=30)
    except ServiceError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise ServiceError(explain_error(w3, contract, exc)) from exc


# ---------- transaksi lewat MetaMask ----------
def preflight(w3, contract, fn, sender: str, value_wei: int = 0):
    """Simulasikan transaksi (eth_call) sebelum MetaMask dibuka.
    Jika kontrak menolak, kembalikan pesan ramah; jika lolos, kembalikan None."""
    if value_wei and w3.eth.get_balance(sender) < value_wei:
        return "Saldo akun tidak cukup untuk jumlah ini. Isi saldo uji di tab Wallet."
    try:
        fn.call({"from": sender, "value": value_wei})
        return None
    except Exception as exc:  # noqa: BLE001
        return explain_error(w3, contract, exc)


def tx_request(fn, sender: str, to: str, value_wei: int = 0) -> dict:
    """Parameter eth_sendTransaction yang akan ditandatangani di MetaMask."""
    return {"from": sender, "to": to, "data": fn._encode_transaction_data(),
            "value": hex(value_wei)}


def confirm(w3, contract, tx_hash: str):
    """Tunggu transaksi yang sudah ditandatangani di MetaMask; kembalikan receipt."""
    try:
        r = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=45)
    except Exception as exc:  # noqa: BLE001
        raise ServiceError(f"Transaksi belum terkonfirmasi: {exc}") from exc
    if r["status"] != 1:
        raise ServiceError("Transaksi dibatalkan oleh blockchain (reverted).")
    return r


def faucet(w3, address: str, amount_eth: int = 10) -> None:
    """Isi saldo akun uji di node Hardhat lokal (hardhat_setBalance)."""
    res = w3.provider.make_request("hardhat_setBalance", [address, hex(int(w3.to_wei(amount_eth, "ether")))])
    if "error" in res:
        raise ServiceError(f"Faucet gagal: {res['error'].get('message', res['error'])}")


# ---------- rupiah ----------
ETH_IDR = 30_298_898  # kurs tetap: 1 ETH = Rp 30.298.898


def rupiah(eth_amount: float) -> str:
    return "Rp " + f"{int(round(eth_amount * ETH_IDR)):,}".replace(",", ".")


def idr_to_wei(idr) -> int:
    """Rupiah -> wei (dibulatkan ke bawah)."""
    return int((Decimal(str(idr)) / Decimal(ETH_IDR) * Decimal(10) ** 18).to_integral_value(ROUND_FLOOR))


def idr_floor(eth_amount: float) -> int:
    return int(eth_amount * ETH_IDR)


# ---------- nama pengguna (alamat -> nama) ----------
NAMES_PATH = PROJECT_DIR / "names.json"
_FIRST = ["Budi", "Siti", "Agus", "Dewi", "Rizky", "Putri", "Andi", "Wulan", "Fajar", "Maya",
          "Hendra", "Nurul", "Dimas", "Sekar", "Rudi", "Citra", "Bayu", "Anisa", "Eko", "Laras"]
_LAST = ["Santoso", "Rahayu", "Wijaya", "Lestari", "Pratama", "Hidayat", "Kusuma", "Saputra",
         "Permata", "Nugroho", "Maharani", "Setiawan"]


def load_names() -> dict:
    try:
        return json.loads(NAMES_PATH.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def save_name(address: str, name: str) -> None:
    names = load_names()
    if name.strip():
        names[address.lower()] = name.strip()
    else:
        names.pop(address.lower(), None)
    NAMES_PATH.write_text(json.dumps(names, ensure_ascii=False, indent=2), encoding="utf-8")


def who(address: str, admin: str, names: dict | None = None) -> str:
    """Nama tampilan untuk sebuah alamat: nama buatan pengguna, 'Admin AmalKita', atau nama otomatis."""
    names = load_names() if names is None else names
    if address.lower() in names:
        return names[address.lower()]
    if address.lower() == admin.lower():
        return "Admin AmalKita"
    h = int(hashlib.sha256(address.lower().encode()).hexdigest(), 16)
    return f"{_FIRST[h % len(_FIRST)]} {_LAST[(h >> 8) % len(_LAST)]}"