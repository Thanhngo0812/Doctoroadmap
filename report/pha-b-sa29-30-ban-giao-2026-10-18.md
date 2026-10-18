# Bàn giao SA-29–30 — 2026-10-18

Triển khai theo spec khâu tên sửa ở `e3b4f2d` và quyết định soát SA-25–28. Chủ dự án yêu cầu tiếp tục hai vé và đã duyệt chi phí trong phiên này; không yêu cầu duyệt lại. Chỉ dùng sáu cuốn phát triển, không đọc tập giữ lại T-01, tập khóa D-02 hoặc giá trị cache live.

## SA-29: phục hồi tên tốt và sửa mô tả

- Bước 1, cache SA-28: giữ **144/160 tên LLM**, 0 lời gọi mới, 0 USD. Tên và mô tả được kiểm riêng; lỗi mô tả không loại tên tốt.
- Bước 2, cùng phản hồi cũ: giữ **79 mô tả LLM**, 81 mô tả khuôn, 0 lời gọi mới, 0 USD. Từ vựng mô tả thêm đoạn dạy và âm tiết ở ít nhất `max(3, 0,02 × số đoạn)` của chính cuốn. Luật mượn từ module ±1 chạy bằng mã; từ vựng tên giữ nguyên.
- Đã đối chiếu đúng mốc 82 của Claude: phép cũ kiểm gộp tên và mô tả, mở rộng cả từ vựng tên. Phép mới có 87 mô tả đạt độc lập trước kiểm mượn, rồi loại 8 còn 79; giao giữa tên đúng luật và mô tả trước mượn là 81. Một tên chỉ được phép cũ cho qua nhờ tập từ mở rộng giải thích 82 so với 81.
- Prompt mới cấm tự xưng, mô tả bắt đầu thẳng bằng điều được dạy. Input gửi từ vựng nội dung, không gửi toàn bộ tập từ theo tần suất cuốn.

Chi tiết và số liệu từng cuốn: [báo cáo SA-29](pha-b-sa29-2026-10-18.md). Lượt Vertex mới dùng `gemini-3.1-flash-lite`, ghim 160 module trên các nguồn A10 v52/v37/v37/v24/v63/v22, kho riêng. Preflight ngay trước chạy có mức dự phòng theo byte request và trần output **0,432635 USD**, dưới cap **0,50 USD**; gate kiểm trước mỗi lần gửi, tính cả retry.

**Lượt có tiền đã hoàn tất:** 160 lần gửi HTTP, 160 phản hồi được ghi, không có dòng usage thất bại. Chi phí theo token ghi nhận **0,142519 USD / trần 0,50 USD**; khoản dự phòng 0,432635 USD không phải chi phí tính theo token. Không gọi thêm lượt để sửa kết quả.

| Cuốn | Bản tên mới | Tên LLM | Mô tả LLM / khuôn | USD ghi nhận |
|---|---:|---:|---:|---:|
| doc-1 | v57 | 29/33 | 1 / 32 | 0,02652175 |
| nhap-mon-ml | v50 | 10/15 | 6 / 9 | 0,01184275 |
| naive-bayes | v49 | 5/5 | 1 / 4 | 0,00409450 |
| doc-6 | v29 | 1/2 | 0 / 2 | 0,00161425 |
| xstk-ch3-1 | v68 | 11/14 | 5 / 9 | 0,01181075 |
| doc-4 | v27 | 80/91 | 69 / 22 | 0,08663500 |
| **Tổng** | | **136/160** | **82 / 78** | **0,14251900** |

Cả sáu đồ thị giữ nguyên trường ngoài tên/mô tả và metadata naming. Mô tả dự phòng giảm từ 135 ở SA-28 còn 78, nhưng vẫn còn nhiều, đặc biệt doc-1 chỉ giữ 1/33 mô tả LLM. Các cờ mô tả là 70 `description_vocabulary`, 6 `description_borrowed`, 2 `description_references`. Tên của lượt sinh mới còn 24 trường hợp dự phòng; số 144 ở bước 1 là tên từ cache cũ, không phải số tên được giữ trong lượt mới. Các hạn chế này cần được đọc và quyết định ở bước soát, không tự nới luật hoặc coi mọi nội dung đã đạt.

Đọc lại sáu trường hợp doc-4 có từ “nội dung” cho thấy đây là thuật ngữ môn học, không phải cách tự xưng; không phát hiện mẫu meta “module này/chương này/bài này”. Một số mô tả được giữ có ba câu trong một trường `text` dù prompt yêu cầu 1–2 câu. Schema giới hạn số mục mô tả, chưa kiểm số câu ngữ pháp trong từng mục; đây là điểm để Claude soát nội dung, không che bằng số đếm qua luật.

