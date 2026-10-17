# 19k — Pass chính song song (chỉ làm nếu 19j nhận)

**Nguồn chân lý:** [spec đổi mặc định chuỗi gộp](../../doc/doi-mac-dinh-chuoi-gop-spec.md), pha 1b, "Pass chính song song".
**Ai:** nhân viên · **Chi phí mô hình:** 0 USD (test bằng mô hình giả) · **Chặn bởi:** 19j (đã nhận) · **Trạng thái:** hoàn thành cả ba mục kiểm của Claude, 1.632 test qua ngày 2026-10-17

## Vì sao

Nếu thí nghiệm 19j cho thấy bỏ cạnh của các phiên trước khỏi đầu vào phiên không làm E4 tụt quá nhiễu, thì các phiên của một chương có thể chạy song
song. Pass chính doc-4 khi đó có thể còn vài phút thay vì 13,7 phút.

## Cần làm

- Thêm tuỳ chọn cho pass chính: không đưa "cạnh đã có của các phiên trước trong chương" vào đầu vào phiên. Tuỳ chọn nằm trong khoá cache.
- Khi bật, các phiên của một chương chạy song song, qua bộ giới hạn tốc độ hiện có.
- **Bật làm mặc định** (spec mục 1b, kết quả 19j).
- **Giữ đúng hình dạng đầu vào đã thử:**
  - khoá `previous_edges_in_chapter` vẫn có mặt, với danh sách rỗng;
  - `previous_edges_omitted_count` bằng 0;
  - prompt hệ thống không đổi.

  Lượt thí nghiệm chỉ gộp mọi phiên vào một đợt (`scripts/gop-khau/thu_pass_chinh.py`, biến thể `song`). Phần sửa sau pass chính vẫn chạy như cũ.
- Checkpoint và thứ tự nhật ký vẫn tất định.

## Nghiệm thu

- [x] Test với mô hình giả: khi bật, đầu vào phiên không có cạnh của phiên trước, và các phiên chạy đồng thời; khi tắt, hành vi như cũ.
- [x] Đổi tuỳ chọn thì khoá cache đổi. Toàn bộ test qua.

**Kiểm chứng 2026-10-17:** `DOC2ROADMAP_ROADMAP_MAIN_PARALLEL=true`, tuỳ chọn constructor `parallel_sessions`. 4 phiên cùng chương đạt 4 lời đồng thời; khi tắt đạt 1 và nhận cạnh cũ. Đầu vào, prompt, sửa lời phán, checkpoint và nhật ký được kiểm; HTTP qua extractor thật giữ limiter 2. Đổi tuỳ chọn đổi cache/checkpoint, đảo về tái dùng artifact. [Báo cáo 19k và gỡ cache 19g](../../report/v4-19kg-song-song-va-go-cache-2026-10-17.md).

Toàn bộ **1.621 test qua**, mã thoát 0, 276,78 giây. Phát lại phản hồi thật đã lưu của 19j: **361/361 đầu vào khớp**, kể cả lời sửa; cạnh, cờ và nhật ký executor của doc-1/xstk/doc-4 cùng băm. Không gọi API mới.

## Kiểm của Claude 2026-10-17 — yêu cầu trước cổng 19l

**Đã xử lý cả ba mục bên dưới.** Các mô tả hiện trạng là ghi nhận trước sửa. Kết quả và lệnh kiểm ở [báo cáo checkpoint 19k](../../report/v4-19k-checkpoint-kiem-claude-2026-10-17.md).

**Đã kiểm, đạt:**
- Diff khớp vé.
- Tự chạy lại phát lại phản hồi 19j bằng mã sản phẩm, kết quả 361/361 đầu vào khớp. Cạnh, cờ và nhật ký executor cùng băm.
- Phản chứng: đặt `parallel_sessions=False` thì phát lại hỏng ngay ở phiên đầu tiên nhận cạnh cũ (doc-1). Như vậy phép phát lại phân biệt được hai chế độ.

Hai việc dưới đây không đổi đầu ra, nhưng đổi thời gian và rủi ro mất tiền. Cổng 19l đo thời gian từng stage, nên cần làm trước cổng.

