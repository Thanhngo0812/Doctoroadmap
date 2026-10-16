# D-04d — Đo các luật giữ cứng cạnh ngược (E8) trên nhãn D-04

**Nguồn chân lý:** [đặc tả D-04](D-04-dac-ta-nhan-canh-nguoc.md), mục "Cách Claude dùng nhãn"; báo cáo vòng 2, mục 8.13.
**Ai:** Claude · **Chi phí mô hình:** 0 USD · **Chặn bởi:** D-04c · **Trạng thái:** xong 2026-10-16 — giữ R17, không soạn vé sửa A10

## Vì sao

Quyết có đổi R17 ở A10 hay không, và đổi theo luật nào, bằng độ chính xác đo trực tiếp trên từng cạnh ngược, thay cho các chỉ số gián tiếp của
mục 8.13.

## Cần làm

- **Chất lượng nhãn:**
  - độ tự nhất quán trên phiếu lặp;
  - kappa A–B, theo nhãn và theo nhị phân `can_hoc_truoc`;
  - tỉ lệ `khong_ro`;
  - Claude đọc 40 cặp lệch và 40 cặp đồng thuận, rồi ghi kiểu lỗi.
  - Nếu nhãn lệch có hệ thống thì dừng, báo chủ dự án, sửa hướng dẫn trước khi đo.
- **Đo trên nhãn đồng thuận:** với mỗi luật (`tat`, `cung-chuong`, `pass-chinh` chỉ ở nguồn 1, `tin-chac`, `so_muc_giua` ≤ k), tính:
  - độ chính xác giữ cứng, kèm khoảng Wilson;
  - độ phủ `can_hoc_truoc`;
  - báo theo nguồn, lĩnh vực và hệ.
  - Đo lại trên nhãn từng lượt để xem độ nhạy.
- **Mô hình học**, chỉ khi không luật đơn nào đạt: LightGBM trên đặc trưng cấu trúc, chia theo sách như E5.
- **Phát lại** luật tốt nhất trên ba tài liệu vàng bằng đường phát lại của E8.
- **Phụ phẩm:**
  - tỉ lệ `nghia_khac` và `khong_tien_quyet` trên cạnh ngược của từng hệ;
  - phân bố `kien_thuc_nen`, để dùng cho C8 và vé 17.
- Viết mục báo cáo trong báo cáo vòng 2, cập nhật kế hoạch v4, commit.

## Nghiệm thu

- [x] Tiêu chí soạn vé sửa A10 áp đúng như đặc tả đã chốt trước khi có nhãn. Không chỉnh ngưỡng sau khi thấy số.
- [x] Mọi số tái tạo được bằng một lệnh ghi trong mục "Chạy lại" của báo cáo.
- [x] Báo cáo nêu rõ đây là nhãn bạc, và nêu phán xét: soạn vé sửa A10 theo luật nào, hay giữ R17.
- [x] Nếu đạt tiêu chí: soạn vé sửa A10 cho nhân viên, giữ luật mới tắt mặc định cho tới khi đo trên T-01.

## Kết quả (Claude, 2026-10-16)

- Kết quả ở báo cáo vòng 2, mục 8.14. Mã: `scripts/pass-phu-ml/do_luat_d04.py`, có test.
- Không luật nào đạt tiêu chí, ở bất kỳ bộ nhãn hay nhóm nào. Mô hình học cũng không đạt.
- Độ chính xác cao nhất: 0,07 trên nhãn đa số và 0,17 trên A∪B (`pass-chinh`), trong khi ngưỡng là 0,70. Vì vậy không phát lại trên vàng.
- **Phán: giữ R17.** Mục "nếu đạt tiêu chí thì soạn vé" không áp dụng.
- **Phụ phẩm:** 33–48% cạnh ngược là cạnh sai, lẽ ra phải bỏ. Ở E5 chủ yếu là `nghia_khac`, do bộ khớp tên; ở LLM v3 chủ yếu là
  `khong_tien_quyet`. Đề xuất sửa bộ khớp tên của pass phụ.
