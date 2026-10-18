# Bàn giao Pha B — vé 01–18 và 24 — 2026-10-15

Đã cài các use case, CLI và trang xem thử cho vé 01–18 và 24, phối hợp với ba subagent GPT-6 Luna theo phân công của chủ dự án. Trạng thái là **đã cài và kiểm thử, chờ soát nghiệm thu**. Vé 19–23 không nằm trong lần bàn giao này; các lượt thử dưới đây không thay thế đánh giá chất lượng và chấm mù của những vé đó.

## Chạy và xem kết quả

Trang xem thử: <http://127.0.0.1:8765/>. Máy chủ hiện chạy chế độ ngoại tuyến, thao tác trên trang không phát sinh chi phí Gemini. Tên và mô tả module đọc từ các artifact đã tạo bằng Gemini; chế độ ngoại tuyến của bài giảng/chat/quiz không làm mất các tên này.

```powershell
.\.venv\Scripts\python.exe -B -X utf8 -m doc2roadmap.presentation.cli.main phase-b serve --port 8765
```

Chọn tài liệu ở thanh trên, bấm **Nạp lộ trình mới** nếu trang đã mở từ trước. Cột lộ trình hiện tên, mã mục và mô tả. Hướng dẫn lệnh và chế độ ở [doc/pha-b-cli.md](../doc/pha-b-cli.md).

## Tên module: vé 05 và 06

Vé 05 dựng tên và mô tả theo luật từ giáo trình/đồ thị. Vé 06 gọi LLM cho từng module, kiểm đầu ra rồi dùng kết quả vé 05 nếu không đạt. Tên dự phòng ưu tiên tiêu đề mục sách thích hợp; nếu không thì ghép tên khái niệm nguyên vẹn. Không phải tên được bịa ngoài nguồn.

Đã chạy thật trên cả sáu tài liệu phát triển: **159 module, 152 tên và mô tả LLM được chấp nhận, 7 dùng dự phòng**. Cả sáu chỉ mục khái niệm đã có, tổng 915 khái niệm. Số module thực tế khác con số 142 ước tính cũ trong vé.

| Tài liệu | Graph A10 đầu vào | Graph đã đặt tên | LLM / tổng | Dự phòng |
|---|---:|---:|---:|---:|
| doc-1 | v37 | v45 | 39 / 39 | 0 |
| nhap-mon-ml | v37 | v46 | 14 / 15 | 1 |
| naive-bayes | v37 | v45 | 5 / 5 | 0 |
| doc-6 | v8 | v17 | 4 / 4 | 0 |
| xstk-ch3-1 | v46 | v48 | 9 / 9 | 0 |
| doc-4 | v12 | v15 | 81 / 87 | 6 |

Artifact ở `artifacts/graph/<doc_id>/vN/`, có `roadmap.html`. Audit đọc lại các artifact: [JSON](../tmp/phaseb-handoff-audit.json), [script](../tmp/phaseb-handoff-audit.py).

| Tài liệu / module | Tên dự phòng đang lưu | Lý do loại đầu ra LLM |
|---|---|---|
| nhap-mon-ml / module_010 | Thu thập dữ liệu · Tiền xử lý dữ liệu | Từ vựng ngoài tập được phép |
| doc-4 / module_028 | Vận động xã hội · Tính khách quan | Trùng tên module gần |
| doc-4 / module_032 | Tình cảm · Ý chí | Trùng tên module gần |
| doc-4 / module_040 | Nội dung và hình thức | Từ vựng ngoài tập được phép |
| doc-4 / module_043 | Khả năng ngẫu nhiên · Khả năng gần | Từ vựng ngoài tập được phép |
| doc-4 / module_062 | Trình độ lực lượng sản xuất | Hình thức tên |
| doc-4 / module_082 | hình tượng nghệ thuật · Ý thức tôn giáo | Trùng tên module gần |

Các trường `title_source`, `description_source`, `naming_flags` giữ nguồn và lý do kiểm. Có một cặp tên trùng xa nhau ở nhap-mon-ml, module_009 và module_013; luật hiện tại kiểm phạm vi ±2 module theo vé. Xem số đo và chi phí từng cuốn ở [báo cáo tên và chỉ mục](pha-b-live-group1-2026-10-15.md).

Rà soát cuối phát hiện tên dự phòng module_062 dài 87 ký tự, vượt trần 60. Đã sửa luật chọn tên dự phòng để dùng cặp hoặc tên khái niệm nguyên vẹn đủ ngắn, không cắt cụt chữ; bản v15 dùng tên 27 ký tự. Xuất lại từ v12 bằng cache và model stub chặn mạng: dry-run 0 lời gọi, thực tế 0 lời gọi, 81 tên LLM còn nguyên. Khâu tên tăng algorithm ID lên v3 nhưng giữ prompt và khóa phản hồi đã ghi.

