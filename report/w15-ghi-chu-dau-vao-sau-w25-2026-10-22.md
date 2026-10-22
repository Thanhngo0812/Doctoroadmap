# W-15 — ghi chú đầu vào sau W-25 — 2026-10-22

**Trạng thái:** chuẩn bị tài liệu, chưa triển khai runner thật/chưa chạy dry-run/chưa xin hoặc chi tiền. Nền đọc `b86bde2` (main đã có backend `a572459`). W-14 đầu-cuối vẫn chờ nhóm web và điều phối. Nguồn: [vé W-15](../task/web/W-15-noi-bo-dung-that-do-usd-cuon.md), [hỗ trợ hợp đồng W-14](w14-loi-ho-tro-tich-hop-cuoi-2026-10-22.md).

## 1. Điểm nối hiện có và khoảng thiếu đã xác định

| Điểm nối | Hiện trạng đọc từ mã | Việc cần chốt trong W-15 |
|---|---|---|
| `BuildRunner.execute(..., progress, cancelled, dry_run)` | W-13 có; web worker chỉ chọn fake dev | Nối real runner bằng cấu hình riêng, mặc định dev giữ fake; không giả định `build_runner=real` đã được cài |
| Final recorder | `BuildResult` có tổng usage và elapsed cho lượt execute; worker gắn build/actor/lease phía server | Tiêm recorder web vào factory; không dùng mặc định CLI `SqliteBuildLog` |
| Progress usage | Worker nhận `data['usage']` và ghi delta theo step. Scripted fake đã phát dữ liệu này | `BuildDocument` thật hiện phát started/completed metadata, **chưa gắn usage checkpoint**; cần port/chốt callback trước khi nhận số từng bước |
| Pha B bên trong runner thật | `DocumentPipeline.roadmap` tạo `JsonPhaseBStore(.../phase_b/live.json)` cho tên; `learning_prep` tạo runtime dùng cùng đường JSON | Phải tiêm PostgreSQL web đến mọi phụ thuộc con, không chỉ đổi `runtime.store`; ghi đề nghị port trước sửa lõi nếu vượt quyền |
| Cache và định danh | Web upload tạo `u-<băm>`; reuse đòi đúng doc/pipeline. Pipeline thật tạo version từ commit + config | Chốt identity/version và nguồn cache doc-6 trước lượt cache; không mặc nhiên graph của `doc-6` là cache hợp lệ cho `u-...` hoặc `web-fake-v1` |
| Dry-run | Core trả status `dry_run`; worker chỉ nhận bốn terminal succeeded/failed/rejected/cancelled | Chạy kiểm nội bộ bằng đường riêng, không ném dry-run vào queue rồi coi là course thành công |

Các điểm trên là đầu việc nối runner thật của W-15, **không phải lỗi mới chặn backend giả W-14**. Lượt này không sửa `src/doc2roadmap/`, không tạo migration hoặc mở transport thật.

## 2. Hợp đồng usage checkpoint cần hoàn thiện

Đề xuất dùng đúng `Progress = Callable[[str, dict], None]` và bốn bước hiện có, không thêm endpoint người dùng. Payload dưới đây là **mẫu đề xuất cho W-15**, chưa phải callback thật đã được phát:

```json
{
  "status": "completed",
  "usage": {
    "spent_usd": 0.003,
    "model_calls": 3,
    "input_tokens": 300,
    "output_tokens": 60,
    "usage_complete": true
  }
}
```

`progress('concepts', payload)` gửi usage **luỹ kế từ đầu lần execute/lease hiện tại**, không phải delta riêng bước và không phải số lịch sử từ artifact. Core `BuildUsage` tích luỹ trong vòng đời pipeline; adapter phải lấy baseline ở đầu execute và trừ baseline cho mọi checkpoint, giống final `BuildResult`. Retry lease mới bắt đầu baseline mới; các receipt trước vẫn được cộng ở build aggregate bởi PostgreSQL.

