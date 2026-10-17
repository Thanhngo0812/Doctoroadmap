# 19j — Thí nghiệm pass chính: nhiễu và chạy song song

Ngày 2026-10-17. Người chạy: Claude. Vé [19j](../task/v4/19j-thi-nghiem-pass-chinh.md), spec [đổi mặc định chuỗi gộp](../doc/doi-mac-dinh-chuoi-gop-spec.md)
pha 3. **Chi thật: 3,06 USD** (Vertex, gemini-3.1-flash-lite, temperature 0), trong trần 10 USD của đợt 19.

## Kết luận

1. **Pass chính tất định theo đầu vào.** Chạy lại doc-1 và xstk trên đúng upstream và khoá cấu hình của lượt cuối 17i thì ra y hệt từng byte:
   128/128 lời gọi, kể cả lời gọi sửa. Không có cache nào ở giữa. Dao động E4 giữa hai lượt 17i (doc-1 Q7 0,73 so với 0,42) vì thế đến hoàn
   toàn từ đầu vào khác nhau, không phải từ mô hình.
2. **Nhiễu đo bằng nhiễu đầu vào không đổi nghĩa.** Xáo thứ tự danh sách "khái niệm nhắc ở nơi khác" trong mọi phiên làm đổi khoảng 25–30% cạnh
   pass chính, và Q7 của doc-1 dao động 0,42–0,60. Pass chính nhạy với cả những thay đổi vô nghĩa của đầu vào.
3. **Pass chính song song: nhận vé 19k, bật làm mặc định.** Pass chính nhanh hơn 3–10 lần và rẻ hơn 20–33%. E4 của doc-1 và doc-4 nằm trong
   dải nhiễu hoặc tốt hơn. xstk tụt ở hai chỉ số bao đóng; xem mục 3.

## 1. Cách làm

Script `scripts/gop-khau/thu_pass_chinh.py` chép kho riêng 17i của một tài liệu sang thư mục mới, giữ graph tới artifact `mentions` mà lượt cuối
17i dùng (doc-1 và xstk: v10; doc-4: v2). Sau đó chạy pass chính, pass phụ ML, kiểm đồ thị, nhãn khái niệm và dãy học như sản phẩm (bỏ đặt tên
module), rồi chấm E4 bằng `cham_gop.score`. Không sửa mã sản phẩm. Khoá cấu hình pass chính trùng lượt 17i (doc-1 `8fdf5318…`).

| Biến thể | Nghĩa |
|---|---|
| `noi-s0` | lượt cuối 17i, không tốn tiền |
| `noi-r1` | chạy lại nguyên trạng, để kiểm tính tất định |
| `noi-x1`, `noi-x2` | nối tiếp như sản phẩm; xáo `mentioned_elsewhere` của từng phiên với hạt 1 và 2 |
| `song-s1` | mọi phiên một đợt, nên không phiên nào nhận cạnh của phiên trước; không xáo |

`scripts/gop-khau/phan_tich_19j.py` gộp E4, độ trùng cạnh và nhiễu theo phiên. Kết quả máy đọc nằm ở `tmp/v4-19j/ket-qua/`.

## 2. Tính tất định (`noi-r1`)

| | Lời gọi | Đầu ra giống nguyên văn lượt 17i | Jaccard cạnh pass chính | E4 |
|---|---:|---:|---:|---|
| doc-1 | 78 | 78 | 1,000 | trùng khít |
| xstk | 50 | 50 | 1,000 | trùng khít |

Số token vào/ra của từng lời gọi cũng trùng. Hệ quả cho đợt baseline đánh giá: chạy lặp nguyên trạng không cho khoảng tin cậy nào. Đổi lại, một
lượt chạy tái lập được nếu giữ nguyên artifact thượng nguồn.

## 3. E4 và thời gian

Mỗi ô là giá trị, hoặc khoảng min–max trên các lượt `noi-s0`, `noi-x1`, `noi-x2`. Q6 là tỷ lệ vi phạm thứ tự, càng thấp càng tốt; các chỉ số khác
càng cao càng tốt.

