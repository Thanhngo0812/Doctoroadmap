# Báo cáo Đối chiếu Giao diện Web Thực tế (W-23) — Sửa Lát 1 theo Review R11 (2026-10-28)

- **Người thực hiện:** Nhóm Thiết kế (Design Group)
- **Người tiếp nhận:** Điều phối viên dự án, Nhóm Web & Chủ dự án
- **Nhánh thực hiện:** `work/w23-paired-web-evidence` tại worktree `tmp/w23-paired-web-evidence`.
- **Mốc thiết kế xem xét:** `60412c87df1b684c97e6148d1f88f578d5202322` (bản sửa theo Review R11).
- **Mốc main local đã nhận:** `b2fedda1f4453fc79880f1203cfa70e07aa67db1` (đã merge `main` sạch sẽ vào nhánh thiết kế).
- **Phạm vi & Nguyên tắc:** Khắc phục triệt để hai yêu cầu Required của Review R11 (D-R11-01 và D-R11-02). Giữ nguyên các mốc token/branding/math, bằng chứng cắt cúp 3 ảnh React chuẩn từng pixel, đính chính AA/target/no-lag, và copy W-04/W-12 đã được hội đồng chấp thuận. Chi phí: **0 USD**, không dùng Cloud Figma.

---

## 1. Khắc phục D-R11-01: Ràng buộc Nguồn Hiện hành & Chứng minh Tái dùng Hẹp (Narrow Leaf Reuse Proof)

### 1.1. Minh bạch hóa nhãn nguồn ảnh React Runtime lịch sử
Ba ảnh cắt cúp React được gán nhãn chính xác là **ảnh cắt từ runtime lịch sử** (`historical-runtime-crop`):
1. `react-w08-self-check-folded-crop.png` (680×164px): Cắt từ `ready-1280-dark-reduced.png` tại commit `b4136987668c3fb822ea374f399b947064ce7f18` (URL harness: `http://127.0.0.1:8018/courses/c1/modules/m1/lectures/n1`).
2. `react-w08-self-check-open-crop.png` (680×206px): Cắt từ `self-check-open-1280-dark-reduced.png` tại commit `b4136987668c3fb822ea374f399b947064ce7f18` (cùng URL harness trên).
3. `react-w10-library-here-crop.png` (366×478px): Cắt từ `library-here-390-light.png` tại commit `1fc0f553bec808241388b722fa2c10a1c6ead33d` (URL harness: `http://127.0.0.1:8020/courses/c1/modules/m1`).

Việc cắt cúp vùng thành phần `.lecture-self-check` và `.content-library` đã loại bỏ hoàn toàn các trạng thái ngoài ý muốn ở phần còn lại của trang (như khối prerequisite mở ở ảnh W-08 cũ).

### 1.2. Chứng minh tái dùng hẹp (Narrow Leaf-Source & Style Reuse Proof) với `main` hiện hành
Mặc dù toàn bộ tệp `Learning.tsx` và `ContentLibrary.tsx` có các bổ sung chức năng mới trên `main` hiện hành (`b2fedda1`), các thành phần lá (leaf components) được đối chiếu thực tế có **diff 0 bytes** về cấu trúc DOM và CSS:

#### A. Khối Tự kiểm tra W-08 (`.lecture-self-check`):
- **Cấu trúc JSX:** Tại `src/web/frontend/src/Learning.tsx` (dòng 117–120):
  ```tsx
  {lecture?.self_check && !streaming && <section className="lecture-self-check" aria-labelledby="self-check-title">
    <h2 id="self-check-title">Tự kiểm tra</h2><LectureMarkdown text={lecture.self_check.question_md} sources={lecture.sources} onSource={pages ? openSource : undefined} />
    <details><summary>Xem đáp án</summary><LectureMarkdown text={lecture.self_check.answer_md} sources={lecture.sources} onSource={pages ? openSource : undefined} /></details>
  </section>}
  ```
- **Quy tắc CSS:** Tại `src/web/frontend/src/learning.css` (dòng 62–64):
  ```css
  .lecture-self-check { border-block: 1px solid var(--color-border); padding-block: var(--space-6); }
  .lecture-self-check summary { display: flex; align-items: center; min-height: 44px; font-weight: 600; color: var(--color-primary); cursor: pointer; }
  .lecture-self-check details[open] summary { margin-bottom: var(--space-3); }
  ```
