# Pass phụ chấm cặp bằng mô hình học, không gọi LLM

**Status:** accepted — 2026-10-16 · thay phần "pass phụ hỏi LLM" của ADR 0008

Mặc định, pass phụ không gọi LLM. Nó vẫn **chỉ kiểm cặp**, như ADR 0008: chỉ phán các cặp nghi tiên quyết do code đề cử, và không tạo cạnh ngoài hồ
sơ. Thứ thay đổi là người phán: một mô hình LightGBM đóng băng (E5) chấm từng chiều X → Y bằng 82 đặc trưng cấu trúc. Các đặc trưng này lấy từ thứ đã
có trước pass phụ: nguồn cặp, trích dẫn, thứ tự và mục, tên X trong cửa sổ định nghĩa Y, độ phủ.

Cạnh được tạo theo ba luật:
- Ngưỡng tính riêng cho từng tài liệu bằng hiệu chỉnh isotonic, lặp tới điểm bất động trên các cặp được phán.
- Chỉ tạo **cạnh cứng** `can_de_hieu` / `trong_dinh_nghia`, với câu trích nguyên văn trong cửa sổ định nghĩa của đích.
- Câu trích phải qua đúng bộ kiểm hợp đồng của pass chính.

Pass phụ LLM vẫn chọn được (`secondary_mode = llm`). Nó là mốc so sánh và là đường lùi.

**Căn cứ**
- Chủ dự án chốt ngày 2026-10-05: pass phụ bỏ LLM, cho cả đồ án lẫn seminar. LLM chỉ còn ở A3 và pass chính. Ngày 2026-10-16, chủ dự án duyệt đổi
  mặc định sau nghiệm thu.
- Chi phí: trên d01-02, cả cuốn tốn 0,124 USD với pass phụ không LLM, so với 2,99 USD với pass phụ LLM. Pass phụ chạy 18 giây thay vì 26 phút.
- Nghiệm thu (vé 18d): sản phẩm tái lập đúng E5 nghiên cứu trên ba tài liệu vàng.

**Considered Options**
- *Giữ LLM.* Chất lượng tốt hơn ở doc-1 và xstk, nhưng pass phụ chiếm khoảng 91–96% tiền mỗi cuốn.
- *Cross-encoder PhoBERT (E6).* AP trên D-01 cao hơn chút, nhưng không hơn E5 ở doc-4. Chạy CPU mất 14 phút một cuốn. Để đo lại trên T-01.
- *Lọc bí danh cắt cụt trong bộ khớp tên.* Làm sạch cạnh ngược nhưng hại vàng ở sách toán (báo cáo vòng 2, mục 8.15).

**Consequences**
- Chất lượng là đánh đổi đã chấp nhận. E5 hơn LLM ở doc-4, nhưng kém ở doc-1 và xstk. Kết luận cuối đo trên T-01.
- Mô hình học trên nhãn agentic D-01, là nhãn bạc. Khi thượng nguồn đổi (vé 17 gộp khâu trước A8), phải đo lại E5. Nếu tụt thì học lại; mã stage
  không đổi, chỉ đổi tệp mô hình và phiên bản.
- Pass phụ không còn bắt được quan hệ mà tên X không xuất hiện trong cửa sổ định nghĩa của Y. Đây là trần của cách chọn ứng viên.
- Khoảng 40% cạnh ngược của E5 là cạnh sai, chủ yếu do tên đa nghĩa (D-04). R17 hạ chúng thành cạnh mềm.
