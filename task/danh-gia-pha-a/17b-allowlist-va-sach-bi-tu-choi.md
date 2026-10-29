# DG-17b — Trả nợ cổng allowlist, và dòng số cho sách bị sản phẩm từ chối

**Nguồn:** spec mục 14; giao thức `dang-ky-truoc.md` mục 9 (sách bị từ chối); báo cáo DG-17 · **Ai:** agent · **Chi phí:** 0 · **Chặn bởi:** DG-17, DG-08b ·
**Hạn:** 04/11 · **Trạng thái:** ready-for-agent (giao sau khi DG-08b ghép)

## A. Nợ allowlist

DG-17 dựng cổng `bao_cao.cong` và test phân loại mọi lệnh trong `_LENH`. Còn 12 lệnh chưa có test bí mật, nằm trong danh sách `CHUA_KIEM_BI_MAT`:
`xuat`, `chuyen-vang`, `doi-chieu`, `phieu-g3`, `phieu-g4`, `can-khai-niem`, `phieu-g5`, `b5`, `baseline`, `phat-lai`, `g1g2`, `luot`.

Với mỗi lệnh, làm một trong hai việc:
- **Nhận dữ liệu tập thử:** khi manifest hay đầu vào thuộc tập thử, màn hình chỉ in qua `cong.in_allowlist`.
  - Thông điệp có nội dung (lỗi của validator phiếu có chép ô của phiếu, cảnh báo câu không khớp…) ghi vào **tệp** trong thư mục ra, kèm một dòng số đếm theo mã
    lỗi trên màn hình. Không in nội dung.
  - Có test bí mật: chuỗi giả cài trong `stats` lồng, tên khái niệm, câu, ô phiếu. Kèm bằng chứng bản in ngây thơ làm test đỏ.
- **Không bao giờ nhận dữ liệu tập thử** (ví dụ `chuyen-vang`, `doi-chieu` chỉ cho vàng A8 cũ): chuyển sang danh sách "không nhận dữ liệu tập thử" kèm lý
  do. Nếu lệnh nhận manifest thì từ chối manifest `tap = thu`, kèm test.

Danh sách `CHUA_KIEM_BI_MAT` phải rỗng khi xong. Test phân loại vẫn đỏ với lệnh mới chưa phân loại.

## B. Sách bị sản phẩm từ chối

Theo giao thức mục 9: lượt hệ chính bị sản phẩm từ chối (bản ghi có `ket_qua.tu_choi`, bước trạng thái `tu_choi_<mã>`, mã thoát 3) thì không có hợp đồng, mà số
chính của cuốn đó vẫn phải có, tính như hệ không trả gì:
- độ phủ A3 và đầu-cuối bằng 0;
- Q6 bằng 1;
- F1 quan hệ bằng 0, tức là tp = 0, fn = số cạnh vàng, fp = 0, nhưng ép F1 = 0 thay vì `None`;
- tỉ lệ bằng chứng có thật bằng 0;
- các thước khâu khác để trống.

Việc:
- một hàm hay lệnh sinh các dòng `dong` đó cho từng chương bốc của cuốn, từ bản ghi lượt bị từ chối cộng vàng (G3, G4, để biết mẫu số);
- bộ sinh bảng (DG-17) nhận các dòng này và ghi chú dưới Bảng 9 "cuốn X bị sản phẩm từ chối (mã …)";
- hệ `chinh_vong_chu` (đường vòng) hiện ở một dòng riêng trong phụ lục, không vào Bảng 9 hay ba phép kiểm định.

## Tiêu chí

- [ ] `CHUA_KIEM_BI_MAT` rỗng; mỗi lệnh nhận tập thử có test bí mật với bằng chứng bản in ngây thơ đỏ.
- [ ] Dòng của sách bị từ chối: test tính tay mẫu số, kèm ca F1 = 0 chứ không phải `None`. Bảng 9 có chú thích. Kiểm định chính gồm cuốn đó với giá trị bất lợi.
- [ ] Bảng phá, tối thiểu:
  - in nội dung lỗi validator ra màn hình;
  - sách bị từ chối bị bỏ khỏi trung bình;
  - F1 = None thay vì 0;
  - đường vòng lọt vào Bảng 9.