- **Kết quả so sánh mã:** Diff giữa commit lịch sử `b4136987` và `main` hiện hành trên chính xác khối `.lecture-self-check` và quy tắc CSS là **0 bytes diff**. Việc `Learning.tsx` bổ sung `AssistantDock`, `ContentLibrary` ở cuối trang và thêm hàm `onAsk` vào `Lesson` hoàn toàn không chạm tới DOM, hành vi toggle hoặc kiểu dáng của `.lecture-self-check`. Tự kiểm tra không bị hỏng bởi các thay đổi ngoài phạm vi này.

#### B. Khối Thư viện Tài liệu W-10 (`.content-tabs` & `.content-library-list`):
- **Cấu trúc JSX:** Tại `src/web/frontend/src/ContentLibrary.tsx` (dòng 45–50):
  ```tsx
  <div className="content-library-filters">
    {moduleId ? <div className="content-tabs" role="group" aria-label="Nơi tạo nội dung">
      <button type="button" aria-pressed={group === 'here'} onClick={() => setGroup('here')}>Tạo ở đây <span>{rows.filter(row => row.group === 'here').length}</span></button>
      <button type="button" aria-pressed={group === 'elsewhere'} onClick={() => setGroup('elsewhere')}>Tạo ở nơi khác <span>{rows.filter(row => row.group === 'elsewhere').length}</span></button>
    </div> : <label className="content-all"><input type="checkbox" checked={all} onChange={event => setAll(event.target.checked)} />Tất cả nội dung trong khoá</label>}
  </div>
  ```
- **Quy tắc CSS:** Tại `src/web/frontend/src/content.css`:
  ```css
  .content-tabs button { min-height: 44px; padding: var(--space-2) var(--space-3); font: inherit; ... }
  ```
- **Kết quả so sánh mã:** Diff giữa mốc nghiệm thu `aaf68eb` và `main` hiện hành trên khối `.content-tabs`, logic lọc (`group === 'here'`) và danh sách thẻ `.content-library-list` là **0 bytes diff**. Bổ sung mới `<UsageLimits usage={usage.value} />` nằm ở khoảng giữa header và filter, không làm thay đổi cấu trúc, kích thước nút tab 44px hay danh sách hiển thị của nhóm "Tạo ở đây".

### 1.3. Ghi nhận số đo thực tế đo lường trên React Runtime
- **React W-08 Tự kiểm tra (Gập):**
  - Vùng bấm `<summary>`: Chiều cao thực tế đạt **44.0px** (`min-height: 44px; display: flex; align-items: center; cursor: pointer;`).
  - Tiêu đề `<h2>`: Cỡ chữ 20px / 1.25rem, font-weight 700.
  - Câu hỏi: Cỡ chữ 16px / 1rem, line-height 1.6, màu chữ `#e8edf2`, đặt bên ngoài `<details>`.
  - Nhãn toggle: Văn bản "Xem đáp án", không có biểu tượng tam giác.
  - Màu sắc: Chữ `#29a9ff` trên nền tối `#0d1117` / `#161b22`, tỷ lệ tương phản $\approx 6.77:1$ (WCAG AA).
- **React W-08 Tự kiểm tra (Mở):**
  - Nội dung mở rộng: Hiển thị văn bản đáp án ngắn *"Bằng 1."* (cỡ chữ 16px, màu `#e8edf2`), tăng chiều cao khung thành phần từ 164px lên 206px (+42px).
- **React W-10 Thư viện "Tạo ở đây":**
  - Nút tab "Tạo ở đây (2)": Chiều cao thực tế đạt **44.0px** (`min-height: 44px`, `padding: 8px 12px`, `border-radius: 6px`, màu nền active `#f6f8fa`).
  - Danh sách thẻ: 2 thẻ tài liệu hiển thị (chiều rộng 332px, padding 16px, viền phân cách 1px `#d0d7de`).

---

## 2. Khắc phục D-R11-02: Một Receipt cho Đúng Một Run & Phân Định Rõ Kích Thước PNG

