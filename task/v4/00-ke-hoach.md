# v4 — Nhanh, rẻ, vẫn chuẩn: kế hoạch vé

**Nguyên tắc số một (chủ dự án, 2026-10-03):** đây là ứng dụng phục vụ người dùng, nên phải tối ưu **phút/cuốn** và **USD/cuốn** trước hết.
- Mỗi vé đo hai số trước và sau sửa, trên cùng bộ tài liệu: phút/cuốn và USD/cuốn.
- Chất lượng vẫn đo trên vàng. Cách tiết kiệm nào làm tụt chất lượng thì báo đánh đổi bằng số, chủ dự án quyết.
- Đường gọi sản phẩm là Gemini Developer API, song song cao. Vertex chỉ dùng khi còn credit.

**Nguồn:** [nghiên cứu tiền và thời gian](../../report/nghien-cuu-v4-chi-phi-thoi-gian-2026-10-04.md) ·
[kết quả tập giữ lại v3](../../report/ket-qua-tap-giu-lai-v3-2026-10-04.md) · mục "Hướng v4" của
[kế hoạch v3](../v3-lo-trinh-doc-duoc/00-ke-hoach.md).

**Mốc v3:** doc-4 (giáo trình trọn cuốn) tốn khoảng 50 USD; riêng A8 pass phụ 45,9 USD (91%) và khoảng 4,5–5 giờ trên Vertex.

**Trạng thái:**
- Chủ dự án giao 01/02 ngày 2026-10-04. Phần đo 02 đã xong. 01 đã được Claude kiểm: nhận tiêu chí cờ rộng hơn; còn thiếu mẫu theo dõi 3% và chưa
  commit.
- Từ 2026-10-05, việc chính là **pass phụ không LLM** (vé 11), vòng 1 đã xong.
- Từ 2026-10-10, nguồn lực dồn cho vé 11 vòng 2 → [kế hoạch vòng 2](../../report/nghien-cuu-pass-phu-vong-2-ke-hoach-2026-10-10.md).

## Quyết định của chủ dự án ngày 2026-10-05

- **Đồ án chỉ làm tài liệu tiếng Việt.** Luật đa ngôn ngữ không còn ràng buộc luồng chính; được dùng công cụ riêng tiếng Việt, ví dụ tách từ.
- **Pass phụ A8 bỏ LLM**, cho cả đồ án lẫn seminar. Luồng LLM cũ giữ lại, chọn được, để so sánh.
- **Đích dài hạn:** LLM chỉ còn ở A3 (trích ứng viên) và A8 pass chính (agent suy luận cạnh). Các khâu khác nghiên cứu bỏ LLM sau, từng khâu một.
- **A1:** đầu vào sau này sạch như doc-4 hay doc-1 (PDF có lớp chữ), nên chỉ cần nhanh nhất cho ứng dụng.
- Chủ dự án tự làm dữ liệu huấn luyện bằng agentic theo đặc tả của Claude ([D-01](D-01-dac-ta-du-lieu-pass-phu.md)).

## Quyết định của chủ dự án ngày 2026-10-10

- **A1 đổi mặc định sang bộ đọc nhẹ** ([vé 16](16-a1-bo-doc-nhe-mac-dinh-va-cay-cha-con.md)), không chờ pha 4 vé 15.
  - Đây là đánh đổi: trên tập phát triển, M3 thấp hơn docling 0,065 và M1 thấp hơn 0,043; đổi lại nhanh hơn khoảng 36 lần.
  - Docling vẫn chọn được; tài liệu cũ giữ docling.
- **Không dồn thêm nguồn lực cho A1.** Chủ dự án và Claude tạm dừng việc A1. Nhân viên làm vé 16: tích hợp, rồi nghiên cứu cây cha–con trong hạn mức 3 ngày.
- **Tập khoá D-02 giữ niêm phong** cho một lần đánh giá sau.
- **Người duyệt nhãn D-02 dùng agentic.** Phần đã duyệt gọi là "agentic + duyệt agentic", không gọi là vàng người.
- **Dồn nguồn lực sang pass phụ A8 không LLM** (vé 11 vòng 2), vì một bản phục vụ cả đồ án lẫn seminar. Claude nhận phân tích, nghiên cứu và
  triển khai; mã `src/` vẫn đi qua vé cho nhân viên.
