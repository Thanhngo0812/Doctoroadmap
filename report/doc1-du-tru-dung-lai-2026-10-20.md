# Doc-1 — dry-run và đề nghị duyệt đợt dựng lại, 2026-10-20

**Trạng thái: đã dry-run; chưa được duyệt chạy có tiền. Chi mới: 0 USD.** Dừng tìm bản sao theo chỉ thị mới của chủ dự án. Báo cáo này không nhận lại phê duyệt chi doc-6 của W-13 làm phê duyệt cho doc-1.

## Đầu vào và kết quả thật

- Thư mục chạy: `C:\Users\ngoco\Desktop\Doctoroadmap`, nhánh **main**, commit dry-run `88a6905f1fbac890469f694772318286f6053256`. Không sửa mã sản phẩm.
- Doc-6 đã khôi phục **122/122 tệp khớp SHA-256**. Trên manifest cũ gồm 927 tệp, cả hai cuốn hiện **787 khớp, 140 thiếu, 0 sai hash**. [Biên bản khôi phục](su-co-va-khoi-phuc-cache-2026-10-20.md).
- Kiểm doc-6 sau khôi phục: **12 passed**, gồm bốn ca W-13 và kiểm WebSettings. Đây là kiểm tập trung, không thay cổng toàn repo. Lượt đầu chỉ chọn test lõi bị lỗi thu thập vì tùy chọn `--require-postgres` được khai báo trong conftest backend; lượt sau thêm module WebSettings, không bỏ guard, không sửa runner/test.
- `build --dry-run` đã đọc doc-1 bằng **Nhe mặc định**, tạo **parse v6, chunks v8** ở kho dùng chung. Đây là artifact mới 0 USD, không phải bản phục hồi của các phiên bản cũ.
- Kết quả: **102 trang, 302 chunk, 197 section, 82.268 chữ cái, 806,55 chữ/trang, 0% trang trắng, tỉ lệ dấu 21,82%**. Qua cổng sớm, không nới ngưỡng. Đọc/kiểm mất **14,38 giây**.
- Cây parse có **2.602 node công thức**. Chưa đồng nghĩa sẽ cắt được 2.602 ảnh; còn phải kiểm bbox và số bị bỏ qua.
- Bằng chứng các lệnh, số liệu và giá tham chiếu: [doc1-dry-run-evidence-2026-10-20.json](doc1-dry-run-evidence-2026-10-20.json). Log chi tiết nằm ở `tmp/coord-doc1-rebuild-20261020/`.
- Baseline đã được điều phối ghi trước sự cố trong [báo cáo ngày 18](dieu-phoi-tiep-nhan-2026-10-18.md): **graph v57, 33 module, 205 khái niệm học được**, 29 tên module LLM, 1 mô tả module LLM và 32 mô tả khuôn. JSON số đếm gốc ở `tmp/dieu-phoi-doi-chieu-20261018.json`; không có số cạnh hoặc danh sách node module để đối chiếu. Đây là bản ghi số liệu trước sự cố, không phải manifest đã phục hồi.

## Cache và phụ thuộc

1. Ingest dry-run ban đầu báo không có parse tương thích với Nhe hiện hành. Bước đọc thật trong `build --dry-run` đã tạo parse/chunks mới, để lượt có tiền dùng lại đầu vào này.
2. `label-roles` **cache miss**: còn **162 heading, 16 batch**. Bắt buộc chạy trước A3; không chuyển nhãn hoặc sửa metadata để ép cache hit.
3. A3/A3′: kiểm khóa cấu hình với đầu ra nhãn dự kiến không thấy candidate/retrieval tương thích. Checkpoint A3 đúng khóa cũng chưa có. Đầu vào trước nhãn có **168 ngữ cảnh**; số việc có thể đổi sau gán vai trò.
4. Còn **18 checkpoint doc-1**: anchor 5, concept-labels 1, identity/identity-verify 8, implicit 1, relation 1, teaching 2. Chúng giữ phản hồi LLM cũ, nhưng cùng PDF không đủ để xác nhận tái dùng: phải khớp cấu hình, node/chunk và ngữ cảnh mới. **Chưa tính khoản tiết kiệm chưa chứng minh được.**
5. A4 dry-run với `declared_language='vi'` trên candidate cũ báo 244 tên cần embedding; các bước merge/repair/verify/describe/check/anchor còn phụ thuộc. Đây là số tham chiếu, không phải kế hoạch đã biết đầu ra A3 mới. Dùng port A4 của chuỗi W-13, `coverage=none`, không dùng đường CLI cũ đòi bộ vàng.
6. Roadmap dry-run dừng rõ vì canonical khôi phục v4 còn thuộc chuỗi v3, không phải canonical gop hợp lệ của đường dựng mới. Không dùng v4 để giả rằng roadmap mới đã có thể chạy.
7. A12, concept-index và formulas dry-run đều dừng vì chưa có graph doc-1. Không ghi chúng thành đã đạt hay 0 lời gọi khi chạy thật chỉ vì dry-run bị chặn.

