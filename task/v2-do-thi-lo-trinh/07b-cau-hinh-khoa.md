# 07b — Cấu hình khoá cho lần chạy tập giữ lại (T10)

Sinh bởi `scripts/khoa-cau-hinh/tao_bang.py`. Chủ dự án duyệt bảng này trước bước 2 của vé 07; từ lúc duyệt, mọi thay đổi
là hậu kiểm, báo tách riêng.

## Mã

- commit: `a9fac5c133ae05e7e572e7317ae778156fa15b26` (2026-09-26 docs(v2): kế hoạch lần chạy vé 07 và các việc của người trên tập giữ lại (T13–T)
- cây làm việc: sạch (chỉ tính tệp đã theo dõi)
- chuỗi mặc định: clusters → mentions → provenance → edges (chính + phụ) → validated → teaching (neo C8 v3) → identity → stages (A10 neo sách)

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

## prompt_hash từng stage (mô hình và generation đúng như chuỗi mặc định)

| stage | prompt_hash |
|---|---|
| provenance | `dfa9e8aa8532dbac7f729651f00ff9d7667b3a6741d8b9cd2cfd71ca45a7fa41` |
| edges — pass chính | `2e445aef817af4aca178ccee86ef873a2fa2be7477b40f0d214495b728a14bba` |
| edges — pass phụ | `1b7a9d4e0970076399f69fd8358792a3eedfd008ab0356b1f2813d2af8a7ff26` |
| teaching — neo C8 v3 | `b096f47218b80be1af571e7e4082611e7d105c0e967d3a49a775ea463813ccf3` |
| identity | `8532fbcbb015f9fc9366173c97f4f1dc02168157b42092d5b13f98dbc5398386` |

## Luật cố định trong mã

- neo: 6 câu ứng viên, luật gom `nfkc-latex-dash-name+a3-evidence+symbolic-whole-doc`; generation {'temperature': 0.0, 'max_output_tokens': 2048}
- danh tính: gộp nhóm đã kiểm đủ (`verified-clique-v1`); quyết định người: ['Không chắc', 'Không gộp', 'Là hai nghĩa khác nhau', 'Đồng ý gộp']; generation {'temperature': 0.0, 'max_output_tokens': 1024}
- A10: trọng số chia module {'alpha': 1, 'unit': 2, 'chapter': 4, 'cut': 1, 'floor': 3, 'small': 2}; trần module 8

## Đầu vào đã có của tập giữ lại

| tài liệu | chunks | candidates (A3) | canonical (A4/A5) |
|---|---|---|---|
| xstk-ch3-1 | v2 (`docling:2.114.0`) | v5 | v7 |
| doc-4 | v3 (`docling:2.114.0+pypdfium2`) | v1 | v1 |

Ngưỡng: bảng *Tiêu chí nghiệm thu đã chốt* của spec v2 (Q1–Q10 và Q7b, bản tại commit trên).
