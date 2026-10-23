# W-15 — Nối bộ dựng thật; đo USD/cuốn và phút/cuốn

**Nguồn chân lý:** [spec chức năng](../../doc/web-chuc-nang-spec.md), mục 4, 8, câu hỏi mở 2; vé [W-13](W-13-dung-mot-cuon-o-loi.md), [W-14](W-14-tai-sach-len-ban-dung.md).
**Ai:** nhân viên lõi chạy · người soát và Claude đọc số · **Chi phí mô hình:** một cuốn mới, ước dưới 3 USD theo D-01; dry-run trước, **chủ dự án duyệt**
· **Chặn bởi:** W-13, W-14 đã đạt; còn port PostgreSQL của Pha A · **Trạng thái:** đạt mốc adapter/kiểm 0 USD tại `eea5472`; toàn vé còn mở, chưa cấp quyền chạy có tiền.

**Nghiệm thu mốc 2026-10-23:** nhận `a8bb295` trên main `605f6a3`, mốc tích hợp `eea5472`; độc lập **2.266 Python đạt/0 fail/1 Cloudinary live không bật,
104 React/build**, thử phá guard port bị assertion bắt và SHA nguồn phục hồi. Chỉ nhận adapter dùng core BuildDocument thật/pipeline giả/PG thật;
pipeline mặc định còn thiếu port nên từ chối trước claim/provider, chưa chạy toàn chuỗi thật, cache doc-6 qua web hoặc dry-run thật.
Đề nghị port `DocumentPipeline(..., phase_b_store=None)`/`PhaseBRuntime(..., store=None)` và một nguồn chi build đã ghi mục 8 bàn giao;
chờ Claude/phiên Pha A chốt người sửa/phạm vi. Không tạo JSON rồi gán lại store, không coi số giả thành tiền provider.
Giữ Vertex, `allow_spend=False`; tiếp kiểm identity/cache trên bản sao trong lúc chờ. Sau port mới dry-run/đề nghị trần/duyệt đúng lượt.
Đã ghép/đẩy riêng mốc này bằng `d12b67c`, không đóng toàn vé. Xem [báo cáo](../../report/dieu-phoi-nghiem-thu-w11-w15-w24-va-ke-hoach-2026-10-23.md),
[lời giao](../../report/lenh-giao-viec-sau-w11-2026-10-23.md).

## Vì sao

**Cập nhật cuối đợt 2026-10-22:** W-14 đầu-cuối bộ dựng giả đã đạt có ghi chú và ghép/đẩy `7fe63df`, mốc kiểm `61b5d80`:
2185Python/104React/build, browser/SQL đạt. Tài liệu lõi `1acaf4e` được nhận cùng mốc ghép. Lõi bắt đầu phần adapter/composition/test fake0USD,
đọc [ghi chú đầu vào](../../report/w15-ghi-chu-dau-vao-sau-w25-2026-10-22.md); phần port trong `BuildDocument`/`composition_build.py` phối hợp
Claude/phiên pha A qua mục8 bàn giao trước khi sửa. Kiểm PostgreSQL xuyên suốt, Vertex, usage checkpoint và identity/cache; không rơi về JSON/SQLite.
Dry-run và tin nhắn duyệt tiền cho một cuốn/lượt/trần riêng vẫn bắt buộc; chưa chạy provider thật hoặc coi ngân sách SA-55/phục hồi là quyền chi W-15.
Xem [kế hoạch/lời giao](../../report/lenh-giao-viec-sau-w14-2026-10-22.md). Các cập nhật trước dưới đây giữ làm lịch sử.

**Cập nhật 2026-10-22:** backend/schema W-14+W-25 đã đạt và ghép `a572459`; React W-14 mới xong local, chưa cổng/ nghiệm thu đầu-cuối nên W-15 vẫn chưa mở chạy thật. Lõi có thể chuẩn bị ghi chú hợp đồng usage checkpoint/dry-run; mọi lượt có tiền vẫn cần duyệt mới. Xem [kế hoạch mới](../../report/dieu-phoi-kiem-lai-w25-w14-react-w24-va-ke-hoach-2026-10-22.md).

**Sau soát 2026-10-21:** backend W-14 chưa đạt, cần sửa [W-25](W-25-dong-bo-xac-nhan-huy-va-ket-thuc-ban-dung.md) và còn React/tích hợp. W-15 chưa mở lượt chạy thật; sau khi W-14 đầu-cuối đạt vẫn cần dry-run/tin nhắn duyệt tiền mới. Phần callback usage checkpoint từng bước còn phải chốt khi nối runner thật; không suy tổng thành chi từng bước. Xem [kế hoạch mới](../../report/dieu-phoi-nghiem-thu-w07-w14-w24-va-ke-hoach-2026-10-21.md).

