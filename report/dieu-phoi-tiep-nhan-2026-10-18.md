# Tiếp nhận điều phối — 2026-10-18

**Trạng thái:** Codex chính thức nhận điều phối theo yêu cầu trực tiếp của chủ dự án. Đã hoàn tất đối chiếu ban đầu; SA-45 và các vé web chưa được coi là đã giao hoặc nghiệm thu qua báo cáo này.

**Mốc mã đối chiếu:** nhánh `main`, HEAD `3871c85`. Không sửa mã sản phẩm, không chạy lượt mô hình trả phí, không mở tập giữ lại hay phần cache của `artifacts/phase_b/live.json`.

**Cập nhật thương hiệu 2026-10-19:** chủ dự án xác nhận logo là 20 tệp `design/Artboard 9.png` đến `design/Artboard 28.png`, đã kiểm đủ và xem ảnh.
Artboard 21–24 đen nền trong, 25–28 trắng nền trong; bảng dùng ở spec thiết kế mục 1. Các ghi nhận thiếu logo ngày 18 bên dưới là lịch sử, không còn chặn W-01/W-22.

## 1. Kết luận để ra quyết định

Việc cần làm ngay là **giao SA-45 cho người soát độc lập và khởi động W-01 cho nhóm web**. Yêu cầu commit B2 trong bản bàn giao cũ đã hoàn thành. Nhân viên lõi có thể nhận phần xác định chuỗi dựng của W-13, rồi ưu tiên sửa SA-46+ nếu người soát tìm thấy lỗi. Người thiết kế làm W-22; cập nhật 2026-10-19 đã có logo Artboard 9–28, phần thương hiệu không còn chờ tài sản này.

Dự án đang chuyển từ lõi đã triển khai sang kiểm chất lượng và tích hợp sản phẩm. Điểm nghẽn hiện tại là **nghiệm thu và nền web**, không phải thiếu thêm tính năng học trong spec.

## 2. Căn cứ và giới hạn đợt tiếp nhận

Đã đọc bản bàn giao điều phối; hai bảng kế hoạch Pha B/web; AGENTS.md; README và CONTEXT; các phần hợp đồng, kiến trúc, tiền, kiểm thử của spec Pha B/B2/web; yêu cầu cơ sở dữ liệu và thương hiệu; SA-45; W-01/W-05/W-13/W-22; báo cáo SA-29–30 và bàn giao B2 cùng bốn báo cáo con. Đã đối chiếu các điểm nối trong mã thay vì chỉ đọc báo cáo.

Đã kiểm Git, đường dẫn sản phẩm, tài sản thiết kế, gói giao agentic; đọc trực tiếp sáu đồ thị phát triển để đếm lại phiên bản và kết quả naming; đọc cấu trúc ví dụ JSON; chạy bộ kiểm 280 test và bảy phép sửa sai phần nền.

Đây là phân tích để điều phối. Chưa làm đủ quy trình SA-45: chưa đọc và phán xét toàn bộ 160 tên/mô tả, sáu tài liệu và 12 bài giảng; chưa thử sửa sai mọi điểm canh giữ; chưa thực hiện bảy thao tác trình duyệt của SA-44. Không dùng kết quả test để tự đóng vé nội dung.

Không suy diễn tình trạng tài khoản Cloudinary/Gmail từ việc có spec. Chưa kiểm bí mật trong `.env`; chỉ xác nhận lệnh Docker/Node/npm tồn tại trên máy này, chưa xác nhận Docker daemon, WSL2 hoặc môi trường của bốn thành viên nhóm web đã sẵn sàng. Chưa kiểm các chat khác, nên tình trạng giao việc ngoài checkout cần chủ dự án xác nhận khi phân người.

## 3. Bản đồ hệ thống thực tế

