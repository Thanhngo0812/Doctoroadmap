# Spec thiết kế giao diện WayFinder — cho bản Figma và giao diện React

**Ngày:** 2026-10-18. **Nhãn:** `ready-for-agent`. **Dùng cho:** vé [W-22](../task/web/W-22-ban-figma.md) (Figma), giao diện của mọi vé `task/web/`, và
[W-23](../task/web/W-23-doi-chieu-figma-va-giao-dien.md) (đối chiếu).

**Dựa trên:** [spec chức năng](web-chuc-nang-spec.md) (trang, chức năng, mã lỗi), [spec Pha B2](pha-b2-spec.md) (hai trang học, bài giảng `lecture-2`),
[ADR 0023](adr/0023-cloudinary-cho-tep-goc-va-anh.md) (ảnh trang).

**Chủ dự án đã chốt (2026-10-18):**
- tên sản phẩm **WayFinder**;
- font **Be Vietnam Pro**;
- màu do Claude chọn, lấy từ logo;
- logo, favicon và GIF chờ do chủ dự án cung cấp;
- stack React + FastAPI + PostgreSQL;
- nhân viên vẽ Figma, Claude chỉ viết spec.

---

## Vấn đề

- Nhóm web cần một nguồn thiết kế chung trước khi dựng 20 trang, để các vé không tự chọn màu, cỡ chữ và cách báo lỗi mỗi người một kiểu.
- Thương hiệu WayFinder là **pixel art**: mặt đeo kính, chữ "W" pixel, GIF nhân vật gõ laptop. Nhưng sản phẩm là nơi **đọc bài giảng dài bằng tiếng Việt**. Nếu
  dùng pixel khắp nơi thì khó đọc.
- Màu thương hiệu `#29A9FF` trên nền trắng chỉ đạt **2,56:1**, dưới mức 4,5:1 của WCAG AA cho chữ. Dùng thẳng cho chữ hay nút là sai chuẩn.
- GIF chờ rộng 2000 px, nặng 7,4 MB, quá nặng cho một vòng chờ.

## Giải pháp

- **Pixel cho thương hiệu, chữ sạch cho nội dung.** Pixel chỉ xuất hiện ở logo, favicon, vòng chờ, minh hoạ trạng thái rỗng, và vài chi tiết nhỏ (góc thẻ,
  dấu "đã học"). Mọi vùng đọc dùng Be Vietnam Pro, nền sáng, cột chữ hẹp.
- **Hai lớp màu xanh:** `#29A9FF` cho mảng màu, minh hoạ, nền logo, chế độ tối. Một sắc đậm hơn (`#0A6AB3`, 5,64:1 trên trắng) cho chữ, link và nút ở chế
  độ sáng.
- **Màu nhấn phụ là cam hổ phách** lấy từ GIF (`#FEBA4F`), cho khối "Tiếp theo", huy hiệu, điểm nhấn ấm.
- **Hai chế độ sáng và tối,** cùng tên token.
- **Thiết kế từ điện thoại** (390 px), rồi mở ra máy tính bảng (768 px) và máy tính (1280 px).

---

## Quyết định thiết kế

### 1. Tệp thương hiệu

Mọi tệp ở thư mục `design/` của repo.

**Logo — 4 bố cục × 2 bản màu.** Tên tệp theo giả định của Claude, đọc từ ảnh chủ dự án dán ngày 2026-10-18; tệp thật tới lúc 19:30 cùng ngày. Nếu
đánh số khác thì chỉ sửa bảng này.

| tệp | bố cục | bản màu | dùng ở |
|---|---|---|---|
| `logo1` | xếp dọc: mặt ở trên, "Way / Finder" hai dòng | đen trên trắng | trang đăng nhập, đăng ký (máy tính bảng trở lên) |
| `logo2` | chữ hai dòng bên trái, mặt lệch góc phải | đen trên trắng | trang giới thiệu, đầu thư email |
| `logo3` | mặt trên bên trái, "WayFinder" một dòng | đen trên trắng | trang đăng nhập ở điện thoại |
| `logo4` | ngang: mặt trái, chữ phải | đen trên trắng | **thanh trên mọi trang**, chế độ sáng |
| `logo5` | như `logo1` | trắng trên xanh `#29A9FF` | trang giới thiệu, ảnh chia sẻ link |
| `logo6` | như `logo2` | trắng trên xanh | slide, báo cáo |
| `logo7` | như `logo3` | trắng trên xanh | màn hình chờ khi mở ứng dụng |
| `logo8` | như `logo4` | trắng trên xanh | thanh trên ở chế độ tối (nếu có bản nền trong), chân trang |

**Favicon** (`OTP1`–`OTP6`, 521×521 PNG):