**Cập nhật phụ thuộc 2026-10-19:** W-13 đã được điều phối nghiệm thu sau khi kiểm doc-6 hoàn tất và tái lập cả hai kho ở 0 USD;
xem [soát mới](../../report/dieu-phoi-kiem-lai-w13-w24-2026-10-19.md). Vé này vẫn chờ W-14. Phê duyệt hoàn tất W-13 không tự thay cho
phạm vi duyệt chi của lượt W-15; không chạy thêm mô hình trong bước điều phối này.

Bản demo không giới hạn khâu dựng (chủ dự án chốt 2026-10-18), nhưng chuỗi gộp hiện hành chưa có số USD/cuốn đo trên một cuốn mới hoàn toàn. Cần số thật
để chủ dự án biết một cuốn tốn bao nhiêu, và để biết bật trần ở mức nào nếu có lạm dụng. Cũng cần chạy trọn đường web với bộ dựng thật một lần.

## Cần làm

- **Nối dây:** worker dùng `BuildRunner` thật khi bật cấu hình `build_runner = real`; mặc định vẫn là bản giả ở dev.
- **Đường gọi thật:** worker tạm dùng Vertex AI (`DOC2ROADMAP_LLM_TRANSPORT=vertex`), cả sinh và embedding (chủ dự án cập nhật 2026-10-19). Kiểm cấu hình
  trước dry-run/lượt thật, ghi transport trong báo cáo cùng số đo; không chép bí mật. Chỉ chuyển Developer API khi chủ dự án yêu cầu chuẩn bị demo.
- **Lượt 1, 0 USD:** tải doc-6 qua web. Phải dùng lại bản dựng hay cache sẵn có, nên chi thật xấp xỉ 0. Kiểm trọn đường đi: trạng thái, thư, khoá học.
- **Lượt 2, có tiền:** chọn **một** cuốn tiếng Việt cỡ vừa trong `document-data/train/`, chưa có artifact chuỗi gộp.
  - **Không** dùng `document-data/test/` hay cuốn của tập giữ lại.
  - Ghi tên tệp và số trang vào báo cáo **trước** khi chạy.
  - Chạy dry-run nội bộ kiểm phụ thuộc; người làm chuẩn bị riêng dự toán/trần đề nghị cho chủ dự án duyệt, rồi mới chạy qua web. `BuildRunner`/app không
    tính dự toán theo cập nhật W-13; không tự bỏ bước duyệt tiền vì app đã bỏ dự toán.
- **Đo** cho mỗi lượt:
  - USD theo bước (từ sổ chi `purpose = build` và manifest đồ thị);
  - phút theo bước, tách phần chờ embedding;
  - số lời gọi mô hình;
  - usage_complete và các giới hạn số đo; ghi riêng trần được duyệt so với chi thực, không yêu cầu app có dự toán.
- **Đọc tận nơi:** mở khoá học của lượt 2 trên web; đọc tên module và vài bài giảng (phát lại hay mô hình giả, 0 USD). Ghi nhận xét chất lượng; không chặn vé.

## Tiêu chí nghiệm thu

- [ ] Lượt 1 qua web xong với chi ≈ 0, khoá học `ready`, thư "bản dựng xong" trong `Mailer` console.
- [ ] Lượt 2 có dry-run, có xác nhận duyệt của chủ dự án (trích tin nhắn hay ghi chú), rồi mới chạy.
- [ ] Bảng số: USD/cuốn, phút/cuốn theo bước, số lời gọi/token thực và cờ thiếu usage; trần đã duyệt so với chi thực. Không lấy chi lịch sử trong manifest
  làm chi của lần cache mới; không yêu cầu chức năng dự toán trên app.
- [ ] Báo cáo ghi đúng transport thực tế: hiện tạm dùng `vertex` cho sinh/embedding; nếu chủ dự án đã chỉ thị chuyển để demo thì trích chỉ thị và ghi
  cấu hình mới. Không tự chuyển transport.
- [ ] Đề xuất mức `system_daily_build_max_usd`, `build_monthly_max` **để sẵn khi cần bật**, theo số đo. Claude đọc rồi báo chủ dự
  án.
- [ ] Không mở tập giữ lại.

## Ngoài vé

Tối ưu chi phí khâu dựng (việc của phiên pha A).
