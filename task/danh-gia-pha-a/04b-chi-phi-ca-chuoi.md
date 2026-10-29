# DG-04b — Chi phí trong hợp đồng hệ chính phủ cả chuỗi

**Nguồn:** spec mục 8 (thước chi phí), mục 2 (hợp đồng `chi_phi`); lượt phát triển 29/10 · **Ai:** agent · **Chi phí:** 0 · **Chặn bởi:** DG-04, DG-08b ·
**Hạn:** 01/11 · **Trạng thái:** ready-for-agent

## Vì sao

Lượt phát triển `dev-xstk/chinh-vong-chu` (29/10, đường sản phẩm) có hai số không khớp:
- sổ chi của lượt (`so-chi.json`): **0,484 USD**, khoảng 254 giây;
- khối `chi_phi` của hợp đồng xuất ra: **0,161 USD**, 100 giây.

Hợp đồng chỉ cộng các artifact `graph` (cụm, nhắc, cạnh, kiểm, xếp tầng) và phần đặt tên module của Pha B. Nó bỏ sót:
- `chunks` v2 (gán vai trò);
- `candidates` (A3, 0,17 USD);
- `retrieval` (A3', 0,014 USD);
- `canonical` (A4, 0,13 USD).

Ngoài ra chi của cạnh pass chính (0,152 USD, `graph` v3) lại hiện dưới khoá `graph_v8_stages`, tức là gán nhầm khâu.

Bảng 9 (phút/cuốn, USD/cuốn) và RQ3 đọc `chi_phi` của hợp đồng. Nếu không sửa thì chi phí sản phẩm bị báo thấp khoảng ba lần.

## Làm được gì

- Bộ xuất hệ chính (`danhgia.xuat`, `he_chinh.py`) đi theo chuỗi thượng nguồn của graph được xuất, qua `upstream_version` và các khoá phiên bản trong manifest:
  `graph` → `canonical` → `candidates`, `retrieval` → `chunks` (gồm phiên bản nhãn vai trò) → `parse`. Bộ xuất cộng chi và thời gian của **đúng các artifact
  trong chuỗi đó**, cộng phần Pha B của lượt.
- `chi_phi.theo_khau` có khoá theo khâu của luồng, không theo số phiên bản: `a1_doc`, `a2_vai_tro`, `a3_trich`, `a3_truy_xuat`, `a4_hop_nhat`, `a6_cum`,
  `a7_nhac`, `a8_pass_chinh`, `a8_pass_phu`, `a9_kiem`, `a10_xep_tang`, `dat_ten`.
  - Mỗi khoá có `usd`, `giay_chay`, `giay_cho_embedding`, số lời gọi, token.
  - `tong` là tổng các khâu.
  - Khoá nào không có artifact thì không ghi, chứ không ghi 0.
- Mỗi khoản chi được ghi đúng khâu đã gây ra nó. Tìm hiểu vì sao chi của cạnh pass chính hiện dưới `stages` v8: có thể manifest của bước sau cộng dồn chi của
  bước trước (`cost_summary` tích luỹ). Nếu đúng vậy, đừng cộng hai lần.
- **Bất biến:** với lượt `luot` của hệ chính, `chi_phi.tong.usd` của hợp đồng bằng tổng `usd` của `so-chi.json` trừ các artifact không thuộc chuỗi (ví dụ
  phiên bản `chunks` v1 trước khi gán vai trò, nếu nó không nằm trong chuỗi), sai số dưới 1e-9. Bộ xuất ghi rõ đã loại những artifact nào khỏi tổng.
- Hợp đồng của biến thể dùng lại thượng nguồn (`xao-k`, `pass-phu-llm`, `oracle-a8`, phát lại) vẫn chỉ ghi phần chạy thêm, như quy ước Bảng 11 của DG-17.
  Kiểm cách các biến thể đó đang ghi chi, và giữ đúng quy ước này.

## Tiêu chí

- [ ] Test trên kho fixture có đủ chuỗi (`parse`, `chunks`, `candidates`, `retrieval`, `canonical`, `graph`), mỗi artifact mang `cost_summary` dựng tay:
  - tổng hợp đồng bằng tổng tính tay;
  - mỗi khâu đúng khoá;
  - artifact ngoài chuỗi (phiên bản cũ trong kho) không được cộng.
- [ ] Test trên dữ liệu thật **chỉ đọc**: lượt `C:\Users\ngoco\Desktop\danh-gia-pha-a-luot\phat-trien\dev-xstk\chinh-vong-chu`. Xuất lại hợp đồng vào thư mục tạm
  của bạn, không ghi vào thư mục lượt. Tổng phải khớp `so-chi.json` theo bất biến trên. Nếu đường dẫn không có thì test bỏ qua (skip), như `DANHGIA_KHO_CHUNG`.
- [ ] Bảng phá, tối thiểu:
  - bỏ A3 khỏi chuỗi;
  - cộng artifact ngoài chuỗi;
  - cộng dồn hai lần;
  - ghi khâu theo số phiên bản;
  - khâu không có artifact ghi 0.
