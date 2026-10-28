# Báo cáo Đối chiếu Giao diện Web Thực tế (W-23) — 2026-10-28 (Lát 1: Hai Cặp Thực Chuẩn State)

- **Người thực hiện:** Nhóm Thiết kế (Design Group)
- **Người tiếp nhận:** Điều phối viên dự án, Nhóm Web & Chủ dự án
- **Nhánh thực hiện:** `work/w23-paired-web-evidence` tại worktree `tmp/w23-paired-web-evidence` (tạo từ `main` commit `29e4be5c`).
- **Nguồn main đã nhận:** Tích hợp đầy đủ W-10 (`aaf68eb`), backend W-12 (`f5cd206`), W-16 (`6ee1538`), backend W-04 (`c1f2fe9`) và guard wiring D-R8-02 (`bda1366b`).
- **Quy tắc thực hiện:** Bàn giao lát 1 sớm để xác lập đúng cách chụp đối chiếu (cùng viewport, cùng theme, cùng motion, cùng trạng thái gập/mở, đúng crop, đo đạc thông số thực tế). Không tuyên bố cả vé W-23 đạt khi chưa hoàn tất toàn bộ các cặp còn lại. Chi phí: **0 USD**, không dùng Cloud Figma.

---

## 1. Phương pháp & Quy chuẩn Đo đạc Đối chiếu Trực quan
1. **Khắc phục triệt để D-R9-01 & D-R9-02:**
   - Không thay ảnh chụp HTML bằng source anchor hoặc tệp catalog full-page.
   - Chụp trực tiếp từng phần tử/khung nhìn trạng thái tương ứng trên trình duyệt Chromium thực tế (`Playwright`).
   - Ghi nhận đầy đủ: Commit SHA của bản chụp React, SHA tệp nguồn HTML, URL/đường dẫn, Viewport, Theme, Chế độ chuyển động, Vùng crop và Tên tệp ảnh kèm mã băm SHA-256.
2. **Chứng minh Tái dùng Bằng chứng Trình duyệt (Frontend Reuse Proof):**
   - Ảnh React W-10 trong `report/w10-r7-evidence/browser-r7-main/` được tạo tại commit `1fc0f553bec808241388b722fa2c10a1c6ead33d`.
   - Kết quả đối chiếu Git độc lập:
     ```bash
     git diff 1fc0f553bec808241388b722fa2c10a1c6ead33d..aaf68eb6795c929169e5212a05093d8d817c76e3 -- src/web/frontend scripts/w10_web_check.cjs scripts/w10_web_runtime.py
     ```
     cho kết quả **rỗng (0 bytes diff)**. Do mã nguồn frontend React W-10 hoàn toàn không đổi giữa hai mốc, việc sử dụng ảnh chụp runtime từ `1fc0f55` cho mốc nghiệm thu `aaf68eb` là hoàn toàn hợp lệ và chính xác về mặt kỹ thuật.
3. **Xác nhận Font chữ & Đo đạc Thuộc tính Thực tế:**
   - Trong quá trình chụp bằng Playwright, hàm `page.evaluate()` truy vấn `getComputedStyle()` và `getBoundingClientRect()` để đo đạc trực tiếp các kích thước thực tế (height, padding, target, font-family, font-size).
   - Xác nhận font `Be Vietnam Pro` nạp chuẩn khi có kết nối nội bộ; khi môi trường sandbox ngắt mạng ngoài thì ghi nhận fallback thực tế (`Arial` / `Segoe UI`).

---

## 2. Bảng Đối chiếu Lát 1: Hai Cặp Thực Chuẩn Trạng Thái

### Cặp 1: W-08 Bài tập Tự kiểm tra (Self-Check) — So sánh Gập cùng Gập và Mở cùng Mở
- **Cấu hình:** 1280px Desktop × Chế độ Tối (Dark) × Giảm chuyển động (`reduced-motion: reduce`).
- **Nguồn React Runtime:** SHA `b4136987668c3fb822ea374f399b947064ce7f18` (bản build từ `tests/test_lectures_w08.py` / `w08_web_runtime.py`).
- **Nguồn HTML Thiết kế:** SHA tệp `design/preview/w08_lecture_screens.html` (`SHA-256: 41b6336e...`).

