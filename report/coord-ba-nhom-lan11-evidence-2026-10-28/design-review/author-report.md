# Báo cáo Đối chiếu Giao diện Web Thực tế (W-23) — Sửa Lát 1 theo Review R10 (2026-10-28)

- **Người thực hiện:** Nhóm Thiết kế (Design Group)
- **Người tiếp nhận:** Điều phối viên dự án, Nhóm Web & Chủ dự án
- **Nhánh thực hiện:** `work/w23-paired-web-evidence` tại worktree `tmp/w23-paired-web-evidence` (tạo từ `main` commit `29e4be5c`).
- **Mốc thiết kế xem xét:** `24538ae0a658c6e7a7439a8cf3418373e53a7aa4` (bản sửa theo Review R10).
- **Mốc main local nhận:** `776f1f00b13726fcdc95f12bfd18a2b937bbd153`.
- **Phạm vi & Nguyên tắc:** Khắc phục triệt để 4 điểm Required (D-R10-01 đến D-R10-04). Không tuyên bố đạt toàn bộ vé W-23; giữ các mốc token/branding/math và guard D-R8-02 đã nghiệm thu; chi phí **0 USD**, không dùng Cloud Figma.

---

## 1. Khắc phục D-R10-01: Khung So sánh Đồng nhất & Cấu trúc Tự kiểm tra

### 1.1. Minh bạch hóa nguồn gốc ảnh React Runtime lịch sử
Ba ảnh React trong mốc trước là bản sao nguyên bản (byte-for-byte) từ các lượt chạy kiểm thử trình duyệt lịch sử:
1. `react-w08-self-check-folded-1280-dark-reduced.png` (1280×2380): nguyên gốc là `ready-1280-dark-reduced.png` tại `report/w08-evidence/browser-required3-20261024/` (commit `b4136987668c3fb822ea374f399b947064ce7f18`).
2. `react-w08-self-check-open-1280-dark-reduced.png` (1280×2572): nguyên gốc là `self-check-open-1280-dark-reduced.png` tại `report/w08-evidence/browser-required3-20261024/` (commit `b4136987668c3fb822ea374f399b947064ce7f18`).
3. `react-w10-library-here-390-light.png` (390×900): nguyên gốc là `library-here-390-light.png` tại `report/w10-r7-evidence/browser-r7-main/` (commit `1fc0f553bec808241388b722fa2c10a1c6ead33d`, tái dùng hợp lệ cho `aaf68eb6795c929169e5212a05093d8d817c76e3` với diff 0 bytes).

Trong ảnh W-08 mở nguyên bản lịch sử, khối kiến thức tiên quyết (prerequisite) ở phía trên bị mở rộng, khác với trạng thái ở ảnh gập. Để loại trừ sự lệch trạng thái ngoài ý muốn này và đồng nhất khung hình so sánh với ảnh cắt của HTML, Nhóm Thiết kế đã thực hiện cắt cúp (crop) chính xác khối thành phần tương ứng:
- **React W-08 Folded Crop:** Cắt khối `.lecture-self-check` tại tọa độ `(x: 446, y: 1064, w: 680, h: 164)`.
- **React W-08 Open Crop:** Cắt khối `.lecture-self-check` tại tọa độ `(x: 446, y: 1214, w: 680, h: 206)`.
- **HTML W-08 Folded Crop:** Cắt `#details-self-check` tại tọa độ `(x: 236, y: 419, w: 808, h: 61)`.
- **HTML W-08 Open Crop:** Cắt `#details-self-check` tại tọa độ `(x: 236, y: 419, w: 808, h: 153)`.
- **React W-10 Library Crop:** Cắt khối `.content-library` tại tọa độ `(x: 12, y: 72, w: 366, h: 478)`.
- **HTML W-10 Library Crop:** Cắt `#section-document-library` tại tọa độ `(x: 12, y: 93, w: 366, h: 807)`.

### 1.2. Khác biệt UX & Trình bày Tự kiểm tra (W-08)
- **Giao diện React (`src/web/frontend/src/Learning.tsx`):**
  - Hiển thị tiêu đề `<h2>Tự kiểm tra</h2>`.
  - Câu hỏi đại số (*"Tổng hai nửa bằng bao nhiêu?"*) hiển thị ở ngoài khối `<details>` như một đoạn văn bản độc lập.
  - Thẻ `<summary>` chỉ chứa nhãn **"Xem đáp án"** và không có biểu tượng tam giác mũi tên mặc định.
  - Khi mở, nội dung hiển thị câu trả lời ngắn gọn: *"Bằng 1."*.
