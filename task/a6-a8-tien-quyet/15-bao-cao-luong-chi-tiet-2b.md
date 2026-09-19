# 15 — Báo cáo luồng chi tiết 2b

**What to build:** Một báo cáo mô tả **luồng thật** của tầng 2b sau khi chạy trên tài liệu thật, theo mẫu
[`report/luong-chi-tiet-agent-2a.md`](../../report/luong-chi-tiet-agent-2a.md). Đây là tài liệu spec D16 bắt buộc có
mà đợt cắt vé đầu bỏ sót.

Khác vé 14: vé 14 là **báo cáo thực nghiệm** (E1–E8, số đo, khoảng tin cậy, đóng góp). Vé này là **báo cáo luồng**:
đi từ một chunk tới một cạnh `requires`, qua đúng những bước code thật chạy, để người đọc sau này sửa được hệ thống.

**Blocked by:** 13 (cần số của lượt chạy thật cuối). Viết nháp được ngay sau vé 11. (Việc của Claude.)

**Status:** ready-for-agent

- [ ] Đi hết một ví dụ thật từ đầu tới cuối: một khái niệm đích, phiên nào chứa nó, prompt nhận gì, mô hình trả gì,
      executor xử ra sao, cạnh vào nhật ký nào, và cuối cùng nằm ở tầng nào của lộ trình.
- [ ] Mô tả sáu stage của tầng `graph` (`clusters`, `mentions`, `provenance`, `edges` ×2, `validated`, `stages`):
      đầu vào, đầu ra, khoá cấu hình, có gọi mô hình hay không, và artifact nào đọc artifact nào.
- [ ] Ghi rõ **bảy luật executor** của D9 và mỗi luật loại bỏ bao nhiêu thao tác trên dữ liệu thật.
- [ ] Ghi rõ luật chọn chiều, `evidence_kind` → confidence, luật cạnh ngược thứ tự tài liệu và mức trừ.
- [ ] Ghi cách pass phụ chọn cặp, hai hồ sơ đảo, luật hoà giải, và luật tỉa — kèm số thật.
- [ ] Ghi tầng 3: giải chu trình theo thành phần liên thông mạnh, chu trình hai node, cổng chất lượng, đánh dấu cạnh
      thừa — kèm số thật.
- [ ] Ghi các điểm **đã biết là yếu**: provenance mở đề so với chunk định nghĩa (F105/F106), cạnh bằng chứng mềm
      (`evidence_hard = false`), stage cỡ 1 khái niệm của A10.
- [ ] Mỗi khẳng định trỏ về spec hoặc về số đo, không mô tả theo trí nhớ.
