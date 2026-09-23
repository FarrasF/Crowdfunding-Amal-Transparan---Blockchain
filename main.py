from block import Block
from pow import proof_of_work
from pos import proof_of_stake


# Proof of Work
print("=" * 60)
print("PROOF OF WORK - Sistem Crowdfunding & Amal Transparan")
print("=" * 60)

# Data block: transaksi donasi (tema project crowdfunding amal)
data_block = {
    "Aktor": "Donatur (Budi)",
    "Aksi": "Kirim Donasi",
    "Nominal": "Rp 50.000.000",
    "Keterangan": "Transfer ke rekening kampanye"
}

hasil_pow = []

for difficulty in [2, 3, 4, 5]:

    block = Block(
        index=1,
        data=data_block,
        previous_hash="0"
    )

    print(f"\nData Block      : {block.data}")
    print(f"Difficulty      : {difficulty}")

    waktu = proof_of_work(block, difficulty)

    print(f"Hash            : {block.hash}")

    hasil_pow.append((difficulty, block.nonce, waktu, block.hash))

# Tabel ringkasan untuk laporan (Soal 1)
print("\n\n" + "=" * 90)
print("TABEL HASIL EKSPERIMEN PoW (untuk laporan)")
print("=" * 90)
print(f"{'Difficulty':<12}{'Nonce':<12}{'Waktu (s)':<15}{'Hash'}")
print("-" * 90)
for difficulty, nonce, waktu, hash_result in hasil_pow:
    print(f"{difficulty:<12}{nonce:<12}{waktu:<15.4f}{hash_result}")


# Proof of Stake 
print("\n\n" + "=" * 60)
print("PROOF OF STAKE - Validator Jaringan Crowdfunding Amal")
print("=" * 60)

# Validator disesuaikan dengan aktor pada project crowdfunding amal
# (pihak yang memvalidasi/mencatat setiap transaksi dana)

# Percobaan 1: stake awal
validators_awal = {
    "Yayasan Amal": 10,
    "Vendor Toko": 20,
    "Auditor Independen": 30,
    "Perwakilan Donatur": 40
}

# Percobaan 2: stake diubah
validators_ubah = {
    "Yayasan Amal": 70,
    "Vendor Toko": 10,
    "Auditor Independen": 10,
    "Perwakilan Donatur": 10
}


def simulasi_pos(validators, jumlah_simulasi=20):
    hasil = {nama: 0 for nama in validators}

    for _ in range(jumlah_simulasi):
        terpilih = proof_of_stake(validators)
        hasil[terpilih] += 1

    return hasil


for label, validators in [
    ("PERCOBAAN 1 (stake relatif merata)", validators_awal),
    ("PERCOBAAN 2 (stake diubah, satu validator dominan)", validators_ubah)
]:
    print(f"\n--- {label} ---")
    print("Validator:")
    for validator, stake in validators.items():
        print(f"  - {validator}: {stake} stake")

    hasil = simulasi_pos(validators, jumlah_simulasi=20)

    print("\nHasil 20x simulasi (jumlah terpilih):")
    for validator, jumlah in hasil.items():
        persen = (jumlah / 20) * 100
        print(f"  - {validator:<22}: {jumlah:>2}x terpilih ({persen:.0f}%)")