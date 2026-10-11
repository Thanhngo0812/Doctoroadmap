# Bàn giao bổ sung — D-01 bước 3, lượt A (2026-10-10, tối)

Tệp này áp dụng ngay cho phiên agentic đang gán lượt A. Đọc cùng [bàn giao bước 3](ban-giao-agentic-d01-buoc-3-2026-10-10.md) và
[hướng dẫn gán](huong-dan-agentic-gan-nhan-d01.md), bản 1.1. Mọi luật của bàn giao bước 3 vẫn giữ nguyên:
- chỉ đọc các tệp đầu vào được phép;
- không tra mạng;
- không tìm cách nhận ra nguồn sách, phiếu kiểm hay phiếu lặp.

## 1. Đọc bản 1.1 của hướng dẫn gán

Hướng dẫn gán vừa thêm ca khó 12 (mục 6) và ví dụ 10 (mục 7). Luật cũ không đổi.
- Từ lô kế tiếp, phiên chính và mọi subagent đọc hai mục này trước khi gán.
- Lời giao cho subagent kèm đường dẫn hướng dẫn gán bản 1.1, như các tệp đầu vào khác.
- Ghi vào `ghi-chu-A.md` số thứ tự (trong `phieu.jsonl`) của phiếu đầu tiên được gán theo bản 1.1.

## 2. Gán lại phiếu 1–240

Phiếu 1–240 được gán trước khi chia subagent và trước bản 1.1. Gán lại 240 phiếu này để cả lượt A đi cùng một quy trình.
- Dùng subagent mới, giao giống các lô khác: lô 8 phiếu, đủ tệp đầu vào, hướng dẫn bản 1.1.
- Subagent gán lại **không được thấy** nhãn cũ của các phiếu này. Không chép, không đối chiếu.
- Ghi kết quả vào tệp riêng, mỗi lô một tệp: `tmp/d01-gan-nhan/gan-lai-<từ>-<đến>.jsonl`, kèm ghi chú lô như các tệp `agent-*`. `luot` vẫn là
  `"A"`.
- **Không sửa, không xoá** các dòng cũ của phiếu 1–240 trong `nhan-A.jsonl`.
- Làm song song với phần chưa gán; không cần dừng việc đang chạy.

## 3. Gộp cuối lượt A

Khi mọi phiếu đã có nhãn, gộp như sau:
1. Tạo tệp mới `tmp/d01-gan-nhan/nhan-A-gop.jsonl`, theo thứ tự phiếu trong `phieu.jsonl`:
   - phiếu 1–240 lấy từ các tệp `gan-lai-*.jsonl`;
   - phiếu 241 trở đi lấy từ `nhan-A.jsonl` và các tệp `agent-*.jsonl`.
2. Giữ nguyên `nhan-A.jsonl` và mọi tệp lô. Không ghi đè tệp nào.
3. Kiểm `nhan-A-gop.jsonl` bằng script **không** có `--mot-phan`. Yêu cầu: đủ 65.525 cặp, ĐẠT, mã thoát 0. Lưu lệnh, kết quả và mã thoát vào
   `kiem-A.txt`.
4. Ghi vào `ghi-chu-A.md`:
   - tệp nguồn của từng khoảng phiếu;
   - ai gán từng khoảng: phiên chính hay subagent;
   - mốc bắt đầu áp bản 1.1 (mục 1).

## 4. Báo lại

Báo chủ dự án ở hai mốc:
- xong phần gán lại phiếu 1–240;
- có `nhan-A-gop.jsonl` đạt kiểm đầy đủ.
