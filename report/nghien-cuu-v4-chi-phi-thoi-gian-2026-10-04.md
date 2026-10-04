# Nghiên cứu v4: tiền và thời gian tạo lộ trình (2026-10-04)

Theo nguyên tắc số một của v4 (chủ dự án, 2026-10-03), đợt sửa tới phải tối ưu **phút/cuốn** và **USD/cuốn** trước hết, không hạ chất lượng
ngầm. Mọi số dưới đây đo bằng 0 USD, từ manifest và nhật ký của lượt v3 (sáu tài liệu phát triển và hai tài liệu giữ lại).

## 1. Mốc v3: tiền theo khâu

Giá dùng là giá đã khoá trong mã: 0,25 USD cho mỗi triệu token vào, 1,50 USD cho mỗi triệu token ra (`gemini-3.1-flash-lite`). Chưa tính
embedding (rất nhỏ). doc-4 là một giáo trình trọn cuốn (671 đoạn, khoảng 620 khái niệm); xstk là một chương.

| khâu | doc-4: lời gọi | doc-4: USD | xstk: USD |
|---|---:|---:|---:|
| A3 trích khái niệm | 744 | 0,83 | (manifest cũ không ghi) |
| A4/A5 gộp, mô tả | — | 0,64 | (manifest cũ không ghi) |
| A7 nguồn gốc | 89 | 0,09 | 0,02 |
| C8 neo | 619 | 0,40 | 0,05 |
| A9'' danh tính | 907 | 0,27 | 0,05 |
| A8 pass chính | 298 | 2,21 | 0,19 |
| **A8 pass phụ** | **43.190** | **45,92** | **2,35** |
| tên module | 56 | 0,01 | 0,002 |
| **cộng** | | **≈ 50,4** | **≈ 2,7** |

**Pass phụ chiếm 91% tiền của doc-4** (88% của xstk). Trong pass phụ, token vào chiếm 77% tiền: 141,6 triệu token vào so với 7,0 triệu token
ra, trung bình khoảng 3.280 token vào mỗi lời gọi.

## 2. Thời gian

- A1 (đọc PDF): khoảng 7,2 giây/trang ở máy này (đo cũ), tức khoảng 48 phút cho sách 400 trang.
- Pass phụ doc-4 trên Vertex: lượt đầu chạy 2 giờ 50 phút được 61,6%, nên cả pass khoảng 4,5–5 giờ, có nghẽn 429.
- Trên Gemini Developer API bậc 1 có trần chi 10 USD mỗi 10 phút, nên **một việc X USD cần ít nhất khoảng X phút**: pass phụ doc-4 cần ít nhất
  khoảng 46 phút dù song song bao nhiêu. Giảm tiền cũng là giảm thời gian.
- Manifest không ghi thời gian chạy của các khâu gọi mô hình; chỉ cụm và nhắc tên có `runtime_seconds`. Vì vậy chưa có bảng phút theo khâu
  (vé v4-02).

## 3. Một lời gọi pass phụ gồm gì

Đếm trên 300 cặp mẫu của doc-4 bằng tokenizer cục bộ (Gemma), tổng khớp mức 3.280 token đo thật:

| phần | token | tỉ lệ trong hồ sơ cặp |
|---|---:|---:|
| phần chung: system prompt 283 + schema 206 | 489 | (ngoài hồ sơ) |
| `evidence_chunks`: toàn văn các đoạn nhắc cả hai khái niệm và đoạn neo | 1.653 | **59%** |
| cửa sổ định nghĩa của hai khái niệm | 321 | 11% |
| mô tả và thông tin node | 450 | 16% |
| thông tin khác (nguồn cặp, trọng số kênh, thứ tự…) | 363 | 13% |
| đường gián tiếp | 15 | 1% |

Hợp đồng vé 12 chỉ nhận cạnh cứng khi câu trích nằm trong **cửa sổ định nghĩa**, phần này chiếm 11%. Toàn văn đoạn chiếm 59%.

## 4. Các đòn bẩy, xếp theo rủi ro

**A. Hỏi lười thứ tự thứ hai: đầu ra y hệt, bớt 19–38% lời gọi.**
- Mỗi cặp đang được hỏi hai lần (hai thứ tự trình bày) rồi gộp bằng `reconcile_pair_verdicts`. Luật gộp hoãn cặp khi hai thứ tự khác
  quyết định, và hoãn khi một thứ tự lỗi. Vì vậy **thứ tự đầu nói "không quan hệ" thì cặp chắc chắn không ra cạnh**. Đây là điều mã bảo đảm,
  không chỉ là quan sát trên số liệu.
