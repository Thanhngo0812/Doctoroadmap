# SA-45 — Soát tài liệu SA-30 và quiz/tài liệu SA-37, ngày 2026-10-18

**Phán xét:** phần tài liệu của SA-30 **đạt có ghi chú**; SA-37 **chưa đạt**, sửa ở SA-46 và SA-50. Phần bài giảng của SA-30 có báo cáo soát riêng. Chi phí đợt soát: 0 USD; không dựng adapter provider.

## Test và thử sửa sai

Lệnh đã chạy:

```powershell
.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider --basetemp tmp/sa45-artifacts-tests tests/unit/application/test_phase_b_b2_artifacts.py tests/unit/application/test_phase_b_sa30_documents.py tests/unit/application/test_phase_b_lectures_documents.py tests/unit/application/test_phase_b_sa25.py tests/unit/application/test_phase_b_quiz.py tests/unit/application/test_phase_b_quiz_sa27.py tests/unit/domain/test_learning_graph.py tests/unit/test_architecture.py --junitxml tmp/sa45-artifacts-tests.xml
.venv/Scripts/python.exe scripts/phase-b/sa45_artifact_mutations.py
.venv/Scripts/python.exe scripts/phase-b/sa45_document_response_audit.py
```

JUnit xác nhận **91 passed, 0 failed** trên bộ test hiện hành. **4/4 mutation phần tài liệu/quiz bị bắt** bằng assertion thất bại: cho tài liệu sáu module qua; lấy mẫu quiz bỏ tiến độ; trả đáp án trong đề công khai; giữ tiêu đề rỗng sau hậu kiểm. Script sau đó được bổ sung một mutant trần nhắc nền SA-36, cũng bị bắt (tổng 5/5). Chi tiết stdout của từng mutant ở `tmp/sa45-artifact-mutations.json`. Mutant chỉ sửa hàm trong bộ nhớ của tiến trình test con, không sửa nguồn trên đĩa.

Sáu assertion mới của `tests/unit/application/test_phase_b_sa45_artifact_audit.py` đã thấy đỏ: năm assertion đầu ở `tmp/sa45-quiz-all-red.xml`, assertion Q3 chạy riêng. Các test giữ `xfail(strict=True)` với số vé sửa; chạy lại bằng `--runxfail` để thấy lỗi hiện hành, không tính chúng là test xanh.

## SA-30: đọc đủ sáu tài liệu và kiểm lại nguồn

Đã đọc toàn bộ Markdown sáu kết quả lịch sử và sáu kết quả qua mã hiện hành B2. Script cũ `sa30_documents_replay.py` từ chối vì hash prompt/settings B1 khác B2. Không tắt kiểm hash trong adapter: script audit mới nạp đúng sáu phản hồi lịch sử, kiểm ghép theo câu yêu cầu và node nguồn, rồi đưa nguyên payload qua `DocumentUseCase` B2. Kết quả này là **phát lại phản hồi**, không khẳng định prompt B2 sẽ sinh giống mô hình cũ.

Đếm độc lập trong `tmp/sa45-document-response-audit.json`: **6/6 ready, 17 câu trích được mã chọn lại, 0 lỗi offset**, sáu dòng ledger có `replayed=true`, tổng 0 USD, 0 HTTP. Mỗi quote được so trực tiếp với lát văn bản chunk từ `char_start/char_end` đã trừ gốc chunk; không chỉ đọc cờ hậu kiểm.

| Cuốn/khái niệm | Nội dung đã đọc | Ghi chú |
|---|---|---|
| doc-1 / Tập hợp | Tập hợp/phần tử, tập con, bằng nhau, tập rỗng | Có thân bài, không còn chỉ tiêu đề; nguồn S1/S2. |
| nhap-mon-ml / Dữ liệu | Thu thập dữ liệu, đại diện mẫu, tiền xử lý, nhãn | Không còn tiêu đề ghi chú rỗng; khối ngoài sách vẫn là lời nhận xét chung về AI. |
| naive-bayes / Supervised Learning | NBC, ưu điểm, phân phối, hạn chế | Đủ nội dung/citation; câu toán ở dạng văn bản trích từ nguồn, chưa đánh giá hiệu quả dạy học. |
| doc-6 / CSDL | Tổng quan, DBMS, từ điển dữ liệu, sao lưu | Khối ngoài sách là lời khuyên ôn thi, chưa phải ví dụ cụ thể. |
| xstk / Tổng thể | Định nghĩa, đặc trưng, quan hệ với mẫu | Ký hiệu nguồn còn thô `σ 2`; không tự diễn giải thành công thức mới. |
| doc-4 / Hình thái ý thức xã hội | Cấu trúc, quan hệ, chính trị/khoa học | Có nguồn ở các ý; khối ngoài sách vẫn khá chung. |