1. **Ghi checkpoint một lần mỗi đợt, không ghi theo từng phiên.**
   - Hiện trạng: vòng gộp cuối đợt ghi checkpoint sau từng phiên. Ở chế độ song song, cả pass là một đợt, nên mọi lần ghi dồn về sau khi lời gọi
     mô hình cuối cùng đã xong. Ngay sau đó checkpoint lại bị xoá.
   - Số đo, phát lại doc-4, 0 USD: 177 lần ghi, tệp lớn dần tới 13,5 MB, tổng 1,15 GB. Riêng phần ghi mất khoảng 79 giây; cả pass chính
     (không tính thời gian chờ mô hình) mất 84 giây. Lượt 19j song song đo 285 giây cho doc-4, tức khoảng 28% là ghi checkpoint.
   - Chế độ nối tiếp cũng ghi thừa trong mỗi đợt.
   - Cần làm: ghi một lần sau khi gộp xong cả đợt. Nội dung bằng lần ghi cuối của đợt hiện nay.
   - [x] Phát lại doc-4 song song bằng `tmp/19k-review/benchmark.py replay` (mở rộng từ dữ liệu của `tmp/19kg-replay-research.py`): thời gian ghi checkpoint dưới 5 giây. Băm `main_edges`, `main_flags`,
     `executor_log`, `decision_log` không đổi.

2. **Chế độ song song phải giữ tiến độ khi lỗi giữa chừng.**
   - Hiện trạng: `run_model_jobs` ném lại `ModelTransportError`. Lỗi này xảy ra khi hết 8 lần thử, hoặc khi gặp HTTP không thử lại được.
   - Ở chế độ song song, chỉ một lỗi như vậy là mất hết mọi lời gọi đã trả về.
   - Đo bằng phản hồi đã lưu của doc-4, lỗi giả ở lời gọi thứ 60:
     - song song: 65 lời gọi đã chạy, 0 checkpoint;
     - nối tiếp: lưu được 56 phiên.
   - Với doc-4, phần mất là tới khoảng 1,3 USD và phải chạy lại cả pass.
   - Yêu cầu: lời gọi đã trả về phải được lưu, để lượt chạy lại tái dùng theo `input_hash`, như cơ chế tái dùng hiện có.
   - Không được giảm độ song song. Không chia pass thành các nhóm phải chờ nhau, vì đuôi mỗi nhóm để worker rảnh.
   - Gợi ý: `run_model_jobs` nhận một hàm gọi lại khi từng lời gọi xong. Pass chính lưu các dòng đó vào checkpoint, ở một khoá riêng, tách khỏi
     `decision_log`, và giãn lần ghi (ví dụ mỗi 16 lời gọi xong). Thứ tự hoàn thành không tất định, nhưng khoá riêng này chỉ dùng làm cache tái
     dùng. Nhật ký cuối vẫn dựng theo thứ tự phiên. Cách khác cũng được, nếu đạt nghiệm thu.
   - [x] Test mô hình giả: lỗi vận chuyển ở lời gọi thứ k. Lượt chạy lại không gọi lại lời gọi nào đã trả về trước lỗi. Cạnh, cờ và
     `executor_log` bằng lượt chạy liền mạch. `decision_log` chỉ được khác ở cờ `reused`.
   - [x] Mô hình giả có độ trễ: đỉnh đồng thời vẫn bằng `concurrency`. Thời gian không chậm hơn bản hiện tại quá 5%.
   - [x] Không thêm trường nào vào khoá cache hay id checkpoint.

**Nên làm cùng lúc (một dòng, đầu ra y hệt từng byte):**
- `JsonArtifactStore._write` gọi `json.dump` thẳng vào tệp, nên Python dùng bộ mã hoá JSON viết bằng Python thuần.
- `json.dumps` cùng tham số dùng bộ mã hoá C. Trên checkpoint doc-4 12 MB: 0,23 so với 0,68 giây, chuỗi ra trùng khít.
- Mọi stage đều ghi qua hàm này; riêng graph doc-4 sau pass chính là 41 MB.
- [x] Test cũ về artifact vẫn qua. Thêm một test: với cùng một payload, bytes ghi ra bằng bản cũ.

**Nghiệm thu bổ sung:** doc-4 ghi checkpoint **1,376 giây**, 16 lần (15 lưu cache phản hồi, 1 trạng thái đã gộp), 112,3 MB; bốn băm đầu ra, config/id và checkpoint cuối không đổi. Đo bằng `tmp/19k-review/benchmark.py replay`, mở rộng phép phát lại 19j đã nêu trên, ghi thật trong kho thử. Mô hình trễ: đỉnh 8/8 worker, trung vị 0,714 → 0,501 giây (5 cặp đo). Writer trên tệp 13,5 MB: 0,461 → 0,211 giây, bytes trùng khít. Test lỗi phủ cả phán chính/lời sửa và kết quả đã kết thúc với lỗi schema; lượt sau không gọi lại kết quả đã xong. **1.632 test qua**, mã thoát 0, 240,85 giây; **0 USD**. Không chạy dry-run/cổng 19l.

