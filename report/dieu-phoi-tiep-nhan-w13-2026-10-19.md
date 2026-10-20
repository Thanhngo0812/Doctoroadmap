# Điều phối tiếp nhận W-13 — 2026-10-19

**Trạng thái:** đã nhận báo cáo triển khai, **chờ commit và soát độc lập**. Không đánh dấu W-13 đạt, không mở W-15 chỉ bằng số test.

## Bằng chứng đã đối chiếu

- [Báo cáo nhân viên](w13-dung-mot-cuon-2026-10-19.md) và [vé W-13](../task/web/W-13-dung-mot-cuon-o-loi.md).
- Đã đọc port `BuildRunner`/`BuildResult`, use case điều phối, composition pipeline, bộ đo usage, SQLite recorder, CLI và các test ranh giới chính.
- Mã W-13 vẫn ở working tree: `src/doc2roadmap/presentation/cli/main.py` đang sửa, các tệp W-13 mới còn untracked. HEAD lúc kiểm là `181a134`, không
  phải commit chứa mã W-13. Không stage/commit thay phần của nhân viên hoặc tệp phiên khác.
- XML nhân viên: `tmp/w13-full-final.xml` có **1.868 test**, `tmp/w13-final-acceptance.xml` có **65 test**, cả hai không failure/error/skip. Đây là kiểm
  báo cáo máy đọc, không phải điều phối đã chạy lại toàn bộ 1.868 test.
- Điều phối tự chạy lại **67 test đạt** = 65 test W-13 + 2 test kiến trúc, 16,60 giây; hai cảnh báo SWIG. XML: `tmp/coord-w13-20261019.xml`.
- Tự chạy lại bốn biến thể qua `scripts/w13_mutations.py --case <tên>`: bỏ nhãn, chuyển nhãn sau canonical, bỏ cổng trang, truyền sai transport. **4/4**
  bị test bắt. Baseline của cùng các test đã xanh. Bằng chứng riêng: `tmp/coord-w13-mutations-20261019/`; không sửa tệp mã sản phẩm.
- Kiểm thử integration chặn đường gọi nhà cung cấp/xác thực qua bản giả, dùng doc-6 và PDF tổng hợp; chi mô hình mới của điều phối **0 USD**.

Lệnh chạy lại:

```powershell
& '.venv/Scripts/python.exe' -X utf8 -m pytest tests/unit/application/test_build_document.py tests/unit/application/test_build_pipeline.py tests/unit/infrastructure/test_build_log.py tests/unit/infrastructure/test_fake_build_runner.py tests/unit/presentation/test_build_cli.py tests/integration/test_w13_build.py tests/unit/test_architecture.py -p no:cacheprovider --basetemp=tmp/coord-w13-20261019 --junitxml=tmp/coord-w13-20261019.xml --tb=short -ra
```

## Những điểm đã thấy trong mã/test

- Thứ tự `read → label_roles → a3 → canonical → roadmap → learning_prep`; A3 và A3′ chạy song song bên trong bước `a3`.
- Đường canonical gọi trực tiếp `a4_gold_coverage="none"`, `gold_sheet_id=None`, tiếng Việt; không gọi bộ nạp vàng. Ca tái dùng canonical doc-6 có test
  riêng không nạp thêm cuốn khác, giữ nguyên manifest cache lịch sử.
- Generation và embedding nhận transport từ Settings; test nối dây truyền Vertex đúng quyết định tạm thời hiện hành. Chưa có worker web thật để chứng
  minh đường FastAPI → worker → lõi.
- `BuildResult` giữ usage/chi phí quy đổi từ token thực trả và bảng giá; có `usage_complete`, thời gian thực. Callback ghi kết quả cả thành công/lỗi/huỷ.
  SQLite recorder có phép kiểm truy vấn độc lập với usage giả khác 0. Đây là số quy đổi theo token, không phải hoá đơn nhà cung cấp.
- CLI đã ghi SQLite; **PostgreSQL web chưa được nối**, thuộc W-14. Không diễn đạt “ghi DB” thành đã xong tích hợp cơ sở dữ liệu web.

## Phần còn chờ

1. **Nhân viên lõi commit W-13 theo đúng danh sách tệp của vé**, gồm mã/test/script/báo cáo cần thiết, và báo hash commit. Không cuốn thay đổi đang có
   của các phiên Pha A, dữ liệu D-01/D-02 hay các bổ sung spec khác vào. Người soát cần snapshot tái lập được.
2. **Người soát nhận W-13** theo tiêu chí vé, trên commit đó. Lượt kiểm của điều phối không thay phán xét độc lập.
3. **Doc-6 toàn chuỗi chưa hoàn tất:** chạy từ bộ đọc nhẹ mới thiếu cache `label-roles`; chặn trước chi là hành vi đúng, nhưng chưa đạt tiêu chí dựng
   thành công toàn chuỗi từ cache. Người làm chuẩn bị kế hoạch tái dùng cache đúng cấu hình hoặc dự toán riêng cho chủ dự án nếu cần chi; không tự bỏ
   label-roles, bỏ cổng chữ hay dùng cấu hình tập giữ lại để ép qua. Không đồng nhất việc bỏ dự toán trên app với bỏ thủ tục xin duyệt tiền nội bộ.
4. Nhap-mon-ml chỉ đo từ parse cache một trang vì thiếu PDF gốc; người soát ghi giới hạn hiệu chỉnh, không gọi là sáu phép đo PDF gốc.
5. **W-14 và W-15:** nhóm web nối callback/usage vào PostgreSQL và dùng luồng thả tệp → xác nhận → dựng, không dự toán. Spec mục 4 đã ghi quyết định mới;
   điều phối đồng bộ các yêu cầu cũ còn sót, giữ thủ tục duyệt lượt nghiệm thu có tiền.

## Việc kế tiếp của nhóm lõi

- Ngay: commit W-13, bàn giao commit và phần doc-6 còn thiếu cho người soát; xử lý phát hiện của lượt soát nếu có.
- W-05 vẫn chờ **W-01 đạt**; có thể đọc/chuẩn bị hợp đồng, chưa coi đủ điều kiện triển khai toàn vé. Khi W-01 đạt, ưu tiên W-05 để mở W-06 cho nhóm web.
- W-15 vẫn chờ **W-13 và W-14 đạt**. Chưa duyệt hoặc tự chạy sách mới có tiền.

Lời giao tiếp cho nhân viên lõi:

> Hoàn tất commit đúng phạm vi W-13 và báo hash. Ghi rõ đã triển khai/kiểm thử nhưng doc-6 toàn chuỗi còn thiếu cache label-roles; chuẩn bị cách tái lập
> không chi hoặc dự toán riêng để chủ dự án quyết nếu cần. Không tự gọi có tiền, không bỏ bước bắt buộc. Sau đó chờ phán xét W-13; chuẩn bị W-05 nhưng
> chỉ mở toàn vé khi W-01 đạt. Bộ dựng/DB thực của web sẽ do W-14 nối theo BuildRunner/BuildResult, không tính là đã hoàn tất trong W-13.
