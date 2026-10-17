# Vé 19g, 19i — tăng tốc CPU, 2026-10-17

**Cập nhật sau kiểm 19g:** cache query được mô tả dưới đây là phương án của lượt cài đầu và đã được gỡ theo yêu cầu mới. NumPy, guard số học và dò tên dùng chung được giữ; phép đo toàn stage doc-4 chuyển sang 19l. Xem [báo cáo 19k và gỡ cache](v4-19kg-song-song-va-go-cache-2026-10-17.md) cho mã và kiểm chứng mới nhất.

## Phạm vi và cách đo

Không gọi LLM hay dịch vụ embedding. Kho nguồn `tmp/v4-17i/artifacts` chỉ được đọc; kết quả pass phụ mới nằm ở `tmp/19gi/trial`. Mã trước sửa đã được chụp vào `tmp/19gi/*_before.py`. Các benchmark lớn chạy lần lượt.

```powershell
.venv/Scripts/python.exe -X utf8 tmp/19gi/benchmark.py before
.venv/Scripts/python.exe -X utf8 tmp/19gi/benchmark.py after
.venv/Scripts/python.exe -X utf8 tmp/19gi/benchmark.py mentions
```

Script đo, dữ liệu JSON và mẫu stack nằm tại `tmp/19gi/`, không đưa nội dung giáo trình vào Git.

## 19i — pass phụ ML

Artifact `graph/doc-4/v4` đã hoàn tất pass phụ; manifest trỏ về pass chính **phiên bản 3**. Chuỗi của bộ artifact này là `gop`, không phải nhánh canonical `v3`. Hai lượt phát lại cùng pass chính phiên bản 3, chunk, mô hình LightGBM, tokenizer và cấu hình.

| Toàn stage, lấy mẫu stack mỗi 10 ms | Trước | Sau |
|---|---:|---:|
| Giây | 374,653 | 197,569 |
| Cặp xét | 23.661 | 23.661 |
| Chiều được chấm, mỗi chiều 82 đặc trưng | 4.650 | 4.650 |
| Cạnh pass phụ | 877 | 877 |

Nhanh **1,90 lần**, giảm **47,3%**. Đây là một cặp đo trên máy hiện tại, có lấy mẫu stack nhẹ; không dùng số 592 giây lịch sử làm mẫu trước.

Mẫu trước có 13.495 stack tại `execute`: dựng đặc trưng chiếm 54,7%; tokenizer nằm trong 28,2% và chuẩn hoá tên trong 22,9% số stack, các tỷ lệ này có thể chồng nhau. Dựng lại các lượt cạnh chiếm 38,1%; bộ chọn/tỉa cặp chiếm 37,1%. Nút cổ chai đã sửa là tính lặp chuẩn hoá, chuẩn hoá lại kết quả tách từ và tính hai cửa sổ có hướng nhiều lần cho cùng cặp. Cache có phạm vi một `SecondaryFeatureContext`. Bộ tỉa đường đi còn là giới hạn tốc độ, chưa sửa trong vé này.

Hai lượt có **cùng từng băm dưới đây**, kể cả toàn payload:

| Đại lượng | SHA-256 |
|---|---|
| Payload pass chính / source hash | `d212b0642959904e26a1204abd6e485864898cff6b52c50c74907be307a3ed01` |
| Config stage | `7a4aa9f851480f188c3eaf1b0963a745eec0a1fcca44aa9c8243fca8b78cf44e` |
| Toàn payload kết quả | `a0de36935e147a6f43f688922a4e322bbc81a418c7f0d687a4948dee2e540c0c` |
| Đặc trưng đưa vào mô hình, giữ thứ tự chiều | `f0ef509735ed2bab70a823d00a052a3ba3fad69228cf1af1e95e5040dab58fd3` |
| Điểm mô hình | `653ccb0de240024ef0ecb9a4afa69c58c73bd1fd7c28cf854d5d6cebf5c72b81` |
| Xác suất sau hiệu chỉnh | `c2b805b789b6b414f7dddd032834b88ce5ce68a4599b0ffb66cf229a7d7c4c7d` |
| Nhật ký quyết định từng chiều | `a5b333f9111e8124341a70a26d781667eb5779ecb6ca314b263c78f12590ff19` |
| Cạnh pass phụ | `a41d4c06d74f1c721c3c7b380b6c516f9d9002dce73266b0a1128fd0810a3acf` |

Ba ngưỡng vẫn là `0.49721683659785315`, `0.48062816610214076`, `0.4791813188439727`; số dương ước lượng cuối vẫn là 982. Không đổi mã đặc trưng, quy tắc ứng viên, cache key hoặc mô hình.

## 19g — mention map