| phần | trách nhiệm | bằng chứng hiện có | việc điều phối |
|---|---|---|---|
| Pha A | đọc PDF/DOCX, chunk, ứng viên, hợp nhất/neo, chỉ mục, cạnh tiên quyết, dãy học/module | có mã lõi, artifact phát triển và báo cáo riêng | giữ ranh giới phiên pha A; W-13 phải xác nhận chuỗi cho cuốn mới |
| Pha B | đọc đồ thị, đặt tên/mô tả, truy hồi, trợ lý, bài giảng, quiz, tài liệu | đã triển khai; SA-25–27 đã có phán xét trước; SA-28 chuyển SA-29 | ưu tiên SA-29/30 và các lượt thật còn thiếu |
| Pha B2 | phạm vi, phiên đủ lượt, tiến độ, thư viện, trần ngày, `lecture-2`, xem thử hai trang | hai commit B2, bộ kiểm đang xanh, có JSON ví dụ | soát độc lập SA-31…44, nội dung SA-43 và giao diện SA-44 |
| WayFinder | tài khoản, khoá học, quyền thành viên, tải/dựng sách, chia sẻ, quản trị, giao diện | có ba spec, ADR 0020–0023, 23 vé; chưa có `src/web` | bắt đầu nền W-01, rồi đi theo phụ thuộc; chưa phải web đã hoàn thiện |
| Đánh giá | chất lượng tên, bài giảng, quiz, trợ lý | vé SA-20…23 và gói 19a đã chuẩn bị | chờ các sửa/B2 được soát; ghim mã, đồ thị, prompt trước chạy |

Ranh giới tích hợp đã chốt: `wayfinder` gọi `doc2roadmap`; lõi không import web. Mã web ở `src/web/backend/wayfinder` và `src/web/frontend`; dùng một `pyproject.toml` và `.venv`. Chỉ W-05/W-13 được đổi phần lõi theo phạm vi vé. React và API cùng nguồn; PostgreSQL giữ dữ liệu web/Pha B; Cloudinary giữ tệp gốc và ảnh riêng tư; artifact Pha A ở đĩa; worker dựng tách khỏi API.

`LearningGateway` kiểm thành viên, lấy `owner` từ tài khoản và `doc_id`/phiên bản từ khoá học rồi gọi Pha B. Dữ liệu học theo người × cuốn, không theo khoá học; hai khoá cùng cuốn dùng chung tiến độ/phiên của một người. Đây là hợp đồng cần giữ trong mọi vé tích hợp.

B2 neo phạm vi phiên bằng tập `node_id`, không bằng mã module dễ thay đổi. Cache bài giảng dùng chung không chứa tiến độ cá nhân; nhãn được gắn khi trả bài. Sau cổng hai ý đạt, lỗi đuôi chỉ làm ngắn bài. Bài hỏng giữ khung và đường đọc nguồn/hỏi trợ lý, không trả bài trích câu dự phòng. Những hành vi này phải được đối chiếu trong SA-45 và ảnh nghiệm thu web.

Hai cuốn nhap-mon-ml và naive-bayes vẫn ở chuỗi v3 theo quyết định Q17: không chạy lại bằng chuỗi gộp. Thiếu câu trích cạnh ở hai cuốn này được xử lý bằng phần gợi lại không có câu nối, không tự coi là lý do chạy lại trả phí. Hợp đồng B2 thay B1 có chủ đích, không yêu cầu di trú phiên B1 ngoài spec.

## 4. Những thông tin trong bàn giao cần cập nhật

| nội dung | bàn giao ban đầu | đối chiếu lúc tiếp nhận | hệ quả |
|---|---|---|---|
| commit B2 | còn khoảng 28 tệp chưa commit | `a7f57d0` ghép B2; `3871c85` sửa lỗi cắt đuôi; `src/` sạch | bỏ việc giao commit lại; soát cả hai commit |
| số test B2 | 279 | bản bàn giao B2 mới và lượt chạy hiện tại: 280 | dùng kết quả hiện tại, ghi rõ phạm vi |
| logo | nói đã có `logo1`…`logo8` | `rg --files design` chỉ thấy OTP1…6 và GIF | cần cung cấp/chỉ vị trí; chưa nghiệm thu thương hiệu |
| trần học | câu hỏi có bỏ hay không | spec web đã ghi giữ 0,20 USD/người/ngày và 5 USD/ngày nội dung chung | không mở lại quyết định nếu chủ dự án chưa yêu cầu đổi |
| SA-43 | SA-45 vẫn ghi chờ duyệt lượt thật | báo cáo B2 ghi đã chạy, 0,06523425 USD/trần 0,50 USD | giao soát nội dung/bằng chứng, không giao chạy trả tiền lại |
| `ready-for-agent` | mọi vé web có nhãn này | nhiều vé còn phụ thuộc chưa đạt | nhãn sẵn sàng của vé không tự xoá điều kiện chặn |

