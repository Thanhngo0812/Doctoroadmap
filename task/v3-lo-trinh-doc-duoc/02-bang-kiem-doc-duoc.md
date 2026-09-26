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
