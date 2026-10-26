# DG-02 — Phiếu G3 trọn vòng: từ phiếu trống tới kho khái niệm chốt

**Nguồn:** spec mục 5 (G3), 6, 7 (luật tự động); kế hoạch mục 6.2 (định nghĩa khái niệm) · **Ai:** Claude viết hướng dẫn gán G3 (chủ dự án duyệt trước
29/10); agent A làm công cụ · **Chi phí mô hình:** 0 · **Chặn bởi:** lược đồ manifest ở DG-01 (đã có trong vé đó) · **Hạn:** 28/10, vì cặp toán gán thử
ngày 29/10 · **Trạng thái:** ready-for-agent

## Làm được gì

Người giữ chạy một lệnh để sinh **phiếu G3** (Excel) cho một cuốn, trên các chương đã bốc trong manifest. Hai sinh viên điền phiếu độc lập. Phiếu về thì:
1. validator kiểm, rồi đọc thành JSON thô;
2. hai bản thô được căn với nhau;
3. sinh **phiếu bất đồng**;
4. phiếu bất đồng điền xong thì chốt thành **kho chốt**, mỗi khái niệm có mã `G-<ma_sach>-<nnn>`;
5. xuất số đếm đồng thuận (a, b, c) theo chương.

## Định dạng

**Phiếu G3:** một sheet mỗi chương. Cột:
- tên khái niệm; tên khác (ngăn bằng `;`);
- trạng thái, chọn trong danh sách: `day_o_day`, `day_qua_vi_du`, `chi_nhac`, `kien_thuc_nen`;
- trang định nghĩa; câu định nghĩa chép nguyên văn;
- không chắc (có/không); ghi chú.

Mỗi dòng có cột mã ẩn. Sheet đầu là hướng dẫn tóm tắt và thông tin người gán (mã ẩn danh).

**JSON `danh-gia-g3-1`:**

```json
{
  "schema": "danh-gia-g3-1",
  "ma_sach": "…",
  "nguoi_gan": "T1-a",
  "phien_ban_huong_dan": "g3-1",
  "khai_niem": [
    {"ma": "…", "chuong": "c10", "ten": "…", "ten_khac": ["…"], "trang_thai": "day_o_day",
     "dinh_nghia": {"trang": 12, "cau": "…"}, "khong_chac": false, "ghi_chu": ""}
  ],
  "tranh_chap": []
}
```

- Ở bản thô, `nguoi_gan` là mã người, `ma` là mã dòng.
- Ở kho chốt, `nguoi_gan` là `hoi-y`, `ma` là `G-<ma_sach>-<nnn>`, và có thêm `tranh_chap`.

**Validator** kiểm:
- cột bắt buộc có đủ;
- giá trị nằm trong danh sách;
- trang nằm trong chương;
- câu định nghĩa khớp mờ được trong văn bản trang đó: chỉ cảnh báo, không chặn;
- không có hai dòng trùng tên trong cùng một chương.

**Căn hai bản thô** dùng luật tự động của spec mục 7: trùng tên hay tên khác sau chuẩn hoá theo ranh giới âm tiết, hoặc cùng câu định nghĩa trên cùng trang.
Cặp còn lại mà gần nhau (chung âm tiết, hay câu định nghĩa cùng trang) được đưa vào phiếu bất đồng dưới dạng câu hỏi "có phải cùng khái niệm không".

**Phiếu bất đồng:** chỉ gồm mục hai người khác nhau, kèm câu trích của mỗi bên. Mỗi người chọn "giữ" hoặc "bỏ" và ghi một dòng lý do. Luật chốt:
- cả hai "giữ" thì vào kho;
- cả hai "bỏ" thì loại;
- còn lại là tranh chấp.

Văn bản trang lấy từ PDF bằng pypdfium2, như bộ đọc nhẹ. Không dùng đầu ra pipeline.

## Phạm vi tệp

Gói `danhgia`: mô-đun phiếu G3, lược đồ G3, chuẩn hoá tên (dùng chung với DG-09), CLI. Test trong `tests/evaluation/`. Fixture là một PDF nhỏ tự sinh, cộng
một phần nhỏ của sách phát triển.

## Tiêu chí nghiệm thu

- [ ] Round-trip: sinh phiếu → điền bằng mã → đọc lại ra đúng dữ liệu.
- [ ] Validator bắt từng loại lỗi bằng một ca riêng.
- [ ] Căn hai bản thô khớp được tên có âm tiết tận cùng "y", như "quy luật" hay "tỷ lệ", với chính nó, kể cả khi tên nằm giữa câu (bài học vòng 2, mục 8.11).
- [ ] Luật chốt ba nhánh: mỗi nhánh một test. Kho chốt có mã ổn định giữa hai lần chạy cùng đầu vào.
- [ ] Số đếm đồng thuận (a, b, c) theo chương đúng trên ví dụ dựng tay.
- [ ] Bảng phá, gồm ít nhất: bỏ chuẩn hoá NFC; so tên không theo ranh giới âm tiết; nhận cả khi một người "giữ"; đánh mã kho theo thứ tự dict.
- [ ] Phiếu mở được bằng Excel, có danh sách chọn. Báo cáo kèm ảnh chụp hoặc mô tả phiếu.

## Ngoài phạm vi

Phiếu G4 (DG-03); căn với đầu ra máy (DG-09); thống kê đồng thuận có CI (DG-05).