- **Mẫu HTML Thiết kế (`design/preview/w08_lecture_screens.html`):**
  - Đặt toàn bộ câu hỏi tim mạch (*"💡 Câu hỏi tự kiểm tra: Vì sao nhịp tim quá nhanh lại dễ gây thiếu máu cơ tim?"*) bên trong thẻ `<summary>` kèm biểu tượng tam giác mở `▶`.
  - Khi mở, nội dung hiển thị đoạn văn giải thích chi tiết cơ chế tưới máu tâm trương.
- **Phân loại theo W-23:** Đây là **khác biệt về phương án thiết kế UX hợp lệ cần Chủ dự án lựa chọn (Lựa chọn 4)**, không phải sự tương đương tuyệt đối đã đo lường.

### 1.3. Khác biệt Số lượng Tab Thư viện (W-10)
- **React (`ContentLibrary.tsx`):** Hiển thị 2 tab ngữ cảnh tại module: *"Tạo ở đây (2)"* và *"Tạo ở nơi khác (2)"*.
- **HTML (`w10_quiz_screens.html`):** Trình diễn 3 tab dạng catalog tổng thể: *"Tất cả (4)"*, *"Tạo ở đây (2)"*, *"Tạo ở nơi khác (2)"*.
- **Phân loại theo W-23:** Đề xuất mở cần Chủ dự án quyết định: Nhóm Thiết kế đề xuất giữ phương án 2 tab của React trên thiết bị di động 390px vì tối ưu diện tích và tránh ngắt dòng tab bar.

---

## 2. Khắc phục D-R10-02: Vùng Bấm Kích Thước Thực Tế, Tương Phản Màu & Hiệu Năng

### 2.1. Vùng bấm Click Target thực tế
- **Mẫu HTML W-08:** Phần tử `<summary>` có kích thước thực tế là `774 × 27.1875px` (`min-height: 0px`, `padding: 0px`). Thẻ bao `<details>` có `padding: 16px`, nhưng khi nhấp chuột vào vùng padding trên của `<details>`, sự kiện không kích hoạt mở/đóng; chỉ khi nhấp trực tiếp vào `<summary>` thì `<details>` mới toggle (đã kiểm chứng qua runtime probe). Do đó, vùng bấm thực tế của mẫu HTML hiện tại là 27.2px, chưa đạt khuyến nghị touch target $\ge 44$px.
- **Giao diện React W-08:** `src/web/frontend/src/learning.css` định nghĩa `.lecture-self-check summary { min-height: 44px; display: flex; align-items: center; }`. Bộ guard kiểm thử trình duyệt lịch sử độc lập xác nhận không có target nào dưới 43.5px.

### 2.2. Độ tương phản màu sắc
- **HTML W-08 Summary:** Màu chữ `#29A9FF` (`rgb(41, 169, 255)`) trên nền tổng hợp từ thẻ cha `#161B22` (`rgb(22, 27, 34)`), cho tỷ lệ tương phản **6.7657:1**.
- **Đánh giá chuẩn WCAG:** Tỷ lệ này đạt chuẩn **WCAG AA** (yêu cầu $\ge 4.5:1$ cho văn bản thường), nhưng **dưới ngưỡng WCAG AAA** (yêu cầu $\ge 7:1$). Nhóm Thiết kế rút lại nhận định "đạt AAA" và đính chính chuẩn xác là đạt chuẩn **WCAG AA**.

### 2.3. Rút lại tuyên bố hiệu năng không đo lường
- Ảnh chụp tĩnh PNG không thể chứng minh trạng thái "không bị giật lag". Nhóm Thiết kế rút lại tuyên bố này cho đến khi có dữ liệu đo frame/latency hoặc video tương tác thực tế ở lát kiểm tra tiếp theo.

### 2.4. W-10 Tab & Card
- Tab HTML `#tab-lib-here`: `min-height: 44px`, `height: 44px`, `padding: 0 16px` (đạt chuẩn touch target $\ge 44$px).
- Thẻ tài liệu: `width: 332px`, `padding: 16px`, `border-radius: 10px`.

---

## 3. Khắc phục D-R10-03: Mã Băm Minh Bạch & Bằng Chứng Tải Font

### 3.1. Bảng mã băm tệp nguồn (Phân biệt Raw CRLF và Git Blob LF)

| Đường dẫn Tệp | Mã băm Git LF Blob SHA-256 | Mã băm Worker Raw CRLF SHA-256 |
|---|---|---|
| `design/preview/w08_lecture_screens.html` | `ef89ee7e58fde9ca8eed7bf0a580cb79ab75958dec55e5a62be0b2fcac9f2fe7` | `066de4625bb71316916da7dee7f06ffb636897c32d619c0cde395c79a3987a13` |
| `design/preview/w10_quiz_screens.html` | `a6d42207d1c4f3915734b9efff6c757442ca6fefead5bec61706b9eddf7c0ecf` | `f2dea29c39708a24cf72e4617731e8d7dea588d4d2d6fc2aa75c4087d89ca989` |
| `design/tokens/tokens.css` | `5ce8eafee0b298032b57e3d4b2afb41a28850b6c30dd9b1413414192284834c3` | `d1efab8bae8f72344bb9e4b29697bc150b53bf098543e4b96e50b7357761b590` |