- Snapshot phải gồm các lời gọi đã hoàn tất và số usage thực trả; lời gọi có retry cũng phải được đếm theo bộ đo hiện có. Cache hit không gọi model thì delta 0, không nhập chi cũ.
- Snapshot của bước completed phải xảy ra sau khi các công việc song song của bước đã join, trước khi sang bước tiếp. A3/A3′ chạy song song nhưng cùng `concepts`; không cộng hai lần từ parent/child meter.
- Nếu có số ở lỗi/huỷ giữa bước, phát checkpoint gắn bước đó khi có thể xác định chắc nguồn chi. Nếu chỉ biết tổng cuối, ghi phần dư chưa phân bổ; không gán bừa sang bước tiếp theo hoặc chia đều.
- Caller không gửi owner/lease/account từ request. Worker đóng các giá trị này từ job đã claim, kiểm lease/checkpoint và cancellation boundary. Giữ lại phép phá guard/receipt W-25 khi nối real runner.
- Final recorder được gọi một lần về mặt ghi receipt. Core có thể vừa callback vừa trả `BuildResult`; worker/DB phải giữ idempotency như hiện tại. Callback muộn của lease cũ được ghi usage đã biết một lần nhưng không publish hoặc gửi mail cho lease mới.

## 3. Tổng chưa phân bổ và cờ thiếu số

`record_usage` lưu snapshot luỹ kế vào `build_attempt`, lấy phần tăng để append `usage_ledger` (`purpose=build`, actor/doc/build/lease/claim). Không cộng nguyên snapshot lần nữa ở mỗi checkpoint.

| Dữ liệu | Cách hiểu/ghi hiện tại |
|---|---|
| `extra.step` | Bước có checkpoint được chứng minh; terminal-only dư thì `null` |
| `extra.attribution_complete` | Hiện bằng `step is not None`; **không** đồng nghĩa tổng usage đã đủ |
| `usage_complete` | Đủ các số usage của attempt/build; false phải giữ false khi thiếu số hoặc reclaim |
| Tổng chưa phân bổ | SUM `cost_usd` của dòng `extra.step IS NULL`; không chia sang bốn bước |
| Tổng build | Chi đã biết của tất cả attempt, kể cả lease cũ trả muộn; không phải chỉ receipt của lease cuối |

Ví dụ tổng `.003`, concepts checkpoint `.001`, terminal `.003`: ledger ghi `.001` cho concepts và `.002` chưa phân bổ; tổng `.003`. Nếu số thiếu, giữ chi đã biết và `usage_complete=false`, không thay chi bằng 0 để trông đầy đủ. Final receipt 0 delta có thể hợp lệ khi checkpoint đã ghi hết; không coi một dòng 0 đó là cả lượt không tốn tiền.

Truy vấn sau là **mẫu đọc SQL cho lần chạy tương lai**, không phải kết quả DB vừa chạy. Dùng connection độc lập sau commit, tham số build ID từ lượt kiểm:

```sql
SELECT extra->>'step' AS step,
       extra->>'attribution_complete' AS attribution_complete,
       extra->>'usage_complete' AS usage_complete,
       sum(cost_usd) AS known_usd,
       sum(input_tokens) AS input_tokens,
       sum(output_tokens) AS output_tokens,
       sum((extra->>'model_calls')::bigint) AS model_calls
FROM usage_ledger
WHERE purpose = 'build' AND extra->>'build_id' = :build_id
GROUP BY 1, 2, 3;
```

Đối chiếu riêng `build` và `build_attempt.result`, quota/course/version/mail, không chỉ ledger. USD là quy đổi từ token trả về theo bảng giá được ghim, không thay hoá đơn nhà cung cấp. Giá và thông số model phải xác minh lại khi lập đề xuất có tiền; lượt tài liệu này chưa tra giá hoặc đưa dự toán mới.

## 4. Thời gian từng bước và phần chờ embedding

Final `BuildResult.elapsed_seconds` hiện chỉ là tổng thời gian. Các progress event chưa có số thời gian/embedding wait đủ để báo cáo W-15. Cần đo thời gian đơn điệu cho started → completed/failed/cancelled, không gồm thời gian chờ queue; ghi queue wait riêng nếu có.

Phần chờ embedding phải đo ở adapter/limiter hoặc span có nguồn rõ; chưa đo thì ghi thiếu, không lấy thời gian cả concepts làm embedding wait. A3/A3′ chạy song song nên tổng thời gian các lời gọi có thể lớn hơn thời gian tường của bước. Báo cáo tách wall time, thời gian chờ và tổng thời gian lời gọi, không cộng chồng thành phút/cuốn.

## 5. Transport Vertex và kho web

Cấu hình cần đối chiếu lúc W-15 thực sự mở:

