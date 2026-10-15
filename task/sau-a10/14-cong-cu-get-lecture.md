# SA-14 — Công cụ `get_lecture` của trợ lý

**Nguồn chân lý:** [ADR 0012](../../doc/adr/0012-tro-ly-la-agent-goi-cong-cu.md); [spec Pha B](../../doc/pha-b-spec.md), mục 8 (hai đường gọi
chung một hàm), 10 (bảng công cụ), bất biến 14.
**Ai:** nhân viên · Claude kiểm · **Chi phí mô hình:** 0 USD (bài giảng tính vào chức năng bài giảng) · **Chặn bởi:** 08, 12 ·
**Trạng thái:** ready-for-agent

## Vì sao

Chủ dự án chốt: bài giảng đã có sẵn khi bấm, nên agent không tự viết bài giảng. Khi người học nhắn "giảng cho tôi khái niệm X", agent mở đúng bài
mà nút bấm hiện.

## Cần làm

**Công cụ `get_lecture(concept)`:**
- Đọc bài giảng trong cache. Chưa có thì gọi **đúng hàm** của nút bấm, cùng khoá, và bài vào cache chung.
- Trả cho mô hình bản tóm tắt các ý, kèm nhãn nguồn, để mô hình trích được.

**Hai thay đổi đi kèm:**
- Câu trả lời của trợ lý có sự kiện `artifact` trỏ tới bài giảng, để web hiện bản đầy đủ.
- Nhãn của bài giảng được nhập vào tập nhãn của lượt, để hậu kiểm của vé 09 nhận được.

## Tiêu chí nghiệm thu

- [ ] Test: đường nút bấm và đường công cụ cho cùng `lecture_key`. Gọi lần hai thì không sinh.
- [ ] Test: câu trả lời trích một ý của bài giảng thì qua hậu kiểm. Nhãn bịa thì bị xoá như mọi nhãn khác.
- [ ] Phí sinh bài giảng ghi trong sổ chi theo mục đích `lecture`, không tính vào trần của agent.
