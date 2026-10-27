# DG-09 — Căn khái niệm

**Nguồn:** spec mục 7 · **Ai:** agent A; Claude phán ca tay · **Chi phí:** 0 · **Chặn bởi:** DG-02 (định dạng G3, chuẩn hoá tên), DG-04 (hợp đồng) · **Hạn:**
01/11 · **Trạng thái:** ready-for-agent

## Làm được gì

Từ kho chốt G3, nguồn "ngoài" của G4 và hợp đồng của **mọi hệ** trên một cuốn, công cụ cho ra **bảng căn `danh-gia-can-1`**. Mỗi dòng gồm: khái niệm vàng; node
`<he>:<id>`; quan hệ (`khop`, `may_rong_hon`, `may_hep_hon`, `khong_khop`); nguồn quyết định (`luat_ten`, `luat_cau_neo`, `phan_tay`); mã phán; ghi chú.

Công tắc làm ba việc:
1. **Luật tự động** theo spec mục 7: tên hoặc tên khác trùng sau chuẩn hoá (dùng chung `danhgia/ten.py` của DG-02); câu neo trùng câu định nghĩa cùng trang
   theo ngưỡng khai trước; ký hiệu không dùng để căn.
2. **Phiếu căn tay mù:** gộp node của mọi hệ, gán mã ngẫu nhiên theo seed, không lộ tên hệ. Chỉ đưa vào phiếu cặp có ứng viên gần. Đọc phiếu đã phán về bảng
   căn, kèm nhật ký.
3. **Phiếu kiểm 20%:** lấy mẫu 20% số ca phán tay theo seed. Phiếu không hiện phán của Claude. Đọc lại, tính % đồng ý và κ (gọi DG-05 khi đã có).

## Tiêu chí

- [ ] Ca dựng tay cho từng luật. Có ca tên chữ "y"; có ca ký hiệu (`μ`, `F` khác `f`) không được căn.
- [ ] Phiếu mù: trong tệp phiếu không có chuỗi tên hệ nào. Test tìm các tên hệ trong mọi ô.
- [ ] Mã ngẫu nhiên tất định theo seed. Bảng căn tái lập được từ nhật ký.
- [ ] Mẫu kiểm đúng 20% (làm tròn lên), không lộ phán gốc.
- [ ] Chạy trên vàng gán thử xstk và hợp đồng hệ chính xstk. Báo tỉ lệ căn tự động.
- [ ] Bảng phá, gồm ít nhất: lộ tên hệ qua mã node; căn bằng ký hiệu; lấy mẫu kiểm không theo seed.