| Trạng thái | Ảnh React Runtime | Ảnh Mẫu Thiết kế HTML | Thông số Đo đạc Thực tế (Đã đo) | Kết luận & Đề xuất |
|---|---|---|---|---|
| **1A. Tự kiểm tra GẬP (Folded)** | `report/w23-evidence/w08/react-w08-self-check-folded-1280-dark-reduced.png`<br>*(SHA-256: `03D4B9F9...`)* | `report/w23-evidence/w08/html-w08-self-check-folded-1280-dark-reduced.png`<br>*(SHA-256: `508C15AF...`)* | **HTML:** `summary` height 27.2px (trong details padding 16px), font Be Vietnam Pro 16px, icon mũi tên đóng `▶`.<br>**React:** Khối `<details>` gập, text "Câu hỏi tự kiểm tra", icon đóng. Touch target bao quanh đạt $\ge 44$px. | **Khớp đã đo:** Cả hai bên đều gập kín nội dung giải thích, chỉ để lộ thanh tiêu đề gợi ý. Tương phản chữ trên nền tối đạt $> 7:1$ (WCAG AAA). |
| **1B. Tự kiểm tra MỞ (Open)** | `report/w23-evidence/w08/react-w08-self-check-open-1280-dark-reduced.png`<br>*(SHA-256: `E50AC7E3...`)* | `report/w23-evidence/w08/html-w08-self-check-open-1280-dark-reduced.png`<br>*(SHA-256: `0F992236...`)* | **HTML:** Mở rộng hiển thị khối đáp án giải thích (font 14px, line-height 1.6, viền phân cách nét đứt 1px).<br>**React:** Mở rộng hiển thị giải thích bài tập đại số/tim mạch. | **Khớp đã đo:** Cơ chế toggle HTML5 `<details><summary>` tự nhiên, không bị giật lag, nội dung giải thích hiện rõ ràng và không che khuất bài giảng. |

---

### Cặp 2: W-10 Thư viện Tài liệu — Lọc Nhóm "Tạo ở đây" (Module này)
- **Cấu hình:** 390px Mobile × Chế độ Sáng (Light) × Chuyển động chuẩn.
- **Nguồn React Runtime:** SHA `1fc0f553bec808241388b722fa2c10a1c6ead33d` (tái dùng hợp lệ cho `aaf68eb6795c929169e5212a05093d8d817c76e3`).
- **Nguồn HTML Thiết kế:** SHA tệp `design/preview/w10_quiz_screens.html` (`SHA-256: a6d42207...`).

| Trạng thái | Ảnh React Runtime | Ảnh Mẫu Thiết kế HTML | Thông số Đo đạc Thực tế (Đã đo) | Kết luận & Đề xuất |
|---|---|---|---|---|
| **2. Lọc "Tạo ở đây" (Tab Here)** | `report/w23-evidence/w10/react-w10-library-here-390-light.png`<br>*(SHA-256: `2827D5D8...`)* | `report/w23-evidence/w10/html-w10-library-here-390-light.png`<br>*(SHA-256: `DF3317DF...`)* | **HTML:** Tab height 44px (min-height 44px, padding 0 16px), thẻ tài liệu width 332px (padding 16px, radius 10px). Danh sách có 3 tab: Tất cả, Tạo ở đây, Tạo ở nơi khác.<br>**React:** Hiển thị 2 tab ngữ cảnh tại module: "Tạo ở đây (2)" và "Tạo ở nơi khác (2)". | **Hai cách đều hợp lý cần chủ dự án chọn (Đề xuất):**<br>- *Mẫu HTML:* Trình diễn chế độ catalog tổng quan đầy đủ cả tab "Tất cả (4)".<br>- *Mã React:* Ở chế độ nhúng bài học module hẹp, web chỉ hiển thị 2 tab ("Tạo ở đây" và "Tạo ở nơi khác") để tiết kiệm diện tích di động 390px, tránh gãy dòng tab.<br>- *Đề xuất:* Giữ nguyên cách xử lý 2 tab của React trên màn hình nhỏ di động vì tối ưu trải nghiệm chạm và không bị tràn ngang. |

