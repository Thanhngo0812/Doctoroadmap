# ADR 0006: Embedding chỉ đề cử, không bao giờ tự gộp

**Trạng thái:** accepted  
**Ngày:** 2026-09-11

## Bối cảnh

Spec cũ cho cosine tự gộp ứng viên ở ba chỗ: A4 (`≥ 0,90`), Tầng 2a (`≥ 0,95`, *"merge thẳng bằng code"*) và
MVP (*"A4 chỉ lớp lọc tên + embedding"*, không có lời gọi mô hình nào). Đo trên bốn tài liệu
(`report/nghien-cuu-a4-a5-hop-nhat-thuc-the.md`, mục 2), với `gemini-embedding-001` trên `description_draft`:
nền cosine giữa hai thực thể bất kỳ là 0,80; trong 62 cặp tên khác nhau vượt 0,95 chỉ 8 cặp là trùng thật;
31 cặp khác tên đạt ≥ 0,999 vì A3 viết cùng một câu mô tả cho các mục trong một danh sách liệt kê. Năm hệ
thống đang chạy thật (GraphRAG, LightRAG, Graphiti, KGGen, Neo4j LLM Graph Builder) đều không để embedding
của mô tả quyết định danh tính.

## Quyết định

Code chỉ tự gộp các ứng viên trùng tên khít sau chuẩn hoá. Embedding — cùng alias và độ giống chuỗi của tên —
chỉ **đề cử** cặp nghi trùng; các cặp này được gom thành cụm ứng viên và mô hình phán từng cụm dựa trên câu bằng
chứng nguyên văn. Không có ngưỡng cosine nào, dù cao đến đâu, được gộp thẳng.

## Hệ quả

- Gộp nhầm — lỗi không tầng nào sau báo — chỉ còn đến từ tên trùng khít hoặc từ một phán quyết có lý do ghi
  trong nhật ký gộp.
- Đổi mô hình embedding chỉ đổi recall của hàng chờ, không trực tiếp đổi danh tính; vẫn phải chạy lại A4
  theo ADR 0004.
- Mỗi tài liệu tốn thêm vài chục lời gọi mô hình: khoảng 60 cụm cho cả bốn tài liệu hiện tại.
