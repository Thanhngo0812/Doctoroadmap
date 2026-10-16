# Spec — Pass phụ A8 không LLM (`a8-secondary-ml-v1`)

**Status:** ready-for-agent · soạn 2026-10-16 (Claude). Chủ dự án yêu cầu đưa E5 vào sản phẩm nhanh, rồi chuyển sang vé 17.

**Quyết định của chủ dự án:**
- 2026-10-05: pass phụ A8 bỏ LLM, cho cả đồ án lẫn seminar. Luồng LLM cũ giữ lại làm mốc so sánh.
- 2026-10-16: triển khai E5 ngay, không chờ thêm thí nghiệm.

**Nguồn:**
- báo cáo vòng 1 (`report/nghien-cuu-pass-phu-khong-llm-vong-1-2026-10-05.md`), mục 10;
- báo cáo vòng 2 (`report/nghien-cuu-pass-phu-vong-2-ke-hoach-2026-10-10.md`): mục 7, mục 8 (E5, E9, sửa bộ khớp ở 8.11, E6 ở 8.10, D-04 ở 8.14,
  bộ khớp sạch ở 8.15);
- ADR 0008 (pass chính trích mở, pass phụ kiểm cặp);
- thuật ngữ trong `CONTEXT.md`: pass phụ, cặp nghi tiên quyết, cạnh mềm, requires.

## Problem Statement — Vấn đề

Pass phụ hiện nay (`a8-secondary-pass-lazy-v7`) hỏi LLM từng cặp nghi tiên quyết, tối đa hai chiều mỗi cặp. Đây là khâu tốn nhất của một cuốn
sách: khoảng 91% tiền mỗi cuốn, và hàng nghìn lời gọi với cuốn cỡ doc-4. Chủ dự án đặt ưu tiên số một của v4 là phút/cuốn và USD/cuốn.

Vòng 1 và vòng 2 đã làm ra một bộ thay không LLM, gọi là E5:
- LightGBM học trên nhãn agentic D-01, gồm 35 nghìn dòng của 16 sách;
- 82 đặc trưng cấu trúc, lấy từ thứ đã có trước pass phụ;
- ngưỡng chọn bằng hiệu chỉnh isotonic;
- cạnh lắp bằng chính bộ kiểm hợp đồng của pass chính.

E5 hiện chỉ sống trong `scripts/pass-phu-ml/`, chạy trên bảng CSV ở `tmp/`, và cần môi trường riêng. Sản phẩm chưa dùng được nó.

Chất lượng trên ba tài liệu vàng, đo bằng E4 (A9 → A10 → chấm), seed gốc:

| | Q7 | Q7b | bao đóng P | bao đóng R | cạnh pass phụ |
|---|---|---|---|---|---|
| doc-1, LLM v3 | 0,667 | 0,877 | 0,874 | 0,740 | 468 |
| doc-1, E5 | 0,603 | 0,743 | 0,821 | 0,664 | 196 |
| xstk-ch3-1, LLM v3 | 0,414 | 0,644 | 0,636 | 0,214 | 171 |
| xstk-ch3-1, E5 | 0,206 | 0,530 | 0,593 | 0,163 | 59 |
| doc-4, LLM v3 | 0,322 | 0,606 | 0,584 | 0,459 | 1.473 |
| doc-4, E5 | 0,483 | 0,859 | 0,856 | 0,522 | 727 |

Số E5 là seed gốc sau khi sửa bộ khớp (`sua-y.jsonl`; bản đầu của spec ghi nhầm số trước khi sửa, đã chữa 2026-10-16). Số LLM v3 đo trước khi sửa bộ khớp ở mục 8.11, và chỉ dùng để tham khảo. E5 hơn rõ ở cuốn lớn nhất, nhưng kém ở doc-1 và xstk. Đây là đánh đổi chủ
dự án đã chấp nhận khi chốt bỏ LLM. Kết luận cuối sẽ đo trên vàng T-01.

## Solution — Giải pháp

