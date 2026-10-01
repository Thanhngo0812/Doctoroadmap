# 02 — Bảng kiểm đọc được

**Nguồn chân lý:** [spec v3](../../doc/v3-lo-trinh-doc-duoc-spec.md), R11 · **Ai:** **tôi** (công cụ kiểm thử) · **Phụ thuộc:** — · **Chi phí mô hình:** 0

**Trạng thái:** xong — xem cuối vé

## Việc cần làm
`scripts/doc-lo-trinh/kiem_doc_duoc.py <doc> [stages]` in các vi phạm của bảng kiểm R11 trên một artifact `stages`:
1. module 1 lấy từ vùng ngoài `noi_dung` (khi có vai trò vùng — vé 03) hoặc tên khớp mẫu đề cương/lời nói đầu/bài tập;
2. tên module trùng; tên chứa mẫu vùng ngoài `noi_dung`; tên là câu dài;
3. `mentioned_only`/`unchecked` nằm trong dãy học;
4. dòng "cần:" hiển thị > 3 mục;
5. tên khái niệm là nhãn đánh số hoặc từ chung;
6. một section `noi_dung` bị tách thành hai module cách nhau quá một chương.
Kèm công cụ đọc có sẵn `scripts/doc-lo-trinh/in_lo_trinh.py`.

## Nghiệm thu
Chạy được trên sáu tài liệu phát triển và ra đúng các lỗi đã ghi trong báo cáo đánh giá (ví dụ doc-2: 49 tên từ vùng không dạy).

## Đã làm (2026-09-26, tôi) — mốc "trước" cho mọi vé v3

`scripts/doc-lo-trinh/kiem_doc_duoc.py` (thêm `--chi-tiet` để in từng vi phạm). Chưa có vai trò vùng (vé 03) nên kiểm theo mẫu tiêu đề.

| vi phạm | doc-1 v37 | doc-2 v29 | doc-6 v8 | nhap-mon-ml v37 | doc-3 v19 | naive-bayes v37 |
|---|---|---|---|---|---|---|
| module 1 ngoài bài giảng | 0 | 1 | 1 | 1 | 0 | 0 |
| tên module trùng | 10 | 11 | 0 | 1 | 0 | 0 |
| tên từ vùng không dạy | 4 | 49 | 1 | 4 | 0 | 0 |
| tên là câu dài | 3 | 0 | 2 | 6 | 1 | 2 |
| chỉ-được-nhắc trong dãy học | 17 | 104 | 14 | 19 | 27 | 13 |
| "cần:" hiển thị > 3 | 38 | 56 | 1 | 2 | 1 | 3 |
| tên khái niệm vô nghĩa | 9 | 2 | 0 | 0 | 0 | 0 |
| mục bị xé | 7 | 17 | 0 | 4 | 0 | 0 |

(doc-6 v8 dựng bằng chuỗi cũ C8 v2; sẽ dựng lại bằng chuỗi mới khi chạy vé 05.)

**Trạng thái:** xong (công cụ); dùng để kiểm mọi vé sau.

## Bản không phụ thuộc ngôn ngữ (vé 02b, tôi, 2026-10-01) — mốc mới

Từ nay `kiem_doc_duoc.py` không còn regex vi/en:
- vùng không dạy lấy từ vai trò section (R1);
- nhãn đánh số lấy từ họ nhãn trong chính tài liệu (`label_families`, như R9);
- mã chương/mục lấy từ họ đánh số (`chapter_members`, `section_code`).

Thêm ba kiểm:
- `ten-nen-la-goc`: tên nền là nút gốc, kiểu "document>";
- `ten-nen-chi-co-ma`: tên nền chỉ có mã, kiểu "6B", "Chapter 3", "第3章";
- `ten-theo-khai-niem-dau`: tên module là nguyên tên khái niệm đầu (đích của vé 09d).

Tên dài đo theo từ, hoặc theo ký tự với chữ viết không cách từ (> 36, như `clean_titles`). `--tu-kiem` chạy ví dụ tiếng Đức và tiếng Nhật;
ba đột biến của luật nhận mã và độ dài đều làm nó đỏ.

Mốc trên kho `v3-05b-a9v10-evaluation`. v6 là trước 09c, v10 là sau 09c; mọi tài liệu cùng dãy học. Ô ghi bản mới; khác bản cũ thì ghi
"bản cũ → bản mới".

| vi phạm | doc-1 v6 / v10 | doc-2 v6 / v10 | doc-3 v6 / v10 | doc-6 v6 / v10 | naive-bayes v6 / v10 | nhap-mon-ml v6 / v10 |
|---|---|---|---|---|---|---|
| module 1 ngoài bài giảng | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| tên module trùng | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| tên từ vùng không dạy | 0 / 0 | 1 → 0 / 1 → 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| tên là câu dài | 8 / 6 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 5 / 3 |
| **tên nền là gốc** | 0 / 0 | 0 / 0 | **3** / 0 | **2** / 0 | **3** / 0 | 0 / 0 |
| **tên nền chỉ có mã** | 0 / 0 | **14** / **5** | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| **tên theo khái niệm đầu** | 0 / 0 | 5 / 2 | 0 / **3** | 0 / **2** | 0 / **3** | 0 / 0 |
| chỉ-được-nhắc trong dãy học | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| "cần:" hiển thị > 3 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| tên khái niệm vô nghĩa | 1 / 1 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| mục bị xé | 1 / 1 | 2 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |

Giải thích chênh lệch giữa bản cũ và bản mới:
- **doc-2, "tên từ vùng không dạy" 1 → 0:** bản cũ bắt chữ "Problems" trong mục nội dung "6C … Minimization Problems …". Đó là báo nhầm do
  regex.
- **Ba kiểm mới:**
  - bản cũ bỏ sót 8 tên "document> — …" ở ba tài liệu slide (v6) và 14 tên chỉ có mã ở doc-2;
  - sau 09c còn 5 tên chỉ có mã (trang mục lục mất khi parse);
  - còn 10 module đặt theo tên khái niệm đầu (vé 09d).
- **Không đổi:** "tên khái niệm vô nghĩa" doc-1 = 1 ("Định lý 4", fallback của 11b). Nay nhận qua họ nhãn "định lý" của chính tài liệu thay
  vì regex.
