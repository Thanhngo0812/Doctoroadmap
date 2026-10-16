# 18e — Đổi mặc định pass phụ sang `ml`, ADR và CONTEXT.md

**Nguồn chân lý:** [spec pass phụ không LLM](../../doc/a8-pass-phu-ml-spec.md), mục 1 và 8.
**Ai:** nhân viên đổi cấu hình · Claude viết ADR và cập nhật `CONTEXT.md` · **Chi phí mô hình:** 0 USD ·
**Chặn bởi:** 18d, và chủ dự án đồng ý · **Trạng thái:** xong 2026-10-16 — mặc định `ml`, hồi quy toàn bộ xanh; phần Claude (ADR 0015, `CONTEXT.md`) đã xong

## Cần làm

- Đổi mặc định chế độ pass phụ sang `ml`. Chế độ `llm` vẫn chọn được.
- ADR mới: pass phụ chấm cặp bằng mô hình học. ADR này thay phần pass phụ dùng LLM của ADR 0008, nhưng vẫn giữ luật "chỉ kiểm cặp, không tự đề xuất
  cạnh".
- Cập nhật định nghĩa "Pass phụ" trong `CONTEXT.md`.

## Nghiệm thu

- [x] Chạy chuỗi đồ thị không truyền tuỳ chọn thì ra artifact `a8-secondary-ml-v1`.
- [x] Toàn bộ test qua.

## Triển khai nhân viên — 2026-10-16

- `Settings.secondary_mode` mặc định `ml`; `.env.example` đồng bộ `DOC2ROADMAP_SECONDARY_MODE=ml`.
- CLI/composition chọn nhánh ML sẵn có, không thêm cờ hay sửa thuật toán/cache. `DOC2ROADMAP_SECONDARY_MODE=llm` vẫn ghi đè được.
- Test đỏ trước sửa: **3 failed / 3 passed**, gồm lệnh `roadmap --doc-id doc` đi vào LLM và bị SpendGuard chặn. Sau sửa: **6 passed**.
- Test chuỗi dùng CLI + composition + orchestrator + stage ML thật trên dữ liệu tổng hợp; scorer/tokenizer giả, stage khác giả lập cache.
  Kiểm artifact có algorithm_id `a8-secondary-ml-v1`, một cạnh thực nhận, đúng thứ tự các stage, không `--allow-spend`, 0 USD pass phụ.
- Theo yêu cầu bổ sung của chủ dự án, `.env` thật cũng đã đồng bộ `DOC2ROADMAP_SECONDARY_MODE=ml`; giữ nguyên mọi giá trị khác và không commit tệp
  chứa khóa bí mật. Không gọi mô hình trả phí, không chạy lại dữ liệu nhãn/đổi mô hình. ADR/CONTEXT do Claude cập nhật giữ nguyên.
- Hồi quy toàn worktree: **1.385 passed**, 7 cảnh báo thư viện, **187,14 giây**. Kiểm đọc `Settings()` từ `.env` thật trả `secondary_mode=ml`.
- Snapshot riêng tám tệp sẽ commit, không cần mã Pha B đang dở: **1.203 passed**, 7 cảnh báo thư viện, **205,06 giây**.
- Lệnh và kết quả hồi quy: [báo cáo 18e](../../report/v4-18e-mac-dinh-pass-phu-ml-2026-10-16.md).