Đã cập nhật mục 2, 3, 5, 8, 10 của bản bàn giao để người tiếp theo không lặp việc cũ. Không sửa spec, ADR hoặc phán xét của người soát.

## 5. Kết quả kiểm chứng

### 5.1. Kiểm thử kỹ thuật

Lệnh đã chạy, từ gốc repo:

```powershell
$coordTests = @(rg --files tests/unit/application tests/unit/infrastructure tests/unit/presentation -g 'test_phase_b*.py')
$coordTests += @('tests/unit/domain/test_learning_graph.py', 'tests/unit/test_architecture.py')
& '.venv/Scripts/python.exe' -m pytest @coordTests --basetemp tmp/pytest-dieu-phoi-localhost-20261018 -p no:cacheprovider -ra --junitxml=tmp/dieu-phoi-tests-localhost-20261018.xml
```

Kết quả: **280 passed**, 18,72 giây; hai cảnh báo SWIG. Đây là bộ Pha B/B2, LearningGraph và kiến trúc được chọn bằng lệnh trên, **không phải toàn bộ test repo**. Bao gồm 11 test trang xem thử; HTTP dùng dữ liệu giả và localhost.

Lượt sandbox trước đó: 272 đạt, tám test HTTP lỗi `WinError 10013` khi kết nối localhost. Chạy lại cùng bộ ngoài sandbox sau bước cấp quyền cho kết quả 280 đạt. Không ghi tám lỗi quyền này thành lỗi sản phẩm.

```powershell
& '.venv/Scripts/python.exe' scripts/phase-b/b2_foundation_mutations.py
```

Kết quả: **7/7** bản sai bị assertion bắt: dùng mã module cũ; xoá không tác dụng; bỏ lọc tài liệu; quiz ghi đè lựa chọn người học; tắt trần ngày; cho ghi sổ thiếu người học; bỏ kiểm trần trước gọi mô hình. Script sửa trong tiến trình thử, không sửa tệp sản phẩm.

Bằng chứng máy đọc ở `tmp/dieu-phoi-tests-localhost-20261018.xml`, `tmp/phaseb-b2-foundation-mutations.json`.

### 5.2. Đếm lại artifact phát triển

Chỉ nạp sáu tài liệu cho phép bằng `JsonArtifactStore(Path('artifacts'))` và `load_learning_graph`; không đọc kho `live.json`.

| tài liệu | đồ thị | module | khái niệm học | tên LLM | mô tả LLM | mô tả khuôn |
|---|---:|---:|---:|---:|---:|---:|
| doc-1 | 57 | 33 | 205 | 29 | 1 | 32 |
| nhap-mon-ml | 50 | 15 | 75 | 10 | 6 | 9 |
| naive-bayes | 49 | 5 | 33 | 5 | 1 | 4 |
| doc-6 | 29 | 2 | 11 | 1 | 0 | 2 |
| xstk-ch3-1 | 68 | 14 | 82 | 11 | 5 | 9 |
| doc-4 | 27 | 91 | 495 | 80 | 69 | 22 |
| **tổng** | | **160** | **901** | **136** | **82** | **78** |

Số đếm khớp báo cáo SA-29. Tên LLM chiếm 85%; mô tả LLM 51,25%. Tỉ lệ LLM thấp tự nó chưa chứng minh mô tả sai, nhưng doc-1 chỉ 1/33 là tín hiệu cần đọc phản hồi bị loại và kiểm luật từ vựng. Không tự nới luật bằng quyết định điều phối.

Đã parse ví dụ JSON B2 và thấy các phiên bản `session-1`, `turn-1`, `answer-2`, `library-1`, `progress-1`, `lecture-2`, `quiz-2`, `document-2`. Phạm vi là đối tượng `kind/node_ids` lồng trong các hợp đồng. Đây là kiểm có ví dụ và cấu trúc phiên bản, chưa phải xác nhận toàn bộ hợp đồng đúng ngữ nghĩa. Số đếm lưu ở `tmp/dieu-phoi-doi-chieu-20261018.json`.

## 6. Điểm nghẽn và cách xử lý

