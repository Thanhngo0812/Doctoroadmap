# SA-26 — Bài giảng: chống lặp ý, bản lùi sạch, ghi lý do hỏng, `usage` đúng

**Nguồn chân lý:** [spec Pha B](../../doc/pha-b-spec.md), mục bài giảng (K1–K8, bản lùi, stream); vé [11](11-bai-giang-khong-llm.md),
[12](12-bai-giang-llm-kiem-va-cache.md), [13](13-bai-giang-stream-tai-truoc.md); [báo cáo kiểm thử 2026-10-18](../../report/kiem-thu-pha-b-2026-10-18.md),
mục 3.2, 4.
**Ai:** nhân viên · Claude kiểm · **Chi phí mô hình:** 0 USD (phát lại phản hồi đã ghi của nhóm 2) · **Chặn bởi:** nhân viên commit mã Pha B còn
dở · **Trạng thái:** ready-for-agent

## Vì sao

Đọc 12 bài LLM và 10 bài trích câu ngày 2026-10-18 thấy năm lỗi:
- **Lặp ý mà K6 không bắt.** Bài doc-1 "Tập hợp" có 4 ý, ý 1 trùng ý 3, ý 2 trùng ý 4. K6 hiện chỉ bắt một cụm 8 từ lặp ≥ 3 lần trong cả JSON.
- **Bản lùi trộn ý LLM đã stream với câu trích.** xstk "Tỉ lệ tổng thể" có một ý lặp 3 lần. Bản lùi gộp ý của cả hai lần sinh với câu TextRank, và chỉ
  khử trùng khi giống hệt từng ký tự.
- **`usage` báo 0** ở mọi bài phải sửa lại hoặc rơi bản lùi. `_aggregate_usage` đọc khoá `promptTokenCount` trên dòng sổ chi đã chuẩn hoá, nơi khoá là
  `input_tokens`.
- **Không ghi lý do hỏng.** Vé 12 cần tỉ lệ bỏ ý theo từng luật và số bài rơi bản lùi theo luật; hiện không đo được.
- **Đường trích câu sinh ý rác (vé 11):**
  - mẩu vụn ở công thức có dấu chấm;
  - ý chỉ là `[formula]`;
  - gạch đầu dòng slide còn ký tự font ký hiệu (``, `u`, `❖`, ``);
  - câu cụt ở ranh giới chunk;
  - câu định nghĩa lặp lại làm ý đầu.

Đường trích câu là bản lùi của 5/12 bài trong lượt thật, nên lỗi của nó lộ ra cả ở bài LLM.

## Cần làm

**1. Chống lặp ý.**
- **So từng cặp ý trong cùng bài,** kể cả ý đã stream. Hai ý có độ trùng vượt ngưỡng thì giữ ý đến trước.
  - Độ trùng dùng Jaccard trên 3-gram âm tiết sau chuẩn hoá, như `_duplicate` của quiz.
  - Ngưỡng đặt ở `BSettings`.
- **Ý trùng câu định nghĩa cũng bỏ,** vì câu định nghĩa đã hiện riêng.
- **Mỗi ý bị bỏ vì lặp được đếm vào K6.**
- **Bài LLM còn dưới `lecture_min_explanations` ý sau khi bỏ lặp** thì đi đúng nhánh K8 hiện có: sinh lại một lần, rồi bản lùi.

**2. Bản lùi sạch.**
- Khi rơi về bản lùi, giữ các ý đã gửi qua stream. Không được rút lại ý đã gửi (vé 13).
- Chỉ thêm câu trích không trùng ý đã gửi, theo đúng luật ở mục 1.
- Ý của lần sinh lại cũng qua luật trùng với ý đã gửi.

**3. Ghi lý do.**
- **Mỗi lần sinh ghi luật làm hỏng bài** (K1–K8), cùng số ý bị bỏ theo từng luật (K2 trích, K3 nhãn, K5 ký hiệu, K6 lặp, K7 ngoài sách).
- **Nơi ghi:** nhật ký hoặc dòng sổ chi của lần sinh đó, không thêm trường bắt buộc vào hợp đồng `lecture-1`.
- **Một lệnh tổng hợp đọc nhật ký này** để vé 12 và 21 báo số.

**4. `usage` đúng.** `usage` của bài bằng tổng các dòng sổ chi của mọi lần sinh cho bài đó (token và USD), ở cả nhánh `ready` sau sửa lại và nhánh
bản lùi.

**5. Đường trích câu.**
- Tách câu bằng `UnicodeSentenceSplitter`, không bằng regex `(?<=[.!?])\s+`. Không cắt ở dấu chấm trong `{e1, …, em}` hay "…".
- Bỏ câu chỉ có dấu giữ chỗ (`[formula]`) hay có quá ít chữ, ngưỡng ở `BSettings`.
  - Chỗ có công thức thì dùng nhãn `⟦CTk⟧` đã có ảnh (vé 04), nếu bài có ảnh cho công thức đó.
- Bỏ ký tự gạch đầu dòng ở đầu dòng: ký tự vùng dùng riêng của font ký hiệu, `❖`, `•`, `▪`, và chữ `u` đơn lẻ trước khoảng trắng khi chunk là slide.
- Bỏ câu cụt ở cuối chunk (không có dấu kết câu) khi còn câu khác để chọn.
- Bỏ câu trùng câu định nghĩa.

## Tiêu chí nghiệm thu

- [ ] Test với mô hình giả, mỗi cái thấy đỏ trên mã hiện tại rồi mới xanh:
  - hai ý diễn đạt khác nhau nhưng trùng nội dung (rút gọn từ bài "Tập hợp") thì ý sau bị bỏ và K6 đếm 1 (sửa sai M9 của báo cáo kiểm thử phải đỏ);
  - bài rơi bản lùi sau khi đã stream 2 ý thì kết quả không có ý nào trùng nhau, và vẫn giữ 2 ý đã gửi;
  - bài sửa lại một lần thì `usage` bằng tổng hai dòng sổ chi;
  - bài rơi bản lùi thì `usage` bằng tổng các dòng sổ chi và nhật ký ghi luật hỏng;
  - năm lỗi trích câu, mỗi lỗi một ca rút gọn từ mẫu thật ở báo cáo kiểm thử, mục 3.2.
- [ ] Phát lại 0 USD 12 bài của nhóm 2 qua luật mới. Báo:
  - trạng thái trước và sau;
  - số ý bị bỏ theo từng luật;
  - `usage`.
- [ ] Chạy lại đường trích câu cho 915 khái niệm của sáu cuốn, 0 USD. Báo số câu bị lọc theo từng luật mới, và số bài còn dưới 2 ý.
- [ ] Đính kèm 10 bài trích câu mới, cùng 10 khái niệm như mẫu cũ, cho Claude đọc lại.
- [ ] Cache: đổi luật kiểm thì đổi khoá cache, để bài cũ có lỗi không được dùng lại.

## Ngoài vé

Bốn việc không thuộc vé này:
- đổi prompt sinh bài giảng;
- sửa neo sai của khái niệm (phía pha A);
- lượt thật đo giây của vé 13, chạy sau vé này;
- đánh giá chất lượng (vé 21).