### 3.2. Bằng chứng tải Font chữ (CDP Platform Fonts)
- Trong môi trường sandbox chặn mạng ngoài (offline reproduction), `document.fonts.ready` hoàn tất nhưng `document.fonts` không có font web Google Fonts từ xa; CDP ghi nhận font thực tế hiển thị trên trình duyệt là `Segoe UI` (cho W-08) và `Arial` (cho W-10).
- Dữ liệu chi tiết về platform fonts, số lượng glyph, trạng thái loaded/unloaded được xuất đầy đủ trong receipt máy đọc được: [`report/w23-evidence/w23-slice1-receipts.json`](file:///c:/Users/ngoco/Desktop/Doctoroadmap/tmp/w23-paired-web-evidence/report/w23-evidence/w23-slice1-receipts.json).
- Kịch bản tái hiện chuẩn hóa: [`scripts/capture_w23_slice1_fixed.cjs`](file:///c:/Users/ngoco/Desktop/Doctoroadmap/tmp/w23-paired-web-evidence/scripts/capture_w23_slice1_fixed.cjs).

---

## 4. Khắc phục D-R10-04: Đính chính Hướng dẫn Thiết kế & Copy cho W-04 và W-12

### 4.1. W-04 (Hồ sơ cá nhân & Đổi mật khẩu)
- **Quy tắc mật khẩu:** Mật khẩu hợp lệ phải có độ dài từ **8–128 ký tự**, đồng thời bị từ chối nếu nằm trong danh sách các mật khẩu phổ biến dễ đoán (bundled common-password list theo `doc/web-chuc-nang-spec.md:277`).
- **Phân định rõ phía máy chủ:** Thuật toán **Argon2id** được xử lý ở phía máy chủ backend để băm mật khẩu; **không** đưa thuật ngữ kỹ thuật "Argon2id" hay "mã hoá" vào nhãn trường giao diện người dùng. Nhãn chuẩn trên UI: *"Mật khẩu mới (tối thiểu 8 ký tự)"*.
- **Phiên làm việc & Đăng xuất mọi nơi:** Thao tác đổi mật khẩu chỉ giữ phiên hiện tại; nút "Đăng xuất mọi nơi" (Logout all sessions) hiển thị hộp thoại xác nhận thu hồi cả phiên A và phiên B.

### 4.2. W-12 (Lời mời Email & Quyền riêng tư)
- Căn chỉnh chính xác theo văn bản quyền riêng tư đã chuẩn hóa tại W-11 (`src/web/frontend/src/Sharing.tsx` dòng 227-228) và `doc/web-chuc-nang-spec.md:455`:
  > *"Chủ khoá thấy tên bạn, hoạt động gần nhất và tiến độ theo từng module. Không thấy nội dung chat, tài liệu riêng hay đáp án quiz của bạn."*
- **Dữ liệu được hiển thị cho chủ khoá:** Tên học viên, ngày tham gia, **hoạt động gần nhất** và **tiến độ theo từng module**.
- **Dữ liệu được bảo vệ riêng tư (loại trừ rõ ràng):** Không thấy **nội dung hội thoại chat**, **tài liệu riêng**, và **đáp án các câu hỏi quiz**.
- **Giới hạn nghiệp vụ:** Hộp nhập paste tối đa 50 email mỗi đợt (tự gộp trùng), thời hạn lời mời (TTL) 7 ngày, giới hạn tối đa 200 lời mời/ngày cho mỗi chủ khoá.

---

## 5. Bảng Bằng chứng & Mã Băm Lát 1 (Đã Chuẩn Hóa Cắt Cúp)

### 5.1. Bảng đối chiếu hai cặp thực tế

| Cặp đối chiếu | Ảnh Cắt Cúp React Runtime | Ảnh Mẫu Thiết kế HTML | Thông số Thực tế & Nhận định |
|---|---|---|---|
| **W-08 Tự kiểm tra GẬP** | `report/w23-evidence/w08/react-w08-self-check-folded-crop.png`<br>*(Crop: 680×164px, SHA-256: `676626EF...`)* | `report/w23-evidence/w08/html-w08-self-check-folded-1280-dark-reduced.png`<br>*(Crop: 808×61px, SHA-256: `508C15AF...`)* | **HTML:** `summary` height 27.2px, contrast 6.77:1 (WCAG AA). Câu hỏi trong summary kèm `▶`.<br>**React:** Câu hỏi ngoài summary, text "Xem đáp án" không icon, touch target $\ge 43.5$px.<br>**Phân loại:** Khác biệt UX cần Chủ dự án chọn (Lựa chọn 4). |
| **W-08 Tự kiểm tra MỞ** | `report/w23-evidence/w08/react-w08-self-check-open-crop.png`<br>*(Crop: 680×206px, SHA-256: `CEADE2B5...`)* | `report/w23-evidence/w08/html-w08-self-check-open-1280-dark-reduced.png`<br>*(Crop: 808×153px, SHA-256: `0F992236...`)* | **HTML:** Mở hiển thị đoạn giải thích chi tiết cơ chế tim mạch.<br>**React:** Mở hiển thị đáp án "Bằng 1.".<br>**Phân loại:** Khác biệt nội dung minh họa, cơ chế toggle `<details>` hoạt động chuẩn. |
| **W-10 Thư viện "Tạo ở đây"** | `report/w23-evidence/w10/react-w10-library-here-crop.png`<br>*(Crop: 366×478px, SHA-256: `0DF8DD7D...`)* | `report/w23-evidence/w10/html-w10-library-here-390-light.png`<br>*(Crop: 366×807px, SHA-256: `DF3317DF...`)* | **HTML:** 3 tab catalog ("Tất cả", "Tạo ở đây", "Tạo ở nơi khác"), tab height 44px, card width 332px.<br>**React:** 2 tab module ("Tạo ở đây", "Tạo ở nơi khác"), tab height 44px.<br>**Phân loại:** Đề xuất giữ 2 tab của React trên 390px (Lựa chọn 4). |

### 5.2. Danh mục đầy đủ các tệp ảnh và mã băm SHA-256

| Tệp Bằng chứng | Kích thước | Dung lượng | Mã băm SHA-256 | Ghi chú nguồn gốc |
|---|---|---|---|---|
| `report/w23-evidence/w08/html-w08-self-check-folded-1280-dark-reduced.png` | 808×61 | 7,709 B | `508c15af5d5ca0138c0ca01bdf934bfceb9db616edd88b40f492325690f380ae` | Chromium capture selector `#details-self-check` |
| `report/w23-evidence/w08/html-w08-self-check-open-1280-dark-reduced.png` | 808×153 | 23,442 B | `0f9922365c2ada53e8cc21f8745e3009b311eb1796364edf7c5c9809436268d6` | Chromium capture selector `#details-self-check` (open) |
| `report/w23-evidence/w08/react-w08-self-check-folded-crop.png` | 680×164 | 10,730 B | `676626eff3200b96f2eaf6d83eac21c1be98589f5109634f27211c116396b87b` | Cắt cúp từ `ready-1280-dark-reduced.png` (commit `b4136987`) |
| `report/w23-evidence/w08/react-w08-self-check-open-crop.png` | 680×206 | 12,773 B | `ceade2b5587a5e13ca69bff291ccc0c71720f00eb6d15e1919254ecf0955a305` | Cắt cúp từ `self-check-open-1280-dark-reduced.png` (commit `b4136987`) |
| `report/w23-evidence/w08/react-w08-self-check-folded-1280-dark-reduced.png` | 1280×2380 | 210,418 B | `03d4b9f9e0c4f040c7924d934654cb029514ca63fdfdf340e734aeda21097e5e` | Tệp toàn trang lịch sử (tham chiếu gốc) |
| `report/w23-evidence/w08/react-w08-self-check-open-1280-dark-reduced.png` | 1280×2572 | 234,952 B | `e50ac7e32b5fcab31f207f6f190066fb7544fea458d6f5c6ebff8a9b03fc32ca` | Tệp toàn trang lịch sử (tham chiếu gốc) |
| `report/w23-evidence/w10/html-w10-library-here-390-light.png` | 366×807 | 58,515 B | `df3317df87aeed222b7e23caba9eef57a5a1f7c14565768609a1b92a51daf677` | Chromium capture selector `#section-document-library` |
| `report/w23-evidence/w10/react-w10-library-here-crop.png` | 366×478 | 40,594 B | `0df8dd7d3320bcfa34f44476c0a53fe9ea513121489e632fc4874655a76f8126` | Cắt cúp từ `library-here-390-light.png` (commit `1fc0f553`) |
| `report/w23-evidence/w10/react-w10-library-here-390-light.png` | 390×900 | 53,116 B | `2827d5d8009c6a3b52467b7236850bc2b5378e264f7974bb90e2a5069a417d5d` | Tệp toàn viewport lịch sử (tham chiếu gốc) |
