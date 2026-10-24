# Quiz `quiz-3`: câu hỏi kiểm hiểu và vận dụng, giữ lại nhờ một lần giải mù có suy nghĩ

**Status:** accepted — 2026-10-24. Thay lời nhắc sinh câu, đầu ra có trích nguyên văn, hơn 15 luật loại cục bộ và bước kiểm `quiz_verify` của `quiz-2`
(spec Pha B mục 9, spec Pha B2 mục 7). Giữ:
- ngân hàng câu dùng chung theo khái niệm, tính vào trần hệ thống;
- lần làm quiz, nộp bài, tiến độ, thư viện, `home_scope`, `origin`;
- câu điền khuyết khi không có mô hình.

**Mỗi khái niệm 3 câu**: nhớ định nghĩa, hiểu (phân biệt, giải thích), vận dụng (tình huống, bài tính ngắn). Mỗi câu 4 phương án, công thức LaTeX được phép,
có lời giải thích và lý do từng phương án sai. Tư liệu rộng như bài giảng (chữ thô công thức, ảnh trang).

**Giữ câu nhờ một kiểm khách quan, thay cho luật.**
- Một lời gọi khác tự giải mù các câu, với phương án đã xáo, ở mức suy nghĩ `medium`.
- Câu được giữ khi người giải chọn trùng đáp án và không thấy phương án nào khác cũng đúng.
- Luật cục bộ chỉ còn luật cấu trúc: 4 phương án khác nhau, đúng một đáp án.

**Căn cứ:**
- Chủ dự án, 2026-10-23: nâng cấp cả 4 khâu "để thật chuẩn đỉnh chuẩn các app lớn production".
- **SA-22:** bản cũ loại 58% câu do mô hình sinh. Phần thiếu bù bằng câu điền khuyết.
- **Bản cũ chạy lại 2026-10-24,** 12 khái niệm:
  - được 8 câu, 4 khái niệm không có câu nào;
  - câu chủ yếu ở mức nhớ;
  - một câu điền khuyết vô nghĩa ("Dạng ma trận của ___ là: Ax = 0, A = [aij ]m×n ___ (2.2)…").
- **Bản thử mới,** cùng 12 khái niệm, 36 câu. Claude đọc từng câu:
  - 29 tốt;
  - 3 hơi mơ hồ;
  - 3 sai: hai đáp án tính sai, một câu hai đáp án đúng.
  - Giải mù không suy nghĩ giữ lại 2 câu sai và loại nhầm 2 câu đúng.
- **Chạy lại riêng bước giải mù** trên 36 câu đó (`tmp/claude-tools/kiem_lai_quiz3.py`):

  | mức suy nghĩ | bắt câu sai (3) | bắt câu mơ hồ (3) | loại nhầm câu đúng (30) | giây/khái niệm |
  |---|---|---|---|---|
  | không | 1 | 0 | 2 | 2,3 |
  | `low` | 1 | 0 | 1 | 2,9 |
  | `medium` | 2 | 0 | 0 | 3,8 |
  | `high` | 2 | 1 | 0 | 10,6 |

- **Suy nghĩ giúp ở bước giải** (tự tính lại AB và r rồi thấy đáp án sai). Ở bước viết bài và tài liệu, suy nghĩ không giúp (ADR 0027). Quiz là chỗ đáp án sai
  chấm sai người học, và ngân hàng dùng chung nên chi kiểm chỉ trả một lần cho mỗi khái niệm.

**Giới hạn đã biết:** câu "điều kiện nào bảo đảm …" có hai điều kiện đủ (hạng < n và m < n) lọt qua mọi mức. Theo dõi ở đợt đánh giá tổng và qua nút báo câu
sai.

**Considered Options**
- **Giữ `quiz-2`, nới luật:** luật trích nguyên văn và cấm công thức là nguyên nhân chính loại câu tốt. Nới thì vẫn còn câu mức nhớ, 3 phương án.
- **Suy nghĩ ở bước sinh:** chậm và đắt ở mọi câu, mà ở tài liệu đã thấy không chữa được lỗi tính.
- **`high` ở bước giải:** bắt thêm 1 câu mơ hồ nhưng chậm gấp gần ba. Ở lại `medium`; đợt đánh giá tổng đo lại.
- **Mô hình mạnh hơn để giải:** ngoài phạm vi khi phát triển (chỉ flash-lite).
