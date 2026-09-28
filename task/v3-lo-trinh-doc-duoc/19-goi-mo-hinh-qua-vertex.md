# 19 — Gọi mô hình qua Vertex AI (dùng credit Google Cloud)

**Nguồn chân lý:** vé này (hạ tầng, không đổi luật của spec v3) · **Ai:** nhân viên · **Phụ thuộc:** — ·
**Chi phí mô hình:** thử nghiệm vài lời gọi (< 0,01 USD); tiền chạy thật sau này trừ vào credit Google Cloud của chủ dự án

**Trạng thái:** chờ giao. **Chủ dự án quyết:** chi từ credit Vertex có tính vào trần 50 USD của dự án hay có trần riêng.

## Vì sao
Chủ dự án có 300 USD credit Google Cloud trên project `gen-lang-client-0947038321`. Thử 2026-09-28 (`scripts/thu-vertex/goi_thu_vertex.py`
và một lời gọi REST): Vertex AI chạy được `gemini-3.1-flash-lite` ở vùng `global`, temperature 0, JSON theo schema đúng. Endpoint REST
của Vertex nhận **đúng thân yêu cầu** mà bộ gọi hiện tại gửi (`systemInstruction`, `contents`, `generationConfig` với
`responseJsonSchema`) và trả cùng định dạng (`candidates`, `usageMetadata`). Vì vậy chỉ cần đổi URL và cách xác thực.

## Việc cần làm
- Thêm lựa chọn đường gọi cho các lời gọi mô hình ngôn ngữ (không đụng embedding):
  - `llm_transport` ∈ `developer_api` (mặc định, như hiện nay) · `vertex`; thêm `vertex_project`, `vertex_location` (mặc định `global`) trong
    `Settings`;
  - `vertex`: URL `https://aiplatform.googleapis.com/v1/projects/{project}/locations/{location}/publishers/google/models/{model}:generateContent`,
    header `Authorization: Bearer <token>` và `x-goog-user-project`; token lấy qua `google-auth` (Application Default Credentials hoặc tệp
    khoá service account ngoài repo), tự làm mới khi hết hạn; giữ nguyên thân yêu cầu, phân tích phản hồi và luật thử lại (408, 429, 5xx).
- **Không làm mất cache.** `model_id` giữ nguyên; `identifier` của bộ gọi mô tả hợp đồng yêu cầu (giữ
  `gemini-generate-content-rest:v1beta`), còn đường gọi (`developer_api`/`vertex`) chỉ ghi vào manifest và sổ chi, không vào khoá cache.
  Lý do: cùng mô hình, cùng prompt, cùng cấu hình sinh; đổi đường gọi không phải đổi phương pháp. Kiểm bằng `--dry-run` sáu tài liệu
  trước/sau khi bật `vertex`: không stage nào chuyển sang "sẽ chạy".
- **Giá:** đối chiếu trang giá chính thức của Vertex AI cho `gemini-3.1-flash-lite`, ghi nguồn và ngày kiểm. Sổ chi (`SpendGuard`, các
  bộ đếm chi của công cụ thử) tính theo giá của đường gọi đang dùng. Không đưa giá riêng của Vertex vào khoá cache (các config hiện có
  trường `pricing_usd_per_million` giữ nguyên giá Developer API như dữ liệu lịch sử).
- **Embedding giữ Developer API.** Đổi nguồn embedding làm đổi `embedding_adapter` trong khoá cache của A6 và kéo chạy lại A6–A8; để vé
  khác nếu cần.
- Phụ thuộc: thêm `google-auth` (ghim phiên bản) vào `pyproject.toml`; không cần `google-genai` cho luồng chính (script thử vẫn dùng nó,
  cài riêng bằng `uv pip install google-genai`).
- Bảo mật: không ghi token hay đường dẫn khoá vào log; tệp khoá luôn ở ngoài repo.

## Tệp liên quan
`infrastructure/llm/gemini.py`, `config.py`, `composition.py`, `pyproject.toml`, `CONTEXT.md`/`doc/spec-addendum.md` (ghi đường gọi mới).

## Nghiệm thu
- Test không mạng (token và HTTP giả): dựng đúng URL và header cho `vertex`; thân yêu cầu giống hệt `developer_api`; làm mới token khi
  hết hạn; `identifier`, `model_id` và mọi config hash không đổi khi đổi đường gọi; manifest ghi đường gọi.
- **Tôi kiểm:** dry-run sáu tài liệu không đổi trạng thái stage; chạy một bước thật nhỏ qua Vertex (ví dụ vé 11b hoặc lượt xác minh danh
  tính trên một tài liệu), so kết quả và số token với lần chạy qua Developer API; đọc sổ chi.
