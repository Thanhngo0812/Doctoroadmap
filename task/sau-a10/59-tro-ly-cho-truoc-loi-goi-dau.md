# SA-59 — Trợ lý: đo và cắt thời gian chờ trước lời gọi mô hình đầu tiên

**Nguồn:** lượt thật SA-55 (`report/pha-b-sa55-2026-10-22.md`). Ưu tiên của dự án là thời gian và tiền cho mỗi cuốn. Đã biết trước: trên Vertex,
embedding gửi mỗi văn bản một request và bị bóp quota khi nhiều văn bản.

**Ai:** agent Sonnet đo và cài · Claude nghiệm thu · **Chi phí mô hình:** 0 USD; phần đo latency thật, nếu cần, dry-run và xin duyệt riêng ·
**Chặn bởi:** SA-58 · **Trạng thái:** chờ SA-58

## Vì sao

Ở SA-55, người học chờ khá lâu trước khi thấy chữ đầu tiên:

| | p50 | p90 |
|---|---|---|
| tới chữ đầu tiên (TTFT của sản phẩm) | 15,8 s | 28,2 s |
| riêng mô hình, sau khi đã gọi | 0,95 s | 2,7 s |

Như vậy hơn 90% thời gian chờ nằm **trước** lời gọi mô hình. Các dấu hiệu:
- 150 lời gọi embedding cho 36 lượt, tức khoảng 4 lời gọi mỗi lượt;
- phiên module chờ 16–18 s, còn phiên lộ trình chỉ khoảng 5 s;
- `SearchDocumentB.search` nạp lại đồ thị (`load_learning_graph`) và chỉ mục (`load_latest_retrieval`) ở mỗi lần tìm;
- lượt chạy qua Vertex, mà Vertex gửi mỗi văn bản một request và bóp quota.

Chưa biết phần nào chiếm bao nhiêu.

## Cần làm

1. **Đo, 0 USD.** Dùng embedding giả có độ trễ cố định và mô hình giả. Với mỗi lượt của bộ câu SA-55 (`scripts/phase-b/sa55_plan.json`), ghi:
   - thời gian nạp đồ thị và chỉ mục;
   - số lời gọi embedding và **chỗ gọi**: tìm kiếm trước vòng đầu, `lookup_concept`, chỉ mục khái niệm hay chỗ khác;
   - thời gian xếp hạng;
   - thời gian dựng ngữ cảnh.

   Báo theo phiên module và phiên lộ trình, trên doc-1 và nhap-mon-ml.
2. **Cắt**, theo kết quả đo, trong phạm vi sau:
   - không nạp lại đồ thị và chỉ mục giống hệt ở mỗi lượt; dùng bộ nhớ đệm theo `(doc_id, graph_version, phiên bản chỉ mục)`;
   - không embedding lại cùng một câu hỏi nhiều lần trong một lượt;
   - gộp các văn bản cần embedding vào một lời gọi nếu adapter hỗ trợ.

   Không đổi thuật toán xếp hạng, ngưỡng hay số kết quả.
3. Đo lại, 0 USD, cùng cách, và so trước với sau.

## Tiêu chí nghiệm thu

- [ ] Bảng đo trước và sau, theo từng khâu, ở phiên module và phiên lộ trình.
- [ ] Số lời gọi embedding mỗi lượt giảm, hoặc giải thích vì sao từng lời gọi còn lại là cần.
- [ ] Kết quả tìm kiếm trước và sau giống hệt nhau trên bộ câu SA-55: cùng `chunk_id`, cùng thứ tự. Phát lại bản ghi SA-55 vẫn khớp.
- [ ] Test cho bộ nhớ đệm:
  - đổi `graph_version` hay phiên bản chỉ mục thì nạp lại;
  - không lẫn dữ liệu giữa hai `doc_id`.
- [ ] Test Pha B, test kiến trúc và cổng toàn repo xanh.
- [ ] Nếu cần số latency thật trên Vertex hay Developer API: dry-run, rồi chờ chủ dự án duyệt. Không tự chạy có tiền.
