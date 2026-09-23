# 12 — Chạy E1 và E2 trên bộ vàng

**What to build:** Trả lời hai câu quyết định của cả đợt, **không tốn lời gọi mô hình nào**: cạnh tiên quyết nằm
ở đâu, và bộ sinh cặp nào đáng giữ. Kết quả quyết định mention map và pass phụ có vào mặc định hay không.

**Blocked by:** 05, 11, và việc gán nhãn đã đóng băng. (Việc của Claude.)

**Status:** **đã có nhãn của cả hai người trên cả hai chương (2026-09-23)**; κ đã tính và đạt mốc văn liệu.
Chờ **hội ý** hai file `-hoi-y.xlsx` rồi mới đóng băng bộ vàng và chạy E1/E2.

> **Hai chương vàng (chủ dự án chốt 2026-09-18, hướng a):** một chương giữa của `doc-1` (tiếng Việt) và một
> chương giữa của `doc-2` (tiếng Anh). Bộ vàng song ngữ, nên **mọi bảng phải tách theo từng chương**, không gộp
> hai ngôn ngữ thành một con số. Xem spec D13.
>
> **⚠️ Danh sách rút gọn cho `doc-1` đã hết hiệu lực ngày 2026-09-22.** Chủ dự án thay `doc-1` bằng một PDF khác
> vì bản cũ hỏng lớp text (24 ký tự có dấu trên 42.087 ký tự chữ cái = 0,06%; `Tính chất` ra thành `T‰nh ch§t`).
> Bản mới là **một cuốn khác** — *Bài giảng Đại số tuyến tính*, Đại học Hàng hải, **102 trang, 5 chương**, sạch
> watermark, 25,46% ký tự có dấu. Mọi số trang và tên chương của `doc-1` ở bản trước đều không còn dùng được.
> **Danh sách rút gọn mới nằm ở vé 19**, reviewer đề xuất **Chương 3 — Không gian véc tơ** (tr. 44–74, 5 mục).
>
> **Danh sách rút gọn cho `doc-2` vẫn giữ nguyên (2026-09-20, đo thẳng trên PDF):**
>
> | | `doc-2` (Axler, tiếng Anh) |
> |---|---|
> | ⭐ đề xuất | **3C — Matrices**, tr. 83–96 (14 tr, 9 "definition") |
> | B | 5A — Invariant Subspaces, tr. 147–156 (10 tr, 5) |
> | C | 2A — Span and Linear Independence, tr. 43–52 (10 tr, 8) |
>
> Số khái niệm đích thật chỉ biết được sau vé 19 (`a8-gold-sheet --list-chapters`); nếu chương chọn ra dưới 15 hoặc
> trên 45 khái niệm thì ghép thêm/bớt một mục liền kề, đúng cơ chế dải mục của vé 04.

## Lượt gán thật — 2026-09-23

Bốn bảng đã nộp và **kiểm hợp lệ: 0 lỗi, 0 cảnh báo** ở cả bốn.

| | A1 | A2 | cùng ghi | chỉ A1 | chỉ A2 | Jaccard | **κ trực tiếp** | **κ có bắc cầu** |
|---|---|---|---|---|---|---|---|---|
| `doc-1` Chương 3, dải 10-12 (VN) · 26 đích / 225 khái niệm | 40 | 35 | 23 | 17 | 12 | 0,442 | **0,611** | **0,733** |
| `doc-2` mục 3C, dải 98-115 (EN) · 24 đích / 438 khái niệm | 59 | 54 | 46 | 13 | 8 | 0,687 | **0,813** | **0,818** |

Cờ người gán nêu: doc-1 A1 17 / A2 13 · doc-2 A1 18 / A2 14.

**Hai file của mỗi chương khác nhau thật** — không có ca trùng khít, nên κ có nghĩa.

**Đối chiếu văn liệu** (báo cáo vòng 36 mục 7): LectureBank đạt **κ = 0,7** với hai nghiên cứu sinh gán nhãn nhị
phân, và nói rõ bản ba mức trước đó chỉ được **κ = 0,3** trên **cùng các cặp**. PREAP đạt **0,45–0,71** khi gán
trong lúc đọc giáo trình. Vậy `doc-2` ở 0,813 **vượt mốc LectureBank**, còn `doc-1` ở 0,611 trực tiếp / 0,733 có
bắc cầu nằm **trong dải PREAP và đạt mốc LectureBank khi tính đồng thuận ngầm**.

**Một bất đối xứng đáng đưa vào báo cáo:** bắc cầu nâng κ của `doc-1` từ 0,611 lên 0,733 (+0,122) nhưng chỉ nâng
`doc-2` từ 0,813 lên 0,818 (+0,005). Nghĩa là phần lớn bất đồng trên `doc-1` là **"một người ghi cạnh trực tiếp,
người kia ghi đường vòng"** — đúng ca *long dependencies* mà LectureBank chỉ đích danh là nguồn bất đồng chính.
Đây là lý do D13 bắt tách số theo từng chương thay vì gộp hai ngôn ngữ.

**File hội ý đã sinh:**

| file | cùng ghi | phải quyết |
|---|---|---|
| `artifacts/a8-gold/doc-1-chuong-10-12-hoi-y.xlsx` | 23 | **29** |
| `artifacts/a8-gold/doc-2-chuong-98-115-hoi-y.xlsx` | 46 | **21** |

