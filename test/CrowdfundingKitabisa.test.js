require("@nomicfoundation/hardhat-chai-matchers"); // revertedWithCustomError, emit
const { expect } = require("chai");
const { ethers } = require("hardhat");

// Status: 0 PENDING, 1 ACTIVE, 2 CLOSED, 3 REJECTED
describe("CrowdfundingKitabisa (admin-only)", function () {
  let contract, admin, donor1, donor2;
  const ONE = ethers.parseEther("1");

  beforeEach(async function () {
    [admin, donor1, donor2] = await ethers.getSigners();
    const Factory = await ethers.getContractFactory("CrowdfundingKitabisa");
    contract = await Factory.deploy();
    await contract.waitForDeployment();
  });

  async function activeCampaign() {
    await contract.createCampaign("Bantu Biaya Operasi", ethers.parseEther("10"), 30);
    await contract.verifyCampaign(1, true);
  }

  it("deployer menjadi admin", async function () {
    expect(await contract.owner()).to.equal(admin.address);
  });

  it("alur berhasil: buat, verifikasi, donasi, tarik, tutup", async function () {
    await contract.createCampaign("Bantu Biaya Operasi", ethers.parseEther("10"), 30);
    expect((await contract.getCampaign(1)).status).to.equal(0n);

    await contract.verifyCampaign(1, true);
    expect((await contract.getCampaign(1)).status).to.equal(1n);

    await contract.connect(donor1).donate(1, { value: ONE });
    expect((await contract.getCampaign(1)).totalRaised).to.equal(ONE);
    expect(await contract.ownerOf(1)).to.equal(donor1.address); // NFT bukti donasi
    expect(await contract.totalReceipts()).to.equal(1n);

    const half = ONE / 2n;
    await expect(contract.withdraw(1, half, "DP biaya operasi"))
      .to.emit(contract, "FundsWithdrawn");
    expect(await contract.availableBalance(1)).to.equal(half);

    await contract.closeCampaign(1);
    expect((await contract.getCampaign(1)).status).to.equal(2n);
  });

  it("kampanye ditolak tidak bisa menerima donasi", async function () {
    await contract.createCampaign("Ditolak", ONE, 7);
    await contract.verifyCampaign(1, false);
    expect((await contract.getCampaign(1)).status).to.equal(3n);
    await expect(contract.connect(donor1).donate(1, { value: ONE }))
      .to.be.revertedWithCustomError(contract, "InvalidStatus");
  });

  describe("pembatasan akses (hanya admin)", function () {
    it("bukan admin tidak bisa createCampaign", async function () {
      await expect(contract.connect(donor1).createCampaign("X", ONE, 7))
        .to.be.revertedWithCustomError(contract, "OnlyOwner");
    });

    it("bukan admin tidak bisa verifyCampaign", async function () {
      await contract.createCampaign("X", ONE, 7);
      await expect(contract.connect(donor1).verifyCampaign(1, true))
        .to.be.revertedWithCustomError(contract, "OnlyOwner");
    });

    it("bukan admin tidak bisa withdraw", async function () {
      await activeCampaign();
      await contract.connect(donor1).donate(1, { value: ONE });
      await expect(contract.connect(donor1).withdraw(1, 100, "coba tarik"))
        .to.be.revertedWithCustomError(contract, "OnlyOwner");
    });

    it("bukan admin tidak bisa closeCampaign", async function () {
      await activeCampaign();
      await expect(contract.connect(donor1).closeCampaign(1))
        .to.be.revertedWithCustomError(contract, "OnlyOwner");
    });

    it("admin tidak boleh berdonasi", async function () {
      await activeCampaign();
      await expect(contract.donate(1, { value: ONE }))
        .to.be.revertedWithCustomError(contract, "OwnerCannotDonate");
    });
  });

  describe("validasi input dan status", function () {
    it("donasi 0 ditolak", async function () {
      await activeCampaign();
      await expect(contract.connect(donor1).donate(1, { value: 0 }))
        .to.be.revertedWithCustomError(contract, "InvalidInput");
    });

    it("donasi ke kampanye PENDING ditolak", async function () {
      await contract.createCampaign("X", ONE, 7);
      await expect(contract.connect(donor1).donate(1, { value: ONE }))
        .to.be.revertedWithCustomError(contract, "InvalidStatus");
    });

    it("donasi ke kampanye yang tidak ada ditolak", async function () {
      await expect(contract.connect(donor1).donate(99, { value: ONE }))
        .to.be.revertedWithCustomError(contract, "CampaignNotFound");
    });

    it("withdraw melebihi saldo ditolak", async function () {
      await activeCampaign();
      await contract.connect(donor1).donate(1, { value: ONE });
      await expect(contract.withdraw(1, ONE * 2n, "terlalu besar"))
        .to.be.revertedWithCustomError(contract, "InsufficientBalance");
    });

    it("withdraw tanpa keterangan ditolak", async function () {
      await activeCampaign();
      await contract.connect(donor1).donate(1, { value: ONE });
      await expect(contract.withdraw(1, 100, ""))
        .to.be.revertedWithCustomError(contract, "InvalidInput");
    });

    it("donasi setelah kampanye CLOSED ditolak", async function () {
      await activeCampaign();
      await contract.closeCampaign(1);
      await expect(contract.connect(donor1).donate(1, { value: ONE }))
        .to.be.revertedWithCustomError(contract, "InvalidStatus");
    });
  });

  describe("NFT bukti donasi", function () {
    it("riwayat MINTED lalu TRANSFERRED tercatat", async function () {
      await activeCampaign();
      await contract.connect(donor1).donate(1, { value: ONE });

      let history = await contract.getReceiptHistory(1);
      expect(history.length).to.equal(1);
      expect(history[0].action).to.equal("MINTED");

      await contract.connect(donor1).transferFrom(donor1.address, donor2.address, 1);
      expect(await contract.ownerOf(1)).to.equal(donor2.address);

      history = await contract.getReceiptHistory(1);
      expect(history.length).to.equal(2);
      expect(history[1].action).to.equal("TRANSFERRED");

      // donor asli tetap tersimpan di data bukti donasi
      const [data, currentOwner] = await contract.getReceipt(1);
      expect(data.donor).to.equal(donor1.address);
      expect(currentOwner).to.equal(donor2.address);
    });
  });
});
