# Nghiên cứu: gọi mô hình song song cao (≥ 100) mà kết quả không đổi

Ngày 2026-10-02. Người làm: Claude. Chủ dự án yêu cầu sau khi tạm dừng lượt chạy pass phụ: "tăng lên concurrency 100 luôn hoặc lớn hơn tuỳ
cấu hình, vì sau này còn phải phục vụ user". Vé triển khai: [22](../task/v3-lo-trinh-doc-duoc/22-song-song-cau-hinh-duoc.md).

## Kết luận
- **Làm được, và không đổi kết quả.** Pass phụ dùng cách "hỏi trước một lô, chốt theo đúng thứ tự cũ".
  - Mô phỏng trên nhật ký thật của bốn tài liệu: 100 lời gọi song song chỉ thừa 0,4–2,1% lời gọi và nhanh khoảng 48 lần; 200 lời gọi song
    song thừa ≤ 2,5%.
  - Đầu ra giống hệt cách chạy tuần tự, vì mỗi cặp chỉ được chốt khi đầu vào trùng đầu vào mà cách tuần tự sẽ gửi.
- **Giới hạn thật nằm ở Vertex, không ở mã.**
  - Ở bậc chi hiện tại, thông lượng nền khoảng 2 triệu token/phút cho cả tổ chức. Với 2.864 token/lời gọi thì khoảng 700 lời gọi/phút, gấp
    khoảng 15 lần hiện nay (46/phút).
  - Đặt 100 đồng thời vẫn được, nhưng cần bộ giới hạn theo token/phút và tự hạ khi gặp 429.
- **Hai nút thắt trong mã phải sửa cùng:**
  - điểm lưu ghi lại toàn bộ sau mỗi cặp (55 MB, khoảng 1 giây mỗi lần, tăng dần);
  - sổ chi của script ghi lại cả tệp sau mỗi lời gọi.
- Lượt đang dừng **an toàn**:
  - điểm lưu doc-2 đọc được, có 3.517 cặp đã xong và 425 cạnh phụ;
  - tệp `.tmp` 28 MB cạnh nó là bản ghi dở lúc dừng, vô hại, lần ghi sau sẽ đè;
  - không xoá tệp `.json` chính.

## 1. Nút thắt trong mã

| chỗ | hiện trạng | hệ quả |
|---|---|---|
| `build_secondary_edges.py` | vòng `for pair in pending`, mỗi cặp 2 lời gọi (`min(self.concurrency, 2)`) | tối đa 2 lời gọi cùng lúc; ≈ 46 lời gọi/phút |
| điểm lưu pass phụ | `save_progress()` ghi lại **toàn bộ** checkpoint sau mỗi cặp (`indent=2`, `sort_keys`) | doc-2 ở 37%: 55 MB, ≈ 1,0 s/lần (đo 0,93–1,02 s), tăng tuyến tính → tổng O(n²) |
| sổ chi `MeteredGemini` (script đánh giá) | ghi lại cả `llm-ledger.json` (3,6 MB) sau mỗi lời gọi, dưới khoá | tuần tự hoá mọi luồng khi song song cao |
| thử lại 429 | mỗi luồng tự lùi `2**attempt + random()`; không có giới hạn chung | song song cao → nhiều luồng cùng dội 429 |
| embedding qua Vertex | `_embed_vertex` gọi tuần tự từng câu | chậm khi lập chỉ mục tài liệu lớn |
| pass chính | song song theo chương (`_waves`), vì đầu vào mỗi phiên chứa cạnh của phiên trước cùng chương | song song tối đa bằng số chương (doc-2: 9); pass chính chỉ ≈ 600 lời gọi nên chấp nhận được |

Vì sao pass phụ phải có thứ tự:
- trước mỗi cặp, `select_secondary_pairs` cắt cặp đã có cạnh hoặc đường đi rõ. doc-1 cắt 708/3.471 cặp (20%) nhờ cạnh vừa tạo;
- hồ sơ của mô hình (`pair_dossier`) chứa đường đi hiện có giữa hai khái niệm.

## 2. Mô phỏng 0 USD trên nhật ký thật