### Thời gian gán: **không đo được ở lượt này** (chủ dự án chốt 2026-09-23, cách b)

> **Đính chính của reviewer.** Tôi có viết hai lần rằng "E7 cần ô thời gian" — **sai**. E7 đo *cái giá của các bước
> nhất quán* (cạnh vàng bị cắt chu trình, bị đánh dấu thừa, bị tỉa; precision theo `evidence_hard`), **không dùng
> thời gian gán**. Ô thời gian tồn tại vì lý do khác: PREAP đo thời gian gán như một dữ kiện về giao thức.

Cả bốn bảng để trống `annotation_minutes` và `revision_minutes`. Luật của dự án từ phase trước
(`task/a4-a5-hop-nhat/06-nguoi-dung-gan-mu-bo-vang.md`) là **"ghi thời gian gán thật, không ước lượng"**, nên
không điền số suy đoán. **Báo cáo phải ghi thẳng: lượt gán này không đo thời gian.**

Chủ dự án tự khai: cặp làm trước vào buổi chiều, cặp sau vào chiều 23/9. Metadata trong file cho thấy khác một
ngày ở cặp trước, và đây là toàn bộ bằng chứng cứng có được:

| file | created | modified | đọc ra |
|---|---|---|---|
| `doc-2-...-A2-output` | 22/9 12:02:04 | **22/9 14:34:26** | có vết sửa thật |
| `doc-1-...-A2-output` | 22/9 13:10:56 | **22/9 14:34:26** | có vết sửa thật |
| `doc-1-...-A1-output` | 23/9 07:25:26,25 | 23/9 07:25:26,25 | máy ghi, **không có vết sửa** |
| `doc-2-...-A1-output` | 23/9 07:25:26,32 | 23/9 07:25:26,32 | máy ghi, **không có vết sửa** |

Bảng trống chỉ sinh ngày **22/9** (doc-2 lúc 12:02, doc-1 lúc 13:10), nên **không thể gán ngày 21/9**.

Khoảng 83 phút (`doc-1` A2) và 152 phút (`doc-2` A2) là **khoảng từ lúc sinh bảng tới lúc lưu**, tức **biên trên**,
**không phải thời gian ngồi làm**. Đừng trích chúng như số đo.

- [x] Hai người gán đã nộp file, độ đồng thuận đã tính (có kể đồng thuận ngầm qua bắc cầu); **còn chờ hội ý**;
      bộ vàng đóng băng trước khi chạy.
- [x] Hai file gán phải **khác nhau**: đây là hai người làm độc lập, không phải một bản chép làm hai. Kiểm ngay khi
      nhận file, hai file trùng khít thì κ vô nghĩa và bộ vàng không dùng được.
- [ ] E1: bảng sáu loại vị trí, kèm NMI giữa cụm chủ đề và chương, cho cả hai giáo trình.
- [ ] E2: bảng theo từng bộ sinh và từng tổ hợp, kèm recall riêng và ba cấu hình định tuyến.
- [ ] Áp **luật chọn bộ sinh mặc định** đã viết trước ở D5, và ghi kết quả áp luật.
- [ ] Mọi số kèm khoảng tin cậy; chỗ nào khoảng chồng lấn thì viết "chưa phân biệt được".
- [ ] Báo cáo cả số trên hợp và trên giao nhãn của hai người, để xem độ nhạy.

## Bảng gán đã chuẩn bị — 2026-09-22

> **Bảng dưới đã lỗi thời cho `doc-1`.** Dải `10-13` (45 đích, 360 dòng) **không được dùng**; reviewer chốt lại
> dải `10-12` ngày 2026-09-22 vì 360 dòng nhiều hơn 73% so với khối lượng đã hiệu chuẩn bằng lượt thử. Lượt gán
> thật chạy trên dải `10-12`. Giữ bảng để tra lịch sử.

| Tài liệu/chương | Phạm vi section cấp 2 | Đích sau provenance | Dòng quan hệ mỗi bảng | File A1/A2 trong `artifacts/a8-gold/` |
|---|---|---:|---:|---|
| ~~`doc-1` Chương 3, mục 3.1–3.4~~ | ~~`10-13`~~ | ~~45~~ | ~~360~~ | ~~`doc-1-chuong-10-13-*.xlsx`~~ **không dùng** |
| **`doc-1` Chương 3, mục 3.1–3.3** | **`10-12`** | **26** | **208** | `doc-1-chuong-10-12-A1.xlsx` / `-A2.xlsx` |
| `doc-2` mục 3C, tr. 85–95 có đích | `98-115` | 24 | 200 | `doc-2-chuong-98-115-A1.xlsx` / `-A2.xlsx` |

Cả hai bảng của mỗi chương dùng cùng `concept_hash` và cùng graph provenance v3 để bảo đảm
phạm vi giống nhau, nhưng là **bảng trống** cho hai người làm riêng; không dùng mô hình tự điền.
`doc-1` sau provenance có 45/45 mô tả qua luật tiếng Việt; `doc-2` có 24/24 qua luật tiếng Anh.
Khi nhận lại file, kiểm A1/A2 thực sự khác nhau trước khi tính đồng thuận như checklist trên.