Thêm một **stage pass phụ không LLM** vào chuỗi đồ thị. Stage này nhận cùng đầu vào và trả cùng hợp đồng artifact như pass phụ LLM. Cách làm:
1. Chọn cặp nghi tiên quyết bằng đúng hàm chọn cặp hiện có.
2. Với mỗi cặp, xét hai chiều X → Y. Một chiều là **ứng viên** khi hợp đồng cho phép đích Y, và tên X có trong cửa sổ định nghĩa của Y theo ranh
   giới từ tiếng Việt.
3. Tính 82 đặc trưng cho mỗi chiều ứng viên. Chấm bằng mô hình LightGBM đóng băng.
4. Chọn ngưỡng cho từng tài liệu bằng hiệu chỉnh isotonic đóng băng: số cạnh giữ bằng tổng xác suất đã hiệu chỉnh trên các ứng viên của những cặp
   pass phụ thật sự phán (không bị tỉa), tính lặp tới điểm bất động (mục 4 của Implementation Decisions).
5. Duyệt cặp theo đúng thứ tự của pass phụ LLM. Cặp bị tỉa vì đã có cạnh hay đường cứng thì bỏ qua. Với cặp còn lại, lấy chiều điểm cao hơn; nếu
   điểm vượt ngưỡng thì dựng cạnh cứng (`can_de_hieu`, căn cứ `trong_dinh_nghia`). Câu trích là câu trong cửa sổ định nghĩa của Y có tên X, gần
   câu neo nhất. Cạnh phải qua bộ kiểm hợp đồng của pass chính; không có câu nào qua thì không tạo cạnh.

Stage mới không gọi mô hình và không tốn tiền. Pass phụ LLM vẫn chọn được bằng một tuỳ chọn cấu hình. **Mặc định là `ml` từ vé 18e (2026-10-16),
sau khi Claude nghiệm thu đạt 18d và chủ dự án duyệt.**

## User Stories

1. Là chủ dự án, tôi muốn pass phụ không gọi LLM, để USD/cuốn giảm phần lớn mà lộ trình vẫn dùng được.
2. Là chủ dự án, tôi muốn pass phụ chạy vài phút trên CPU laptop cho một cuốn cỡ doc-4, để phút/cuốn giảm.
3. Là chủ dự án, tôi muốn chọn pass phụ LLM hay không LLM bằng một tuỳ chọn cấu hình, để so sánh và quay lại khi cần.
4. Là chủ dự án, tôi muốn manifest ghi rõ artifact sinh từ pass phụ nào, phiên bản mô hình nào và băm của mô hình, để không lẫn kết quả.
5. Là chủ dự án, tôi muốn `--dry-run` báo pass phụ không LLM tốn 0 lời gọi và 0 USD, để dự toán đúng.
6. Là chủ dự án, tôi muốn chuỗi chạy được cả khi không có `--allow-spend` ở pass phụ không LLM, vì nó không tiêu tiền.
7. Là chủ dự án, tôi muốn mặc định chỉ đổi sau khi nghiệm thu đạt, để không vô tình hạ chất lượng.
8. Là người học, tôi muốn mỗi cạnh tiên quyết do pass phụ thêm có câu trích nguyên văn trong đoạn định nghĩa của khái niệm đích, để thấy vì sao phải
   học trước.
9. Là người học, tôi muốn pass phụ không thêm cạnh mềm hay cạnh không có căn cứ, để dãy học không bị kéo lệch bởi phán đoán yếu.
10. Là A9 và A10, tôi muốn nhận artifact pass phụ cùng hợp đồng với bản LLM: `secondary_edges`, `secondary_log`, `stats`, `cost_summary`,
    `secondary_complete`, để không phải đổi gì phía sau.
11. Là A10, tôi muốn cạnh do bản không LLM tạo qua R17 như mọi cạnh khác. D-04d đã cho thấy R17 nên giữ nguyên.
12. Là bộ chấm E4 và các công cụ nghiên cứu, tôi muốn đọc artifact của bản không LLM bằng đúng mã chấm hiện có.
13. Là Claude, tôi muốn mỗi cặp có một dòng nhật ký: điểm hai chiều, chiều chọn, ngưỡng, trạng thái (tạo cạnh, dưới ngưỡng, không có câu căn cứ,
    bị tỉa) và câu trích, để đọc lại khi chất lượng có vấn đề.
