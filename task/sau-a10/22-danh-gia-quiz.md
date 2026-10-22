# SA-22 — Đánh giá quiz

**Nguồn chân lý:** [báo cáo quiz](../../report/nghien-cuu-quiz-tu-kiem-tra-2026-10-11.md), mục 2.7, 5; [spec Pha B](../../doc/pha-b-spec.md), "Ghi chú
thêm".
**Ai:** agent Sonnet chạy và xuất bảng · hai thành viên nhóm chấm; giảng viên chấm 20 câu nếu được · Claude phân tích · **Chi phí mô hình:** khoảng
1,7 USD, dry-run trước, chủ dự án duyệt · **Chặn bởi:** 16, 27, 52 (đều đã đạt) · **Trạng thái:** sẵn sàng

**Dữ liệu (cập nhật 2026-10-22):** graph ghim và kho Pha B theo [bảng kế hoạch, đợt đánh giá 20–23](00-ke-hoach.md). Câu điền khuyết theo luật `quiz-local-rules-v4` (SA-52).

## Vì sao

Cần trả lời bốn câu hỏi:
- Câu do LLM sinh có đạt chuẩn viết câu trắc nghiệm không?
- Lời gọi kiểm giải mù bắt được bao nhiêu lỗi?
- Lỗi "nhiều hơn một đáp án đúng" có tỉ lệ bao nhiêu? Văn liệu cho thấy lỗi này gần như không bắt được tự động.
- Bản LLM hơn bản điền khuyết ở đâu?

## Cần làm

**Mẫu:** khoảng 200 câu LLM trải đều sáu cuốn, cùng các câu điền khuyết trên cùng tập khái niệm. Ghi cả các câu mà lời gọi kiểm đã loại, để đo độ
chính xác của nó.

**Bảng chấm mù:**
- Rubric theo hướng dẫn viết câu trắc nghiệm của Haladyna, Downing và Rodriguez: đúng đáp án, chỉ một đáp án đúng, câu nhiễu hợp lý, không lộ đáp
  án, căn cứ trong tài liệu, mức Bloom, tiếng Việt.
- Người chấm tự trả lời câu hỏi trước rồi mới chấm.

**Đo:**
- precision và recall của lời gọi kiểm so với người chấm;
- tỉ lệ câu có hơn một đáp án đúng;
- độ phủ khái niệm theo cuốn;
- phân bố mức Bloom;
- USD mỗi module, giây tới câu đầu.

## Tiêu chí nghiệm thu

- [ ] Dry-run và chạy thật trong trần. Báo USD.
- [ ] Bảng chấm mù và tệp khoá để riêng.
- [ ] Hai người chấm xong. Claude tính κ và AC1, viết báo cáo kết quả gồm ca xấu. Báo cáo đề xuất có giữ lời gọi kiểm hay không, theo độ chính xác đo được.
