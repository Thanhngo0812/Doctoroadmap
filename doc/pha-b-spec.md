# Spec Pha B — tên và mô tả module, bài giảng, quiz, trợ lý agent

**Ngày:** 2026-10-15. **Nhãn:** `ready-for-agent`. **Trạng thái:** chờ chia vé (skill `ticket`); vé sẽ ở `task/sau-a10/`.

**Căn cứ:** bốn báo cáo nghiên cứu ngày 2026-10-11 (commit `536f366`, sửa tên module ở commit kế tiếp). Mỗi báo cáo có văn liệu, số đo và
giao thức chi tiết; spec này thắng khi hai bên lệch nhau.
- [Tên và mô tả module](../report/nghien-cuu-ten-va-mo-ta-module-2026-10-11.md)
- [Bài giảng theo khái niệm](../report/nghien-cuu-bai-giang-theo-khai-niem-2026-10-11.md)
- [Quiz tự kiểm tra](../report/nghien-cuu-quiz-tu-kiem-tra-2026-10-11.md)
- [Trợ lý hỏi đáp dùng đồ thị](../report/nghien-cuu-tro-ly-hoi-dap-do-thi-2026-10-11.md)

**Quyết định kiến trúc đi kèm:**
- [ADR 0011](adr/0011-noi-dung-hoc-sinh-khi-can-cache-theo-ngu-canh.md): nội dung học sinh khi cần, cache theo băm ngữ cảnh.
- [ADR 0012](adr/0012-tro-ly-la-agent-goi-cong-cu.md): trợ lý là agent gọi công cụ.
- [ADR 0013](adr/0013-lop-gan-module-va-media-da-xac-nhan.md): lớp gán module cho chỉ mục, và media đã xác nhận.
- [ADR 0014](adr/0014-ten-module-do-llm-dat.md): tên module do LLM đặt, cho cả hai môn.

**Quyết định của chủ dự án:** đợt tra hỏi ngày 2026-10-15 (Q1–Q29) cộng các câu trả lời ngày 2026-10-11. Nguyên tắc chủ dự án đặt: "sau A10
cứ LLM thoải mái".

**Quy trình:** tôi viết spec và vé, chủ dự án giao nhân viên cài, tôi kiểm theo vé. Mã lõi nằm trong `src` dưới dạng use case kèm lệnh CLI;
nhóm web chỉ bọc các use case này bằng FastAPI, theo hợp đồng dữ liệu ở mục 13.

---

## Vấn đề

Pha A đã biến một giáo trình thành lộ trình gồm các module có thứ tự. Người học mở lộ trình thì gặp năm vấn đề:
- **Tên module chưa nói đúng nội dung.**
  - Có tên nhảy lên cấp chương hay phần: 23/87 tên của doc-4, như "Phần II — …", "Chương XI".
  - Có tên sai mục vì cây mục hỏng: 8/9 module xstk mang tên "THỐNG KÊ TOÁN §1. LÝ THUYẾT MẪU — …".
  - Có tên chung ("2.2.2 Tính chất"), mẩu tên ghép ("Tích hợp · Giảm"), và nhãn đánh số ("Tính chất 3").
  - Module chưa có mô tả "học gì, cần gì trước".
- **Bấm vào một khái niệm thì chưa có gì để học:** không có bài giảng, không có giải thích hay ví dụ, không có câu tự kiểm tra.
- **Không tự kiểm tra được** sau khi học một module.
- **Không có ai để hỏi.** Người học không hỏi được "vì sao phải học A trước B", "cho tôi ví dụ", "tóm tắt chương này cho tôi", và không nhận
  được nhắc nhở về khái niệm nền mình đang thiếu.
- **Đề cương đồ án chưa được đáp ứng.** Đề cương hứa trợ lý hỏi đáp và tạo bài giảng có trích dẫn, chủ động nhắc khái niệm nền, đánh giá
  bằng RAGAS so với mốc và có ablation. Lịch đặt trợ lý ở tuần 7 (19–25/10) và bài giảng ở tuần 8.

Có ba ràng buộc nền:
- **Đồ thị có cạnh sai.** Độ chính xác cạnh bao đóng chỉ 0,58–0,64 trên tập giữ lại v3, nên mọi nội dung phải hiện bằng chứng và không khẳng
  định quá mức.
- **Sách toán mất công thức.** Công thức đứng riêng bị thay bằng `[formula]`: doc-1 có 81% khái niệm bị ảnh hưởng.
- **Tiền và giây chờ là ưu tiên số một.**

## Giải pháp

Người học thấy sáu thay đổi:
1. **Tên và mô tả module.** Mỗi module có tên ngắn, đúng nội dung, không trùng với module kề, và một mô tả 1–2 câu "học gì, cần gì trước".
   Số mục sách ("2.1.3") hiện riêng nếu web muốn. LLM đặt tên mọi module. Nếu module trùng đúng một mục sách, LLM giữ tiêu đề của tác giả trừ
   khi đó là nhãn chung hay trùng với module kề.
2. **Bài giảng khi bấm vào khái niệm.**
   - Phần do mã dựng hiện ngay, không chờ: vị trí trong module, định nghĩa nguyên văn kèm trang, các khái niệm nền kèm câu trích "vì sao",
     hình đã xác nhận, ảnh công thức gốc.
   - Phần do LLM viết hiện dần theo từng ý đã kiểm trích dẫn: nhắc nền, giải thích, ví dụ, phân biệt, một câu tự kiểm tra.
   - Bài sinh ở lần bấm đầu và dùng chung cho mọi người học. Ví dụ ngoài sách được phép nếu có nhãn rõ.
3. **Quiz tự kiểm tra cho module.**
   - Bấm "làm quiz" thì câu hỏi hiện dần, câu nào sẵn sàng trước hiện trước.
   - Mỗi khái niệm một câu trắc nghiệm 3 phương án.
   - Nộp xong có phản hồi: đáp án đúng, câu trích làm nguồn, vì sao phương án đã chọn sai, link bài giảng của khái niệm làm sai.
   - Không khoá module, không chấm "trình độ".
4. **Trợ lý agent trong khung chat.**
   - Hỏi bất cứ điều gì về tài liệu đang học. Module đang mở là ngữ cảnh ưu tiên, nhưng trợ lý tìm cả tài liệu và không chặn theo tiến độ.
   - Câu trả lời có trích dẫn tới đoạn và trang, ghi chú "học kỹ ở module N" khi cần, và một dòng nhắc khái niệm nền.
   - Trợ lý có thể mở bài giảng, tạo quiz theo yêu cầu, và tạo tài liệu theo yêu cầu (ví dụ "một bản chi tiết về khái niệm X"), tải về được.
   - Câu hỏi ngoài tài liệu thì trợ lý nói tài liệu không có.
5. **Công thức ở sách toán** hiện bằng ảnh cắt từ chính trang sách. LLM không tự viết công thức.
6. **Nhóm web nhận hợp đồng JSON ổn định.** Nhóm làm giao diện mà không phải đọc `graph.json`.

---

## User story

**Người học, tên và mô tả module:**
1. Là người học, tôi muốn mỗi module có một tên ngắn nói đúng nội dung, để biết buổi học này về gì.
2. Là người học, tôi muốn hai module liền nhau không mang tên giống hay gần giống nhau, để phân biệt được chúng.
3. Là người học, tôi muốn tên module không phải nhãn chung ("Tính chất", "Các khái niệm cơ bản") hay nhãn đánh số ("Chương XI", "Tính chất 3"),
   để tên tự nó có nghĩa.
4. Là người học, tôi muốn thấy tiêu đề của tác giả khi module trùng đúng một mục sách, để đối chiếu được với giáo trình.
5. Là người học, tôi muốn mỗi module có mô tả 1–2 câu "học gì, cần gì trước", để quyết định học tiếp hay ôn lại.
6. Là người học, tôi muốn số mục sách ("2.1.3") hiện riêng chứ không nằm trong tên, để tên gọn mà vẫn tìm được trong sách.

**Người học, bài giảng:**
7. Là người học, tôi muốn bấm vào một khái niệm là thấy ngay vị trí của nó trong module, khái niệm trước và khái niệm sau, để định hướng.
8. Là người học, tôi muốn thấy ngay câu định nghĩa nguyên văn kèm số trang, để tin đó là lời của sách.
9. Là người học, tôi muốn thấy các khái niệm nền của khái niệm này, mỗi cái kèm câu trích giải thích vì sao cần, để biết nên ôn gì trước.
10. Là người học, tôi muốn khái niệm nền mà sách trình bày ở phần sau được ghi là "sách trình bày ở phần sau", không ghi là "đã học", để không
    bị hiểu sai.
11. Là người học, tôi muốn phần giải thích chia thành từng ý ngắn, mỗi ý có trích dẫn tới đoạn nguồn, để kiểm tra được.
12. Là người học, tôi muốn có một ví dụ, ưu tiên ví dụ có lời giải trong sách, để thấy khái niệm được dùng ra sao.
13. Là người học, tôi muốn ví dụ ngoài sách, nếu có, được đánh dấu rõ là "ví dụ minh hoạ, không có trong tài liệu", để không nhầm với nội dung
    sách.
