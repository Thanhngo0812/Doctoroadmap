# 17j — Sửa sau lượt nghiệm thu đầu của chuỗi gộp

**Nguồn chân lý:** [spec gộp khâu trước A8](../../doc/gop-khau-truoc-a8-spec.md), mục 3.2, 3.3 và 4; số đo của Claude ngày 2026-10-16 (dưới đây).
**Ai:** nhân viên · **Chi phí mô hình:** 0 USD (test bằng mô hình giả) · **Chặn bởi:** 17a–17h · **Trạng thái:** sẵn sàng giao

## Vì sao

Lượt chạy thật đầu tiên của vé 17i, trên kho riêng với gemini-3.1-flash-lite, cho ra ba vấn đề.

**1. Chương trình sập khi một lời gọi A5 gộp trượt kiểm sau mọi lượt sửa.**
- Ở xstk-ch3-1, `a4` chuỗi gộp dừng với `lỗi: 'reused'` sau 115 giây; doc-4 dừng vì cùng lỗi sau 16 phút. Tài liệu lớn gần như chắc gặp lỗi này.
- Gốc lỗi:
  - hàng nhật ký mà `run_model_jobs` trả cho lời gọi hỏng không có khoá `reused`;
  - đoạn gắn nhật ký neo của lời gọi A5 gộp lại đọc `row["reused"]`.
- Canonical không có checkpoint, nên mọi lời gọi đã trả tiền của lượt đó mất trắng.

**2. Gom lô lời phán sửa làm A4 bỏ sót các cặp đồng nghĩa và bản dịch.**

Đo trên các lời phán sửa có thật của nhap-mon-ml (17 lô, 158 mục). Script ở `scripts/gop-khau/thu_prompt_gop.py`.

| Biến thể | Các cặp v3 có mà chuỗi gộp bỏ sót, được gộp lại | USD |
|---|---|---|
| prompt chuỗi gộp, lô cỡ 10 (cấu hình hiện nay, hỏi lại) | 1/5; mô hình ghi `same_as` / `synonym` / `synonym_of` giữa hai node tách | 0,094 |
| prompt chuỗi gộp, mỗi mục một lời | **5/5** | 0,111 |
| prompt sửa thử, mỗi mục một lời | 5/5, y hệt | 0,114 |

- Năm cặp là: Modeling = Giai đoạn mô hình hoá, Thuật toán học = Giải thuật học, Data preparation = Tiền xử lý dữ liệu, Lớp mô hình = Kiểu mô
  hình, Hiệu chỉnh = Kỹ thuật hiệu chỉnh.
- doc-6 cho cùng kết quả: CSDL = Cơ sở dữ liệu và DBMS = Hệ Quản Trị CSDL chỉ được gộp khi hỏi từng mục.
- **Kết luận:** prompt không có lỗi. Gom lô làm mô hình né gộp, và gần như không bớt tiền vì token vào chiếm phần lớn chi phí.

**3. Luật R2 không bắt được nhãn `synonym`.**
- R2 coi một quan hệ đồng nhất nối hai node tách rời là tự mâu thuẫn. Nó chỉ nhận đúng năm nhãn: `same_as`, `equivalent_to`, `identical_to`,
  `synonym_of`, `alias_of`.
- Mô hình còn ghi `synonym` (doc-6, nhap-mon-ml), nên lời phán tự mâu thuẫn đi lọt thành quan hệ đề xuất.

## Cần làm

1. **Lời gọi A5 gộp bị hỏng không được làm sập stage.**
   - Phần mô tả đi đường dự phòng như hiện nay (`draft_fallback_invalid`).
   - Các khái niệm trong lời gọi đó đi đường neo "một khái niệm" của vé 17b. Vẫn hỏng thì nhận `uncertain` và được giữ, đúng hợp đồng C8.
2. **Mặc định cỡ lô phán sửa của chuỗi `gop` là 1.**
   - Giữ tuỳ chọn cấu hình để đo lại sau.
   - Cập nhật `.env.example`.
   - Chuỗi v3 không đổi.
3. **Chỉ ở chuỗi `gop`, R2 nhận thêm các nhãn đồng nhất.**
   - So **đúng nhãn sau chuẩn hoá**, không so chuỗi con: `same_category` không phải nhãn đồng nhất.
   - Tối thiểu gồm: `synonym`, `synonym_of`, `same_as`, `alias`, `alias_of`, `abbreviation`, `abbreviation_of`, `acronym`, `acronym_of`,
     `initialism_of`, `translation`, `translation_of`, `equivalent_to`, `identical_to`.
   - Đổi mã luật kiểm trong config của chuỗi `gop`. Config và cache của chuỗi v3 giữ nguyên.

## Nghiệm thu

- [ ] Test qua `execute` của stage canonical, với mô hình giả luôn trả lời hỏng cho một lời gọi A5 gộp: stage không sập; phần mô tả nhận
      `draft_fallback_invalid`; neo của các khái niệm trong lời gọi đó được hỏi lại riêng. Test này phải đỏ trên mã hiện nay (`KeyError: 'reused'`).
- [ ] Không đặt cấu hình thì chuỗi `gop` phán sửa mỗi cặp một lời. Đặt cỡ lô khác 1 thì vẫn gom lô như vé 17f. Khoá cache đổi theo cỡ lô.
- [ ] Ở chuỗi `gop`, quan hệ `synonym` nối hai node tách rời bị bắt phán lại; `same_category` thì không. Ở chuỗi v3, hành vi và băm config
      không đổi.
- [ ] Mỗi luật chặn có ít nhất một test thấy nó trượt khi luật bị bỏ. Toàn bộ test qua.
- [ ] Commit phần vé 17 (17a–17j) tách riêng khỏi các thay đổi Pha B đang có trong cây làm việc.
