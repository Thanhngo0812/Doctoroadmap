# Nhãn vàng tiên quyết bám văn bản, gán mù, chỉ dùng để kiểm

**Status:** accepted — 2026-09-16

Bộ vàng cho quan hệ tiên quyết được gán theo giao thức PREAP: hai người đọc chương và ghi quan hệ **trong lúc
đọc**, dựa trên cách tài liệu trình bày chứ không dựa vào kiến thức nền. Họ làm **mù** — file gán nhãn không chứa
cạnh nào của pipeline — và độc lập với nhau; độ đồng thuận được tính có kể đồng thuận ngầm qua bắc cầu, rồi hai
người hội ý các chỗ lệch để ra bộ vàng. Bộ vàng **chỉ dùng để kiểm**, chạy một lần; việc phát triển prompt làm
trên các tài liệu và chương khác.

**Considered Options**

- *Dùng bộ vàng tiên quyết có sẵn trong văn liệu.* Không hợp: các bộ phổ biến cho người gán dùng kiến thức nền,
  và một mô hình không đọc văn bản nào đã vượt baseline có giám sát trên chúng. Chấm 2b bằng bộ như vậy là thưởng
  cho đúng thứ 2b phải chặn, vì rubric 2b đòi bằng chứng trong tài liệu.
- *Để Claude gán, như bộ vàng A4.* Đủ cho vòng dev, nhưng không bảo vệ được trong một báo cáo thực nghiệm, và
  không cho biết trần chất lượng do con người đặt ra.
- *Gán mọi cặp thay vì chỉ ghi cặp có quan hệ.* PREAP đo được cách này cho đồng thuận thấp hơn hẳn và tốn thời
  gian hơn 29–43%.

**Consequences**

- Việc gán nhãn là **đường găng** của cả giai đoạn; công cụ gán và hướng dẫn phải xong trước phần chấm.
- Bộ vàng gắn với một phiên bản bảng node canonical; file gán nhãn mang ô phiên bản để lúc chấm biết nó khớp với
  artifact nào. Đổi cách gán thì phải gán lại từ đầu.
- Danh sách khái niệm lấy từ pipeline, nên mọi số P/R của 2b là **có điều kiện trên tập khái niệm đó**. Người gán
  đánh dấu node sai; các cờ đó vừa là dữ liệu sửa chữa, vừa là mẫu kiểm A4 trên tài liệu mới.
- Vì bộ vàng chỉ dùng một lần, mọi thay đổi sau khi thấy số phải được báo cáo tách riêng là thay đổi hậu kiểm.
