# SA-18 — Tài liệu theo yêu cầu (`make_document`)

**Nguồn chân lý:** [spec Pha B](../../doc/pha-b-spec.md), mục 1, 11, 13 (hợp đồng `document-1`), bất biến 1, 3.
**Ai:** nhân viên · Claude kiểm · **Chi phí mô hình:** lượt thử 5 yêu cầu, dưới 0,05 USD, dry-run trước · **Chặn bởi:** 09, 12 ·
**Trạng thái:** ready-for-agent

## Vì sao

Chủ dự án muốn agent tạo tài liệu theo đúng yêu cầu của người học, ví dụ "một bản chi tiết về một khái niệm", hay "đề cương ôn chương 2". Tài
liệu phải có trích dẫn như mọi nội dung khác, và tải về được.

## Cần làm

**Use case tài liệu theo yêu cầu, kèm công cụ `make_document(request, scope)`:**
- `request` là yêu cầu tự do; `scope` là khái niệm, danh sách khái niệm, hay module.
- **Ngữ cảnh:** dùng lại bộ lắp ngữ cảnh của bài giảng (vé 12) cho từng khái niệm trong phạm vi. Phạm vi lớn thì chỉ lấy câu định nghĩa, chunk dạy
  và tiên quyết. Thêm truy hồi theo yêu cầu.
- **Ngân sách:** trần ngữ cảnh 8.000 token, trần đầu ra 3.000 token, trần chi khoảng 0,01 USD mỗi tài liệu. Các giá trị này nằm trong cấu hình
  và được chỉnh ở lượt thử.
- **Đầu ra:** Markdown có nhãn nguồn và khối ngoài tài liệu. Hậu kiểm bằng cùng luật của vé 09. Công thức chỉ bằng nhãn `[CTk]`.

**Lưu và xuất:**
- Tài liệu lưu theo người học, không cache chung.
- Xuất tệp Markdown để tải về: nhãn đổi thành chú thích nguồn (trang, mục), khối ngoài tài liệu giữ khung có nhãn.

**Hợp đồng và CLI:**
- Hợp đồng `document-1`.
- Sự kiện `artifact` trong câu trả lời của trợ lý.
- Lệnh CLI tạo tài liệu từ một yêu cầu, có `--dry-run` và `--allow-spend`.

## Tiêu chí nghiệm thu

- [ ] Test với mô hình giả, mỗi cái thấy đỏ trước:
  - nhãn bịa bị xoá;
  - tài liệu không có nhãn hợp lệ nào thì trả `failed` kèm lý do;
  - khối ngoài tài liệu được giữ và được đếm;
  - vượt trần đầu ra thì cắt đúng chỗ và ghi cờ;
  - bản xuất Markdown có chú thích nguồn đúng trang.
- [ ] Lượt thật 5 yêu cầu trên doc-1 và doc-4, sau dry-run và chủ dự án duyệt. Báo USD và giây cho từng tài liệu. Claude đọc cả 5 tài liệu và ghi phán xét.

## Ngoài vé

Xuất PDF, và thẻ ghi nhớ.
