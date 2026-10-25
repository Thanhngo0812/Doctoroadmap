# W-16 — mốc backend usage-1 — 2026-10-26

Nhánh `work/w16-usage-backend`, worktree `tmp/w16-usage-backend`, nền main local
`b3c4426666dd868040ea0bc52e6485f5af6e1ac4`. W-15 đã nhận tại `efed8db`, ghép `7f54b14`;
mọi dữ liệu/run/grant của W-15 giữ nguyên, unknown cũ 0,4139008 USD không được ghi thành 0 hay hóa đơn.

## Phạm vi và thay đổi

Giữ endpoint GET `/api/v1/me/usage`, response DTO `MyUsage` và quota W-14 đã có.
Projection dùng `runtime.store.usage_rows(learner_id,since,purposes)`, fallback cổng PG cùng application engine
khi ứng dụng chỉ có build service. Hai truy vấn có lọc người/ngày/purpose; không đọc toàn ledger.
Assistant/document cộng theo người xuyên khoá; lecture/quiz_gen/quiz_verify tính toàn hệ thống;
trace counted_in=build bị loại khỏi tổng học, build tách riêng.

Sửa hai biên nửa mở: ngày `[00:00,00:00 hôm sau)` theo spend_day_timezone và tháng
`[đầu tháng,đầu tháng kế)` trong quota hiện hành. Trước sửa, dữ liệu fixture kỳ sau bị cộng vào kỳ trước.
Quota tháng vẫn đếm counts_quota, không lấy USD làm số lượt. max=null khi demo tắt; override tài khoản giữ nguyên.
ADR 0026 và BSettings hiện hành dùng learner_daily_max_usd=1,00; 0,20 trong đoạn Pha B2 cũ đã bị thay thế.
Đề xuất daily build 5 USD/monthly 3 lượt chưa được bật hoặc ghi vào cấu hình.

Không thêm migration: usage_ledger, chỉ mục learner/day và purpose/day, build/counts_quota/queued_at đã đủ.
Chỉ sửa hai tệp infrastructure và thêm test W-16. API/DTO, core, gateway/app, route W-10, React/OpenAPI không đổi.
Đây là projection đọc; không sao chép check/reserve/admission của DailySpendGuard và không sửa callback sinh/cache/retry.

## RED → GREEN và phạm vi bằng chứng

Lượt đầu: 13 setup errors vì thư mục cha basetemp chưa có, giữ XML; không tính là RED nghiệp vụ.
RED đúng baseline: **7 assertion failed / 6 pass / 0 setup error** — ba ca ngày, ba ca tháng, một ca chưa dùng port có lọc.
GREEN sau sửa: **69 pass**, gồm 13 ca W-16 và hồi quy W-09/W-14, PG thật/fake clock/provider bị chặn.
Phản chứng lần đầu phát hiện mutant shared chỉ tính owner còn sống sót; đã giữ log/XML và thêm assertion
cho người không phát sinh chi. Sau tăng assertion: **4 mutation bị bắt, source khôi phục nguyên byte, 13 ca W-16 đạt lại**.
Test bao gồm cuối tháng, cuối năm, 29/02 năm nhuận, 16:59→17:00 UTC, xuyên khoá/tách người,
personal/shared/build, trace không cộng trùng, override/default demo, quyền và DTO HTTP thật quét đệ quy tên khoá usd/cost.

Các ledger/build/cost trong test là **fixture tổng hợp**, không phải chi thật. Mọi công việc W-16 là 0 USD;
không sử dụng lại phê duyệt/grant W-15. JSON thật từ HTTP/PG cho web ở
[usage-1.json](w16-evidence/green-20261026-01/usage-1.json); các alias build quota W-14 được giữ để tương thích.

Fixture toàn repo dùng helper allowlist/SHA sáu sách; candidate train chỉ ordinary copy để phục vụ test fake/dry-run
đã có trong cổng, không chạy operator hoặc nhập DB/cache/run W-15. Không commit PDF/artifact/.env.

## Bàn giao cho web và trạng thái

Web có thể dùng nguyên usage-1 với learner_today.used_ratio/limited/resets_at,
builds_this_month.used/max/resets_at và shared_content_today chỉ có limited.
max=null là không giới hạn theo cấu hình demo, resets_at giữ offset +07:00; các giá trị ngày/tháng theo giờ Việt Nam.
Web giữ OpenAPI, trang mức dùng/dải React thực hiện sau W-10 và sau khi mốc backend được ghép.
Không tự ghép/push main, không sửa task/kế hoạch/handoff điều phối, không gửi message cho phiên khác.
Mốc này chờ soát và **không đóng toàn W-16**. Cổng toàn repo/React/build và commit cuối được ghi tiếp bên dưới.

## Kết quả cổng cuối

Commit mã **`7f98cf799cff78344a2d196118ec430d164c6b26`**, main đã nhận `b3c4426666dd868040ea0bc52e6485f5af6e1ac4`. Full PostgreSQL: **2729 pass**, 2 skip/xfail giữ nguyên; React **203 pass**; build **exit 0**. Các cổng chạy tuần tự; native/JUnit/lệnh/cwd/source SHA ở `w16-evidence/runs/`.

[JSON usage-1 bàn giao](w16-evidence/usage-1.json), [metadata fixture](w16-evidence/usage-1.metadata.json), [manifest](w16-evidence/manifest.json). JSON từ GET thật, ledger tổng hợp; không là chi tiền thật hoặc truy vấn dữ liệu W-15.

Tự động duyệt đã từ chối helper khôi phục rộng báo cáo W-14/W-06 vì có nguy cơ bỏ sửa dở ngoài phạm vi. Đã dùng phương án chỉ COPY; giữ nguyên output gốc chưa commit ngoài W-16 và ghi danh sách `retained-test-exports.json`. Không stash/reset/restore, không xóa dữ liệu. Những tệp đó không nằm trong commit W-16; source và commit mốc sạch trong phạm vi được giao.
