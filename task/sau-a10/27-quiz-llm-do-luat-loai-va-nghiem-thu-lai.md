# SA-27 — Quiz LLM: ghi luật loại câu, sửa theo số đo, nghiệm thu lại vé 16

**Nguồn chân lý:** [báo cáo quiz](../../report/nghien-cuu-quiz-tu-kiem-tra-2026-10-11.md); vé [16](16-quiz-llm-theo-khai-niem.md);
[báo cáo kiểm thử 2026-10-18](../../report/kiem-thu-pha-b-2026-10-18.md), mục 3.5, 4.
**Ai:** nhân viên · Claude kiểm và quyết luật nào sửa · **Chi phí mô hình:** 0 USD cho phần đo (phát lại); lượt thật vé 16 dry-run trước, chủ dự án
duyệt · **Chặn bởi:** nhân viên commit mã Pha B còn dở · **Trạng thái:** đã triển khai, phát lại và chạy thật hai module; chờ Claude soát độc lập

**Bàn giao 2026-10-18:** mã nền đã commit ở `bbcfcc6`. Chủ dự án duyệt lượt mới tối đa 0,50 USD trong tổng 1 USD cho SA-27/28. Lượt hai module chi 0,0782415 USD, có 35 lời gọi thành công; xem [báo cáo SA-27](../../report/pha-b-sa27-2026-10-18.md). Phán xét nội dung và quyết định điều phối về luật tên trong đề vẫn cần Claude soát độc lập; không đánh dấu các ô nghiệm thu thay Claude.

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

### Quyết định triển khai 2026-10-18, trước khi sửa luật

Codex điều phối theo yêu cầu chủ dự án triển khai vé 25–28; phần này chờ Claude soát độc lập. Phát lại V1–V4 không gọi API cho thấy:
- V1: 144 ứng viên bị loại vì nhãn nguồn đúng dùng ID chunk thô thay vì nhãn S/D.
- V2: 67 ứng viên; 47 sai khớp `from`/nguồn, 14 quote câu nhiễu sai, 5 quote đáp án đúng sai, 1 đáp án quá dài.
- V3: 4 ứng viên; 2 qua luật cục bộ, 1 phương án chứa nhau, 1 bị luật tên khái niệm trong đề; cả hai bản kiểm đều không kết luận được câu nhiễu.
- V4: 2 ứng viên; 1 qua luật cục bộ và kiểm mù, 1 phương án chứa nhau.

Quyết định: **chỉ sửa luật tên khái niệm trong đề theo điều kiện đã nêu ở mục 3**. Giữ việc loại khi đáp án đúng là tên hoặc alias của chính khái niệm đó. Không nới nhãn nguồn, `from`, quote, độ dài, phương án chứa nhau hay kết luận không đủ bằng chứng của bộ kiểm. Bảng đo không chứng minh các trường hợp ấy là loại oan. Không có lời gọi kiểm đã ghi thì chỉ báo qua luật cục bộ, không tự coi câu là được chấp nhận. Chi tiết mẫu ở `tmp/phaseb-sa27-replay-v1-v4.json` và báo cáo SA-27.

- [x] Bảng loại theo luật từ phát lại V1–V4, 0 USD, đính kèm ở `report/pha-b-sa27-2026-10-18.md` và `tmp/phaseb-sa27-replay-v1-v4.json`.
- [ ] Quyết định triển khai đã được Codex điều phối ghi vào vé trước khi sửa mã; Claude soát độc lập và phê chuẩn quyết định còn pending.
- [x] Regression tests chạy xanh:
  - lời gọi kiểm chọn sai, verdict đầy đủ, thì câu bị bỏ (sửa sai M10 phải đỏ);
  - mỗi luật được sửa có một ca giữ đúng và một ca vẫn loại đúng;
  - mỗi câu bị loại có đúng một mã luật trong nhật ký.
- [x] Phát lại V1–V4 sau khi sửa: V3 qua local tăng từ 2/4 lên 3/4; verifier vẫn loại 2 do nguồn không phân biệt. V1/V2/V4 không đổi. Chi phí $0.
- [x] Lượt thật vé 16 trên 2 module sau dry-run và duyệt; 8 LLM items returned. Codex điều phối đã đọc 13 biến thể verifier-passed trong bank và ghi phán xét ở báo cáo. Phán xét độc lập của Claude còn pending.

### Kết quả lượt thật SA-27, 2026-10-18

- doc-1 v53, `module_001`: 7/8 ready; $0.028338; 9 generation + 7 verifier calls; 21.306 s tới câu đầu, 25.958 s tới câu cuối.
- doc-4 v23, `module_001`: 4/7 ready; $0.049904; 13 generation + 6 verifier calls; 6.192 s tới câu đầu, 11.060 s tới câu cuối.
- Tổng: 11/15 câu ready, $0.0782415; acceptance recording có 35 phản hồi model hợp lệ. Đầu lượt sandbox chỉ tạo 15 lỗi transport, 0 USD; không tính là lượt nghiệm thu.
- Replay ghi 42 ứng viên: 17 qua luật cục bộ, 13 được verifier chấp nhận, 4 bị loại vì nguồn không phân biệt; cache bank có 13 biến thể LLM, lượt đầu trả 8 và giữ 5 biến thể để xoay vòng. Ba câu fallback cloze được trả thêm.
- Đọc thủ công 13 biến thể bank: không thấy câu trả lời sai hoặc mâu thuẫn với trích dẫn. Đây là smoke review, không phải đánh giá chất lượng vé 22.

## Ngoài vé

Hai việc không thuộc vé này: đánh giá chất lượng quiz (vé 22), và đổi mô hình kiểm.
