# T10b — Chạy tập giữ lại một lần theo bậc (07 v2)

**Nguồn chân lý:** [giao thức T10/07 v2](T10-07v2-giao-thuc-tap-giu-lai.md) · [bảng khoá](T10-cau-hinh-khoa.md) · lệnh mẫu ở `CONTEXT.md`
(mục "Lệnh bậc 1–3") · **Ai:** nhân viên chạy; chủ dự án duyệt chi từng bậc và T14; Claude chấm · **Chi phí:** **trần 90 USD** cho toàn lượt (chủ dự án nâng ngày 2026-10-03)

**Trạng thái:** **hoàn tất bậc 1–3 và bàn giao bậc 4 ngày 2026-10-04**. Xstk cuối **v46**, doc-4 cuối **v12** (tên module, lúc 18:11:49 Asia/Saigon); doc-4 tái dùng identity v6/main v7 và nối checkpoint, hoàn tất 22.972/22.972 cặp rồi A9 → tên khái niệm → A10 → tên module. CLI và watcher đã thoát thành công; heartbeat tạm dừng sau bàn giao. **Tổng luỹ kế ghi nhận + dự phòng embedding: 51,96653480 USD / trần 90 USD**, chưa gồm usage lời gọi đang bay khi ngắt, lượt neo cũ bị ngắt và retry embedding chưa đo được. Số HTTP 429 chính xác chưa đo được; 768 sự kiện throttle trong manifest của lượt nối gộp 429/503, không thay số 429. Không đổi mã/prompt/cấu hình/cờ; không đọc/chấm holdout. [Báo cáo bậc 3](../../report/T10b-bac-3-2026-10-03.md) · [bậc 1–2b](../../report/T10b-bac-1-2026-10-03.md). Danh tính T14 đạt 13/13 quyết định. **Chờ Claude làm bậc 5**, không tự chạy chấm. Trần riêng bậc 2 là 10 USD.

## Luật trong suốt lượt chạy
- **Không đổi gì.** Mã chạy từ commit đã khoá (`src/` giống `fce6c48`). Không sửa mã, prompt, `.env` phương pháp, cờ hay tham số giữa các
  bậc. Lỗi chặn chạy thì **dừng và báo**; bản sửa là hậu kiểm, kết quả ghi "không sạch".
- **Không đọc nội dung.** Chỉ báo trạng thái, số đếm, chi phí. Không mở đồ thị, lộ trình hay tệp vàng của xstk-ch3-1 và doc-4. Không
  chạy `cham_tap_giu_lai.py`, `kiem_doc_duoc.py` hay `a8-gold-check` trên hai tài liệu này.
- **Trần 90 USD cho cả lượt, hai tài liệu cộng lại** theo chỉ thị mới ngày 2026-10-03. Lệnh `roadmap` không có sổ chi riêng, nên giữ trần bằng thủ tục:
  - mỗi bậc tốn tiền: dry-run trước, gửi chủ dự án con số, chờ duyệt rồi mới `--allow-spend`;
  - sau mỗi bậc: cộng chi thật theo token trong manifest các stage vừa chạy, báo **một tổng chi luỹ kế**;
  - riêng lượt doc-4 đã được chủ dự án duyệt dù dự toán cộng dự phòng 1,5 lần vượt trần: theo dõi usage từ checkpoint, **dừng nếu tổng chi thật vượt 90 USD**; không đổi phương pháp/cờ/cấu hình, không tự nâng trần.
- Sập giữa chừng thì chạy tiếp từ checkpoint, không đổi cấu hình.
- Chạy riêng từng tài liệu: `xstk-ch3-1` trước (nhỏ), rồi `doc-4`.

## Các bậc

| bậc | việc | ai duyệt trước khi chạy |
|---|---|---|
| 1 | `ingest` cây tham chiếu, **đúng cột "cờ `ingest` bậc 1"** của bảng khoá (xstk: không cờ; doc-4: `--pdf-backend pypdfium2 --heading-scheme vn-textbook`). Rồi `label-roles` trên cây mới, rồi chuyển vai trò về chunks gắn A3 (`--chunks-version` 2 cho xstk, 3 cho doc-4, `--transfer-from-chunks-version <v cây mới>`) | chủ dự án duyệt dự toán `label-roles` (cỡ 0,01 USD) |
| 2 | `roadmap --stop-after identity`: clusters → mentions → provenance → neo → danh tính | chủ dự án duyệt dự toán |
| 2b | `tao_bang.py <doc> <v identity> --no-gold --output-dir tmp/duyet-danh-tinh-giu-lai` → **chủ dự án duyệt mọi cặp (T14)** → `doi_json.py <bảng đã điền> <khoá> <doc> <json>` → chạy lại `roadmap --identity-review <json> --allow-spend --stop-after identity` | — |
| 3 | `roadmap --identity-review <json> --dry-run` (dự toán A8 thật) → duyệt → chạy hết: A8 chính + phụ → A9 → tên khái niệm → A10 → tên module | chủ dự án duyệt dự toán |
| 4 | báo cáo bàn giao, rồi dừng | — |

## Báo cáo mỗi bậc (ngắn)
- Lệnh đã chạy (chép nguyên), version artifact tạo ra, "tái dùng" hay "chạy".
- Bậc 1: số section, chunk; số vai trò chuyển được và **số chunk không khớp** khi chuyển; cảnh báo của `ingest` (nếu doc-4 vẫn báo tách
  rời âm tiết là sai cờ: dừng).
- Bậc 2–3: số lời gọi, số 429, chi bậc, **tổng chi luỹ kế**.
- Bậc 2b: số cặp trong bảng, đường dẫn bảng; sau khi chủ dự án điền: version danh tính mới.

## Bàn giao (bậc 4)
- Version `stages` cuối (sau tên module) của từng tài liệu; commit mã đã chạy; tổng chi một con số; mọi sự cố.
- Commit báo cáo vào `report/`. Cây sạch ở mã chạy.
- **Claude** làm bậc 5: chuyển vàng xstk sang JSON, băm lại vàng doc-4, chấm theo giao thức, đọc hai lộ trình, báo cáo kể cả kết quả xấu.
