# 03 — Ba giai đoạn: trích → quét lại → kiểm định

**What to build:** Một section đi qua **một hội thoại ba giai đoạn** thay vì một lời gọi. Kết quả: bắt
được khái niệm nằm giữa đoạn mà lượt đầu bỏ sót, và loại được thứ chỉ *được nhắc* khỏi thứ thật sự
*được giảng*.

## Vì sao ba giai đoạn

**Recall của A3 là trần cứng cho toàn bộ lộ trình** — khái niệm sót ở đây không bao giờ quay lại: merge
chỉ gộp cái đã có, suy luận cạnh chỉ nối cái đã có. GraphRAG dựng hẳn cơ chế quét lại vì *"LLM không
trích hết trong một lượt"*.

```
1. TRÍCH      -> thực thể + cạnh đề xuất, mỗi thứ kèm câu trích
2. QUÉT LẠI   -> "còn gì chưa liệt kê?"  ·  dừng khi một vòng thêm 0 thực thể mới  ·  trần 5 vòng
3. KIỂM ĐỊNH  -> theo lô, soát CẢ thực thể LẪN cạnh
```

**Dừng theo lợi tức, không hỏi mô hình "hết chưa".** GraphRAG dùng logit bias để ép câu trả lời đáng
tin; hỏi bằng lời thì mô hình hay nói "còn" cho lịch sự. **Đếm thực thể mới là tín hiệu khách quan.**

**Chống ép bịa:** median section chỉ **215 token**. Hỏi ba lần liên tiếp trên 215 token là tạo áp lực
phải sinh thêm, mà cách rẻ nhất để làm vừa lòng là bịa. Prompt phải nói rõ **"không còn gì" là câu trả
lời tốt và được chờ đợi**. Không dùng ngưỡng kích thước để bỏ quét lại — kích thước không phải đại diện
cho độ giàu.

**Blocked by:** 02 — mỗi giai đoạn sinh thực thể phải đi qua xác minh bằng chứng.

**Status:** done

- [x] Ba giai đoạn chạy trong **cùng một hội thoại**, không phải ba lời gọi độc lập
- [x] Dừng quét lại khi một vòng thêm **0 thực thể mới**; trần **5** vòng
- [x] **Chuỗi thực thể-mới-mỗi-vòng** ghi vào thống kê, không chỉ ghi tổng — `5→2→0` là lành mạnh,
      `3→3→4` là dấu mô hình sản xuất để làm vừa lòng
- [x] Lượt kiểm định soát **cả thực thể lẫn cạnh đề xuất**, theo lô — cạnh là output nhiễu nhất
- [x] Có test: vòng quét lại thứ hai thêm 0 ⇒ dừng, không gọi vòng ba
- [x] Có test: chạm trần 5 vòng ⇒ dừng, ghi cờ chạm trần
- [x] Có test: thực thể bị lượt kiểm định loại **không** xuất hiện trong đầu ra
- [x] Fixture hội thoại của ticket 01 mở rộng thành nhiều lượt; phát lại trả **đúng lượt thứ n**