- **Thầy gợi ý** dùng bộ dữ liệu tiên quyết công khai, dịch sang tiếng Việt rồi huấn luyện. Claude đã kiểm 11 bộ và đề xuất chiếu AL-CPL sang
  Wikipedia tiếng Việt thay cho dịch → [kế hoạch vòng 2](../../report/nghien-cuu-pass-phu-vong-2-ke-hoach-2026-10-10.md), mục 2.
- **D-01:** hướng dẫn gán bản 1.1; lượt A gán lại phiếu 1–240; lượt B do Claude gán trên mẫu 956 phiếu, trong gói ngoài repo.

## Ràng buộc sản phẩm từ nghiên cứu R-01 (Claude kiểm lại trên trang chính thức 2026-10-04)

Nghiên cứu [R-01](../../report/nghien-cuu-v4-gemini-va-rut-gon-ngu-canh-2026-10-04.md) đổi vài giả định của v4. Các điểm dưới đây Claude đã
tự đọc lại trên trang gốc:
- **Trần chi theo tháng trên cả tài khoản thanh toán** (trang Billing, 2026-09-28): bậc 1 250 USD, bậc 2 2.000 USD (đã trả 100 USD và qua
  3 ngày), bậc 3 20.000–100.000 USD. Chạm trần thì mọi project của tài khoản dừng tới chu kỳ sau. Theo giá v3, bậc 1 chỉ đủ khoảng 5 cuốn
  cỡ doc-4 mỗi tháng. Ngoài ra còn trần 10/50/200 USD mỗi 10 phút trượt.
- **Credit chào mừng của Google Cloud không trả được Gemini API**; Developer API phải nạp trước (Prepay). Đúng với cách đang làm: dùng
  Vertex trong lúc còn credit.
- **`gemini-3.1-flash-lite` tắt sớm nhất ngày 2027-05-07** (trang Deprecations). Mô hình thay thế `gemini-3.5-flash-lite` giá 0,30/2,50 USD,
  đắt hơn khoảng 31% mỗi lời gọi pass phụ. Đổi mô hình là đổi cấu hình, phải đo lại chất lượng.
- **Cache không áp dụng cho pass phụ**: dòng Gemini 3 cần tiền tố ít nhất 4.096 token, lớn hơn cả một lời gọi.
- **Batch** rẻ 50% nhưng mục tiêu 24 giờ, chỉ hợp việc nền. **Flex** rẻ 50%, gọi đồng bộ, độ trễ mục tiêu 1–15 phút: ứng viên cho người dùng
  chờ, cần thử nhỏ.
- RPM/TPM/RPD theo mô hình chỉ xem được trong AI Studio; phải xem trước khi chuyển sang Developer API (một cuốn cần khoảng 44.000 lời gọi).

## Dữ liệu dùng được

- Tập giữ lại v3 (xstk, doc-4) **đã dùng**. Từ v4, hai tài liệu này là tài liệu phát triển, cùng sáu tài liệu cũ.
- Mọi sửa chất lượng của v4 cần **tập giữ lại mới**: tài liệu mới và vàng mới, chọn trước khi sửa. Đổi tiền và thời gian mà đầu ra y hệt
  (như v4-01) thì không cần.

## Phạm vi theo khâu (cả Pha A, A1 → A10)

v4 là đợt tiếp theo của dự án, phủ mọi khâu. Mỗi khâu có thể có việc về thời gian, tiền hoặc chất lượng. Việc đổi đầu ra của một khâu thì
các khâu sau phải chạy lại, và nếu đổi chunk hay khái niệm thì phải ánh xạ lại vàng, nên các việc như vậy gom vào một lượt chạy lại.

