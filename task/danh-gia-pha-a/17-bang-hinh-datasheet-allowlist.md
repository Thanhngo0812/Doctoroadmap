# DG-17 — Bảng, hình, datasheet, cổng allowlist

**Nguồn:** spec mục 14, 16; bản hội đồng mục 13; skill `dataviz` · **Ai:** agent A · **Chi phí:** 0 · **Chặn bởi:** DG-05, DG-15, DG-16 · **Hạn:** 04/11 ·
**Trạng thái:** ready-for-agent

## Làm được gì

Một lệnh đọc kết quả của thư mục lượt, rồi sinh:
- **bảng 9–12** của bản hội đồng, dạng Markdown, có tên bảng đặt trên bảng;
- **Hình 3** (điểm F1 theo cuốn, có CI, hệ chính và B5);
- **Hình 4** (thác nước quy lỗi).

Hai hình xuất SVG bằng mã, theo bảng màu và quy tắc của `dataviz`, đọc được ở nền sáng và tối.

Thêm hai việc:
- sinh khung **datasheet** cho bộ vàng (Gebru; mục D của danh mục ACL), có chỗ điền thông tin người gán ẩn danh;
- **cổng allowlist**: mọi lệnh có tham số tập thử chỉ in trường số hay bool trong danh sách cho phép.

## Tiêu chí

- [ ] Bảng sinh ra từ kết quả fixture khớp số tính tay. Ô thiếu số hiện "—", không hiện 0.
- [ ] SVG hợp lệ, có tiêu đề và nhãn trục, không phụ thuộc thư viện ngoài.
- [ ] **Allowlist:** test có chuỗi bí mật giả cài trong `stats` lồng, tên khái niệm, câu; bản in ngây thơ phải đỏ, bản allowlist phải xanh.
- [ ] Bảng phá, gồm ít nhất: in nguyên dict kết quả; trục hình cắt mất CI; bảng làm tròn trước khi tính.
