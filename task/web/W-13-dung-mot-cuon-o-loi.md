# W-13 — Use case `build_document`: dựng một cuốn ở lõi

**Nguồn chân lý:** [spec chức năng](../../doc/web-chuc-nang-spec.md), mục 4 ("Dựng một cuốn ở lõi", luồng, kiểm sớm); [spec đổi mặc định chuỗi gộp](../../doc/doi-mac-dinh-chuoi-gop-spec.md);
[chạy lại doc-6](../../report/pha-b-chay-lai-doc6-chuoi-gop-2026-10-18.md) (chuỗi lệnh đã chạy thật); [Pha B CLI](../../doc/pha-b-cli.md).
**Ai:** nhân viên lõi · phối hợp phiên pha A · người soát kiểm · **Chi phí mô hình:** 0 USD (dry-run, phát lại, cache sẵn có) · **Chặn bởi:** không ·
**Trạng thái:** ready-for-agent

## Vì sao

Hiện dựng một cuốn cần chạy tay nhiều lệnh, và `a4` đòi đường dẫn bộ vàng kể cả khi cuốn không có vàng. Web cần một hàm duy nhất: chạy từng bước, báo
tiến trình, dry-run được, chạy tiếp từ bước lỗi.

## Cần làm

**Xác định chuỗi chuẩn trước khi viết mã.** Đọc spec chuỗi gộp và báo cáo chạy lại doc-6, rồi ghi vào báo cáo vé danh sách lệnh và tham số của một lần dựng
cuốn mới. Danh sách hiện biết:
1. `ingest` (đọc tài liệu, bộ đọc nhẹ mặc định);
2. `a4 --language vi`, chế độ không có vàng;
3. `roadmap` (tới A10 và tên module);
4. `phase-b a12`, `phase-b concept-index`, `phase-b formulas --pdf` (PDF mới có).

Bước nào thiếu hay thừa (ví dụ `label-roles`) thì hỏi phiên pha A và ghi câu trả lời vào báo cáo vé.

**Use case `build_document`** ở application, gọi các use case Pha A và Pha B có sẵn; **không** gọi CLI qua tiến trình con. Tham số:
- đường dẫn tệp, `doc_id`, ngôn ngữ `vi`;
- hàm báo tiến trình `(step, detail)`;
- hàm hỏi cờ huỷ, kiểm ở ranh giới bước;
- chế độ `dry_run`.

**Bốn bước công khai** khớp spec chức năng: `doc_reading`, `concepts`, `graph`, `learning_prep`.

**Kiểm sớm sau `doc_reading`**, 0 USD:
- bản quét: ký tự chữ trung bình mỗi trang < 200, hay > 50% số trang không có chữ;
- ngôn ngữ: tỉ lệ ký tự có dấu tiếng Việt trên ký tự chữ < `vi_min_diacritic_ratio`.
- **Chỉnh ngưỡng** trên sáu cuốn phát triển, cộng hai tệp tiếng Anh và một PDF chỉ có ảnh tạo trong test. Ghi số đo của từng tệp vào báo cáo.

**Dry-run:** chạy `doc_reading` thật (0 USD), rồi dự toán các bước còn lại bằng dry-run có sẵn của từng lệnh. Trả `{usd, minutes, model_calls}`.
- Phút ước tách phần chờ embedding, vì Vertex bóp quota embedding.

**Chạy tiếp:** gọi lại sau lỗi thì các bước đã xong không gọi lại mô hình, nhờ cache và checkpoint của Pha A. Kiểm bằng đếm lời gọi.

**Không cần vàng:**
- Chế độ sản phẩm không đọc tệp vàng nào.
- Nếu `a4` hiện không chạy được khi thiếu tệp vàng, **không sửa tệp của phiên pha A.** Ghi yêu cầu cho phiên pha A, và tạm truyền một tệp vàng rỗng hợp lệ
  do vé này tạo ở thư mục tạm. Báo rõ cách tạm này trong báo cáo vé.

**`pipeline_version`:** commit hiện hành cộng băm của cấu hình chuỗi. Trả về cùng kết quả.

**Port `BuildRunner`** bọc use case này cho W-14. **Bản giả** của port (dùng ở W-14 và mọi test web) chép artifact sẵn có của một cuốn phát triển sang
`doc_id` mới, báo đủ bốn bước, và 0 USD.

**CLI:** `doc2roadmap build --file … --doc-id … [--dry-run] [--allow-spend]`, cho người soát chạy tay.

## Tiêu chí nghiệm thu

- [ ] Báo cáo vé có chuỗi lệnh chuẩn, kèm xác nhận của phiên pha A hay ghi chú câu hỏi còn treo.
- [ ] `build --dry-run` trên doc-6 (tệp gốc của sáu cuốn phát triển) chạy xong, ra dự toán, 0 USD, không ghi phiên bản đồ thị mới.
- [ ] Chạy thật trên doc-6, **chỉ dùng cache sẵn có**: số lời gọi mô hình tính tiền là 0, hoặc báo số nhỏ trước khi chạy để chủ dự án duyệt.
- [ ] PDF chỉ có ảnh bị dừng ở `ban_quet` sau `doc_reading`; tệp tiếng Anh bị dừng ở `ngon_ngu_khong_ho_tro`; 0 lời gọi mô hình. Thấy đỏ trước khi có kiểm
  sớm.
- [ ] Cờ huỷ bật trong bước 2 thì không bước nào bắt đầu sau đó (test với use case giả từng bước).
- [ ] Lỗi giả ở bước 3 rồi chạy lại: bước 1 và 2 không gọi lại mô hình.
- [ ] Bản giả của `BuildRunner` qua cùng test hợp đồng của port như bản thật ở chế độ dry-run.
- [ ] Không mở tập giữ lại; test không dùng tệp của `document-data/test/`.

## Ngoài vé

Hàng đợi và worker (W-14). Đo USD/cuốn trên cuốn mới hoàn toàn (W-15). OCR bản quét.
