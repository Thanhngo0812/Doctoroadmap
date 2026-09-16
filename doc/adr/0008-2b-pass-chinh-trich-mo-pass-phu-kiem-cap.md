# 2b: pass chính trích mở, pass phụ chỉ kiểm cặp, không tool

**Status:** accepted — 2026-09-16

Ở tầng 2b, **pass chính trích mở**: mỗi (siêu) section của chương, hoặc mỗi cụm chủ đề, là một lời gọi duy nhất;
mô hình đọc văn bản và tự đề xuất cạnh `requires` giữa các khái niệm **trong danh sách của phiên**, được hỏi theo
từng khái niệm đích kiểu PREAP. **Pass phụ chỉ kiểm cặp**: nó chỉ phán các cặp nghi tiên quyết do code đề cử, và
không được tạo cạnh ngoài hồ sơ. Không phiên nào dùng tool: danh sách khái niệm do mention map lo, văn bản đã bơm
sẵn, và chu trình giải ở tầng 3 chứ không chặn đồng bộ lúc thêm cạnh.

**Considered Options**

- *Kiểm cặp ở mọi lượt.* Văn liệu ủng hộ hướng này: hỏi từng cặp cho precision cao, và mọi cạnh truy được về một
  bộ sinh, nên đo được recall của bộ sinh. Cái giá là recall của 2b bị chặn cứng bởi bộ sinh, và mô hình mất cơ
  hội dùng mạch trình bày của cả đoạn văn.
- *Trích mở ở mọi lượt.* Rẻ và tự nhiên, nhưng văn liệu đo được mô hình rải quan hệ tiên quyết khi trích mở
  (25–45% quan hệ trích ra), và không có bộ sinh nào để đo.
- *Agent loop có tool như `spec-preview`.* Bị loại vì khó cache và khó phát lại, trong khi tái lập là thứ báo cáo
  thực nghiệm của đợt này cần.

**Consequences**

- Recall của pass chính **không** bị bộ sinh chặn, nên E2 chỉ đo được **trần** của nhánh chương: bao nhiêu cạnh
  vàng có cả hai đầu trong cùng một danh sách phiên.
- Có cả hai chế độ trong một pipeline nên so được chúng trên cùng bộ vàng (thí nghiệm E6). Luật đổi mặc định viết
  trước: chuyển sang kiểm cặp khi nó hơn **≥ 0,05 F1**, khoảng tin cậy của hiệu không chứa 0, và recall không
  thấp hơn.
- Vì không chặn chu trình lúc thêm cạnh, các phiên ghi đề xuất vào một nhật ký chỉ-thêm và một bộ gộp tất định
  áp chúng; kết quả không phụ thuộc phiên nào chạy xong trước.
- 2b **chỉ sinh `requires`**; quan hệ kiểu mở vẫn là việc của 2a (ADR 0007). Đây là chỗ hẹp hơn `spec-addendum`
  §494.