14. Là người học, tôi muốn thấy khái niệm này khác gì khái niệm gần nó, để khỏi nhầm.
15. Là người học, tôi muốn biết khái niệm này được dùng ở những khái niệm nào về sau, để hiểu học nó để làm gì.
16. Là người học, tôi muốn một câu tự kiểm tra có đáp án ẩn, để tự kiểm tra trước khi đi tiếp.
17. Là người học, tôi muốn công thức hiện đúng như trong sách, bằng ảnh cắt từ trang sách, để không đọc phải công thức máy tự viết sai.
18. Là người học, tôi muốn thấy hình hay bảng đã được xác nhận là minh hoạ khái niệm, kèm ghi chú "mô tả do máy sinh" khi cần.
19. Là người học, tôi muốn bài giảng bắt đầu hiện trong vài giây, và hiện ngay nếu đã có người mở trước, để không phải chờ lâu.
20. Là người học, tôi muốn bài giảng không bao giờ hiện một ý rồi xoá ý đó đi, để không bị rối.
21. Là người học, tôi muốn được báo khi tài liệu không có đoạn giảng khái niệm này, kèm các đoạn có nhắc tới nó, thay vì nhận một bài bịa.
22. Là người học, tôi muốn báo được "quan hệ này sai", để nhóm sửa đồ thị.

**Người học, quiz:**
23. Là người học, tôi muốn bấm "làm quiz" của một module và thấy câu đầu tiên trong vài giây, các câu sau hiện dần.
24. Là người học, tôi muốn mỗi khái niệm của module có một câu hỏi, để quiz phủ hết buổi học.
25. Là người học, tôi muốn câu hỏi có 3 phương án và đúng một đáp án đúng, để không bị đánh đố.
26. Là người học, tôi muốn câu hỏi không đoán được qua độ dài hay cách viết phương án, để quiz thật sự kiểm tra hiểu biết.
27. Là người học, tôi muốn câu hỏi không bắt tôi đọc một hình hay công thức không hiển thị được.
28. Là người học, tôi muốn sau khi nộp thấy đáp án đúng, câu trích làm nguồn, và vì sao phương án tôi chọn sai, để học từ lỗi.
29. Là người học, tôi muốn có link bài giảng của từng khái niệm tôi làm sai, để ôn đúng chỗ.
30. Là người học, tôi muốn làm lại quiz và gặp biến thể khác của câu hỏi, để không chỉ nhớ đáp án.
31. Là người học, tôi muốn xem lại lịch sử các lần làm quiz của mình, để thấy mình tiến bộ.
32. Là người học, tôi muốn quiz không khoá module nào và không gắn nhãn trình độ cho tôi.
33. Là người học, tôi muốn báo được câu hỏi lỗi, để câu bị báo nhiều lần được ẩn đi chờ soát.

**Người học, trợ lý:**
34. Là người học, tôi muốn hỏi bằng tiếng Việt tự nhiên về bất cứ điều gì trong tài liệu, để được giải đáp ngay khi học.
35. Là người học, tôi muốn trợ lý ưu tiên nội dung của module tôi đang mở, để câu trả lời sát bài đang học.
36. Là người học, tôi muốn hỏi được cả về phần sau, nhận câu trả lời kèm ghi chú "học kỹ ở module N".
37. Là người học, tôi muốn mỗi câu có nội dung trong câu trả lời đều có trích dẫn tới đoạn và trang, để tự kiểm tra lại.
38. Là người học, tôi muốn trợ lý nói thẳng là tài liệu không có khi câu hỏi nằm ngoài tài liệu, thay vì bịa.
39. Là người học, tôi muốn hỏi "vì sao phải học A trước B" và nhận câu trích bằng chứng, kèm lưu ý rằng quan hệ do hệ thống suy ra.
40. Là người học, tôi muốn hỏi "muốn hiểu X thì cần học gì", và nhận danh sách module cần học đã được rút gọn.
41. Là người học, tôi muốn trợ lý chủ động nhắc tối đa vài khái niệm nền liên quan ở cuối câu trả lời, nhưng không nhắc lại cùng khái niệm trong
    một phiên, và tôi tắt được tính năng này.
42. Là người học, tôi muốn hỏi tiếp kiểu "còn cái kia thì sao?" mà trợ lý vẫn hiểu đang nói về khái niệm nào.
43. Là người học, tôi muốn thấy trợ lý đang làm gì ("đang tra đồ thị…", "đang tạo quiz…"), để biết nó chưa treo.
44. Là người học, tôi muốn nhờ trợ lý mở bài giảng của một khái niệm, và nhận đúng bài mà nút bấm hiện, không phải một bản khác.
45. Là người học, tôi muốn nhờ trợ lý tạo một quiz theo yêu cầu (vài khái niệm, một module, mức khó), và lần làm đó được ghi vào lịch sử của tôi.
46. Là người học, tôi muốn nhờ trợ lý tạo một tài liệu theo đúng yêu cầu của mình (ví dụ "bản chi tiết về khái niệm X", "đề cương ôn chương 2"),
    có trích dẫn và tải về được dạng Markdown.
47. Là người học, tôi muốn ví dụ hay giải thích ngoài sách trong câu trả lời có nhãn rõ, còn định nghĩa, công thức và khẳng định về sách luôn
    có trích dẫn.
48. Là người học, tôi muốn thấy hình đã xác nhận khi hỏi về một khái niệm có hình minh hoạ.

**Nhóm web:**
49. Là thành viên nhóm web, tôi muốn hợp đồng JSON có phiên bản cho tên module, bài giảng, quiz, câu trả lời, tài liệu và sự kiện stream, để
    làm giao diện song song với lõi.
50. Là thành viên nhóm web, tôi muốn gọi lõi qua các use case Python có sẵn, để chỉ phải viết lớp FastAPI mỏng.
51. Là thành viên nhóm web, tôi muốn đề quiz gửi xuống trình duyệt không chứa đáp án, để người học không đọc được đáp án trong mã trang.
52. Là thành viên nhóm web, tôi muốn trích dẫn có `chunk_id`, trang, đường mục và vị trí tô sáng, để làm một thành phần hiện nguồn dùng chung.
53. Là thành viên nhóm web, tôi muốn ảnh công thức và ảnh hình có tham chiếu ổn định, để thay nhãn `[CTk]` bằng ảnh.
54. Là thành viên nhóm web, tôi muốn kho lưu trữ là một port có hợp đồng rõ, để thay bản JSON tệp bằng Postgres mà không sửa lõi.

**Chủ dự án và nhóm nghiên cứu:**
55. Là chủ dự án, tôi muốn mọi lời gọi mô hình ở Pha B ghi vào sổ chi (mô hình, token, USD, giây chờ, mục đích), để báo cáo USD và giây chờ.
56. Là chủ dự án, tôi muốn mỗi tin nhắn của trợ lý có trần vòng công cụ và trần USD, để không có tin nhắn đắt bất thường.
57. Là chủ dự án, tôi muốn lệnh CLI cho từng chức năng, có `--dry-run` dự toán và `--allow-spend` mới gọi mô hình, để thử và đo trước khi có web.
58. Là chủ dự án, tôi muốn tỉ lệ gọi công cụ sai của flash-lite được đo, để quyết có cần mô hình mạnh hơn không.
59. Là người nghiên cứu, tôi muốn chạy bốn cấu hình trợ lý trên cùng bộ câu hỏi thử (LLM không bằng chứng, RAG thuần, agent không công cụ đồ
    thị, agent đầy đủ), để đo đóng góp của đồ thị cho báo cáo đồ án.
60. Là người nghiên cứu, tôi muốn RAGAS chạy bằng Gemini, không gửi nội dung giáo trình sang OpenAI.
61. Là người nghiên cứu, tôi muốn bảng chấm mù cho tên module, bài giảng, quiz và câu trả lời, để hai người chấm độc lập và đo độ đồng thuận.
62. Là người nghiên cứu, tôi muốn đo riêng tỉ lệ nội dung ngoài sách và tỉ lệ ý bị gắn cờ "cần soát", để báo cáo trung thực.
63. Là người nghiên cứu, tôi muốn các lượt chạy có tiền được ghi lại và phát lại được, để biến chúng thành bộ kiểm thử hồi quy 0 USD.
64. Là người chấm, tôi muốn bảng chấm không lộ cấu hình nào sinh ra mục đang chấm.

**Nhân viên cài đặt:**
65. Là nhân viên, tôi muốn mỗi use case có một đường kiểm thử ở mức use case với mô hình giả theo kịch bản, để kiểm hành vi mà không tốn tiền.
66. Là nhân viên, tôi muốn mọi giới hạn mà mã kiểm cũng được nêu trong prompt. Bài học xstk: mô hình hỏng 8/8 vì luật độ dài không có trong
    prompt.

---

## Quyết định triển khai

### 1. Nguyên tắc chung

Sáu nguyên tắc áp cho mọi phần của spec:
- **Mã làm những gì mã làm được; LLM chỉ viết phần diễn giải.**
  - Mã dựng sẵn: vị trí, định nghĩa nguyên văn, danh sách tiên quyết và câu trích, khối nhắc khái niệm nền, ghi chú module, câu từ chối ngoài
    tài liệu.
  - Mã quyết định: danh sách tiên quyết (sơ đồ Hasse), cạnh nào được hiện.