### 2.1. Phân định rõ hai ngữ cảnh chạy (Run Contexts)
Để bảo đảm tính trung thực tuyệt đối và không gán ngược bằng chứng font offline cho ảnh tham chiếu online:
1. **Lượt chạy Tham chiếu Tác giả (Canonical Reference Run — Online Font State):**
   - **Môi trường:** Chromium / Playwright trên Windows x64.
   - **Trạng thái mạng:** Cho phép kết nối tải font thiết kế `Be Vietnam Pro` từ Google Fonts (`fonts.googleapis.com`).
   - **Trạng thái font:** `document.fonts.status = "loaded"`, các font face `Be Vietnam Pro` được nạp đầy đủ vào `document.fonts`.
   - **Tài sản xuất xưởng:** Ba tệp PNG tham chiếu chuẩn được tái dùng nguyên vẹn từ mốc `24538ae0`:
     - `html-w08-self-check-folded-1280-dark-reduced.png` (808×62px, 7,709 B, SHA-256: `508c15af...`).
     - `html-w08-self-check-open-1280-dark-reduced.png` (808×154px, 23,442 B, SHA-256: `0f992236...`).
     - `html-w10-library-here-390-light.png` (366×808px, 58,515 B, SHA-256: `df3317df...`).
2. **Lượt chạy Kiểm thử Ngoại tuyến Độc lập (Independent Offline Reproduction Run):**
   - **Môi trường:** Chromium với cờ chặn toàn bộ yêu cầu mạng ngoài: `context.route(/^https?:/, route => route.abort())`.
   - **Trạng thái mạng:** Ngoại tuyến hoàn toàn; chỉ đọc tệp cục bộ.
   - **Trạng thái font:** Không tải được font Google Fonts từ xa; `document.fonts.faces` rỗng `[]`; CDP ghi nhận font hiển thị hệ thống thay thế: `Segoe UI` (78 glyphs) + `Segoe UI Emoji` (1 glyph) cho W-08; `Arial` (15 glyphs) cho W-10.
   - **Ghi nhận receipt:** Toàn bộ dữ liệu font fallback này được lưu riêng tại trường `offlineFallbackAudit` trong receipt JSON, minh chứng rằng kịch bản chạy độc lập cục bộ thành công mà không làm nhiễu thông số font của ảnh tham chiếu chuẩn.

### 2.2. Tách bạch Kích thước Decoded PNG và Hình chữ nhật CSS (Floating Rect)
Tránh việc làm tròn số học (`Math.round`) gây lệch 1px giữa receipt và tệp ảnh thực tế:
- **Kích thước Decoded PNG (`decodedPngDimensions`):** Đọc trực tiếp từ chunk IHDR của tệp PNG (số nguyên pixel chuẩn xác).
- **Hình chữ nhật CSS (`elementBoundingRect`):** Lưu tọa độ và kích thước dấu phẩy động thực tế từ `getBoundingClientRect()`.

| Tệp Bằng chứng | Kích thước Decoded PNG | Kích thước Hình chữ nhật CSS (`elementBoundingRect`) | Dung lượng (Bytes) |
|---|---|---|---|
| `html-w08-self-check-folded-1280-dark-reduced.png` | **808 × 62 px** | `x: 236.0, y: 419.14, w: 808.0, h: 61.19` | 7,709 B |
| `html-w08-self-check-open-1280-dark-reduced.png` | **808 × 154 px** | `x: 236.0, y: 419.14, w: 808.0, h: 153.58` | 23,442 B |
| `html-w10-library-here-390-light.png` | **366 × 808 px** | `x: 12.0, y: 92.98, w: 366.0, h: 807.0` | 58,515 B |
| `react-w08-self-check-folded-crop.png` | **680 × 164 px** | Crop Rect: `x: 446, y: 1064, w: 680, h: 164` | 10,730 B |
| `react-w08-self-check-open-crop.png` | **680 × 206 px** | Crop Rect: `x: 446, y: 1214, w: 680, h: 206` | 12,773 B |
| `react-w10-library-here-crop.png` | **366 × 478 px** | Crop Rect: `x: 12, y: 72, w: 366, h: 478` | 40,594 B |

---

## 3. Bảng Đối chiếu Hai Cặp Thực tế & Quyết định Đề xuất