| ưu tiên | điểm nghẽn | bằng chứng / ý nghĩa | hành động và người phụ trách |
|---|---|---|---|
| 1 | SA-29/30/B2 chưa có phán xét độc lập | triển khai và test xanh chưa đủ điều kiện mở các vé tích hợp phụ thuộc | chủ dự án giao SA-45; người soát ghi từng phán xét và tạo SA-46+ nếu cần |
| 1 | web chưa có nền | chưa có `src/web`; W-02 và W-05 cần W-01 | nhóm web nhận W-01 ngay, không cần chờ toàn bộ nội dung B2 |
| 1 | thiếu bằng chứng trình duyệt SA-44 | 11 test HTTP không thay bảy thao tác/ảnh | chủ dự án thử hoặc giao người có quyền trình duyệt; lưu ảnh cho người soát |
| 2 | chuỗi dựng cuốn mới W-13 chưa xác nhận đủ | A4 đọc candidates; BuildMentions đọc retrieval; doc-6 đã có hai đầu vào này | nhân viên lõi xác nhận với phiên pha A qua chủ dự án trước cài, test cả đầu vào mới |
| 2 | W-05 có nguy cơ chặn nhóm web | W-06 cần W-05; bản JSON hiện là một tiến trình | giữ người lõi cho W-05 ngay khi W-01 đạt và sửa kho B2 đã ổn; W-13 không được làm W-05 treo vô thời hạn |
| đã giải quyết 2026-10-19 | tên/bộ logo | đủ Artboard 9–28, gồm bản nền trong | W-01/W-22 dùng bảng tệp thực ở spec mục 1, không chờ tám logo giả định |
| 2 | gói 19a chưa có đầu ra được nghiệm thu | thư mục giao tồn tại; chưa thấy kết quả soát | chủ dự án giao cho họ mô hình khác Gemini, chỉ giao gói công khai; người soát chạy checker sau khi nhận |
| 3 | câu hỏi chất lượng/thiết kế còn treo | doc-1 ít mô tả LLM; doc-4 thẻ khoảng 1.322 token; dữ liệu thời gian chỉ bốn mẫu | ghi và chuyển đúng người quyết; giữ spec hiện hành trong khi chờ |

### W-13: điểm kỹ thuật phải chốt

Đây là yêu cầu làm rõ chuỗi trong vé, chưa phải tự sửa spec:

- `src/doc2roadmap/application/use_cases/canonicalize.py`, `_run`: `load_latest_candidates(doc_id)` rồi đọc chunks theo version của candidates. A4 không tự thực hiện A3 trong đường này.
- `src/doc2roadmap/application/use_cases/build_mentions.py`, `_run`: đọc `load_latest_retrieval(doc_id)`.
- CLI tách `extract`, `index`, `a3`; `_a3` chạy trích ứng viên và lập chỉ mục. Báo cáo doc-6 chỉ là chạy lại A4/roadmap trên tài liệu đã có đầu vào, không chứng minh đường PDF mới hoàn toàn.
- Chuỗi dự kiến cần xét `ingest → [label-roles?] → A3/A3′ → A4/A5 → roadmap/A10/naming → chuẩn bị Pha B`, gom dưới bốn bước công khai đã chốt. Phiên pha A xác nhận vị trí chính xác, chế độ không vàng và cách dry-run khi đầu ra trung gian chưa có.
- Không báo tổng dự toán đầy đủ nếu downstream chưa biết. W-13 cần ghi rõ cách biểu diễn phần chưa biết, hỏi lại khi hợp đồng hiện hành chưa đủ; không lấy số của artifact cuốn cũ để giả làm dự toán cuốn mới.

Đây là lý do nên giao W-13 phần xác định chuỗi ngay, nhưng chỉ bắt đầu đổi mã khi đã chốt phối hợp và không đụng vùng phiên pha A đang sửa.

### Chất lượng bài giảng chưa đóng

Theo báo cáo SA-43, chi đã ghi là 0,06523425 USD trong khoản duyệt 0,50 USD; **không cần chạy trả phí lại để bắt đầu soát**. Sau sửa, replay nhánh nhiệt độ 0 có 10/12 ready, hai failed. Có các bài được báo trùng ý, lệch sang khái niệm lân cận hoặc chưa bao phủ đủ ý. `ready` là đạt luật/cổng, chưa phải đạt chất lượng sư phạm.

