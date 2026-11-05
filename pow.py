import hashlib
import time


def proof_of_work(block, difficulty):

    target = "0" * difficulty

    start_time = time.time()

    block.hash = block.calculate_hash()
    while not block.hash.startswith(target):
        block.nonce += 1
        block.hash = block.calculate_hash()

    end_time = time.time()

    print("\nMining selesai!")
    print("Nonce :", block.nonce)
    print("Waktu :", round(end_time - start_time, 4), "detik")

    return end_time - start_time
