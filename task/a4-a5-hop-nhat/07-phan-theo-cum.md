# 07 — Phán theo cụm

**What to build:** `a4` gửi mỗi cụm ứng viên cho mô hình **một lần**, nhận lại cách chia cụm thành node, các cạnh
`subtype_of` và danh sách `deferred`; code kiểm đầu ra rồi mới áp. Sau ticket này, bảng node canonical gộp được cả những
cặp khác tên mà lớp tên không bắt được — `Tranh chấp dữ liệu`/`Race Condition`, `WebSocket`/`WebSockets` — trong khi
anh em như `Mutex`/`Pessimistic Locking` vẫn là hai node.

## Vì sao mô hình không thấy draft và không được tự đọc chunk

- A3 hay viết **cùng một câu** cho mọi mục trong một danh sách, còn hai lần xuất hiện của cùng một khái niệm lại có
  draft khác nhau theo ngữ cảnh. Draft sai theo cả hai chiều; câu bằng chứng nguyên văn thì không (spec D4).
- Code biết trước ứng viên nào thiếu ngữ cảnh — câu bằng chứng không nhắc tên, đúng hàm của ticket 01 — nên đính kèm
  sẵn toàn văn chunk cho đúng những ứng viên đó, thay vì cho mô hình một tool và một vòng lặp (Q27).

**Blocked by:** 04 — Đồ thị đề cử và gom cụm ứng viên; 01 — Hai cảnh báo trả về A3

**Status:** done

**Cập nhật triển khai 2026-09-11:** Đã triển khai và test mô hình giả, retry/deferred/subtype. Theo chủ dự án, model tạm dùng gemini-3.1-flash-lite; chưa gọi phán thật trước task 06.
Chi tiết kiểm chứng và phần chưa hoàn tất: [feedback A4/A5](../../feedback/F18-a4-a5-hop-nhat.md).

- [x] **Đầu vào**, cho từng nhóm trong cụm: tên, alias (tên gọi + viết tắt), ký hiệu, `node_type` của các thành viên,
      `section_path`, tối đa 3 câu bằng chứng nguyên văn theo thứ tự tài liệu. Ứng viên có câu bằng chứng không chứa
      tên/alias/ký hiệu (hàm của ticket 01) ⇒ kèm **toàn văn chunk nguồn**. Các nhóm xếp theo thứ tự tài liệu.
- [x] `description_draft` **không** xuất hiện trong dữ liệu gửi đi — có test khẳng định điều này.
- [x] Mỗi cụm là một phiên một lượt qua **cổng hội thoại LLM hiện có**; không tool. Khung prompt tiếng Anh, dữ liệu giữ
      nguyên ngôn ngữ tài liệu. Rubric năm nhãn: cùng · cha–con · anh em / liên quan · khác · không chắc; phân vân thì
      không gộp.
- [x] Model của bước phán cấu hình **riêng**; A/B chốt `gemini-3.1-flash-lite`. Model, tham số sinh, khung prompt và
      schema vào `prompt_hash` và config hash, cùng khuôn A3.
- [x] **Code kiểm đầu ra**: phân hoạch phải có mọi nhóm đúng một lần; sai ⇒ thử lại **một lần** kèm id cụ thể, vẫn sai
      ⇒ cả cụm `deferred`. Sau đó kiểm riêng từng `subtype_of`; cạnh nối cùng node hoặc trích chunk sai bị loại và ghi
      `subtype_rejected`, không làm mất phân hoạch hợp lệ.
- [x] **Áp kết quả**: nhóm chung node ⇒ gộp, rồi tính lại tên chuẩn, alias, ký hiệu, kiểu và id neo bằng đúng các luật
      của ticket 02. `subtype_of` ⇒ cạnh kiểu mở kèm lý do và bằng chứng, ghi sổ đăng ký kiểu. `deferred` ⇒ các nhóm
      để riêng, gắn cờ và lý do.
- [x] Bước này **không bao giờ** sinh `requires`: trọng tài giả cố tình trả một cạnh `requires` thì bị luật kiểm từ chối
      (test).
- [x] Ánh xạ cạnh của ticket 03 chạy lại trên bảng node sau gộp.
- [x] **Nhật ký**, mỗi cụm: đầu vào, đầu ra, lý do, model, `prompt_hash`, băm dữ liệu gửi đi, số lần thử lại và mọi
      đầu ra bị từ chối trong `attempts`.
- [x] **Manifest**: số cụm đã phán, số node gộp thêm, số nhóm `deferred`, số lần thử lại, số cụm `deferred` vì sai
      định dạng; chép hai cảnh báo A3 (ticket 01) của tài liệu vào manifest.
- [x] **Seam ①** với trọng tài giả viết tay (bảng nhóm → node cố định), không chạm mạng, mỗi nhánh thấy hỏng khi bỏ
      guard tương ứng:
    - gộp đúng theo bảng; `subtype_of` đúng chiều;
    - trả *không chắc* ⇒ `deferred`, không gộp;
    - sai định dạng một lần rồi đúng ⇒ vẫn gộp;
    - sai định dạng hai lần ⇒ cả cụm `deferred`;
    - bỏ sót hoặc lặp một nhóm ⇒ bị bắt như sai định dạng.
- [x] Nhóm không nằm trong cụm nào đi thẳng thành node, không phát sinh lời gọi (test đếm lời gọi).
- [x] Toàn bộ test hiện có vẫn xanh.
