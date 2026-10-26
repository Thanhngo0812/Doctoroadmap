# DG-03 — Phiếu G4 trọn vòng: quan hệ tiên quyết trên kho chốt

**Nguồn:** spec mục 5 (G4), 6, 8 (đồng thuận) · **Ai:** Claude viết hướng dẫn gán G4; agent A làm công cụ · **Chi phí mô hình:** 0 · **Chặn bởi:** DG-02
· **Hạn:** 29/10 · **Trạng thái:** ready-for-agent

## Làm được gì

Từ kho chốt G3, người giữ sinh **phiếu G4** cho một cuốn. Sinh viên ghi quan hệ "phải hiểu nguồn trước khi học đích", chọn từ danh sách, không gõ tên. Hai
bản về thì:
1. đọc, kiểm;
2. sinh phiếu bất đồng;
3. chốt thành **vàng chính**, **vàng hợp**, **vàng giao**;
4. xuất số đếm đồng thuận theo chương.

## Định dạng

**Phiếu G4:** một sheet mỗi chương bốc. Cột:
- đích: chọn từ khái niệm kho chốt của chương đó;
- nguồn: chọn từ toàn bộ kho chốt, hoặc chọn `ngoai` rồi ghi tên và trang định nghĩa;
- loại: `van_ban` hoặc `kien_thuc`;
- trang và câu bằng chứng;
- không chắc; ghi chú.

Mỗi sheet kèm bảng tra kho chốt: mã, tên, tên khác, trang định nghĩa.

**JSON `danh-gia-g4-1`:**

```json
{
  "schema": "danh-gia-g4-1",
  "ma_sach": "…",
  "nguoi_gan": "T1-a",
  "kho_chot_sha256": "…",
  "quan_he": [
    {"dich": "G-…-001", "nguon": "G-…-007", "loai": "van_ban",
     "bang_chung": {"trang": 30, "cau": "…"}, "khong_chac": false, "ghi_chu": ""},
    {"dich": "G-…-002", "nguon": {"ngoai": {"ten": "…", "trang": 4}}, "loai": "van_ban",
     "bang_chung": {"trang": 31, "cau": "…"}, "khong_chac": false, "ghi_chu": ""}
  ]
}
```

Bản chốt có thêm ba danh sách `vang_chinh`, `vang_hop`, `vang_giao`, cùng `tranh_chap`.

**Nguồn "ngoài" của hai người được căn với nhau** bằng tên chuẩn hoá cộng trang, sai lệch tối đa 1 trang. Kho chốt phải khớp `kho_chot_sha256`, nếu không thì
từ chối.

**Đồng thuận:**
- số đếm (a, b, c) theo chương;
- thêm bản có **tín dụng bắc cầu kiểu PREAP**: hai người được coi là đồng ý về X → Z nếu cả hai cùng ghi X → Z, hoặc một người ghi X → Z còn người kia có
  đường X → … → Z;
- tách theo loại `van_ban` và `kien_thuc`.

## Tiêu chí nghiệm thu

- [ ] Round-trip phiếu; validator bắt: đích không thuộc chương, nguồn trùng đích, nguồn "ngoài" thiếu trang, kho chốt lệch hash.
- [ ] Vàng chính, hợp, giao đúng trên ví dụ dựng tay có đủ ba nhánh chốt.
- [ ] Tín dụng bắc cầu đúng trên ví dụ dựng tay. Có ca đường dài 3 cạnh, và có ca chu trình không làm lặp vô hạn.
- [ ] Bảng phá, gồm ít nhất: tính bắc cầu cả theo chiều ngược; gộp `kien_thuc` vào vàng chính; bỏ kiểm hash kho chốt.

## Ngoài phạm vi

Chấm hệ trên G4 (DG-04 dùng định dạng này); PSA có CI (DG-05).