## Kiểm lần 2 của Claude 2026-10-17 — đạt; việc dừng sớm đã hoàn thành

**Đã kiểm lại, đạt.** Kiểm trên phản hồi đã lưu của doc-4 trong 19j, 0 USD.
- **Ghi checkpoint:** 16 lần ghi, tổng 0,11 GB, mất 1,5 giây. Trước khi sửa là 79 giây.
- **Lỗi đơn lẻ ở lời gọi thứ 60:** lượt chạy lại chỉ gọi 67 lời, gồm lời bị lỗi và 66 lời sửa.
- **Lỗi kéo dài từ lời gọi 60 trở đi:** lượt chạy lại gọi 184 lời. Đúng bằng số lời chưa xong.
- Ở cả hai ca, cạnh, cờ và `executor_log` bằng lượt chạy liền mạch. `decision_log` chỉ khác ở cờ `reused`.

**Dừng sớm khi lỗi — đã xử lý.** Hiện trạng bên dưới là ghi nhận trước bản vá.
- Hiện trạng: khi có lỗi vận chuyển, `run_model_jobs` vẫn chạy hết các việc còn trong hàng đợi rồi mới ném lỗi. Thử lỗi kéo dài từ lời gọi 60:
  lượt đầu vẫn gọi đủ 177 lời, tức 117 lời lỗi thêm.
- Với transport thật, mỗi lời lỗi thử 8 lần, có backoff, tổng khoảng 4 phút.
  - Trường hợp hết quota ngày của Developer API rơi đúng vào cảnh này: mọi lời đều trả 429.
  - Khi đó pass sẽ treo khoảng 117/4 × 4 phút, tức gần 2 giờ, rồi mới báo lỗi.
  - Trên Vertex, với 100 lời đồng thời, treo khoảng 8 phút.
- Cần làm: ở lỗi đầu tiên, huỷ các việc chưa bắt đầu. Vẫn chờ và lưu kết quả của các việc đang chạy, rồi ném lỗi gốc.
  - Lượt chạy lại sẽ gọi các việc đã bị huỷ. Các việc này chưa từng tốn tiền, nên tổng chi không đổi.
- Lưu ý đã kiểm trên Python của dự án: `concurrent.futures.CancelledError` kế thừa `Exception`. Bỏ qua future đã huỷ trước khi lấy kết quả; giữ lỗi vận chuyển đầu tiên để ném lại sau khi thu các việc đang chạy.
- [x] Test mô hình giả, lỗi kéo dài từ lời k, `concurrency` = c: lượt đầu gọi không quá k + 2c lời (chừa chỗ cho việc worker vừa nhận) và ném đúng lỗi vận chuyển gốc. Lượt chạy lại
  ra cạnh, cờ và `executor_log` bằng lượt liền mạch.

**Kiểm chứng bản vá:** `test_persistent_transport_failure_cancels_queued_calls_and_resumes` phủ phán chính/lời sửa × 1/4 worker, k = 6 trên 24 phiên. Cả bốn ca đỏ trước sửa (vẫn gọi 24 việc), xanh sau sửa; checkpoint giữ tất cả kết quả đã trả về, chạy tiếp không gọi lại chúng, nhật ký chỉ khác `reused`, config hash không đổi. Nhóm liên quan **36 test qua**, 8,64 giây; **0 USD API**. [Báo cáo dừng sớm](../../report/v4-19k-dung-som-khi-loi-2026-10-17.md).

**Claude kiểm lại 2026-10-17 (commit `8f1c9d0`):**
- **Logic:** chỉ huỷ việc chưa bắt đầu. Lời gọi đang chạy vẫn được chờ xong và ghi checkpoint. Future đã huỷ thì bỏ qua, nên không đụng `CancelledError`.
  Mã ném lại đúng đối tượng lỗi gốc.
- **Tái lập "đỏ trước sửa":** chạy test trên bản sao `src` có `model_calls.py` của `8f1c9d0^` thì cả 4 ca đỏ; trên mã hiện tại thì xanh.

**Đạt. 19k đóng.**
