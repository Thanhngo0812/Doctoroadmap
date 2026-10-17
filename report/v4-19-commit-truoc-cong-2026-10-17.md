# Đợt 19: commit mã trước cổng 19l

Commit mã để ghim khi chạy cổng: `f4871fd83aa8169d771b8cbfe40d0a61d7baf56a`.
Git tree đã kiểm: `265e3fc287bd8ba678fda5e38a33a418e5f9eef2`.

Đã commit mã/test/báo cáo 19a–19i, 19k và ba mục kiểm cuối 19k, gồm gỡ cache query 19g.
Kèm công tắc 17k và các thư viện Pha B đã có trong workspace mà test 19e và stage đặt tên module thực tế phụ thuộc.
Phần nối CLI Pha B, preview, parser và D01/D02 ngoài phạm vi vẫn giữ trong workspace, không đưa vào commit này.

## Kiểm chứng đúng nội dung commit

Dựng bản riêng từ HEAD nền rồi áp đúng patch chuẩn bị commit, không đọc mã từ checkout bẩn.
Đã kiểm đường import `doc2roadmap` nằm trong bản riêng; sau test so bytes từng blob staged với bản đã kiểm trước khi commit.
Kết quả: **1480 test qua**, 0 lỗi, 0 bỏ qua; mô hình giả/offline, **0 USD API**.
JUnit: `tmp/19-commit-review/tests-final.xml`; patch: `tmp/19-commit-review/batch19.patch`.
Kết quả 1.632 test trong báo cáo 19k trước đây thuộc toàn workspace tại thời điểm đó; số ở đây thuộc riêng cây mã được commit.

## Nguồn gốc artifact và cổng

Chưa chạy dry-run hoặc cổng 19l. Không thay nội dung artifact đã sinh trước commit để gán nguồn gốc hồi tố.
Các artifact cũ chưa có commit sinh ra được xem là chưa biết nguồn gốc mã; các băm replay trong báo cáo 19k chỉ là bằng chứng đầu ra, không chứng minh commit sinh artifact cũ.

Vé 19l đã yêu cầu báo cáo ghi SHA mã thực tế chạy và bảng đối chiếu đường dẫn/version/băm manifest-payload/commit của artifact mới và artifact tái dùng. Commit nằm ngoài config hash/cache key.
Nếu chạy sau một commit khác, phải ghi SHA thực tế của lượt đó và xác nhận có commit mã nêu trên.
Workspace còn mã ngoài commit bên dưới; chạy cổng từ checkout sạch của commit đã ghim để tránh gán sai nguồn gốc.

```text
M scripts/pass-phu-ml/chay_d01.py
 M scripts/pass-phu-ml/xuat_phieu.py
 M src/doc2roadmap/domain/models.py
 M src/doc2roadmap/infrastructure/parsing/docling_parser.py
 M src/doc2roadmap/infrastructure/parsing/nhe/hinh_r6.py
 M src/doc2roadmap/presentation/cli/main.py
?? scripts/doc-nhe/cham_loai_bien_d02.py
?? scripts/doc-nhe/do_bu_m5_d02.py
?? scripts/thu-a1/lam_sach_d01.py
?? src/doc2roadmap/application/phase_b/assistant.py
?? src/doc2roadmap/application/phase_b/concept_index.py
?? src/doc2roadmap/application/phase_b/documents.py
?? src/doc2roadmap/application/phase_b/formula_images.py
?? src/doc2roadmap/application/phase_b/quiz.py
?? src/doc2roadmap/composition_phase_b.py
?? src/doc2roadmap/infrastructure/llm/phase_b.py
?? src/doc2roadmap/infrastructure/llm/phase_b_demo.py
?? src/doc2roadmap/infrastructure/media/formula_images.py
?? src/doc2roadmap/presentation/cli/phase_b.py
?? src/doc2roadmap/presentation/preview/__init__.py
?? src/doc2roadmap/presentation/preview/phase_b.html
?? src/doc2roadmap/presentation/preview/server.py
```
