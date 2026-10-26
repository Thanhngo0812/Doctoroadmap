# DG-01 — Manifest sách, bốc chương theo seed, kiểm PDF gốc

**Nguồn:** spec mục 4 · **Ai:** Claude (người giữ sổ tập thử) · **Chi phí mô hình:** 0 · **Chặn bởi:** không · **Trạng thái:** ready-for-agent

## Làm được gì

Mỗi cuốn, cả tập phát triển lẫn tập thử, có một **manifest** ghi danh sách chương lấy từ mục lục in. Một lệnh bốc 3 chương tất định theo seed và luật lọc
không nhìn nội dung. Mỗi PDF của tập thử được kiểm là PDF gốc bằng bộ định tuyến đã có; lệnh kiểm chỉ in số.

**Lược đồ manifest `danh-gia-sach-1`** (một JSON mỗi cuốn). Vé 02 và vé 12 dùng lược đồ này ngay, không chờ lệnh bốc:

```json
{
  "schema": "danh-gia-sach-1",
  "ma_sach": "dev-xstk",
  "chu_de": "toan",
  "tap": "phat_trien",
  "pdf_sha256": "…",
  "so_trang": 0,
  "quyen": "da_xac_nhan",
  "chuong": [
    {"ma": "c10", "so": "10", "ten": "…", "trang_dau": 1, "trang_cuoi": 1, "loai": "noi_dung"}
  ],
  "boc": {"seed": 0, "n_trang_toi_thieu": 0, "chuong": ["c10"]}
}
```

- `tap` nhận `phat_trien` hoặc `thu`.
- `loai` nhận `noi_dung`, `mo_dau`, `bai_tap` hoặc `phu_luc`.
- Số trang là trang của tệp PDF, đánh từ 1, không phải số in trên sách.

## Việc

- Viết manifest cho tập phát triển (commit):
  - xstk ch10–13 và doc-1 ch10–12 lấy khoảng chương từ vàng A8 cũ;
  - `nhap-mon-ml` bốc một khoảng chương bằng chính lệnh bốc.
- Lệnh bốc 3 chương: chia các chương thoả luật lọc thành ba phần (đầu, giữa, cuối), mỗi phần bốc một chương theo seed. Kết quả tất định.
- Lệnh kiểm PDF gốc: dùng bộ định tuyến của vé 15, chỉ in số (tỉ lệ trang có lớp chữ, cờ bản quét).
- Manifest tập thử nằm ở sổ người giữ ngoài repo. Repo chỉ giữ hash.

## Tiêu chí

- [ ] Test: cùng seed thì ra cùng 3 chương; chương bị lọc không bao giờ được bốc; sách có ít hơn 3 chương hợp lệ thì báo lỗi rõ.
- [ ] Test allowlist cho lệnh kiểm PDF: có chuỗi bí mật giả trong tên sách, và lệnh không in ra.
- [ ] Manifest tập phát triển qua được validator.
