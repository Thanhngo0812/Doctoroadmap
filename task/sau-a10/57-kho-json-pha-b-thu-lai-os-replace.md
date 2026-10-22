# SA-57 — Kho JSON Pha B: thử lại `os.replace` khi Windows báo `PermissionError`

**Nguồn:** báo cáo SA-54 (`report/pha-b-sa54-2026-10-22.md` trên nhánh `work/sa54-test-gaps`), mục "Câu hỏi" 1; nghiệm thu của Claude ngày
2026-10-22.

**Ai:** agent Sonnet cài · Claude nghiệm thu · **Chi phí mô hình:** 0 USD · **Chặn bởi:** SA-54 ghép trước · **Trạng thái:** sẵn sàng

## Vì sao

`JsonPhaseBStore._persist` trong `infrastructure/artifacts/phase_b_store.py` ghi tệp tạm rồi gọi `os.replace` **một lần**. Trên Windows, khi máy nặng
tải, lệnh này ném `PermissionError` (WinError 5 hoặc 13): một luồng hay tiến trình khác đang mở tệp đích.

Đây là nguồn của hai lỗi:
- 3/30 lần đỏ của hai test kho JSON ở SA-54, khi máy chạy 6 tiến trình tải;
- `test_phase_b_lecture_sa30.py::test_stale_persisted_fallback_is_not_returned_or_kept` đỏ chập chờn trong cổng toàn repo.

`JsonArtifactStore._write` trong `infrastructure/artifacts/json_store.py` đã có cách xử lý: thử lại 5 lần, chờ tăng dần 0,1 giây mỗi lần.

## Cần làm

- `JsonPhaseBStore._persist` thử lại `os.replace` khi gặp `PermissionError`, theo cùng cách của `JsonArtifactStore._write`. Lần cuối vẫn hỏng thì ném
  lỗi ra, không nuốt.
- Không đổi định dạng tệp, khoá hay hành vi nào khác.
- Ba chỗ `os.replace` khác (`embedding/replay.py`, `llm/phase_b.py`, `llm/replay.py`) **không** thuộc vé này. Ghi vào báo cáo nếu thấy chúng cũng cần.

## Tiêu chí nghiệm thu

- [ ] Test mới, dùng `monkeypatch` để `os.replace` ném `PermissionError` hai lần rồi thành công: tệp được ghi đúng, đọc lại ra đúng dữ liệu. Bỏ vòng
  thử lại thì test đỏ.
- [ ] Test mới: `os.replace` luôn ném lỗi thì `_persist` ném `PermissionError`, không nuốt lỗi.
- [ ] Chạy lại phép thử tải của SA-54, 30 lần mỗi test dưới 6 tiến trình tải: 0 lần đỏ. Ghi cách tạo tải, và **tắt hết tiến trình tải** khi xong.
- [ ] Test Pha B và test kiến trúc xanh. Cổng toàn repo chạy trong worktree đã chép hai gói dữ liệu phát triển theo manifest, không chạy cùng lúc với
  cổng PostgreSQL nào khác.