14. Là Claude, tôi muốn `stats` ghi số cặp, số chiều ứng viên, số cặp bị tỉa, số dưới ngưỡng, số không có căn cứ, số cạnh tạo, ngưỡng và số dương
    ước lượng, để so với số của nghiên cứu.
15. Là Claude, tôi muốn đặc trưng của sản phẩm trùng khớp với bảng nghiên cứu trên bốn tài liệu cũ, để chắc mô hình đóng băng nhận đúng đầu vào nó
    đã học.
16. Là Claude, tôi muốn có một lệnh xuất bảng đặc trưng từ artifact pass chính bằng chính mã sản phẩm, để kiểm khớp và để học lại sau này.
17. Là Claude, tôi muốn đóng băng mô hình và bộ hiệu chỉnh từ script nghiên cứu thành tệp có băm, để sản phẩm không cần dữ liệu D-01 hay `tmp/`.
18. Là Claude, tôi muốn học lại mô hình (ví dụ sau vé 17 hay khi có T-01) chỉ bằng cách thay tệp mô hình và đổi phiên bản, không sửa mã stage.
19. Là nhân viên, tôi muốn phần đặc trưng là mã miền thuần nhận một hàm tách từ được tiêm vào, để test không cần underthesea và miền không phụ
    thuộc thư viện ngoài.
20. Là nhân viên, tôi muốn tái dùng hàm chọn cặp, hàm cửa sổ định nghĩa, bộ chuẩn hoá tên của mention map, bộ kiểm hợp đồng và bộ gộp đề xuất của
    pass chính, để không viết lại luật đã kiểm.
21. Là nhân viên, tôi muốn tách mô hình chấm điểm thành một cổng ở tầng ứng dụng, có bản cài LightGBM ở hạ tầng, để test stage bằng bộ chấm giả.
22. Là nhân viên, tôi muốn tệp mô hình đọc bằng định dạng văn bản của LightGBM và bộ hiệu chỉnh bằng JSON, không dùng pickle.
23. Là nhân viên, tôi muốn stage dừng với lỗi rõ khi tệp mô hình thiếu, sai băm, hoặc danh sách đặc trưng không khớp.
24. Là nhân viên, tôi muốn stage dùng lại cache như các stage khác: cùng đầu vào và cùng config thì trả artifact đã lưu.
25. Là nhân viên, tôi muốn thứ tự duyệt cặp và luật tỉa giống hệt bản LLM, để hai bản so được với nhau.
26. Là nhân viên, tôi muốn lỗi của một cặp (không dựng được câu trích, hay bộ kiểm hợp đồng từ chối) chỉ làm cặp đó không có cạnh, có ghi nhật ký,
    chứ không dừng cả stage.
27. Là người duy trì, tôi muốn underthesea được ghim phiên bản trong phụ thuộc của dự án và chạy offline với mô hình tách từ đóng gói sẵn.
28. Là người duy trì, tôi muốn kết quả tất định: chạy hai lần trên cùng artifact ra cùng cạnh và cùng băm payload.
29. Là chủ dự án, tôi muốn có ADR ghi quyết định pass phụ không LLM, và `CONTEXT.md` cập nhật định nghĩa pass phụ, để người sau không đọc nhầm ADR 0008.
30. Là chủ dự án, tôi muốn sau này đổi bộ chấm (ví dụ PhoBERT qua dịch vụ GPU) chỉ phải thay bản cài của cổng chấm điểm.

## Implementation Decisions

### 1. Chế độ pass phụ và vị trí trong chuỗi

- Thêm tuỳ chọn cấu hình chọn chế độ pass phụ: `llm` (stage hiện có) hoặc `ml` (stage mới). Chế độ nằm trong config của pass phụ, nên nằm trong khoá
  cache. Hai chế độ không dùng chung artifact.