Tích vô hướng dùng NumPy; chuẩn hoá chunk và kết quả dò từng tên được dùng chung cho tên phổ biến, exact hiện tại và luật cũ. Luật chọn tên dài nhất vẫn xét riêng cho từng bộ luật. API chuẩn hoá chunk cũng được vé 19f dùng, giữ cách khớp riêng từng node của neo.

Soát độc lập tìm được ca cosine gần như hằng lệch một ULP giữa BLAS và phép cộng Python, rồi thành z-score khác hẳn do phương sai rất nhỏ. Mã phát hiện thứ hạng hoặc ngưỡng có thể mơ hồ trong sai số làm tròn và tính lại bằng thứ tự cộng Python cũ; không làm tròn hoặc đổi luật xếp hạng. Ca `random.Random(19)` với sáu bộ vector hoán vị phải giữ cả z-score bằng 0 và chọn id `0`.

Fixture trước sửa: `tests/fixtures/mentions/baocao-canhan-before-19g.json`. Đầu vào gồm node/chunk thật của `baocao-canhan` và vector đã ghi; đây là phép thử thuật toán trên cùng vector. Tên phổ biến, hai bộ exact, map bỏ riêng `dense_z` và thứ hạng toàn bộ chunk đều khớp; `dense_z` so với dung sai **tuyệt đối** `1e-12`, `rel=0`.

### Giới hạn dữ liệu và sửa tiền đề của vé

Cả clusters và mentions lấy **description hoặc name** làm văn bản. Tuy nhiên clusters dùng **`SEMANTIC_SIMILARITY`**, mentions dùng **`RETRIEVAL_QUERY`**. Dùng vector clusters ở đây sẽ đổi ý nghĩa và mention map. Adapter thật không có cache vector từng yêu cầu; artifact mention cũ cũng không lưu vector query.

Vector query mới được lưu trong **metadata manifest của mentions**, kèm model id, task và băm văn bản; không thêm trường vào semantic payload hoặc config. Stage tìm cache ở các phiên graph trước, kể cả khi một phiên clusters mới đã bắt đầu. Sai task, sai model hoặc văn bản đổi đều phải embed lại theo đường cũ. Không chuyển lời gọi query sang clusters để làm đẹp số đếm.

Test embedding giả: lượt đầu có 2 yêu cầu; đổi cấu hình mention hoặc tạo clusters mới mà văn bản/model không đổi thì lượt sau có **0 yêu cầu mới**. Đổi văn bản một node gọi lại 1; đổi model/task gọi lại cả 2. Source/config hash mặc định trên fixture giả vẫn khớp mã trước sửa.

**Không có vector `RETRIEVAL_QUERY` gốc của doc-4 để phát lại toàn stage bằng 0 USD.** Đo doc-4 chỉ phát lại CPU dò tên và dense trên vector `SEMANTIC_SIMILARITY` có trong clusters, dùng cùng vector cho mã trước/sau; không gọi đó là thời gian toàn stage hoặc mention map query lịch sử.

### Số đo CPU doc-4

630 node, 671 chunk; cùng đầu vào băm `85e35edbed2cf2b0670b55cca9dc6615a485e54a38ff63c11506355cd915ef35`.

| Phần CPU, không gồm embedding và ghi artifact | Trước | Sau |
|---|---:|---:|
| Dò tên phổ biến, exact hiện tại và luật cũ | 130,057 giây | 13,251 giây |
| Dense | 28,147 giây | 1,401 giây |
| Tổng hai phần | 158,205 giây | 14,652 giây |

Tổng nhanh hơn **10,80 lần**. Cả hai lượt giữ băm thứ hạng `5e2d502a13c9824c21626819b7b46163702c55df02fd4fcc810d4c0dc7609780`, băm exact/legacy `28b1834eba6015a9af269d0ccd4f751deffa46556ef35128e0f3514ccfe32e01` và map sau khi bỏ riêng `dense_z`. Sai lệch z lớn nhất trên mọi cặp là **2,6867397195928788e-14**, nhỏ hơn dung sai tuyệt đối `1e-12`. Băm toàn map khác do các sai lệch số này; không tuyên bố băm toàn map giống hệt. Dữ liệu đo ở `tmp/19gi/mentions-result.json`.

### Phát lại nghiệm thu 18d

Lệnh `.venv\Scripts\python.exe -X utf8 scripts/pass-phu-ml/nghiem_thu_18d.py --kho=tmp/19gi/18d-root-01`, chạy 0 USD, cho kết quả:

