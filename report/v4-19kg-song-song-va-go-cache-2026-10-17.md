# 19k và gỡ cache query của 19g

**Cập nhật sau kiểm của Claude:** đã gộp ghi trạng thái checkpoint theo đợt, giữ phản hồi hoàn tất khi lỗi và đổi writer sang `json.dumps` với bytes không đổi. Hồi quy mới nhất **1.632 test qua**. Các số checkpoint theo từng phiên bên dưới là của lượt cài đầu; xem [báo cáo sửa ba mục kiểm 19k](v4-19k-checkpoint-kiem-claude-2026-10-17.md).

Ngày 2026-10-17. Theo yêu cầu tiếp theo của chủ dự án, sau quyết định nhận 19k trong báo cáo 19j và ghi chú kiểm 19g. Chỉ dùng mô hình giả, HTTP giả và fixture đã lưu; **chi phí API của lượt này 0 USD**. Không chạy lại thí nghiệm có chi, không thực hiện cổng 19l hoặc đổi chuỗi mặc định 19m.

## Pass chính song song

`BuildMainEdges(..., parallel_sessions=True)` là mặc định. Composition nối với `DOC2ROADMAP_ROADMAP_MAIN_PARALLEL=true` trong cấu hình và `.env.example`. Đặt `false` để trở lại các đợt nối tiếp trong từng chương. Giá trị `parallel_sessions` nằm trong config/hash của pass chính và id checkpoint; số worker vẫn không làm đổi cache.

Khi bật, mọi phiên chờ cùng một đợt như biến thể `song` của 19j. Đầu vào giữ nguyên khoá `previous_edges_in_chapter=[]` và `previous_edges_omitted_count=0`, kể cả khi nối lại từ checkpoint có cạnh đã lưu. Prompt hệ thống và đường sửa lời phán không đổi. Bộ chạy model và limiter cũ tiếp tục điều khiển số lời đồng thời.

Kết quả và checkpoint vẫn ghi theo id phiên đã sắp. Phần kiểm lời phán khi tiếp tục một đợt song song dùng cùng nền cạnh trống như lần đầu; phần gộp cuối vẫn xử lý trùng cạnh với phần đã lưu. Nếu dùng các cạnh đã lưu làm nền kiểm, cùng đầu ra model sẽ đổi từ `accepted` thành `dropped_duplicate`, làm nhật ký khác lượt chạy liền mạch. Test tái hiện đúng trường hợp này.

Script đối chứng `scripts/gop-khau/thu_pass_chinh.py` chọn tuỳ chọn sản phẩm theo `noi`/`song`, nên biến thể nối tiếp không bị đổi nghĩa khi sản phẩm bật mặc định song song. README có cách tắt.

## Gỡ cache vector query

Đã xoá `_cached_queries`, việc duyệt các phiên graph cũ và metadata `query_embedding_cache` khi ghi manifest. Khi stage cache miss, mentions gọi embedding `RETRIEVAL_QUERY` cho các mô tả/tên đang học được. Khi cả artifact stage đã có, vẫn tái dùng như cũ. Dry-run với upstream tường minh không tải lịch sử graph.

NumPy, guard sai số và lượt dò tên dùng chung giữ nguyên. Trước sửa đã ghim băm toàn mention map của fixture thật `baocao-canhan` là `00c96ea9b8c46e8585678c32a32ab57b7eb9eea390f25ec9646ac2f3c90ce68d`; sau gỡ cache test vẫn đúng băm này. Source/config hash mentions mặc định cũng giữ nguyên.

Tìm `query_embedding_cache` trong manifest của `artifacts/graph` không có kết quả; không cần sửa artifact chính. Các kho thử đỏ/xanh cũ giữ làm bằng chứng. Phép đo toàn stage doc-4 được chuyển sang cổng 19l theo ghi chú của vé 19g.

## Kiểm chứng