Nhánh nhiệt độ 1 có hai yêu cầu sửa không khớp recording, nên không được so sánh 9/12 với 10/12 để chọn nhiệt độ. p50 từ cổng tới hết 939 ms chỉ dựa trên bốn mẫu thật đầy đủ, với giới hạn mã đo đã nêu. Giữ stream S3 và nhiệt độ sửa 0 theo spec; gửi câu hỏi cho Claude/người có thẩm quyền thiết kế. Mọi lượt mới cần dry-run và chủ dự án duyệt riêng.

## 7. Kế hoạch giao theo điều kiện

Không tự hứa ngày hoàn tất khi chưa có người nhận và ước lượng của người làm. Dùng các mốc kiểm chứng sau:

| đợt | giao việc | điều kiện mở | đầu ra để chuyển bước |
|---|---|---|---|
| ngay | SA-45 cho người soát | có commit, đã đáp ứng | phán xét SA-29 rồi SA-30, tiếp tục B2 và SA-43; lỗi có vé SA-46+ |
| ngay | W-01 cho nhóm web | không phụ thuộc B2 được soát | nền FastAPI/React/PostgreSQL, đường kiểm bắt buộc, media-smoke, ảnh hai cỡ/sáng tối theo vé |
| ngay | W-13 phần xác định chuỗi cho nhân viên lõi | B2 đã commit; xác nhận không xung đột phiên pha A | chuỗi chuẩn cho cuốn mới, điểm hỏi, phạm vi tệp; sau đó triển khai theo vé |
| ngay | W-22 cho người thiết kế | spec token và Artboard 9–28 đã có | toàn bộ thiết kế, gồm thương hiệu theo bảng tệp thực; không còn chờ logo |
| ngay | gói 19a và chuẩn bị tài khoản/ảnh SA-44 | chủ dự án phân người/cấp tài khoản | đầu ra agentic để checker, ảnh thử tay, xác nhận cấu hình dịch vụ |
| sau W-01 đạt | W-02 và W-05 | mỗi vé có người phụ trách; không đụng sửa kho B2 | tài khoản/phiên và kho PostgreSQL được soát |
| sau W-02 đạt | W-03 và W-04 | giữ phạm vi dịch vụ/tệp không trùng | email và hồ sơ được soát |
| sau W-02/W-05 đạt | W-06 | cả hai vé đã có phán xét đạt | khoá học/gateway và kiểm quyền thành viên |
| sau W-06 | W-07, W-11; W-14 khi W-03 cũng đạt | W-07 còn cần SA-34 đạt | mở ba nhánh học, chia sẻ, tải/dựng |
| sau W-07 | W-08/W-09/W-10 | SA-39/40/41, SA-32/33/42, SA-35/37 tương ứng đã đạt | phần học thật qua gateway; chia rõ phạm vi hàm trong LearningGateway |
| tiếp theo | W-12/15/16/17/18/19/20 | dùng chính cột chặn bởi của từng vé | các lát dọc được nghiệm thu; không ép tuần tự nếu đủ điều kiện |
| cuối | W-21 và W-23 | đủ vé tiền nhiệm ghi trong bảng | bằng chứng triển khai/sao lưu/đầu-cuối và đối chiếu Figma |

Điều kiện B2 không được bỏ qua ở W-07…W-10. Hàng soát nên đi theo phụ thuộc 30 → 31 → 32/34, 38 → 39 → 40 → 41, rồi 33/35/36/37/42 theo tiền nhiệm và SA-43/44. Cần giữ thứ tự hàng đợi SA-29 → SA-30 trước; sau đó ưu tiên những vé B2 đang chặn tích hợp.

Với W-05, có thể phân người lõi làm phần port và người web làm PostgreSQL, nhưng phải chốt phần port trước và có một người chịu trách nhiệm ghép/nghiệm thu toàn vé. Không để hai người tự sửa chung tệp kho. W-06 rồi W-07 làm xong mới chia W-08/09/10, vì cùng thêm hàm vào LearningGateway.

SA-08/10/13 còn lượt thật sau sửa. Chỉ chuẩn bị dry-run sau khi người soát xác nhận nhánh liên quan ổn. SA-20…23 chạy sau các sửa/B2; SA-23 còn cần gói 19a được kiểm. Các mức tiền ghi trên vé là kế hoạch, không phải quyền tự chi trong đợt điều phối này.

## 8. Việc chủ dự án cần làm ngay