| tệp | hình | dùng ở |
|---|---|---|
| `OTP6` | chữ "W" pixel trắng trên ô xanh bo góc | **favicon tab** 16, 32, 48 px (chữ "W" đọc được ở cỡ nhỏ hơn mặt) |
| `OTP3` | mặt pixel trắng trên ô xanh bo góc | `apple-touch-icon` 180 px, biểu tượng PWA 192 và 512 px |
| `OTP5` | chữ "W" xanh trên nền trắng | chỗ cần biểu tượng nhỏ trên nền trắng (thư email) |
| `OTP4` | mặt xanh trên nền trắng | minh hoạ nhỏ trong trạng thái rỗng |
| `OTP1` | mặt trắng, nền trong | biểu tượng trên nền tối hay nền xanh |
| `OTP2` | mặt đen, nền trong | in đen trắng, báo cáo |

**Luật dùng logo:**
- Không vẽ lại, không kéo méo, không đổi màu ngoài hai bản đen và trắng-trên-xanh, không thêm bóng đổ.
- **Khoảng trống quanh logo** tối thiểu bằng chiều cao của hai "điểm ảnh" trong mặt pixel.
- **Cỡ nhỏ nhất:** logo ngang cao 24 px trên thanh trên ở điện thoại, 32 px ở máy tính. Dưới cỡ đó thì chỉ dùng favicon.
- **Phóng ảnh pixel** (favicon, mặt, GIF) bằng `image-rendering: pixelated`, theo bội số nguyên khi được, để cạnh không nhoè.
- **Chữ trong logo là chữ vẽ riêng,** không phải Be Vietnam Pro. Không dựng lại logo bằng chữ HTML.

**Cần chủ dự án cung cấp thêm** (người thiết kế hỏi ngay khi nhận vé):
- bản **SVG**, hay PNG nền trong, của 8 logo; nhất là bản **trắng nền trong**, cho thanh trên ở chế độ tối;
- xác nhận bảng đánh số ở trên;
- **tệp gốc của GIF** (các khung, hay tệp Procreate hay Aseprite), để xuất lại ở cỡ nhỏ mà không nhoè.

### 2. Vòng chờ GIF

**Tệp gốc:** `Untitled_Artwork.gif`. Nhân vật pixel gõ laptop, 61 khung × 50 ms, vòng lặp 3,05 giây, nền trong. Lưới pixel gốc khoảng 60×60 ô, phóng lên
2000 px.

**Xuất lại** (người thiết kế hay vé W-01):

| bản | cỡ | định dạng | mục tiêu dung lượng |
|---|---|---|---|
| lớn | 240×240 | WebP động (GIF dự phòng) | ≤ 300 KB |
| nhỏ | 120×120 | WebP động (GIF dự phòng) | ≤ 120 KB |
| tĩnh | 240×240 | PNG của khung 0 | ≤ 20 KB |

- Phóng bằng hàng xóm gần nhất (nearest neighbour), không làm mịn.
- Nếu 61 khung quá nặng, bỏ bớt khung xen kẽ và tăng thời lượng khung lên 100 ms. Vòng lặp giữ khoảng 3 giây.

**Dùng ở đâu:**
- **chờ việc dài, có ý nghĩa:**
  - bài giảng trước cổng: "Đang soạn bài…";
  - bản dựng: bước đang chạy;
  - đang tạo tài liệu;
  - đang sinh quiz, khi chưa có câu nào;
- **cỡ:** 160 px khi chiếm cả vùng; 96 px khi nằm trong thẻ; luôn có một dòng chữ bên dưới nói đang làm gì;
- **chỉ hiện sau 400 ms,** để không nháy với việc xong nhanh;
- **không dùng** cho tải trang thường hay tải danh sách. Chỗ đó dùng **khung xương** (skeleton) xám nhạt;
- **`prefers-reduced-motion`:** thay bằng ảnh tĩnh, cộng ba chấm chuyển màu chậm, hoặc không động.
- Có `role="status"` và chữ ẩn cho trình đọc màn hình, ví dụ "Đang soạn bài giảng".

### 3. Token

Tên token dùng chung cho Figma (variables) và CSS (custom properties). Giữ **đúng tên** ở cả hai bên.

**Chữ:**
- `font-sans`: "Be Vietnam Pro", rồi `system-ui`, `-apple-system`, "Segoe UI", sans-serif. Nạp từ Google Fonts với `display=swap`, các độ đậm 400, 500, 600,
  700.
- `font-mono`: `ui-monospace`, "SFMono-Regular", Consolas, monospace (mã nguồn, ký hiệu).

