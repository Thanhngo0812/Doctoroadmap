# Spec tài liệu `document-3`: viết tự nhiên theo yêu cầu

**Ngày:** 2026-10-24 · **ADR:** [0027](adr/0027-tai-lieu-3-viet-tu-nhien.md) · **Liên quan:** [spec bài giảng 3](bai-giang-3-spec.md) mục 11 (chữ thô công thức,
ảnh trang); ADR 0024 (luật kiểm chỉ ghi log); spec Pha B2 mục 7 (phạm vi, thư viện) · **Vé:** SA-67

## Vấn đề

Người học bấm "Tạo tài liệu", hay nhờ trợ lý tạo, để có đề cương ôn tập, bảng công thức, bảng so sánh, hay hướng dẫn từng bước cho vài module. Bản hiện tại
(`document-2`) trả 280–1.583 ký tự, không công thức, có khi lạc đề. Lý do:
- tư liệu bị cắt mất đúng khái niệm được hỏi;
- đầu ra JSON buộc trích nguyên văn;
- hậu kiểm xoá câu không có nhãn và câu có công thức.

## Giải pháp

Mô hình đọc tư liệu rộng của các module được chọn, cùng chữ thô và ảnh trang của công thức, rồi viết thẳng một tài liệu Markdown đúng thứ người học xin.
Chữ hiện dần khi mô hình viết. Kiểm chỉ ghi log cho admin.

## User stories

1. Là người học, tôi muốn xin "đề cương ôn tập phần ma trận" và nhận định nghĩa, tính chất, ví dụ giải mẫu, để ôn trước kỳ thi.
2. Là người học, tôi muốn xin "tóm tắt công thức cần nhớ" và nhận bảng công thức đúng ký hiệu của sách, kèm khi nào dùng.
3. Là người học, tôi muốn xin "bảng so sánh các học thuyết" và nhận một bảng Markdown rõ ràng.
4. Là người học, tôi muốn xin "hướng dẫn từng bước có ví dụ số" và nhận các bước có số cụ thể, ưu tiên ví dụ của sách.
5. Là người học, tôi muốn tài liệu bao quát mọi khái niệm của các module tôi chọn, không chỉ vài đoạn tìm được.
6. Là người học, tôi muốn công thức hiện đúng như sách (LaTeX), kể cả khi PDF làm mất công thức khi trích chữ.
7. Là người học, tôi muốn thấy chữ hiện dần ngay, không chờ cả tài liệu.
8. Là người học, tôi muốn biết từng ý lấy ở trang nào (nhãn `[Sx]` và khối "Trong sách").
9. Là người học, tôi muốn tài liệu không bao giờ rỗng khi mô hình đã viết.
10. Là người học, khi tài liệu không tạo được, tôi muốn biết lý do và có nút thử lại.
11. Là người học, khi chọn quá 5 module, tôi muốn được bảo thu hẹp phạm vi, thay vì chờ một tài liệu hỏng.
12. Là người học, tôi muốn tải tài liệu về dạng Markdown có chú thích trang.
13. Là người học nhờ trợ lý, tôi muốn trợ lý tạo tài liệu và báo lại tiêu đề.
14. Là admin, tôi muốn log nhãn dùng, nhãn lạ, câu không nhãn, công thức còn sót, ảnh đã gửi, để theo dõi chất lượng mà không chặn người học.
15. Là chủ dự án, tôi muốn mỗi tài liệu tốn vài phần nghìn USD và tính vào trần chi người học.

## Quyết định cài đặt

### 1. Use case

- Thay ruột `DocumentUseCase.create` bằng luồng `document-3`. Giữ:
  - chữ ký;
  - các kiểm tra đầu vào (`owner`, `doc_id`, `origin`);
  - `home_scope`, `session_id`;
  - phạm vi tối đa `document_max_modules`: vượt thì `failed`, `scope_too_large`, 0 USD;
  - lưu bản ghi `documents`.
- Bỏ khỏi đường `document-3`: `DOCUMENT_SCHEMA`, `call_json`, trích nguyên văn, `outside_document_blocks`, `check_text`, `_cap_context`.
  `postcheck.py` không sửa: trợ lý và bài giảng đã thôi dùng nó; dọn mã chết là vé sau.

### 2. Gom tư liệu (`document-context-3`)

1. Với từng khái niệm của phạm vi, theo thứ tự module rồi thứ tự trong module: lấy các đoạn theo luật gom của bài giảng (`gather_chunks`), với trần riêng
   `document_per_concept_chars` (1.600).
2. Tìm kiếm theo câu yêu cầu, `k` = 6, như tìm kiếm của trợ lý.
3. Chọn theo ưu tiên, tới `document_context_chars` (20.000) ký tự, không trùng:
   - đoạn đầu của mỗi khái niệm;
   - các đoạn tìm được;
   - các đoạn còn lại của từng khái niệm.
