// Mengisi data contoh supaya tampilan Streamlit tidak kosong.
// Jalankan SETELAH deploy:
//   npx hardhat run scripts/seed.js --network localhost
const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
  const { ethers } = hre;
  const deployment = JSON.parse(
    fs.readFileSync(path.join(__dirname, "..", "deployment.json"), "utf8")
  );

  // Akun #0 = admin (deployer), akun #1 dan #2 = donatur
  const [admin, donor1, donor2] = await ethers.getSigners();
  const contract = await ethers.getContractAt(
    deployment.contractName,
    deployment.address,
    admin
  );

  console.log("Admin   :", admin.address);
  console.log("Donatur1:", donor1.address);
  console.log("Donatur2:", donor2.address);

  // 1. Admin membuat kampanye (status PENDING)
  await (await contract.createCampaign("Bantu Biaya Operasi", ethers.parseEther("10"), 30)).wait();
  await (await contract.createCampaign("Beasiswa Santri Berprestasi", ethers.parseEther("5"), 60)).wait();
  await (await contract.createCampaign("Kampanye Uji Ditolak", ethers.parseEther("1"), 7)).wait();
  console.log("3 kampanye dibuat (PENDING)");

  // 2. Admin memverifikasi: 1 dan 2 disetujui, 3 ditolak
  await (await contract.verifyCampaign(1, true)).wait();
  await (await contract.verifyCampaign(2, true)).wait();
  await (await contract.verifyCampaign(3, false)).wait();
  console.log("Kampanye 1 dan 2 ACTIVE, kampanye 3 REJECTED");

  // 3. Donatur berdonasi (otomatis mendapat NFT bukti donasi)
  await (await contract.connect(donor1).donate(1, { value: ethers.parseEther("2") })).wait();
  await (await contract.connect(donor2).donate(1, { value: ethers.parseEther("1") })).wait();
  await (await contract.connect(donor1).donate(2, { value: ethers.parseEther("0.5") })).wait();
  console.log("3 donasi masuk, 3 NFT bukti donasi dicetak");

  // 4. Admin menarik sebagian dana kampanye 1 dengan keterangan
  await (await contract.withdraw(1, ethers.parseEther("0.5"), "DP biaya operasi")).wait();
  console.log("Admin menarik 0.5 ETH dari kampanye 1");

  console.log("Seed selesai. Muat ulang halaman Streamlit.");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
