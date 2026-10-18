# SA-27 — Quiz LLM: ghi luật loại câu, sửa theo số đo, nghiệm thu lại vé 16

**Nguồn chân lý:** [báo cáo quiz](../../report/nghien-cuu-quiz-tu-kiem-tra-2026-10-11.md); vé [16](16-quiz-llm-theo-khai-niem.md);
[báo cáo kiểm thử 2026-10-18](../../report/kiem-thu-pha-b-2026-10-18.md), mục 3.5, 4.
**Ai:** nhân viên · Claude kiểm và quyết luật nào sửa · **Chi phí mô hình:** 0 USD cho phần đo (phát lại); lượt thật vé 16 dry-run trước, chủ dự án
duyệt · **Chặn bởi:** nhân viên commit mã Pha B còn dở · **Trạng thái:** ready-for-agent

## Vì sao

Quiz LLM gần như chưa chạy được:
- lượt V2 có 34 lời gọi sinh, 0 câu qua luật cục bộ, nên lời gọi kiểm chưa chạy lần nào;
- cả bốn lượt (0,29 USD) chỉ ra 1 câu `generator=llm`.

Mã không ghi câu bị loại vì luật nào, nên không biết sửa gì. Đọc mã có một nghi phạm:
- `_rules_pass` loại mọi câu có tên khái niệm trong đề.
- Luật này đúng khi đáp án là tên khái niệm, vì đề tự lộ đáp án.
- Nhưng nó loại luôn mọi câu hỏi về tính chất hay vai trò của một khái niệm có tên trong đề.

Đây mới là giả thuyết; vé này đo trước rồi mới sửa.

Thêm một test thiếu: lời gọi kiểm chọn sai đáp án chưa được test riêng (sửa sai M10 sống).

## Cần làm

**1. Ghi lý do loại.**
- Mỗi câu ứng viên bị loại ghi một mã luật. Hai nguồn loại:
  - các nhánh trả `None` của `_normalize_item`: sai khái niệm, nhãn nguồn, câu trích, số phương án, `from` của câu nhiễu, câu nhiễu cùng chunk;
  - từng luật của `_rules_pass`.
- Lời gọi kiểm cũng ghi lý do: chọn sai, `valid` sai, câu trích không thấy, verdict thiếu, "đúng theo nguồn", "nguồn không nói".
- Ghi vào nhật ký hoặc sổ chi, không vào đề công khai.

**2. Đo bằng phát lại, 0 USD.**
- Phát lại mọi phản hồi sinh đã ghi của nhóm 3 (V1–V4) qua bộ ghi lý do.
- Ra bảng: số câu ứng viên, số câu bị loại theo từng mã luật, theo cuốn.
- Claude đọc bảng và một mẫu câu bị loại ở mỗi luật lớn, rồi quyết luật nào sửa. Quyết định ghi vào vé này trước khi sửa.

**3. Sửa theo quyết định ở bước 2.** Ứng viên đã biết là luật tên khái niệm trong đề, đổi thành có điều kiện: chỉ loại khi đáp án đúng là tên hay alias
của khái niệm đó. Các luật khác chỉ sửa nếu bảng đo chỉ ra.

**4. Test lời gọi kiểm.** Lời gọi kiểm chọn sai đáp án, dù mọi verdict của câu nhiễu đều "sai theo nguồn", thì câu vẫn bị bỏ.

**5. Lượt thật vé 16.** Làm lại theo tiêu chí gốc: 2 module (doc-1, doc-4), dry-run trước, chủ dự án duyệt, trong trần chung. Báo:
- USD mỗi module;
- giây tới câu đầu và tới câu cuối;
- tỉ lệ bỏ câu theo từng luật và theo lời gọi kiểm;
- tỉ lệ khái niệm còn ít nhất 1 câu LLM.

Ghi lại phản hồi để phát lại.

## Tiêu chí nghiệm thu

- [ ] Bảng loại theo luật từ phát lại V1–V4, 0 USD, đính kèm vào vé.
- [ ] Quyết định sửa luật nào được Claude ghi vào vé trước khi sửa mã.
- [ ] Test, mỗi cái thấy đỏ trước rồi mới xanh:
  - lời gọi kiểm chọn sai, verdict đầy đủ, thì câu bị bỏ (sửa sai M10 phải đỏ);
  - mỗi luật được sửa có một ca giữ đúng và một ca vẫn loại đúng;
  - mỗi câu bị loại có đúng một mã luật trong nhật ký.
- [ ] Phát lại V1–V4 sau khi sửa: báo số câu qua luật cục bộ trước và sau (vẫn 0 USD, vì lời gọi kiểm chưa có bản ghi thì không chạy).
- [ ] Lượt thật vé 16 trên 2 module, sau dry-run và duyệt. Claude đọc mọi câu LLM được chấp nhận và ghi phán xét.

## Ngoài vé

Hai việc không thuộc vé này: đánh giá chất lượng quiz (vé 22), và đổi mô hình kiểm.