| Tài liệu | Chiều so điểm | Lệch điểm tối đa | Cạnh sản phẩm / nghiên cứu / chung | Lệch Q7 / Q7b / bao đóng P / R |
|---|---:|---:|---|---|
| doc-1 | 701 | 0 | 199 / 196 / 195 | 0 / 0 / 0 / 0 |
| xstk-ch3-1 | 203 | 0 | 60 / 59 / 59 | 0 / −0,086 / −0,093 / 0 |
| doc-4 | 4.001 | 0 | 749 / 727 / 716 | +0,002 / 0 / +0,001 / +0,006 |

Tổng **4.905 chiều**, lệch điểm bằng 0. Các số trùng kết quả 18d lượt 2 đã chốt ở `task/v4/18d-nghiem-thu-pass-phu-ml.md`: doc-1/doc-4 đạt ±0,03; xstk có đủ 59/59 cạnh chuẩn và thừa 1, được vé 18d đánh giá theo số cạnh chung vì vàng quá nhỏ.

**Script trả mã 1, in `CHƯA ĐẠT`** vì vẫn áp ±0,03 cho cả xstk. Không gọi lượt script này là xanh; kết quả chất lượng giữ nguyên ngoại lệ xstk đã được chấp nhận từ trước, không phát sinh lệch mới. Thời gian của lượt 18d này có chạy đồng thời với pytest, nên không dùng để so hiệu năng. Phép đo hiệu năng ghép cặp ở mục 19i là lượt riêng trên cùng artifact gop doc-4.

## Kiểm chứng có thể bác bỏ

- `test_real_fixture_preserves_matches_rankings_and_dense_scores`: map, trường số và thứ hạng fixture thật.
- `test_shared_scan_keeps_unicode_legacy_and_longest_match_and_normalizes_chunks_once`: Unicode, luật cũ, tên lồng nhau, mỗi chunk chuẩn hoá một lần; thay bằng ba lượt quét cũ đã thấy đỏ.
- `test_nearly_constant_cosines_preserve_python_scores_and_id_tie_break`: phương sai rất nhỏ; bỏ kiểm tra sai số và chỉ chạy NumPy đã thấy đỏ.
- `test_query_cache_reuses_real_query_vectors_outside_payload_and_cache_key` và `test_new_cluster_artifact_can_reuse_queries_from_previous_mention_manifest`: giảm yêu cầu embedding, giữ config/source key. Thay bằng `_run` cũ đã thấy đỏ: 4 thay vì 2 yêu cầu tích luỹ.
- `test_query_cache_rejects_wrong_task_model_or_changed_text`: sai model/task/text không tái dùng; bỏ riêng kiểm task và model đều đã thấy đỏ.
- `test_all_direction_features_match_frozen_before_19i_hash`: đủ 82 trường của hai chiều, băm lấy từ mã trước sửa.
- `test_context_tokenizes_each_unique_sentence_once_across_directions_and_repeated_queries`: tách từ và cửa sổ không tính lặp; gỡ từng cache tương ứng đều đã thấy đỏ.
- `test_cached_windows_are_local_to_one_document`: tài liệu khác dùng lại id node vẫn có cửa sổ riêng.

Lượt tập trung: 9 test 19g qua; 28 test đặc trưng/pass phụ ML qua. Kiểm toàn kho cuối sau sửa kiến trúc: **1.617 test qua**, mã thoát 0, 458,03 giây; xem [báo cáo tích hợp](v4-19-phan-tich-va-kiem-chung-2026-10-17.md). Phép nghiệm thu thời gian toàn stage 19g vẫn còn mở vì thiếu query lịch sử.

## Kiểm tra kiến trúc khi tích hợp

Bộ tổng đầu tiên có 1.616 test qua và một test kiến trúc đỏ vì NumPy nằm trong domain. Phép nhân ma trận và kiểm tra sai số được chuyển vào `application/use_cases/build_mentions.py`; domain giữ chuẩn hoá vector và xếp hạng Python dùng chung. Danh sách thư viện chuẩn trong test kiến trúc bổ sung `functools` cho cache 19i. Không thêm ngoại lệ cho thư viện bên thứ ba ở domain.

Sau sửa, nhóm kiến trúc, mention stage, số học và fixture: **18 test qua**, 8,48 giây. Thử bỏ guard số học ở vị trí mới vẫn làm test phương sai gần 0 đỏ. Bộ tổng chạy lại **1.617 test qua**.

Phát lại riêng phần sau tối ưu bằng `tmp/19gi/recheck_mentions_after.py` sau khi chuyển lớp: băm toàn map, toàn thứ hạng, exact/legacy và tên phổ biến **giống hệt** lượt sau của cặp benchmark trên doc-4. Lượt kiểm này mất 39,28 giây trong lúc còn kiểm khác, chỉ dùng chứng minh đầu ra; số 10,80× lấy từ cặp đo trước/sau đã ghi, không suy từ lượt kiểm chồng này.
