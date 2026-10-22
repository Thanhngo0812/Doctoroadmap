# Lõi — bàn giao backend và hỗ trợ tích hợp cuối W-14 — 2026-10-22

## 1. Mốc nhận và phạm vi

Backend/schema W-14 + W-25 **đã đạt và ghép**, không còn chặn nhóm web. Căn cứ [báo cáo điều phối](dieu-phoi-kiem-lai-w25-w14-react-w24-va-ke-hoach-2026-10-22.md):

| Mốc | Commit |
|---|---|
| Bàn giao lõi | `c00c0284ffc9df2f05f5b4234fe6b549e19f1a0c` |
| Người soát chạy cổng độc lập | `4dbfe8eb64b57ade2a4da27abc841c5c8dd29307` |
| Ghép backend lên main | `a5724597117094600152fb9a705354ebba10bde0` |
| Main đọc trong lượt hỗ trợ | `b86bde2` — tài liệu ghi nghiệm thu backend |
| React đọc để đối chiếu | `6494f51eb6b1033150d041197745b4d88a8a69da` |

Worktree hỗ trợ riêng: `tmp/w14-core-integration-notes`, nhánh `work/w14-core-integration-notes`, tạo từ main trên. Giữ nguyên `tmp/w25-build-cancellation`, `tmp/w14-build-worker` và worktree web. Lượt này chỉ đọc mã/bằng chứng và viết báo cáo; không sửa production/test, không tạo migration, không chạy lại cổng hoặc provider. Không gửi tin nhắn sang phiên khác theo yêu cầu chủ dự án.

Áp dụng skill `api-and-interface-design` để đối chiếu DTO và `documentation-and-adrs` để ghi quyết định/giới hạn; dùng báo cáo theo quy ước repo, không tạo ADR mới cho hợp đồng đã được soát.

## 2. Hai bổ sung DTO: xác nhận giữ khi web nhận main

Hai thay đổi thuộc nhánh React, commit `4c13841` và `261523e`; điều phối đã soát tính hợp lý và quyền. Main backend gốc chưa có hai trường này tại thời điểm đọc. Khi web merge main vào **worktree của web**, giữ cả hai bổ sung, đồng thời giữ nguyên CAS confirm và transaction terminal W-25. Không cherry-pick lại cả W-14 hoặc ghi đè OpenAPI của một nhánh.

| Trường | Nghĩa và quyền | UI dùng |
|---|---|---|
| `BuildView.upload_id: string \| null` | Upload của actor ứng với đúng `(build_id, course_id)`; course card chỉ tra upload khi actor là chủ. Learner card nhận `null`; poll build của người khác vẫn `not_found` | Quay lại bản dựng từ thẻ course, tìm đúng upload để xác nhận; không lấy upload nguồn dùng chung của người khác |
| `UploadView.confirmed_at: datetime \| null` | Timestamp xác nhận của chính upload đã kiểm ownership. Độc lập trạng thái build dùng chung | Vẫn cho đặt tên/xác nhận course thứ hai khi build chung queued/running/succeeded, nếu upload đó chưa xác nhận |

Hai trường chỉ thêm vào DTO/service/OpenAPI, không thêm cột: `upload.confirmed_at` đã có ở `w14_0006`. Giữ `build-1`/`upload-1`; consumer cũ vẫn đọc được. Không lộ `spent_usd`, token hoặc public media ID.

Ví dụ sau là **mẫu rút gọn**, không phải HTTP/SQL vừa chạy:

```json
{
  "contract_version": "upload-1",
  "upload_id": "upload-B",
  "confirmed_at": null,
  "build": {
    "contract_version": "build-1",
    "build_id": "shared-build",
    "course_id": "course-B",
    "upload_id": "upload-B",
    "status": "running",
    "can_cancel": false
  }
}
```

`can_cancel` ở mẫu giả định B không phải người yêu cầu build; quyền điều khiển dùng capability server, không suy từ quyền sở hữu course. UI gửi `POST /api/v1/uploads/{upload-B}/build` với `{"title":"Tên riêng của B"}` sau khi người dùng xác nhận. Không gửi `build_id`, owner hoặc doc từ body để chọn đích; service tra từ upload của actor. Xác nhận lặp không ghi đè tên/timestamp và không nhân quota/worker.

Khi quay lại trang, giữ `build_id + course_id`; có `upload_id` thì đọc upload và kiểm cả ba ID khớp. Poll/cancel/retry đều truyền `course_id`. `confirmed_at`, không phải riêng `build.status`, quyết định upload hiện tại đã xác nhận chưa. Đổi tên sau xác nhận vẫn qua PATCH course đã có.

## 3. Đối chiếu mã và bằng chứng hiện có

Không có lượt chạy mới trong bảng này. Kết quả backend độc lập đã được người soát ghi nhận; số của web bên dưới là local tại mốc React, chưa đổi thành nghiệm thu W-14 cuối.

