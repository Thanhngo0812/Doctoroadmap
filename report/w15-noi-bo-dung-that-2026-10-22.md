# W-15 — adapter/composition và kiểm 0 USD — 2026-10-22

## Phạm vi, kế hoạch và nền

Nhánh `work/w15-real-build`, worktree một cấp `tmp/w15-real-build`, từ main `157cbb3`. W-14 đã được nghiệm thu tại `61b5d80`, ghép `7fe63df`. Giữ mọi worktree W-14/W-25; không tự ghép main, không sửa task/kế hoạch/handoff, không sửa ké SA-54/56/57.

Giai đoạn này: adapter/composition web, test fake và PostgreSQL thật, kiểm cache/identity trên bản sao manifest; chi dịch vụ ngoài 0 USD. Chưa mở lượt có tiền hoặc nhận W-15 hoàn tất.

1. Chốt đề nghị port trước sửa lõi → xác minh chữ ký/đường dẫn và test cần có.
2. Cài adapter web và kiểm RED/GREEN → dùng BuildDocument với pipeline được tiêm, không tạo JSON/SQLite ngầm.
3. Kiểm usage/lease/transport/cache và guard W-25 → SQL độc lập; full gate qua runner; báo rõ phần chưa đo.

## Đề nghị port để điều phối phối hợp Claude qua mục 8 bàn giao

**Đã ghi trước khi triển khai adapter; chưa sửa bất kỳ tệp lõi nào.** Chủ dự án yêu cầu chỉ ghi báo cáo, không gửi tin nhắn trực tiếp sang phiên điều phối. Những chữ ký sau là đề nghị, chưa được nhận là đã cài/được phiên Pha A chấp thuận.

| Đường dẫn/chữ ký | Thay đổi đề nghị | Test nghiệm thu port |
|---|---|---|
| `src/doc2roadmap/composition_build.py::DocumentPipeline.__init__(settings, *, allow_spend, phase_b_store=None)` | Nhận kho Pha B từ composition web. Khi được tiêm, roadmap/name/concept-index và runtime con dùng đúng kho đó. CLI giữ mặc định riêng; web không gọi nhánh mặc định | Chặn constructor JsonPhaseBStore/SqliteBuildLog, dùng hai engine PG thật đọc name/cache/module_assignment; không chỉ kiểm thuộc tính store |
| `src/doc2roadmap/composition_phase_b.py::PhaseBRuntime.__init__(..., store=None)` | Chọn store được tiêm trước khi tạo DailySpendGuard/use case/session/model con; không tạo JSON rồi gán lại store | Session/spend guard/cache use case đều ghi/đọc PostgreSQL xuyên connection độc lập, không có live.json |
| `src/doc2roadmap/composition_build.py::build_document_runner(..., recorder=...)` | Web truyền recorder bắt buộc hoặc dùng trực tiếp BuildDocument; không gọi mặc định SQLite | Spy recorder terminal đúng một receipt; cấm constructor SQLite; lỗi/huỷ giữ usage |
| `src/doc2roadmap/application/use_cases/build_document.py::BuildDocument.execute(...progress...)` | Không cần sửa ở giai đoạn adapter: web bọc progress completed để chụp usage baseline→hiện tại sau khi bước join; nếu sau này đưa checkpoint vào core thì giữ cùng payload/baseline, không phát trùng | Snapshot luỹ kế attempt, lịch sử meter bị trừ; final thiếu số giữ false; lỗi giữa bước dư step=null |

Payload checkpoint: `progress(step, {"status":"completed", "usage":{"spent_usd":0.003,"model_calls":3,"input_tokens":300,"output_tokens":60,"usage_complete":true}})`. Các số là ví dụ giả. Snapshot tính từ đầu attempt/lease, không delta một bước/historical artifact. Worker hiện ghi phần tăng vào PostgreSQL ledger; final còn dư chưa phân bổ dùng step=null.

Adapter mặc định phải từ chối pipeline thật chưa có port `phase_b_store` **trước khi claim job hoặc gọi provider/ADC**. Test tiêm pipeline fake nhận đúng cùng PostgreSQL; không suy test fake thành port thật đã xong. Không tự sửa tệp Pha A trong lúc chờ.

## Tiến độ kiểm và bàn giao

Đang triển khai. Sẽ bổ sung mốc commit, RED/GREEN/log/JUnit/SQL, ma trận usage/cache, transport/recorder, thời gian tường, dry-run và bảng đề nghị với mọi số chưa biết ghi rõ chưa biết. Không chạy mô hình/mail/Cloudinary thật.