## SA-30: sửa bài giảng, câu trích và tài liệu

| Nhánh | Trước → sau phát lại | Tiền phát sinh |
|---|---|---:|
| 12 bài giảng nhóm 2 | 9 ready / 3 fallback → **11 ready / 1 fallback** | 0 USD |
| 6 tài liệu nhóm 2 | 4 ready / 2 failed → **6 ready** | 0 USD |

K6 chỉ dò chữ của các ý và câu tự kiểm tra, không dò quote hay khung JSON; vẫn giữ lỗi cắt output. `lecture_validator_version` tăng lên 3. Bài không ready không được lưu bền: kết quả lỗi chỉ có TTL ngắn trong RAM (mặc định 60 giây), hết TTL được sinh lại, các yêu cầu đồng thời vẫn chia sẻ một lần sinh. Cache fallback bền cũ cũng bị loại nếu gặp lại.

Câu trích cạnh dùng `BSettings.quote_max_chars` (mặc định 200) thay số 120. Cắt ở ranh giới câu hoặc từ và giữ đúng offset nguồn; giới hạn tùy chỉnh đi qua cả ngữ cảnh bài giảng, trợ lý và công cụ why_here. Tài liệu chọn câu nguyên văn trong nguồn đã nạp khi quote của mô hình sai; không phục hồi nhãn bịa. Sau hậu kiểm, bỏ tiêu đề rỗng và dòng chỉ dấu câu. Replay tài liệu sửa 17 quote; các vị trí citation đã được kiểm lại với nguồn gốc.

Bài còn fallback là doc-6 “Mô hình dữ liệu quan hệ”: cả lượt đầu và lượt sửa còn thiếu hai ý giải thích theo K8 sau lọc K2/K3/K5/K7. Không thay prompt bài giảng hoặc quyết định giao diện khi bài hỏng hẳn, đúng phần ngoài vé.

Chi tiết: [K6/cache/replay bài giảng](pha-b-sa30-2026-10-18.md), [tài liệu/câu trích và sáu bản đọc](pha-b-sa30-documents-quotes-2026-10-18.md).

## Phép đo thời gian và kiểm thử

- Stream: đồng hồ bắt đầu trước request, kết thúc ở mẩu text hoặc lời gọi công cụ đầu tiên, gồm cả thời gian chờ headers. JSON không stream đo tới byte response đầu tiên; đây là TTFB của response JSON, không phải thời gian tới chữ của một luồng giao diện.
- Trợ lý ghi riêng TTFT của từng vòng công cụ, không chép TTFT vòng đầu cho mọi dòng. Kết quả tổng hợp giữ thời gian tới phản hồi đầu của lượt hỏi.
- Metadata được lưu trong recording rồi phát lại nguyên số đã ghi. Không lấy tốc độ replay để điền số thiếu; các fixture bài giảng cũ ghi 0 được báo là chưa có số đo.
- Năm test adapter mới đã đỏ trước sửa. Đồng hồ giả mô phỏng chờ headers 2 giây, byte/mẩu đầu sau 0,5 giây và phần còn lại 3 giây: TTFT phải 2.500 ms, tổng JSON 5.500 ms. Các test riêng xác nhận per-round assistant, replay giữ metadata, và lỗi parse vẫn ghi TTFT cùng usage.

Các hồi quy nghiệp vụ có test thấy đỏ trước hoặc phép sửa sai trong bộ nhớ. Bộ ghép cuối gồm **206 test xanh** trên 28 tệp (Pha B, learning graph, ảnh công thức, kiến trúc và runner). Lệnh dùng `.tools/uv.exe run pytest`, basetemp `tmp/pytest-sa2930-final-20261018`, `-p no:cacheprovider -ra`; HTTP localhost chạy ngoài sandbox. Có hai deprecation warning của SWIG. Một lượt ghép trước có lỗi quyền thay tệp JSON tạm trên Windows; chạy lại store/cache trong thư mục mới và bộ ghép cuối đều xanh, không đổi mã persist để xử lý lỗi tạm đó.

Các runner được lưu trong `scripts/phase-b/`, gồm adapter input SA-28 lịch sử để tái lập bước 1/2 sau khi prompt mới đã đổi. Cache check sau lượt mới có 0 miss và SHA-256 ledger không đổi. Không commit fixture/đầu ra giáo trình, không kèm thay đổi Pha A ngoài phạm vi.

Claude vẫn cần đọc nội dung và ghi phán xét vào hai vé. Số lượng ready và trích dẫn đúng vị trí là bằng chứng chạy được theo luật, không tự thay thế việc soát chất lượng.
