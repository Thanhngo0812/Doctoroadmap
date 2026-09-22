# 20 — A9 v2: kiểm tra tính nhất quán cấu trúc

**Nguồn chân lý:** [`doc/va-a9-a10-do-thi-tot-va-lo-trinh-dung-duoc-spec.md`](../../doc/va-a9-a10-do-thi-tot-va-lo-trinh-dung-duoc-spec.md)
V3, V4, V5, V6, V10, V11 (F113)

**What to build:** A9 làm đúng việc nó nói: gỡ chu trình bằng nghiệm **chính xác** ở mọi cỡ, đưa cặp hai chiều ra
khỏi đồ thị tiên quyết, và một cổng chất lượng không còn phán xét chất lượng tài liệu bằng hai hằng số không nguồn.

**Blocked by:** None — chạy được song song với vé 19. **Chặn:** vé 21, vì A10 chỉ đúng khi A9 giao cho nó một DAG thật.

**Status:** ready-for-agent

## Vì sao sửa

Ba điều đã đo hoặc đã tra được, chi tiết ở báo cáo vòng 36:

1. **Mã hiện tại lặng lẽ chuyển sang xấp xỉ.** `_feedback_edges` vét cạn khi SCC có ≤ 16 cạnh nội bộ (đo: 16 cạnh
   hết 217 ms) và **rơi sang heuristic khi nhiều hơn** — D11 không nhắc tới nhánh đó. Viết "giải bằng vét cạn"
   trong báo cáo là câu sai. Nhánh xấp xỉ chưa từng chạy trên corpus hiện tại, nhưng nó tồn tại.
2. **Lý lẽ giữ chu trình hai cạnh dựa trên tiền đề sai.** Con số ~4% là đúng, nhưng tác giả bộ dữ liệu viết rằng
   các cặp ấy gợi ý nên **gộp thành một khái niệm** — không phải "quan hệ hợp lệ". Ca thật duy nhất của ta là
   **ERD ↔ Thiết kế Cơ sở dữ liệu**, một quan hệ bộ phận–toàn thể bị đoán ngược, nên gộp cũng sai.
3. **`confidence` gần như vô nghĩa.** Trên cả **327 cạnh** của bốn tài liệu nó chỉ nhận **ba giá trị** 0,7 · 0,8 ·
   0,9. Văn liệu đo AUROC của độ tin cậy mô hình tự khai ở mức 51,3–62,7 trên năm mô hình.

## Việc phải làm

- [ ] **V3 — MFAS có trọng số, giải chính xác.** Liệt kê chu trình đơn trong SCC → giải phủ tập hợp có trọng số →
      chỉ rơi về heuristic tuyến tính khi vượt ngân sách, và **artifact ghi nghiệm là `approximate`**.
- [ ] **Ngân sách đặt theo số chu trình đơn, không theo số node hay số cạnh.** Một SCC 27 node / 60 cạnh có 2⁶⁰
      tập con cạnh nhưng chỉ 177 chu trình đơn — khoảng cách ấy chính là lý do đổi thuật toán.
- [ ] **Trọng số giữ cạnh:** loại bằng chứng → thuận thứ tự trình bày → số nguồn độc lập, mã hoá theo bậc cơ số để
      tiêu chí trước luôn trội. **Bỏ `confidence`.** Phá hoà cuối bằng khoá cạnh theo thứ tự từ điển.
- [ ] Artifact ghi thêm cho mỗi SCC đã xử lý: số chu trình đơn, phương pháp (`exact` / `approximate`), tổng trọng
      số đã gỡ.
- [ ] **V4 — cặp hai chiều.** Đưa **ra khỏi** đồ thị con `requires`; sinh cờ `suspected_relation_type_error` mang
      hai node, cả hai cạnh, bằng chứng từng chiều và lý do. Không tính vào cổng, không tính vào mật độ, không vào
      lộ trình. Người duyệt phán một chiều đúng thì chiều ấy quay lại qua đường xử lý tồn đọng đã có.
- [ ] **V5 — cố định thứ tự tám bước** và ghi thành assertion. Đánh dấu bắc cầu **phải** chạy sau khi hết chu trình.
      Giữ nguyên **đánh dấu, không xoá**; bổ sung lý do thống kê vào phần biện minh (cạnh nhiễu ít bị bắc cầu hàm ý
      hơn cạnh thật, nên xoá cạnh thừa sẽ ưu tiên xoá cạnh đúng).
- [ ] **V6 — cổng chất lượng.** Tử số đếm cạnh **không mang `redundant_via`**. Hạ ngưỡng xuống mức chỉ bắt lỗi
      pipeline chết (đề xuất 0,15 cạnh/node và 85% cô lập; vé chốt con số và ghi lý do). Manifest **luôn** ghi đủ
      số đo kể cả khi cổng mở. Cổng đóng thì sinh cảnh báo đọc được, **không** im lặng đổi chế độ.
- [ ] **V10 — đổi cách gọi tên** trong spec, artifact và thông điệp: A9 là **kiểm tra tính nhất quán cấu trúc**.
- [ ] **V11/F113** — kiểm hợp đồng của pass phụ phải kiểm **từng phần tử** của danh sách cờ. Hiện hai cờ rỗng `{}`
      trên `nhap-mon-ml` lọt vào trang duyệt thành `{"status": "unresolved"}` không ai xử lý được.
- [ ] Chạy lại A9 cho bốn tài liệu phát triển, **dán số trước/sau**: số cạnh, số cạnh thừa, cờ, kết quả cổng.
- [ ] Test ở seam đã có (`tests/unit/domain/test_global_validation.py`).

## Ca test phải có

- Một SCC mà nghiệm tối ưu là gỡ **hai cạnh rẻ** thay vì **một cạnh đắt** phải cho ra hai cạnh rẻ. Đây là ca phân
  biệt MFAS **có trọng số** với MFAS **đếm cạnh**, và luật hiện tại sẽ đỏ ở ca này.
- Vượt ngân sách chu trình → artifact ghi `approximate`.
- Cùng đầu vào cho cùng đầu ra qua nhiều lượt.
- Cặp hai chiều không có trong cạnh `requires` đầu ra; cờ mang đủ hai cạnh và bằng chứng; cổng không đổi vì nó.
- Sau A9, đồ thị con `requires` **không còn SCC nào lớn hơn một node**.
- Đồ thị mà **mọi** cạnh đều thừa thì **không** qua cổng.
- Manifest có đủ số đo cổng kể cả khi cổng mở.

Đột biến tối thiểu: quay về đếm cạnh thay vì tổng trọng số; đưa `confidence` trở lại trọng số; giữ cặp hai chiều
trong `requires`; đảo thứ tự bước 5 và 6; đếm cả cạnh thừa vào tử số cổng; bỏ cảnh báo khi cổng đóng; bỏ nhãn
`approximate`.