| token | cỡ / dòng | độ đậm | dùng |
|---|---|---|---|
| `text-display` | 36 / 44 | 700 | tiêu đề trang giới thiệu (máy tính) |
| `text-h1` | 30 / 38 | 700 | tên khoá học, tên trang |
| `text-h2` | 24 / 32 | 600 | tên module, tên khái niệm trong bài giảng |
| `text-h3` | 20 / 28 | 600 | tiêu đề khối |
| `text-lead` | 18 / 30 | 400 | **thân bài giảng**, câu định nghĩa |
| `text-body` | 16 / 26 | 400 | chữ giao diện, chat |
| `text-small` | 14 / 22 | 400–500 | nhãn, chú thích, trích dẫn |
| `text-caption` | 12 / 18 | 500 | huy hiệu, thời gian |

- Ở điện thoại, `text-display` 28/36, `text-h1` 24/32, `text-h2` 20/28. Các cỡ khác giữ nguyên.
- **Tiếng Việt có dấu chồng** (ví dụ "ệ", "ổ"): dòng của tiêu đề không dưới 1,3 lần cỡ chữ; không dùng giãn chữ âm quá −0,01 em.
- **Cột đọc của bài giảng và tài liệu** rộng tối đa 72 ký tự (khoảng 680 px ở `text-lead`).

**Màu, chế độ sáng:**

| token | giá trị | tương phản | dùng |
|---|---|---|---|
| `color-bg` | `#FFFFFF` | | nền trang |
| `color-bg-subtle` | `#F6F8FA` | | nền vùng phụ, thanh bên |
| `color-surface` | `#FFFFFF` | | thẻ, hộp thoại |
| `color-border` | `#DDE2E8` | | đường chia trang trí |
| `color-border-input` | `#8994A0` | 3,08:1 trên trắng | viền ô nhập, viền nút phụ (cần ≥ 3:1) |
| `color-text` | `#12161B` | 18,16:1 | chữ chính |
| `color-text-muted` | `#5B6673` | 5,84:1 trên trắng; 5,49:1 trên `bg-subtle` | chữ phụ, thời gian, trích dẫn |
| `color-brand` | `#29A9FF` | **2,56:1 — không dùng cho chữ** | nền logo, minh hoạ, thanh tiến độ, vạch chọn |
| `color-brand-tint` | `#EAF6FF` | | nền mục đang chọn, nền câu trả lời của trợ lý |
| `color-primary` | `#0A6AB3` | 5,64:1 trên trắng; ≥ 4,94:1 trên mọi nền nhạt ở bảng này | link, nút chính (chữ trắng 5,64:1), viền focus |
| `color-primary-hover` | `#0A5E9C` | 6,79:1 | nút chính khi rê chuột |
| `color-accent` | `#FEBA4F` | chữ `#12161B` trên nó 10,68:1 | huy hiệu, dải "Tiếp theo", điểm nhấn |
| `color-accent-tint` | `#FFF4DF` | | nền khối "Tiếp theo", dải cảnh báo |
| `color-accent-text` | `#8A4F0F` | 6,01:1 trên `accent-tint` | chữ cảnh báo, "sắp hết trần" |
| `color-success` | `#146C3B` | 5,82:1 trên `success-tint` | "đã học", đúng |
| `color-success-tint` | `#E8F6EE` | | nền ô đúng |
| `color-danger` | `#B02F2F` | 5,58:1 trên `danger-tint` | lỗi, sai, xoá |
| `color-danger-tint` | `#FDECEC` | | nền lỗi |

**Màu, chế độ tối** (cùng tên token):

| token | giá trị | tương phản |
|---|---|---|
| `color-bg` | `#0E1217` | |
| `color-bg-subtle`, `color-surface` | `#161B22` | |
| `color-surface-2` | `#1E252E` | (thẻ nổi, hộp thoại) |
| `color-border` | `#2A323C` | trang trí |
| `color-border-input` | `#6B7785` | ≥ 3:1, kiểm lại bằng plugin |
| `color-text` | `#E8EDF2` | 14,68:1 trên `surface` |
| `color-text-muted` | `#9AA6B2` | 6,98:1 trên `surface` |
| `color-primary`, `color-brand` | `#29A9FF` | 6,77:1 trên `surface`; nút chính dùng chữ `#0E1217` (7,35:1) |
| `color-accent` | `#FEBA4F` | 10,17:1 trên `surface` |
| `color-success` | `#4ADE80` | 9,93:1 |
| `color-danger` | `#F87171` | 6,25:1 |
| các `*-tint` | màu tương ứng ở độ mờ 12–16% trên `surface` | kiểm chữ trên nền tint ≥ 4,5:1 |

Mọi số tương phản ở trên được tính theo công thức WCAG 2.x. Người thiết kế kiểm lại bằng plugin trong Figma, và ghi các cặp đã kiểm vào báo cáo W-22.

**Khoảng cách:** thang 4 px: `space-1` 4, `space-2` 8, `space-3` 12, `space-4` 16, `space-5` 20, `space-6` 24, `space-8` 32, `space-10` 40, `space-12` 48,
`space-16` 64.
- Lề trang 16 px ở điện thoại, 24 px ở máy tính bảng, 32 px ở máy tính.

