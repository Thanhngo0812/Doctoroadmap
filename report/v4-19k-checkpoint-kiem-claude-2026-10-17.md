# 19k — Ba mục kiểm của Claude

Phạm vi: đúng phần kiểm cuối vé 19k; không chạy cổng/dry-run 19l. Dùng mô hình giả và phản hồi 19j đã lưu, chỉ ghi vào kho thử. **Chi phí API: 0 USD.**

## Thay đổi

1. Gộp xong một đợt mới ghi checkpoint trạng thái đã gộp. Áp cho cả song song và nối tiếp; nội dung bằng checkpoint cuối của đợt trước đây.
2. `run_model_jobs` có callback thu kết quả hoàn tất tại luồng gọi; các worker tiếp tục nhận việc trong lúc luồng này lưu tiến độ. Kết quả trả về vẫn theo thứ tự đầu vào. Khi một future gặp lỗi vận chuyển, thu hết kết quả của các future còn lại rồi ném lại lỗi. Pass chính lưu cache phản hồi riêng ở `pending_model_results`/`pending_model_metrics`, giãn mỗi 16 lời xong và flush phần còn lại khi lỗi. Cache này không đi vào `decision_log` hoặc artifact cuối. Khi khôi phục, nguồn và id checkpoint vẫn được kiểm theo cơ chế hiện có; dùng lại theo `input_hash` và dựng nhật ký cuối theo thứ tự phiên.
3. `JsonArtifactStore._write` dùng `json.dumps` rồi ghi chuỗi, giữ tham số JSON, UTF-8, xuống dòng và thay tệp tạm nguyên tử.

Cache phản hồi đã hoàn tất còn giữ cả kết quả đã hết lần thử do sai schema. Kết quả đó được tái dùng như một lỗi đã kết thúc, không trả tiền để thử lại khi lỗi vận chuyển nằm ở phiên khác. Cache phản hồi hợp lệ vẫn qua validator cũ. Không thêm config, không đổi cache key/id checkpoint, không thêm rào chia nhóm phiên.

## Đỏ trước sửa, xanh sau sửa

- Lượt đầu: **6 test đỏ, 7 xanh**. Hai chế độ còn ghi 4 checkpoint thay vì 1/2; lỗi ở phán chính hoặc lời sửa không có checkpoint; bộ chạy chưa có callback. Hai test bytes đã xanh trên bản cũ, làm chuẩn đối chiếu định dạng.
- Ca schema kết thúc rồi gặp lỗi vận chuyển: test đỏ vì lời sai schema bị gọi 4 lần thay vì 2. Sau sửa không gọi lại; test callback/cache terminal tương ứng cũng xanh.
- Nhóm tập trung cuối: **59 test qua**, 6,70 giây, gồm model runner, main, limiter, spend guard, telemetry, artifact và bytes JSON.

Các assertion chính:

- `test_checkpoint_is_written_once_per_wave_with_its_final_state`: một lần cho toàn pass song song; hai lần cho hai đợt nối tiếp nhiều chương; checkpoint cuối bằng nội dung artifact tương ứng.
- `test_transport_failure_preserves_every_finished_call_and_reuses_it`, hai vị trí lỗi `main`/`repair`: giữ cả kết quả trả sau khi future khác đã lỗi. Chạy tiếp không gọi lại phản hồi đã xong; cạnh, cờ và executor log bằng chạy liền mạch, decision log chỉ khác `reused`.
- `test_transport_resume_also_reuses_completed_terminal_schema_failures`: giữ nguyên số lần gọi đã kết thúc với lỗi schema.
- `test_progress_cache_is_throttled_and_separate_from_final_decision_log`: 48 kết quả được flush ở mốc 16/32/48, nằm ngoài nhật ký ngữ nghĩa; sau khi gộp xong, checkpoint không còn cache tạm.
- `test_completion_callback_reports_finished_rows_and_keeps_return_order` và `test_completion_callback_drains_successes_even_after_a_transport_failure`: thứ tự callback theo hoàn tất, thứ tự kết quả theo đầu vào, không mất future xong muộn hơn lỗi.
- `test_json_writer_keeps_exact_bytes_of_the_previous_stream_encoder`: compact và pretty, chữ Việt/CJK/emoji, xuống dòng, số thực, âm 0, giá trị JSON đặc biệt; bytes đúng bản `json.dump` cũ, không còn tệp tạm.

