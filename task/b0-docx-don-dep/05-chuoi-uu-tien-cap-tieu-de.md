# 05 — Chuỗi ưu tiên ba bậc cho cấp tiêu đề (F35)

**What to build:** Ingest báo cáo DOCX ra đúng cây hai cấp như tác giả viết trong Word: **cả 12
section `B.` `C.` `D.` đang lạc cấp gốc quay về dưới đúng CHƯƠNG của nó**, `section_path` mang đủ
tên chương, window gom đúng phạm vi.

## Cơ chế lỗi đang sửa

Bộ dựng cây bỏ qua cấp Word đã khai (cây parse lưu đủ: chương `level=1`, mục chữ cái `level=2`),
tự suy từ chữ bằng hai regex không biết `A.` (chỉ biết `A)`) và không biết `CHƯƠNG I` số La Mã
(chỉ biết chữ số). Mọi mục chữ cái suy ra cấp 1; guard theo `tree_depth` chỉ cứu được mục đầu
(`A.` — 5 cảnh báo clamp toàn của `A.` là dấu vân tay), từ `B.` trở đi bật lên cấp gốc.

## Luật mới — ba bậc, bằng chứng mạnh trước

1. **Đánh số tường minh trong văn bản** — mục số (`1.`, `2.3.`), từ khoá chương **mở rộng nhận số
   La Mã** (`CHƯƠNG I`, `CHƯƠNG IV`), mục chữ cái **mở rộng nhận cả chấm lẫn ngoặc** (`A.` và `A)`,
   một chữ cái Unicode bất kỳ kể cả `Đ`).
2. **Cấp khai báo của cây parse, khi cây khai không thoái hoá** — tiêu đề của tài liệu khai từ hai
   cấp phân biệt trở lên ⇒ tin cấp khai. Số đo neo quyết định: bốn tài liệu hiện có, chỉ DOCX có
   phân cấp thật `{1: 9, 2: 17}`; ba PDF phẳng toàn cấp 1 — phép phân biệt tách đúng 4/4, không cần
   biết định dạng nguồn.
3. **Suy diễn hiện hành** — giữ nguyên cho cây thoái hoá.

Guard kẹp theo `tree_depth` và **toàn bộ** bộ lọc tiêu đề giả giữ nguyên — chúng trả lời *có phải
tiêu đề không*, độc lập với *cấp mấy*.

**Nhích `CHUNK_ALGORITHM_ID` một lần — cú nhích duy nhất của cả đợt cho tầng chunk** (ticket 06 và
08 cũng đổi tầng này nhưng không nhích nữa).

**Blocked by:** 02 — số vàng phải có trước để cú tái cấu trúc cây nhìn thấy được từng con số.

**Status:** done

- [x] Trên fixture DOCX: đủ 27 section, cây hai cấp, **0 section chữ-cái ở cấp gốc**, mọi
      `section_path` của mục chữ cái mở đầu bằng tên CHƯƠNG của nó
- [x] Có test cây tay: `CHƯƠNG IV` (La Mã) ra cấp 1; `A.` và `A)` và `Đ.` ra cấp con của mục số
      gần nhất; cây khai hai cấp được tin nguyên trạng; cây khai phẳng rơi về suy diễn
- [x] Có test: đánh số tường minh **thắng** cấp khai báo khi hai bên mâu thuẫn
- [x] Hồi quy hai giáo trình: **không một định danh chunk nào đổi** — cây phẳng đi đường suy diễn
      y như tám vòng qua
- [x] Hồi quy regex mở rộng: các tiêu đề thật của hai giáo trình (`a) Chọn kiểu mô hình:`,
      `TẬP THỂ TÁC GIẢ:`, mục số) không bị hai regex mới bắt nhầm sang cấp khác
- [x] Số vàng: DOCX đổi đúng phần cây (27 section giữ nguyên số lượng, cấu trúc cha đổi);
      slide **đứng yên** — cây khai phẳng của nó không việc gì
- [x] `CHUNK_ALGORITHM_ID` nhích đúng một lần