**Bo góc:** `radius-sm` 6 (huy hiệu), `radius-md` 10 (nút, ô nhập), `radius-lg` 14 (thẻ), `radius-xl` 20 (hộp thoại, khung chat). `radius-pixel` 0 cho chi
tiết pixel.

**Bóng:** `shadow-1` `0 1px 2px rgb(18 22 27 / 0.06), 0 1px 3px rgb(18 22 27 / 0.08)` (thẻ); `shadow-2` `0 8px 24px rgb(18 22 27 / 0.12)` (hộp thoại, menu).
Chế độ tối thay bóng bằng viền `color-border` và nền `surface-2`.

**Chuyển động:** `motion-fast` 120 ms, `motion-base` 200 ms, `ease-out`. Tắt hết khi `prefers-reduced-motion`.

**Điểm ngắt:** `sm` 390 (thiết kế gốc), `md` 768, `lg` 1024, `xl` 1280. Nội dung chính rộng tối đa 1200 px.

**Chi tiết pixel** (dùng tiết kiệm):
- góc trên trái của thẻ khoá học có một ô 4×4 px màu `color-brand`;
- dấu "đã học" là một dấu tích vẽ bằng ô vuông 2 px;
- minh hoạ trạng thái rỗng dùng mặt pixel (`OTP4`) cộng một dòng chữ.

### 4. Sơ đồ trang và đường dẫn

| đường | trang | ai |
|---|---|---|
| `/` | giới thiệu (khách); chuyển sang `/khoa-hoc` nếu đã đăng nhập | khách |
| `/dang-nhap`, `/dang-ky`, `/quen-mat-khau`, `/dat-lai-mat-khau`, `/xac-minh` | tài khoản | khách |
| `/join/:token` | tham gia bằng link | khách, người dùng |
| `/khoa-hoc` | **Khoá học của tôi** (trang chủ sau đăng nhập) | người dùng |
| `/tai-len` | tải giáo trình | đã xác minh |
| `/ban-dung/:id` | tiến trình bản dựng | người tải |
| `/khoa-hoc/:cid` | **trang lộ trình** | thành viên |
| `/khoa-hoc/:cid/module/:mid` | **trang học** | thành viên |
| `/khoa-hoc/:cid/module/:mid/khai-niem/:nid` | trang học, mở sẵn bài giảng | thành viên |
| `/khoa-hoc/:cid/quiz/:aid` | làm quiz, kết quả | thành viên |
| `/khoa-hoc/:cid/tai-lieu/:did` | xem tài liệu | thành viên |
| `/khoa-hoc/:cid/thanh-vien` | thành viên; bảng tiến độ lớp (chủ khoá) | thành viên |
| `/khoa-hoc/:cid/quan-ly` | tên, mô tả, chia sẻ, mời, báo lỗi, vùng nguy hiểm | chủ khoá |
| `/ho-so`, `/muc-dung` | hồ sơ, mức dùng | người dùng |
| `/admin/nguoi-dung`, `/admin/ban-dung`, `/admin/chi`, `/admin/khoa-mau`, `/admin/bao-loi`, `/admin/nhat-ky` | quản trị | admin |
| mọi đường khác | 404 với mặt pixel | |

### 5. Khung chung

**Thanh trên** (cao 56 px ở điện thoại, 64 px ở máy tính), nền `color-surface`, viền dưới `color-border`:
- trái: logo ngang (`logo4`; chế độ tối dùng bản trắng nền trong khi có);
- giữa (máy tính): tên khoá học đang mở, kèm đường dẫn "Khoá học / Module 3";
- phải: nút "Tải giáo trình", biểu tượng mức dùng (vòng tỉ lệ nhỏ), menu tài khoản (Hồ sơ, Mức dùng, Quản trị nếu là admin, Chế độ tối, Đăng xuất).
- Ở điện thoại, phần giữa ẩn; nút "Tải giáo trình" vào menu.

**Dải thông báo** dưới thanh trên, cố định khi cần:
- chưa xác minh email: nền `brand-tint`;
- hết trần ngày: nền `accent-tint`, chữ `accent-text`, kèm giờ đặt lại;
- lỗi mạng: nền `danger-tint`.

**Thông báo nổi (toast):** góc dưới phải ở máy tính, dưới giữa ở điện thoại; tự tắt sau 5 giây, trừ lỗi.

### 6. Bố cục từng trang chính

**Khoá học của tôi** (`/khoa-hoc`):