| Chỉ số | doc-1 nối tiếp | doc-1 song song | xstk nối tiếp | xstk song song | doc-4 nối tiếp (s0) | doc-4 song song |
|---|---|---|---|---|---|---|
| Q6 | 0,125 | 0,100 | 0,525–0,542 | 0,508 | 0,129 | 0,129 |
| Q7 | 0,419–0,596 | 0,496 | 0,253–0,427 | 0,348 | 0,638 | 0,636 |
| Q7b | 0,645–0,667 | 0,683 | 0,467–0,506 | 0,469 | 0,878 | 0,878 |
| P trực tiếp | 0,483–0,517 | 0,552 | 0,286–0,308 | 0,308 | 0,739 | 0,723 |
| R trực tiếp | 0,483–0,552 | 0,552 | 0,111 | 0,111 | 0,642 | 0,642 |
| P bao đóng | 0,713–0,763 | 0,797 | 0,562–0,618 | **0,528** | 0,893 | 0,892 |
| R bao đóng | 0,465–0,604 | 0,653 | 0,257–0,324 | **0,181** | 0,629 | 0,623 |
| Cạnh pass chính | 211–223 | 217 | 74–83 | **63** | 546 | 488 |
| Cạnh cứng của dãy học | 405–419 | 416 | 141–148 | 141 | 1.052 | 1.043 |
| Giây pass chính | 124–152 | **18,5** | 130–157 | **12,4** | 825 | **285** |
| USD pass chính | 0,30–0,31 | 0,24 | 0,16–0,18 | 0,12 | 1,95 | 1,30 |

Đọc bảng:
- **doc-1:** song song bằng hoặc tốt hơn dải nối tiếp ở mọi chỉ số.
- **doc-4:** song song lệch lượt 17i tối đa 0,016. Token vào giảm từ 6,77 xuống 4,30 triệu, vì đầu vào không còn cạnh của phiên trước.
  - 285 giây là trần của bộ giới hạn 1,6 triệu token/phút: 4,3 triệu token cần ít nhất khoảng 2,7 phút.
  - 53 lời gọi phải thử lại, không tính token. Nâng trần token/phút sẽ nhanh thêm.
- **xstk:** cả 31 phiên nằm trong một chương, nên ở chế độ nối tiếp phiên nào cũng thấy cạnh của các phiên trước.
  - Song song sinh ít cạnh pass chính hơn: 63 so với 74–83.
  - P và R bao đóng tụt dưới dải: R 0,18 so với 0,26–0,32, tức 19 so với 27–34 cạnh bao đóng đúng trên 105.
  - Các chỉ số còn lại nằm trong dải. Pass phụ ML bù lại số cạnh cứng: 141, bằng dải nối tiếp.

**Độ trùng cạnh pass chính (Jaccard):**

| | Trong nhóm nối tiếp | Nối tiếp so với song song |
|---|---|---|
| doc-1 | 0,67–0,75 | 0,64–0,79 |
| xstk | 0,69–0,72 | 0,49–0,58 |

Như vậy song song ở doc-1 lệch không hơn một lần xáo thứ tự, còn ở xstk thì lệch hơn.

## 4. Quyết định về 19k

**Nhận, bật làm mặc định:**
- Tiêu chí của vé là "E4 không tụt quá dải nhiễu, thời gian giảm rõ". doc-1 và doc-4 đạt.
- xstk tụt ở hai chỉ số bao đóng. Đây là tài liệu một chương, nơi chuỗi phiên dài nhất. Nó cũng là tài liệu yếu nhất của A8 ở mọi biến thể (R
  trực tiếp 0,111).
- Lợi ích lớn: pass chính là khâu chậm nhất còn lại của luồng gộp. doc-4 giảm từ 13,7 phút xuống 4,7 phút, và rẻ hơn khoảng 0,65 USD mỗi cuốn.

**Rủi ro còn lại:** tài liệu một chương dài có thể mất một phần cạnh pass chính. Cổng 19l sẽ soi xstk.
- Nếu R bao đóng của xstk ở cổng lại nằm dưới 0,2, mở vé xem cách lai: song song giữa các nhóm phiên, nối tiếp trong nhóm.
- Không làm cách lai trước khi có số.

**Dải nhiễu cho cổng 19l:** dùng bảng mục 3, gộp cả cột nối tiếp lẫn song song của từng tài liệu. Cổng chạy canonical mới nên đầu vào pass chính
khác 17i. Theo kết luận 2, lệch trong dải này là nhiễu đầu vào; vẫn phán bằng cách đọc, như luật cổng.

## 5. Chi phí

| Lượt | USD |
|---|---:|
| `noi-r1`: doc-1, xstk | 0,489 |
| `noi-x1`, `noi-x2`: doc-1, xstk | 0,912 |
| `song-s1`: doc-1, xstk | 0,361 |
| `song-s1`: doc-4 | 1,303 |
| **Tổng** | **3,064** |

Trần đợt 19 còn khoảng 6,9 USD, đủ cho cổng 19l (ước 5 USD). Lượt `noi-r1` tốn 0,49 USD mà chỉ cho câu trả lời "tất định". Khi đã biết điều này,
không còn chạy lặp nguyên trạng nữa.
