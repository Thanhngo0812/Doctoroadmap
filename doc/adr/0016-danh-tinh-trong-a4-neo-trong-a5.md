# Danh tính nằm trong gộp thực thể ở A4; neo và trạng thái dạy quyết ở A5

**Status:** accepted — 2026-10-17 · thay luồng provenance → neo C8 (A9′) → danh tính (A9″) của spec v2/v3 · cập nhật ADR 0004

Trước đây, sau A5 mỗi cuốn còn đi qua ba stage LLM nối tiếp rồi mới tới A8: provenance, neo C8 và danh tính. Từ nay chuỗi mặc định
(`upstream_chain=gop`) gom cả ba vào stage canonical. Stage này còn hai bước:

1. **A4 gộp thực thể, kiêm luôn danh tính.** Kết quả là tập node canonical cuối, không còn bản đồ danh tính.
   - **Đề cử cặp nghi trùng** từ alias, độ giống chuỗi của tên, láng giềng theo vector tên, và ba nguồn trước đây chỉ danh tính dùng:
     - tên hoặc alias trùng nhau sau chuẩn hoá;
     - viết tắt theo chữ đầu;
     - hai tên khác nhau đúng một tiền tố chung chung.

     Đề cử vẫn chỉ là đề cử (ADR 0006).
   - **Phán theo tiêu chí cùng ngoại diên**, trên câu bằng chứng nguyên văn của A3. Quan hệ "trường hợp riêng" thì giữ tách và ra quan hệ đề xuất.
   - **Cặp gộp khác tên** phải qua một lời xác minh độc lập. Chỉ quan hệ `dong_nhat` giữ gộp.
   - **Hai nhóm có tên trùng sau chuẩn hoá thì buộc gộp.** Chuẩn hoá gồm NFKC, bỏ dấu LaTeX và gộp gạch nối. Luật này chỉ mở rộng phép chuẩn hoá
     trong luật "code chỉ gộp tên trùng khít" của ADR 0006, không gộp theo độ giống. Alias không được buộc gộp.
   - **Chia cụm tất định.** Thành phần có mâu thuẫn bắc cầu chỉ giữ gộp cho các cặp chung tên sau chuẩn hoá.
   - **Quyết định của người duyệt** nạp ở A4 (`a4 --merge-review`) và thắng phán của mô hình.
2. **A5 viết mô tả, rồi quyết câu neo và trạng thái dạy, mỗi khái niệm một lời gọi** (`anchor_batch_mode=single`). Luật giữ như C8:
   - mã dựng tối đa 6 câu ứng viên;
   - phán một trong 6 trạng thái;
   - `prior_knowledge` phải qua một lời xác minh;
   - khái niệm không có câu ứng viên trong vùng nội dung thì mã tự xếp, không gọi mô hình.

   Chunk chứa câu neo được thêm vào `defining_chunk_ids` theo luật chỉ thêm. Vì vậy chuỗi không cần stage provenance nữa.

Id node vẫn theo ADR 0005: id biến mất được ghi vào bảng chuyển hướng.

**Căn cứ**
- **Quyết định của chủ dự án:**
  - 2026-10-12: gộp danh tính vào A4 (phương án 1 trong ba phương án);
  - 2026-10-16: chuỗi gộp thành mặc định mà không chờ T-01, vì ba stage cũ kéo dài thời gian mỗi cuốn và làm luồng khó trình bày.
- **Ba stage cũ chủ yếu làm lại việc của thượng nguồn.**
  - Câu neo của C8 trùng câu bằng chứng A3 ở 88,6% khái niệm.
  - Provenance chỉ quyết định 3% số neo.
  - Trên ba tài liệu phát triển, danh tính chỉ gộp thêm 20 nút, trong đó ít nhất 3 lần gộp sai theo vàng.
- **Cổng 19l** chạy trên 6 tài liệu, mã ở commit `f4871fd`:
  - neo ở đích vàng giữ cùng trạng thái dạy ở 25/26, 26/26 và 47/47, bằng mốc;
  - gộp sai mà vàng phát hiện còn 1, so với 3 ở v3;
  - doc-4 trước A8 tốn 1.108 lời gọi, 0,88 USD; chuỗi v3 tốn 2.295 lời, 1,367 USD.

  E4 lệch dưới dải nhiễu của 19j. Đọc từng chỗ lệch thì doc-1 và doc-4 là nhiễu do đầu vào đổi, còn xstk là lỗi neo đã biết (vé 05). Chi tiết ở
  [báo cáo cổng](../../report/v4-19l-cong-doi-mac-dinh-2026-10-17.md).

**Considered Options**

Các phương án dưới đây đã đo và bị loại. Phần mã của chúng gỡ ở vé 19o.
- ***Neo gom vào lời gọi A5.***
  - Bớt lời gọi nhưng không bớt tiền, vì mỗi lời A5 gộp mang câu ứng viên của nhiều khái niệm.
  - Phán "được dạy" lỏng hơn C8. Ở doc-4, 67 khái niệm đổi từ "chỉ nhắc" sang "được dạy"; neo một khái niệm chỉ có 9 trường hợp như vậy. Đọc mẫu
    12 khái niệm thì khoảng 9 thật ra chỉ được nhắc, và dãy học dài thêm 60 khái niệm.
  - Nó tình cờ sửa được ba đích xstk bị A2 gắn nhầm "đề cương", nhưng chỗ sửa đúng là vé 05.
