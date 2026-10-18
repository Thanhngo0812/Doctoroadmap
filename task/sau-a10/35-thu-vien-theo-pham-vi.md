# SA-35 — Thư viện tài liệu và quiz theo phạm vi; tạo bằng nút

**Nguồn chân lý:** [spec Pha B2](../../doc/pha-b2-spec.md), mục 3 (công cụ tạo nội dung), 4, 7, 10 (`library-1`, `quiz-2`, `document-2`); [ADR 0017](../../doc/adr/0017-pham-vi-phien-la-noi-luu-neo-vao-khai-niem.md).
**Ai:** nhân viên · Claude kiểm · **Chi phí mô hình:** 0 USD (mô hình giả và phát lại) · **Chặn bởi:** 32 · **Trạng thái:** ready-for-agent

## Vì sao

Mỗi module và trang lộ trình cần một thư viện tài liệu và quiz. Nội dung tạo ở module A mà nói về khái niệm của module B phải tìm thấy được ở cả hai nơi.
Người học cần nút tạo nội dung ngoài chat.

## Cần làm

**Tài liệu và lần làm quiz có thêm năm trường:**
- `home_scope`;
- `session_id`, hoặc null nếu tạo bằng nút;
- `origin` ∈ {`button`, `assistant`};
- `node_ids`;
- `created_at`.

Bỏ giá trị `module_button` cũ.

**Tạo nội dung:**
- **Qua trợ lý:** `make_quiz` và `make_document` gán `home_scope` theo phạm vi phiên, `origin = assistant`, rồi thêm tham chiếu vào `artifact_refs` của
  phiên.
- **Qua nút:** use case nhận phạm vi và `origin = button` từ người gọi.

**`list_library(owner, doc_id, filter)`:**
- **Module X**, hai nhóm:
  - `here`: nội dung có `home_scope` giải ra X;
  - `elsewhere`: nội dung tạo nơi khác mà `node_ids` giao với tập khái niệm hiện hành của X.
- **Lộ trình:** nội dung có `home_scope = roadmap`.
- **`all`:** mọi nội dung.

Module của nội dung được suy lúc liệt kê, không lưu cứng. Mục quiz có điểm nếu đã nộp.

**Xoá phiên** không xoá nội dung trong thư viện. Mục thư viện ghi phiên đã xoá.

**CLI:** lệnh liệt kê thư viện theo bộ lọc.

## Tiêu chí nghiệm thu

- [ ] Test, mỗi cái thấy đỏ trước:
  - tài liệu tạo trong phiên module A về khái niệm của B thì có ở thư viện A, nhóm `here`, và ở thư viện B, nhóm `elsewhere`;
  - tạo bằng nút có `origin = button` và `session_id = null`;
  - xoá phiên thì nội dung vẫn ở thư viện;
  - dùng cặp đồ thị v1, v2 của vé 31: module của nội dung được suy theo đồ thị hiện hành, không theo mã lưu lúc tạo;
  - đề quiz trong thư viện vẫn không có đáp án;
  - `owner` khác không thấy thư viện.
- [ ] Ví dụ JSON thật của `library-1`, kèm một mục `here` và một mục `elsewhere`, đính kèm báo cáo vé.
