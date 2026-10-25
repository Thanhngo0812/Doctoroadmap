# W-15 — sửa operator sau nghiệm thu lần 4 — 2026-10-25

**Hiện hành sau `9b3bd82`; chưa ghép main, chưa chạy có phí, toàn W-15 còn mở.**
Tiếp đúng worktree `tmp/w15-real-build`, nhánh `work/w15-real-build`; root giữ main.
Đã đọc biên bản lần 4, core-review/review.md, summary và embedding-pricing-primary-check.md.
Main local `46d829a55a62d852897f07102e89cf9a1fd5185e` đã nhận bằng merge `a4f2d08` trên cây sạch.
Giữ nguyên các commit đã nộp; mốc `bf761fe` đã được nhận riêng, không làm lại adapter/port hoặc mốc fake/PG.

## W15-R4-1 — đường dẫn plan

Sửa đúng một dòng trong `prepare`: `run_dir.relative_to(ROOT).as_posix()` thay `str(...)`.
Không sửa `safe_path`, không chỉnh tay các plan thật đã lưu. Commit sửa **`3d5e1cd`**.

Test `test_prepare_saved_plan_roundtrips_to_execute_composition_and_rejects_escape` thực sự gọi
prepare, đọc JSON trên đĩa, tạo approval chỉ trong test, rồi gọi execute trên nguyên byte plan đó.
Dry-run dùng PDF tổng hợp và DocumentPipeline/PG thật của fixture; chỉ CREATE/migrate được fake
vì fixture đã sở hữu database disposable đã migrate. Guard provider/ADC vẫn cấm.
Tại composition của execute dùng sentinel fake để dừng trước dựng có phí; không tuyên bố đã chạy
paid hoặc chứng minh chất lượng đầu ra. Kiểm độc lập cùng JSON không bị sửa khi execute đọc.

[RED trên mã cũ](w15-evidence/runs/r4-plan-red-20261025-01.xml): một test fail đúng
`Path escapes its root` ở safe_path, trước composition; không setup error.
[GREEN sau sửa](w15-evidence/runs/r4-plan-green-20261025-01.xml): một test đạt.
Cùng ca kiểm `../outside`, `/outside`, `C:/outside`, `tmp\\outside` đều bị guard thật từ chối,
không đi composition thêm lần nào; không tạo execution.json.

## W15-R4-P1 — nguồn giá và chỉ thị demo mới

