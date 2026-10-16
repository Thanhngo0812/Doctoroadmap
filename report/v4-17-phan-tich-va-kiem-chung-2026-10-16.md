# Vé 17 — Phân tích trước khi cài đặt và sổ kiểm chứng

Ngày: 2026-10-16. Phạm vi cài đặt: 17a–17h. Nguồn chuẩn:
`doc/gop-khau-truoc-a8-spec.md` và tám vé tương ứng trong `task/v4/`.
Vé 17i là nghiệm thu nghiên cứu riêng, có duyệt chi; không dùng kết quả test giả để kết luận chất lượng mô hình thật.

## Dự án hiện tại

`doc2roadmap` là ứng dụng Python 3.12 với các lớp miền, ca sử dụng, hạ tầng và CLI.

- B0/A1 đọc PDF/DOCX thành cây và chunk có phiên bản. Nhãn vai trò A2 có thể là một phiên bản metadata tương thích; `load_role_chunks` kiểm toàn bộ ID, văn bản, vị trí và nguồn trước khi dùng nhãn này.
- A3 trích ứng viên, căn cứ nguyên văn, alias và quan hệ; lưu vector mô tả nháp. A3′ lập chỉ mục truy hồi.
- `Canonicalize` gom tên chính xác, embed tên, dựng đồ thị đề cử, rồi gọi `CanonicalReasoning` phán cụm/cặp cắt và viết/kiểm mô tả. Canonical lưu thành viên, chuyển hướng ID, quan hệ đề xuất, nhật ký và chi phí.
- `BuildLearningGraph` hiện chạy `clusters → mentions → provenance → teaching → identity → main_edges → secondary_edges → validated → concept_labels → stages → module_titles`.
- `AnchorConcepts` hiện chứa cả luật neo và việc đọc/ghi graph/checkpoint. Luật câu ứng viên và kiểm phản hồi đã nằm trong `domain/anchors.py`; không cần viết lại.
- Pass chính A8 hiện chấp nhận `provenance`/`identity`, bật hợp đồng theo định nghĩa khi gặp `identity`. Pass phụ LLM đọc `definition_contract`; pass phụ ML đọc trực tiếp trường neo, trạng thái dạy và chunk định nghĩa.
- A10 dựng dãy học rồi chia module. Pha B đang có thay đổi riêng trong cây làm việc và dùng đồ thị/lộ trình phía sau; cần giữ nguyên các thay đổi đó.
- Bộ chấm A8 xác thực hash danh sách khái niệm và sự có mặt của ID trước khi áp bản đồ danh tính. Đây là chỗ phải đổi thứ tự có kiểm soát ở 17h.

## Hợp đồng cần giữ

1. Vắng công tắc chuỗi nghĩa là `v3`. Không thêm trường mặc định vào config v3; chỉ giữ cùng hành vi là chưa đủ, vì cache băm cả config.
2. `gop` chỉ nhận canonical đầy đủ. Trong chuỗi này, A4 tạo tập node cuối và A5 mang neo/trạng thái dạy; không có bước danh tính phủ lên tập node nữa.
3. Câu ứng viên phải dựng từ chunk nguồn, căn cứ A3, tên/alias khớp chính xác trên toàn văn, ký hiệu và heading; chỉ chọn câu thuộc vùng nội dung. Không dùng dense/provenance để mở vùng tìm.
4. Hai chế độ neo dùng cùng tập ứng viên, dựng trước lời gọi A5. Chế độ riêng từng khái niệm là đối chứng; chế độ gom vào A5 chỉ tiết kiệm lời gọi.
5. `mentioned_only`/`unchecked` khi không có ứng viên không phát sinh lời gọi neo. Phán hỏng sau lượt sửa giữ `uncertain`; kiến thức nền phải có xác minh độc lập.
6. Trường ghi lên node giữ đúng dạng C8. Chunk neo chỉ được thêm vào `defining_chunk_ids`, giữ bản trước ở `defining_chunk_ids_source`.
7. Vector chỉ đề cử. Phán mô hình, xác minh và ràng buộc người duyệt mới quyết định gộp.
8. ID dựa trên ứng viên có vị trí sớm nhất theo ADR 0005; ID mất phải có chuyển hướng. Chuyển hướng không được tạo vòng hay cấp lại ID cũ cho khái niệm khác.
9. Quy ID vàng trước khi từ chối ID lạ; sau đó vẫn áp identity map v3. Không sửa tệp vàng và không thay hash để bỏ qua xác thực tập gán cũ.
10. Chi phí mô hình/embedding đi qua `SpendGuard` ở chuỗi mới. Dry-run chỉ đọc và lập dự toán; phần chưa biết phải ghi chưa biết. Thời gian đo nằm trong manifest, không làm thay đổi payload ngữ nghĩa/cache.