- **Mặc định là `ml` từ vé 18e (2026-10-16)**, sau khi Claude nghiệm thu đạt và chủ dự án đồng ý. Giá trị `llm` vẫn chọn được bằng cấu hình.
- Stage mới đứng đúng chỗ của pass phụ LLM: sau pass chính hoàn chỉnh, trước ValidateGraph. Đầu vào giống hệt: artifact pass chính, chunk, mention
  map, sổ cặp cụm, cặp nghi tiên quyết, định tuyến.
- `algorithm_id` là `a8-secondary-ml-v1`. Config ghi:
  - phiên bản và băm của tệp mô hình và tệp hiệu chỉnh;
  - danh sách đặc trưng;
  - tên bộ tách từ và phiên bản;
  - luật ứng viên, luật ngưỡng, luật tỉa;
  - `definition_before` và `definition_after` lấy từ pass chính.

### 2. Ứng viên và bộ khớp tên

- Ứng viên là một chiều X → Y của cặp đã chọn, thoả hai điều:
  - hợp đồng cho phép: trạng thái dạy của Y không thuộc nhóm bị loại, như `validate_main_proposals`, và cả hai đầu học được;
  - tên X (tên chính hoặc bí danh) có trong ít nhất một câu của cửa sổ định nghĩa Y.
- "Có tên" phải thoả cả hai phép khớp như bản nghiên cứu `--tach-tu`:
  - khớp theo kênh exact của mention map: chuẩn hoá giống hệt, bỏ ký hiệu, ranh giới từ;
  - khớp theo ranh giới **từ** tiếng Việt trên câu đã tách từ, để tên một âm tiết không khớp vào giữa từ ghép.
- Câu tách từ phải chuẩn hoá **từng âm tiết**. Đây là bài học của lỗi chữ "y" ở mục 8.11.
- **Giữ bộ khớp hiện tại.** Không bỏ bí danh cắt cụt, không bắt chữ viết tắt khớp đúng chữ hoa. Mục 8.15 đã đo: bản "sạch" hại vàng ở sách toán.

### 3. Đặc trưng

- Đúng 82 đặc trưng của E5 (danh sách nằm trong tệp mô hình), mỗi đặc trưng giữ đúng định nghĩa của bảng nghiên cứu. Gồm các nhóm:
  - nguồn cặp;
  - trích dẫn;
  - sổ cặp cụm;
  - thứ tự và cấu trúc mục;
  - tên X trong cửa sổ định nghĩa Y, cả hai chiều;
  - từ báo đứng trước tên;
  - độ "khung";
  - RefD trên chunk định nghĩa;
  - độ phủ và đồng xuất hiện;
  - PageRank trên đồ thị trích dẫn;
  - trạng thái dạy và khả năng học;
  - độ dài và lồng tên;
  - vai trò chunk của câu neo Y.
- **Không** dùng đặc trưng lấy từ cạnh pass chính (`main_*`), vì D-01 không chạy pass chính.
- Phần đặc trưng là mã miền thuần, nhận nút, chunk, mention map, trích dẫn, sổ cặp cụm và **một hàm tách từ được tiêm vào**. Bản cài tách từ bằng
  underthesea ở hạ tầng có bộ nhớ đệm theo câu.
- Giá trị thiếu mã hoá như lúc học: rỗng thành −1.
- Đặc trưng phải khớp bảng nghiên cứu. Đây là điều kiện nghiệm thu (mục Testing), không phải hy vọng.

### 4. Mô hình, hiệu chỉnh và ngưỡng

- **Mô hình đóng băng:** LightGBM học trên toàn bộ dòng D-01 (nhãn lượt A, `trong_cua_so = 1`), đúng tham số của E5, seed 20261005. Đây là mô
  hình cuối của lượt `e5-d01-a`.