1. **Chọn/giao người soát SA-45** và người phụ trách W-01. Hai việc này quyết định tiến độ hiện tại.
2. **Giao nhân viên lõi W-13**, yêu cầu báo chuỗi chuẩn trước khi cài; bảo lưu năng lực làm W-05 ngay sau W-01 và sửa SA-46+ nếu phát sinh.
3. **Logo đã đủ, cập nhật 2026-10-19:** dùng Artboard 9–28 ở `design/`, theo spec mục 1. SVG và tệp gốc GIF có thể bổ sung nếu có; không yêu cầu cung cấp tám logo giả định hoặc vẽ lại.
4. **Chạy/giao bảy thao tác SA-44** theo báo cáo `pha-b2-sa37-44-2026-10-18.md`, có ảnh cho từng thao tác. Máy chủ ngoại tuyến được báo ở `http://127.0.0.1:18765/`, kho riêng `tmp/b2-preview-manual.json`; đợt tiếp nhận chưa xác nhận server hiện còn chạy.
5. **Giao đúng gói 19a** ở `Desktop/pha-b-cau-hoi-thu/giao-agentic/` cho họ mô hình khác Gemini. Thư mục giao tồn tại, có hướng dẫn/checker và các thư mục dữ liệu. Không giao thư mục người giữ đáp án.
6. **Chuẩn bị Cloudinary, Gmail và Docker trên máy nhóm web.** Bí mật chỉ đặt vào `.env`; báo đã cấu hình, cỡ tệp/tín dụng của tài khoản, kết quả smoke, không dán giá trị khoá vào chat. W-01 có thể triển khai với đồ giả trước, nhưng media-smoke và PostgreSQL thật vẫn là tiêu chí phải hoàn thành.

Các việc 3–6 có thể làm song song lúc người soát và nhóm web bắt đầu. Hiện không cần duyệt thêm tiền để đọc/soát dữ liệu đã ghi và làm các vé web 0 USD.

## 9. Lời giao việc sẵn để chủ dự án chuyển

### Giao SA-45

> Bạn nhận `task/sau-a10/45-soat-thay-claude-nhan-vien-cap-cao.md`. Đọc bản bàn giao điều phối và `report/dieu-phoi-tiep-nhan-2026-10-18.md`, rồi đọc nguồn chân lý theo vé. Soát SA-29 → SA-30 → SA-31…44 và nội dung 12 bài SA-43. Mã SA-29/30 ở `2356ee8`; B2 ở `a7f57d0`, bản sửa mới nhất `3871c85`. SA-43 đã chạy trong khoản duyệt, không giao lại lượt có tiền chỉ vì đoạn trạng thái cũ trong SA-45. Soát 0 USD bằng phản hồi đã ghi, đọc tận nơi đầu ra, thử bản sai, kiểm lại số liệu. Bộ 280 test đang xanh chưa thay cho phán xét của bạn. Ghi phán xét từng vé vào kế hoạch và báo cáo; chưa đạt thì tạo SA-46+ theo khuôn vé. Không đổi spec/ADR, không mở tập giữ lại hay cache live, không commit lẫn tệp người khác. Báo cáo tổng hợp theo tên SA-45 quy định, nêu rõ phần chưa soát và câu hỏi cần chủ dự án quyết.

### Giao W-01

> Bạn nhận `task/web/W-01-nen-web-fastapi-react-postgres.md`. Đọc vé, luật chung trong kế hoạch web và các spec dẫn trong vé. Mọi mã web ở `src/web`, dùng chung `pyproject.toml`/`.venv`, lõi không import web. Làm đủ tiêu chí của vé, gồm PostgreSQL thật và lệnh kiểm phải hỏng nếu thiếu db-test; đồ giả không thay media-smoke cần tài khoản. Chụp 390 px/1280 px, sáng/tối; kèm JSON thật và lệnh/số test. `.gitignore` đang có thay đổi của phiên khác, cần thống nhất với người giữ trước khi sửa; chỉ commit đường dẫn của vé và không cuốn thay đổi cũ. Logo đã có đủ Artboard 9–28 trong `design/`; thanh trên dùng Artboard 24/28 cho sáng/tối, theo spec mục 1, không vẽ lại logo. Báo cáo có dòng trạng thái và phần còn chờ; 0 USD mô hình.

### Giao W-13