- **Mọi ý LLM viết về sách phải trỏ về nguồn đã nạp**, bằng nhãn ngắn. Mã kiểm nhãn có thật và câu trích nguyên văn trước khi ý tới người học.
  Ý hỏng không bao giờ tới người học.
- **Nội dung ngoài sách được phép, nhưng phải tách bạch.**
  - Phải gắn nhãn `outside_document` và hiện trong khung riêng, không gắn trích dẫn.
  - Định nghĩa, công thức và khẳng định về nội dung sách không bao giờ được là nội dung ngoài sách.
- **Đồ thị có thể sai, nên lời lẽ phải mềm.** Câu dẫn mặc định là "định nghĩa này dùng tới…", không phải "bạn phải học trước". Luôn kèm câu trích
  và lưu ý "quan hệ do hệ thống suy ra, có thể sai".
- **Mô hình** là `gemini-3.1-flash-lite` cho mọi lời gọi.
  - Nhiệt độ 0 cho tên module, bài giảng và quiz, vì các phần này đã có cache.
  - Nhiệt độ mặc định cho trợ lý và tài liệu theo yêu cầu.
  - Mọi giá trị cấu hình sinh nằm trong khoá cache.
- **Mỗi lời gọi ghi sổ chi; mỗi chức năng có trần.** Lệnh CLI tốn tiền theo kỷ luật của Pha A: `--dry-run` dự toán, `--allow-spend` mới gọi.

### 2. Tên và mô tả module (khâu tên ở cuối A10)

Thay luật R7 hiện hành. Đặt tên coi là việc sau A10, dùng cho cả đồ án lẫn seminar (ADR 0014). Khâu này vẫn chạy cuối chuỗi `roadmap`, qua chốt
chi và `--dry-run` như hiện nay.

**Đầu vào mỗi lời gọi.** Mỗi module một lời gọi, gồm năm nhóm:
- **Module đích:**
  - danh sách khái niệm theo thứ tự dãy học: `node_id`, `display_name` (không dùng `name`), mô tả A5 cắt ≤ 200 ký tự;
  - đường mục tác giả đã làm sạch của mục đa số và của tổ tiên chung;
  - cờ "module trùng đúng một mục sách".
- **Ứng viên:** 3–5 tiêu đề hoặc cụm do mã xếp hạng, kèm điểm (xem báo cáo, mục 6.3), làm gợi ý.
- **Đối chứng:** tên và danh sách khái niệm của module ngay trước và ngay sau (±1), ghi rõ "không thuộc module này". Không gửi mô tả module kề.
- **Ràng buộc**, viết trong prompt và đúng bằng giá trị mã kiểm:
  - tên ≤ 60 ký tự;
  - không số đánh mục;
  - không lặp tên ±2;
  - chỉ dùng từ vựng của module đích;
  - tiếng Việt.
- **Mặc định giữ tiêu đề tác giả:** nếu module trùng đúng một mục sách và tiêu đề không phải nhãn chung, không trùng module kề, không là nhãn
  đầu đoạn hay chỉ có mã, thì giữ tiêu đề đó. Nhãn chung nhận bằng bằng chứng trong tài liệu: cùng chuỗi tiêu đề (bỏ số) xuất hiện ở ≥ 2 mục
  cha khác nhau.

**Đầu ra** theo lược đồ JSON sau (lấy từ báo cáo):

```json
{"title": "Phép toán trên ma trận",
 "description": [{"text": "…", "node_ids": ["…"]},
                 {"text": "…", "node_ids": ["…"], "module_ids": ["…"]}]}
```

**Năm luật kiểm bằng mã.** Hỏng luật nào cũng đi đường lùi, không hỏi lại.

**Sửa 2026-10-18, sau soát SA-28:**
- Tên và mô tả được kiểm và rơi đường lùi **riêng nhau**. Tên đạt luật tên thì giữ dù mô tả hỏng.
- Từ vựng của mô tả rộng hơn từ vựng của tên. Lý do: khi mô tả viết thành câu, 122/160 module rơi đường lùi vì luật 1, dù câu có nghĩa
  ([soát](../report/kiem-thu-pha-b-sa25-28-2026-10-18.md), mục 4).

Năm luật:
1. **Từ vựng có căn cứ.**
   - **Tên:** mọi âm tiết nội dung phải có trong từ vựng module đích. Từ vựng gồm tên, alias, `display_name`, mô tả A5 của khái niệm, và tiêu đề các mục
     chứa chúng.
   - **Mô tả:** từ vựng của tên, cộng âm tiết của các đoạn dạy khái niệm trong module, cộng âm tiết có ở ít nhất max(3, 2% số đoạn) của chính cuốn sách.
     Tỉ lệ 2% là `naming_common_chunk_ratio` trong `BSettings`.
   - Âm tiết chức năng nhận bằng tần suất trong chính cuốn sách, không bằng danh sách từ viết tay.
2. **Không mượn từ module kề, kiểm bằng mã.**
   - Âm tiết bị coi là "mượn" khi có trong tên hay alias khái niệm của module ±1, mà không có trong tên, alias, mô tả A5 hay đoạn dạy của module đích.
   - Câu chứa âm tiết mượn bị loại.
3. **Trích khái niệm hợp lệ.** `node_ids` của mỗi câu mô tả thuộc module đích, mỗi câu có ít nhất một. `module_ids` chỉ được là phụ thuộc
   module.
4. **Hình thức tên.** Tên ≤ 60 ký tự. Tên không trùng tên module ±2 sau chuẩn hoá. Tên không là nhãn đánh số theo luật họ nhãn R9.
5. **Mảnh tên nguyên vẹn.** Tên có ghép " · " thì mỗi mảnh phải là một tên khái niệm hay một tiêu đề mục nguyên vẹn.

**Đường lùi tối giản**, cờ `title_source = fallback`:
- tên: tiêu đề tác giả nếu module trùng một mục; nếu không, 2–3 `display_name` (khái niệm đầu và khái niệm có nhiều cạnh cứng ra nhất);
- mô tả: theo khuôn "Học: A, B, C. Cần trước: X (module n)", dựng từ đồ thị.

**Ba sửa lỗi bắt buộc**, theo báo cáo mục 6.5:
- trần 12 token của tiêu đề đổi sang trần ký tự;
- kiểm từng mảnh tên thay cho kiểm cả chuỗi;
- dùng `display_name`.

Cộng thêm hai luật mới:
- Khâu tên **bỏ qua vai trò `de_cuong` khi mục chứa khái niệm được dạy**. Đây là luật tạm, chờ A2 sửa gốc.
- Bỏ nhánh dùng lại tên từ artifact cũ khi băm prompt khác, vì nhánh này đang giữ lại các tên mẩu cũ.

**Trường mới trên mỗi module của artifact graph:**
- `title`: không có số đánh mục; dấu đánh số cục bộ như "a)", "I-" cũng bị bỏ;
- `section_code`: số đường dẫn mục, ví dụ "2.1.3", hoặc rỗng;
- `title_source` ∈ {`llm`, `author_section`, `fallback`};
- `description`: các câu, mỗi câu kèm `node_ids`;
- `description_source` ∈ {`llm`, `template`};
- `naming_flags`.

**Cache và nhiệt độ:**
- Khoá là băm của mô hình, prompt, lược đồ, cấu hình sinh và JSON chuẩn hoá của đầu vào, gồm cả tên module kề. Đổi tên một module làm mất cache
  của hai module kề, và như vậy là đúng.
- Nhiệt độ 0.

**Chi phí ước:** doc-4 tốn khoảng 0,035–0,059 USD (87 lời gọi), doc-1 khoảng 0,013–0,022 USD. Thời gian dưới 1 phút ở song song 16 (ước,
phải đo).

### 3. Lớp gán module cho chỉ mục (A12)

Theo ADR 0013 và ADR 0002, A12 ghi module vào chỉ mục mà không phải embed lại:
- **Đầu ra** là một lớp gán riêng cho mỗi cặp (phiên bản đồ thị, phiên bản chỉ mục). Không ghi lại tệp vector.
- **Mỗi chunk** có `module_id`, `all_module_ids`, `module_source`:
  - `chunk_module_map` nếu chunk có trong bản đồ của A10;
  - `hint` nếu chunk không dạy khái niệm nào: lấy module của chunk dạy gần nhất đứng trước. Cách này đưa độ phủ từ 28–63% lên 74–99%;
  - `none` nếu không có chunk dạy nào đứng trước.
- **Trường `stage_id`** của chỉ mục đổi tên thành `module_id`, theo ADR 0010.
- **Truy hồi không lọc theo module**, chỉ xếp hạng ưu tiên (mục 10). Chunk không có module vẫn được truy hồi; chunk bài tập là nguồn tốt cho câu
  hỏi "ví dụ".
- **Media có cạnh `illustrates`/`tabulates` với `confirmed = true`** được hiện dù chưa gắn module. Điều chặn cũ của A12 bị bỏ. Media chưa xác
  nhận thì không bao giờ hiện cho người học.

