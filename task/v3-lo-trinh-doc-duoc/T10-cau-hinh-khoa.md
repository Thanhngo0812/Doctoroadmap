# T10 — Cấu hình khoá cho lần chạy tập giữ lại 07 v2 (chuỗi v3)

Sinh bởi `scripts/khoa-cau-hinh/tao_bang.py`.

**Chủ dự án duyệt 2026-10-03; trần chi 50 USD cho cả lượt.**
Chủ dự án duyệt bảng này trước bước chạy của [giao thức](T10-07v2-giao-thuc-tap-giu-lai.md); từ lúc duyệt, mọi thay đổi là
hậu kiểm, báo tách riêng, không thay kết quả tập giữ lại.

## Mã

- commit: `2f03781dea292b49867113917edfff4b3338f437` (2026-10-03 docs(v3): bậc 1 ingest lại cây tham chiếu đúng bộ đọc PDF và thang tiêu đề của )
- cây làm việc: sạch ở mã chạy (`src/`, `scripts/`, `pyproject.toml`, `uv.lock`); tệp đã theo dõi khác chưa commit, không ảnh hưởng chạy: `.gitignore`
- chuỗi: vai trò vùng (A2, `label-roles`) → clusters → mentions → provenance → teaching (neo C8 v3, vé 05/05b) → identity (vé 10b) → edges chính → edges phụ (hợp đồng cửa sổ định nghĩa, vé 12) → validated (A9) → concept_labels (vé 11/11b) → stages (A10 neo sách, vé 07/08/09c/18/20/21) → module_titles (vé 09–09d)

## Mô hình và tham số (thiết lập không bí mật)

| thiết lập | giá trị |
|---|---|
| `extraction_model_id` | `gemini-3.1-flash-lite` |
| `merge_model_id` | `gemini-3.1-flash-lite` |
| `description_model_id` | `gemini-3.1-flash-lite` |
| `embedding_model_id` | `gemini-embedding-001` |
| `embedding_dimensions` | `768` |
| `roadmap_model_id` | `gemini-3.1-flash-lite` |
| `topic_neighbors` | `3` |
| `topic_edge_quantile` | `0.5` |
| `topic_resolution` | `None` |
| `topic_seed` | `42` |
| `topic_cluster_cap` | `12` |
| `mention_dense_top_k` | `3` |
| `mention_dense_min_z` | `0.0` |
| `mention_pair_cluster_top_k` | `3` |
| `roadmap_single_session_limit` | `20` |
| `roadmap_stage_cap` | `8` |
| `extraction_max_output_tokens` | `8192` |
| `a8_definition_before` | `4` |
| `a8_definition_after` | `2` |

Không thuộc phương pháp (không đổi kết quả hay khoá cache), ghi để kiểm toán: `llm_transport=vertex`, `vertex_location=global`, `vertex_concurrency=2`, `roadmap_concurrency=4`, `llm_max_in_flight=100`, `llm_tpm_budget=1600000`, `llm_rpm_budget=None`.

## prompt_hash từng stage (mô hình và generation đúng như chuỗi mặc định)

| stage | prompt_hash | doc-1 · doc-6 |
|---|---|---|
| vai trò vùng (A2) | `ee94d7347aa2ea564cce772e0c34384792e95740d6cfb06a9d5e650bc854e7fb` | khớp · khớp |
| provenance (A7) | `dfa9e8aa8532dbac7f729651f00ff9d7667b3a6741d8b9cd2cfd71ca45a7fa41` | khớp · khớp |
| teaching — neo C8 v3 | `17b755a2b3c6ad75bd3b315b8e2b493ed5843575a1df9864fd3852a0fdc64e04` | khớp · khớp |
| teaching — kiểm kiến thức nền | `056d64c7263119faeb4f706bee25ccc29a7bd8ced1fbab99aadf890f160be7c8` | khớp · khớp |
| identity — lượt 1 | `8532fbcbb015f9fc9366173c97f4f1dc02168157b42092d5b13f98dbc5398386` | khớp · khớp |
| identity — lượt xác minh | `8e47b51c577c5887079605957eacff8fcc050e6d3afd17f5f5f6e9fb89fe7934` | khớp · khớp |
| edges — pass chính | `8d7a922297030a0530ffe46693e221d2596d068d593cf9b43abcc7d38f78fe4b` | khớp · khớp |
| edges — pass phụ | `2f1b2f2d54d1a1e9e955f283ef099dd1177658c027b3b9150c7418212dace8d2` | khớp · khớp |
| concept_labels | `8f88d1cd5345b5767c511dbb633683ce9723ca4ea8219985aa97e21fd48453c8` | khớp · khớp |
| module_titles | `0c36cd6956f5d45edbbb249f0aa0618be8d537c156fc35f40d71a862f2678aa1` | khớp · khớp |

Cột cuối so với `prompt_hash` trong manifest của lượt nghiệm thu vé 12 (`artifacts/v3-r12-final-evaluation` và chuỗi trước A8 ở kho chính). Mọi stage khớp.

## Luật cố định trong mã