| khâu | thời gian / tiền | chất lượng | nguồn bằng chứng |
|---|---|---|---|
| A1 đọc PDF (docling 2.114) | khoảng 7,2 giây/trang, tức khoảng 48 phút cho sách 400 trang. Pipeline song song theo trang **đã là mặc định**. Đòn bẩy chính: **OCR** (docling OCR mọi ảnh phủ ≥ 5% trang, kể cả trang có lớp chữ; engine tự chọn không đọc được dấu tiếng Việt và chữ OCR trong hình không tới adapter) và **số luồng** (mặc định 4, máy có 8 nhân) | công thức thành `[formula]`; cây mục dạng §1, §2; tách âm tiết doc-4 (`enforce_same_font`) | [R-03](../../report/nghien-cuu-v4-a1-docling-2026-10-04.md); script đo dở ở `tmp/thu-a1/` |
| A2 chunk, vai trò vùng | nhỏ | mục "Cách giải" bị gán đề cương (xstk 48/126 đoạn) | kết quả tập giữ lại |
| A3 trích khái niệm | khoảng 0,8 USD/cuốn | thiếu kết quả có tên (vé 13); độ hạt | v3 |
| A4/A5 gộp, mô tả | khoảng 0,6 USD/cuốn | — | — |
| A6 cụm, nhắc tên | nhỏ; số cặp ứng viên quyết định số lời gọi pass phụ | diễn đạt khác không thành cặp | v3 |
| A7, C8 neo, A9'' danh tính | khoảng 0,8 USD/cuốn | C8 không hỏi `kind` với khái niệm chỉ có căn cứ ngoài nội dung; neo sai câu (doc-4 "Kết cấu") | tập giữ lại, vé 21 |
| A8 pass chính, pass phụ | **khoảng 48 USD/cuốn, nhiều giờ**: v4-01, v4-03, bộ lọc cặp (R-02) | cạnh khái niệm khung (doc-4) | nghiên cứu tiền và thời gian |
| A9, A10, tên | gần 0 | R17 làm mềm cạnh ngược sách cả khi đúng (5/11 cạnh ngược doc-4); tên module theo cây mục hỏng | tập giữ lại |

## Vé