## Phân chia và điều kiện chuyển bước

| Vé | Phạm vi chính | Điều kiện kiểm chứng |
|---|---|---|
| 17a | Lõi neo dùng lại; stage teaching giữ phần artifact/cache/checkpoint | Payload phát lại cùng băm; cache cũ 0 lời gọi; các nhánh lõi có test trực tiếp |
| 17h | Hàm miền quy ID vàng, nối vào scorer có tùy chọn | Bắc cầu, vòng, cạnh tự nối, đích, ID không quy được, băm tệp vàng giữ nguyên |
| 17b | Công tắc, neo riêng trong canonical, chốt chi/dry-run | Fixture thật với mô hình giả; cache v3 giữ nguyên; candidate/quote sai bị bác |
| 17c | Bộ điều phối và các hợp đồng A8/A10 của chuỗi mới | Đúng thứ tự; không ba stage cũ; cả ML/LLM; thiếu identity map vẫn chạy |
| 17d | Neo nằm trong lời gọi mô tả/kiểm A5 | Không lời neo riêng khi hợp lệ; lỗi chỉ hỏi lại đúng khái niệm |
| 17e | Năm nguồn đề cử mới và tiêu chí cùng ngoại diên | Không tự gộp theo cosine; không embed mô tả thêm; thống kê khớp nhật ký |
| 17f | Gom lô phán sửa | Lỗi chỉ hỏi lại mục hỏng; lô 1 và lô lớn cho cùng node với cùng phán |
| 17g | Xác minh gộp khác tên, quyết định người, chuyển hướng ID | Xác minh mù; người thắng cả hai chiều; tệp sai tài liệu bị từ chối |

Thứ tự thực hiện: `17a ∥ 17h → 17b → 17c ∥ 17d ∥ 17e → 17f và 17g sau 17e`.
Các nhánh dùng chung workspace nên cần giao quyền sửa file rõ và kiểm lại sau tích hợp.

## Điểm lệch giữa mô tả và code cần lưu ý

- Spec gọi bộ chia cụm A4 là Leiden, nhưng `domain/nomination.py` đang dùng NetworkX Louvain. Các vé yêu cầu giữ cách chia hiện có; không tự thay thuật toán trong nhóm vé này. A6/A7 mới dùng Leiden thật.
- Một số vàng được gán theo đồ thị provenance, khác phạm vi canonical thô. Chuyển ID cần xác thực đúng đầu vào gán cũ, không chỉ có bảng chuyển hướng.
- `build_clusters` dựng payload mới thay vì chép toàn bộ canonical; khai báo neo và chuỗi phải được truyền qua điểm này. Chỉ thêm marker vào canonical sẽ chưa đủ cho A8.
- Cây làm việc đã có nhiều thay đổi trước lượt này. Không dùng reset/checkout để tạo nền sạch và không gộp các thay đổi Pha B/A1/D-01 vào phạm vi vé 17.

## Kết quả kiểm chứng

Lượt test nền đầu gặp ACL của thư mục tạm pytest trên Windows, cả khi chạy ngoài sandbox;
đã chuyển sang một thư mục test mới trong `tmp/` và tắt cache pytest cho lượt kiểm tra này.

### 17h