- neo: 6 câu ứng viên; generation {'temperature': 0.0, 'max_output_tokens': 2048}
- danh tính: gộp nhóm đã kiểm đủ; quyết định người: ['Không chắc', 'Không gộp', 'Là hai nghĩa khác nhau', 'Đồng ý gộp']; generation {'temperature': 0.0, 'max_output_tokens': 1024}
- A8: cửa sổ định nghĩa = câu neo, 4 câu trước, 2 câu sau, trong cùng đoạn của chunk neo; chỉ `can_de_hieu` là cạnh cứng
- A10: trọng số chia module {'alpha': 1, 'unit': 2, 'chapter': 4, 'cut': 1, 'floor': 3, 'small': 2}; trần module 8
- trần token đầu ra thật của adapter: provenance 8192, neo 2048, danh tính 1024, pass chính 8192, pass phụ 8192, tên khái niệm 512, tên module 128

## Đầu vào đã có của tập giữ lại (dùng lại — bộ vàng gắn với canonical này)

Chunks gắn với A3 là version mà candidates trỏ tới, không phải version mới nhất. Ingest lại cây tham chiếu ở bậc 1 tạo version
mới hơn chỉ dùng để chuyển vai trò và tên mục.

| tài liệu | chunks gắn A3 | chunks mới nhất | candidates (A3) | canonical (A4/A5) | cờ `ingest` bậc 1 |
|---|---|---|---|---|---|
| xstk-ch3-1 | v2 (`docling:2.114.0`) | v2 | v5 | v7 | `mặc định` |
| doc-4 | v3 (`docling:2.114.0+pypdfium2`) | v3 | v1 | v1 | `--pdf-backend pypdfium2 --heading-scheme vn-textbook` |

Cờ `ingest` bậc 1 lấy từ manifest chunks gắn A3 (bộ đọc PDF, thang tiêu đề), không chọn theo kết quả. Ingest lại khác thiết lập này thì văn bản không khớp khi chuyển vai trò; doc-4 tách rời âm tiết với bộ đọc mặc định.

## Tệp nhãn của tập giữ lại (chỉ băm, không mở)

| tệp | SHA-256 |
|---|---|
| `xstk-ch3-1-chuong-10-13-A1-output.xlsx` | `7487bbd1f214db1aedb4355fd38ed4f89a0bc9f15cc436a8f105d5b13a31ff45` |
| `xstk-ch3-1-chuong-10-13-A1.xlsx` | `fd62bb684c4e62bd61fef72320be19197766c7b9500652eb7ba53555132f2c11` |
| `xstk-ch3-1-chuong-10-13-A2-output.xlsx` | `83edf48f2717fd68842215301e7f0d102f135e69432496d30e8f6f42b9365ab5` |
| `xstk-ch3-1-chuong-10-13-A2.xlsx` | `0eca4cbc06c6730ae47c4a23df2356bb4fde7e89ff511c0aa41f329b370e7036` |
| `xstk-ch3-1-chuong-10-13-hoi-y-output.xlsx` | `0707f4b7a95330c1e7f05dd5d44d76ba5e5f4a9bf3a0c04745b163846425f134` |
| `xstk-ch3-1-chuong-10-13-hoi-y.xlsx` | `b2ec06f30adc2232695de1fc44c75941767a2837321a999b2bb3ba3b8be79303` |
| `doc-4-chuong-8-A1-output.xlsx` | `a9386e9e090dadd19cd716b3c2cb7f2307a5125337476b22a878e9e934e557da` |
| `doc-4-chuong-8-A1.json` | `2a9c5a88e11db309226b80988b9453ac17fbf839240dd9637992ad732bd9f3dd` |
| `doc-4-chuong-8-A1.xlsx` | `b8e336ec8cb19799467cd282262ed2cc082dae66d94cd9ad8b6ff3e548f0c603` |
| `doc-4-chuong-8-A2-output.xlsx` | `d5696bcbc88f5d5ce921b7bdfd60bc47c8f4c632b34855a50afc5adabcb34048` |
| `doc-4-chuong-8-A2.json` | `c7bae000ede9cfac2b08e28010f776a62fc5beeecf643e5edb6dd59567e0c0e5` |
| `doc-4-chuong-8-A2.xlsx` | `7280ae49deab5214e9a5936dcd0cfa1d3473030f4ae91145faf24d9abbb6192f` |
| `doc-4-chuong-8-hoi-y-output.xlsx` | `bbb995017f297ed02bff2b3a7cd119e8aec9bf8f657bdbef650930ee5c3f9baa` |
| `doc-4-chuong-8-hoi-y.xlsx` | `27b51496cdc1838fde36dcf93cef413a7037348bf6af87047877d39103afdaa9` |
| `doc-4-chuong-8-vang.json` | `df0c6cb9d42fffc4007f4e18c1922f1898ea932644fda4d5a483bfb05f8bc9ed` |
| `liet-ke-mu-giu-lai.md` (T13) | `40893176582ea921054632b0038fb08c232248c4068de8c11a794bf55c90a49f` |
