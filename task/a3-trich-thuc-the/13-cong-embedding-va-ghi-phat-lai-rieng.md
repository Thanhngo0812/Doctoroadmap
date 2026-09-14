# 13 — Cổng embedding, cơ chế ghi–phát lại riêng, embed chunk

**What to build:** 233 chunk có vector, và bộ test chạy trên **vector đã ghi** nên nhanh, miễn phí,
không đổi kết quả khi nhà cung cấp cập nhật.

Ticket này mở **ray thứ hai** của đợt — chạy song song hoàn toàn với ray A3, không chờ ticket nào.

## Cơ chế ghi–phát lại **riêng**, không dùng chung với hội thoại LLM

| | Bản ghi LLM (ticket 01) | Bản ghi embedding (ticket này) |
|---|---|---|
| Hình dạng | nhật ký hội thoại **có thứ tự** | từ điển **văn bản → vector** |
| Tra cứu | theo lượt thứ n | theo băm của văn bản đầu vào |
| Trạng thái | có — lượt sau phụ thuộc lượt trước | không — thuần hàm |
| Vô hiệu hoá bởi | `prompt_hash` | `embedding_model_id` |

Ép chung một cơ chế buộc phía embedding mang trạng thái hội thoại nó không có, và buộc phía LLM chấp
nhận tra cứu theo băm đầu vào — trong khi cùng một đầu vào ở hai lượt khác nhau **phải** cho hai kết quả
khác nhau. Hai cơ chế nhỏ rõ ràng hơn một cơ chế phải chiều cả hai.

Bản ghi embedding còn có vai riêng: **đợt merge sau cần vector thật** để test blocking ở ngưỡng
0,75/0,95 — từ điển văn bản→vector dùng lại được nguyên vẹn, nhật ký hội thoại thì không.

## Ngữ cảnh ghép lúc embed — và vì sao điều đó quan trọng

Ghép `section_path` vào **thời điểm embed**, `text` chunk **giữ nguyên**:

```
embed("THỐNG KÊ TOÁN §1. LÝ THUYẾT MẪU > 1.2. Phân loại mẫu\n\n" + chunk.text)
```

Vì `text` không đổi nên **băm định danh chunk không đổi** ⇒ quyết định này **đảo ngược được**, và nâng
cấp lên ngữ cảnh sinh bởi LLM sau này không phải embed lại vì đổi định danh.

Bằng chứng cho việc ghép: Docling đặt `contextualize()` làm **mặc định** cho mọi chunker; Anthropic đo
giảm **35%** lỗi truy hồi. `section_path` đã tính sẵn nên tốn 0 đồng.

**Blocked by:** None — can start immediately, song song với ticket 01.

**Status:** done

- [x] Cổng embedding trong `application/ports/`, có `identifier` và `embedding_model_id`
- [x] **Một cổng duy nhất** — ticket 15 và đợt merge gọi lại cổng này, không dựng cổng thứ hai
- [x] Adapter thật; thiếu key ⇒ báo lỗi ngay lúc dựng
- [x] Cơ chế ghi–phát lại **riêng**: từ điển băm-văn-bản → vector, đặt ở `tests/fixtures/embedding/`
- [x] Bản ghi vô hiệu hoá khi `embedding_model_id` đổi
- [x] 233 chunk được embed với tiền tố `section_path` ghép **lúc embed**
- [x] **`text` chunk và định danh chunk KHÔNG đổi** — số vàng B0 đứng yên mọi cột
- [x] Có test: cùng văn bản vào ⇒ cùng vector ra từ bản ghi, **không chạm mạng**
- [x] Có test: đổi `embedding_model_id` ⇒ bản ghi cũ không được dùng
- [x] Ghi lại cỡ tệp thật của fixture vector
