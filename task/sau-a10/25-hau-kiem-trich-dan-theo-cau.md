# SA-25 — Hậu kiểm trích dẫn theo câu cho trợ lý và tài liệu

**Nguồn chân lý:** [spec Pha B](../../doc/pha-b-spec.md), mục "Nội dung ngoài sách", trợ lý bước 5 (hậu kiểm), tài liệu theo yêu cầu ("hậu kiểm
bằng cùng luật"); [báo cáo kiểm thử 2026-10-18](../../report/kiem-thu-pha-b-2026-10-18.md), mục 3.3, 3.4, 3.8, 4.
**Ai:** nhân viên · Claude kiểm · **Chi phí mô hình:** 0 USD (phát lại phản hồi đã ghi) · **Chặn bởi:** nhân viên commit mã Pha B còn dở ·
**Trạng thái:** ready-for-agent

## Vì sao

Spec yêu cầu định nghĩa, công thức và khẳng định về sách luôn có nguồn. Lượt kiểm 2026-10-18 tìm thấy ba đường lọt:
- **Trợ lý kiểm theo đoạn, không theo câu.** "…[S1]. Một hệ quản trị có đúng 7 thành phần bắt buộc." qua hậu kiểm nguyên vẹn, vì câu sau đứng cùng đoạn
  với một nhãn.
- **Tài liệu theo yêu cầu chỉ xoá nhãn sai mà giữ câu.** Định nghĩa không nguồn hiện ra cho người học. Nhãn ghép `[S3, S5]` không được kiểm.
- **Khối ngoài tài liệu chặn định nghĩa bằng từ khoá.** Câu "Supervised learning là một nhánh của học máy…" lọt. Ở tài liệu thì không có luật nào.

Cộng thêm: giá viết cứng ở sáu tệp Pha B, nên trần chi của trợ lý và tài liệu tính sai khi giá đổi.

## Cần làm

**1. Một bộ hậu kiểm dùng chung cho trợ lý và tài liệu.**
- **Đơn vị kiểm là câu.**
  - Tách bằng `UnicodeSentenceSplitter`, không bằng regex riêng.
  - Nhãn đứng cuối câu, trước hoặc sau dấu chấm, đều thuộc câu đó.
- **Câu không có nhãn hợp lệ thì bỏ**, và đếm cờ `unsourced_sentence`.
  - Ngoại lệ là câu nối: không có chữ số, không có ký hiệu toán, không có tên hay alias khái niệm nào của tài liệu, và ngắn. Ngưỡng độ dài đặt ở
    `BSettings`, báo giá trị đã chọn.
  - Câu nối được giữ mà không cần nhãn.
- **Câu có nhãn bịa:**
  - Nhãn bịa bị xoá.
  - Câu còn ít nhất một nhãn hợp lệ thì giữ; không còn nhãn nào thì bỏ như câu không nhãn.
- **Nhãn ghép** `[S3, S5]`, `[S3; S5]`, `[S3][S5]`: tách ra và kiểm từng nhãn.
- **Khối ngoài tài liệu:**
  - Thêm luật mẫu câu định nghĩa. Khối bị bỏ nếu có câu dạng "<tên hay alias khái niệm trong phạm vi> là …", "… được gọi là …", "… nghĩa là …",
    cộng với các luật từ khoá và ký hiệu đang có.
  - Tài liệu áp đúng luật này. Hiện tài liệu chưa có luật nào cho khối ngoài tài liệu.
- **Trợ lý giữ hành vi hiện có ở mức câu trả lời:** không còn câu có nguồn nào thì đổi thành từ chối.

**2. Tài liệu theo yêu cầu.**
- Dùng bộ hậu kiểm ở trên cho `markdown`.
- `ready` khi còn ít nhất một câu có nguồn. Báo thêm số câu bị bỏ.
- Bỏ tiêu đề `#` lặp: nếu `markdown` mở đầu bằng một dòng `#`, không thêm dòng `#` từ `title` nữa.

**3. Bảng giá dùng chung.**
- Mọi use case Pha B tính USD từ một bảng giá duy nhất, gồm trợ lý, tài liệu, bài giảng, tên, chỉ mục khái niệm.
- Kiểm lại giá embedding hiện hành, và ghi nguồn giá.

**4. Test traverse của vé 10.** Cạnh `requires` nằm trong `open_edges` (khác mọi cạnh cứng) không bao giờ ra khỏi `traverse`.

## Tiêu chí nghiệm thu

- [ ] Test, mỗi cái thấy đỏ trên mã hiện tại rồi mới xanh:
  - "…có cấu trúc [S1]. Một hệ quản trị có đúng 7 thành phần." thì câu sau bị bỏ và có cờ;
  - một câu mang cả nhãn thật lẫn nhãn bịa thì nhãn bịa bị xoá, câu giữ (sửa sai M5 của báo cáo kiểm thử phải đỏ);
  - tài liệu có nhãn bịa thì nhãn bị xoá (sửa sai M6 phải đỏ);
  - tài liệu có câu định nghĩa mất nhãn thì câu bị bỏ;
  - `[S3, S5]` được kiểm từng nhãn;
  - khối ngoài tài liệu chứa "X là …" với X là khái niệm trong phạm vi thì bị bỏ, ở cả trợ lý và tài liệu;
  - câu nối ngắn không có số và tên khái niệm thì được giữ;
  - tài liệu không lặp tiêu đề `#`;
  - `traverse` không trả cạnh `requires` mở (sửa sai M2 phải đỏ);
  - đổi giá trong bảng chung thì ước chi và sổ chi của trợ lý, tài liệu, bài giảng đổi theo.
- [ ] Phát lại 0 USD các phản hồi đã ghi của nhóm 2 (6 câu trợ lý, 6 tài liệu) qua bộ hậu kiểm mới. Báo:
  - số câu bị bỏ;
  - số nhãn bị xoá;
  - số khối ngoài tài liệu bị bỏ;
  - trạng thái trước và sau.

  Đính kèm 6 tài liệu sau hậu kiểm cho Claude đọc.
- [ ] Test kiến trúc vẫn xanh.

## Ngoài vé

Hai việc không thuộc vé này: đổi prompt của trợ lý hay tài liệu, và lượt thật có tiền. Lượt thật của vé 08 và 10 chạy sau vé này, theo kế hoạch.
