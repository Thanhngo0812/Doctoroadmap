# 15 — Embed mô tả thực thể và media

**What to build:** Mọi thực thể và media có vector, sẵn sàng cho hai việc của đợt sau: **blocking merge**
ở 2a, và tra cứu ngữ nghĩa của gia sư pha B.

Đây là điểm hội tụ hai ray của đợt.

## Bốn thời điểm embed — ticket này làm ② và ③

```
① EMBED CHUNK (233)              ticket 13
② EMBED description_draft        ticket này  ->  blocking merge 2a  [đợt sau]
③ EMBED mô tả media (79)         ticket này  ->  get_media_for_concept  [pha B]
④ EMBED description chuẩn        đợt merge, sau A5
```

**Hàng rào đồng bộ trước ②:** 2a gom cụm trên pool ứng viên **toàn tài liệu**, không phân theo chương —
mọi lần xuất hiện của cùng khái niệm ở chương 3, 5, 8 phải nằm trong một cụm để một agent nhìn thấy hết.
Nên không thể embed nháp theo từng chương rồi merge dần: chương 8 chưa trích thì chưa biết khái niệm ở
chương 3 có bạn hay không.

## Vì sao embed hai lần chứ không một

Bản nháp viết từ **một section** nên thiếu — `Overfitting` định nghĩa ở chương 2, cho ví dụ ở chương 5,
so sánh ở chương 8. Nhưng blocking **cần vector trước khi merge**. Gỡ bằng cách chấp nhận blocking chạy
trên bản thiếu, vì hai việc đòi chất lượng khác nhau:

- **Blocking** cần recall thô — *"hai cái này có thể là một không?"* Bản nháp đủ.
- **Cạnh ngữ nghĩa, mention map, tra cứu pha B** cần mô tả đã hợp nhất đủ nguồn ⇒ đó là ④, đợt sau.

Phân tầng artifact ở ticket 09 tự nó là chỗ chứa đúng cho hai bản: nháp ở `candidates`, chuẩn ở
`canonical`. Không ghi đè, không mất dấu.

## Media đi đường khác

Node `figure`/`table` **không có bản chuẩn** — mô tả chốt tại A3 (chú thích gốc hoặc mô tả đa phương
thức). Cho bước sau viết lại nghĩa là để mô hình suy diễn nội dung ảnh từ văn bản xung quanh, đúng ảo
giác mà ticket 05 sinh ra để chặn.

> **Hệ quả phải ghi vào ADR:** embedding quyết định **blocking merge**, nên đổi mô hình embedding là
> **đổi tập node** — cặp nào lọt vào cùng cụm đổi ⇒ merge đổi ⇒ cluster đổi ⇒ mention map đổi. Bán kính
> rộng hơn nhiều so với "tìm kiếm hơi khác". Đây là lý do `embedding_model_id` phải ghim một chỗ duy nhất.

**Blocked by:** 13 — cần cổng embedding. 08 — cần ứng viên toàn tài liệu để embed.

**Status:** done

- [x] `description_draft` của mọi thực thể học được được embed qua **đúng cổng của ticket 13**
- [x] Mô tả 79 media được embed qua cùng cổng đó
- [x] Embed nháp chạy **sau hàng rào** — đủ toàn tài liệu, không theo từng chương
- [x] Vector nháp lưu ở tầng `candidates`; ghi rõ trong manifest đây là bản **nháp**
- [x] `embedding_model_id` ghi vào manifest artifact
- [x] Có test: thực thể không có `description_draft` ⇒ bỏ qua kèm cảnh báo, không lỗi
- [x] Có test: media không có mô tả (`caption_source: none`) ⇒ bỏ qua kèm cảnh báo
- [x] Ghi số thật: bao nhiêu vector cho mỗi loại, tổng bao nhiêu
- [x] Viết ADR ghi hệ quả **"đổi mô hình embedding là đổi tập node"**