Lệnh đặt tên mặc định chạy lại theo A10 đầu vào ban đầu, nên tên hàng xóm do chính lần đặt tên trước tạo không vô tình làm mất cache. Truyền rõ `--graph-version` vẫn cho phép đặt tên theo ngữ cảnh bản được chỉ định. Dùng lại cache cần cùng kho và cấu hình; kho smoke nhóm 1 là `artifacts/phase_b/acceptance-group1.json`, tách với kho live mặc định.

Đã kiểm tra lại lệnh mặc định trên cả sáu tài liệu với model stub chặn mạng: cả sáu dry-run đều 0 lời gọi, 0 USD; SHA-256 của tệp cache/sổ chi trước và sau giống nhau. [Kết quả](../tmp/phaseb-handoff-repeat-check.json), [script](../tmp/phaseb-handoff-repeat-check.py).

## Phạm vi mã bàn giao

| Vé | Kết quả | Điểm vào chính |
|---|---|---|
| 01 | Kho JSON và bộ nhớ, single-flight, cache âm, sổ chi và giới hạn dùng chung | `application/ports/phase_b.py`, `domain/phase_b_limits.py`, `infrastructure/artifacts/phase_b_store.py` |
| 02–03 | Read-model đồ thị, nhãn nguồn có offset raw, công cụ đồ thị, A12 và truy hồi ưu tiên module | `domain/learning_graph.py`, `domain/source_labels.py`, `application/phase_b/retrieval.py` |
| 04 | Cắt ảnh công thức theo từng lần xuất hiện, gắn lại vào bài giảng | `application/phase_b/formula_images.py`, `infrastructure/media/formula_images.py` |
| 05–07 | Tên tất định, tên LLM có kiểm/cache, chỉ mục khái niệm | `application/phase_b/naming.py`, `application/phase_b/concept_index.py` |
| 08–10 | Trợ lý gọi công cụ, vòng lặp có trần, hội thoại, trích dẫn, từ chối, nhắc nền | `application/phase_b/assistant.py` |
| 11–14 | Bài giảng trích nguồn, sinh có kiểm, stream, tải trước, công cụ bài giảng | `application/phase_b/lectures.py` |
| 15–17 | Quiz điền khuyết, sinh LLM và kiểm mù, lần làm, phản hồi, lịch sử, báo lỗi | `application/phase_b/quiz.py` |
| 18 | Tài liệu theo yêu cầu có trích dẫn, lưu và xuất Markdown | `application/phase_b/documents.py` |
| 24 | HTTP localhost, JSON/SSE, HTML tiếng Việt, bốn vùng và mở nguồn | `presentation/preview/server.py`, `presentation/preview/phase_b.html` |

Lắp ghép ở `composition_phase_b.py`; CLI ở `presentation/cli/phase_b.py`. Adapter Gemini, ghi/phát lại nằm ở `infrastructure/llm/phase_b.py`. Application không import infrastructure; domain dùng thư viện chuẩn theo kiểm kiến trúc hiện có.

Đã nối khâu tên mới vào lệnh roadmap hiện hữu. Không thay thành viên module, dãy học, node hay cạnh khi đặt tên; `section_code` được bổ sung từ mục sách. Loader mặc định chọn A10 hoàn chỉnh, bỏ artifact trung gian mới hơn. Các thay đổi parser chỉ phục vụ tọa độ ảnh công thức; đã kiểm hồi quy đầu ra Nhe.

## Kết quả thử nội dung và chi phí

Chủ dự án duyệt ba nhóm, mỗi nhóm tối đa 0,50 USD, tổng tối đa 1,50 USD. Mọi lượt có tiền đã dừng; việc bàn giao và phát lại không gọi nhà cung cấp.

| Nhóm | USD ghi trong sổ, gồm các lần thử lỗi | Cận trên gồm dự phòng thiếu usage |
|---|---:|---:|
| 1 — tên module và chỉ mục | 0,30966550 | 0,30966550 |
| 2 — bài giảng, trợ lý, tài liệu | 0,06717575 | 0,07717575 |
| 3 — quiz và bộ kiểm mù | 0,29097900 | 0,29422110 |
| **Tổng** | **0,66782025** | **0,68106235** |

Đây là USD ước tính từ token theo cấu hình, không phải hóa đơn nhà cung cấp. Hai lượt lỗi đầu còn thiếu số token đầy đủ nên báo cả cận trên, không coi là miễn phí. Chi tiết từng lần thử giữ trong báo cáo nhánh và recording.

