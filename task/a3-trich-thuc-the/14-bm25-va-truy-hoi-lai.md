# 14 — BM25 và truy hồi lai

**What to build:** Hỏi `P(A|B)`, `Naïve Bayes`, hay `sync.Mutex` thì tìm ra — những thứ truy hồi vector
hay trượt vì chúng là **chuỗi chính xác**, không phải ngữ nghĩa.

## Bằng chứng và lý do khớp đúng corpus này

Truy hồi lai dense + sparse tăng NDCG **26–31%** so với dense đơn thuần; recall@1000 từ ~0,87 lên 0,98.
Lý do khớp đúng loại tài liệu của dự án: dense hỏng ở **thuật ngữ chính xác, ký hiệu, tên riêng** — mà
giáo trình xác suất thống kê đầy `P(A|B)`, còn báo cáo DOCX đầy `sync.Mutex`, `Docker Compose`.

## Không thêm bộ tách từ tiếng Việt

Dùng `tsvector` mặc định (`simple`). Tiếng Việt viết rời âm tiết nên BM25 mặc định không hiểu `học máy`
là một từ — **nhưng đó không phải việc BM25 được thêm vào để làm**. Nó bù cho vector ở chuỗi chính xác,
mà chuỗi chính xác khớp nguyên văn, không cần tách từ.

Thêm phụ thuộc mang tên một ngôn ngữ là **đúng thứ dự án đã bác ba lần** ở B0 — bộ tách câu, danh sách
cụm nối, danh sách từ khoá chương. Nếu sau này đo thấy truy hồi văn xuôi tiếng Việt yếu thì mở lại,
**có số liệu**.

**Blocked by:** 13 — cần chỉ mục vector tồn tại để hợp nhất kết quả.

**Status:** done

- [x] Chỉ mục BM25 dựng từ **`text` chunk**, không cần gọi mô hình nào
- [x] Truy hồi lai: chạy hai nhánh, hợp nhất bằng Reciprocal Rank Fusion
- [x] Lọc theo `stage_id` hoạt động trên **cả hai** nhánh (chuẩn bị cho pha B)
- [x] Có test: truy vấn `P(A|B)` ⇒ nhánh BM25 tìm ra chunk chứa nó
- [x] Có test: truy vấn diễn đạt lại bằng lời ⇒ nhánh vector tìm ra
- [x] Có test: truy vấn có cả hai đặc tính ⇒ lai xếp hạng cao hơn từng nhánh riêng
- [x] **Không** thêm phụ thuộc tách từ mang tên ngôn ngữ nào
- [x] Ghi lại: với 5 truy vấn thuật ngữ dựng tay, thứ hạng của nhánh vector / BM25 / lai
