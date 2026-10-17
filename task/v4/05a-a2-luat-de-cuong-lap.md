# 05a — A2: tiêu đề lặp chỉ là đề cương khi thân mục là danh sách tên mục

**Nguồn chân lý:** [nghiên cứu vé 05](../../report/v4-05-a2-de-cuong-lap-2026-10-17.md), mục 1 · kế hoạch v4, hàng 05.
**Ai:** nhân viên · **Chi phí mô hình:** 0 USD · **Chặn bởi:** không · **Trạng thái:** chờ giao

## Vì sao

**Luật hiện nay.** Trong `assign_section_roles`, một tiêu đề là mục con đầu tiên của ít nhất 3 mục cha thì mọi mục mang tiêu đề đó nhận `de_cuong`,
nguồn `structure`. Lớp nhãn LLM (`label-roles`) không ghi đè được nhãn này.

**Luật bắt sai nhiều hơn bắt đúng.** Trên 26 tài liệu (trừ T-01), luật bắt 26 nhóm tiêu đề:
- 1 nhóm là đề cương thật: "Nội dung" của doc-6;
- 7 nhóm là câu hỏi, bài tập hoặc đáp án;
- 5 nhóm là mục tiêu hoặc giới thiệu chương;
- 13 nhóm là nội dung dạy: "Cách giải" (xstk), "1.1. Khái niệm" (d01-10), "I. Định nghĩa" (d01-02)…

**Hậu quả ở xstk.** 13 mục "Cách giải" thành đề cương, nên:
- 9/25 khái niệm đích của vàng rơi khỏi dãy học;
- chỉ 32/62 cạnh vàng có cả hai đầu trong dãy học.

Mô phỏng 0 USD cho thấy sau khi sửa, 8 trong 9 khái niệm có câu ứng viên neo từ đúng phần dạy. Trần là 59/62 cạnh.

**Dấu hiệu tách được, không phụ thuộc ngôn ngữ:** thân của mục đề cương chủ yếu là tên các mục khác. Trung vị độ phủ của "Nội dung" doc-6 là 0,62; của
mọi nhóm khác ≤ 0,44; của "Cách giải" là 0.

## Cần làm

**1. Đổi điều kiện của nhánh "tiêu đề lặp" trong `assign_section_roles`.**
- Giữ cách đếm như cũ: tiêu đề là mục con đầu tiên của ≥ 3 mục cha.
- Cả nhóm mục mang tiêu đề đó chỉ nhận `de_cuong` (nguồn `structure`) khi **trung vị độ phủ** của nhóm ≥ 0,5.
- **Định nghĩa độ phủ** của một mục:
  - tỉ lệ ký tự chữ, số trong văn bản chunk của chính mục đó mà nằm trong một lần xuất hiện tên của một mục khác cùng tài liệu;
  - khớp theo ranh giới từ;
  - chuẩn hoá cả hai phía: NFC, casefold, bỏ dấu câu, gộp khoảng trắng, bỏ số thứ tự ở đầu tiêu đề;
  - không tính tên của chính nhóm; bỏ tên ngắn hơn 3 ký tự.
- **Mục có thân rỗng** không có độ phủ. Nhóm không có mục nào có độ phủ thì không đạt.
- **Nhóm không đạt** thì luật lặp bỏ qua nhóm đó: mục đi tiếp các nhánh cấu trúc còn lại như thể luật lặp không có. Với các ca đã đo (mục con như
  "Cách giải"), kết quả là `role_source` rỗng, và lớp nhãn LLM quyết. Không gán `noi_dung` thay. Lý do:
  - bỏ sót một đề cương thì vẫn an toàn, vì lớp LLM có nhãn `de_cuong`;
  - gán nhầm nội dung là đề cương thì khái niệm rơi khỏi dãy học mà không lời gọi nào được hỏi.
- **Giữ nguyên** nhánh mục lục (`is_toc`), nhánh cuối sách và nhánh mở đầu.
- **Không dùng** danh sách từ khoá của ngôn ngữ nào.
- **Mã tham chiếu:** `norm` và `coverage` trong `scripts/a2-de-cuong/do_phu_tieu_de.py`. Đây là mã nghiên cứu, không phải mã sản phẩm. Kết quả
  của bản cài phải khớp bảng trong báo cáo.

**2. Khoá cache.**
- Không đổi `CHUNK_ALGORITHM_ID`, `chunk_id`, văn bản hay offset. Chunk của `ingest` cũ vẫn tái dùng được, và A3 của tài liệu cũ **không** chạy lại.
- Artifact nào chứa vai trò tính bằng luật mới phải có băm cấu hình khác bản cũ: `label-roles` (`region_roles.algorithm_id`) và `refresh_chunk_roles`.
  Không được dùng âm thầm artifact vai trò cũ dưới luật mới.
- Nên dùng một mã luật vai trò riêng, thay vì dùng chung hằng số với thuật toán chunk như `refresh_chunk_roles` đang làm.

**3. Kiểm 0 USD trên kho thật.**
- Viết một script chỉ đọc: chạy luật mới trên `sections.json` và `chunks.json` đã lưu của mọi tài liệu, **trừ `d01-t01`, `d01-t02`** và `smoke*`.
- In mỗi nhóm lặp: tài liệu, tiêu đề, số mục, độ phủ trung vị, vai trò cũ, vai trò mới.
- `label-roles --dry-run` cho xstk (chunk v3) và doc-4, báo số mục chờ nhãn LLM. xstk cần cờ `--allow-text-quality-reason` như khuôn T10 trong
  `CONTEXT.md`.

## Không làm

- Không chạy `label-roles`, `a4` hay `roadmap` có chi. Việc đó thuộc vé [05b](05b-chay-lai-xstk-doc4.md) của Claude.
- Không sửa bước neo, prompt nhãn vùng, hay luật bỏ qua khái niệm ngoài vùng nội dung. Nghiên cứu mục 3 đo thấy luật đó đúng ở 30/32 ca ngoài xstk.
- Không chạy lại 16 cuốn D-01 (đã đóng băng).

## Nghiệm thu

- [ ] **Test dựng tay theo hình dạng các ca thật**, chạy trên `assign_section_roles` và `label-roles` với mô hình giả:
  - nhóm kiểu "Cách giải": là mục con đầu của ≥ 3 mục cha, thân là lời giải → không nhận `de_cuong`, `role_source` rỗng, và được đưa cho mô hình ở
    `label-roles`. **Phải đỏ trên mã hiện nay**;
  - nhóm kiểu "Nội dung": thân là tên các mục phía sau → vẫn `de_cuong`, nguồn `structure`;
  - nhóm thân rỗng → không nhận `de_cuong`;
  - nhóm câu hỏi ôn tập có nhắc vài tên mục, độ phủ dưới 0,5 → để lớp LLM quyết.
- [ ] **Test khoá cache:** luật mới làm đổi băm cấu hình của `label-roles`. `chunk_id`, văn bản, offset và cấu hình chunk của `ingest` không đổi.
- [ ] **Bảng kiểm 0 USD** (mục 3) khớp báo cáo nghiên cứu: trên kho thật, chỉ còn "Nội dung" của doc-6 nhận `de_cuong` theo luật lặp. Có số mục chờ
      nhãn của xstk và doc-4.
- [ ] Toàn bộ test qua.
