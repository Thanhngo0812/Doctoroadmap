# Trạng thái dự án lúc tạm dừng (2026-10-05, trước khi nén ngữ cảnh)

Bản lưu để phiên sau nối tiếp. Kế hoạch sống của v4 ở [task/v4/00-ke-hoach.md](../task/v4/00-ke-hoach.md).

## Quyết định mới của chủ dự án (2026-10-05)

Chủ dự án chốt hai việc lớn:
- **Đồ án chuyên ngành đổi phạm vi: chỉ hỗ trợ tài liệu tiếng Việt** (trước đây là mọi ngôn ngữ). Luật đa ngôn ngữ không còn ràng buộc luồng
  chính; được dùng công cụ và mẫu riêng tiếng Việt. Mã đa ngôn ngữ đã có không cần gỡ.
- **Pass phụ A8 không dùng LLM nữa, cho cả đồ án chuyên ngành lẫn seminar.** Phải nghiên cứu và triển khai bản thay thế bằng ML/DL. Luồng LLM
  cũ giữ lại làm mốc so sánh (và làm thầy để chưng cất nhãn). Các khâu khác của đồ án vẫn dùng LLM; seminar vẫn là cả Pha A không LLM.

Tài liệu tham khảo chủ dự án vừa thêm vào `doc/` (soạn hồi viết spec-addendum/spec-review, **không phải chân lý**, luồng hiện tại đã lớn hơn):
- [doc/pipeline-seminar-chuan-V1-V13-v2.md](../doc/pipeline-seminar-chuan-V1-V13-v2.md)
- [doc/luong-moi-pipeline-agent-final-v2.md](../doc/luong-moi-pipeline-agent-final-v2.md)
Phiên sau đọc hai tệp này khi thiết kế pass phụ không LLM, đối chiếu với nghiên cứu R-02.

## Việc đang dở

- **Pass phụ không LLM (việc chính kế tiếp):**
  - Nền nghiên cứu: [R-02](nghien-cuu-ml-dl-loc-cap-va-tien-quyet-2026-10-04.md). Mục tiêu đổi từ "bộ lọc trước LLM" sang "thay hẳn LLM".
  - Bước đầu 0 USD: thí nghiệm E0–E6 của R-02 (dựng bảng cặp × đặc trưng × phán quyết LLM từ nhật ký tám tài liệu; GBDT/hồi quy logistic,
    để riêng từng tài liệu; phát lại A9→A10 trên cạnh dự đoán; chấm vàng doc-1, doc-2, xstk, doc-4).
  - Phải giải bài toán câu trích: hợp đồng vé 12 đòi cạnh cứng có câu trích nguyên văn trong cửa sổ định nghĩa của đích. Mô hình không LLM có
    thể lấy câu trong cửa sổ có nhắc tên tiên quyết làm câu trích; cặp không có tên trong cửa sổ cần quyết riêng.
  - Chưa chốt: mục tiêu recall (Claude đề nghị ≥ 0,99 trên cạnh cứng, để riêng từng tài liệu ra đo; kiểm mẫu khoảng 500 lời gọi mỗi cuốn mới).
    Với hướng thay hẳn LLM, cần đặt lại chỉ tiêu theo chất lượng đồ thị so với luồng LLM và vàng người.
- **Vé v4-01 (hỏi lười pass phụ):** mã đúng, phát lại 5 tài liệu y hệt (Claude tự phát lại xstk: −35% lời gọi), 843 test xanh. Chưa đóng:
  - nhân viên phải thêm mẫu theo dõi 3% luôn hỏi đủ hai thứ tự;
  - Claude **chấp nhận** câu nghiệm thu cờ rộng hơn (cờ được giảm khi thứ tự đầu hợp lệ, không tạo cạnh, thứ tự sau cũ lỗi) — ghi vào vé;
  - nhân viên **chưa commit** mã v4-01/02; nhắc commit rồi Claude ghi nghiệm thu vào vé.
  - Lưu ý: nếu pass phụ chuyển hẳn sang ML/DL, v4-01 chỉ còn giá trị cho luồng LLM dùng làm mốc so sánh.
- **Vé v4-02 (đo thời gian):** phần nhân viên đạt (dry-run giữ cache). Phần Claude xong: `scripts/do-chi-phi/bao_cao.py` (commit `1f68209`).
- **Vé v4-10 (đo A1 tại máy):** script `scripts/thu-a1/do_a1.py` (commit `57eea8d`). Lượt đo bị dừng giữa chừng; kết quả có được ở
  `tmp/thu-a1/ket-qua/`: slide Naive Bayes, 20 trang, mốc 135,3 giây (6,8 giây/trang), 8 luồng 113,8 giây (nhanh 1,19 lần). Chưa đo tắt
  OCR, mốc lần 2, doc-1, xstk, doc-4. Chạy lại lệnh `do_a1.py --trang=20 --ra=tmp/thu-a1/ket-qua` lúc máy rảnh (script chưa bỏ qua cấu hình
  đã có; nên thêm).
- **Chấm mù tập giữ lại (T15):** bảng `artifacts/a8-gold/cham-mu-giu-lai-{xstk-ch3-1,doc-4}.xlsx` chờ hai người chấm; xong thì viết báo cáo
  tổng kết v3.
- **Tập giữ lại v4 (T-01):** chủ dự án chọn 2 tài liệu tiếng Việt mới và người gán vàng.

## Kết quả đã có (tóm tắt)

- v3 xong: [kết quả tập giữ lại](ket-qua-tap-giu-lai-v3-2026-10-04.md) — tổng quát hoá một phần.
- Nghiên cứu v4: [tiền và thời gian](nghien-cuu-v4-chi-phi-thoi-gian-2026-10-04.md), [R-01 Gemini](nghien-cuu-v4-gemini-va-rut-gon-ngu-canh-2026-10-04.md),
  [R-02 ML/DL](nghien-cuu-ml-dl-loc-cap-va-tien-quyet-2026-10-04.md), [R-03 A1](nghien-cuu-v4-a1-docling-2026-10-04.md).
- Mốc chi phí v3: doc-4 trọn cuốn khoảng 50 USD, pass phụ 91%. Developer API bậc 1 trần 250 USD/tháng; 3.1 Flash-Lite tắt sớm nhất 2027-05-07.
