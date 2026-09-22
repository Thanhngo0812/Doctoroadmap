# 12 — Chạy E1 và E2 trên bộ vàng

**What to build:** Trả lời hai câu quyết định của cả đợt, **không tốn lời gọi mô hình nào**: cạnh tiên quyết nằm
ở đâu, và bộ sinh cặp nào đáng giữ. Kết quả quyết định mention map và pass phụ có vào mặc định hay không.

**Blocked by:** 05, 11, và việc gán nhãn đã đóng băng. (Việc của Claude.)

**Status:** chờ hai người gán nhãn độc lập — bộ chấm đã xong ở vé 05; bốn bảng trống đã sinh
từ artifact provenance thật ngày 2026-09-22, chưa có nhãn để chạy E1/E2.

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

- [ ] Hai người gán đã nộp file, độ đồng thuận đã tính (có kể đồng thuận ngầm qua bắc cầu), và **đã hội ý** xong;
      bộ vàng đóng băng trước khi chạy.
- [ ] Hai file gán phải **khác nhau**: đây là hai người làm độc lập, không phải một bản chép làm hai. Kiểm ngay khi
      nhận file, hai file trùng khít thì κ vô nghĩa và bộ vàng không dùng được.
- [ ] E1: bảng sáu loại vị trí, kèm NMI giữa cụm chủ đề và chương, cho cả hai giáo trình.
- [ ] E2: bảng theo từng bộ sinh và từng tổ hợp, kèm recall riêng và ba cấu hình định tuyến.
- [ ] Áp **luật chọn bộ sinh mặc định** đã viết trước ở D5, và ghi kết quả áp luật.
- [ ] Mọi số kèm khoảng tin cậy; chỗ nào khoảng chồng lấn thì viết "chưa phân biệt được".
- [ ] Báo cáo cả số trên hợp và trên giao nhãn của hai người, để xem độ nhạy.

## Bảng gán đã chuẩn bị — 2026-09-22

| Tài liệu/chương | Phạm vi section cấp 2 | Đích sau provenance | Dòng quan hệ mỗi bảng | File A1/A2 trong `artifacts/a8-gold/` |
|---|---|---:|---:|---|
| `doc-1` Chương 3, mục 3.1–3.4 | `10-13` | 45 | 360 | `doc-1-chuong-10-13-A1.xlsx` / `doc-1-chuong-10-13-A2.xlsx` |
| `doc-2` mục 3C, tr. 85–95 có đích | `98-115` | 24 | 200 | `doc-2-chuong-98-115-A1.xlsx` / `doc-2-chuong-98-115-A2.xlsx` |

Cả hai bảng của mỗi chương dùng cùng `concept_hash` và cùng graph provenance v3 để bảo đảm
phạm vi giống nhau, nhưng là **bảng trống** cho hai người làm riêng; không dùng mô hình tự điền.
`doc-1` sau provenance có 45/45 mô tả qua luật tiếng Việt; `doc-2` có 24/24 qua luật tiếng Anh.
Khi nhận lại file, kiểm A1/A2 thực sự khác nhau trước khi tính đồng thuận như checklist trên.
