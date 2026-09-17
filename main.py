from blockchain import Blockchain

# 1. Inisialisasi Blockchain
amal_chain = Blockchain()

# 2. Data Aliran Dana Amal (4 Aktor: Donatur -> Yayasan -> Vendor -> Penerima)
transaksi = [
    {"Aktor": "Donatur (Budi)",    "Aksi": "Kirim Donasi",  "Nominal": "Rp 50.000.000", "Keterangan": "Transfer ke rekening kampanye"},
    {"Aktor": "Yayasan Amal",      "Aksi": "Alokasi Dana",  "Nominal": "Rp 50.000.000", "Keterangan": "Beli material semen & besi ke vendor"},
    {"Aktor": "Vendor Toko",       "Aksi": "Kirim Barang",  "Nominal": "Rp 50.000.000", "Keterangan": "Resi INV-7788: Material dikirim ke lokasi"},
    {"Aktor": "Penerima Manfaat",  "Aksi": "Terima Bantuan","Nominal": "Rp 50.000.000", "Keterangan": "Material 100% diterima warga di lapangan"}
]

# Tambahkan setiap transaksi ke dalam blockchain
for tx in transaksi:
    amal_chain.add_block(tx)

# 3. Tampilkan Riwayat Blockchain
print("\n" + "=" * 65)
print("     SISTEM CROWDFUNDING & AMAL TRANSPARAN BERBASIS BLOCKCHAIN")
print("=" * 65)

for block in amal_chain.chain:
    print(f"\n[BLOK #{block.index}]")
    print(f"  Prev Hash : {block.previous_hash}")
    print(f"  Curr Hash : {block.hash}")
    print(f"  Waktu     : {block.timestamp}")
    print("  Data      :")
    for k, v in block.data.items():
        print(f"    * {k:<12}: {v}")
    print("  " + "-" * 45)

print(f"\nStatus Validitas: {'VALID (100% Aman & Terverifikasi)' if amal_chain.is_valid() else 'TIDAK VALID'}")
print("=" * 65 + "\n")