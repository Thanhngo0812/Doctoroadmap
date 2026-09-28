# Kiểm chứng v3-05b, 09b, 11b và Vertex AI — 2026-09-28

## Kết luận

- Vé 19 (đường gọi Vertex AI) **đạt nghiệm thu kỹ thuật**: LLM và embedding dùng Application Default Credentials, token được làm mới, giữ nguyên thân yêu cầu và định danh cache; vector Vertex chuẩn hoá L2. `.env` cục bộ đã chuyển sang `vertex`/`global` với concurrency 2. Không chạy lại A8.
- `.env.example` để `DOC2ROADMAP_LLM_TRANSPORT=developer_api` làm mặc định an toàn; `.env` đang đặt `vertex` và project `gen-lang-client-0947038321`, nên lượt chạy trong báo cáo dùng Vertex. `DOC2ROADMAP_ROADMAP_STAGE_FLOOR` thuộc A10 xếp tầng cũ, hiện không được `Settings` đọc và đã được bỏ khỏi `.env` cục bộ thay vì quảng bá một biến vô hiệu trong mẫu.
- Ba vé chất lượng đã được triển khai và chạy lại. **Chưa thể tuyên bố roadmap đạt chuẩn**: doc-2 còn 13/57 cạnh vàng ngoài phạm vi và Q7 = 0,469. Cần xử lý đầu vào A3/định danh khái niệm và đối chiếu vàng trước khi dùng làm lộ trình chuẩn.
- Các con số dưới đây lấy từ `artifacts/v3-05b-a9v10-evaluation/`, dùng **A9 v10**. Lượt `artifacts/v3-05b-evaluation/` trên A9 v9 chỉ là chẩn đoán, không trộn vào điểm cuối.

## Dòng chạy và khả năng tái dùng

Sáu tài liệu được chạy `AnchorConcepts 05b → JudgeIdentity 10b → NameConceptLabels 11b → BuildRoadmap → NameModules 09b`. Đầu vào neo là artifact A9 v10; danh tính, nhãn, roadmap và tên cùng nằm trong một kho thử. Doc-1/doc-2 được chạy trước; lượt sáu tài liệu sau đó tái dùng hoàn toàn hai kết quả ấy. Neo A9 v10 chỉ cần hỏi lại 5 khái niệm doc-2; 397 phán quyết doc-2 và toàn bộ phán quyết neo của năm tài liệu khác được tái dùng.

| Tài liệu | Khái niệm trong dãy | Module | Trùng tên module | Chỉ-nhắc/chưa kiểm trong dãy | Nhãn số còn lại |
| --- | ---: | ---: | ---: | ---: | ---: |
| doc-1 | 199 | 32 | 0 | 0 | 1 |
| doc-2 | 307 | 48 | 0 | 0 | 0 |
| doc-3 | 22 | 3 | 0 | 0 | 0 |
| doc-6 | 12 | 2 | 0 | 0 | 0 |
| naive-bayes | 20 | 3 | 0 | 0 | 0 |
| nhap-mon-ml | 54 | 9 | 0 | 0 | 0 |

Đây là phần đếm R11 liên quan trực tiếp đến ba vé, không phải khẳng định mọi điều kiện R11 đều bằng 0. Vẫn có 8 tiêu đề dài hơn 12 từ ở doc-1 và 5 ở nhap-mon-ml; doc-2 còn tên nền quá chung như `Chapter 1`, `Chapter 9`, `6B`.

## Chất lượng có vàng

| Tài liệu | Cạnh vàng được giữ đúng | Đảo thứ tự | Ngoài phạm vi | Q6 `learning_order_error` | Q7 coverage | Q7b precision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| doc-1 | 35/39 | 1/39 | 3/39 | 0,103 | 0,825 | 0,660 |
| doc-2 | 44/57 | 0/57 | 13/57 | 0,228 | 0,469 | 1,000 |

`0` cạnh đảo của doc-2 **không** có nghĩa Q6 bằng 0: 13 cạnh ngoài phạm vi vẫn bị tính trong `learning_order_error`. Q7 thấp hơn kỳ vọng của vé 05b; không lấy `rate` (chỉ xét cặp còn trong phạm vi) thay cho điểm tổng.