4. Xếp theo thứ tự đọc, đánh nhãn `S1…Sn`.
5. Mỗi `[formula]` thay bằng `[formula: <raw_text>]`, dùng hàm chung của bài giảng bản 2 (SA-70).
6. Ảnh trang: các trang có `[formula]` trong tư liệu đã chọn, tối đa `document_max_page_images` (8), theo thứ tự đọc. Đọc qua cổng `PageImages`.

Tin nhắn người dùng, khuôn của bản thử:
- `Yêu cầu của sinh viên: …`;
- `Phạm vi đã chọn: module n: <tên>; …`, theo số module của ứng dụng;
- `Các khái niệm trong phạm vi:`, mỗi dòng `- <tên> (module n)`;
- `Tư liệu từ sách:`, mỗi đoạn mở đầu bằng `[Sk] (trang p, mục …)`.

Yêu cầu rỗng thì dùng câu "Tóm tắt các ý chính của phạm vi này để ôn tập, có ví dụ."

### 3. Lời nhắc (`document-prompt-3`)

Nguyên văn. Đây là bản thử ngày 2026-10-24, cộng hai chỗ sửa sau 12 lần lặp. `{formula_rule}` theo luật 1 hay luật 2 của spec bài giảng mục 4.

```text
Bạn là một giảng viên đại học giỏi và tận tâm. Bạn soạn tài liệu học tập bằng tiếng Việt cho sinh viên đang tự học từ một cuốn sách, theo đúng yêu cầu của sinh viên.

Cách viết:
- Làm đúng thứ sinh viên yêu cầu: đề cương ôn tập, tóm tắt công thức, bảng so sánh, hướng dẫn từng bước, tổng quan… Chọn hình thức hợp nhất với yêu cầu: văn xuôi, danh sách, bảng Markdown, hay kết hợp.
- Bao quát các khái niệm trong phạm vi đã chọn, dành nhiều chỗ hơn cho những gì yêu cầu nhắc tới. Sắp theo trình tự dễ học, thường theo thứ tự module.
- Giải thích đủ để hiểu, không chỉ chép định nghĩa. Có ví dụ khi giúp hiểu: ưu tiên ví dụ trong sách; ví dụ tự nghĩ phải đúng: ví dụ số thì chọn số đơn giản, dễ tính, và soát lại từng phép tính, từng bước suy luận trước khi viết.
- Dòng đầu là một tiêu đề "# …" ngắn, nói rõ tài liệu này là gì.

Trung thực với sách:
- Sách là chuẩn. Không viết điều mâu thuẫn với sách. Dùng đúng ký hiệu và thuật ngữ của sách.
- Giữ đúng chiều và phạm vi của phát biểu trong sách: sách nói "nếu A thì B" thì đừng viết thành "nếu B thì A"; điều sách gán cho đối tượng hay vai trò nào thì giữ đúng đối tượng, vai trò đó. Khi tóm tắt thành gạch đầu dòng hay bảng cũng vậy: giữ đúng điều kiện và chiều của phát biểu.
- Viết công thức bằng LaTeX trong $...$ hoặc $$...$$.
- {formula_rule}
- Đoạn nào dựa vào sách thì gắn nhãn nguồn như [S2] ở cuối đoạn hay cuối dòng bảng. Phần giải thích hay ví dụ tự nghĩ thì không cần nhãn.
- Nếu sách nói ít về điều được hỏi, vẫn viết đầy đủ bằng hiểu biết chung, nhưng không mâu thuẫn với sách.

Định dạng: Markdown. Độ dài tuỳ yêu cầu và phạm vi, thường 600–1.500 từ. Không chào hỏi, không nói về bản thân, không nhắc tới "tư liệu" hay "đoạn trích".
```

### 4. Gọi mô hình

- `gemini-3.1-flash-lite`, nhiệt độ `document_temperature` 1,0, `document_max_output_tokens` 8.192, đầu ra chữ, stream, không bật suy nghĩ.
- Ước tính chi trước lời gọi: chữ chia 3, cộng 1.300 token mỗi ảnh, cộng trần đầu ra. Quá `document_max_usd` (0,03) thì `failed`,
  `estimated_cost_over_limit`, 0 USD, như cũ.
- Trần chi người học như cũ (`purpose = document`). Hết trần thì `failed`, `daily_limit`.
- Đầu ra rỗng thì sinh lại đúng một lần. Lỗi mạng, hết giờ: thử lại tầng mạng như bài giảng. Lỗi giữa chừng sau khi đã có chữ thì giữ chữ, `ready`,
  cảnh báo `cat_ngan`.

### 5. Hợp đồng `document-3`