### 4. Chỉ mục khái niệm

Mỗi tài liệu có một chỉ mục vector cho khái niệm, để trợ lý liên kết được câu hỏi không gọi tên khái niệm:
- **Nội dung:** `display_name` cộng mô tả A5 của mọi khái niệm học được, embed bằng `gemini-embedding-001`, 768 chiều, task tài liệu truy hồi.
  Câu hỏi embed bằng task truy vấn tương ứng.
- **Vì sao không dùng vector A6:** vector A6 embed với task `SEMANTIC_SIMILARITY`. Chúng chỉ làm nhánh so sánh trong lượt thử, không làm mặc định.
- **Chi phí:** không đáng kể (ước dưới 0,01 USD cho sáu cuốn). Lệnh vẫn qua chốt chi.

### 5. Ảnh công thức

Ảnh vùng công thức được cắt sẵn ở bước tải tài liệu, một lần cho mỗi tài liệu:
- **Cách cắt:** mã đọc các nút công thức của cây parse (`formula_id`, `page`, `bbox`, `raw_text`), vẽ trang PDF rồi cắt theo `bbox`. Ảnh lưu cạnh
  ảnh hình, khoá theo `formula_id`. Không đổi `chunk_id`, không chạy lại khâu nào. 0 USD.
- **Hiển thị:** web thay nhãn `[CTk]` trong chữ bằng ảnh gốc. LLM nhận chữ thô dạng `⟦CTk: raw_text⟧`, kèm ghi chú "chữ thô, có thể sai cấu trúc,
  không chép lại thành công thức". LLM chỉ được nhắc công thức bằng nhãn `[CTk]`.
- **Khi thiếu dữ liệu:** công thức thiếu `bbox` (DOCX, hoặc bộ đọc không ghi) thì không có ảnh. Khi đó bài giảng ghi cờ `thieu_cong_thuc`, và chỉ
  còn nhãn kèm chữ thô.
- **Phụ thuộc vé 16:** đầu ra công thức của bộ đọc nhẹ, nay là mặc định A1, phải được kiểm khi làm vé này. Nếu bộ đọc nhẹ không tách vùng công
  thức thì báo lại, không tự sửa A1.
- **Nhánh thí nghiệm:** gửi ảnh công thức cho mô hình đa phương thức, chỉ bật nếu chấm người cho thấy cần (báo cáo bài giảng, mục 4.6).

### 6. Mô hình đọc đồ thị học và nhãn nguồn

Phần này là module sâu nhất của Pha B: một mô hình đọc thuần trên artifact graph, lớp gán module, chỉ mục chunk và chỉ mục khái niệm. Nó không
gọi mô hình, nạp một lần cho mỗi phiên bản tài liệu, và mọi công cụ của agent cùng phần mã dựng của bài giảng đều đi qua nó.

Mô hình đọc trả lời sáu loại truy vấn:
- **Khái niệm:**
  - tra theo tên, alias, `display_name`: khớp theo ranh giới âm tiết, tên dài nhất trước;
  - tên phổ biến (xuất hiện ở quá nhiều chunk, ví dụ "chất" ở 297/671 chunk doc-4) chỉ được nhận khi câu hỏi gần như chỉ gồm tên đó;
  - tên trùng giữa hai khái niệm thì trả cả hai, không đoán.
- **Module:** thông tin module; quan hệ của một module hay chunk với module đang mở (`truoc`, `dang_mo`, `sau`, `khong_ro`).
- **Vì sao khái niệm đứng ở đây:**
  - chỉ đọc tiên quyết hiển thị (Hasse, tối đa 3) và `requires_edges`, kèm `quote`, trang, `soft_reason`, `order_relation`;
  - cạnh `cong_cu` ghi "công cụ, không bắt buộc";
  - cạnh ngược thứ tự sách ghi "sách trình bày ở phần sau".
- **Lộ trình tới khái niệm đích:** bọc `target_roadmap`, bỏ cạnh mềm. Liệt kê tối đa 12 module, phần còn lại gộp "và N module nữa"; ở doc-4,
  lộ trình p90 có 47 module.
- **Đi theo cạnh có kiểu:**
  - `requires` chỉ đọc `requires_edges`;
  - cạnh mở kiểu `requires` là đề xuất chưa kiểm, nên **không bao giờ trả cho người học**;
  - cạnh mở không có câu trích thì không trả.
- **Media:** chỉ cạnh `confirmed`, tối đa 2, kèm `caption_source`.

**Nhãn nguồn.** Mỗi ngữ cảnh gửi mô hình dùng nhãn ngắn; mã giữ bảng tra nhãn → `chunk_id`, vị trí ký tự, trang, đường mục. Các họ nhãn:

| nhãn | nghĩa |
|---|---|
| `S#` | đoạn (chunk) |
| `N#` | câu neo của tiên quyết |
| `Q#` | câu trích của cạnh `requires`, đã kiểm nguyên văn ở A8 |
| `R#` | cạnh mở |
| `H#` | hình hoặc bảng |
| `B#` | chunk bài tập |
| `CT#` | công thức |
| `K#` | khái niệm (thẻ khái niệm của quiz) |
| `D#` | ứng viên câu nhiễu |

Cùng một bảng nhãn dùng cho tên module, bài giảng, quiz, trợ lý và tài liệu.

### 7. Port mô hình, sổ chi và trần

Lõi dùng ba port gọi mô hình:
- **Phiên JSON hiện có** (`ask_json`, nhận ảnh): dùng cho tên module, quiz, lời gọi kiểm giải mù.
- **Phiên JSON có stream:** cho bài giảng. Port trả từng mẩu chữ của JSON. Lớp ứng dụng tách ra những ý đã đóng xong rồi kiểm từng ý, theo tài
  liệu chính thức của Gemini về stream structured output.
- **Port mô hình hội thoại có công cụ (mới):** cho trợ lý và tài liệu theo yêu cầu.
  - Một lượt nhận chỉ dẫn hệ thống, lịch sử, danh sách công cụ và chế độ gọi công cụ (`AUTO`, `NONE`).
  - Port trả luồng sự kiện: mẩu chữ, lời gọi công cụ, kết thúc kèm usage.
  - Phần riêng của nhà cung cấp (thought signature của Gemini 3) do phiên giữ kín và gửi lại đúng lượt, lớp ứng dụng không thấy.
  - Structured output không dùng chung với công cụ ở flash-lite, nên câu trả lời là văn bản Markdown có nhãn.

Sổ chi và trần được quy định như sau:
- **Sổ chi Pha B:** mọi lời gọi ghi `model_id`, mục đích (`module_title`, `lecture`, `quiz_gen`, `quiz_verify`, `assistant`, `document`,
  `embedding`), token vào/ra/suy nghĩ, USD, TTFT, tổng ms, `context_hash`. Sổ chi nằm trong kho Pha B (mục 12).
- **Trần:**
  - trợ lý: tối đa 5 vòng công cụ mỗi tin nhắn, và khoảng 0,01 USD cho các lời gọi của chính agent; khi vòng kế tiếp sẽ vượt trần thì gọi
    vòng cuối ở chế độ `NONE`;
  - công cụ tạo nội dung (`make_quiz`, `make_document`) chi theo trần riêng của chức năng đó và ghi riêng trong `usage`;
  - thử lại 429/503 tối đa 2 lần, lùi theo hàm mũ có nhiễu; timeout mỗi lời gọi đặt trong cấu hình.
- **Tỉ lệ gọi công cụ sai:** tên công cụ sai, tham số sai lược đồ, hay lặp một lời gọi lỗi. Tỉ lệ này được đo trong sổ chi. **Quá 10% thì báo
  chủ dự án trước khi thử mô hình mạnh hơn**; không tự đổi mô hình.

### 8. Bài giảng theo khái niệm

Theo ADR 0011, use case bài giảng nhận (tài liệu, phiên bản đồ thị, khái niệm) và trả luồng sự kiện rồi bản cuối theo hợp đồng `lecture-1`.

**Hai đường gọi chung một hàm:**
- nút bấm khái niệm của web;
- công cụ `get_lecture` của trợ lý.

Không có bản bài giảng thứ hai do agent tự viết.

**Phần do mã dựng**, gửi ngay ở sự kiện `skeleton`, 0 USD:
- vị trí: module, k/m, khái niệm trước và sau;
- câu định nghĩa nguyên văn kèm trang và ảnh công thức;
- danh sách tiên quyết hiển thị kèm câu trích và ghi chú thứ tự ("đã học ở module m", "cùng module, ngay trước", "sách trình bày ở phần sau");
- hình đã xác nhận;
- dòng "học để làm gì": tối đa 3 khái niệm học sau, chỉ tên.

**Lắp ngữ cảnh cho LLM**, theo thứ tự và hạn mức của báo cáo mục 4.1. Cụ thể:
- **Các khối:** thẻ khái niệm → câu định nghĩa (S1) → chunk dạy (S1) → tối đa 2 chunk định nghĩa thêm (S2, S3) → tối đa 3 tiên quyết (`N#` câu
  neo, `Q#` câu trích) → tối đa 3 cạnh mở có bằng chứng (`R#`) → hình xác nhận (`H#`) → tối đa 1 chunk bài tập (`B#`) → tên khái niệm học sau →
  nhắc nhiệm vụ ở cuối.