Mọi API sinh/embedding, lấy header ADC và kết nối mạng trong tiến trình kiểm đã bị chặn; **0 lần chạm guard mạng**. Đường khởi tạo roadmap định mở `artifacts/phase_b/live.json` được chuyển trong harness sang một kho doc-1 riêng, có ghi nhận trong bằng chứng. Không đọc kho global chứa tập giữ lại.

## Dự toán trước khi xin duyệt

Vertex global, `gemini-3.1-flash-lite`: **0,25 USD/M token vào, 1,50 USD/M token ra**; Gemini Embedding online **0,15 USD/M token vào**. Đã đối chiếu [bảng giá chính thức](https://cloud.google.com/vertex-ai/generative-ai/pricing). Khớp giá ghim trong repo; không tự đổi model hoặc transport.

Phân biệt lời gọi sinh và embedding: adapter Vertex hiện phát một request embedding cho mỗi văn bản. Các dải dưới đây là **ước lượng lập ngân sách**, chưa phải số đã được dry-run tính chính xác hoặc trần số request. Retry, nhãn không hợp lệ, số node và cache hit thực sẽ làm thay đổi kết quả. Thời gian là khoảng dự kiến, chưa đo độ trễ Vertex của lượt này.

| Bước | Lời gọi ước tính | USD ước tính | Thời gian dự kiến | Căn cứ |
|---|---|---:|---|---|
| Ingest Nhe + kiểm sớm | 0 | 0 | Đã đo 14,38 giây; lượt sau có cache | Kết quả thật ở trên |
| label-roles | 16 sinh, chưa tính sửa nhãn | 0,018842; dự phòng 0,02–0,04 | 0,5–2 phút | Dry-run trực tiếp, 162 heading/16 batch |
| A3 | Khoảng 500–650 sinh, 300–700 embedding mô tả ứng viên | 0,60–0,95 | 3–10 phút | A3 doc-1 cũ: 80 ngữ cảnh, 258 sinh, 0,28750175 USD; nhân tỉ lệ 168/80 cho mốc khoảng 542 sinh và 0,603754 USD, rồi dự phòng |
| A3′ | 302 embedding chunk, nếu tập chunk không đổi | Khoảng 0,007596; dự phòng 0,008–0,012 | 15–60 giây, song song A3 | 50.641 token ước theo văn bản thực; chưa gọi countTokens |
| A4/A5 tiếng Việt, gop/coverage none | Khoảng 300–700 sinh, 250–700 embedding tên | 0,35–1,00 | 3–10 phút | Canonical v4 cũ có 267 sinh/0,20522325 USD; đường gop còn neo/verify và pool mới, không áp số cũ làm số chính xác |
| Roadmap, nhãn khái niệm, tên module | Khoảng 250–550 sinh, 200–700 embedding | 0,20–0,65 | 2–8 phút | Tham chiếu 225 node học ở canonical v4; đầu ra mới chưa biết. Secondary hiện dùng ML, không gán chi LLM cho phần ML |
| A12 | 0 API mô hình | 0 | 5–30 giây | Gán chunk vào module từ graph/retrieval đã có |
| Concept-index | Khoảng 225–450 embedding | 0,002–0,01 | 15–60 giây | Node học cũ 225; văn bản tham chiếu 13.217 token, 0,001983 USD; node mới có thể khác |
| Formulas `--pdf` | 0 API mô hình | 0 | 1–5 phút | Cắt ảnh cục bộ; 2.602 node nguồn, ghi đủ cut/skipped/bbox lỗi |

**Tổng dự kiến khoảng 1,18–2,67 USD, khoảng 10–40 phút cho phần dựng**, chưa gồm cổng kiểm mới. Đây là dải tham chiếu, không phải cam kết toàn chuỗi sẽ dùng đúng số này. **Ngân sách đề nghị: 3 USD cho một lượt**, có dự phòng retry. Phải chặn chi trước lời gọi theo ngân sách đã duyệt, tính cả lượng đang chạy; không chỉ kiểm sau mỗi bước. Chuẩn bị/kiểm guard bằng fake trước lượt có tiền, không sửa mã sản phẩm.

Để so sánh: doc-6 W-13 từ kho rỗng đã chạy **341 lời gọi tổng, 95,70 giây, 0,1203762 USD**. Không dùng mức đó làm dự toán doc-1: doc-1 có 102 trang, 168 ngữ cảnh trước nhãn và nhiều công thức hơn; cấu hình gop và số phản hồi cần hỏi phụ thuộc đầu ra mới.

## Lượt thực hiện sau khi được duyệt bằng tin nhắn

**Chưa có phê duyệt cho lượt này.** Trích nguyên văn tin nhắn mới và thời điểm vào báo cáo thực thi trước khi bật `allow_spend`. Không dùng sự im lặng hoặc phê duyệt W-13 cũ thay thế.

1. Ghim main và các cấu hình đã duyệt; tạo snapshot bằng chép tệp của phần doc-1 còn lại, checkpoint, manifest và ledger trước khi ghi artifact mới. Không junction và không dọn worktree/cache.
2. Chạy từ thư mục chung, dùng artifact Pha A chung. Riêng **kho Pha B của lượt dựng dùng đường doc-1 riêng** để không mở/ghi live global chứa tập giữ lại. Việc nối đường kho nằm trong harness vận hành, không đổi source. Không tuyên bố tái dùng tên module/index từ kho chưa được kiểm.
3. Thực hiện đúng `ingest Nhe → kiểm sớm → label-roles → A3/A3′ → A4 language vi/coverage none → roadmap → A12 → concept-index → formulas --pdf`. Sau mỗi bước ghi version, cache hit, lời gọi/usage/chi thật, thời gian và lỗi; chạy lại planner theo đầu ra vừa có.
4. Usage thật lấy từ meter của runner và nhà cung cấp, lưu `build_runs`/báo cáo. Tách số ước tính trong dòng usage riêng của concept-index khỏi chi thật toàn lượt; không cộng ước tính vào số tiền thực chi. Usage thiếu thì báo thiếu, không giả thành 0.
5. Giữ checkpoint khi lỗi hoặc ngân sách không đủ; dừng xin duyệt phần tiếp, không tự tăng ngân sách/model/trần chung.
6. Ghi graph mới thực tế và số module/node học/cạnh. Graph cũ đã mất cả manifest nên kho có thể đánh số lại từ đầu; **không tự đặt tên v45 hoặc v57 để làm test qua**. Kho Pha B riêng ngăn trộn cache theo số version cũ.
7. So số module/node học với baseline v57 đã ghi ở trên; số cạnh cũ hiện thiếu. Không gắn số canonical v4 thành số graph v57. So thẻ/tên module bằng node-id/context hash và số lượng khớp/lệch khi có nguồn doc-1 hợp lệ; nếu chưa có bản cache doc-1 được tách hợp lệ thì báo chưa thể kiểm khớp. Không mở kho global hoặc in nội dung cache.
8. Tạo một worktree kiểm mới từ main sau khi dựng. **Chỉ chép dữ liệu phát triển**, kiểm hash; chạy cả Python qua runner có PostgreSQL, React test và build theo quy trình. Ghi toàn bộ lỗi, kể cả các ca ghim v45; không bỏ test để xanh.
9. Lưu báo cáo thực thi đủ lệnh, tệp, phiên bản, chi thật và phê duyệt; ghi tiền thực chi vào **mục 10** của handoff. Hiện chỉ được ghi dry-run 0 USD, chưa ghi lượt dựng có tiền thành xong.

## Hai quyết định chờ Claude/chủ dự án, không tự sửa

**Test quiz ghim v45:** ưu tiên đổi sang **fixture nhỏ trong repo**, không đọc kho dùng chung. Giữ riêng kiểm tích hợp với graph phát triển mới khi có đầu vào. Đã dừng tìm bản v45 theo chỉ thị, không làm giả phiên bản hoặc sửa assertion để né lỗi. Đề xuất này chưa được duyệt, chưa sửa test. Nếu chưa quyết, vẫn chạy cổng và giải thích rõ các ca v45 còn đỏ.

**Lưu dữ liệu phát triển:** đề xuất **fixture nhỏ trong repo cho unit test**, cộng **snapshot cố định có danh sách SHA-256 cho integration cần PDF/graph thật**. Hai loại phục vụ hai mục đích; bản integration chỉ chứa sách phát triển, có quy trình kiểm/chép vào worktree, không junction và không phụ thuộc kho đang thay đổi. Cần chủ dự án/Claude chốt trước khi đổi cấu trúc test/CI.

## Tiêu chí đóng đợt

- [x] Doc-6 đủ 122/122 hash; đã báo tình trạng 787/927 của manifest cũ.
- [x] Dry-run doc-1 từ main, kiểm cache/checkpoint và báo ước lượng; 0 USD mới.
- [ ] Có tin nhắn duyệt riêng đợt 2 và ngân sách.
- [ ] Doc-1 có graph dùng được, đủ chuẩn bị học, báo usage/chi thật và phiên bản mới.
- [ ] Có số đối chiếu v57/module cache hoặc ghi rõ thiếu nguồn.
- [ ] Cổng đầy đủ ở worktree mới, dữ liệu chép riêng; 0 fail hoặc chỉ còn các ca đã giải thích, không hạ cổng.
- [ ] Báo cáo thực thi và mục 10 handoff có tiền thật; hai đề xuất test/fixture có phán quyết trước khi sửa.