Các ghi chú về khối ngoài sách và văn phong đã có từ đợt soát trước; chúng không làm sai tiêu chí sửa tiêu đề, quote nguyên văn và offset của SA-30. Giữ cho bước đánh giá nội dung, không đổi spec/prompt bằng quyết định riêng của người soát.

## SA-37: lỗi được tái hiện và vé sửa

**SA-46 — phạm vi lộ trình đi từ công cụ trợ lý:** `make_quiz(scope='roadmap')` bỏ qua nhánh lấy mẫu vì cờ `roadmap_scope` chỉ nhận object có `kind`. `PhaseBRuntime.assistant` truyền dạng chuỗi từ công cụ, nên đây là đường gọi thực tế. Đồ thị giả 18 khái niệm có ngân hàng đầy đủ trả **18 câu**, trong khi object canonical cùng seed chỉ lấy 10. Với cấu hình trần 3, object canonical kèm `n=10` vẫn trả 10. Ba assertion đầu kiểm các hậu quả này.

**SA-50 — câu điền khuyết bỏ qua luật:** phát lại doc-4 v27, seed 37 bằng `QuizUseCase` không mô hình, kho trong bộ nhớ: **4 câu / 4 module / 0 USD**, khớp số bàn giao. Đã đọc cả bốn câu, không chỉ đếm. Câu Chủ nghĩa duy vật chất phác có phương án "Chủ nghĩa duy vật" chứa trong đáp án; câu Phương pháp luận chung có ba phương án chứa nhau. Q3 không được áp dụng trong `_cloze_bank`. Ca tổng hợp khác tạo được đề có `[formula]` thiếu ảnh (Q6) và câu dẫn "ba điều kiện sau đây:" không có phần điều kiện. Ví dụ JSON doc-1 cũng có câu Tích trực tiếp/Nhóm dừng ở phần "sau đây". Ba assertion cuối kiểm các lỗi này; không sửa dữ liệu/neo của Pha A.

Các đường đã đạt của SA-37: scope tài liệu được tính theo module hiện hành; sáu module bị chặn trước provider; năm module được tạo với mô hình giả; ngưỡng remap đọc cấu hình; seed canonical, ưu tiên đã học, giới hạn số câu canonical mặc định; đề trước nộp không chứa đáp án; nộp cập nhật tiến độ qua use case. Lỗi đồng thời của tiến độ và ngân sách có vé SA-47/48 riêng.

## JSON và trang xem thử

Đã đọc trực tiếp ví dụ session/lượt/thư viện/quiz/tài liệu của `report/pha-b2-contract-examples-2026-10-18.json`: cùng ID tài liệu tạo tại module 1 về module 2 có nhóm `here` và `elsewhere`, còn sau xoá phiên; phạm vi nơi tạo khác phạm vi nội dung; lượt lưu cả câu hỏi và `answer-2`; quiz công khai có options nhưng không có đáp án. Nội dung DemoModel của tài liệu chỉ là một câu trích ngắn, dùng kiểm hợp đồng, **không phải mẫu để kết luận chất lượng sinh bài**. `quiz.graph_version` trong ví dụ là null nếu bên gọi bỏ tham số; cần phía web truyền phiên bản khi ghi lần làm.

Chạy thêm `tests/unit/presentation/test_phase_b_preview.py` và `test_phase_b2_cli.py` bằng localhost ngoài sandbox: **13 passed** (11 HTTP + 2 CLI), JUnit `tmp/sa45-preview-tests.xml`. Vé 44 đạt theo chủ dự án miễn thao tác/ảnh; không ghi kết quả tự động thành đã thử giao diện.

## Phạm vi còn chưa chắc

Đây là review mã và phản hồi đã ghi, không đo lại chất lượng hay độ trễ của prompt mới trên Gemini. Không có thêm lượt có tiền. Các lỗi đã được lập vé sửa; SA-45 không tự cài SA-46/50 trong lượt soát này. Chỉ các artifact sáu cuốn phát triển được dùng trong các script audit nêu ở đây.