- **Trần mềm:** 2.500 token cho phần ngữ cảnh. Khi vượt, bỏ dần theo thứ tự: bài tập → học để làm gì → cạnh mở → chunk định nghĩa thứ hai →
  cắt đuôi chunk định nghĩa thứ nhất. Không bao giờ cắt chunk dạy hay câu định nghĩa.
- **Nhiều khái niệm cùng một chunk dạy:** chỉ dẫn yêu cầu "chỉ giảng khái niệm này; khái niệm khác trong đoạn chỉ nhắc tên".
- **Mô tả A5 là bản nháp chưa kiểm:** không nạp.

**Phần LLM viết**, lược đồ JSON của báo cáo mục 4.3. Có năm phần:
- `prereq_notes`: mỗi tiên quyết một câu nhắc nghĩa và một câu "vì sao cần";
- `explanation`: 3–6 ý;
- `example`: 0–1 ví dụ, ưu tiên ví dụ trong sách;
- `contrasts`: 0–2 ý;
- `self_check`: 1 câu, đáp án ẩn.

Thêm hai quy định:
- Mỗi ý có `sources` (nhãn) và `quote` (đoạn nguyên văn ngắn trong nguồn đầu tiên).
- `outside_document: true` được phép ở `example` và `contrasts`, tối đa 1 ý mỗi bài, không trích dẫn, và không chứa định nghĩa hay khẳng định về
  sách. Mục `gaps` ghi điều tài liệu không nói; web không hiện mục này.

**Luật kiểm K1–K9** (báo cáo, mục 4.4):

| # | luật | khi hỏng |
|---|---|---|
| K1 | đúng lược đồ và số mục | sinh lại 1 lần, rồi về mốc trích câu |
| K2 | nhãn trong `sources` có thật; `prereq`, `relation` có thật | bỏ ý |
| K3 | `quote` ≤ 200 ký tự, tìm được nguyên văn (NFC, chuẩn khoảng trắng) trong nguồn đầu tiên | bỏ ý |
| K4 | độ phủ âm tiết nội dung của `text` trong nguồn được trích ≥ ngưỡng đặt ở lượt thử | gắn cờ `can_soat`, vẫn hiện |
| K5 | không ký hiệu toán, chữ số hay biến mới ngoài nguồn được trích (kể cả chữ thô công thức). Ý `outside_document` được miễn nhưng bị đếm riêng | bỏ ý |
| K6 | không lặp n-gram 8 âm tiết ≥ 3 lần; không bị cắt vì hết token | sinh lại 1 lần với giới hạn chặt hơn |
| K7 | ý `outside_document` không trích dẫn, ≤ 1 mỗi bài, không nằm ở `explanation` hay `prereq_notes` | bỏ ý |
| K8 | `explanation` còn ≥ 2 ý sau khi bỏ | sinh lại 1 lần kèm danh sách lỗi; vẫn hỏng thì dùng mốc trích câu và đánh dấu |
| K9 | đáp án câu tự kiểm tra qua K2 và K3 | bỏ câu tự kiểm tra |

**Stream và kiểm:**
- Luật cục bộ (K2, K3, K5, K7) chạy ngay khi một ý đóng xong. Chỉ ý đạt mới đẩy ra sự kiện `item`.
- Hết stream thì chạy luật toàn bài, rồi gửi sự kiện `final`.
- Chỉ bản cuối được vào cache.

**Cache:**
- `lecture_key` là băm của tài liệu, khái niệm, `context_hash` (JSON chuẩn hoá của toàn bộ khối ngữ cảnh sau khi lắp), prompt, lược đồ, mô hình,
  cấu hình sinh và phiên bản hợp đồng.
- `graph_version` chỉ lưu làm siêu dữ liệu.
- Chống sinh trùng: một khoá chỉ có một lời gọi đang chạy, người đến sau nghe chung luồng.
- Không cache bản lỗi; cache âm 60 giây khi API lỗi.
- **Tải trước:** người học mở khái niệm k thì xếp hàng sinh khái niệm k+1 trong dãy học, nếu chưa có.

**Trường hợp đặc biệt:**
- Không có chunk dạy cũng không có chunk định nghĩa: không gọi LLM, trả `status = no_source` kèm các đoạn có nhắc tên.
- Mọi đường hỏng đều về mốc trích câu (V11), `status = fallback`.

**Chi phí ước:**
- khoảng 0,0019 USD mỗi bài (0,0013–0,0027); khoảng 70% là token ra;
- doc-1 khoảng 0,37 USD và doc-4 khoảng 0,92 USD nếu mọi khái niệm đều được bấm.

Giây chờ tới ý đầu và hết bài phải đo ở lượt thử.

### 9. Quiz tự kiểm tra

Theo ADR 0011, quiz chỉ sinh khi người học bấm "làm quiz" của một module, hoặc khi trợ lý gọi `make_quiz`.

**Đơn vị sinh và cache là khái niệm, không phải module:**
- Mỗi khái niệm có một ngân hàng 2 câu ở hai mức Bloom do mã gán theo `node_type` (báo cáo quiz, mục 3.1).
- Bấm quiz thì các khái niệm của module được sinh **song song**. Mỗi khái niệm đi qua: 1 lời gọi sinh → luật mã → 1 lời gọi kiểm "giải mù" → luật
  mã lần hai → ngân hàng.
- Câu nào sẵn sàng thì đẩy xuống web ngay. Câu đầu ước ra sau khoảng 5–10 giây (giả định, phải đo).
- Ngân hàng của khái niệm cache chung cho mọi người học, khoá theo `context_hash` của ngữ cảnh quiz khái niệm đó, cộng prompt, lược đồ, prompt
  kiểm, mô hình và cấu hình.
- Lần làm thì riêng từng người.

**Ngữ cảnh mỗi lời gọi sinh** (báo cáo quiz, mục 3.1):
- thẻ module: tên, mô tả, danh sách khái niệm;
- thẻ khái niệm (`K#`) kèm mức Bloom;
- câu neo và chunk dạy (`S#`), mô tả A5 ghi "chỉ để hiểu, không trích";
- tối đa 3 tiên quyết (`N#`);
- tối đa 4 ứng viên câu nhiễu (`D#`) do mã chọn: cạnh mở → cùng module → cùng cụm ở module đã học, ưu tiên cùng `node_type`;
- tối đa 2 chunk bài tập cùng chương làm mẫu văn phong (`B#`);
- một câu mẫu viết tay;
- nhắc nhiệm vụ.

Hình chưa nạp ở bản này.

**Dạng câu:**
- Trắc nghiệm một đáp án đúng, **3 phương án**.
- Mỗi lần làm có 1 câu cho mỗi khái niệm. Module 3–4 khái niệm thêm câu thứ hai cho các khái niệm đầu để đủ 5 câu.
- Lần làm sau dùng biến thể còn lại; thứ tự phương án do mã xáo.
- Không có câu đúng/sai, không có tự luận chấm bằng LLM.

**Luật kiểm Q1–Q8 cộng K5** (báo cáo quiz, mục 3.4):

| # | luật |
|---|---|
| Q1 | đúng lược đồ, đúng độ dài: `explanation` ≤ 300 ký tự, `why_wrong` ≤ 150 |
| Q2 | `quote` của đáp án nguyên văn trong chunk của chính khái niệm hoặc cùng module |
| Q3 | các phương án không trùng hay chứa nhau; phương án là tên khái niệm thì không được là tên, alias hay danh tính đã gộp của khái niệm đáp án |
| Q4 | câu nhiễu tự viết phải có `quote`; câu nhiễu là khái niệm khác thì câu neo khác câu neo của đáp án |
| Q5 | không lộ đáp án qua độ dài hay từ lặp; cấm "tất cả đều đúng", "KHÔNG", từ tuyệt đối |
| Q6 | không nhắc hình, bảng, `[formula]` hay nhãn công thức không có ảnh; **đáp án và câu nhiễu không bao giờ là công thức** |
| Q7 | tiếng Việt tự nhiên |
| Q8 | không trùng câu |
| K5 | không bịa ký hiệu toán |

**Lời gọi kiểm "giải mù":**
- Mô hình nhận chunk dạy và câu đã xáo, không đánh dấu đáp án.
- Mô hình chọn phương án và phán từng phương án: đúng, sai, hay nguồn không nói.
- Câu bị bỏ khi mô hình chọn khác đáp án, hoặc thấy hơn một phương án đúng. Câu nhiễu "đúng theo nguồn" thì bỏ câu; câu nhiễu "nguồn không nói" thì
  gắn cờ.
- Khái niệm không còn câu: sinh lại 1 lần; vẫn hỏng thì dùng câu điền khuyết (mốc V11) nếu đủ điều kiện, không thì bỏ khái niệm và ghi nhật ký.
  Câu hỏng không chặn cả bộ.