- **Bộ hiệu chỉnh:** isotonic, học trên dự đoán ngoài mẫu chia theo sách của D-01. Lưu dạng hai mảng điểm và xác suất.
- **Định dạng tệp:**
  - mô hình lưu ở định dạng văn bản của LightGBM;
  - bộ hiệu chỉnh và siêu dữ liệu lưu bằng JSON: danh sách đặc trưng theo thứ tự, phiên bản, ngày học, nguồn nhãn, AP ngoài mẫu.
  - Tệp không chứa văn bản giáo trình, nên được đưa vào repo và đóng gói cùng gói như mô hình A1 nhẹ. Băm SHA-256 của các tệp nằm trong config.
- **Ngưỡng theo từng tài liệu: điểm bất động trên các cặp được phán** (sửa 2026-10-16 sau nghiệm thu 18d; bản đầu ở dưới):
  - với một ngưỡng t, lắp cạnh như mục 5. **Tập tính ngưỡng** là các chiều ứng viên của những cặp không bị tỉa trong lượt lắp đó, tức các cặp
    pass phụ thật sự phán. Đây là cách hiểu của nghiên cứu, vốn dùng các cặp mà pass phụ LLM đã hỏi;
  - k = tổng xác suất đã hiệu chỉnh trên tập đó, làm tròn; t' = điểm của ứng viên thứ k theo điểm giảm dần; k = 0 thì không tạo cạnh nào;
  - ngưỡng khởi đầu tính trên các cặp chưa bị cạnh pass chính tỉa. Lặp tới khi t' = t;
  - nếu một ngưỡng lặp lại (vòng dao động, doc-4 dao động giữa hai giá trị) thì chọn ngưỡng **lớn nhất** trong vòng; tối đa 10 lượt, hết lượt thì
    chọn ngưỡng lớn nhất đã gặp. Cạnh cuối là cạnh của lượt lắp với ngưỡng được chọn.
  - Đã đo trong 18d (Claude mô phỏng bằng bộ lắp nghiên cứu): doc-1 hội tụ sau 2 lượt, E4 trùng hệt nghiên cứu; doc-4 E4 lệch tối đa 0,006.
  - **Bản đầu, bỏ:** tính một lần trên các cặp chưa bị cạnh pass chính tỉa. Tập này lớn hơn nên ngưỡng cao hơn; doc-1 mất 9 cạnh, Q7 −0,042, R −0,038.
- **Đóng băng do Claude làm**, từ script nghiên cứu, vì cần dữ liệu D-01 ngoài repo. Nhân viên chỉ nhận tệp mô hình.

### 5. Lắp cạnh

- Duyệt cặp theo thứ tự hàm chọn cặp trả về. Trước mỗi cặp, gọi lại hàm chọn cặp với cạnh hiện có (pass chính cộng cạnh pass phụ đã tạo) để tỉa,
  giống pass phụ LLM.
- Mỗi cặp chọn chiều điểm cao hơn. Dưới ngưỡng thì ghi `below_threshold`.
- Câu trích:
  - lấy các câu trong cửa sổ định nghĩa Y có tên X, xếp theo khoảng cách tới câu neo;
  - lần lượt thử với bộ kiểm hợp đồng của pass chính (`require_kind=True`, cùng `definition_before` và `definition_after`);
  - câu đầu tiên qua thì dùng.
  - Không câu nào qua thì ghi `no_evidence`, không tạo cạnh.
- Chỉ tạo **cạnh cứng**: `prerequisite_kind = can_de_hieu`, `evidence_kind = trong_dinh_nghia`. Không tạo cạnh `cong_cu` hay cạnh mềm từ đồng xuất
  hiện, vì E5 được đo với `--chi-cung`.
- Lý do của cạnh ghi điểm và căn cứ, ví dụ "pass phụ không LLM: điểm 0,734; căn cứ trong_dinh_nghia".
- Gộp cạnh bằng bộ gộp đề xuất của pass chính.
- `secondary_log` dùng lại các trạng thái tỉa hiện có (`pruned_direct_edge`, `pruned_explicit_path`), thêm ba trạng thái: `created`,
  `below_threshold`, `no_evidence`.
- `cost_summary` giữ phần của pass chính; phần pass phụ là 0.

### 6. Phụ thuộc và hiệu năng