- 99 test miền, bộ chấm, vàng và kiến trúc đã qua; 3 test CLI mới đã qua.
- 15 biến thể cố ý bỏ luật bảo vệ bị assertion bắt trong tiến trình con, không sửa source chia sẻ: quy bắc cầu, quy đích, ID chỉ có ở đích, bỏ cạnh tự nối, vòng chuyển hướng, từ chối ID không quy được, hash vàng gốc, phiên bản canonical gốc, tài liệu của graph gán, tài liệu của manifest, manifest thiếu, lineage không xác định được canonical, vòng lineage, kho artifact bắt buộc và tùy chọn graph gán cần bật quy ID.
- Guard CLI `--gold-graph` có test `test_gold_source_graph_requires_remapping_and_reaches_scorer`; bỏ guard trong bộ nhớ làm test này đỏ (CLI trả 0 thay vì 2).
- Test `test_v3_identity_mapping_runs_after_canonical_redirects_and_maps_targets` chạy cả hai scorer và kiểm thứ tự chuyển hướng rồi danh tính v3.
- Giao diện: `a8-score --remap-gold-ids [--gold-graph <graph-gán-gốc>]`; `a8-roadmap-score --remap-gold-ids`.

### Mẫu v3 trước thay đổi

- Canonical fixture `baocao-canhan`: config SHA-256 `67f96297f5d209ad030123ad8057b26e04f6498bd8ae384f29ca334e0aa740a5`, payload SHA-256 `ea9dcfe574b523f800f2583a0f778f1a30049631a8c632554b8d4159ae76fd34`, 52 lời gọi giả.
- Teaching trên cùng fixture: config SHA-256 `5f6b4ccd530c4c1467db0ca6621ae2757e193c3e4310aaf48c1e83a681405c92`, payload SHA-256 `5170440ad3fb1060bda178af373041265cd0f7c38c7e0b6959dd8c5d6ec427ca`, 46 lời gọi phát lại.

### 17a và hồi quy sau đợt đầu

- 63 test tập trung đã qua: gọi lõi trực tiếp, nhánh neo, miền, stage, phát lại fixture thật, cache, lập dự toán và đo stage.
- Bỏ kiểm phản hồi trong bộ nhớ làm các test mã neo bịa, câu trích bịa và `confidence` đỏ; bỏ hạ nhãn kiến thức nền làm test xác minh sai/hỏng đỏ; bỏ quét tên dự phòng làm test không tìm được câu dạy đỏ; ép gọi cho node không ứng viên tạo lời gọi thừa và bị test bắt.
- Lượt toàn dự án (chưa tính test 17b đang đỏ trước cài): 1.400 qua, 3 lỗi socket localhost do sandbox. Chạy lại toàn bộ `test_phase_b_preview.py` ngoài sandbox: 4 qua. Không chỉnh code preview vì đây là hạn chế môi trường chạy.
- Bắt được và đã sửa lỗi trong bước tách A4/A5 của 17b: cộng metadata ngôn ngữ dạng chữ vào `Counter`. Băm v3 đã khớp sau sửa.

### 17b, 17d và 17f

- 17b: 60 test tập trung đã qua, sau đó nhóm kết hợp b/f/e/CLI 31 test qua. Băm canonical v3 trùng mẫu trước cài. Sáu biến thể bỏ guard bị bắt: chế độ đầy đủ, chốt chi, dry-run, cấm lấy chunk chỉ gần nghĩa, giữ băm v3 và giữ chunk định nghĩa cũ.
- 17d: 76 test tập trung đã qua. Chế độ `a5` không có lời neo riêng khi mọi phần hợp lệ; phần neo hỏng chỉ gọi lại đúng khái niệm; giữ neo hợp lệ khi viết lại singleton hoặc sửa mô tả. Biến thể bỏ kiểm neo, sửa lại cả lô, thu neo sau kiểm mô tả và đính ứng viên rỗng đều làm assertion đỏ.
- Lời A5 kết hợp được tính đúng một lần vào phần `anchor` của chi phí; nhật ký có `origin_stage=describe|check`. Các bộ đếm riêng là `anchor_in_a5_calls`, `anchor_concepts_in_batch`, `anchor_concepts_fallback`.
- 17f: 13 test riêng qua, gồm thiếu/lặp item ID, envelope hỏng, phản hồi tự mâu thuẫn và quan hệ đề xuất theo mục. Bốn biến thể bỏ kiểm từng mục, gọi lại cả lô, đếm chi phí hai lần và bỏ cỡ lô khỏi cache đều bị bắt.

### 17e và 17g