Lượt nội dung cuối nhóm 2 gồm 24 thao tác trên sáu graph ghim: 12 bài giảng (7 `ready`, 5 `fallback`), 6 câu trợ lý (4 `answered`, 2 `insufficient_context`), 6 tài liệu (4 `ready`, 2 `failed`). Đã phát lại một mẫu thành công của mỗi loại với sổ chi **0 USD**. Các trạng thái dự phòng/thiếu nguồn/thất bại được giữ trong kết quả, không đổi nhãn thành thành công. [Báo cáo nhóm 2](pha-b-live-group2-v2-2026-10-15.md).

Nhóm quiz đã thử cả sáu tài liệu, phát hiện và sửa lỗi hợp đồng nhãn nguồn và hướng dẫn bộ kiểm mù. Lượt cuối trên một khái niệm doc-1 trả một câu `generator=llm` được bộ kiểm mù chấp nhận; phát lại ra cùng câu, không gọi API. Đây là kiểm tra hợp đồng thực, chưa chứng minh chất lượng quiz LLM trên toàn bộ sáu cuốn. [Báo cáo quiz thật cuối](pha-b-live-quiz-final-2026-10-15.md).

## Kiểm thử và bằng chứng

Lượt unit diện rộng gần nhất: **1.287 passed, 1 skipped**. Sau sửa chi phí phát lại và hợp đồng quiz, lượt tập trung: **64 passed**. Kiểm tra cuối cho preview/tên/chỉ mục/truy hồi/kiến trúc: **27 passed**. Có cảnh báo deprecation PyMuPDF/SWIG; lượt cuối còn cảnh báo không ghi được pytest cache, không có test thất bại.

Sau rà soát tên dài và cache của lệnh chạy lại, hai ca mới đã thấy đỏ trên hành vi cũ rồi xanh: `test_overlong_author_heading_uses_complete_fallback_after_title_validation_failure` và `test_repeating_default_naming_reuses_original_a10_context_without_more_model_calls`. Lượt tên/runtime/kiến trúc sau sửa: **14 passed**. Lượt cuối bổ sung cả ba ca lineage sai và HTTP: **33 passed**, chỉ còn cảnh báo deprecation SWIG. `git diff --check` không báo lỗi whitespace trên các tệp tracked thuộc phạm vi.

Lệnh kiểm tra cuối đã chạy:

```powershell
.\.tools\uv.exe run pytest tests/unit/presentation/test_phase_b_preview.py tests/unit/application/test_phase_b_naming.py tests/unit/application/test_phase_b_naming_runtime.py tests/unit/application/test_phase_b_concept_index.py tests/unit/application/test_phase_b_retrieval.py tests/unit/test_architecture.py --basetemp tmp/pytest-phase-b-handoff-final-20261015 -q -p no:cacheprovider
```

Các bất biến chính có assertion chạy được:

| Bất biến | Assertion |
|---|---|
| Dry-run không gọi model hay ghi kho | `test_dry_run_never_calls_search_model_or_writes_store`, `test_naming_cache_is_per_context_and_dry_run_never_writes_or_calls` |
| Replay không tính chi phí mới | `test_replayed_provider_tokens_are_recorded_without_new_spend` |
| Lỗi JSON vẫn ghi chi phí | `test_failed_session_json_decode_bills_usage_retained_on_session` |
| Hai request cùng lượt không tạo hai artifact | `test_same_client_turn_runs_one_model_sequence_and_artifact_then_replays_final_to_both`; ca đối chứng `test_mutation_bypassing_public_guard_duplicates_model_and_artifact_work` |
| Nguồn ánh xạ về offset raw chính xác | `test_source_registry_maps_normalized_quote_back_to_raw_absolute_offsets`, `test_source_registry_quote_starting_with_combining_mark_excludes_preceding_newline` |
| Khâu tên không đổi đồ thị học | `test_deterministic_naming_changes_only_presentation_and_uses_display_names`, `test_invalid_model_naming_falls_back_without_changing_learning_graph` |
| Chạy lại tên mặc định không phát sinh lời gọi mới do đổi tên hàng xóm | `test_repeating_default_naming_reuses_original_a10_context_without_more_model_calls`; đối chứng `test_explicit_named_graph_still_uses_its_changed_neighbor_context` |
| Lineage khâu tên sai dừng trước model | `test_invalid_naming_lineage_stops_before_model_work` (thiếu, bằng 0, hoặc vượt phiên bản hiện tại) |
| Ưu tiên module vẫn giữ nguồn ngoài module | `test_module_promotion_never_filters_later_or_unassigned_chunks` |
| Formula ID trùng vẫn có ảnh đúng từng vị trí | `test_formula_occurrences_do_not_overwrite_same_formula_id`, `test_batch_renderer_keeps_each_occurrence_image_attached_to_its_formula` |
| Cache bài giảng không bị sửa khi đưa vào chat | `test_lecture_label_import_does_not_mutate_cache_and_rewrites_text_with_taken_s1` |
| Quiz công khai không lộ đáp án | `test_public_quiz_hides_all_answers_and_events_then_returns_feedback`, `test_stream_endpoints_use_real_use_cases_and_never_return_quiz_answers` |
| Bộ kiểm mù đọc đúng nguồn của phương án nhiễu | `test_blind_verifier_is_told_to_route_options_to_distractor_anchor_evidence` |
| HTTP chỉ phục vụ localhost và sáu tài liệu phát triển | `test_preview_serves_only_its_page_and_development_documents`, `test_foreign_origin_is_rejected_even_on_localhost` |

