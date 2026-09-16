# 05 — Bộ chấm E1 và E2

**What to build:** Có bộ vàng và artifact ở stage `mentions` là chấm được ngay hai câu hỏi quyết định, **không
tốn lời gọi mô hình nào**: cạnh tiên quyết nằm ở đâu trong tài liệu (E1), và bộ sinh cặp nào giữ được cạnh vàng
với ít cặp nhất (E2).

Luật ở spec D14.

**Blocked by:** 03, 04. (Việc của Claude.)

**Status:** ready-for-agent

- [ ] E1: chia cạnh vàng theo sáu loại vị trí của D14, kèm NMI giữa cụm chủ đề và chương.
- [ ] E2: với từng bộ sinh và từng tổ hợp — số cặp, recall cạnh vàng, và **recall chỉ riêng nó có**. Gồm ba cấu
      hình định tuyến: chỉ trục chương, chỉ trục cụm, hợp cả hai.
- [ ] Chấm được cả **cạnh trực tiếp** lẫn **bao đóng bắc cầu**.
- [ ] Mọi chỉ số kèm khoảng tin cậy 95% bằng bootstrap lấy mẫu lại theo khái niệm đích.
- [ ] Không gọi mô hình; chạy được khi chặn mạng.
- [ ] Test trên một ví dụ dựng sẵn có đáp án tính tay; đột biến tối thiểu: nhầm chiều cạnh, bỏ bao đóng, bootstrap
      lấy mẫu theo cạnh thay vì theo khái niệm đích.