| Ca | Assertion/evidence đã đối chiếu | Kết luận hỗ trợ |
|---|---|---|
| Huỷ commit trước confirm | `test_cancel_commit_before_confirmation_queue_write_wins`; SQL build cancelled, quota 0, tên/confirmed_at rollback | Web giữ conflict/cancelled từ server, không tự xếp hàng lại |
| Confirm commit trước huỷ | `test_confirmation_commit_before_cancel_keeps_used_quota`; quota 1 giữ nguyên | Không tự hoàn lượt |
| Huỷ khi graph/formula/media publication và trước terminal lock | `test_cancel_commit_before_terminal_prevents_success_and_preserves_receipt`, complete/incomplete; SQL cancelled, course failed/version NULL, không mail thành công; `.003` usage giả | Giữ transaction/lease và dọn đúng media mới của W-25 |
| Thứ tự commit terminal/huỷ | `test_terminal_row_read_and_cancel_follow_observed_commit_order`; SQL và `pg_blocking_pids`; bỏ khoá gây sai trạng thái cuối | Terminal commit trước thì success hợp lệ; huỷ được nhận trước thì không success |
| Hai tên/course dùng chung build | `test_same_actor_separate_courses_keep_the_confirmation_and_polling_context` và `test_reused_queued_upload_has_its_own_confirmation_and_title` của web | Đúng course/title, timestamp riêng, một quota, không thêm attempt |
| Scope upload ID | `test_build_cards_expose_only_the_viewers_upload_for_the_course` của web | Hai course có upload khác nhau; outsider 404, learner card null |
| Callback muộn/lặp | `test_cancelled_new_lease_cannot_be_published_by_late_old_receipt`, `test_heartbeat_reclaim_only_once_and_stale_callback_is_fenced` | Lease cũ chỉ ghi usage biết được một lần, không publish lên lease mới; tổng `.012` là số giả |
| Usage trong DB web | `record_usage`, receipt và các SQL W-25; web `runtime.json` ghi 5 usage rows, tổng `.002`, kết nối PG độc lập | Đây là ghi thật vào DB từ số tổng hợp; chi provider vẫn 0 USD, không gọi là tiền nhà cung cấp |

Nguồn mã: `src/web/backend/tests/test_build_cancellation_w25.py`, `test_builds_w14.py`, `wayfinder/application/builds.py`, `wayfinder/infrastructure/build_store.py`. Nguồn bổ sung DTO nằm tại `tmp/w14-react` ở commit đã ghim.

Nguồn bằng chứng:

- Backend đã được soát: [JUnit độc lập 2.163 pass/1 skip](coord-w25-w14-w24-evidence-2026-10-22/backend/full-gate.xml), [bằng chứng SQL/RED/GREEN của lõi](w25-evidence/manifest.json).
- Web local: [rà hợp đồng](C:/Users/ngoco/Desktop/Doctoroadmap/tmp/w14-react/report/w14-react-evidence/backend-contract-review.md), [18 test hợp đồng/hồi quy đạt](C:/Users/ngoco/Desktop/Doctoroadmap/tmp/w14-react/report/w14-react-evidence/build-contract2.xml), [SQL tích hợp/DB tạm đã dọn](C:/Users/ngoco/Desktop/Doctoroadmap/tmp/w14-react/report/w14-react-evidence/runtime.json). Đã đọc XML/JSON; không thực thi script web hoặc kết nối DB mới trong lượt hỗ trợ này.
- [Báo cáo React local](C:/Users/ngoco/Desktop/Doctoroadmap/tmp/w14-react/report/w14-react-tich-hop-2026-10-22.md) ghi rõ ảnh/video có trước sửa câu chữ cuối và cổng tích hợp mới còn phải chạy. Không nhận 104 React local hoặc 47 ảnh cũ là lượt kiểm cuối của nhóm lõi.

Các liên kết web trỏ tới worktree được giữ nguyên trên máy; mã và bằng chứng thuộc commit React đã ghim. Đọc trạng thái Git lúc đối chiếu: web vẫn ở `6494f51`, chưa nhận merge backend `a572459`; đây là việc nhận main của web, không phải backend còn chặn. Không sửa hoặc merge giúp trong worktree web. [Hồ sơ đối chiếu chỉ đọc và hash nguồn](w14-loi-ho-tro-evidence-2026-10-22/doi-chieu.json) phân biệt kết quả cũ với lượt hỗ trợ tài liệu này.

## 4. Phần hỗ trợ đã hoàn tất và phần chờ

Đã xác nhận hợp đồng, mốc nhận backend, các assertion/ràng buộc SQL và [ghi chú đầu vào W-15](w15-ghi-chu-dau-vao-sau-w25-2026-10-22.md). Không phát hiện lỗi W-14 mới qua đối chiếu này; không sửa mốc đã duyệt.

Nhóm web tiếp tục nhận main, giữ DTO, loại basetemp khỏi Git theo điều phối và chạy cổng/browser mới trên đỉnh tích hợp. Nếu có lỗi mới cần mã sửa, ghi repro rồi làm nhánh sửa phạm vi cụ thể để người soát nhận lại; không sửa nóng main. Backend đã ghép không được liệt kê là điểm chặn web.

W-25 đạt không tự đóng W-14. W-15 chưa mở chạy thật; chờ W-14 đầu-cuối được nghiệm thu và đề xuất/dry-run/duyệt tiền mới. Chi ngoài trong lượt hỗ trợ này: **0 USD**.