- Phát lại trên nhật ký:

  | tài liệu | cặp | bản ghi lời gọi pass phụ | bớt được | cạnh mất |
  |---|---:|---:|---:|---:|
  | doc-1 | 3.471 | 5.526 | 1.953 (35%) | 0 |
  | doc-2 | 9.513 | 15.040 | 4.584 (30%) | 0 |
  | nhap-mon-ml | 997 | 1.766 | 582 (33%) | 0 |
  | xstk | 942 | 1.582 | 308 (19%) | 0 |
  | doc-4 | 22.972 | 38.556 | 14.497 (38%) | 0 |

- Ở doc-4, 85,5% cặp có cả hai thứ tự đều nói "không", và chỉ 0,2% cặp hai thứ tự cho chiều ngược nhau.
- Thứ tự đầu lỗi sau mọi lần thử lại thì cặp cũng bị hoãn bất kể thứ tự sau, nên bỏ được thêm.
- Thay đổi duy nhất ở đầu ra là cờ chẩn đoán `outside_or_invalid_secondary_edge` của các cặp (thứ tự đầu "không", thứ tự sau lỗi); ở doc-4
  có khoảng 500 cặp như vậy.
- Ước tính: pass phụ doc-4 từ 45,9 xuống khoảng 28 USD, thời gian giảm theo cùng tỉ lệ. → **vé v4-01**.

**B. Hồ sơ gọn: bớt khoảng một nửa token vào, nhưng đổi đầu vào của mô hình.**
- Toàn văn đoạn (59% hồ sơ) không phải căn cứ của cạnh cứng theo hợp đồng vé 12. Rút về các câu có nhắc hai khái niệm, hoặc chỉ giữ cửa sổ
  định nghĩa, có thể bớt khoảng một nửa token vào.
- Rủi ro: đổi đầu vào thì có thể đổi cạnh. Cạnh mềm `cong_cu` và các loại căn cứ `noi_ro`, `mach_trinh_bay` có thể dựa vào phần ngoài cửa sổ.
- Cần một lượt thử nhỏ trả tiền trên hai chương vàng phát triển: so cạnh với lượt v3 và chấm vàng. Ước 2–4 USD, chờ chủ dự án duyệt.

**C. Giảm phản hồi lỗi.**
- Ở doc-4, 2.710 cặp bị hoãn vì phản hồi không hợp lệ (12% số cặp). Mỗi cặp đó tốn hai lời gọi cộng thử lại mà không ra gì.
- Bước đầu 0 USD: đọc nhật ký xem lỗi nào chiếm nhiều nhất (câu trích không nguyên văn, ngoài cửa sổ, sai khuôn).

**D. Cache ngữ cảnh: ít tác dụng.** Phần chung của mỗi lời gọi chỉ khoảng 490 token (khoảng 15%), có thể còn dưới độ dài tối thiểu để Gemini
cache. Không ưu tiên.

**E. Batch/Flex: rẻ hơn 50% nhưng chậm.** Batch xử lý tới 24 giờ. Chỉ hợp việc nền, không hợp người dùng đang chờ.

**F. Lọc cặp bằng học máy:** vẫn là ý tưởng, chờ chủ dự án giao nghiên cứu (ghi ở kế hoạch v3).

**G. Song song cao trên Developer API:** chỉ giảm thời gian, trong giới hạn của bậc chi.

**H. Tăng tốc A1:** nghiên cứu dở, tạm ngưng từ 2026-10-02; liên quan trực tiếp tới phút/cuốn.

Nếu A và B cùng đạt, pass phụ doc-4 ước còn khoảng 15 USD, và cả cuốn khoảng 20 USD thay vì 50 USD. Chưa tính C.

## 5. Đề xuất thứ tự

1. **v4-01 hỏi lười** (0 USD, nghiệm thu bằng phát lại) và **v4-02 ghi thời gian từng khâu** (0 USD).
2. Lượt thử **hồ sơ gọn** (B), sau khi chủ dự án duyệt khoảng 2–4 USD.
3. Đọc nhật ký **phản hồi lỗi** (C), 0 USD.
4. Sửa chất lượng đã thấy ở tập giữ lại (A2 "Cách giải", C8 bỏ qua khái niệm ngoài nội dung, R17, cạnh khái niệm khung). Phần này cần
   **tập giữ lại mới**, nên chủ dự án cần chọn tài liệu mới và người gán sớm.