**Phản hồi** hiện khi nộp cả bài:
- mỗi câu: đúng/sai, đáp án đúng, giải thích kèm câu trích, và `why_wrong` của phương án đã chọn;
- cuối bài: danh sách khái niệm làm sai kèm link bài giảng;
- chỉ ghi "đúng 5/7 câu" như thông tin; không khen chê, không làm cổng.

Phản hồi tốn 0 USD, vì mọi chữ đã có sẵn trong ngân hàng.

**Lịch sử:** mỗi lần làm lưu theo người học gồm điểm theo khái niệm, câu đã chọn và thời điểm. Lịch sử chỉ để chính người học xem lại, không tính
trình độ. Quiz do trợ lý tạo cũng ghi vào đây.

**Báo câu lỗi:** người học báo lý do; câu bị báo nhiều lần thì ẩn khỏi ngân hàng chờ soát.

**Chi phí ước:**
- khoảng 0,0025 USD mỗi khái niệm, gồm sinh và kiểm;
- khoảng 0,015 USD mỗi module;
- cận trên mỗi cuốn: doc-1 0,49 USD, doc-4 1,22 USD.

### 10. Trợ lý agent

Theo ADR 0012, trợ lý là agent gọi công cụ, không có bộ định tuyến cố định. Mỗi tin nhắn đi theo bảy bước:
1. **Ngữ cảnh mồi do mã lắp** (0 USD). Gồm năm phần:
   - thẻ module đang mở;
   - khái niệm liên kết được, tối đa 2, kèm "vì sao đứng ở đây";
   - tối đa 4 đoạn truy hồi lai trên cả tài liệu, xếp ưu tiên module đang mở rồi các module trước, mỗi đoạn mang nhãn vị trí so với module đang mở;
   - tối đa 3 lượt hội thoại gần nhất (chỉ câu hỏi và câu trả lời, trần 1.000 token);
   - trạng thái phiên.

   Câu hỏi nối tiếp không liên kết được khái niệm nào thì mượn khái niệm của lượt trước. Ngữ cảnh mồi giúp phần lớn câu trả lời xong trong một
   lời gọi. Đây là tham số thiết kế phải đo ở lượt thử, không phải luật cứng.
2. **Vòng agent.** Mô hình hoặc trả lời, hoặc gọi công cụ.
   - Tối đa 5 vòng công cụ mỗi tin nhắn, trần khoảng 0,01 USD.
   - Vòng cuối, hoặc vòng sắp vượt trần, đặt chế độ `NONE`.
   - Sau mỗi lời gọi công cụ có sự kiện tiến trình cho người học.
3. **Mười công cụ.** Mọi công cụ tra cứu là hàm thuần trên mô hình đọc ở mục 6, có giới hạn độ dài kết quả. Tổng kết quả một vòng ≤ 2.500 token.
   Lỗi trả thông báo có cấu trúc, không ném ngoại lệ ra mô hình.

| công cụ | việc | giới hạn |
|---|---|---|
| `search_document(query, scope, k)` | truy hồi lai. `scope` ∈ {ưu tiên module, cả tài liệu, một module} | ≤ 6 đoạn, mỗi đoạn ≤ 1.200 ký tự |
| `lookup_concept(name)` | tra khái niệm theo tên, alias, mô tả (chỉ mục khái niệm) | ≤ 3 ứng viên |
| `get_module_info(module)` | tên, mô tả, khái niệm theo thứ tự, vị trí so với module đang mở | ≤ 300 token |
| `why_here(concept)` | tiên quyết Hasse kèm câu trích (mục 6) | ≤ 500 token |
| `path_to(target)` | module cần học tới khái niệm đích, đã gộp | ≤ 12 module |
| `traverse(concept, edge_type, direction)` | đi theo cạnh có kiểu; loại cạnh mở kiểu `requires` | ≤ 5 cạnh |
| `get_media(concept)` | hình hoặc bảng `confirmed` | ≤ 2 |
| `get_lecture(concept)` | đọc bài giảng trong cache; chưa có thì gọi đúng hàm của nút bấm | trả tóm tắt các ý kèm nhãn; web hiện bản đủ |
| `make_quiz(scope, n, level)` | tạo một lần làm quiz cho người học từ ngân hàng theo khái niệm (mục 9), sinh phần thiếu | `n` ≤ 10 |
| `make_document(request, scope)` | tạo tài liệu theo yêu cầu tự do (mục 11) | trần riêng |

4. **Trả lời.** Câu trả lời là văn bản Markdown stream từng chữ. Mỗi câu có nội dung về sách gắn nhãn (`[S2]`, `[Q1]`…) ở cuối câu. Nội dung ngoài
   sách đặt trong khối có nhãn "ngoài tài liệu" và không gắn trích dẫn.
5. **Hậu kiểm bằng mã**, dưới 50 ms:
   - nhãn lạ thì xoá;
   - câu có chữ số, ký hiệu toán hay tên khái niệm mà không có nhãn và không nằm trong khối ngoài tài liệu thì gắn cờ "chưa có nguồn";
   - câu trả lời không có nhãn hợp lệ nào mà cũng không phải câu "tài liệu không có" thì đổi thành câu từ chối cố định và ghi nhật ký;
   - mô hình được dặn trả `KHONG_DU` ở dòng đầu khi ngữ cảnh không đủ; mã đổi tín hiệu này thành câu từ chối kèm các đoạn gần nhất.
6. **Phần mã gắn thêm**, 0 USD:
   - ghi chú "học kỹ ở module N" khi khái niệm thuộc module sau;
   - khối nhắc khái niệm nền theo bảng luật ở báo cáo trợ lý, mục 3.5: tối đa 1 khối mỗi câu trả lời, tối đa 3 khái niệm, không nhắc lại trong
     phiên, không nhắc ở câu từ chối hay câu nối tiếp ngắn, có nút tắt;
   - tham chiếu ảnh công thức và media `confirmed`.
7. **Ghi nhật ký:** khái niệm liên kết, đoạn đã nạp, các lời gọi công cụ (`by` ∈ {`code`, `model`}), token, USD, giây chờ, `context_hash`.

**Không cache câu trả lời chung giữa người học**, vì câu trả lời phụ thuộc lịch sử và module đang mở. Trạng thái phiên do máy chủ giữ trong kho Pha B:
`doc_id`, module đang mở, tập khái niệm đã nhắc, 3 lượt gần nhất. Không lưu trình độ.

**Chi phí ước:**
- một lời gọi: khoảng 0,0014–0,0021 USD;
- hai đến ba vòng: khoảng 0,0022–0,0034 USD;
- trần 0,01 USD mỗi tin nhắn.

Giây chờ phải đo.

### 11. Tài liệu theo yêu cầu

`make_document` nhận yêu cầu tự do của người học (ví dụ "một bản chi tiết về khái niệm X", "đề cương ôn chương 2") và một phạm vi: khái niệm,
danh sách khái niệm, hay module.

**Cách lắp và sinh:**
- **Ngữ cảnh:** với mỗi khái niệm trong phạm vi, lắp như bài giảng; phạm vi lớn thì chỉ lấy câu định nghĩa, chunk dạy và tiên quyết. Thêm truy hồi
  theo yêu cầu.
- **Ngân sách:** trần ngữ cảnh 8.000 token, trần đầu ra 3.000 token, trần chi 0,01 USD mỗi tài liệu (ước, chỉnh ở lượt thử).
- **Đầu ra:** Markdown có nhãn trích dẫn và khối ngoài tài liệu như câu trả lời của trợ lý. Hậu kiểm bằng cùng luật. Công thức chỉ bằng nhãn
  `[CTk]`.

**Lưu và tải:** tài liệu lưu theo người học, không cache chung. Người học tải về được dạng Markdown, nhãn đã đổi thành chú thích nguồn (trang, mục).
PDF để sau.

### 12. Kho Pha B (port lưu trữ)

Lõi chỉ thấy một port lưu trữ. Bản cài cho CLI và kiểm thử ghi tệp JSON; nhóm web cài bản Postgres theo cùng hợp đồng. Port chứa sáu loại dữ liệu:
- **Cache chung:** bài giảng theo `lecture_key`; ngân hàng quiz theo khoá khái niệm; khoá chống sinh trùng; cache âm.
- **Theo người học:** lần làm quiz, quiz do trợ lý tạo, tài liệu theo yêu cầu, phiên hội thoại.
- **Sổ chi Pha B** (mục 7).
- **Phản hồi:** báo sai quan hệ, báo câu hỏi lỗi, nút tắt nhắc. Dữ liệu này dành cho A13 sau này.
- **Ảnh công thức và ảnh hình:** chỉ là tham chiếu tới kho ảnh có sẵn từ bước tải tài liệu.
- **Chỉ mục khái niệm và lớp gán module:** chỉ là tham chiếu tới artifact.

### 13. Hợp đồng dữ liệu cho web

Mọi đối tượng có `contract_version`. Đường dẫn API, xác thực và giao diện do nhóm web tự thiết kế. Các hợp đồng dưới đây trích phần mang quyết
định từ bốn báo cáo; chi tiết từng trường đọc ở báo cáo tương ứng.

Có bốn quy ước chung:
- **Trích dẫn** có cùng hình dạng ở mọi nơi: `{label, chunk_id, page, section_path, char_start, char_end, quote}`. Web làm một thành phần hiện
  nguồn dùng chung.