| vé | việc | ai | chi phí mô hình | trạng thái |
|---|---|---|---|---|
| [01](01-pass-phu-hoi-luoi.md) | A8 pass phụ hỏi lười thứ tự thứ hai: đầu ra y hệt, bớt 19–38% lời gọi | nhân viên | 0 (phát lại) | mã/test/replay xong; Claude nhận tiêu chí cờ rộng hơn; còn mẫu theo dõi 3% và commit. Từ 2026-10-05 chỉ còn giá trị cho luồng LLM làm mốc so sánh |
| [02](02-thoi-gian-moi-khau.md) | mọi stage ghi thời gian chạy; Claude viết báo cáo phút/USD mỗi cuốn | nhân viên + Claude | 0 | **xong**: phần nhân viên đạt; script `scripts/do-chi-phi/bao_cao.py` (Claude, `1f68209`); nhân viên chưa commit |
| 03 | thử hồ sơ cặp gọn cho pass phụ (bớt toàn văn đoạn) | Claude soạn sau 01 | khoảng 2–4 USD, chờ duyệt | chưa soạn |
| 04 | đọc nhật ký phản hồi lỗi của pass phụ (12% cặp doc-4) | Claude | 0 | chưa làm |
| 05 | sửa chất lượng từ tập giữ lại: A2 "Cách giải", C8 bỏ qua khái niệm ngoài nội dung, R17, cạnh khái niệm khung. **Số đo 2026-10-12** ([quy lỗi thượng nguồn](../../report/quy-loi-thuong-nguon-a8-2026-10-12.md)): chuỗi A2 → C8 làm mất 29/62 cạnh vàng xstk; cạnh vàng chỉ có đường mềm 25 với LLM v3, 15 với E5 (đo lại sau khi sửa lỗi bộ khớp tên, cùng ngày) | Claude soạn | cần tập giữ lại mới | chưa soạn |
| T-01 | chọn 2 tài liệu mới và người gán vàng cho tập giữ lại v4 | **chủ dự án** | 0 | hai cuốn `d01-t01`, `d01-t02` (`document-data/test/`); quyền xác nhận 2026-10-11; T-01a xong, bốn phiếu trống đã giao. **Chờ hai người gán**, rồi kiểm, gộp, hội ý, đóng băng (bước 8 vé T-01a). **Đường găng của vòng 2**, không phụ thuộc D-01 |
| [T-01a](T-01a-chay-luong-hai-cuon-giu-lai.md) | chạy A1 → A5 trên hai cuốn giữ lại (A1 giống D-01, `a4` đầy đủ như doc-4), gửi danh sách chương, sinh file gán A1/A2, đóng băng vàng; không đọc nội dung, kiểm bằng `scripts/t01/kiem_t01a.py` | nhân viên | dưới 2 USD Vertex, trần 5 USD | **Claude kiểm 2026-10-11: đạt** → [vòng 2, mục 8.8](../../report/nghien-cuu-pass-phu-vong-2-ke-hoach-2026-10-10.md): chạy trên checkout ghim `ff797eb`; checker ĐẠT hai cuốn; tám hash khớp; LLM đo được 1,94 USD. Sự cố mất mù d01-t01 phía nhân viên do checker của Claude in nguyên `stats`; chủ dự án chấp nhận; checker đã vá. Còn bước 8 khi người gán nộp phiếu |
| R-01 | nghiên cứu nguồn gốc: Gemini Developer API (giá, giới hạn, cache, Batch), rút gọn ngữ cảnh, độ lệch vị trí → [báo cáo](../../report/nghien-cuu-v4-gemini-va-rut-gon-ngu-canh-2026-10-04.md) | Claude (tác tử nền) | 0 | **xong 2026-10-04** |
| 06 | đổi `responseJsonSchema` (đã deprecated) sang `responseFormat` ở bộ chuyển đổi Gemini, kiểm bằng phát lại; xử lý lỗi 402 khi hết tiền nạp trước | nhân viên | 0 | chưa soạn |
| 07 | thử Flex nhỏ: độ trễ thật, tỉ lệ bị từ chối (503), đầu ra có y hệt Standard không | Claude soạn | dưới 1 USD, chờ duyệt | chưa soạn |
| 08 | kế hoạch chuyển sang `gemini-3.5-flash-lite` trước 2027-05: đo chất lượng và USD/cuốn | Claude soạn | cần tập giữ lại mới | chưa soạn |
| R-02 | nghiên cứu ML/DL: lọc cặp trước pass phụ (v4) và học tiên quyết không LLM (seminar) → [báo cáo](../../report/nghien-cuu-ml-dl-loc-cap-va-tien-quyet-2026-10-04.md) | Claude (tác tử nền) | 0 | **xong 2026-10-04** |
| R-03 | nghiên cứu A1: tuỳ chọn tốc độ của docling 2.114 (đọc mã nguồn đã cài), tuỳ chọn nào giữ nguyên đầu ra, nhận dạng công thức chạy tại máy → [báo cáo](../../report/nghien-cuu-v4-a1-docling-2026-10-04.md) | Claude (tác tử nền) | 0 | **xong 2026-10-04** |
| [09](09-khoa-cache-parse.md) | khoá cache parse gồm **mọi** tuỳ chọn pipeline docling và engine OCR ghi đích danh (không để tự chọn), để đổi tuỳ chọn không âm thầm dùng lại parse cũ; chỉ ghi tuỳ chọn khác mặc định nên băm cũ giữ nguyên; làm trước mọi đổi A1 | nhân viên | 0 | **soạn xong 2026-10-05**, chờ giao |
| 10 | đo A1 tại máy (0 USD): cấu hình hiện tại chạy hai lần (có tất định không), số luồng 8, tắt OCR, rồi các tuỳ chọn khác; kiểm đầu ra y hệt ở bốn tầng (JSON docling, từng mục, adapter, tập `chunk_id`); chạy lúc máy rảnh | Claude | 0 | **lượt 1 xong** → [báo cáo](../../report/v4-10-do-a1-tai-may-2026-10-05.md): docling tất định; 8 luồng giữ đầu ra; tắt OCR giữ đầu ra trên PDF có lớp chữ. Số giây bị nhiễu, phải đo lại lúc máy rảnh, sau vé 09 Lượt 2 và bước 2 → [báo cáo](../../report/v4-10-buoc-2-bo-doc-nhe-2026-10-05.md): chia đoạn song song đầu ra y hệt nhưng **không nhanh hơn trên laptop 15 W**; bộ đọc nhẹ pypdfium2 nhanh hơn 35–150 lần, sách chữ (doc-4) gần như thay được, sách toán chưa (công thức, bảng). Đề xuất chọn bộ đọc theo tín hiệu font toán; muốn đưa vào luồng thì cần thí nghiệm có tốn tiền ở các khâu sau (doc-4, khoảng 4–5 USD), chờ duyệt |
| 11 | **pass phụ A8 không LLM** (đồ án và seminar): ứng viên = tên X trong cửa sổ định nghĩa Y theo ranh giới từ tiếng Việt; LightGBM học ý định cạnh cứng của LLM; lắp cạnh tất định qua hợp đồng vé 12 | Claude nghiên cứu; nhân viên triển khai sau vòng 2 | 0 | **vòng 1 xong** → [báo cáo](../../report/nghien-cuu-pass-phu-khong-llm-vong-1-2026-10-05.md): doc-4 hơn LLM cả bốn chỉ số, doc-1 sát, xstk kém độ phủ; 0 USD, khoảng 1–2 phút/cuốn so với 45,9 USD và 4,5–5 giờ. **Vòng 2:** [kế hoạch](../../report/nghien-cuu-pass-phu-vong-2-ke-hoach-2026-10-10.md) 2026-10-10 (E0', E5–E10); chờ D-01 gán xong |
| [D-01](D-01-dac-ta-du-lieu-pass-phu.md) | dữ liệu huấn luyện đa lĩnh vực cho vé 11: chủ dự án gom ≥ 12 giáo trình tiếng Việt (2 cuốn để riêng làm T-01), gán nhãn bằng agentic theo đặc tả | **chủ dự án** gom và gán; Claude chạy luồng, xuất phiếu, kiểm | chạy A1 → A8 pass chính trên sách mới: chờ dự toán và duyệt | đặc tả xong 2026-10-05; phiếu xong (vé 12). **2026-10-08:** [hướng dẫn agentic](../../report/huong-dan-agentic-gan-nhan-d01.md) và `scripts/pass-phu-ml/kiem_nhan_d01.py`. **Không đưa tệp đặc tả D-01 cho agentic**: năm ví dụ trong đó trùng phiếu kiểm. **2026-10-10:** agentic gán lượt A (Codex/GPT-6, chia lô subagent); hướng dẫn bản 1.1; gán lại phiếu 1–240 ([bàn giao bổ sung](../../report/ban-giao-agentic-d01-bo-sung-2026-10-10.md)); gói lượt B (Claude, 956 phiếu) ngoài repo |
| [12](12-d01-chay-luong-xuat-phieu.md) | D-01 bước 2: chạy A2 → A9'' (dừng trước A8) trên 16 cuốn học qua Vertex, xuất phiếu gán nhãn; trước đó sửa A2 không thử lại khi 429 và A3 báo mã 0 khi không ghi | nhân viên | khoảng 20 USD Vertex, chủ dự án đã duyệt; trần nâng lên 75 USD ngày 2026-10-06; đo được 28,06 USD LLM | **Claude kiểm 2026-10-08: đạt** → [kiểm thử](../../report/kiem-thu-ve-12-13-14-a1-mo-rong-2026-10-08.md): 16/16 cuốn tới danh tính, 5.901 phiếu / 65.525 cặp; nhận giới hạn 83 phiếu kiểm (371 cặp vàng). Chờ chủ dự án gán nhãn agentic |
| [13](13-a1-bo-doc-chu-tieng-viet.md) | A1 cho tài liệu tiếng Việt: mặc định bộ đọc pypdfium2 (docling-parse giải mã hỏng d01-01, vỡ âm tiết doc-4), đo hai bộ đọc trên mọi PDF tiếng Việt, lưới an toàn chất lượng chữ **có hành động** (tự đổi bộ đọc; cả hai hỏng thì dừng; lệnh tốn tiền từ chối chunk chữ hỏng). Cảnh báo `_text_quality` cũ đã bắt d01-01 nhưng chỉ nằm im trong manifest | nhân viên | 0 | **Claude kiểm 2026-10-08: đạt một phần** → [kiểm thử](../../report/kiem-thu-ve-12-13-14-a1-mo-rong-2026-10-08.md): cổng bỏ sót chữ bị thay bằng Kirin; tự đổi bộ đọc đã chỉ định (lệnh T10 xstk) |
| [13b](13b-sua-cong-chat-luong-chu.md) | sửa cổng chữ của vé 13: thêm tỉ lệ chữ ngoài Latin/Hy Lạp (bắt chữ Kirin), bộ đọc ghim thì không tự đổi, dry-run không chọn lượt chưa đo, bảng khoá T10 thêm `--pdf-text-policy legacy` | nhân viên | 0 | **Claude kiểm 2026-10-08: đạt** → [kiểm thử](../../report/kiem-thu-ve-13b-2026-10-08.md). F1 (test không thể đỏ) và F2 (`CONTEXT.md` thiếu cờ lý do xstk) chưa sửa, đã gộp vào vé 16. Chưa commit |
| [14](14-hoc-nhan-tieu-de.md) | bộ đọc PDF nhẹ: học bộ nhận tiêu đề từ nhãn docling trên 16 cuốn D-01 (ML, không LLM, hợp seminar), đo leave-one-book-out và đầu cuối ở mức chunk; mục tiêu tiêu đề F1 trung vị ≥ 0,9, chunk cùng mục ≥ 0,85, dưới 0,1 giây/trang. Từ 2026-10-07 mở rộng thành "A1 mở rộng" (R2–R25), được tự đưa vào sản phẩm | nhân viên nghiên cứu, báo Claude kiểm | 0 | **Claude kiểm 2026-10-08** → [kiểm thử](../../report/kiem-thu-ve-12-13-14-a1-mo-rong-2026-10-08.md): vòng 1 đạt (chưa đạt mục tiêu nào trừ tốc độ, báo trung thực); phần vào sản phẩm (giữ chữ lặp, nguồn chú thích hình, `declared-v1`) nhận; đề nghị dừng chuỗi R vì đã phẳng (cùng mục lá chặt 0,616 → 0,642). Chủ dự án chọn làm tiếp A1: thay bằng vé 15 |
| [D-02](D-02-dac-ta-nhan-cau-truc-a1.md) | nhãn cấu trúc A1 (cây mục cả cuốn, trang mẫu) gán bằng agentic, người duyệt mẫu. Đã kiểm 20 sách mới: **16 là bản quét kèm OCR**, 4 là PDF gốc. Đợt `new-doc-2` thêm 2 cuốn toán gốc dùng được; toán rời rạc bị tải thiếu. Đợt `new-doc-3` thêm kinh tế vi mô và luật kinh doanh (PTIT, gốc). Tập khoá: 8 cuốn gốc. **Phạm vi chỉ PDF gốc** (2026-10-08): bản quét chỉ dùng kiểm định tuyến, không gán. Tập phát triển 6 cuốn D-01 đã có nhãn agentic (vé 15, pha 1b). [Hướng dẫn agentic](../../report/huong-dan-agentic-gan-nhan-d02.md) đã có | **chủ dự án** xác nhận quyền, gom thêm sách, gán và duyệt; nhân viên xuất phiếu tập phát triển; Claude xuất phiếu tập khoá | 0 | **đang làm**: nhãn phát triển xong. Quyền 8 cuốn khoá xác nhận 2026-10-08; nháp `document-data/manifest-d02.json`. Nhãn khoá agentic nộp 2026-10-10, đang bổ sung; người duyệt dùng agentic |
| [15](15-a1-danh-gia-doc-lap-chon-duong.md) | A1: đóng chuỗi R; xuất phiếu D-02; bộ chấm theo vàng (đo cả docling); phát triển có hạn mức trên tập phát triển; định tuyến nhận ra và từ chối bản quét (ngoài phạm vi); tuỳ chọn sửa cây mục theo mục lục; Claude đánh giá khoá một lần theo luật định trước; tích hợp theo kết quả | nhân viên; Claude chạy pha 4 | 0 (pha 5 tuỳ chọn, khoảng 6–8 USD, cần duyệt) | **Pha 0–3 xong**; Claude kiểm 2026-10-10 đạt quy trình → [kiểm thử](../../report/kiem-thu-ve-15-pha-0-3-2026-10-10.md). Cổng định tuyến 43 PDF không đạt (chặn S2). **Chủ dự án chốt 2026-10-10:** đổi sang bộ đọc nhẹ không chờ pha 4. Pha 4 hoãn, tập khoá niêm phong; pha 5 chuyển sang vé 16 |
| [16](16-a1-bo-doc-nhe-mac-dinh-va-cay-cha-con.md) | A1, hai pha. **Pha 1:** đưa bộ đọc nhẹ R2 vào sản phẩm làm mặc định (`--a1 {nhe,docling}`, khoá cache, tài liệu cũ giữ docling); sửa cổng phạm vi (PDF gốc có trang ảnh không chữ bị từ chối nhầm); xử lý ký tự ngoài BMP; sửa F1/F2 vé 13b. **Pha 2:** nghiên cứu cây cha–con bằng ngữ pháp đánh số, mục lục và `declared-v1`, hạn mức 3 ngày | nhân viên; Claude kiểm khi được giao | 0 | **soạn 2026-10-10**, chờ giao |
| 17 | **gộp khâu trước A8** ([spec](../../doc/gop-khau-truoc-a8-spec.md)): danh tính gộp hẳn vào A4 (một bước gộp thực thể, không còn bản đồ danh tính; chủ dự án chốt 2026-10-12, chấp nhận dựng lại chỉ số cho bộ vàng không chuyển được id); A5 kiêm neo và trạng thái dạy; chuỗi mới bỏ provenance, neo, danh tính khỏi chuỗi đồ thị. Giữ LLM, chỉ bớt lời gọi và stage nối tiếp. Chuỗi v3 vẫn là mặc định tới khi nghiệm thu | nhân viên cài; Claude nghiệm thu | nghiệm thu ước dưới 6 USD, cần dry-run và duyệt | **spec xong 2026-10-12**, chờ chia vé. **Chỉ triển khai sau khi vòng 2 đo xong trên T-01** |
| [D-04](D-04-dac-ta-nhan-canh-nguoc.md) | nhãn cạnh ngược thứ tự sách cho E8 (R17): cặp X → Y mà X dạy sau Y, từ ba tài liệu phát triển và 16 sách D-01; agentic hai lượt gán "có phải học X trước Y không"; Claude đo độ chính xác từng luật giữ cứng, đạt tiêu chí mới soạn vé sửa A10 | Claude đặc tả và đo; xuất phiếu theo vé; **chủ dự án** gán bằng agentic | 0 | **đặc tả xong 2026-10-15**; vé [D-04a](D-04a-xuat-phieu-canh-nguoc.md) xuất phiếu (nhân viên, làm ngay) → [D-04b](D-04b-huong-dan-gan-canh-nguoc.md) hướng dẫn (Claude) → [D-04c](D-04c-gan-nhan-hai-luot.md) gán hai lượt (**chủ dự án**) → [D-04d](D-04d-do-luat-e8.md) đo luật (Claude) |
| [sau-a10](../sau-a10/00-ke-hoach.md) | **Pha B sau A10** ([spec](../../doc/pha-b-spec.md), ADR 0011–0014): tên và mô tả module do LLM đặt, A12 lớp gán module, ảnh công thức, bài giảng theo khái niệm, quiz tự kiểm tra, trợ lý agent, tài liệu theo yêu cầu, đánh giá, trang xem thử; 24 vé SA-01…SA-24 có kế hoạch riêng | nhân viên cài; Claude kiểm; vé SA-19 Claude làm | các lượt thử trong trần chung 16 USD (chủ dự án duyệt 2026-10-15), dry-run trước | **vé soạn xong 2026-10-15**, chờ giao; điều kiện trước: commit phần `src` đang dở |
