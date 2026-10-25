# W-15 — tìm nguyên nhân timeout và giữ retry của core — 2026-10-25

Tiếp từ [lượt thật R5](w15-luot-that-2026-10-25.md), commit `c19d461`.
Worktree `tmp/w15-real-build`, nhánh `work/w15-real-build`; root vẫn main `6249dab`.
Không sửa `src/doc2roadmap/`, không đổi .env, không ghép/push main.

## Chỉ thị mới và thay đổi chính sách operator

Chủ dự án yêu cầu:

> hãy tìm nguyên nhân lỗi đi

Sau đó hỏi:

> tôi tưởng bên core phải xử lí retry này kia để ko lỗi, hay do bạn ko dùng core

> cần gì, tôi chỉ muốn backend lắp core vào dự án thôi mà nhỉ, sao backend lại chặn retry của core

> nếu retry thành công thì lấy usage đó thôi chứ có gì đâu

Đã giải thích usage lần retry thành công không bao gồm chi phí có thể phát sinh ở lần timeout.
Theo hướng để core tự retry, bổ sung opt-in **chỉ trong approval operator tin cậy**:
`retry_unknown_within_cap=true`. Core vẫn tự quyết định retry/backoff/số lần qua adapter thật;
backend không viết vòng retry, không đổi thuật toán hoặc adapter lõi.

Mặc định của approval cũ vẫn chặn khi usage unknown. Web thường vẫn allow_spend=False,
không có cờ HTTP/Settings/UI để bật chi hoặc opt-in retry. Cờ approval phải là boolean thật,
validate trước composition; reference vẫn consume một lần, đúng PDF SHA/u-hash/HEAD/config/profile/DB.

Khi opt-in: mỗi lần timeout giữ nguyên reserve thành unknown upper. Mọi lần retry/request mới vẫn cần
`known + unknown upper + held + reserve <= cap`; hết trần/audit hỏng/bound sai vẫn chặn trước provider.
Không coi timeout là 0 USD. Khi core hoàn tất sau retry, wrapper giữ kết quả core và ghi
usage_complete=false nếu còn attempt thiếu usage; không tự đổi kết quả thành failed chỉ vì unknown
đã được owner cho phép tiếp tục trong trần. Nếu core thất bại hoặc guard thực sự dừng, vẫn failed.

## Bằng chứng 0 USD trước gọi thật

- RED policy: 5 ca mới thất bại trên API cũ chưa có opt-in.
- RED operator: 4 ca bắt cờ bị bỏ qua/không validate; ca mặc định còn đạt.
- RED kết quả: core retry trả vector nhưng wrapper đổi succeeded thành failed chỉ vì unknown.
- GREEN: **48 test operator/approval/guard đạt**, PostgreSQL thật, transport fake và guard mạng.
- Lượt GREEN đầu có một lỗi số học trong test: cap 0,72 nhỏ hơn hai reserve generation 0,720896.
  Đã sửa fixture cap thành 0,721: cho phép đúng lần retry thứ hai và vẫn bắt lần thứ ba trước provider.
  Giữ native thất bại, không bỏ test/cận trên hoặc giảm assertion.

## Vị trí lỗi đã biết, giả thuyết đang phân biệt

R5 whole-build cấu hình 100 hoàn tất concepts, canonical 161 node; A6 BuildClusters gửi 100 request
SEMANTIC_SIMILARITY, 19 đủ response, 81 timeout. SHA của cả 100 payload khớp chính xác đầu vào A6.
52 timeout sau HTTP 200 khi read body, 29 trước khi ghi được HTTP status. Không có lỗi generation ở đợt này.
Probe 100 RETRIEVAL_DOCUMENT trước đó đạt, nên không đồng nhất hai workload.

Môi trường kiểm 0 USD: Python 3.12.11 / OpenSSL 3.5.4, urllib không phát hiện proxy;
không có bằng chứng để quy nguyên nhân cho proxy, quota hay model không hỗ trợ task type.
Phép thử tiếp theo cần giữ core/retry nguyên bản, log thời gian nhận header, framing/content-length,
số byte đọc ở socket, traceback và hash request, không ghi Authorization/token hoặc raw nội dung PDF.

Chưa chạy thêm lượt có phí ở mốc code này. Mọi plan sau đây phải chuẩn bị mới ở đúng commit/config sẽ chạy,
không sửa/tái dùng plan R5. Giữ profile demo embedding_billing_verified=false và trần tổng R5+R6 dưới 4 USD.
Chi R5 theo giả định: known 1,28947575 USD, unknown upper 0,4139008 USD, tổng cận trên 1,70337655 USD.

Nguồn chính thức: [Python 3.12 urllib.request](https://docs.python.org/3.12/library/urllib.request.html)
ghi HTTP/1.1, Connection:close và timeout áp dụng cho thao tác blocking;
[Google Text embeddings API](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/model-reference/text-embeddings-api)
mô tả request/response riêng từng predict và các task type. Các nguồn này không chứng minh nguyên nhân timeout
của máy/lượt chạy này; kết luận phải dựa trên phép thử và log thực tế.

W-15 vẫn mở; kết quả, chi và câu hỏi tiếp theo ghi trực tiếp ở báo cáo này, không gửi message phiên khác.
