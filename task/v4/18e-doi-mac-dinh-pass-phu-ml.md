# 18e — Đổi mặc định pass phụ sang `ml`, ADR và CONTEXT.md

**Nguồn chân lý:** [spec pass phụ không LLM](../../doc/a8-pass-phu-ml-spec.md), mục 1 và 8.
**Ai:** nhân viên đổi cấu hình · Claude viết ADR và cập nhật `CONTEXT.md` · **Chi phí mô hình:** 0 USD ·
**Chặn bởi:** 18d, và chủ dự án đồng ý · **Trạng thái:** chờ 18d

## Cần làm

- Đổi mặc định chế độ pass phụ sang `ml`. Chế độ `llm` vẫn chọn được.
- ADR mới: pass phụ chấm cặp bằng mô hình học. ADR này thay phần pass phụ dùng LLM của ADR 0008, nhưng vẫn giữ luật "chỉ kiểm cặp, không tự đề xuất
  cạnh".
- Cập nhật định nghĩa "Pass phụ" trong `CONTEXT.md`.

## Nghiệm thu

- [ ] Chạy chuỗi đồ thị không truyền tuỳ chọn thì ra artifact `a8-secondary-ml-v1`.
- [ ] Toàn bộ test qua.
