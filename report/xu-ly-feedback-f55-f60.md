# Vòng 18 — F55–F60 và thử nghiệm F47 (2026-09-11)

## Trạng thái

Kiểm chứng cuối: **208 passed**, gồm 5 integration test, exit 0 (64,40 giây).
Lệnh: `.venv/Scripts/python.exe -m pytest --basetemp tmp/f55-f60-full -p no:cacheprovider`.

| Mục | Kết quả |
|---|---|
| F55 | Đã sửa nhánh gộp, giữ bằng chứng ảnh và đếm node sau validation |
| F56 | Tôn trọng việc rút lại: không ép tăng số requires ở A3. Ví dụ cạnh có trong hai few-shot thử nghiệm; chưa chứng minh tăng độ ổn định |
| F57 | Đã ghi fixture thật theo prompt hiện hành, hash từ code, replay đi qua extract_section |
| F58 | Giữ kết quả retry cuối để chẩn đoán, thêm comment tại nhánh; vẫn chặn ghi artifact thiếu coverage |
| F59 | Giữ trạng thái chưa được kiểm chứng trên dữ liệu thật cho khái niệm chỉ có trong ảnh |
| F60 | Không phải lỗi A3 theo spec; guard chính và gold cạnh thuộc tầng 2b chưa triển khai. Không thêm guard sớm trước quyết định learnable cuối cùng |
| F47 | Đã thử hai few-shot theo thể loại trên dữ liệu thật, chưa đạt điều kiện đóng |

## F55: sửa đúng nhánh gộp

Không đưa `None` vào evidence; hợp nhất source_refs không trùng và giữ media_evidence_id
đại diện đầu tiên. Các vị trí ảnh còn lại được giữ qua source_refs, không mở rộng schema sang
danh sách ID trong đợt này. `media_grounded_entities` đếm ứng viên sống sót có liên kết ảnh,
không đếm lượt mô hình đề xuất, ở cả section và document. Node vừa có chữ vừa có ảnh cũng
thuộc chỉ số này; không được đọc nó thành số node chỉ có trong ảnh.

`test_merge_media_evidence_survives_serialization` đã thất bại trên code cũ: cả hai thứ tự
văn bản/ảnh đều khiến section lỗi và không tạo được artifact. Sau sửa, test kiểm tra artifact
thật có một evidence, giữ liên kết ảnh và chỉ đếm một node cho các đề xuất trùng. Hai biến thể
validation xóa node kiểm tra chỉ số trở về 0. Thuật toán lên `a3-section-conversation-v4`
để cache cũ không che thay đổi semantics hậu xử lý; prompt mặc định không đổi.

## F57: nối fixture với mã sản phẩm

Fixture `tests/fixtures/llm/a3-section-with-image.json` được ghi lại từ Gemini thật bằng
`scripts/record_a3_fixture.py`. Hash hiện hành `8e7c14c360ce13e2a51b5ccb636a247ecfc7f637d73265d1feca7860dc244f71`,
model `gemini-3.1-flash-lite`; lần ghi có 4 lượt. File `.context.json` đi kèm giữ đầu vào
section để test không phụ thuộc kho artifact riêng của máy.

`test_committed_multimodal_fixture_replays_without_network` tính hash bằng prompt sản phẩm và
giá trị mặc định Settings, không lấy hash từ fixture hoặc môi trường `.env`. Đã thấy test đỏ
với fixture cũ vì lệch prompt_hash trước khi ghi lại. Test còn chạy `extract_section` thật:
các prompt/schema vòng đầu, glean và validation được code dựng lại rồi đối chiếu request đã ghi;
kiểm tra có entity có evidence và media có mô tả. Network bị chặn bằng monkeypatch trong test.

Fixture replay bảo vệ tương thích request và hậu xử lý; **không tự chứng minh độ ổn định của
mô hình qua nhiều lần gọi**. Cũng không chứng minh F59 chỉ vì fixture có ảnh.

## F47: phép thử có số, không thay mặc định

Hai bộ ví dụ tổng hợp (không lấy đáp án gold để làm mẫu) nằm trong `application/prompts/`:
`few-shot-statistics.txt` và `few-shot-technical-report.txt`. Chọn bằng `extract --few-shot`.
Đây là bộ **thử nghiệm**, không phải cấu hình được chấp nhận thay thế mặc định.

| Tài liệu | Phiên bản | Learnable | Mật độ/1000 | Gold recall | Node/edge Jaccard so baseline |
|---|---|---:|---:|---:|---|
| Báo cáo | v6 → v7 | 72 → 57 | 19,699 → 15,595 | Chưa có gold | 0,6463 / 0,1304 |
| XSTK | v4 → v5 | 156 → 153 | 5,133 → 5,034 | 23/40 → 24/40 (57,5% → 60%) | 0,7437 / 0,1351 |

XSTK excess 32,35% → 31,43%. Báo cáo 76 lượt gọi, XSTK 132 lượt; cả hai ghi artifact thành công.
Hai artifact thử nghiệm hiện là phiên bản mới nhất trong kho, còn baseline giữ nguyên. Hash riêng:

- Báo cáo v7: `96b3124853dfc13efec646b3e3aca8a721d7fafbff0fd808a01c26743b500479`.
- XSTK v5: `1418ee7c073a2e9da6688b12cdd79c12a61587d2962673851fa645c2135b8c62`.

Không cập nhật số-vàng bốn tài liệu bằng kết quả thử nghiệm, không gọi đây là corpus cùng prompt.
Baseline là lần chạy lịch sử; mã hậu xử lý cũng đã thay đổi và mỗi cấu hình chỉ có một mẫu mới,
nên chênh lệch không phải bằng chứng nhân quả/statistical significance của riêng few-shot.

Kết luận: DOCX gần dải hơn nhưng vẫn fine, XSTK vẫn coarse. Không ép số node để đạt mật độ,
không bỏ evidence gate. Cần bộ vàng độc lập cho báo cáo và kiểm tra coverage công thức của XSTK
trước khi chấp nhận chỉnh tiếp; chưa có cơ sở để tuyên bố F47 xong.

## Checklist các lần đổi prompt tiếp theo

1. Chạy a3-compare qua ranh giới thay prompt và lưu cả node/edge Jaccard; đo lặp cùng prompt
   trước khi kết luận cải thiện ổn định (ML v5→v6 từng có node 1,000 nhưng edge chỉ 0,321).
2. Chấm gold ngoài phần calibration; ghi rõ những tài liệu chưa có gold.
3. Ghi lại fixture thật bằng script rồi chạy replay từ prompt sản phẩm, không tự sửa hash fixture.
4. Khi triển khai 2b: lập gold cạnh, xác minh lại đề xuất tầng 1; thực thi requires chỉ nối hai
   node learnable sau quyết định cuối cùng, không copy đề xuất A3 nguyên trạng.
5. F59 chỉ được nâng thành đã kiểm chứng khi có ca thật có evidence rỗng và nguồn ảnh hợp lệ.
