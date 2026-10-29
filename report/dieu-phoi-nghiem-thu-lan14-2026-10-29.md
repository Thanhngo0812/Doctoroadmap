# Nghiệm thu lần 14 — W-26 máy chủ demo local, 2026-10-29

**Người nghiệm thu:** Claude (điều phối). **Kết quả: đạt sau một vòng sửa test, ghép local, chưa push.** Chi nhà cung cấp lúc nghiệm thu 0 USD.

## 1. Mốc

| | commit |
|---|---|
| bản đầu của subagent lõi | `d3c2ec15` (từ main `e0bd4735`) |
| sửa sau nghiệm thu (subagent mới) | `be7f2064` — chỉ test, bộ phá, báo cáo |
| đỉnh nhánh đã gộp main `b94d4a88` | `dec34dac`, nghiệm thu trên worktree `tmp/coord-r14-acceptance-20261029` |

Nhánh đổi `wayfinder/demo_local.py` (mới), `infrastructure/disk_media.py` (mới), `cli.py` (lệnh `demo-local`), `composition.py` (trần người học
lấy từ `WebSettings.learner_daily_max_usd`, mặc định 1,0 như cũ), `build_store.py` (tách `spent_today`), `settings.py`, README và test.
Không sửa `src/doc2roadmap`, không sửa React.

## 2. Đọc mã

- Chi tiền chỉ mở qua `make_demo_worker` → `DemoSpendPolicy`: mỗi bản dựng một giấy phép `min(3 USD, 10 USD − đã chi hôm nay)`, giờ Việt Nam;
  `serve`/`worker` thường vẫn `allow_spend=False`, không endpoint hay biến môi trường nào bật chi.
- Worker chạy tiến trình con riêng, vì hook chi vá `urlopen` toàn tiến trình.
- DB phải khớp `wayfinder_demo_<đuôi>`, host phải là máy này; kiểm hai lần (tạo URL và trước `CREATE DATABASE`). DB `wayfinder` không bị đụng.
- Ảnh và tệp gốc trên đĩa (`DiskMediaStore`), đường dẫn qua `safe_path`; link tải ký HMAC theo phiên tiến trình, có hạn.
- Địa chỉ trong thư: `demo_settings` ghi đè `public_base_url` thành `http://<host>:<port>` (mặc định 8000), vì `src/web/.env` đặt 5173
  cho chế độ Vite. Chủ dự án hỏi đúng điểm này trong lúc nghiệm thu.

## 3. Bộ phá độc lập của Claude

Bảy phép, khác 27 phép của subagent; mỗi phép chạy cả `test_demo_local_w26.py`, khôi phục bytes và đối chiếu SHA. Script và JSON ở
`coord-r14-evidence-2026-10-29/mutations/`.

| phép phá | bản `d3c2ec15` | sau sửa `dec34dac` |
|---|---|---|
| `base-url`: bỏ ghi đè `public_base_url` (thư trỏ 5173) | **sống sót** | bị bắt (2 test) |
| `admin-once`: tạo admin dù đã có | bị bắt | — |
| `limit-zero`: `limit <= 0` → `< 0` | **sống sót** | bị bắt |
| `upload-raw-any`: nhận tệp raw không phải docx | bị bắt | — |
| `no-localhost-origin`: bỏ origin `localhost:8000` | **sống sót** | bị bắt |
| `learner-default-3`: trần người học mặc định 3 ở mọi nơi | bị bắt (2 test) | — |
| `child-not-stopped`: không dừng worker con | bị bắt | — |

Required **WEB-R14-01** (base-url) và Optional WEB-R14-02/03 giao một subagent mới (`tmp/claude-tools/prompt-cai-w26-sua-r14.md`); cả ba đã sửa ở
`be7f2064`. Test W-26: 35 xanh.

## 4. Cổng

`src/web/backend/tests` qua runner, PostgreSQL bắt buộc, trên `dec34dac`:

- lượt đủ: **679 pass / 1 fail / 1 skip**. Ca đỏ duy nhất là `test_internal_dry_run_w15…[candidate]`, thiếu fixture không theo dõi
  `tmp/w15-candidate/input.pdf` (giống lần 13 và lượt của subagent), không phải hồi quy;
- lượt bỏ riêng ca đó (`--deselect`): **679 pass / 0 fail / 1 skip**, native 0 — junit đưa cho `ghep_guard.sh`, in GUARD OK.

React không đổi nên không chạy lại.

## 5. Câu hỏi của subagent cho chủ dự án

1. Lý do xếp hàng khi hết trần ngày hiện ở cửa sổ worker; muốn hiện trên web phải thêm trường vào hợp đồng `build-1` và React.
2. `retry_unknown_within_cap=True`: một lần timeout không làm hỏng cả cuốn, nhưng phần chưa rõ chi không vào sổ ngày, nên trần 10 USD có thể
   vượt vài lần khoảng 0,36 USD. Giữ nguyên tới khi chủ dự án quyết; đổi sang `False` là một dòng.