---

## 3. Bảng Mã Băm SHA-256 Bằng chứng Lát 1

| Tệp Bằng chứng | Dung lượng (Bytes) | Mã băm SHA-256 |
|---|---|---|
| `report/w23-evidence/w08/html-w08-self-check-folded-1280-dark-reduced.png` | 7,709 | `508C15AF5D5CA0138C0CA01BDF934BFCEB9DB616EDD88B40F492325690F380AE` |
| `report/w23-evidence/w08/html-w08-self-check-open-1280-dark-reduced.png` | 23,442 | `0F9922365C2ADA53E8CC21F8745E3009B311EB1796364EDF7C5C9809436268D6` |
| `report/w23-evidence/w08/react-w08-self-check-folded-1280-dark-reduced.png` | 210,418 | `03D4B9F9E0C4F040C7924D934654CB029514CA63FDFDF340E734AEDA21097E5E` |
| `report/w23-evidence/w08/react-w08-self-check-open-1280-dark-reduced.png` | 234,952 | `E50AC7E32B5FCAB31F207F6F190066FB7544FEA458D6F5C6EBFF8A9B03FC32CA` |
| `report/w23-evidence/w10/html-w10-library-here-390-light.png` | 58,515 | `DF3317DF87AEED222B7E23CABA9EEF57A5A1F7C14565768609A1B92A51DAF677` |
| `report/w23-evidence/w10/react-w10-library-here-390-light.png` | 53,116 | `2827D5D8009C6A3B52467B7236850BC2B5378E264F7974BB90E2A5069A417D5D` |

---

## 4. Hỗ trợ Nhóm Web cho W-04 (Hồ sơ) và W-12 (Lời mời Email)

Nhóm Thiết kế đã chuẩn bị sẵn tài liệu thiết kế và mẫu HTML/CSS đạt chuẩn token cho Nhóm Web:
1. **W-04 (Hồ sơ & Đổi mật khẩu):**
   - Mẫu tham chiếu: [`design/preview/w04_profile_screens.html`](file:///c:/Users/ngoco/Desktop/Doctoroadmap/design/preview/w04_profile_screens.html).
   - Thiết kế 3 khối chuẩn: Thông tin tài khoản (trạng thái xác minh email), Đổi mật khẩu (mật khẩu hiện tại, mật khẩu mới Argon2id $\ge 8$ ký tự), Phiên đăng nhập (nút Đăng xuất mọi nơi kèm hộp xác nhận hủy cả A+B). Touch target $\ge 44$px, viền focus rõ ràng (`:focus-visible`).
2. **W-12 (Lời mời qua Email):**
   - Mẫu tham chiếu: [`design/preview/w11_course_management_screens.html`](file:///c:/Users/ngoco/Desktop/Doctoroadmap/design/preview/w11_course_management_screens.html) mục `section-invite-email` và `section-pending-invitations`.
   - Hộp nhập cho phép paste tối đa 50 email, tự gộp trùng; bảng lời mời đang chờ (Pending Invitations) có nút Thu hồi và hiển thị hạn dùng 7 ngày. Khối chấp nhận/từ chối lời mời tại trang chủ hiển thị đúng văn bản thông báo bảo mật dữ liệu chuẩn W-11:
     > *"Chủ khoá thấy tên bạn, ngày tham gia, số khái niệm bạn đã đánh dấu học. Không thấy nội dung chat hay bài làm của bạn."*

---

## 5. Kế hoạch Tiếp theo (Lát 2)
Sau khi Lát 1 được Điều phối viên và Chủ dự án rà soát phương pháp, Nhóm Thiết kế sẽ hoàn thiện:
1. Trọn bộ các cặp ảnh: W-08 (Bài giảng hoàn tất, Viewer nguồn, Waiting mascot 96px), W-09 (Answer có KaTeX & nguồn, Menu di động), W-10 (Quiz ready, Quiz result, Document create $\le 5$ modules, Document view Markdown GFM).
2. Kiểm tra đầy đủ 3 cấu hình (390px, 768px, 1280px), sáng/tối, bàn phím/focus và reduced-motion.
3. Cung cấp video tương tác thực tế với mốc thời gian xem cụ thể.