`scripts/doc-lo-trinh/thu_song_song_pass_phu.py` dựng lại đúng thứ tự tuần tự và cạnh mỗi cặp đã tạo trong lượt cuối
(`artifacts/v3-r12-final-evaluation`), kiểm phép dựng khớp nhật ký (lệch 0 ở cả bốn tài liệu), rồi chạy cách "hỏi trước, chốt theo thứ tự":
1. lấy B cặp còn phải hỏi theo ảnh chụp cạnh;
2. hỏi cả B cặp;
3. chốt theo thứ tự cũ: cặp bị cắt thì bỏ kết quả; cặp có hồ sơ đổi thì lô sau bắt đầu từ nó.

| tài liệu (cặp phải hỏi) | B = 16 (32 song song) | B = 50 (100 song song) | B = 100 (200 song song) | hỏi tất cả một lần |
|---|---|---|---|---|
| doc-3 (238) | thừa 0,0%, ×15,9 | 0,4%, ×47,6 | 0,4%, ×79,3 | 0,4%, 1 lượt |
| nhap-mon-ml (883) | 0,1%, ×15,8 | 0,5%, ×49,1 | 0,7%, ×98,1 | 5,7%, 1 lượt |
| doc-1 (2.763) | 1,2%, ×15,7 | 2,1%, ×47,6 | 2,5%, ×92,1 | 12,5%, 5 lượt |
| doc-2, phần đã chạy (2.901) | 0,8%, ×15,9 | 1,3%, ×49,2 | 1,5%, ×96,7 | 5,5%, 2 lượt |

- "×" là số lượt chờ giảm so với tuần tự.
- Lời gọi thừa ít vì thứ tự cặp theo mã node (gần như ngẫu nhiên), nên cạnh tạo trong cùng lô hiếm khi ảnh hưởng cặp khác trong lô.
- "Hỏi tất cả một lần" là căn cứ cho chế độ batch job ở mục 4: 1–5 lượt, thừa 0,4–12,5%.

## 3. Giới hạn của Vertex AI

