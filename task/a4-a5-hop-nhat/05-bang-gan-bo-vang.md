# 05 — Bảng gán bộ vàng `a4-gold-sheet`

**What to build:** `a4-gold-sheet --doc-id …` sinh một **file HTML tự chứa**. Mở bằng trình duyệt trên máy, người gán
thấy từng mục như một khối: tên, alias, ký hiệu, kiểu, `section_path` và câu bằng chứng của từng nhóm. Người gán bấm
một trong năm nhãn; tiến độ tự lưu trong trình duyệt, mở lại vẫn còn. Gán xong bấm **"xuất JSON"** ra đúng khuôn
fixture bộ vàng A4. Kèm bộ nạp kiểm khuôn file đó.

## Vì sao phải có trước lần chạy mô hình đầu tiên

Bộ vàng là bảng đáp án để chấm A4 bằng số thay vì đoán — chọn k, trần cụm, model, giữ hay bỏ kênh mô tả. Nó chỉ có
giá trị khi **mù**: bảng gán sinh từ đồ thị đề cử (chưa có quyết định mô hình nào), không hiện gợi ý, và người gán
chưa từng thấy kết quả A4. Cùng khuôn `blind_before_first_a3_run` của bộ vàng A3.

File HTML chứa nguyên văn tài liệu, nên nó chạy trên máy và không bao giờ vào git — cùng lý do repo để private.

**Blocked by:** 04 — Đồ thị đề cử và gom cụm ứng viên

**Status:** done

**Cập nhật triển khai 2026-09-11:** Đã sinh bảng 416 mục, loader và chuyển phụ lục A 53 mục/bỏ 5; chưa kiểm thao tác bằng browser vì runtime không khả dụng.
Chi tiết kiểm chứng và phần chưa hoàn tất: [feedback A4/A5](../../feedback/F18-a4-a5-hop-nhat.md).

- [x] **Mục gán** gồm:
    - mọi cạnh của đồ thị đề cử (256 trên bốn tài liệu);
    - 100 cặp nhóm **không** có cạnh, lấy ngẫu nhiên với seed cố định, chia cho các tài liệu theo tỉ lệ số nhóm —
      để đo cặp trùng nằm ngoài tầm ba kênh đề cử;
    - mọi nhóm tên có từ hai ứng viên trở lên (60), để soát đồng âm khác nghĩa.
- [x] **Nhãn cho cặp**: cùng · cha–con (người gán chọn chiều) · anh em / liên quan · khác · không chắc. **Nhãn cho nhóm
      tên**: một thực thể · có đồng âm (đánh dấu ứng viên nào khác nghĩa).
- [x] Thứ tự mục xáo bằng seed cố định. Bảng **không** lộ kênh nào đề cử, **không** hiện cosine, **không** hiện gợi
      ý, **không** hiện kết quả A4 nào.
- [ ] Mở file không gọi mạng; mọi nội dung nhúng sẵn. Tiến độ lưu trong trình duyệt và khôi phục khi mở lại; có bộ
      đếm đã gán / tổng. *DOM giả đã kiểm lưu; chưa kiểm khôi phục bằng browser thật vì phiên review không có
      browser backend.*
- [x] **JSON xuất ra** có: phiên bản khuôn, `doc_id`, mỗi mục một định danh ổn định (khoá tên và `candidate_id` hai
      đầu), nhãn, người gán, thời điểm, cờ `blind_before_first_a4_run: true`.
- [x] **Bộ nạp** fixture bộ vàng A4 kiểm khuôn: thiếu nhãn, nhãn lạ, mục không khớp artifact `candidates` hiện hành ⇒
      lỗi rõ ràng, chỉ ra mục nào.
- [x] File HTML sinh vào thư mục không commit (`/artifacts/` đã nằm trong `.gitignore`).
- [x] Nhãn tay ở **phụ lục A** của `report/nghien-cuu-a4-a5-hop-nhat-thuc-the.md` được chuyển thành một file người
      gán thứ hai cùng khuôn, khớp theo tên nhóm; mục không khớp thì bỏ và đếm — dùng để đo đồng thuận ở ticket 13.
- [x] Test: sinh bảng cho fixture `baocao-canhan` ra đúng số mục (37 cạnh + phần ngẫu nhiên + nhóm tên nhiều ứng
      viên); cùng seed ⇒ cùng tập mục và thứ tự; bộ nạp từ chối file sai khuôn (mỗi loại lỗi một test).
- [x] Toàn bộ test hiện có vẫn xanh.
