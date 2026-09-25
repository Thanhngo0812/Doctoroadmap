# 07 — Xác nhận trên tập giữ lại

**Nguồn chân lý:** spec v2, W18–W19

**What to build:** một lần chạy duy nhất, với cấu hình đã khoá (commit, `prompt_hash`, tham số), trên `xstk-ch3-1` và N2;
chấm Q1–Q9; báo nguyên kết quả kể cả trượt.

**Blocked by:** 02–06; vé 10 — T8 (vàng N2), T10 (duyệt cấu hình khoá)

**Status:** chờ

## Luật

- Trước lần chạy: ghi commit, `prompt_hash` từng khâu, tham số, SHA-256 của mọi tệp nhãn vào chính vé này.
- Chuyển `xstk-ch3-1-chuong-10-13-hoi-y-output.xlsx` thành JSON bằng `a8-gold-check` **ngay trước** lần chạy, không sớm hơn.
- Không chỉnh gì sau khi thấy số. Mọi thay đổi sau đó là hậu kiểm, báo tách riêng.
- Mỗi con số kèm khoảng tin cậy Wilson 95%; khoảng chứa vùng trượt thì kết luận là chưa đủ bằng chứng.

## N2 — chuẩn bị (2026-09-24)

- Tài liệu: `doc-4.pdf` (giáo trình Triết học Mác–Lênin, 214 trang, SHA-256 ghi ở manifest `artifacts/chunks/doc-4/v3`).
- Nhập: `ingest --pdf-backend pypdfium2 --heading-scheme vn-textbook` (docling-parse tách rời âm tiết; luật tiêu đề mặc
  định đặt mục con lên trên chương) → chunks v3: 672 chunk, 152k token.
- A3 candidates v1: 0,827 USD. A4/A5 canonical v1: 0,639 USD (`a4_gold_coverage=none`, cổng hồi quy
  `tests/fixtures/a4/gold-blind.json`). 620 khái niệm text.
- Chương gán vàng: **Chương VIII** (ordinal 9 ở `--chapter-level 2`), 47 khái niệm đích, 376 dòng quan hệ. Bảng
  `artifacts/a8-gold/doc-4-chuong-8-A1.xlsx`, `-A2.xlsx`; sinh **không** kèm `--graph` (chưa chạy A6–A8 trên doc-4), nên cột
  nơi dạy lấy từ A5.
- Luật: doc-4 là tập giữ lại. Không chạy A6–A10 trên doc-4 và không nhìn đồ thị của nó cho tới lần chạy duy nhất của vé này.

## T8 — nhận 2026-09-25

`a8-gold-check` qua cả hai bản, không lỗi: A1 65 cạnh, 13 cờ; A2 53 cạnh, 2 cờ; không bản nào ghi giờ. JSON:
`doc-4-chuong-8-A1.json`, `-A2.json`. Bảng hội ý `doc-4-chuong-8-hoi-y.xlsx` (`a8-gold-merge`): 41 dòng trùng, 36 dòng lệch,
concept_hash `7da62117ab70…`. Tôi không mở nội dung nhãn (tập giữ lại). Còn chờ: hội ý, rồi chuyển thành bộ vàng khoá.