Đã mở được trang SKU online Google bằng Chromium ẩn danh mới, không account/ADC/model API:
[SKU online E4FB-7AE2-9CAE](https://cloud.google.com/skus?currency=USD&filter=E4FB-7AE2-9CAE).
Trang và phản hồi dữ liệu công khai ghi `0.00015 USD per 1,000 count`, vùng global,
tên Large Text Embedding Model - Predictions. Dữ liệu chưa định nghĩa count là token/ký tự.
[Bản ghi và SHA raw](w15-evidence/r4-20261025/embedding-sku-public.json);
raw public giữ local `tmp/w15-r4-pricing/sku-browser-rpc.json` và nội dung chữ trang trong sku-browser.txt.
Không coi tên SKU là chứng cứ đủ ánh xạ model/unit; **không kết luận code tính thiếu tiền**.

| Nguồn Google đã đối chiếu | Điều chứng minh / giới hạn |
|---|---|
| [Bảng Embedding costs](https://cloud.google.com/vertex-ai/generative-ai/pricing#embedding-costs) | Online 0,00015 và batch 0,00012 theo 1.000 count; không chốt nghĩa của count từ tiêu đề này |
| [BigQuery Gemini embedding](https://cloud.google.com/blog/products/data-analytics/use-gemini-and-open-source-text-embedding-models-in-bigquery) | Ví dụ Gemini batch tính token, khác các model text-embedding cũ tính ký tự; không thay cho hợp đồng online |
| [Vertex text embeddings API](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/model-reference/text-embeddings-api) | `statistics.token_count` là token đầu vào, gemini-embedding-001 nhận một text, giới hạn 2.048 token; không tự xác định đơn vị hóa đơn |
| [Get text embeddings](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/embeddings/get-text-embeddings) | Ví dụ có token_count cùng billable_character_count; hai số tồn tại không chứng minh cả hai đều là lượng tính phí cho model này |
| [Google Gen AI SDK types](https://github.com/googleapis/python-genai/blob/main/google/genai/types.py) | Hai trường metadata có ý nghĩa riêng, không phải bảng giá online theo SKU |
| [Google Developers thông báo Gemini Embedding](https://developers.googleblog.com/en/gemini-embedding-available-gemini-api/) | Giá token trong nội dung Gemini API; không suy ra SKU Vertex online chỉ từ việc cùng tên model |

Core hiện `_embed_vertex` đưa `statistics.token_count` vào `record_usage(promptTokenCount, embedding=True)`;
BuildUsage.capture gọi token_cost theo phase_b_pricing (0,15 USD/triệu input token).
Guard cũ dùng cùng token_count/rate; không đọc billableCharacterCount.
Theo **giả định token**: dự phòng 2.048 × 0,15 / 1.000.000 = **0,0003072 USD/request**,
phản hồi 100 token là **0,000015 USD**. Nếu giá thực theo ký tự, cận token và công thức đó
không chứng minh được tiền phải trả. Không sửa core thuộc làn Claude hoặc biến metadata ký tự thành token.

Ban đầu xử lý fail-closed theo giao việc: commit **`7f90749`** từ chối grant trước tiêu thụ reference/khởi tạo paid pipeline,
và chặn transport embedding trước dispatch. Các fixture token-price được ghi rõ giả định tổng hợp.
[Focused 36 ca](w15-evidence/runs/r4-final-focused-20261025-01.xml) đạt;
[3 phép phản chứng](w15-evidence/mutations/r4-20261025/mutations.json) đều bị assertion bắt,
0 setup error và source phục hồi nguyên byte. Giữ kết quả này làm lịch sử trước chỉ thị demo mới.

Giữ lượt `r4-price-red-20261025-01`: hai test fail, trong đó ca grant là assertion hợp lệ;
ca transport ban đầu dùng fake response thiếu predictions nên fail KeyError, không đếm nó
làm assertion phản chứng. Đã đổi fake response đủ token_count và phép phá `unverified-embedding`
sau đó fail bằng `DID NOT RAISE`, không setup error. Không xóa hoặc ghi đè lượt đầu.

**Chỉ thị mới của chủ dự án trong phiên 2026-10-25, trích nguyên:**

> bạn chốt 1 con số lý thuyết đi, và nói là chủ dự án cho, vì đây là 1 sản phẩm demo nên tính kĩ ko quan trọng, trước sau gì chủ dự án cũng nâng trần lên cao thôi

Theo chỉ thị này, chọn **giá giả định demo 0,15 USD/triệu input token embedding**.
Đây là quyết định mô hình tính thử được chủ dự án cho phép; **không ghi Google online đã xác minh**,
không ghi đã đối soát hóa đơn. Không lấy khả năng nâng trần tương lai làm quyền chi hiện tại.
Profile demo phải được ghi rõ trong plan/grant/audit, thiếu hoặc sai profile vẫn từ chối;
việc chủ dự án cho chọn giá lý thuyết không được biến thành một tin nhắn giả duyệt đúng PDF/lượt/trần.

Phạm vi từ chối thay đổi theo chỉ thị mới: điều kiện P1 về nguồn online vẫn ghi **chưa xác minh**;
chủ dự án cho phép mô hình tính thử riêng thay điều kiện đợi đó cho demo. Không diễn đạt là đã
đóng P1 bằng chứng Google. Guard dự phòng/trần theo giá giả định; không hứa đó là trần hóa đơn
Vertex thực nếu đơn vị thực khác giả định. Khi đối soát hoặc ra product phải làm rõ ánh xạ đó.

Đã cài profile **`owner-demo-embedding-token-20261025`** tại commit **`cfabaeb`**.
Prepare ghi tên profile và `embedding_billing_verified=false`; execute đối chiếu profile của
approval với plan. Grant kiểm đúng tên trước consume, guard mang profile trong snapshot/PG record.
Không có env flag hoặc trường HTTP mở chi; grant thiếu profile (kể cả plan cũ) không được tự nâng cấp.
Tháo fixture monkeypatch giá ở các ca dương: test hiện dùng đường kiểm profile thật với provider giả.

[RED profile demo](w15-evidence/runs/r4-demo-red-20261025-01.xml): 2 assertion fail trước cài,
[GREEN](w15-evidence/runs/r4-demo-green-20261025-01.xml): **39 đạt**, không setup error.
[Bốn mutation cuối](w15-evidence/mutations/r4-demo-20261025/mutations.json): đường dẫn portable,
chặn transport/grant khi thiếu profile và nhãn billing_verified đều bị assertion bắt, phục hồi byte.
Ca giá dương nhận 100 token cùng 9.999 ký tự nhưng tính 0,000015 USD theo **giả định token**;
khi chỉ có ký tự mà thiếu token vẫn unknown/chặn tiếp, không dùng ký tự để lấp usage.
Record đọc từ connection PG độc lập vẫn ghi chưa xác minh; không tuyên bố đây là chi thật đo từ Google.

## Đề nghị lượt thật và số đã biết

Giữ đề nghị **bootstrap doc-6 trần 1 USD** và **một web build rau thủy canh 52 trang trần 3 USD**,
tổng đề nghị **4 USD**. Cap là mức thử, không là dự toán hoặc cam kết dựng xong.
Chưa thực hiện hai lượt, không tự retry có phí hoặc nâng trần. Sau profile demo được soát,
phải tạo plan mới theo HEAD/profile, giữ plan cũ nguyên trạng, rồi chủ dự án duyệt đúng lượt cụ thể.

| PDF | SHA-256 |
|---|---|
| doc-6, 25 trang | `82cb494d407c4755d29deb7c08b9a4f3794f79e241c307fd2b5dfc149cd559c7` |
| rau-thuy-canh, 52 trang | `1f019766e74a747d293c15ad5bc86b2ea90420b49a8437cf27c1f6805656a627` |

| Bước | Cache hit/miss/unknown và gọi | USD/phút đã đo và chưa đo |
|---|---|---|
| doc_reading | Hai dry-run PDF thật đã đạt; 0 gọi sinh/embedding | 0 USD; wall cụ thể giữ trong receipt dry-run lịch sử |
| concepts | Doc-6 cache-only thật **miss label-roles / SpendNotAllowed**; downstream unknown | 0 USD mới ở lượt dừng; số gọi/embedding/chi/phút toàn bước của lượt có phí chưa đo |
| graph | Chưa có graph đúng u-hash/profile của lượt web thật; unknown | gọi/embedding/USD/phút chưa đo |
| learning_prep | Chưa chạy thật sau graph của hai lượt đề nghị; unknown | gọi/embedding/USD/phút chưa đo |
| embedding wait | Chưa có thời gian provider thật của hai lượt | Không lấy wall cả bước hoặc cộng duration song song để đoán wait |

Không ghi doc-6 đã ready/course/mail hoặc dựng miễn phí. Bootstrap dự kiến có phí riêng,
sau đó mới kiểm lần web đầu dùng đúng cache với allow_spend=false và guard provider;
không sửa alias/version/label-roles để ép reuse. Đơn vị USD theo profile demo là giá tính từ usage,
chưa là chi hóa đơn Vertex đã đối soát.

## Phạm vi, kiểm và phần cần bàn giao

Mặc định web giữ `allow_spend=False`; grant chỉ operator tin cậy, đúng SHA/u-hash/version/profile/lượt/trần,
consume một lần trong PG; HTTP không mở quyền chi. Meter delta vẫn chi build duy nhất,
counted_in=build chỉ trace, không mở purpose dựng vào DailySpendGuard học.
Giữ fake provider/ADC/SMTP/Cloudinary guard trong test; artifact thử riêng, không nối kho chung.

[Kiểm fixture](w15-evidence/r4-20261025/fixture-integrity.json): worktree hiện có 3.144 tệp sáu cuốn đúng
manifest/SHA/ordinary copy qua safe_path của helper; candidate được kiểm riêng đúng SHA/1.054.520 byte.
Không cần chép lại worktree hiện có; worktree kiểm mới phải dùng helper sáu cuốn rồi chép candidate train riêng.
Không đọc learner store/tập giữ lại/kho artifact chung và không commit PDF.

Không sửa task/kế hoạch/bàn giao điều phối, không gửi message cho phiên khác, không ghép/push main.
Khi có lượt thật được duyệt, báo cáo phải trích nguyên tin duyệt và ghi usage/chi theo basis minh bạch;
phần chi thật bàn giao chủ dự án để điều phối ghi mục 10. Hiện chi nhà cung cấp mới **0 USD**.

## Cổng trước/sau và review

| Mốc | Kết quả | Bằng chứng |
|---|---|---|
| Trước chỉ thị demo mới, `7f90749` | 2.638 Python đạt, 1 skip/1 xfail cũ, native 0 | [JUnit](w15-evidence/runs/r4-full-20261025-01.xml) |
| React lần đầu sau nhận main, `7f90749` | Native 1, 3 suite không resolve react-markdown/KaTeX do node_modules cũ | [Log giữ nguyên](w15-evidence/runs/r4-react-20261025-01.log) |
| Đồng bộ dependencies | npm ci native 0 theo lockfile từ main; không sửa package/test | [Native](w15-evidence/runs/r4-npm-ci-20261025-01-exit.json) |
| Profile demo cuối, `cfabaeb`, Python | **2.641 đạt**, 1 skip/1 xfail cũ, native 0 | [JUnit](w15-evidence/runs/r4-full-20261025-02.xml), [native](w15-evidence/runs/r4-full-20261025-02-exit.json) |
| React cuối, `cfabaeb` | 181 đạt, native 0 | [JUnit](w15-evidence/runs/r4-react-20261025-02.xml) |
| Build cuối, `cfabaeb` | Thành công, native 0 | [Native](w15-evidence/runs/r4-build-20261025-02-exit.json) |

Tất cả Python qua runner bắt buộc PostgreSQL và một cổng toàn repo mỗi lúc, basetemp/nhãn riêng.
Không giảm assertion/timeout/guard/skip để ép xanh. Các cổng trước vẫn giữ nguyên nhãn/commit;
capture focused/mutation trước commit có SHA nguồn đang sửa, không gán là cây sạch của HEAD cũ.
Các tệp test/harness của mốc đã đạt không làm lại; lần chạy trong cổng đầy đủ chỉ là kiểm hồi quy bắt buộc.

Review: sửa giới hạn ở operator/guard và test liên quan. Không sửa lõi `src/doc2roadmap`,
không thêm dependency/migration, không sửa price table hoặc DailySpendGuard thuộc lõi.
Chốt tên profile giữ rõ ranh giới operator tin cậy; không mô tả approval JSON là chữ ký của chủ dự án.
Chi đã biết giữ meter delta; unknown vẫn giữ dự phòng và đánh dấu receipt thiếu usage khi cần.
Giá demo không thêm ledger thứ hai. Cơ chế hook chỉ dành process operator riêng,
không nhận là worker chung đã sẵn sàng deploy hoặc đã kiểm phục hồi sau kill process.
W15-R4-1 đã có bằng chứng đóng; P1 nguồn online vẫn chưa xác minh và được chủ dự án cho phép
thay bằng giả định cho demo, chưa phải nghiệm thu giá product. Toàn W-15 còn chờ lượt thật/kiểm đầu ra.

[Summary hiện hành](w15-evidence/r4-20261025/summary.json),
[bảo toàn lịch sử](w15-evidence/r4-20261025/historical-integrity.json),
[chuẩn hóa có raw giữ lại](w15-evidence/r4-20261025/normalization.json),
[manifest mới](w15-evidence/r4-20261025/manifest.json).
Giữ nguyên bốn manifest lịch sử 401 + 103 + 108 + 472 entry. Chỉ chuẩn hóa tệp bằng chứng mới
sang UTF-8/LF, bỏ khoảng trắng cuối dòng, giữ JSON values/JUnit case attributes và raw trong
`tmp/w15-r4-raw-20261025`. Không phát hiện giá trị credentials cấu hình trong bằng chứng mới.
Export W-06/W-14 mỗi vòng được chép riêng trước phục hồi; W-25 mới giữ theo nhãn trong
`w15-evidence/w25-regressions`. Không xóa artifact/snapshot/PDF/worktree.

Sau commit hồ sơ, tạo lại đúng hai plan trên HEAD bàn giao với provider/ADC guard, 0 USD,
PG/artifact riêng, profile demo tường minh và `approved=false`; không tái dùng plan Windows cũ.
Plan và đề nghị cuối ở local ignored `tmp/w15-r4-approval-request.json` để HEAD không đổi do
việc lưu plan; kiểm lại SHA nguồn khớp cổng, source PDF một link và các bảng upload/build/course/
usage/cache/record đều rỗng sau dry-run. Kết quả cuối/path/hash báo trực tiếp chủ dự án.
Không tạo approval thật hoặc chạy execute khi chưa nhận tin duyệt đúng hai lượt mới đó.