Các test ở `tests/unit/application/test_phase_b_*.py`, `tests/unit/domain/test_learning_graph.py`, `tests/unit/infrastructure/test_phase_b_llm.py`, `tests/unit/infrastructure/test_formula_images.py`, `tests/unit/presentation/test_phase_b_preview.py`. Các lỗi hồi quy được tái hiện gồm stream dùng nhầm usage phiên khác, tính tiền lại cho replay, crop công thức gắn nhầm ảnh cuối batch, và đoạn nguồn bắt đầu bằng combining mark.

Đã thử tay trên trình duyệt ở chế độ ngoại tuyến:

| Thao tác | Ảnh |
|---|---|
| Lộ trình mới, tên và mô tả Pha B đã cập nhật | [11 — bản cuối](../tmp/phaseb-preview-evidence/11-final-module-names.jpg) |
| Bài giảng khái niệm thứ nhất | [01](../tmp/phaseb-preview-evidence/01-lecture.jpg) |
| Bài giảng khái niệm thứ hai | [02](../tmp/phaseb-preview-evidence/02-second-concept.jpg) |
| Mở nhãn nguồn, tô câu trích | [03](../tmp/phaseb-preview-evidence/03-source.jpg) |
| Làm quiz và nộp | [04](../tmp/phaseb-preview-evidence/04-quiz-submit.jpg) |
| Hỏi trong tài liệu và câu nối tiếp | [05](../tmp/phaseb-preview-evidence/05-chat-grounded.jpg) |
| Hỏi ngoài tài liệu, bị từ chối | [06](../tmp/phaseb-preview-evidence/06-outside-refusal.jpg) |
| Nhờ trợ lý tạo tài liệu, tải Markdown | [07](../tmp/phaseb-preview-evidence/07-document-created.jpg) |
| Trợ lý tạo quiz, mở đúng lần làm | [08](../tmp/phaseb-preview-evidence/08-assistant-quiz.jpg) |
| Mở doc-6, thiếu câu định nghĩa được báo rõ | [09](../tmp/phaseb-preview-evidence/09-doc6-offline-full.jpg) |

## Giới hạn cần giữ khi nối web

- Kho JSON và single-flight dùng trong một instance/tiến trình. Không dùng nhiều tiến trình cùng ghi một tệp; nhóm web thay adapter lưu trữ khi làm nhiều người dùng.
- Bốn graph cũ không lưu quote cạnh. Trợ lý/bài giảng chỉ hiện đoạn liên quan với nhãn S và cảnh báo, không gán thành bằng chứng Q đã xác nhận.
- Doc-6 thiếu anchor ở cả 28 khái niệm nên quiz điền khuyết không đủ nguồn; không tự suy ra anchor từ chỗ nhắc tên. [Độ phủ quiz ngoại tuyến](pha-b-quiz-2026-10-15.md).
- Đã cắt được 857/858 lần xuất hiện công thức có trong sáu parse; một công thức nhap-mon-ml thiếu PDF gốc cục bộ. Đã xem 60 crop mẫu và kiểm round-trip 562 ref doc-1. [Đồ thị, nguồn, ảnh và truy hồi](pha-b-graph-retrieval-2026-10-15.md).
- Audit ngoại tuyến đã chạy 915 bài giảng, có 912 bản trích nguồn và 3 `no_source`, kiểm 5.687 đoạn trích đúng offset. Số đo này chứng minh đường lùi và nguồn, không chấm chất lượng diễn giải Gemini. [Báo cáo bài giảng](pha-b-lectures-2026-10-15.md).
- Trang hiện tại dùng nội dung minh họa/trích nguồn khi ngoại tuyến; bật Gemini thật cần chế độ và trần chi đã duyệt. Hợp đồng trả trạng thái thất bại có cấu trúc để web xử lý khi thiếu nguồn hoặc nội dung sinh không qua kiểm.

Các thay đổi ngoài phạm vi đang có sẵn trong workspace được giữ nguyên. Chưa commit/stage chung các thay đổi của những phiên khác.