- Nhóm kiểm 17e/17g: 29 test qua; sau rà soát thêm 5 test cache/duyệt qua. Test mới còn kiểm việc dùng chung một `CanonicalReasoning` giữa hai chuỗi không đổi prompt/cache v3.
- `additional_nominations` dùng lại chuẩn hóa, viết tắt, tiền tố và top-k của danh tính; vector mô tả lấy từ A3, gộp theo nhóm, không embed thêm. Thiếu vector thành viên thì nhóm đó không có nguồn đề cử mô tả.
- Prompt `a4/partition-gop.txt` dùng tiêu chí cùng định nghĩa/ngoại diên; prompt v3 không thay. `nomination_pair` ghi nguồn, kết quả cuối, quan hệ và xác minh; số đếm theo nguồn đối chiếu được với nhật ký.
- Xác minh độc lập phủ mọi cặp khác tên trong thành phần gộp bắc cầu. Chỉ `dong_nhat` được giữ; phản hồi hỏng hoặc quan hệ khác tạo ràng buộc khác.
- Người duyệt thắng mô hình, gồm cả mâu thuẫn bắc cầu. ID cũ được kiểm chuyển hướng rồi chiếu về thành viên A3 của phía đã duyệt nếu còn, để không mất khả năng bác gộp khi hai ID cũ đã chuyển về cùng node.
- Rà soát độc lập bắt ba lỗi và đã sửa: thiếu xuất duyệt cho gộp do người ép; cache cũ cấp lại ID đã nghỉ; ID thay thế thay đổi do một ID nghỉ không liên quan. `test_canonical_retired_cache.py` đã được thấy đỏ trên hai lỗi sau trước khi sửa.
- ID thay thế chỉ dùng khi ID theo neo đã nghỉ: băm neo và số lần nghỉ, không băm toàn bộ lịch sử. Cache có thêm tập ID nghỉ khi artifact cũ xung đột lịch sử; chạy lại sau sửa vẫn tái dùng, không gọi mô hình/embedding.
- Mười ba biến thể 17e/g đã bị assertion bắt: ngưỡng cosine, vector thiếu, bỏ quyền phán của mô hình, bỏ xác minh, hỏi lại cặp chung alias, lộ lý do phán trước, bỏ quyết định người, cấp lại ID nghỉ, cache lịch sử, bỏ tệp duyệt khỏi khóa, vòng ID duyệt, mâu thuẫn người và sai tài liệu.

### 17c và kiểm toàn bộ

- 111 test graph/CLI/canonical hồi quy qua. 25 test chuỗi gộp qua, gồm canonical → A10 → cả hai bộ chấm trên fixture thật, với mô hình giả; pass phụ `ml` và `llm` đều chạy.
- Cả tám artifact graph giữ trường neo và canonical đã ghim, không có stage provenance/teaching/identity, không cần identity map. Chạy lại không tăng số lời gọi model, embedding hay bộ chấm ML.
- Nhóm 17c kết hợp cuối: 66 test qua; tám biến thể bỏ guard về chọn chuỗi, stop, review, thứ tự stage, trộn artifact, kiểu cạnh, khai báo neo và dry-run đều bị bắt.
- Lượt toàn bộ không tích hợp cuối: **1.510 qua, 1 lỗi** (thiếu năm trường mới trong `.env.example`). Đã bổ sung đủ cấu hình mẫu; chạy lại nhóm cấu hình/CLI/cache v3: **11 qua**, gồm đúng test đã lỗi. Không thay mã sản phẩm sau lượt này.
- Lượt tích hợp Docling ở chế độ offline: **8 qua** (model đã có trên máy, không tải mới).
- Như vậy cả **1.519 test hiện có đều đã được chạy và qua** qua các lượt trên; không có test bị bỏ. Hai cảnh báo SWIG và cảnh báo deprecated của RapidOCR là cảnh báo phụ thuộc sẵn có. `git diff --check` qua.

## Assertion tiêu biểu cho từng hợp đồng

Các tên dưới đây chạy được bằng `python -m pytest <file>::<tên>`; các ca tham số hóa chạy tất cả nhánh của cùng tên.