- **429 không phải hết hạn mức cố định.** Theo cơ chế dynamic shared quota, Google cấp từ một bể dùng chung; 429 nghĩa là bể đang tắc tạm thời.
  Khuyến nghị: điểm cuối `global` (dự án đang dùng), lùi luỹ thừa có jitter, **làm đều lưu lượng** thay vì dồn cục, chọn kiểu tiêu thụ phù hợp
  ([Reduce 429 errors on Vertex AI](https://cloud.google.com/blog/products/ai-machine-learning/reduce-429-errors-on-vertex-ai), đã đọc trực
  tiếp; [Standard PayGo / dynamic shared quota](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/dynamic-shared-quota)).
- **Thông lượng nền theo bậc chi** của tổ chức trong 30 ngày, với Flash/Flash-Lite: bậc 1 (10–250 USD) khoảng 2.000.000 token/phút; bậc 2
  (250–2.000 USD) khoảng 4.000.000 token/phút ([Standard PayGo](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/standard-paygo)).
  - *Mức tin:* số này đọc qua trích đoạn của trang chính thức trong kết quả tìm kiếm; công cụ không tải được bảng trên trang. Cần mở trang
    trên trình duyệt xác nhận trước khi đặt mặc định.
  - Dự án đã chi ≈ 45 USD, tức bậc 1.
- **Quy đổi:**
  - Lượt cuối có 16.456 lời gọi có `usage`, trung bình 2.680 token vào và 183 token ra, tổng 2.864 token, 0,00095 USD mỗi lời gọi.
  - 2 triệu token/phút ≈ 700 lời gọi/phút. Độ trễ một vòng hiện khoảng 2,6 s, kể cả ghi điểm lưu, nên cần khoảng 30–40 lời gọi đang chạy để
    đạt mức đó.
  - 100 đồng thời ≈ 2.300 lời gọi/phút ≈ 6,6 triệu token/phút, vượt bậc 1. Phần vượt chỉ chạy được khi bể chung rảnh, còn lại thành 429.
    Vì vậy cần ngân sách token/phút và bộ tự điều chỉnh, không chỉ trần đồng thời.
- **Chế độ rẻ hơn cho việc không gấp:** cả hai **giảm 50%**, đều chưa thử trên `gemini-3.1-flash-lite` của dự án.
  - **Batch inference:** hàng đợi, xử lý trong 24 giờ
    ([Batch inference with Gemini](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/multimodal/batch-prediction-gemini)).
  - **Flex PayGo:** trực tuyến nhưng chậm và bị bóp nhiều hơn. Google khuyên tăng timeout (ví dụ 30 phút) thay vì thử lại dồn dập
    ([Flex PayGo](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/flex-paygo)).

### Khi quay lại Gemini Developer API (sau khi hết credit Vertex)
Chủ dự án chỉ dùng Vertex trong lúc còn 300 USD credit.
- **Cơ chế giới hạn của Developer API** ([Rate limits](https://ai.google.dev/gemini-api/docs/rate-limits), đọc trực tiếp 2026-10-02):
  - tính **theo dự án**, trên ba chiều RPM, TPM (token vào), RPD; vượt chiều nào cũng bị 429;
  - bậc dùng theo tổng chi: bậc 1 = có tài khoản thanh toán, bậc 2 = đã trả ≥ 100 USD, bậc 3 = ≥ 1.000 USD;
  - mỗi bậc có trần chi theo 10 phút: 10 / 50 / 200 USD. Ở 0,00095 USD/lời gọi, trần bậc 1 (≈ 1 USD/phút) tương đương khoảng 1.000 lời
    gọi/phút.
- Trang không còn ghi RPM/TPM cụ thể của từng mô hình; xem trong AI Studio của dự án.
- **Developer API cũng có Batch API**, bảng giới hạn riêng.
- Vì vậy vé 22 làm bộ giới hạn **không phụ thuộc đường gọi**: trần đồng thời, ngân sách token/phút và ngân sách lời gọi/phút đều cấu hình
  được. Cách "hỏi trước, chốt theo thứ tự" của pass phụ giữ nguyên.

## 4. Đề xuất

**Ngay (vé 22):**
- bộ giới hạn chung, gồm trần đồng thời, ngân sách token/phút và tự hạ/tăng theo 429;
- pass phụ chốt theo thứ tự với lô cấu hình được;
- điểm lưu ghi theo lô;
- sổ chi nối thêm;
- embedding song song.

Các thông số này không vào khoá cache, nên doc-2 chạy tiếp từ điểm lưu cũ. Ước thời gian:
- doc-2 còn khoảng 6.000 cặp, tức khoảng 10.000 lời gọi: ≈ 15 phút ở 700 lời gọi/phút, thay vì vài giờ;
- cả pass phụ sáu tài liệu (24,7 nghìn lời gọi): ≈ 35 phút.

**Khi phục vụ người dùng (làm cùng ứng dụng web của đồ án, chưa thuộc vé 22):**
- **Giới hạn phải chung cho cả hệ thống, không chỉ một tiến trình.** Nhiều worker xử lý nhiều cuốn sách cùng lúc dùng chung một ngân sách
  token/phút của tổ chức, ví dụ token bucket trên Redis. Có hàng đợi công việc (mỗi cuốn một job), chia công bằng giữa người dùng, báo tiến
  độ.
- **Quy mô:**
  - Một cuốn cỡ doc-2 cần khoảng 17 nghìn lời gọi, khoảng 50 triệu token: ≈ 25 phút nếu dùng trọn thông lượng bậc 1.
  - Nhiều người cùng tải sách thì phải xếp hàng.
  - Thông lượng tăng theo bậc chi. Khi tải đều và lớn thì cân nhắc Provisioned Throughput.
- **Chi phí:** xử lý sách là việc nền.
  - Thử **Flex PayGo**: rẻ một nửa, đầu ra như cũ nếu mô hình và cấu hình như cũ.
  - Hoặc **Batch** cho các bước không phụ thuộc thứ tự (A3, neo, danh tính, tên). Với pass phụ, chế độ batch cần 1–5 lượt job và thừa ≤ 12,5%
    lời gọi, vẫn rẻ hơn khoảng 44% so với hiện nay.
  - Cả hai cần thử nhỏ trước (độ trễ, tỉ lệ bị bóp) và sổ chi theo giá riêng (vé 19 ghi không dùng giá Flex/Batch cho REST trực tiếp).

## Nguồn
- [Reduce 429 errors on Vertex AI](https://cloud.google.com/blog/products/ai-machine-learning/reduce-429-errors-on-vertex-ai): đọc trực tiếp.
- [Gemini API rate limits](https://ai.google.dev/gemini-api/docs/rate-limits): đọc trực tiếp.
- [Standard PayGo](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/standard-paygo),
  [dynamic shared quota](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/dynamic-shared-quota),
  [Batch inference with Gemini](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/multimodal/batch-prediction-gemini),
  [Flex PayGo](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/flex-paygo): trang chính thức, nội dung đọc qua trích đoạn tìm kiếm
  ngày 2026-10-02; cần xác nhận trên trình duyệt trước khi dựa vào con số.