- **Công thức:** `formula_refs` có dạng `{label, formula_id, image_ref, page, bbox}`.
- **Media:** `{media_id, kind, caption, caption_source, image_ref}`, chỉ chứa media `confirmed`.
- **`usage`** có mặt ở mọi đối tượng sinh, để nhóm ghi USD và giây chờ; web không hiện cho người học.

**Module**, trường mới trong lộ trình:

```json
{"module_id": "module_008", "index": 7, "title": "Phép toán trên ma trận", "section_code": "2.1",
 "title_source": "llm | author_section | fallback",
 "description": [{"text": "…", "node_ids": ["…"]}], "description_source": "llm | template"}
```

**Bài giảng** `lecture-1`. Hợp đồng đầy đủ ở báo cáo bài giảng, mục 5. Hai điểm thay đổi:
- `outside_document` được phép ở `example` và `contrasts`;
- `status` ∈ {`ready`, `generating`, `fallback`, `no_source`, `failed`}.

Có ba sự kiện stream:
- `skeleton`: mọi phần do mã dựng;
- `item`: một ý đã qua luật cục bộ, kèm `section_kind`;
- `final`: bản đầy đủ.

```json
{"contract_version": "lecture-1", "doc_id": "…", "graph_version": "…", "node_id": "…", "lecture_key": "sha256:…",
 "status": "ready", "position": {"module_id": "…", "module_index": 3, "index_in_module": 2, "count_in_module": 6,
 "previous_node_id": "…", "next_node_id": "…"},
 "definition": {"quote": "…", "chunk_id": "…", "page": 10, "formula_refs": []},
 "prerequisites": [{"node_id": "…", "name": "…", "module_index": 2, "order_note": "module_truoc | cung_module_truoc | sach_trinh_bay_sau",
                    "why": {"quote": "…", "chunk_id": "…", "page": 10}, "note": {"text": "…", "citations": [], "check": "pass"}}],
 "sections": [{"kind": "giai_thich | vi_du | phan_biet",
               "items": [{"text": "…", "citations": [], "formula_labels": ["CT1"], "outside_document": false, "check": "pass | can_soat"}]}],
 "media": [], "used_later": [], "self_check": {"kind": "…", "question": "…", "answer": "…", "citations": []},
 "warnings": ["thieu_cong_thuc", "ban_trich_cau", "khong_co_doan_day"], "usage": {}}
```

**Quiz** `quiz-1`. Có năm đối tượng, theo báo cáo quiz, mục 4:
- trạng thái sinh của một lần làm: tổng số khái niệm, số câu đã sẵn sàng;
- **đề gửi web: không có `is_correct`, `why_wrong` hay giải thích**;
- bài nộp;
- kết quả kèm phản hồi và danh sách ôn;
- báo câu lỗi.

Có hai sự kiện stream:
- `item_ready`: một câu, đã bỏ đáp án;
- `done`.

Mỗi lần làm có `origin` ∈ {`module_button`, `assistant`}.

**Trợ lý** `answer-1`. Hợp đồng theo báo cáo trợ lý mục 4, với các thay đổi do bỏ bộ định tuyến:
- yêu cầu: `doc_id`, `graph_version`, `session_id`, `current_module_id`, `question`, `client_turn_id`;
- sự kiện stream:
  - `progress`: chữ tiến trình;
  - `tool_call`: `name`, `args`, `by`, `result_summary`, `ms`;
  - `graph_card`: ghi chú module và khối nhắc nền, do mã sinh;
  - `delta`: chữ có nhãn;
  - `artifact`: tham chiếu tới bài giảng, lần làm quiz hay tài liệu vừa tạo;
  - `final`;
- `status` ∈ {`answered`, `partial`, `not_in_document`, `insufficient_context`, `budget_exhausted`, `error`};
- `final` thêm `outside_document_blocks` và `created_artifacts`.

**Tài liệu** `document-1`:

```json
{"contract_version": "document-1", "document_id": "…", "owner": "…", "doc_id": "…", "request": "…",
 "scope": {"node_ids": ["…"], "module_ids": []}, "title": "…", "markdown": "…", "citations": [],
 "outside_document_blocks": 1, "formula_refs": [], "status": "ready | failed", "usage": {}}
```

### 14. Lệnh CLI

Mỗi use case có lệnh CLI để kiểm thử và đo trước khi có web. Lệnh nào gọi mô hình hoặc embedding thì có `--dry-run` (dự toán, không ghi gì) và
`--allow-spend`. Có các lệnh sau:
- **Khâu tên module:** nằm trong `roadmap`, cộng một lệnh chạy riêng khâu tên trên artifact A10 có sẵn.
- **Gán module cho chỉ mục:** A12, 0 USD.
- **Lập chỉ mục khái niệm:** có tiền embedding.
- **Cắt ảnh công thức:** 0 USD.
- **Sinh bài giảng** cho một khái niệm, hoặc cho một danh sách khái niệm (để chấm).
- **Sinh quiz** cho một module hoặc một danh sách khái niệm.
- **Hỏi trợ lý:** một câu, hoặc chạy cả một tệp câu hỏi. Có cờ chọn cấu hình: `llm_khong_bang_chung`, `rag_thuan`, `agent_khong_do_thi`, `agent_day_du`.
- **Tạo tài liệu theo yêu cầu.**
- **Xuất bảng chấm mù** cho tên module, bài giảng, quiz và câu trả lời. Bảng không lộ cấu hình.

### 15. Cấu hình mặc định

Mọi giá trị dưới đây nằm trong cấu hình và trong khoá cache khi có liên quan:

| mục | giá trị |
|---|---|
| mô hình | `gemini-3.1-flash-lite` cho mọi lời gọi |
| embedding | `gemini-embedding-001`, 768 chiều |
| nhiệt độ | 0 cho tên, bài giảng, quiz sinh, quiz kiểm; mặc định cho trợ lý và tài liệu |
| `maxOutputTokens` | tên 512; bài giảng 2.048; quiz sinh mỗi khái niệm 1.200; quiz kiểm 400; trợ lý 1.024; tài liệu 3.000 |
| trợ lý | tối đa 5 vòng công cụ, trần 0,01 USD mỗi tin nhắn; lịch sử 3 lượt, 1.000 token |
| bài giảng | trần ngữ cảnh 2.500 token; tải trước 1 khái niệm |
| thử lại | 2 lần cho 429/503; cache âm 60 giây |

---

## Quyết định kiểm thử

**Thế nào là một test tốt:**
- Test kiểm **hành vi nhìn từ ngoài**: đối tượng hợp đồng trả ra, dữ liệu ghi vào kho, số lời gọi mô hình. Không kiểm chữ prompt, thứ tự hàm nội bộ
  hay cấu trúc lớp.
- Mỗi bất biến có một test **được thấy đỏ trước** trên phiên bản sai, theo mục 5 của AGENTS.md. Kiểm hệ quả quan sát được độc lập, không kiểm lại
  một cờ mà mã vừa gán.
- Dữ liệu thử là một tài liệu tổng hợp nhỏ (vài module, vài khái niệm, có cạnh mềm, có cạnh mở kiểu `requires`, có media chưa xác nhận, có công
  thức, có chunk bài tập), cộng một lát thật của doc-6 hay naive-bayes khi cần.
- **Không dùng tài liệu tập giữ lại nào** (`d01-t01`, `d01-t02`, tập khoá D-02).

**Đường nối kiểm thử: một đường chính ở mức use case.**
- Mọi hành vi của Pha B được kiểm qua use case công khai (tên module, gán module, chỉ mục khái niệm, ảnh công thức, bài giảng, quiz, trợ lý, tài
  liệu). Mỗi use case chạy với ba đồ giả cho các port:
  - **mô hình giả theo kịch bản:** trả JSON, mẩu stream, lời gọi công cụ hay lỗi 429 theo kịch bản viết trước, và đếm lời gọi;
  - **embedding giả tất định;**
  - **kho Pha B trong bộ nhớ.**
- Các luật kiểm (K, Q, năm luật tên module, luật trích dẫn và từ chối của trợ lý) được kiểm bằng cách cho mô hình giả trả đầu ra vi phạm, rồi kiểm
  ý hay câu vi phạm không có trong hợp đồng. Không gọi thẳng hàm luật.
- Công cụ của agent được kiểm qua use case trợ lý: kịch bản cho mô hình gọi công cụ, rồi kiểm kết quả công cụ xuất hiện ở lượt kế và trong nhật ký.
  Không cần đường nối riêng cho từng công cụ.
- Lệnh CLI chỉ có test nối dây (lệnh gọi đúng use case, `--dry-run` không gọi mô hình và không ghi gì), theo mẫu test CLI hiện có.
- Lượt chạy có tiền dùng bộ ghi và phát lại phiên mô hình có sẵn. Phản hồi thật được ghi một lần, rồi thành bộ kiểm thử hồi quy 0 USD.

