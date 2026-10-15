# SA-17 — Công cụ `make_quiz` của trợ lý

**Nguồn chân lý:** [ADR 0012](../../doc/adr/0012-tro-ly-la-agent-goi-cong-cu.md); [spec Pha B](../../doc/pha-b-spec.md), mục 7 (trần riêng), 9
(lịch sử), 10 (bảng công cụ).
**Ai:** nhân viên · Claude kiểm · **Chi phí mô hình:** 0 USD cho phần của vé; câu thiếu được sinh theo chức năng quiz · **Chặn bởi:** 08, 16 ·
**Trạng thái:** ready-for-agent

## Vì sao

Chủ dự án muốn agent "tạo quiz trực tiếp" theo yêu cầu của người học, ví dụ "cho tôi 5 câu về định thức và hạng".

## Cần làm

**Công cụ `make_quiz(scope, n, level)`:**
- `scope` là một danh sách khái niệm hoặc một module; `n` tối đa 10; `level` là mức Bloom, tuỳ chọn.
- Tạo một lần làm cho người học, rút từ ngân hàng chung của vé 16. Khái niệm nào chưa có ngân hàng thì sinh qua đúng hàm của vé 16.
- Trả cho mô hình mã lần làm và tóm tắt (số câu, các khái niệm).

**Ba thay đổi đi kèm:**
- Câu trả lời có sự kiện `artifact` trỏ tới lần làm.
- Lần làm lưu với `origin = assistant` và hiện trong lịch sử của người học.
- Tiền sinh câu ghi theo mục đích quiz, tách khỏi trần của agent.

## Tiêu chí nghiệm thu

- [ ] Test với mô hình giả gọi công cụ:
  - lần làm được tạo đúng phạm vi và số câu;
  - `origin = assistant`, và có trong lịch sử;
  - ngân hàng có sẵn thì không gọi mô hình;
  - tiền tách khỏi trần của agent.
- [ ] Đề của lần làm do agent tạo vẫn không chứa đáp án.
