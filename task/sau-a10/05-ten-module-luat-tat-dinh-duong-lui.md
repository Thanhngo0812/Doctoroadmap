# SA-05 — Tên module: luật tất định, đường lùi, mô tả khuôn

**Nguồn chân lý:** [ADR 0014](../../doc/adr/0014-ten-module-do-llm-dat.md); [spec Pha B](../../doc/pha-b-spec.md), mục 2, bất biến 12;
[báo cáo tên module](../../report/nghien-cuu-ten-va-mo-ta-module-2026-10-11.md), mục 2, 6.4, 6.5.
**Ai:** nhân viên · Claude kiểm · **Chi phí mô hình:** 0 USD · **Chặn bởi:** không, làm ngay được · **Trạng thái:** ready-for-agent

## Vì sao

Phần lớn lỗi tên hiện nay không do LLM mà do luật của chính khâu tên. Ở doc-4, 23/87 tên nhảy lên cấp chương hay phần. Có ba nguyên nhân:
- trần 12 token, mà tiếng Việt chỉ được khoảng 5–7 từ;
- kiểm cả chuỗi thay vì từng mảnh, nên lọt "Tích hợp · Giảm";
- dùng `name` thay cho `display_name`, nên còn "Tính chất 3".

Vé này sửa các luật đó và dựng đường lùi tất định mà vé 06 sẽ dùng khi lời gọi LLM hỏng.

## Cần làm

**Sửa luật khâu tên:**
- Trần độ dài tính bằng ký tự (mặc định 60) thay cho 12 token.
- Kiểm từng mảnh giữa các dấu " · ": mỗi mảnh phải là một tên khái niệm hay một tiêu đề mục nguyên vẹn.
- Dùng `display_name`.

**Làm sạch tên:**
- Bỏ số đường dẫn mục ("2.1.3") ra khỏi tên, ghi vào trường `section_code`.
- Bỏ dấu đánh số cục bộ đứng đầu ("a)", "I-", "1."), dấu ":" hay "." thừa ở cuối, và "(*)".

**Luật tạm cho vai trò `de_cuong`:** khâu tên bỏ qua vai trò `de_cuong` khi mục chứa khái niệm được dạy, chờ A2 sửa gốc.

**Bỏ nhánh dùng lại tên cũ:** không còn dùng lại tên từ artifact cũ khi băm prompt khác. Nhánh này đang giữ lại các tên mẩu cũ.

**Đường lùi tất định:**
- Module trùng đúng một mục sách, và tiêu đề không phải nhãn chung, thì dùng tiêu đề tác giả. Nhãn chung nhận bằng bằng chứng trong tài liệu:
  cùng chuỗi tiêu đề (bỏ số) có ở ít nhất 2 mục cha khác nhau.
- Nếu không, ghép 2–3 `display_name` bằng " · ": khái niệm đầu và khái niệm có nhiều cạnh cứng ra nhất.
- Hậu tố "(i/n)" chỉ là cách cuối cùng để tên không trùng.

**Mô tả khuôn** dựng từ đồ thị: "Học: A, B, C. Cần trước: X (module n)". Mỗi câu kèm `node_ids`.

**Trường mới trên module:** `title_source` ∈ {`author_section`, `fallback`}, `section_code`, `description`, `description_source = template`,
`naming_flags`. `roadmap.html` hiện mô tả và `section_code`.

**Chế độ chạy không LLM:** khâu tên chạy được ở chế độ chỉ tất định, dùng cho vé này và làm đường lùi về sau.

## Tiêu chí nghiệm thu

- [ ] Chạy lại riêng khâu tên trên sáu cuốn, không gọi mô hình: dry-run báo 0 lời gọi, nhật ký không có lời gọi.
- [ ] Bảng kiểm đọc được (`kiem_doc_duoc`) so trước và sau trên sáu cuốn. Claude đọc toàn bộ tên và ghi phán xét vào vé.
- [ ] Test, mỗi cái thấy đỏ trước:
  - ca "Tính chất 3" ra tên hiển thị;
  - tên không chứa số mục, và `section_code` đúng;
  - nhãn chung nhận bằng bằng chứng trong tài liệu;
  - kiểm từng mảnh loại được mẩu tên;
  - luật bỏ qua `de_cuong`;
  - `node_ids` của mô tả khuôn thuộc đúng module;
  - không dùng lại tên mẩu cũ.
- [ ] Ngoài tên và mô tả, artifact không đổi gì: dãy học, thành viên module, cạnh.

## Ngoài vé

Hai việc không thuộc vé này:
- lời gọi LLM đặt tên (vé 06);
- sửa gốc ở A1 và A2: dòng tiêu đề gộp, xstk mất §2 và §3, gán nhầm `de_cuong`.