- Trước sửa: **7 test đỏ, 4 xanh**. Các nhánh đỏ gồm thiếu mặc định mới, chưa có tuỳ chọn, chưa chạy đồng thời, checkpoint chưa chạy theo đợt, limiter chỉ đạt 1, manifest còn chứa query cache và dry-run còn đọc lịch sử.
- Nhóm cấu hình, composition, main, mention, dry-run và kiến trúc: **36 test qua**, 8,48 giây.
- Nhóm đồ thị gop, tích hợp Pha B, pipeline và hồi quy bốn tài liệu: **43 test qua**, 56,92 giây.
- `test_default_parallel_sessions_keep_experiment_input_prompt_and_deterministic_results`: 4 phiên cùng chương đạt đỉnh 4; mỗi phiên có một lời sửa; toàn payload, prompt, đầu vào và nhật ký bằng chạy 1 worker; checkpoint 1/2/3/4 phiên.
- `test_disabling_parallel_restores_previous_edges_and_sequential_chapter`: đỉnh 1, các phiên sau nhận cạnh phiên trước.
- `test_switch_changes_cache_and_checkpoint_identity_but_worker_count_does_not`: hai lựa chọn khác cache/checkpoint, đảo về tái dùng artifact cũ; đổi worker tái dùng cache.
- `test_parallel_resume_preserves_inputs_edges_and_executor_decisions`: ngắt sau checkpoint đầu, chạy tiếp 3 phiên; cạnh và cả nhật ký model/executor bằng chạy liền mạch. Đã thử bỏ nền kiểm trống trong bộ nhớ và thấy assertion nhật ký đỏ.
- `test_main_parallel_requests_still_obey_actual_extractor_limiter`: extractor thật, HTTP giả, 4 worker; đỉnh HTTP và limiter đều 2.
- Hai test gỡ cache kiểm manifest không có vector query, stage cache còn hiệu lực, và dry-run/thực thi với upstream tường minh không đọc graph lịch sử. Cả hai đã đỏ trên mã trước sửa.
- Thử bỏ trường `parallel_sessions` khỏi config trong bộ nhớ làm test đổi cache đỏ; không sửa tệp nguồn để thử phá luật.

### Phát lại dữ liệu thật của 19j, 0 USD

Lệnh `.venv\Scripts\python.exe tmp/19kg-replay-research.py` đọc các kho `tmp/v4-19j/kho/{doc}-song-s1`; mentions doc-1/xstk ghim v10, doc-4 ghim v2. Bộ model chỉ trả phản hồi đã lưu theo băm đầu vào; đầu vào chưa có sẽ dừng bằng assertion. Mọi ghi graph/checkpoint của lượt này nằm trong bộ nhớ.

| Tài liệu | Đầu vào model khớp / đã lưu | Cạnh pass chính khớp |
|---|---:|---:|
| doc-1 | 74 / 74 | 217 |
| xstk-ch3-1 | 44 / 44 | 63 |
| doc-4 | 243 / 243 | 488 |

**361/361 đầu vào khớp**, kể cả lời sửa, cùng prompt hệ thống. Danh sách phiên, toàn cạnh, cờ và nhật ký executor của cả ba tài liệu cùng băm với biến thể song song đã được 19j nhận. Đây là phát lại phản hồi đã có, không đo lại tốc độ LLM/E4 hoặc tính chi phí mô hình mới. Kết quả máy đọc và băm đầy đủ: `tmp/19kg-research-replay.json`.

Lượt tổng đầu phát hiện `test_mentioned_only_node_is_context_not_allowed_target` tạo instance bằng `object.__new__`, bỏ hàm khởi tạo nên thiếu cấu hình mới. Đã đổi test sang hàm khởi tạo thật; giữ nguyên các assertion về đích được dạy/khái niệm chỉ nhắc. Nhóm này và 19k: **8 test qua**, 3,74 giây. Dừng lượt tổng đã đỏ và chạy lại từ đầu; không thêm xử lý cho instance không được khởi tạo vào mã sản phẩm.

**Hồi quy toàn dự án: 1.621 test qua, 0 lỗi, mã thoát 0, 276,78 giây.** Báo cáo JUnit `tmp/pytest-19kg-full-02.xml`. `git diff --check` qua. Không phát sinh chi phí API. Lệnh:

```powershell
$env:HF_HUB_OFFLINE='1'
$env:TRANSFORMERS_OFFLINE='1'
.venv\Scripts\python.exe -m pytest -p no:cacheprovider --basetemp=tmp/pytest-19kg-full-02 --junitxml=tmp/pytest-19kg-full-02.xml --tb=short
```