> Bạn nhận `task/web/W-13-dung-mot-cuon-o-loi.md`. Mã B2 đã commit, không cần làm lại bước commit B2. Trước khi cài, đối chiếu mã và xác nhận với phiên pha A chuỗi cho tài liệu mới: A3 tạo candidates, A3′ lập retrieval, vị trí label-roles, A4/A5 không vàng, roadmap/A10/naming và chuẩn bị Pha B. A4 hiện đọc candidates, BuildMentions đọc retrieval; không lấy chạy lại doc-6 có cache làm bằng chứng đủ cho cuốn mới. Ghi chuỗi chuẩn/câu hỏi vào báo cáo trước. Use case gọi trực tiếp use case, không gọi CLI bằng tiến trình con; giữ bốn bước công khai của spec. Không sửa mã của phiên pha A. Dùng dry-run/đồ giả/cache với 0 USD; phát hiện cache miss có tiền thì báo con số trước. Phối hợp điều phối để làm W-05 ngay khi W-01 đạt và không đụng vé sửa kho B2.

### Giao W-22

> Bạn nhận `task/web/W-22-ban-figma.md`, bám toàn bộ spec thiết kế. `design/` đã có đủ 20 logo Artboard 9–28, favicon và GIF; làm cả phần thương hiệu theo bảng spec mục 1, không còn chờ bộ tám logo giả định và không vẽ lại logo. Ghi đúng tên Artboard trên các thành phần để React dùng cùng bản. Kết quả cần biến token đúng tên/giá trị, mọi trang/trạng thái ở 390 px và 1280 px, bốn luồng prototype, link xem và ảnh xuất, theo tiêu chí vé và yêu cầu thị giác/hiệu ứng bổ sung.

Các lời giao trên **đã được soạn, chưa gửi sang chat khác, chưa tự tạo agent hoặc chat mới**. Bảng vé chỉ chuyển sang đã giao khi có người nhận được xác nhận.

## 10. Cam kết vận hành điều phối

- Tôi giữ một trạng thái có căn cứ: chưa giao; đang làm; đã báo xong/chờ soát; đạt/đạt có ghi chú; chưa đạt kèm vé sửa. Không gộp các trạng thái này thành "xong".
- Mỗi báo cáo mới được kiểm đầu ra bắt buộc, lệnh và số test, commit, ảnh/JSON khi vé yêu cầu, chi thực và hạn chế bằng chứng; sau đó chuyển đúng hàng soát.
- Chọn vé bằng tiền nhiệm đã **đạt** và kiểm vùng tệp, không chỉ bằng nhãn ready-for-agent. Không giao đồng thời vé sửa cùng tệp; không để phiên soát thử sửa sai trên mã người khác đang chỉnh mà thiếu phối hợp.
- Ghi mục 10 của bản bàn giao mỗi khi trạng thái đổi; giữ câu hỏi thiết kế ở mục 8. Không tự thay spec/ADR hay chốt S2/S3, nhiệt độ, luật từ vựng.
- Chỉ chủ dự án duyệt tiền. Đợt tiếp nhận chi mới **0 USD**. Không suy hạn mức còn lại của toàn dự án từ vài báo cáo, vì chưa kiểm toàn bộ sổ chi.
- Giữ niêm phong d01-t01/d01-t02, document-data/test, tập khoá D-02 và khoa.jsonl; không đọc/in cache live; dữ liệu đối chiếu chỉ sáu cuốn phát triển.
- Không sửa mã sản phẩm trong vai điều phối. Không tự gửi lời giao sang chat khác hoặc tạo người làm nếu chủ dự án chưa giao kênh/người nhận cụ thể.

## 11. Tài liệu để tiếp tục

- [Bàn giao điều phối đã cập nhật](handoff-dieu-phoi-2026-10-18.md)
- [Kế hoạch Pha B](../task/sau-a10/00-ke-hoach.md), [SA-45](../task/sau-a10/45-soat-thay-claude-nhan-vien-cap-cao.md)
- [Bàn giao B2](pha-b2-ban-giao-31-44-2026-10-18.md), [SA-43](pha-b2-sa38-43-2026-10-18.md), [bảy thao tác SA-44](pha-b2-sa37-44-2026-10-18.md)
- [Kế hoạch web](../task/web/00-ke-hoach.md), [spec chức năng](../doc/web-chuc-nang-spec.md), [spec cơ sở dữ liệu](../doc/web-co-so-du-lieu-spec.md), [spec thiết kế](../doc/web-thiet-ke-giao-dien-spec.md)
