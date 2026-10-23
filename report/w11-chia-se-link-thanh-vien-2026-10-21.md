# W-11 — Chia sẻ bằng link và thành viên, 2026-10-21

**Phạm vi đợt này theo chỉ thị chủ dự án:** hoàn tất service/API/UI, lưu tiến trình rồi dừng chờ. Chưa migration hoặc nghiệm thu tích hợp cuối.

## Nhánh và phụ thuộc

- Worktree `C:/Users/ngoco/Desktop/Doctoroadmap/tmp/w11-share-links`, nhánh `work/w11-share-links`, tạo từ mốc W-07 **`cd1ecb83f5f261af6e8911cf415f366c7b786752`**. Main lúc nhận là `eb6af08`, chưa ghép W-07. Theo quy trình, vé cần mã chưa ghép được tách từ nhánh đó; chỉ điều phối ghép main.
- Chủ dự án chốt tuyến **W-14 ghép trước, W-11 nối sau**. Nhánh W-14 có `w14_0006`; W-11 sẽ tạo `w11_0007 → w14_0006` sau khi nhận main bàn giao. Đợt này **chưa tạo migration** hoặc tự nhận mã W-14 chưa được điều phối ghép.
- Giữ nguyên W-07/W-06, snapshot/ZIP, không liên kết thư mục, không đụng `tmp/t01a-clean-ff797eb`. Không sửa vé/kế hoạch/handoff.

## Phạm vi triển khai

SharingService và các endpoint theo vé W-11: tạo/liệt kê/thu hồi link, preview khách, tham gia bằng link, danh sách thành viên, xoá thành viên và rời khoá. UI gồm hộp chia sẻ của chủ khoá, `/join/:token`, `/khoa-hoc/:cid/thanh-vien` và liên kết từ lộ trình. Không làm mời email W-12, tiến độ lớp W-18 hoặc xoá khoá W-20.

[Hợp đồng API](w11-evidence/api-contract.md) đã chốt trước khi frontend nối:

- Token ngẫu nhiên32byte, DB chỉ lưu SHA-256 và6ký tự cuối. URL đầy đủ chỉ có trong phản hồi tạo, dialog giữ tạm trong bộ nhớ và xoá khi đóng. Danh sách không trả token/URL.
- Hạn mặc định7ngày, explicitnull là không hết hạn; max_usesnull không giới hạn. Giá trị không hợp lệ trả422.
- Preview link sai/thu hồi/hết hạn/hết lượt dùng chung lỗi `link_invalid`, không lộ nguyên nhân. Đã là thành viên có thể gọi join lặp mà không trừ lượt; vẫn từ chối link thu hồi/hết hạn, chỉ bỏ kiểm hết lượt cho người đã là thành viên. Người tạo khoá giữ roleowner khi gọi join lặp.
- Tham gia mới khoá hàng link rồi khoá course; membership/use_count/audit trong cùng giao dịch. Xoá/rời không xoá dữ liệu Pha B; vào lại bằng link mới là membership mới và tính một lượt, tiến độ/phiên cũ giữ nguyên.
- Chủ khoá được quản lý link và danh sách thành viên đầy đủ. Thành viên thường chỉ nhận tên chủ khoá/số người, không nhận danh tính người học khác. Chủ khoá không rời hoặc tự xoá mình.
- API sử dụng actor phiên, cookie/Origin/CSRF hiện có; không nhận owner/doc/version từ client. Preview là ngoại lệ công khai theo token, không miễn rộng guard course.

## Thiết kế và quyền riêng tư

Tiếp tục `design-taste-frontend` app screen, token/logo Artboard24/28/Be Vietnam Pro và quyết định W-24 hiện hành. Giữ nhãn “tài liệu”/“bài học”, focus/keyboard và44px; không thêm nội dung mẫu như dữ liệu thật. [Quyết định UI](w11-evidence/design-notes.md).

Access filter che toàn requesttarget chứa đường `/join/`, kể cả `next` đã URL encode một hoặc hai lần; giữ method/status. Header trang join/auth quay lại và API nhạy cảm dùng no-referrer/no-store. Test dùng token tổng hợp, không credentials chủ dự án. Token thật của link kiểm thử không lưu report, log hoặc kho trình duyệt.

## Dữ liệu và kiểm tập trung

Đã cài dependency và chép3.144tệp phát triển theo hai manifest/SHA-256; bỏ learnerstoreCLI, không đọc live/tập giữ lại. [Log chép](w11-evidence/fixture-copy.log).

Các test service/HTTP dùng fake clock/Mailer/model và PostgreSQL UUID riêng; bảng share_link tạm được tạo bằng metadata để phát triển trong lúc chờ tuyến migration. **Đây không phải kiểm migration hoặc bằng chứng nghiệm thu W-11 đầu-cuối.** Test React dùng phản hồi giả để kiểm UI, không gán là API thật.

## Kết quả tại điểm dừng