- `DOC2ROADMAP_LLM_TRANSPORT=vertex`, `DOC2ROADMAP_VERTEX_PROJECT`, `DOC2ROADMAP_VERTEX_LOCATION`; giữ Vertex cho cả sinh/embedding. Không để Settings mặc định `developer_api` lọt vào runner thật.
- `WAYFINDER_DATABASE_URL` trỏ PostgreSQL web; API/worker, cache Pha B/use case và spend guard dùng cùng DB. Log chỉ ghi tên transport/model/region và định danh DB đã che bí mật.
- Ghim model ID/config thực tế, pipeline version và graph/chunks/parse version. Web composition ép Vertex cho model/embedding của Pha B, nhưng điều đó chưa chứng minh mọi dependency mới tạo trong runner thật cũng dùng Vertex/PG.
- Khi kiểm 0 USD, tiêm model/embedding/ADC/Mailer/MediaStore giả và chặn HTTP; kiểm constructor/cấu hình không lấy token hoặc gọi thử mạng. [Test composition hiện có](../src/web/backend/tests/test_composition.py) đã có assertion Vertex cho cả hai adapter, sai transport/project bị chặn trước gọi model.

Không gọi CLI thật với recorder mặc định để thay PostgreSQL. Không thay riêng thuộc tính store trên một runtime mà các session/name/index con vẫn giữ JSON.

## 6. Phạm vi dry-run sau này và điều kiện đề xuất chi

**Sau khi W-14 đầu-cuối đạt**, W-15 cần chuẩn bị lần lượt:

1. Tạo nhánh/worktree W-15 từ main đã nghiệm thu; chốt adapter/checkpoint/transport/PG bằng fake và test trước. Mọi nhu cầu sửa lõi ngoài quyền hiện hành phải ghi phạm vi port để giao đúng người.
2. Kiểm doc-6 bằng bản sao manifest cho phép; doc-6 hiện v29, doc-1 v8. Chứng minh reuse qua định danh web/pipeline hoặc cache hợp lệ; không dựng lại để lấy số phiên bản cũ. Không nhập chi lịch sử.
3. Chọn đúng một PDF/DOCX tiếng Việt cỡ vừa thuộc train chưa có artifact chuỗi gộp; ghi đường dẫn/SHA-256/số trang và trạng thái cache trước chạy. Không mở tập test/giữ lại trong lượt chuẩn bị này.
4. Chạy dry-run nội bộ 0 USD, có network guard và recorder không ghi SQLite. `BuildDocument.execute(dry_run=True)` vẫn ingest/kiểm sớm trước `inspect`, có thể ghi artifact đọc; dùng kho bản sao riêng. `inspect` hiện ghi `cache_validated=false`, chỉ thấy version mới nhất; có version không đủ chứng minh cache dùng lại được.
5. Hoàn thiện bảng đề nghị riêng: số gọi sinh/embedding, USD và phút theo bốn bước, phần hit/miss/unknown, phần embedding wait đo được/chưa đo, cache dùng lại, trần đề nghị và cách dừng. Unknown giữ unknown, không hứa tổng dưới mức nào chỉ từ sự tồn tại artifact. Không đưa bảng dự toán này vào app.
6. Trình chủ dự án **tin nhắn duyệt tiền mới** cho phạm vi một cuốn/lượt/trần cụ thể rồi mới chạy. Phê duyệt phục hồi trước đây, con số dưới 3 USD trong vé và ngân sách SA-55 không cấp quyền chi W-15.

Chuỗi luôn giữ: ingest bằng bộ đọc nhẹ mặc định → kiểm sớm gồm `require_text_quality` → **label-roles bắt buộc** → a3 (A3 + A3′ song song) → a4 tiếng Việt, coverage none → roadmap → a12/concept-index/formulas PDF. Không dùng cấu hình Docling so sánh T-01a, không tự bật `allow_text_quality_reason`, không bỏ nhãn để ép cache qua.

## 7. Trạng thái bàn giao

Đã có ghi chú hợp đồng và danh sách chỗ cần port/đo, chưa có số dự toán W-15 hoặc kết quả dry-run mới. Chưa chọn/mở cuốn train, chưa nối real runner, chưa gọi model/SMTP/Cloudinary, chưa thay JSON/SQLite của CLI, chưa sửa mã hoặc schema. **Chi ngoài mới: 0 USD.** W-14 vẫn do điều phối nghiệm thu đầu-cuối; tài liệu này không tự mở W-15.