- ***Đề cử theo mô tả nháp*** (vector A3 đã lưu, top-3, cosine ≥ 0,85).
  - Trên 4 tài liệu, khoảng 720 cặp chỉ có nguồn này. Chúng ra 4 lần gộp, trong đó 1 lần đúng.
  - Nguồn này sinh phần lớn lời phán sửa, làm doc-4 đắt hơn v3 60%.
- ***Gom lô lời phán sửa*** (10 cặp một lời).
  - Mô hình né gộp đồng nghĩa và bản dịch: trên nhap-mon-ml, lô gộp lại được 1/5 cặp mà v3 có, hỏi từng cặp thì được 5/5.
  - Tiền gần bằng nhau (0,094 so với 0,111 USD), vì token vào chiếm phần lớn.
- ***Nguồn đề cử `same_evidence` và lời phán sửa cho cạnh cắt chỉ có `ngram`*** (bỏ ở vé 19b).
  - `same_evidence` không tạo lần gộp nào trong 13 canonical.
  - Bỏ phán sửa cạnh cắt chỉ có `ngram` không mất lần gộp nào.
  - Trên doc-4, hai loại này tốn khoảng 228 lời phán sửa.
- ***Giữ chuỗi v3.*** Chất lượng tương đương, nhưng thêm ba lượt chờ và một bước gộp thực thể thứ hai.
- ***Cờ "dạy ở đây" trong A3.*** Đổi prompt A3 làm mất cache A3 của mọi tài liệu. Hơn nữa, trạng thái dạy là kết luận trên cả tài liệu, còn A3 chỉ thấy
  một cửa sổ.

**Consequences**
- **Id node đổi** khi khái niệm bị gộp thêm hoặc đổi ứng viên neo. Bảng chuyển hướng nối id cũ sang id mới.
  - Khi chấm, vàng cũ được quy id qua bảng này (vé 17h). Bộ không quy trọn thì để riêng.
  - T-01 đo trên chuỗi gộp khi có vàng.
- **Artifact chuỗi gộp không có `identity_map`.** A8, A10, bộ chấm và Pha B vẫn đọc được artifact v3 cũ; thiếu `identity_map` được hiểu là bản đồ rỗng.
- **Lệnh `roadmap` đi theo chuỗi của canonical mới nhất.** Chạy `a4` mặc định trên một tài liệu cũ sẽ đổi chuỗi của lần `roadmap` sau. Chuỗi gộp không
  dùng `--stop-after provenance|teaching|identity` và `--identity-review`.
- **Canonical chỉ lớp tên** (`a4 --names-only` / `--prepare`, dùng cho D-01) vẫn chạy chuỗi v3. D-01 đóng băng.
- **Pass phụ ML** (ADR 0015) đọc chunk định nghĩa đã có thêm chunk neo, thay cho chunk do provenance vá, nên phân bố đặc trưng lệch.
  - Ở cổng, doc-4 tốt hơn mốc 18d. doc-1 và xstk thấp hơn ở Q7b và chỉ số bao đóng; đọc từng chỗ thì do nhiễu đầu vào và lỗi neo đã biết.
  - Chỉ học lại E5 khi T-01 cho thấy tụt rõ.
- **Cache bài giảng và quiz Pha B cũ mất hiệu lực**, vì id node và ngữ cảnh đã lắp đều đổi.
- **Muốn thay LLM ở gộp thực thể hay ở phần neo** (hướng seminar), chỉ phải thay đúng một bước trong stage canonical.
- **Lỗi còn lại:** neo một khái niệm vẫn xếp "chỉ nhắc" cho khái niệm được dạy dưới mục mà A2 gắn nhầm vai trò. Ở cổng, xstk mất 3 khái niệm vì lỗi
  này. Sửa thuộc vé 05.

**Cập nhật 2026-10-17 (vé 19n, 19o):** chuỗi v3 đã gỡ khỏi mã.
- Không còn tuỳ chọn chọn chuỗi (`upstream_chain`) hay chế độ neo (`anchor_batch_mode`). A4 đầy đủ luôn là chuỗi gộp và neo mỗi khái niệm một lời.
  Artifact vẫn ghi `upstream_chain: gop` để bộ đọc nhận dạng.
- Ba stage cũ, `--stop-after provenance|teaching|identity` và `--identity-review` đã gỡ. `roadmap` gặp canonical v3 thì yêu cầu chạy lại A4.
- Ba phương án bị loại ở trên cũng đã gỡ khỏi mã.
- A8, A10, bộ chấm và Pha B vẫn đọc trực tiếp artifact v3 có `identity_map`. Muốn dựng lại một stage cũ thì dùng checkout của `2c93c5a`.