```json
{"contract_version": "document-3", "document_id": "…", "owner": "…", "doc_id": "…", "graph_version": 29, "request": "…",
 "scope": {"node_ids": [], "module_ids": []}, "title": "…", "markdown": "# … Markdown, LaTeX, nhãn [S1] …",
 "sources": [{"label": "S1", "chunk_id": "…", "page": 15, "section_path": ["…"]}],
 "status": "ready | failed", "failure": null, "warnings": [], "usage": {},
 "home_scope": {}, "session_id": null, "origin": "button | assistant", "node_ids": [], "created_at": "…"}
```

- `title` là dòng `# …` đầu tiên, không có thì "Tài liệu học tập". `markdown` là đúng chữ mô hình viết, giữ dòng tiêu đề.
- `failure` theo ADR 0024: `reason_code`, `message`, `retryable`. Lý do: `scope_too_large` (`retryable = false`), `daily_limit`, `estimated_cost_over_limit`,
  `loi_mang`, `het_thoi_gian`, `khong_dung_duoc`.
- Không có `validation`, `citations`, `outside_document_blocks`, `postcheck`.
- **Stream:** `skeleton {document_id, title: null}`, các `delta {text}`, rồi `final {document}` hoặc `failure`. Công cụ `make_document` của trợ lý gọi không
  stream và trả `{artifact, title, status}` như hiện nay.
- **Xuất Markdown:** nhãn `[Sx]` thành chú thích `[^Sx]: tr. p, <mục> (đoạn <chunk_id>)` từ `sources`.

### 6. Log cho admin (`validation`, không gửi người học)

Ghi vào bản ghi riêng `document_validation` và dòng usage, theo mẫu `answer-3`:
- nhãn dùng, nhãn lạ;
- số câu không nhãn;
- số từ;
- `formula_left`: còn `[formula` trong chữ;
- `pages_with_formula` đếm trước khi cắt, số ảnh đã gửi, `thieu_anh_trang`;
- `finish_reason`; giây tới chữ đầu, giây tới xong; chi.

### 7. `BSettings`

| khoá | mặc định |
|---|---|
| `document_contract_version` | `document-3` |
| `document_prompt_version` | `document-prompt-3` |
| `document_context_version` | `document-context-3` |
| `document_context_chars` | 20.000 |
| `document_per_concept_chars` | 1.600 |
| `document_max_page_images` | 8 |
| `document_max_output_tokens` | 8.192 (từ 3.000) |
| `document_max_usd` | 0,03 (từ 0,01) |

`document_context_tokens` thôi dùng; giữ khoá để không đổi cấu hình cũ.

## Quyết định kiểm thử

- **Đường nối chính** ở mức use case: mô hình giả stream theo kịch bản, tìm kiếm giả, cổng ảnh giả, kho trong bộ nhớ. Không gọi mạng.
- **Mẫu test:** `tests/unit/application/test_phase_b_sa30_documents.py`, `test_phase_b_lectures_documents.py`; test bài giảng 3 cho stream và ảnh.
- **Bất biến phải có test,** mỗi cái thấy đỏ trước:
  1. Phạm vi 3 module: tin nhắn gửi mô hình có đoạn định nghĩa của **mọi** khái niệm trong phạm vi, khi tổng còn dưới trần; có đoạn tìm được theo yêu cầu;
     theo thứ tự đọc; không vượt 20.000 ký tự.
  2. `[formula]` thay bằng chữ thô đúng thứ tự; ảnh của đúng các trang có công thức, tối đa 8; không có công thức thì không gửi ảnh.
  3. Lời nhắc đúng nguyên văn mục 3.
  4. `markdown` đúng từng chữ của mô hình, kể cả câu không nhãn, công thức, nhãn lạ; những điều này chỉ có trong `validation`.
  5. Mẩu chữ đầu đến người gọi trước khi mô hình viết xong.
  6. Đầu ra rỗng thì sinh lại đúng một lần, rồi `failed` với `khong_dung_duoc`, `retryable = true`. Lỗi giữa chừng thì `ready`, `cat_ngan`, giữ chữ.
  7. Quá 5 module thì `scope_too_large`, 0 lời gọi, 0 USD. Hết trần người học thì `daily_limit`.
  8. `validation` không có trong kết quả, sự kiện `final`, hay kết quả công cụ `make_document`.
  9. `title` lấy từ dòng `# …` đầu; không có thì "Tài liệu học tập".
  10. Xuất Markdown có chú thích trang theo `sources`.
- **Graph thật, chỉ đọc:** yêu cầu "Tóm tắt các công thức cần nhớ về tương quan và hồi quy mẫu" trên xstk v68, module thứ 4–6. Tư liệu phải có đoạn định
  nghĩa hệ số tương quan mẫu và đường hồi quy, và chữ thô `0,8165`.

## Ngoài phạm vi

- Web (người điều phối): nút "Tạo tài liệu", thư viện, hiện stream.
- Dọn `postcheck.py` và mã `document-2`.
- Bật suy nghĩ, lời gọi kiểm lại, mô hình mạnh hơn: chờ đợt đánh giá tổng.
- Quiz (vé 68).