- Backend/service/API: commit **`ed3e53ce52980188ab7ada8fc7e48a4e0739fa2f`**. OpenAPI đã xuất từ app với dịch vụ giả, không khởi tạo provider.
- React và menu khách: commit **`fb7b4973efc1da885cff7dd719e0b8bb7883b6f4`**. Mã được kiểm trong working tree ngay trước commit; hai commit không thay nội dung sau các lần kiểm tương ứng. Commit tài liệu tiếp theo chỉ lưu README/báo cáo/bằng chứng.
- Kiểm tập trung backend: **19 đạt, 0 bỏ qua**, native exit **0**. Gồm 14 test sharing (có PostgreSQL thật, race lượt cuối, rollback khi audit hỏng, xoá/tham gia lại giữ Pha B), 3 test che access log/header riêng tư, 2 test inventory route và phát hiện route mới bỏ guard. [Log](w11-evidence/checkpoint-backend.log), [JUnit](w11-evidence/checkpoint-backend.xml).
- React: **13 đạt**, native exit **0**, dữ liệu HTTP giả. [Log](w11-evidence/checkpoint-react.log), [JUnit](w11-evidence/checkpoint-react.xml).
- TypeScript/Vite build: native exit **0**. [Log](w11-evidence/checkpoint-build.log).
- Menu khách có test RED với assertion thấy account-menu rỗng, rồi GREEN sau sửa. [RED](w11-evidence/guest-shell-red.xml), [GREEN](w11-evidence/guest-shell-green.xml). Lỗi hồi đáp muộn/dialog đổi khoá và mutation lỗi trùng đã có hồi quy; [ghi nhận RED/GREEN](w11-evidence/react-red-lifecycle.md). `red.xml` ghi RED khi phương thức còn stub, không coi là phép phá guard. `privacy-red.*` là lỗi collection lúc module chưa tồn tại; `privacy-doc-green.*` có lỗi thiếu thư mục basetemp trước khi fixture chạy. Các lần lỗi được giữ để đối chiếu; kết quả cuối là `checkpoint-*`.
- Đã soát mã bằng `code-review-and-quality`, có [rà soát riêng tư độc lập](w11-evidence/privacy-review.md). Đã sửa các phát hiện: account menu rỗng cho khách, trạng thái link hết hạn/hết lượt, lỗi hiển thị trùng và phản hồi đến muộn sau đóng dialog/đổi route. URL một lần được xoá khi đóng bằng nút, Escape, prop hoặc đổi khoá; không lưu localStorage/sessionStorage.
- Áp dụng `design-taste-frontend` cùng token/font/logo và hướng dẫn thiết kế W-24 hiện có. [Direction đã lưu](w11-evidence/design-direction.json), [quyết định áp dụng/điều chỉnh](w11-evidence/design-notes.md). Chưa có look-and-fix/inspector trên browser thật, ảnh/video hoặc audit accessibility/network; để đợt tích hợp tiếp theo.
- **Đã dừng theo yêu cầu chủ dự án.** Không chạy cổng toàn repo, browser hoặc migration; chưa nghiệm thu/đóng vé, chưa ghép/push main. Không gọi mô hình, gửi thư hoặc upload Cloudinary; chi phí dịch vụ ngoài **0 USD**. README đã ghi vị trí W-11, giới hạn schema và hướng dẫn mở bản W-07 đang có.

### Lệnh kiểm tập trung

Chạy từ gốc worktree W-11, dùng `cmd.exe` để giữ native exit code và redirect log. Mỗi lần dùng basetemp mới.

```bat
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe scripts/w05_run_tests.py src/web/backend/tests/test_w11_sharing.py src/web/backend/tests/test_share_link_privacy_w11.py src/web/backend/tests/test_courses_w06.py::test_every_cid_route_hides_private_course_from_outsiders_including_admin src/web/backend/tests/test_courses_w06.py::test_route_inventory_catches_a_new_unguarded_route -o addopts= -q --assert=plain --basetemp=tmp/w11-checkpoint-backend --junitxml=report/w11-evidence/checkpoint-backend.xml
npm.cmd --prefix src/web/frontend test -- src/Sharing.test.tsx src/CourseShellGuest.test.tsx --pool=threads --maxWorkers=1 --reporter=junit --outputFile=../../../report/w11-evidence/checkpoint-react.xml
npm.cmd --prefix src/web/frontend run build
```

**Điểm tiếp tục:** `work/w11-share-links` trong worktree hiện tại. Giữ nguyên mọi snapshot/worktree; không chạy lại hay mở service cho tới khi chủ dự án nhắn tiếp. Phần còn lại bên dưới là công việc tương lai.

## Khi chủ dự án nhắn tiếp

1. Nhận commit main có W-07 và W-14 đã được điều phối ghép, xử lý composition theo diff, không lấy đè nhánh khác.
2. Tạo đúng một migration share_link nối `w14_0006`; bỏ schema scaffolding khỏi đường nghiệm thu, kiểm một Alembichead/upgrade và ràng buộc.
3. Chạy mutation tuần tự và phục hồi nguồn; kiểm PostgreSQL tranh lượt1/capacity/idempotency/auditrollback/remove/rejoin, inventory tất cả route.
4. Chạy cổng toàn repo/React/build trên commit chốt; browser UUIDPG thật với provider/Mailer/MediaStore giả. Kiểm clipboard, authreturn, memberremove/leave, ảnh sáng/tối390/768/1280, video và audit. Che bearer token trong mọi bằng chứng.
5. Hoàn thiện báo cáo/bằng chứng, bàn giao điều phối soát. Không tự đóng vé hoặc ghép/push main.