```
┌──────────────────────────────────────────────────────────────┐
│ [logo4]                       [Tải giáo trình] (◔) [Tên ▾]   │
├──────────────────────────────────────────────────────────────┤
│ Lời mời (2)   [Khoá A — từ Lan] [Chấp nhận] [Từ chối]        │
│                                                              │
│ Khoá học của tôi                                             │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐                       │
│ │▪ Tên     │ │▪ Tên     │ │ Đang dựng│                       │
│ │ 8 module │ │ 5 module │ │ bước 2/4 │                       │
│ │ xong 12/40│ │ xong 0/22│ │ [gif 96] │                       │
│ │[Học tiếp]│ │[Học tiếp]│ │[Xem]     │                       │
│ └──────────┘ └──────────┘ └──────────┘                       │
│ Được chia sẻ với tôi   (lưới thẻ như trên, có tên chủ khoá)    │
│ Khoá học mẫu           (thẻ, nút [Tham gia])                  │
└──────────────────────────────────────────────────────────────┘
```

- Lưới: 1 cột ở 390 px, 2 cột ở 768 px, 3 cột ở 1280 px.
- **Rỗng hoàn toàn:** mặt pixel cộng câu "Chưa có khoá học. Thử một khoá mẫu, hoặc tải giáo trình của bạn." kèm hai nút.

**Trang lộ trình** (`/khoa-hoc/:cid`):

```
┌───────────────────────────────────────────┬──────────────────┐
│ Tên khoá học                    [Chia sẻ] │ Trò chuyện       │
│ mô tả · xong 12/40 ▓▓▓░░░░░               │ [Tất cả ▾][+ Mới]│
│                                           │ • Phiên lộ trình │
│ [Làm quiz cả khoá] [Tạo tài liệu]         │ • Module 3: ...  │
│                                           │ ───────────────  │
│ ① Tên module 1        xong 5/5  ✓  [Học] │ (khung chat)     │
│   mô tả hai dòng…                    ▸    │                  │
│ ② Tên module 2        xong 3/8     [Học] │                  │
│   ▾ Khái niệm: □ A  ■ B  □ C …            │                  │
│ ③ …                                       │                  │
│                                           │                  │
│ Thư viện của khoá     [Tất cả ▾]          │                  │
│ • Tài liệu "…"  · hôm qua                 │                  │
│ • Quiz cả khoá · 7/10 · 2 ngày trước      │                  │
└───────────────────────────────────────────┴──────────────────┘
```

- **Máy tính:** cột chính cộng khung chat 380 px bên phải, thu gọn được.
- **Điện thoại:** một cột; khung chat thành nút nổi "Hỏi trợ lý" mở bảng toàn màn hình; thư viện là thẻ cuối trang.
- Module đã xong mọi khái niệm có dấu tích `color-success`. Không có khoá hay mờ: tiến độ không chặn gì (ADR 0019).

**Trang học** (`/khoa-hoc/:cid/module/:mid`):

```
┌──────────────┬──────────────────────────────┬────────────────┐
│ Module 3     │ Khái niệm 2/6 · Module 3     │ Trò chuyện     │
│ ■ Khái niệm 1│ ┌ Cần biết trước ───────────┐│ (phiên của     │
│ ▶ Khái niệm 2│ │ ▸ Ma trận · m.2 · ✓ đã học│ │  module)       │
│ □ Khái niệm 3│ │   "Định thức dùng ma trận…"││                │
│ □ …          │ └───────────────────────────┘│                │
│              │ Định nghĩa                    │                │
│ Thư viện     │ "…câu nguyên văn…" (tr. 42)   │                │
│ Tạo ở đây    │ [ảnh công thức]               │                │
│ Tạo nơi khác │ Giải thích  (hiện dần)        │                │
│              │ Ví dụ · Phân biệt · Tự kiểm tra│               │
│ [Làm quiz]   │ ┌ Tiếp theo ───────────────┐ │                │
│ [Tạo tài liệu]│ │ → Khái niệm X · module 5 │ │                │
│              │ └──────────────────────────┘ │                │
│              │ [✓ Đã học]   [Báo lỗi]        │                │
└──────────────┴──────────────────────────────┴────────────────┘
```

- **Máy tính (≥ 1280):** ba cột: danh sách khái niệm 260 px, bài giảng (cột đọc ≤ 680 px), khung chat 380 px thu gọn được.
- **Máy tính bảng:** hai cột; khung chat thành bảng trượt từ phải.
- **Điện thoại:** danh sách khái niệm là màn đầu; bấm một khái niệm thì sang màn bài giảng có nút quay lại; chat là nút nổi.
- **Khối "Cần biết trước"** gập sẵn mỗi tiên quyết. Nhãn "✓ đã học" (`success`) hay "chưa học" (`text-muted`), kèm "module m". Mở ra thấy câu định nghĩa và
  trích dẫn. Câu nối (chữ thường, `text-body`) hiện dưới tên khi tới.
- **Khối "Tiếp theo"** nền `accent-tint`, viền trái 4 px `color-accent`.
- **Trích dẫn** là số nhỏ bấm được, mở khung xem ảnh trang.
- **Ý mới hiện dần:** mờ vào trong 200 ms; không nhảy bố cục (chừa chỗ theo khung xương).

