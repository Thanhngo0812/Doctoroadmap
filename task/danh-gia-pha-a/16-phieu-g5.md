# DG-16 — Phiếu G5 phán mù

**Nguồn:** spec mục 5 (G5), 8 (precision hiệu chỉnh, Likert); VL §7 · **Ai:** agent A · **Chi phí:** 0 · **Chặn bởi:** DG-07, DG-09, DG-11 · **Hạn:** 03/11 ·
**Trạng thái:** ready-for-agent

## Làm được gì

Từ hợp đồng của hệ chính, B1 và B5 trên một cuốn, cùng bảng căn, công cụ sinh ba loại phiếu Excel, mù tên hệ, mã ngẫu nhiên theo seed:
- **(a)** khái niệm máy không căn được: tối đa 60 mục mỗi cuốn, gộp mọi hệ.
- **(b)** cạnh máy ngoài vàng: tối đa 100 mục mỗi hệ mỗi cuốn. Trộn khoảng 10% câu đối chứng là cạnh vàng của chính người phán, và 10% cặp ngẫu nhiên không
  có cạnh.
- **(c)** rubric Likert 7 mức có lời neo cho từng module; so sánh cặp mù hệ chính với B1 và hệ chính với B5, trái phải xáo ngẫu nhiên.

Đọc phiếu về:
- precision hiệu chỉnh: (cạnh khớp vàng + ước lượng cạnh dư đúng) / tổng cạnh máy, có CI Wilson trên mẫu;
- tỉ lệ bác câu đối chứng;
- điểm rubric;
- kết quả so sánh cặp.

## Tiêu chí

- [ ] Không chuỗi tên hệ nào xuất hiện trong phiếu. Test quét mọi ô.
- [ ] Tỉ lệ câu đối chứng đúng; trái phải xáo tất định theo seed.
- [ ] Precision hiệu chỉnh đúng trên ví dụ tính tay, có ca mẫu bị cắt ở 100.
- [ ] Bảng phá, gồm ít nhất: câu đối chứng đánh dấu lộ trong phiếu; không xáo trái phải; tính precision trên mẫu thay vì suy ra tổng.