- Thêm underthesea, ghim phiên bản 9.5.0, phiên bản đã dùng trong nghiên cứu. Chỉ dùng tách từ, với mô hình CRF đóng gói sẵn, không tải gì lúc chạy.
- LightGBM, scikit-learn và networkx đã có trong phụ thuộc. Không thêm torch.
- Mục tiêu: một cuốn cỡ doc-4 (khoảng 4.600 chiều ứng viên) chạy xong stage trong 5 phút trên CPU laptop.

### 7. Công cụ cho Claude

- Một lệnh CLI xuất bảng đặc trưng (CSV) của một tài liệu từ artifact pass chính, bằng chính mã sản phẩm. Dùng để kiểm khớp với bảng nghiên cứu và để
  học lại sau này. Bảng ghi ở thư mục do người chạy chọn, vì có tên khái niệm lấy từ giáo trình.
- Script nghiên cứu đóng băng mô hình (thuộc `scripts/pass-phu-ml/`) xuất đúng định dạng tệp ở mục 4.

### 8. Tài liệu

- ADR mới: pass phụ không LLM, chấm cặp bằng mô hình học, thay một phần ADR 0008. Phần "pass phụ chỉ kiểm cặp, không tự đề xuất cạnh" vẫn giữ.
- Cập nhật định nghĩa "Pass phụ" trong `CONTEXT.md`: phán cặp bằng mô hình học hoặc LLM, tuỳ chế độ.

## Testing Decisions

**Test tốt** chỉ kiểm hành vi nhìn từ ngoài: cạnh nào được tạo, nhật ký ghi gì, artifact có đúng hợp đồng không. Không kiểm cách tính bên trong.
Mỗi luật phải có ít nhất một test thấy nó trượt khi luật bị bỏ (AGENTS.md mục 5).

**Đường nối test (seam).** Có ba đường nối, từ cao xuống:
1. **Stage pass phụ không LLM** (`execute` trên kho artifact trong bộ nhớ, với bộ chấm điểm giả và bộ tách từ giả). Đây là đường nối chính, giống
   test hiện có của pass phụ LLM. Test ở đây:
   - cặp trên ngưỡng có câu trích hợp lệ thì thành cạnh cứng;
   - cặp dưới ngưỡng không thành cạnh, ghi `below_threshold`;
   - cặp không có câu qua bộ kiểm hợp đồng ghi `no_evidence`;
   - cạnh vừa tạo tỉa các cặp phía sau, giống bản LLM;
   - chiều điểm cao hơn được chọn;
   - ngưỡng theo tổng xác suất hiệu chỉnh, có ca k = 0;
   - không có cạnh mềm hay cạnh `cong_cu`;
   - pass chính chưa hoàn chỉnh thì từ chối;
   - cache: chạy lại trả artifact đã lưu;
   - tất định: hai lần chạy cùng băm payload;
   - mô hình thiếu, sai băm, hay lệch danh sách đặc trưng thì dừng với lỗi rõ;
   - `--dry-run` báo 0 lời gọi.
2. **Hàm đặc trưng miền**, trên một tài liệu dựng tay nhỏ, với bộ tách từ giả:
   - tên một âm tiết không khớp giữa từ ghép;
   - tên có âm tiết "y" giữa từ ghép vẫn khớp (lấy lại ca của test `test_khop_tu_am_tiet_y`);
   - ứng viên đòi hợp đồng cho phép;
   - các đặc trưng thứ tự, cùng mục, cùng chương;
   - giá trị thiếu thành −1.
3. **Bản cài LightGBM của cổng chấm điểm**: nạp tệp mô hình nhỏ dựng trong test, kiểm băm, thứ tự đặc trưng, và hiệu chỉnh nội suy đúng.

**Prior art:**
- test của pass phụ LLM (dựng artifact pass chính trong bộ nhớ, kiểm tỉa và nhật ký);
- test của bộ khớp tên theo ranh giới từ trong `tests/unit/scripts/`;
- test kiến trúc (miền không import hạ tầng hay thư viện ngoài).

