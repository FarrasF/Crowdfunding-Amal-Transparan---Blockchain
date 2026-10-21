// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/utils/Strings.sol";
import "@openzeppelin/contracts/utils/Base64.sol";

/// @title CrowdfundingKitabisa - Penggalangan dana transparan (model donasi)
/// @notice Alur: Penggalang membuat kampanye (PENDING) -> Admin memverifikasi
///         (ACTIVE / REJECTED) -> Donatur berdonasi -> Penggalang menarik dana
///         bertahap disertai keterangan -> Penggalang menutup kampanye (CLOSED).
///         Modul 6: setiap donasi menghasilkan NFT (ERC-721) sebagai bukti donasi.
contract CrowdfundingKitabisa is ERC721URIStorage {
    // ---------------------------------------------------------------
    // 1. ENUM & STRUCT
    // ---------------------------------------------------------------
    enum Status {
        PENDING,   // menunggu verifikasi admin
        ACTIVE,    // terverifikasi, menerima donasi
        CLOSED,    // ditutup oleh penggalang
        REJECTED   // ditolak admin
    }

    struct Campaign {
        uint256 id;
        address creator;
        string title;
        uint256 target;         // patokan saja, bukan syarat pencairan
        uint256 deadline;       // batas akhir penerimaan donasi
        uint256 totalRaised;    // total donasi masuk (wei)
        uint256 totalWithdrawn; // total dana yang sudah ditarik (wei)
        Status status;
    }

    // ---------------------------------------------------------------
    // 2. STATE VARIABLES
    // ---------------------------------------------------------------
    address public owner; // admin tunggal (verifikator)
    uint256 private nextCampaignId = 1;

    mapping(uint256 => Campaign) public campaigns;

    // id kampanye => donatur => total donasinya
    mapping(uint256 => mapping(address => uint256)) public donations;

    // ---- Tokenisasi (ERC-721): NFT bukti donasi ----
    uint256 private nextTokenId = 1;

    // Data yang dihubungkan ke setiap NFT (padanan CoffeeBatch di modul)
    struct DonationReceipt {
        uint256 tokenId;
        uint256 campaignId;
        address donor;
        uint256 amount;   // wei
        uint256 mintedAt;
    }

    // Token ID -> data bukti donasi
    mapping(uint256 => DonationReceipt) public receipts;

    // Riwayat tiap NFT (padanan History di modul): dicatat otomatis
    // saat NFT dicetak dan setiap kali berpindah pemilik
    struct History {
        string action;      // "MINTED" atau "TRANSFERRED"
        address from;
        address to;
        uint256 timestamp;
    }

    // Token ID -> Riwayat
    mapping(uint256 => History[]) private histories;

    // ---------------------------------------------------------------
    // 3. CUSTOM ERRORS
    // ---------------------------------------------------------------
    error OnlyOwner();
    error OnlyCreator();
    error CampaignNotFound(uint256 id);
    error InvalidInput();
    error InvalidStatus(Status current);
    error CampaignExpired();
    error InsufficientBalance(uint256 requested, uint256 available);
    error TransferFailed();
    error ReceiptNotFound(uint256 tokenId);

    // ---------------------------------------------------------------
    // 4. EVENTS (sumber riwayat & transparansi)
    // ---------------------------------------------------------------
    event CampaignCreated(
        uint256 indexed id,
        address indexed creator,
        uint256 target,
        uint256 deadline
    );
    event CampaignVerified(
        uint256 indexed id,
        Status status,
        address indexed admin
    );
    event DonationReceived(
        uint256 indexed id,
        address indexed donor,
        uint256 amount
    );
    event FundsWithdrawn(
        uint256 indexed id,
        address indexed creator,
        uint256 amount,
        string purpose
    );
    event CampaignClosed(uint256 indexed id, address indexed creator);
    event ReceiptMinted(
        uint256 indexed tokenId,
        uint256 indexed campaignId,
        address indexed donor,
        uint256 amount
    );

    // ---------------------------------------------------------------
    // 5. CONSTRUCTOR & MODIFIERS
    // ---------------------------------------------------------------
    constructor() ERC721("Kitabisa Donation Receipt", "KDR") {
        owner = msg.sender;
    }

    modifier onlyOwner() {
        if (msg.sender != owner) revert OnlyOwner();
        _;
    }

    modifier campaignExists(uint256 _id) {
        if (campaigns[_id].id == 0) revert CampaignNotFound(_id);
        _;
    }

    // ---------------------------------------------------------------
    // 6. FUNGSI
    // ---------------------------------------------------------------

    /// @notice 1. Penggalang membuat kampanye baru (status PENDING)
    function createCampaign(
        string calldata _title,
        uint256 _target,
        uint256 _durationInDays
    ) external returns (uint256) {
        if (bytes(_title).length == 0 || _target == 0 || _durationInDays == 0) {
            revert InvalidInput();
        }

        uint256 id = nextCampaignId;
        uint256 deadline = block.timestamp + (_durationInDays * 1 days);

        campaigns[id] = Campaign({
            id: id,
            creator: msg.sender,
            title: _title,
            target: _target,
            deadline: deadline,
            totalRaised: 0,
            totalWithdrawn: 0,
            status: Status.PENDING
        });

        nextCampaignId++;

        emit CampaignCreated(id, msg.sender, _target, deadline);
        return id;
    }

    /// @notice 2. Admin menyetujui atau menolak kampanye
    function verifyCampaign(uint256 _id, bool _approved)
        external
        onlyOwner
        campaignExists(_id)
    {
        Campaign storage c = campaigns[_id];

        if (c.status != Status.PENDING) revert InvalidStatus(c.status);

        c.status = _approved ? Status.ACTIVE : Status.REJECTED;

        emit CampaignVerified(_id, c.status, msg.sender);
    }

    /// @notice 3. Donatur berdonasi (kirim ETH bersama transaksi)
    function donate(uint256 _id) external payable campaignExists(_id) {
        Campaign storage c = campaigns[_id];

        if (c.status != Status.ACTIVE) revert InvalidStatus(c.status);
        if (block.timestamp >= c.deadline) revert CampaignExpired();
        if (msg.value == 0) revert InvalidInput();

        c.totalRaised += msg.value;
        donations[_id][msg.sender] += msg.value;

        emit DonationReceived(_id, msg.sender, msg.value);

        // Modul 6: cetak NFT bukti donasi (setelah state diubah, mint terakhir)
        _mintReceipt(_id, msg.sender, msg.value);
    }

    /// @notice 4. Penggalang menarik dana (bertahap) dengan keterangan penggunaan
    function withdraw(
        uint256 _id,
        uint256 _amount,
        string calldata _purpose
    ) external campaignExists(_id) {
        Campaign storage c = campaigns[_id];

        if (msg.sender != c.creator) revert OnlyCreator();
        if (c.status != Status.ACTIVE && c.status != Status.CLOSED) {
            revert InvalidStatus(c.status);
        }
        if (_amount == 0 || bytes(_purpose).length == 0) revert InvalidInput();

        uint256 available = c.totalRaised - c.totalWithdrawn;
        if (_amount > available) revert InsufficientBalance(_amount, available);

        // EFFECTS dulu (cegah reentrancy), kirim ETH paling akhir
        c.totalWithdrawn += _amount;

        (bool ok, ) = payable(c.creator).call{value: _amount}("");
        if (!ok) revert TransferFailed();

        emit FundsWithdrawn(_id, msg.sender, _amount, _purpose);
    }

    /// @notice 5. Penggalang menutup kampanye (berhenti menerima donasi)
    function closeCampaign(uint256 _id) external campaignExists(_id) {
        Campaign storage c = campaigns[_id];

        if (msg.sender != c.creator) revert OnlyCreator();
        if (c.status != Status.ACTIVE) revert InvalidStatus(c.status);

        c.status = Status.CLOSED;

        emit CampaignClosed(_id, msg.sender);
    }

    // ---------------------------------------------------------------
    // 7. FUNGSI VIEW (6. Melihat data)
    // ---------------------------------------------------------------

    function getCampaign(uint256 _id)
        external
        view
        campaignExists(_id)
        returns (Campaign memory)
    {
        return campaigns[_id];
    }

    /// @notice Saldo yang masih bisa ditarik penggalang
    function availableBalance(uint256 _id)
        external
        view
        campaignExists(_id)
        returns (uint256)
    {
        Campaign storage c = campaigns[_id];
        return c.totalRaised - c.totalWithdrawn;
    }

    function totalCampaigns() external view returns (uint256) {
        return nextCampaignId - 1;
    }

    // ---------------------------------------------------------------
    // 8. TOKENISASI ERC-721 (Modul 6)
    // ---------------------------------------------------------------

    /// @dev Mint NFT (modul langkah 5). internal: tidak bisa dipanggil
    ///      orang luar, jadi tidak ada yang bisa mencetak NFT sembarangan.
    function mint(
        address to,
        uint256 tokenId,
        string memory metadataURI
    ) internal {
        // Membuat NFT
        _safeMint(to, tokenId);

        // Menyimpan metadata NFT
        _setTokenURI(tokenId, metadataURI);
    }

    /// @dev Dipanggil dari donate() (modul langkah 8: integrasi mint).
    function _mintReceipt(
        uint256 _campaignId,
        address _donor,
        uint256 _amount
    ) internal returns (uint256) {
        uint256 tokenId = nextTokenId;
        nextTokenId++;

        // Hubungkan NFT dengan data project
        receipts[tokenId] = DonationReceipt({
            tokenId: tokenId,
            campaignId: _campaignId,
            donor: _donor,
            amount: _amount,
            mintedAt: block.timestamp
        });

        // Membuat NFT + menyimpan metadata
        mint(
            _donor,
            tokenId,
            _buildTokenURI(tokenId, _campaignId, _donor, _amount)
        );

        emit ReceiptMinted(tokenId, _campaignId, _donor, _amount);
        return tokenId;
    }

    /// @dev Metadata NFT dibuat langsung di blockchain (JSON base64),
    ///      jadi tidak butuh IPFS atau server luar.
    function _buildTokenURI(
        uint256 _tokenId,
        uint256 _campaignId,
        address _donor,
        uint256 _amount
    ) internal pure returns (string memory) {
        string memory json = string.concat(
            '{"name":"Bukti Donasi #', Strings.toString(_tokenId),
            '","description":"Bukti donasi di CrowdfundingKitabisa",',
            '"attributes":[',
            '{"trait_type":"Kampanye","value":', Strings.toString(_campaignId), '},',
            '{"trait_type":"Donatur","value":"', Strings.toHexString(_donor), '"},',
            '{"trait_type":"Jumlah (wei)","value":"', Strings.toString(_amount), '"}]}'
        );
        return string.concat(
            "data:application/json;base64,",
            Base64.encode(bytes(json))
        );
    }

    /// @notice Cek pemilik NFT bukti donasi (padanan getBatchOwner di modul)
    function getReceiptOwner(uint256 _tokenId) public view returns (address) {
        address tokenOwner = _ownerOf(_tokenId);
        if (tokenOwner == address(0)) revert ReceiptNotFound(_tokenId);
        return tokenOwner;
    }

    /// @notice Data bukti donasi + pemilik NFT saat ini
    function getReceipt(uint256 _tokenId)
        external
        view
        returns (DonationReceipt memory data, address currentOwner)
    {
        currentOwner = getReceiptOwner(_tokenId);
        data = receipts[_tokenId];
    }

    /// @notice Riwayat NFT: kapan dicetak dan ke siapa saja berpindah
    function getReceiptHistory(uint256 _tokenId)
        external
        view
        returns (History[] memory)
    {
        getReceiptOwner(_tokenId); // pastikan NFT ada
        return histories[_tokenId];
    }

    /// @dev Dipanggil ERC-721 setiap kali NFT dicetak atau berpindah
    ///      tangan, jadi riwayat selalu tercatat tanpa bisa dilewati.
    function _update(address to, uint256 tokenId, address auth)
        internal
        override
        returns (address from)
    {
        from = super._update(to, tokenId, auth);
        histories[tokenId].push(
            History({
                action: from == address(0) ? "MINTED" : "TRANSFERRED",
                from: from,
                to: to,
                timestamp: block.timestamp
            })
        );
    }

    function totalReceipts() external view returns (uint256) {
        return nextTokenId - 1;
    }
}