## Doc-4: ghi checkpoint và bảo toàn đầu ra

Lệnh: `.venv\Scripts\python.exe tmp/19k-review/benchmark.py replay`.

Đọc `tmp/v4-19j/kho/doc-4-song-s1`, mentions v2; phát lại model từ pass chính v3. Mã trước sửa được chụp trong `tmp/19k-review/*_before.py`. Lượt đối chiếu trước sửa bỏ I/O checkpoint để lấy đầu ra chuẩn; lượt sau ghi checkpoint thật vào `tmp/19k-review/doc4/after`.

- Ghi checkpoint sau sửa: **1,376 giây**, đạt yêu cầu dưới 5 giây.
- **16 lần ghi:** 15 lần lưu cache phản hồi và **1 lần trạng thái đã gộp**; tổng **112.256.876 bytes**. Số cũ do Claude ghi trong vé: 177 lần, khoảng 1,15 GB và 79 giây. Không dùng lượt đối chiếu bỏ I/O làm số đo thời gian ghi cũ.
- Cả pass phát lại sau sửa: 3,331 giây, không tính chờ dịch vụ mô hình vì chỉ trả phản hồi đã lưu.

Băm trước/sau khớp:

| Đại lượng | SHA-256 |
|---|---|
| `main_edges` | `68823b35af95f6ff5f9365065180021acec9febbee71890027db86eb7bd27562` |
| `main_flags` | `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945` |
| `executor_log` | `2518d67876429467e6839360cf50856e5ad803f24005ddb7d4e2c204ddf5f77c` |
| `decision_log` | `ab38af7b89f85e4163717e1b0f531cbf762220be68f96a3d4acde7df62b22ac1` |
| Checkpoint trạng thái cuối | `73395865618b40155d06f68d86034055b26452207994cd08fc5930bf2f2e48ec` |

Config hash vẫn `c68fb21cecdb43120770f3078599274e28552d65ea3450c785c5e732e4f5aaaf`; id vẫn `main-` ghép hash đó, có assertion đối chiếu mã trước. Dữ liệu máy đọc: `tmp/19k-review/doc4-result.json`.

## Đồng thời và writer

Lệnh `.venv\Scripts\python.exe tmp/19k-review/benchmark.py latency`: 32 phiên giả, mỗi lời chờ 120 ms, 8 worker, ghi checkpoint thật; 5 cặp đo nối tiếp mã trước/sau. Đỉnh đồng thời cả hai vẫn **8**. Trung vị **0,714 → 0,501 giây**, tỷ số **0,701**, nhanh hơn khoảng 30%, đạt giới hạn không chậm quá 5%. Toàn payload cùng băm. Dữ liệu: `tmp/19k-review/latency-result.json`.

Lệnh `.venv\Scripts\python.exe tmp/19k-review/benchmark.py writer`: checkpoint doc-4 **13.522.961 bytes**, ba cặp đo. Trung vị **0,461 → 0,211 giây**; bytes trước/sau khớp tuyệt đối. Dữ liệu: `tmp/19k-review/writer-result.json`.

Các phép đo trên chạy riêng, trước hồi quy tổng, không chạy song song với benchmark khác. Đây là số đo trên máy hiện tại, không phải số đo lại dịch vụ LLM.

## Hồi quy toàn bộ

**1.632 test qua, 0 lỗi, mã thoát 0, 240,85 giây.** Gồm toàn bộ artifact, pipeline, telemetry, model runner, Pha B và kiểm kiến trúc. JUnit: `tmp/pytest-19k-review-full-02.xml`. `git diff --check` qua. Không chạy dry-run hay cổng 19l. Lệnh offline:

```powershell
$env:HF_HUB_OFFLINE='1'
$env:TRANSFORMERS_OFFLINE='1'
.venv\Scripts\python.exe -m pytest -p no:cacheprovider --basetemp=tmp/pytest-19k-review-full-02 --junitxml=tmp/pytest-19k-review-full-02.xml --tb=short
```
