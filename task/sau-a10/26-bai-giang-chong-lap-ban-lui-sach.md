# SA-26 — Bài giảng: chống lặp ý, ghi lý do hỏng, `usage` đúng, `used_later` đúng chiều

**Nguồn chân lý:** [spec Pha B](../../doc/pha-b-spec.md), mục bài giảng (K1–K8, stream); vé [12](12-bai-giang-llm-kiem-va-cache.md),
[13](13-bai-giang-stream-tai-truoc.md); [báo cáo kiểm thử 2026-10-18](../../report/kiem-thu-pha-b-2026-10-18.md), mục 3.2, 4.
**Ai:** nhân viên · Claude kiểm · **Chi phí mô hình:** 0 USD (phát lại phản hồi đã ghi của nhóm 2) · **Chặn bởi:** nhân viên commit mã Pha B còn
dở · **Trạng thái:** ready-for-agent

**Sửa 2026-10-18, theo chủ dự án:** "bài giảng fallback sẽ ko bao giờ đc hiện cho user nên ko cần đầu tư cho nó quá". Vì vậy:
- bỏ phần làm sạch đường trích câu;
- bỏ phần "bản lùi sạch".

Cách xử lý khi bài hỏng hẳn sẽ chốt ở đợt tra hỏi tới. Trước khi chốt, giữ nguyên hành vi hiện tại, không sửa.

## Vì sao

Đọc 12 bài Gemini của lượt thật nhóm 2 thấy bốn lỗi ở đường LLM:
- **Lặp ý mà K6 không bắt.**
  - Bài doc-1 "Tập hợp" có 4 ý: ý 1 trùng ý 3, ý 2 trùng ý 4.
  - K6 hiện chỉ bắt khi một cụm 8 từ lặp ít nhất 3 lần trong cả JSON.
- **`usage` báo 0** ở mọi bài phải sửa lại hoặc rơi về bản lùi. Lý do: `_aggregate_usage` đọc khoá `promptTokenCount`, nhưng dòng sổ chi đã chuẩn hoá
  dùng khoá `input_tokens`.
- **Không ghi lý do hỏng.**
  - 5/12 bài hỏng cả hai lần sinh, mà không biết vì luật nào.
  - Khi bản lùi không còn được hiện cho người học, tỉ lệ hỏng này là lỗi người học thấy trực tiếp. Phải đo được lý do mới giảm được.
- **`used_later` đi ngược chiều.**
  - Mã gọi `traverse(node, "requires", "in")`, tức lấy các tiên quyết, thay vì khái niệm sau dùng tới nó.
  - Ca thật: xstk "Tỉ lệ tổng thể" có `used_later = ["Tổng thể"]`, mà "Tổng thể" chính là tiên quyết của nó.
  - Ca dò trên doc-1 "Định thức": chiều `in` ra "Ma trận con, Ma trận" là tiên quyết; chiều `out` ra "Ma trận phụ hợp, Định thức của tích hai ma trận, …".

## Cần làm

**1. Chống lặp ý.**
- **So từng cặp ý trong cùng bài,** kể cả ý đã stream. Hai ý có độ trùng vượt ngưỡng thì giữ ý đến trước.
  - Độ trùng dùng Jaccard trên 3-gram âm tiết sau chuẩn hoá, như `_duplicate` của quiz.
  - Ngưỡng đặt ở `BSettings`.
- **Ý trùng câu định nghĩa cũng bỏ,** vì câu định nghĩa đã hiện riêng.
- **Mỗi ý bị bỏ vì lặp được đếm vào K6.**
- **Bài còn dưới `lecture_min_explanations` ý sau khi bỏ lặp** thì đi nhánh K8 hiện có.

**2. Ghi lý do.**
- **Mỗi lần sinh ghi luật làm hỏng bài** (K1–K8), cùng số ý bị bỏ theo từng luật (K2 trích, K3 nhãn, K5 ký hiệu, K6 lặp, K7 ngoài sách).
- **Nơi ghi:** nhật ký hoặc dòng sổ chi của lần sinh đó, không thêm trường bắt buộc vào hợp đồng `lecture-1`.
- **Một lệnh tổng hợp đọc nhật ký này** để vé 12 và 21 báo số.

**3. `usage` đúng.** `usage` của bài bằng tổng các dòng sổ chi của mọi lần sinh cho bài đó (token và USD), ở mọi nhánh.

**4. `used_later` đúng chiều.**
- Lấy các khái niệm cần khái niệm này: cạnh `requires` có `source` là khái niệm này, tức `traverse(…, "out")`.
- Tối đa 3, ưu tiên khái niệm ở module gần nhất phía sau.

## Tiêu chí nghiệm thu

- [ ] Test với mô hình giả, mỗi cái thấy đỏ trên mã hiện tại rồi mới xanh:
  - hai ý diễn đạt khác nhau nhưng trùng nội dung (rút gọn từ bài "Tập hợp") thì ý sau bị bỏ, và K6 đếm 1. Sửa sai M9 của báo cáo kiểm thử phải đỏ;
  - bài sửa lại một lần thì `usage` bằng tổng hai dòng sổ chi;
  - bài hỏng cả hai lần thì `usage` bằng tổng các dòng sổ chi, và nhật ký ghi luật hỏng của từng lần;
  - đồ thị có A → B (A là tiên quyết của B) thì bài của A có `used_later` chứa B, còn bài của B thì không chứa A.
- [ ] Phát lại 0 USD 12 bài của nhóm 2 qua luật mới. Báo:
  - trạng thái trước và sau;
  - số ý bị bỏ theo từng luật;
  - `usage`;
  - **bảng lý do hỏng của 5 bài từng hỏng.** Bảng này là đầu vào cho đợt sửa prompt sau.
- [ ] Cache: đổi luật kiểm thì đổi khoá cache, để bài cũ có lỗi không được dùng lại.

## Ngoài vé

Năm việc không thuộc vé này:
- làm sạch đường trích câu: chủ dự án quyết không đầu tư; đường này chỉ còn dùng ở chế độ ngoại tuyến của trang xem thử và làm mốc thô ở vé 21;
- cách xử lý khi bài hỏng hẳn: chờ đợt tra hỏi;
- bài giảng gợi lại tiên quyết và gợi mở phần sau: chờ spec mới;
- đổi prompt sinh bài giảng;
- sửa neo sai của khái niệm (phía pha A).
