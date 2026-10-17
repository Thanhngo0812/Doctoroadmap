# 19k — Dừng sớm khi lỗi vận chuyển

Ngày 2026-10-17. Chỉ xử lý việc nhỏ trong phần kiểm lần 2 của Claude ở vé 19k. Dùng mô hình giả, **0 USD API**; không chạy lại cổng 19l.

## Bản vá

Ở nhánh `run_model_jobs` có callback lưu tiến độ, khi nhận lỗi đầu tiên, gọi `cancel()` trên các future: việc chưa chạy bị huỷ, việc đang chạy tiếp tục. Bỏ qua future đã huỷ, thu và lưu kết quả các việc còn đang chạy rồi ném lại chính đối tượng lỗi đầu tiên. Không đổi số worker, không thêm rào chia lô, config hoặc cache key. Nhánh không có callback giữ nguyên.

Đã kiểm trực tiếp MRO trên Python dự án: `concurrent.futures.CancelledError` kế thừa `Exception`; ghi chú trước đó trong vé đã được sửa.

## Bằng chứng đỏ/xanh

`test_persistent_transport_failure_cancels_queued_calls_and_resumes` có bốn ca: lỗi kéo dài từ lời thứ 6, ở phán chính/lời sửa, với 1/4 worker trên 24 phiên.

- Trước sửa: cả bốn đỏ ở giới hạn số lời gọi; vẫn chạy đủ 24 việc thay vì tối đa 8/14.
- Sau sửa: cả bốn xanh, số lời gọi không quá `k + 2c`; ném đúng đối tượng `ModelTransportError` gốc. Có việc thực sự chưa bắt đầu.
- Toàn bộ phản hồi đã hoàn tất nằm trong checkpoint. Chạy tiếp không gọi lại phản hồi nào đã lưu; các việc bị huỷ được thực hiện và đủ 48 kết quả phán/sửa cuối cùng.
- Cạnh, cờ và executor log bằng lượt liền mạch; decision log chỉ khác `reused`; config hash giữ nguyên và checkpoint được xoá sau thành công.
- Test sẵn có `test_completion_callback_drains_successes_even_after_a_transport_failure` tiếp tục kiểm các lời đang chạy trả thành công sau khi lời khác lỗi vẫn được callback thu đủ.

Lệnh kiểm cuối:

```powershell
.venv\Scripts\python.exe -m pytest tests/unit/application/test_main_checkpoint_review_19k.py tests/unit/application/test_main_parallel_19k.py tests/unit/application/test_model_calls.py tests/unit/application/test_build_main_edges.py tests/unit/application/test_spend_guard.py -p no:cacheprovider --basetemp=tmp/pytest-19k-stop-green --junitxml=tmp/pytest-19k-stop-green.xml --tb=short
```

**36 test qua**, 8,64 giây, mã thoát 0. `git diff --check` qua. Đây là lượt kiểm bản vá; các số toàn kho trong báo cáo trước thuộc các cây mã trước.

## Ghim nguồn mã

Bản vá được commit riêng cùng test và báo cáo này; lấy SHA bằng `git log -1 --format=%H -- src/doc2roadmap/application/model_calls.py`. Khi chạy tiếp pipeline, ghi SHA thực tế đã chạy theo yêu cầu truy vết của 19l; giữ nguyên commit nguồn của artifact đã sinh trước bản vá. Không gán lại commit cho artifact cũ.