| Cặp đối chiếu | Ảnh Cắt Cúp React Runtime (Lịch sử) | Ảnh Mẫu Thiết kế HTML (Tái dùng chuẩn) | Thông số Đo đạc & Phân loại Theo W-23 |
|---|---|---|---|
| **1. W-08 Tự kiểm tra (GẬP)** | `report/w23-evidence/w08/react-w08-self-check-folded-crop.png`<br>*(Decoded: 680×164px)* | `report/w23-evidence/w08/html-w08-self-check-folded-1280-dark-reduced.png`<br>*(Decoded: 808×62px)* | **HTML:** `summary` height 27.2px (< 44px), contrast 6.77:1 (WCAG AA). Câu hỏi đặt trong summary kèm marker `▶`.<br>**React:** Câu hỏi đặt ngoài summary, text "Xem đáp án" không marker, target $\ge 44$px.<br>**Phân loại:** Khác biệt UX cần Chủ dự án chọn (Lựa chọn 4). |
| **2. W-08 Tự kiểm tra (MỞ)** | `report/w23-evidence/w08/react-w08-self-check-open-crop.png`<br>*(Decoded: 680×206px)* | `report/w23-evidence/w08/html-w08-self-check-open-1280-dark-reduced.png`<br>*(Decoded: 808×154px)* | **HTML:** Mở rộng hiển thị đoạn giải thích chi tiết cơ chế tim mạch.<br>**React:** Mở rộng hiển thị đáp án ngắn "Bằng 1.".<br>**Phân loại:** Cơ chế toggle `<details>` hoạt động chuẩn trên cả hai bên. |
| **3. W-10 Thư viện "Tạo ở đây"** | `report/w23-evidence/w10/react-w10-library-here-crop.png`<br>*(Decoded: 366×478px)* | `report/w23-evidence/w10/html-w10-library-here-390-light.png`<br>*(Decoded: 366×808px)* | **HTML:** 3 tab catalog ("Tất cả", "Tạo ở đây", "Tạo ở nơi khác"), tab height 44px, card width 332px.<br>**React:** 2 tab module ("Tạo ở đây", "Tạo ở nơi khác"), tab height 44px.<br>**Phân loại:** Đề xuất giữ 2 tab của React trên 390px (Lựa chọn 4). |

---

## 4. Danh mục Đầy đủ Tệp Nguồn, Tệp Bằng chứng & Mã Băm SHA-256 Chuẩn Xác

### 4.1. Tệp nguồn thiết kế
- `design/preview/w08_lecture_screens.html`:
  - Git LF blob SHA-256: `ef89ee7e58fde9ca8eed7bf0a580cb79ab75958dec55e5a62be0b2fcac9f2fe7`
  - Worker raw CRLF SHA-256: `066de4625bb71316916da7dee7f06ffb636897c32d619c0cde395c79a3987a13`
- `design/preview/w10_quiz_screens.html`:
  - Git LF blob SHA-256: `a6d42207d1c4f3915734b9efff6c757442ca6fefead5bec61706b9eddf7c0ecf`
  - Worker raw CRLF SHA-256: `f2dea29c39708a24cf72e4617731e8d7dea588d4d2d6fc2aa75c4087d89ca989`
- `design/tokens/tokens.css`:
  - Git LF blob SHA-256: `5ce8eafee0b298032b57e3d4b2afb41a28850b6c30dd9b1413414192284834c3`
  - Worker raw CRLF SHA-256: `d1efab8bae8f72344bb9e4b29697bc150b53bf098543e4b96e50b7357761b590`

### 4.2. Tệp ảnh bằng chứng và mã băm SHA-256 đầy đủ (64 hex characters)