**Bài giảng — bốn trạng thái:**

| trạng thái | thấy gì |
|---|---|
| đang chờ (trước cổng) | phần mã dựng (định nghĩa, tiên quyết, ảnh) hiện ngay; dưới đó vòng chờ 96 px + "Đang soạn bài…" |
| đang hiện dần | các ý xuất hiện lần lượt; vòng chờ nhỏ ở cuối cho tới `final` |
| xong | đủ bài; nút "Đã học", "Báo lỗi" |
| hỏng hẳn | phần mã dựng + hộp nền `bg-subtle`: lời nhắn theo `reason_code`, nút "Đọc trang p trong sách" (chính), "Hỏi trợ lý", "Thử lại" (chỉ khi `retryable`) |

**Khung xem trang** ("Đọc trang p"): hộp thoại lớn (điện thoại: toàn màn hình) hiện ảnh trang; nút ‹ trang trước, trang sau ›; số trang; nút "Mở cả tệp".
Ảnh rộng vừa khung, phóng được bằng hai ngón tay.

**Khung chat** (dùng ở hai trang):
- đầu khung: chọn phiên (danh sách thả xuống có tiêu đề, ngày), nút "+ Phiên mới", menu ⋯ (đổi tên, xoá);
- **lượt người học:** bong bóng phải, nền `brand-tint`;
- **lượt trợ lý:** không bong bóng, chữ `text-body`, rộng hết khung; trích dẫn là số nhỏ; nội dung ngoài sách có nhãn "ngoài sách" (`caption`, viền `border`);
- **thẻ module:** "Nội dung ở module 5 — Mở module" (thẻ nhỏ, viền `color-primary`);
- **tiến trình công cụ:** dòng `text-small` `text-muted` có biểu tượng, ví dụ "Đang tìm trong sách…", "Đang tạo quiz…";
- **phạm vi đã cũ:** dải nhỏ đầu khung "Module này đã đổi; trợ lý đang trả lời theo cả khoá";
- **hết trần:** ô nhập khoá, thay bằng dải `accent-tint` kèm giờ đặt lại;
- **ô nhập:** tự cao tới 6 dòng; Enter gửi, Shift+Enter xuống dòng; nút gửi có nhãn cho trình đọc màn hình.

**Làm quiz** (`/khoa-hoc/:cid/quiz/:aid`):
- một cột ≤ 720 px; mỗi câu là một thẻ, ba phương án là nút chọn lớn (cao ≥ 44 px);
- câu nào sinh xong trước hiện trước; câu đang sinh là khung xương;
- thanh dưới cố định: "Đã trả lời 4/10" và nút "Nộp bài";
- **khung chat ẩn** khi đang làm;
- **kết quả:** điểm ở đầu; mỗi câu tô `success-tint` hay `danger-tint`, có giải thích, trích dẫn, nút "Báo lỗi câu này".

**Tải giáo trình** và **tiến trình dựng:**

```
Tải giáo trình                        Còn 2/3 lượt dựng tháng này
┌──────────────────────────────────────────────┐
│     Kéo thả tệp PDF hoặc DOCX vào đây         │
│     hoặc [Chọn tệp]   · tối đa 10 MB, 400 trang│
└──────────────────────────────────────────────┘
☐ Tôi có quyền dùng và chia sẻ tài liệu này        [Tải lên]

Tiến trình
 ✓ Đọc tài liệu
 ● Trích khái niệm      [gif 96]  khoảng 6 phút
 ○ Dựng đồ thị và lộ trình
 ○ Chuẩn bị bài học
 Dự toán: khoảng 12 phút · đã dùng 1 lượt     [Huỷ]
```

- Sau bước đọc: hộp **dự toán** với nút "Dựng lộ trình" và "Để sau". Người dùng thường thấy phút và số lượt, không thấy USD (spec chức năng mục 8).
- **Lỗi bản quét:** mặt pixel, câu "Tệp này là bản quét (ảnh chụp trang), WayFinder chưa đọc được. Hãy dùng bản PDF có chữ chọn được." Không trừ lượt.