| Hợp đồng | File test | Assertion có tên |
|---|---|---|
| Payload/config/checkpoint teaching giữ nguyên | `tests/unit/application/test_anchor_core_regression.py` | `test_real_document_teaching_payload_and_cache_key_match_before_extraction` |
| Không ứng viên thì không gọi mô hình | `tests/unit/application/test_anchor_core.py` | `test_core_no_candidates_does_not_call_model_and_preserves_media` |
| Neo hỏng giữ uncertain, prior cần xác nhận | `tests/unit/application/test_anchor_core.py` | `test_core_invalid_verdict_is_retried_then_kept_uncertain`, `test_core_prior_knowledge_requires_independent_valid_confirmation` |
| Cache canonical v3, vùng tìm, nhãn đúng phiên bản | `tests/unit/application/test_canonical_gop.py` | `test_v3_fixture_config_payload_and_existing_cache_are_unchanged`, `test_gop_candidates_scan_exact_names_without_dense_or_provenance`, `test_gop_reads_roles_pinned_to_a3_and_no_candidates_make_no_anchor_calls` |
| Chốt chi và dry-run | `tests/unit/presentation/test_canonical_gop_cli.py` | `test_gop_composition_blocks_embedding_and_every_model_before_first_call`, `test_gop_cli_dry_run_lists_phases_and_never_executes` |
| Chuỗi và hợp đồng canonical ở A8 | `tests/unit/application/test_gop_graph.py` | `test_roadmap_infers_canonical_chain_and_passes_exact_artifacts`, `test_main_contract_follows_pinned_canonical_declaration_and_preserves_v3` |
| Đầu cuối ML/LLM và hai bộ chấm không identity map | `tests/unit/application/test_gop_graph.py` | `test_real_fixture_canonical_gop_runs_through_roadmap_and_scorers_without_identity_map` |
| Neo A5 độc lập mô tả, cùng tập ứng viên | `tests/unit/application/test_canonical_a5_anchors.py` | `test_one_invalid_anchor_is_retried_alone_and_kept_without_repeating_description`, `test_valid_anchor_survives_rejected_singleton_draft_and_description_retry`, `test_a5_and_single_use_identical_candidates_and_write_identical_anchor_fields` |
| Vector chỉ đề cử; không thêm embedding | `tests/unit/application/test_canonical_gop_nominations.py` | `test_real_fixture_uses_saved_vectors_without_merging_or_embedding_descriptions` |
| Nguồn mới và thiếu vector | `tests/unit/domain/test_canonical_nominations.py` | `test_reuses_identity_name_sources`, `test_same_a3_sentence_and_description_are_separate_nomination_sources`, `test_description_neighbors_respect_top_k_and_missing_member_vectors` |
| Phán sửa chỉ hỏi lại mục hỏng | `tests/unit/application/test_canonical_repairs.py` | `test_only_bad_batch_item_retries_and_invalid_pair_stays_separate`, `test_malformed_batch_ids_retry_only_affected_items` |
| Xác minh mù và người duyệt thắng mô hình | `tests/unit/application/test_canonical_merge_review.py` | `test_different_name_merge_requires_blind_independent_confirmation`, `test_human_overrides_model_both_directions_with_redirected_review_ids`, `test_human_can_reject_an_exported_merge_after_its_ids_have_redirected` |
| Không cấp lại ID nghỉ, cache không phục hồi ID | `tests/unit/application/test_canonical_retired_cache.py` | `test_old_gop_cache_cannot_restore_an_id_retired_by_a_later_review`, `test_reserved_id_stays_stable_when_an_unrelated_id_is_retired` |
| Quy vàng đúng thứ tự, giữ tệp, từ chối thiếu ID | `tests/unit/application/test_a8_gold_redirects.py` | `test_order_scorer_maps_ids_before_unknown_rejection_and_preserves_the_gold_file`, `test_v3_identity_mapping_runs_after_canonical_redirects_and_maps_targets`, `test_remapping_refuses_and_lists_all_unresolved_concepts_including_target_only` |

## Điểm dừng bàn giao

Vé 17i chưa chạy: không có phán chất lượng trên sáu tài liệu phát triển bằng mô hình thật, không có chi phí/phút đo thực của chuỗi mới, chưa dựng ADR 0016 hay đổi mặc định. Các phần đó cần dry-run và duyệt chi theo chính vé 17i. Không dùng test giả để thay kết quả nghiệm thu nghiên cứu.