| Đường dẫn Tệp Bằng chứng | Decoded PNG | Dung lượng | Mã băm SHA-256 Toàn vẹn | Trạng thái Nguồn gốc |
|---|---|---|---|---|
| `report/w23-evidence/w08/html-w08-self-check-folded-1280-dark-reduced.png` | 808×62 | 7,709 B | `508c15af5d5ca0138c0ca01bdf934bfceb9db616edd88b40f492325690f380ae` | Mẫu HTML tham chiếu (tái dùng chuẩn từ `24538ae0`) |
| `report/w23-evidence/w08/html-w08-self-check-open-1280-dark-reduced.png` | 808×154 | 23,442 B | `0f9922365c2ada53e8cc21f8745e3009b311eb1796364edf7c5c9809436268d6` | Mẫu HTML tham chiếu (tái dùng chuẩn từ `24538ae0`) |
| `report/w23-evidence/w08/react-w08-self-check-folded-crop.png` | 680×164 | 10,730 B | `676626eff3200b96f2eaf6d83eac21c1be98589f5109634f27211c116396b87b` | Ảnh cắt cúp runtime lịch sử (từ commit `b4136987`) |
| `report/w23-evidence/w08/react-w08-self-check-open-crop.png` | 680×206 | 12,773 B | `ceade2b5587a5e13ca69bff291ccc0c71720f00eb6d15e1919254ecf0955a305` | Ảnh cắt cúp runtime lịch sử (từ commit `b4136987`) |
| `report/w23-evidence/w08/react-w08-self-check-folded-1280-dark-reduced.png` | 1280×2380 | 210,418 B | `03d4b9f9e0c4f040c7924d934654cb029514ca63fdfdf340e734aeda21097e5e` | Tệp toàn trang lịch sử gốc (tham chiếu lưu trữ) |
| `report/w23-evidence/w08/react-w08-self-check-open-1280-dark-reduced.png` | 1280×2572 | 234,952 B | `e50ac7e32b5fcab31f207f6f190066fb7544fea458d6f5c6ebff8a9b03fc32ca` | Tệp toàn trang lịch sử gốc (tham chiếu lưu trữ) |
| `report/w23-evidence/w10/html-w10-library-here-390-light.png` | 366×808 | 58,515 B | `df3317df87aeed222b7e23caba9eef57a5a1f7c14565768609a1b92a51daf677` | Mẫu HTML tham chiếu (tái dùng chuẩn từ `24538ae0`) |
| `report/w23-evidence/w10/react-w10-library-here-crop.png` | 366×478 | 40,594 B | `0df8dd7d3320bcfa34f44476c0a53fe9ea513121489e632fc4874655a76f8126` | Ảnh cắt cúp runtime lịch sử (từ commit `1fc0f553`) |
| `report/w23-evidence/w10/react-w10-library-here-390-light.png` | 390×900 | 53,116 B | `2827d5d8009c6a3b52467b7236850bc2b5378e264f7974bb90e2a5069a417d5d` | Tệp toàn viewport lịch sử gốc (tham chiếu lưu trữ) |

---

## 5. Hướng dẫn Copy Chuẩn cho W-04 và W-12 (Duy trì Nghiệm thu)

1. **W-04 (Hồ sơ cá nhân & Đổi mật khẩu):**
   - Mật khẩu: Yêu cầu độ dài **8–128 ký tự**, loại bỏ mật khẩu thông dụng. Thuật toán **Argon2id** là xử lý băm ở phía server; nhãn UI hiển thị thuần túy: *"Mật khẩu mới (tối thiểu 8 ký tự)"*.
   - Đổi mật khẩu bảo lưu phiên hiện tại; nút "Đăng xuất mọi nơi" hiển thị hộp thoại xác nhận thu hồi phiên A và phiên B.
2. **W-12 (Lời mời Email & Quyền riêng tư):**
   - Văn bản chuẩn W-11 (`Sharing.tsx:227-228`):
     > *"Chủ khoá thấy tên bạn, hoạt động gần nhất và tiến độ theo từng module. Không thấy nội dung chat, tài liệu riêng hay đáp án quiz của bạn."*
   - Dữ liệu hiển thị cho chủ khoá: **hoạt động gần nhất** và **tiến độ theo từng module**.
   - Dữ liệu được bảo vệ riêng tư: **nội dung hội thoại chat**, **tài liệu riêng**, và **đáp án các câu hỏi quiz**.
   - Giới hạn: tối đa 50 email/lần, TTL 7 ngày, 200 lời mời/ngày.

---

## 6. Kế hoạch Mở rộng Toàn diện W-23 (Lát tiếp theo)
Sau khi Lát 1 hoàn tất đầy đủ hồ sơ biên lai và ràng buộc nguồn hiện hành, Nhóm Thiết kế sẽ mở rộng toàn bộ các cặp còn lại theo đúng tiêu chí W-23:
1. **W-08:** Bài giảng hoàn tất, Viewer xem tài liệu nguồn (`SourceViewer`), Nhân vật chờ (`waiting mascot 96px`).
2. **W-09:** Câu trả lời trợ lý kèm công thức KaTeX & nguồn, Menu hội thoại di động.
3. **W-10:** Quiz ready, Quiz result, Dialog tạo tài liệu theo yêu cầu ($\le 5$ modules), Document viewer Markdown GFM.
4. **Cấu hình & Tương tác:** Kiểm thử trên cả 3 kích thước (390px, 768px, 1280px), sáng/tối, điều hướng bàn phím (`:focus-visible`), reduced-motion, và video tương tác có mốc thời gian xem.