**Bất biến phải có test (danh sách tối thiểu):**
1. Ý có `quote` không tìm được nguyên văn, hoặc có nhãn lạ, không bao giờ có trong bài giảng, câu trả lời hay tài liệu.
2. Khi luật cục bộ đã cho ý ra ngoài, không ý nào bị rút lại sau đó. Bản cuối chỉ được thêm cờ hoặc thay bằng bản dự phòng có `status` tương ứng.
3. Ý `outside_document` không có trích dẫn, không nằm ở phần giải thích hay nhắc nền, và tối đa 1 mỗi bài.
4. Cạnh mở kiểu `requires` và media chưa `confirmed` không bao giờ tới người học, ở mọi đường (bài giảng, công cụ, câu trả lời).
5. Cùng ngữ cảnh thì không gọi mô hình lần hai. Đổi chữ chunk hay tiên quyết thì gọi lại. Đổi phiên bản đồ thị mà ngữ cảnh không đổi thì không gọi.
6. Hai yêu cầu đồng thời cùng khoá chỉ sinh một lời gọi.
7. Đề quiz gửi web không chứa đáp án hay lời giải thích.
8. Câu quiz bị lời gọi kiểm phán sai đáp án, hay có hơn một phương án đúng, bị bỏ. Khái niệm hỏng hết thì có câu điền khuyết hoặc bị bỏ, không chặn
   các câu khác.
9. Trợ lý dừng đúng ở 5 vòng công cụ hoặc ở trần USD, trả `budget_exhausted` hay `partial` kèm phần đã có.
10. Câu trả lời không có nhãn hợp lệ bị đổi thành câu từ chối. `KHONG_DU` bị đổi thành câu từ chối kèm đoạn gần nhất.
11. Khối nhắc khái niệm nền không lặp lại cùng khái niệm trong một phiên, và không có ở câu từ chối.
12. Tên module:
    - không có số đánh mục;
    - dùng `display_name`;
    - từ mượn module kề hay từ không có căn cứ dẫn tới đường lùi;
    - module trùng một mục, tiêu đề tốt, giữ tiêu đề tác giả khi mô hình giả trả đúng tiêu đề đó.
13. Mọi giới hạn mà mã kiểm (độ dài, số mục, trần) lấy từ cùng một nguồn với giá trị viết trong prompt. Test thay giá trị ở nguồn rồi kiểm prompt
    đổi theo.
14. `get_lecture` của trợ lý và nút bấm trả cùng một `lecture_key`.
15. Mọi lời gọi mô hình đều có dòng trong sổ chi. `--dry-run` không gọi mô hình và không ghi kho.
16. A12 không đổi vector hay `chunk_id`. Chunk không dạy khái niệm nhận `module_source = hint` đúng theo chunk dạy đứng trước.

**Tiền lệ trong repo:**
- **Use case dùng kho giả và mô hình giả kiểu duck typing:** test khâu tên module (`start_session`, `ask_json`).
- **Dựng lộ trình và dự toán:** test build roadmap, roadmap plan, spend guard.
- **Hàm thuần của đồ thị và truy hồi:** test sequence, roadmap, a3 retrieval.
- **Test CLI hiện có.**
- **Test kiến trúc:** lớp application không import infrastructure; domain chỉ dùng thư viện chuẩn. Phải giữ nguyên.
- **Bộ ghi và phát lại phiên LLM có sẵn.**

---

## Ngoài phạm vi

Các việc sau không thuộc spec này:
- **Mô hình hoá trình độ người học:** mastery, BKT, học thích nghi (B4), ôn giãn cách tự động, và **mở khoá module**. Đề cương để các việc này
  ngoài phạm vi; quiz chỉ để tự kiểm tra.
- **Giao diện và hạ tầng web:** thiết kế API, xác thực, lược đồ cơ sở dữ liệu cụ thể, giao diện React. Nhóm web làm theo hợp đồng ở mục 13.
- **Màn quản trị A13.** Spec chỉ ghi phản hồi để A13 dùng sau.
- **Mở rộng nguồn và tài liệu:** nhiều tài liệu cho một người học; tìm kiếm web.
- **Các dạng nội dung khác:** tự luận chấm bằng LLM; thẻ ghi nhớ; tài liệu tải về dạng PDF.
- **Sinh trước trọn cuốn bằng Batch/Flex.** Chỉ tải trước một khái niệm.
- **Sửa gốc ở A1 và A2:**
  - LaTeX công thức (CodeFormulaV2);
  - dòng tiêu đề gộp;
  - xstk mất §2 và §3;
  - vai trò `de_cuong` gán nhầm.

  A1 đang tạm dừng; khâu tên chỉ có luật tạm cho `de_cuong`.
- **Bản đặt tên không LLM riêng cho seminar.** Đường lùi tối giản không phải một phương pháp seminar.
- **Mô hình mạnh hơn flash-lite.** Chỉ đổi khi chủ dự án duyệt (xem mục 7).
- **Đánh giá trên tập giữ lại T-01 hay tập khoá D-02.**

---

## Ghi chú thêm

**Thứ tự làm**, bốn đợt vé. Lượt thử có tiền chạy cuối mỗi đợt, dry-run trước:
1. **Nền:**
   - khâu tên module (LLM, đường lùi, ba sửa lỗi);
   - A12 lớp gán module;
   - chỉ mục khái niệm;
   - ảnh công thức;
   - mô hình đọc đồ thị học và bảng nhãn;
   - port mô hình hội thoại có công cụ;
   - kho Pha B, sổ chi.
2. **Trợ lý agent và bài giảng:** gồm `get_lecture` dùng chung với nút bấm.
3. **Quiz và tài liệu theo yêu cầu:** gồm `make_quiz`, `make_document`.
4. **Đánh giá:** bốn cấu hình trợ lý, RAGAS chạy bằng Gemini, bảng chấm mù.

Đề cương đặt trợ lý ở tuần 7 (19–25/10) và bài giảng ở tuần 8. Theo nguyên tắc chất lượng hơn hạn chót, nếu không kịp thì báo để dời, không cắt
luật kiểm.

**Ngân sách lượt thử đầu:** trần chung 16 USD, chủ dự án đã duyệt ngày 2026-10-15. Dự toán trong báo cáo:
- tên module: dưới 1 USD;
- bài giảng: trần 5 USD;
- quiz: khoảng 1,7 USD;
- trợ lý lượt 1: khoảng 8 USD.

Kiến trúc agent đầy đủ tốn hơn kiến trúc lai mà báo cáo dự toán, nên dự toán trợ lý phải làm lại bằng dry-run. Lượt 2 của trợ lý (khoảng
20 USD theo báo cáo) xin duyệt sau khi có kết quả lượt 1.

**Đánh giá chất lượng**, giao thức chi tiết ở mục 7, 6, 5, 5 của bốn báo cáo:
- **Người chấm:** hai thành viên nhóm chấm độc lập, cỡ mẫu khoảng 60% mức báo cáo đề xuất (ước):
  - tên: 142 module;
  - bài giảng: khoảng 50 khái niệm;
  - quiz: khoảng 200 câu, giảng viên chấm 20 câu nếu được;
  - trợ lý: bộ câu hỏi thử do agentic sinh rồi người duyệt, chấm người một mẫu khoảng 60 câu trả lời.
- **Đo độ đồng thuận** bằng κ của Cohen, kèm Gwet AC1 vì κ dễ thấp giả khi phân bố lệch.
- **Luật quyết định viết trước khi đo.** Với tên module, theo mục 7.6 đã sửa của báo cáo: không tự bỏ LLM; chỉ chọn biến thể LLM.
- **Báo riêng:**
  - tỉ lệ nội dung ngoài sách;
  - tỉ lệ ý `can_soat`;
  - tỉ lệ đường lùi;
  - tỉ lệ gọi công cụ sai;
  - USD và giây chờ ở p50 và p90.

**Phụ thuộc và phối hợp:**
- **Vé 16 (A1 bộ đọc nhẹ):** đầu ra công thức và cây mục ảnh hưởng ảnh công thức và tên module.
- **Phiên pass phụ:** A8 đổi thì đồ thị đổi. Cache theo băm ngữ cảnh tự sinh lại đúng các phần bị ảnh hưởng.
- **Nơi để vé:** vé ở `task/sau-a10/`; kế hoạch v4 chỉ thêm một hàng trỏ tới đó.
- **Hai phiên không sửa tệp của nhau.**

**Rủi ro đã biết**, mỗi rủi ro kèm cách đo trong lượt thử:
- **Nhiệt độ 0 với Gemini 3:** dễ lặp câu. Luật K6 đo tỉ lệ lặp, và lượt thử có một nhánh nhiệt độ mặc định.
- **flash-lite gọi công cụ kém.** Ngưỡng báo là 10% gọi sai.
- **Lời gọi kiểm cùng mô hình dễ dãi với chính nó.** Đo độ chính xác của lời gọi kiểm so với người chấm.
- **"Nhiều hơn một đáp án đúng"** gần như không bắt được tự động, nên phải đo bằng người.
- **Ví dụ ngoài sách có thể sai hoặc gây hiểu lầm.** Đo riêng; nếu vượt 5% thì đề xuất tắt.
- **Phụ thuộc vào cây mục:** khi cây mục hỏng, tên module dựa nhiều vào danh sách khái niệm.