### Đọc neo doc-2

- `Matrix of a linear map`: neo ở khối dạy thực, order 343, thay vì câu xem trước đầu chương.
- `Column-row factorization`: neo ở khối dạy, order 391.
- `Matrix`: vẫn neo order 343, cùng chỗ với `Matrix of a linear map`. Node A3 tên `Matrix` có mô tả “representation of a linear map with respect to chosen bases”, tức tên và nghĩa đã nhập nhằng **trước** vé 05b. Luật chọn câu không thể biến node đó thành định nghĩa ma trận tổng quát.
- `Jordan basis`: vẫn `uncertain`; không nên tự coi là khái niệm được dạy.

Vé 05b sửa lỗi tuyển chọn/ưu tiên câu và có test chứng minh khối dạy được giữ trong top 6 ngay cả khi sáu trích dẫn A3 chiếm chỗ. Việc còn lại là phân loại/định danh lại `Matrix` ở A3, rồi đo lại phạm vi của các cạnh vàng. Không nên chỉnh tay điểm số hay ép neo vào một câu không thuộc nghĩa của node.

### Đọc tên doc-1/doc-2

- 09b: không còn tên module trùng, phần phụ lặp nguyên tên nền hay `(1/1)` trong hai tài liệu kiểm; một số tên nền chung và tiêu đề dài vẫn cần cải thiện từ cây mục/thiết kế module, không thuộc luật phần phụ mới.
- 11b: doc-1 có tên hiển thị cho 7/8 nhãn `Tính chất 1–4`, `Định lý 4–7`. `Tính chất 3/4` đã lấy được nội dung sau dòng nhãn. `Định lý 4` giữ nhãn cũ và ghi `display_name quá dài` sau khi bộ kiểm bác tên không hợp lệ, đúng fallback đã đặc tả; `Tính chất 1` còn tên hơi chung.

## Vertex, tiền và kiểm thử

- Lời gọi REST JSON nhỏ đã thành công; embedding `gemini-embedding-001` 768 chiều giữa Developer API và Vertex có cosine ≈ 1, sai khác tối đa sau chuẩn hoá 6,56×10⁻⁹. Dry-run A6 khi đổi transport vẫn tái dùng cache.
- Lượt **cuối trên A9 v10**: 1.511 lời gọi Vertex, 0,42305925 USD theo token trong sổ, 0 lần 429, 0 reservation còn treo. Lượt **chẩn đoán A9 v9**: 2.384 lời gọi, 0,9482885 USD ghi nhận, 34 lần 429 và 1 reservation cũ chưa tất toán do lần chạy bị ngắt. Tổng ghi nhận hai sổ = 1,37134775 USD, **không phải số tiền hoá đơn Cloud đã xác nhận**. Cả hai dưới trần dự án 50 USD; credit 300 USD do chủ dự án cung cấp chưa được xác minh qua Billing.
- Giá đối chiếu ngày 2026-09-28: [Google Cloud Vertex AI pricing](https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing), Gemini 3.1 Flash-Lite global, input 0,25 USD/triệu token, output 1,50 USD/triệu token. Sổ tính theo giá REST standard, không giả định giá Batch/Flex.
- Toàn bộ `tests/unit` và `tests/integration` xanh với `--basetemp=tmp/pytest-v3-vertex-20260928-2 -p no:cacheprovider`. Lần gọi pytest trước đó không có `--basetemp` lỗi quyền tại `%LOCALAPPDATA%/Temp/pytest-of-ngoco`; đây là lỗi môi trường tạo fixture, không phải kết quả test logic.

## Quyết định tiếp theo

Giữ vé 19 hoàn tất. Ba vé 05b/09b/11b đã có mã, test và artifact; 05b **chưa đóng chất lượng** vì doc-2 Q7 và 13 cạnh ngoài phạm vi. Không dùng chỉ số “0 cạnh đảo” để chấp nhận roadmap doc-2. Ưu tiên một vé nhỏ xử lý sai nghĩa/đồng nhất `Matrix` từ A3 và kiểm tra 13 cạnh vàng ngoài phạm vi; chỉ chạy lại các stage bị thay đầu vào, không chạy A8 nếu bằng chứng chưa yêu cầu.
