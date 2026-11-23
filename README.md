# CrowdfundingKitabisa

Penggalangan dana transparan berbasis blockchain (Solidity, ERC-721 sebagai bukti donasi),
dijalankan di Hardhat lokal, dihubungkan ke MetaMask, dan ditampilkan lewat Streamlit + web3.py.

## Peran di smart contract
| Peran | Hak akses |
|---|---|
| **Admin (owner)** | Membuat kampanye, memverifikasi, menarik dana, menutup kampanye |
| **Donatur** | Alamat selain admin: berdonasi dan menerima NFT bukti donasi |

Admin = akun yang men-deploy kontrak. Di Hardhat itu **Account #0**
(`0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266`).

## Struktur project
```
contracts/CrowdfundingKitabisa.sol   smart contract
scripts/deploy.js                    deploy + menulis deployment.json
scripts/seed.js                      (opsional) mengisi data contoh
test/CrowdfundingKitabisa.test.js    tes otomatis (15 skenario)
hardhat.config.js                    solc 0.8.28, evm cancun, jaringan localhost
app.py                               aplikasi Streamlit
requirements.txt                     dependensi Python
```

## Prasyarat
Node.js (LTS, mis. v22), npm, dan Python 3.10+.
```
node --version
npm --version
python --version
```

## Cara menjalankan

### 1. Pasang dependensi Node dan compile (sekali di awal)
```
npm install
npx hardhat clean
npx hardhat compile
```

### 2. Terminal 1: jalankan blockchain lokal (JANGAN ditutup)
```
npx hardhat node
```
Setiap node di-restart, blockchain kembali kosong dan kontrak harus di-deploy ulang.

### 3. Terminal 2: deploy
```
npx hardhat run scripts/deploy.js --network localhost
```
Alamat kontrak tersimpan di `deployment.json`.

Opsional, isi data contoh (3 kampanye, 3 donasi, 3 NFT):
```
npx hardhat run scripts/seed.js --network localhost
```

### 4. MetaMask
1. Pasang ekstensi MetaMask di Chrome, lalu login.
2. Tambah jaringan: nama `Hardhat Local`, RPC `http://127.0.0.1:8545`, Chain ID `31337`, simbol `ETH`.
3. Impor akun uji memakai **private key dari terminal Hardhat**:
   - Account #0 untuk peran **Admin**
   - Account #1 atau lainnya untuk peran **Donatur**
4. Pastikan jaringan aktif adalah **Hardhat Local**.

> Private key Hardhat bersifat publik. Pakai hanya di jaringan lokal, dan jangan pernah
> mengimpor private key wallet asli ke aplikasi ini.

### 5. Jalankan aplikasi Streamlit
```
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows (PowerShell):
.venv\Scripts\Activate.ps1

python -m pip install -r requirements.txt
streamlit run app.py
```
Buka alamat yang tampil (biasanya http://localhost:8501), lalu klik **Connect Wallet**.

## Tes otomatis
```
npx hardhat test
```

## Pemecahan masalah
| Gejala | Penyebab / solusi |
|---|---|
| `Tidak dapat terhubung ke Hardhat Network` | Hardhat node belum jalan (langkah 2) |
| `File deployment.json tidak ditemukan` | Belum deploy (langkah 3) |
| `Artifact smart contract tidak ditemukan` | Belum compile (langkah 1) |
| `Kontrak tidak ditemukan di node ini` | Node di-restart, deploy ulang |
| Peringatan "Jaringan MetaMask berbeda" | Pilih jaringan Hardhat Local di MetaMask |
| MetaMask gagal kirim transaksi setelah node di-restart | MetaMask, Pengaturan, Lanjutan, Hapus data tab aktivitas (reset nonce) |
| `running scripts is disabled` (Windows) | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| Compile gagal, instruksi tidak dikenal | `evmVersion` di `hardhat.config.js` harus `cancun` |
