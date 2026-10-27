# Bổ sung review R9 — thu JSON trước khi navigation

**Approve bản sửa QA cuối `b0d7677b5a62aa5d88507862293476f7f1f41a4e`. QA-R9-JSON-1 đã đóng; không còn Critical/Required/Optional.** Kết luận React W-16 trước đó giữ nguyên. Cổng tích hợp cuối trên SHA mới do root chạy.

Đã soát riêng diff `2d36ed7b → 605d13d2 → b0d7677b` của `scripts/w16_web_check.cjs`. Không thay app/backend/worker hoặc chạy PG/browser full.

## Required đã phát hiện và xác nhận sửa

**QA-R9-JSON-1, `scripts/w16_web_check.cjs:38`:** ở `605d13d2`, hai assertion của nhánh readError nằm ngoài catch ghi `privacyFailures`. Khi clone body lỗi TypeError hoặc AbortError với signal chưa abort, binding chỉ reject fetch; app.catch có thể nhận lỗi đó. Handler response đã bỏ fetch JSON nên pendingRejections rỗng, privacyFailures cũng rỗng; kiểm cuối vẫn đạt dù thiếu JSON body. Bản cũ `2d36ed7b` giữ lỗi đọc TypeError trong pending và không đạt.

`b0d7677b` đưa cả nhánh readError và nhánh JSON.parse/inspectPayload vào một try/catch. Mọi lỗi không được phép đều được lưu ở `privacyFailures` trước rethrow; app.catch không xoá được dấu vết, assertion cuối tại `scripts/w16_web_check.cjs:327` từ chối lượt chạy. AbortError chỉ được bỏ qua khi signalAborted đúng true. Không bỏ JSON.parse hoặc bộ từ khoá privacy.

## Bằng chứng actual JS, RED → GREEN

`qa-json-guard-check.cjs` trích nguyên inspectPayload, binding JSON, fetch wrapper và hai assertion audit cuối từ Git commit được kiểm. Chỉ fake fetch/body lỗi, mô phỏng ứng dụng bắt rejection; không chép lại thuật toán audit. Probe gốc trên 605 được giữ nguyên ở `qa-json-probe.cjs/json`.

| Trường hợp | `605d13d2` | `b0d7677b` |
|---|---|---|
| JSON hợp lệ | Cho qua | Cho qua |
| JSON chứa validation riêng tư | Từ chối | Từ chối |
| JSON không parse được | Từ chối | Từ chối |
| AbortError, signalAborted=true | Cho qua | Cho qua |
| AbortError, signalAborted=false, app bắt lỗi | Cho qua sai | Từ chối |
| TypeError khi đọc body, app bắt lỗi | Cho qua sai | Từ chối |

Cùng driver với yêu cầu đúng: **605 native 1 / assertion fail; b0 native 0, cả 6 tình huống đúng**. Log, JSON kết quả và native receipt lưu ở `qa-json-guard-605d13d2.*`, `qa-json-guard-b0d7677b.*`. Bản b0 ghi source SHA-256 `e083b48f928cbeb4c1d6a44a709658dd865b9681aea4b8d9796efeda024bfcae` từ Git blob thực.

## Phần còn lại của bản vá

- `scripts/w16_web_check.cjs:72` await clone.text và binding trước khi trả response cho app: không phụ thuộc khả năng CDP lấy body sau navigation; clone giữ body gốc cho app đọc.
- `scripts/w16_web_check.cjs:118` chỉ bỏ body đọc trùng cho fetch JSON đã đi qua wrapper; markdown/non-fetch vẫn dùng handler response và pending audit cũ. SSE vẫn giữ tee cùng kiểm privacy trước khi giao chunk cho app.
- `scripts/w16_web_check.cjs:324` đợi networkidle trước đóng context; kết quả pending và privacy vẫn được kiểm sau lưu audit. Không đổi assertion UI/cache/model-call hoặc hạ tiêu chí browser.

Chỉ ghi scratch reviewer. Không PG/network/provider/SMTP/Cloudinary/ADC, không sửa product, chi ngoài 0 USD. Review này phê duyệt mã QA; kết quả browser/PG tích hợp phải được lấy từ cổng root mới đúng SHA b0.