**Tham gia** (`/join/:token`): thẻ giữa trang: logo nhỏ, tên khoá, "do Lan chia sẻ", số module; **khối thông báo dữ liệu** ("Chủ khoá thấy tên bạn, ngày tham
gia, số khái niệm bạn đã đánh dấu học. Không thấy nội dung chat hay bài làm."); nút "Tham gia". Khách thấy nút "Đăng nhập", "Đăng ký".

**Quản lý khoá** (`/khoa-hoc/:cid/quan-ly`), thẻ:
- Thông tin: tên, mô tả;
- Chia sẻ: tạo link (hạn, số lượt), danh sách link, mời qua email, lời mời đang chờ;
- Báo lỗi nội dung;
- Vùng nguy hiểm: xoá khoá (gõ lại tên).

**Mức dùng** (`/muc-dung`): vòng tỉ lệ lớn "Hôm nay đã dùng 35%", giờ đặt lại; thẻ lượt dựng "1/3, đặt lại 1/11"; giải thích ngắn hết trần thì vẫn làm được
gì. Không có số USD.

**Quản trị:** bố cục bảng ở máy tính, thanh thẻ trên; không cần đẹp ở điện thoại, nhưng không được vỡ (bảng cuộn ngang trong khung).

### 7. Bộ thành phần

Mỗi thành phần có trạng thái: mặc định, rê chuột, focus (viền 2 px `color-primary` cách 2 px), bấm, vô hiệu, đang tải.

| thành phần | biến thể |
|---|---|
| Nút | chính, phụ (viền `border-input`), chữ, nguy hiểm; cỡ 36 và 44 px; có biểu tượng hay không; đang tải (vòng nhỏ, không phải GIF) |
| Ô nhập | chữ, email, mật khẩu (nút hiện/ẩn), vùng chữ tự cao; có lỗi (viền và chữ `danger`, câu lỗi dưới ô) |
| Hộp chọn, nút chọn | thường, đã chọn, lỗi |
| Thẻ khoá học | sở hữu, được chia sẻ, mẫu, đang dựng, lỗi dựng |
| Thẻ module | đóng, mở (danh sách khái niệm), xong |
| Mục khái niệm | chưa học, đã học, đang mở |
| Nhãn | đã học, chưa học, module m, ngoài sách, tạo ở nơi khác, `cat_ngan` ("bài rút gọn") |
| Dải thông báo | thông tin, cảnh báo, lỗi, hết trần |
| Thông báo nổi | thành công, lỗi |
| Hộp thoại | xác nhận, nguy hiểm (gõ lại tên), khung xem trang |
| Khung chat | danh sách phiên, lượt người học, lượt trợ lý, thẻ module, tiến trình công cụ, hết trần |
| Khối bài giảng | định nghĩa, tiên quyết (gập, mở), ý, ví dụ, phân biệt, tự kiểm tra, "Tiếp theo", hỏng hẳn |
| Câu quiz | chưa chọn, đã chọn, đúng, sai, đang sinh |
| Vòng chờ | GIF 160, GIF 96, tĩnh (giảm chuyển động), vòng nhỏ trong nút |
| Khung xương | dòng chữ, thẻ, danh sách |
| Trạng thái rỗng | mặt pixel + câu + nút |
| Bảng | thường, có lọc, rỗng (quản trị, thành viên, tiến độ lớp) |
| Thanh tiến độ | ngang (module, khoá), vòng (mức dùng) |

### 8. Trạng thái và câu chữ

**Giọng văn:** xưng "bạn", câu ngắn, nói việc người dùng làm được tiếp theo. Không đổ lỗi cho người dùng. Không dùng từ kỹ thuật (`token`, `quota`, `SSE`).

**Câu báo cho mã lỗi** (bảng ở spec chức năng mục 11). Câu trong giao diện:

| mã | câu |
|---|---|
| `invalid_credentials` | Email hoặc mật khẩu chưa đúng. |
| `rate_limited` | Bạn thử nhiều lần quá. Thử lại sau {retry_after}. |
| `email_unverified` | Bạn cần xác minh email trước. [Gửi lại thư xác minh] |
| `account_disabled` | Tài khoản đang bị khoá. Liên hệ quản trị viên. |
| `not_found` | Không tìm thấy trang này, hoặc bạn chưa tham gia khoá học. |
| `forbidden` | Chỉ chủ khoá học làm được việc này. |
| `link_invalid` | Link mời không còn dùng được. Hãy xin chủ khoá một link mới. |
| `course_full` | Khoá học đã đủ người. |
| `file_too_large` | Tệp lớn hơn 10 MB. Hãy tách tài liệu theo chương rồi tải từng phần. |
| `too_many_pages` | Tài liệu dài hơn 400 trang. Hãy tách theo chương. |
| `file_invalid`, `file_encrypted` | Tệp không phải PDF hay DOCX đọc được, hoặc đang đặt mật khẩu. |
| `quota_exceeded` | Bạn đã dùng hết lượt dựng tháng này. Lượt mới có từ {resets_at}. |
| `daily_limit` (trợ lý) | Hôm nay bạn đã dùng hết lượt hỏi. Bạn vẫn đọc bài giảng, làm quiz và xem thư viện được. Lượt mới từ {resets_at}. |
| `internal_error` | Có lỗi phía máy chủ. Mã tra cứu: {ref}. |

**Mỗi trang có đủ năm trạng thái:** đang tải (khung xương), rỗng, có dữ liệu, lỗi (dải lỗi kèm "Thử lại"), không có quyền hay không tìm thấy.

### 9. Truy cập (WCAG 2.1 AA)

- Tương phản chữ ≥ 4,5:1, chữ lớn và biểu tượng ≥ 3:1 (đã chọn màu ở mục 3).
- Mọi thao tác làm được bằng bàn phím; thứ tự Tab theo thứ tự đọc; viền focus luôn thấy.
- Vùng bấm ≥ 44×44 px ở điện thoại.
- Nút chỉ có biểu tượng có `aria-label`.
- Nội dung hiện dần (bài giảng, chat) nằm trong vùng `aria-live="polite"`; không đọc lại từng chữ, chỉ đọc khi xong một ý.
- Không truyền đạt chỉ bằng màu: "đã học" có dấu tích và chữ; đúng/sai có biểu tượng và chữ.
- `lang="vi"` ở thẻ `html`.

### 10. Cấu trúc tệp Figma

Các trang trong tệp Figma:
1. **Bìa:** tên, phiên bản, link spec này.
2. **Nền tảng:** biến màu (sáng, tối), chữ, khoảng cách, bo góc, bóng, lưới; bảng cặp màu đã kiểm tương phản.
3. **Thương hiệu:** 8 logo, 6 favicon, vòng chờ (khung 0 và ghi chú chuyển động), luật dùng.
4. **Thành phần:** mục 7, mỗi thành phần đủ biến thể và trạng thái.
5. **Màn hình — điện thoại (390):** mọi trang ở mục 4, đủ năm trạng thái ở mục 8.
6. **Màn hình — máy tính (1280):** như trên.
7. **Luồng nguyên mẫu:** bốn luồng ở vé W-22.

### 11. Danh sách kiểm cho W-22

Mỗi dòng ở cả 390 px và 1280 px:
- [ ] Giới thiệu; đăng nhập; đăng ký; quên mật khẩu; đặt lại; xác minh (thành công, hết hạn).
- [ ] Khoá học của tôi: rỗng, có khoá, có lời mời, có khoá đang dựng.
- [ ] Tải giáo trình; tiến trình (đang chạy, dự toán, lỗi bản quét, xong, huỷ).
- [ ] Trang lộ trình: mặc định, module mở, khung chat mở, thư viện rỗng.
- [ ] Trang học: bài đang chờ, đang hiện dần, xong có tiên quyết mở, hỏng hẳn; khung xem trang.
- [ ] Chat: phiên mới, có lượt, thẻ module, tiến trình công cụ, phạm vi đã cũ, hết trần.
- [ ] Quiz: đang sinh, đang làm, kết quả.
- [ ] Tài liệu: tạo (chọn module), đang tạo, xem.
- [ ] Tham gia: khách, đã đăng nhập, link hỏng.
- [ ] Thành viên (chủ khoá, thành viên), bảng tiến độ lớp.
- [ ] Quản lý khoá: chia sẻ, mời, báo lỗi, xoá.
- [ ] Hồ sơ; mức dùng (còn nhiều, gần hết, hết).
- [ ] Quản trị: năm thẻ (chỉ 1280).
- [ ] 404.
- [ ] Mọi trang ở chế độ tối: ít nhất trang lộ trình, trang học, chat, quiz.

---

## Quyết định kiểm thử

- **Token là hợp đồng:** một test ở React so tệp token CSS với bảng token xuất từ Figma (JSON của plugin biến). Lệch tên hay giá trị thì đỏ. Nhóm web chọn
  plugin xuất; ghi vào báo cáo W-22.
- **Tương phản:** một test tính tương phản của các cặp token chữ/nền ở bảng mục 3, theo công thức WCAG; cặp nào dưới ngưỡng thì đỏ. Thấy đỏ trước bằng cách
  đổi thử `color-primary` sang `#29A9FF`.
- **Giảm chuyển động:** test giao diện bật `prefers-reduced-motion` và kiểm vòng chờ là ảnh tĩnh.
- **Ảnh chụp** của từng vé theo luật chung ở kế hoạch vé; W-23 đối chiếu với Figma.

## Ngoài phạm vi

- Thiết kế lại logo; bộ minh hoạ mới ngoài mặt pixel và GIF.
- Chế độ tương phản cao riêng.
- Giao diện tiếng Anh.
- Hoạt hình ngoài vòng chờ và hiện dần.

## Ghi chú thêm

- **Màu là đề xuất của Claude,** theo ủy quyền "màu bạn suy nghĩ". Chủ dự án đổi được ở bảng token; test tương phản bảo đảm không đổi sang cặp kém tương phản.
- **Khi tệp logo tới,** người thiết kế kiểm: có bản nền trong không, nền của bản trắng có phải xanh `#29A9FF` không, và mã màu trong tệp có đúng `#29A9FF` không.
  Favicon đã đo đúng `#29A9FF`.
