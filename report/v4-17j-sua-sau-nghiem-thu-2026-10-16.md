# Vé 17j — Vá sau lượt nghiệm thu đầu

Ngày: 2026-10-16. Nguồn: `task/v4/17j-sua-sau-nghiem-thu-dau.md` và
`doc/gop-khau-truoc-a8-spec.md`, mục 3.2, 3.3, 4. Không phát sinh lời gọi mô hình trả phí.

## Thay đổi

- A5 gộp đọc trạng thái tái dùng bằng `row.get("reused", False)`. Nhật ký lời gọi hỏng
  vẫn giữ khuôn cũ của `run_model_jobs`; phần mô tả dùng `draft_fallback_invalid`.
  Neo hỏng được hỏi riêng; nếu vẫn hỏng sau hai lần thì giữ node với `uncertain`.
  Neo hợp lệ đã nhận vẫn độc lập với lỗi mô tả, theo hợp đồng 17d.
- Mặc định phán sửa là một cặp mỗi lời gọi, trong cả `Settings`, `CanonicalReasoning`
  và `.env.example`. Cỡ lô lớn hơn 1 vẫn dùng được và nằm trong khóa cache của `gop`.
- `gop` kiểm đúng 14 nhãn đồng nhất sau chuẩn hóa chữ/khoảng trắng, tại lời phán cụm,
  phán sửa riêng và từng mục trong lô. `same_category` và các nhãn chỉ chứa chuỗi con
  không bị coi là đồng nhất. Hai nhóm đã gộp có thể ghi quan hệ đồng nhất mà không bị R1 bác nhầm.
- Mã luật trong config `gop` là `consistency-gop-identity-labels-v2`. V3 giữ
  `consistency-v1`, tập năm nhãn cũ, prompt và khóa cache cũ; `v3` vẫn mặc định.

## Bằng chứng hồi quy

Trước sửa, chạy hai file test mới cho **29 lỗi, 1 qua**. Cả bốn ca A5 gộp đều dừng
đúng tại `KeyError: 'reused'`, bao phủ `describe`/`check` và neo dự phòng đúng/hỏng.
Sau sửa, **90 test tập trung qua**, gồm hai file mới, A5, phán sửa, canonical `gop`,
luật partition và thư viện prompt.

| Hợp đồng | File test | Assertion chạy được |
|---|---|---|
| A5 gộp hỏng vẫn hoàn tất stage; neo được hỏi riêng hoặc giữ uncertain | `tests/unit/application/test_canonical_patch_17j.py` | `test_failed_combined_a5_call_falls_back_without_reused_key_error` |
| Mặc định một cặp; vẫn gom khi đặt cỡ khác; cache đổi | Cùng file trên | `test_default_gop_repairs_are_single_and_explicit_batching_still_changes_cache` |
| Synonym phải phán lại; same_category giữ nguyên, ở cả ba đường gọi | Cùng file trên | `test_gop_identity_relation_retries_only_exact_identity_labels` |
| Đủ 14 nhãn, có chuẩn hóa | `tests/unit/domain/test_gop_identity_labels.py` | `test_gop_rejects_each_normalized_identity_label_between_separate_nodes` |
| Không so chuỗi con | Cùng file trên | `test_gop_does_not_match_identity_label_substrings` |
| Nhãn mới chỉ áp dụng cho gop | Cùng file trên | `test_v3_keeps_its_original_identity_label_set` |
| Băm và cache canonical v3 giữ nguyên | `tests/unit/application/test_canonical_gop.py` | `test_v3_fixture_config_payload_and_existing_cache_are_unchanged` |

Phép bỏ luật trong bộ nhớ (không sửa source chia sẻ):

- Đưa tập nhãn `gop` về năm nhãn cũ: **12 assertion đỏ**, gồm chín nhãn bổ sung và
  ba đường gọi `merge`/`repair`/`repair_batch` không còn hỏi lại `synonym`.
- Đổi so nhãn chính xác thành so chuỗi con: **3 assertion đỏ** với `synonym_candidate`,
  `non_alias_of`, `translation_method`; `same_category` vẫn qua.
- Áp tập nhãn mở rộng vào v3: **1 assertion đỏ** vì v3 bác `synonym` trái hành vi cũ.
- Guard khóa `reused` và mặc định cỡ lô đã đỏ trực tiếp trước sửa, không chỉ kiểm đường thành công.

Mẫu v3 vẫn khớp config SHA-256
`67f96297f5d209ad030123ad8057b26e04f6498bd8ae384f29ca334e0aa740a5`, payload SHA-256
`ea9dcfe574b523f800f2583a0f778f1a30049631a8c632554b8d4159ae76fd34` và chạy lại tái dùng cache.

## Kiểm toàn bộ và phạm vi commit

- Toàn bộ **1.549 test qua**, không bỏ test: 277,11 giây, gồm tám test tích hợp
  Docling với model sẵn có ở chế độ offline. Bảy cảnh báo là deprecation SWIG/RapidOCR.
  Lệnh: `.venv/Scripts/python.exe -m pytest -p no:cacheprovider --basetemp=tmp/pytest-17j-full-01 --junitxml=tmp/pytest-17j-full-01.xml`,
  với `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`; chạy ngoài sandbox để test preview mở localhost.
- Kiểm phạm vi commit phát hiện test đầu cuối 17c dùng `NameModulesB` của Pha B.
  Đã đổi sang `NameModules` hiện có và mô hình giả. Sau thay đổi này, **40 test graph,
  composition và CLI qua** trong 33,62 giây khi nạp ba bản nguồn chỉ chứa hunk vé 17.
  Assertion cuối tiến trình xác nhận không module `phase_b` nào được nạp.
- `git diff --check` và kiểm áp patch chọn hunk vào index đều qua.

Ba file dùng chung với Pha B (`composition.py`, CLI `main.py`, `build_roadmap.py`)
được chọn riêng các hunk vé 17 trong index; file làm việc được giữ nguyên.
Commit bao gồm phần cài đặt/test/bàn giao 17a–17h và bản vá 17j. Script chấm và
kết quả nghiên cứu 17i đã được commit riêng trong lúc thực hiện bản vá này.
Không dùng kết quả test giả để kết luận nghiệm thu nghiên cứu 17i đã hoàn thành.
Các thay đổi Pha B, A1, D-01/D-02 và tài liệu ngoài nhóm vé 17 không thuộc commit này.