**Nghiệm thu do Claude làm** (không phải test đơn vị, chạy trên artifact thật):
- **Khớp đặc trưng:** xuất bảng bằng lệnh CLI ở mục 7 cho doc-1, nhap-mon-ml, xstk-ch3-1 và doc-4.
  - So với `tmp/pass-phu-ml/bang/*.csv` trên mọi dòng ứng viên: chênh tuyệt đối tối đa 1e-9 trên mọi đặc trưng. Cột lệch thì trả vé.
  - Cùng tập ứng viên.
- **Khớp điểm:** điểm của mô hình đóng băng trên bảng sản phẩm trùng điểm của lượt `e5-d01-a`, chênh tối đa 1e-9.
- **E4 trên ba tài liệu vàng:** chạy stage mới trên artifact pass chính đã dùng trong nghiên cứu, rồi chạy E4.
  - Q7, Q7b, bao đóng P và R phải nằm trong ±0,03 so với `e5-a-hieu-chinh` (bảng ở mục Problem) trên từng tài liệu.
  - Lệch hơn mức đó thì Claude tìm nguyên nhân trước khi đổi mặc định. Nghi phạm đầu tiên là tập ứng viên tính ngưỡng (mục 4).
- **Thời gian:** ghi phút của stage trên doc-4 trên laptop.
- **Chuỗi đầy đủ:** chạy chuỗi đồ thị một tài liệu D-01 từ pass chính tới A10 ở chế độ `ml`. Kiểm artifact đọc được và lộ trình sinh ra.

## Out of Scope

- **Pass chính A8 vẫn dùng LLM.** Theo đích dài hạn, LLM chỉ còn ở A3 và pass chính.
- Đổi bộ khớp tên: bí danh cắt cụt và chữ viết tắt (mục 8.15). Đo lại riêng trên T-01.
- Cross-encoder PhoBERT (E6), dịch vụ GPU qua LAN.
- Học lại mô hình trên nhãn mới, ví dụ nhãn B, nhãn D-04, hay vàng T-01.
- Đổi R17 hay luật nào khác của A10 (D-04d: giữ R17).
- Gỡ pass phụ LLM. Nó ở lại làm mốc và làm đường lùi.
- Tài liệu ngoài tiếng Việt. Đồ án chỉ hỗ trợ tiếng Việt từ 2026-10-05; bộ tách từ và từ báo là riêng tiếng Việt.
- Vé 17 (gộp khâu trước A8). Xem Further Notes về thứ tự.

## Further Notes

- **Thứ tự với vé 17.**
  - Vé 17 đổi tập node, câu neo và trạng thái dạy ở thượng nguồn. Các đặc trưng của E5 phụ thuộc trực tiếp vào những thứ đó.
  - Mô hình hiện tại học trên D-01 dựng từ chuỗi v3. Vì vậy, khi chuỗi gộp của vé 17 thành mặc định, phải đo lại E5 trên vàng qua chuỗi mới. Nếu
    tụt rõ thì dựng lại bảng D-01 trên chuỗi mới rồi học lại.
  - Nhờ cổng chấm điểm và tệp mô hình có phiên bản, việc học lại không đổi mã stage.
- **Nhãn là bạc.** Mô hình học trên nhãn agentic D-01. Mọi số chất lượng ở đây đo trên ba tài liệu vàng phát triển, không phải T-01. T-01 xong thì so
  E5, PhoBERT và LLM v3 trên tập giữ lại (vé T-01b).
- **Những gì D-04 cho biết về cạnh do E5 tạo** (mục 8.14):
  - khoảng 40% cạnh ngược của E5 là cạnh sai, chủ yếu do tên đa nghĩa ("Nhân", "Chất");
  - R17 hạ chúng thành cạnh mềm, nên ảnh hưởng tới dãy học bị chặn.
  - Cải thiện là việc của vòng sau (đặc trưng tên đa nghĩa), không thuộc spec này.
- **Chi phí đo:** sau khi đổi mặc định, báo cáo phút/cuốn và USD/cuốn của một cuốn D-01, trước và sau.
