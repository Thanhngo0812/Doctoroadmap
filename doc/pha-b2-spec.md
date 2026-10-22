# Spec Pha B2 — giao diện hai tầng, phiên theo phạm vi, tiến độ học, bài giảng `lecture-2`

**Ngày:** 2026-10-18. **Nhãn:** `ready-for-agent`. **Trạng thái:** chờ chia vé (skill `ticket`); vé sẽ ở `task/sau-a10/`.

**Quan hệ với [spec Pha B](pha-b-spec.md):** spec này bổ sung và thay **một phần** các mục 8 (bài giảng), 9 (quiz), 10 (trợ lý), 11 (tài liệu), 12
(kho) và 13 (hợp đồng dữ liệu). Mục nào không nhắc ở đây thì giữ nguyên. Khi hai spec lệch nhau, spec này thắng.

**Căn cứ:**
- [Nghiên cứu giao diện hai tầng và phạm vi phiên](../report/nghien-cuu-giao-dien-hai-tang-pham-vi-phien-2026-10-18.md)
- [Nghiên cứu bài giảng gợi lại tiên quyết, gợi mở, xử lý bài hỏng](../report/nghien-cuu-bai-giang-tien-quyet-goi-mo-xu-ly-hong-2026-10-18.md)
- [Kiểm thử Pha B](../report/kiem-thu-pha-b-2026-10-18.md) và [soát SA-25–28](../report/kiem-thu-pha-b-sa25-28-2026-10-18.md)

**Quyết định kiến trúc đi kèm:**
- [ADR 0017](adr/0017-pham-vi-phien-la-noi-luu-neo-vao-khai-niem.md): phạm vi phiên là nơi lưu và nơi ưu tiên tìm, không phải ranh giới; phạm vi neo
  vào khái niệm.
- [ADR 0018](adr/0018-bai-giang-khong-hien-ban-lui-stream-sau-cong.md): bài giảng không bao giờ hiện bản lùi; stream sau cổng; gợi lại tiên quyết bằng
  phần mã dựng cộng câu nối có trích dẫn.
- [ADR 0019](adr/0019-tien-do-hoc-khong-chan-nhan-gan-luc-doc.md): tiến độ học theo khái niệm, không chặn; nhãn theo người học gắn lúc đọc, không
  cache.

**Quyết định của chủ dự án:** đợt tra hỏi ngày 2026-10-18, vòng 1 (Q1–Q18) và vòng 2 (Q19–Q30). Chủ dự án theo mọi khuyến nghị, trừ Q17: không chạy
lại nhap-mon-ml và naive-bayes bằng chuỗi gộp. Về hợp đồng: "cứ đổi thoải mái nhóm web chưa triển khai đâu".

**Quy trình:** như spec Pha B. Claude viết spec và vé, chủ dự án giao nhân viên cài, Claude kiểm theo vé.

---

## Vấn đề

**Giao diện chủ dự án muốn có hai trang:**
- **Trang lộ trình:** danh sách module và khái niệm; các phiên chat về cả lộ trình; công cụ tạo tài liệu hay quiz theo ý người học.
- **Trang học:** mỗi module có các khái niệm để bấm học, và quản lý riêng các phiên chat, tài liệu và quiz của nó.

**Lõi Pha B hiện chưa phục vụ được hai trang này:**
- **Một kiểu phiên duy nhất,** khoá theo người học, tài liệu và mã phiên. Mỗi câu hỏi bắt buộc có module đang mở, nên không có phiên toàn lộ trình.
- **Không mở lại được phiên cũ:** phiên chỉ giữ 3 lượt cuối.
- **Không liệt kê được** phiên, tài liệu hay quiz theo module hay theo lộ trình.
- **Phạm vi lưu bằng mã module là không ổn định.**
  - Mã module chỉ là nhãn theo vị trí.
  - doc-1 từ v45 sang v53: 33 mã module vẫn còn, nhưng chỉ 2 module giữ nguyên tập khái niệm (Jaccard trung bình 0,26).
  - Trong khi đó 202/205 `node_id` còn nguyên.
  - Một phiên ghim theo mã module có thể lặng lẽ trỏ sang module khác.
- **Không có tiến độ học.** Vì vậy trợ lý không biết nên nhắc khái niệm nền nào, còn bài giảng không biết tiên quyết nào người học đã học.

**Bài giảng chưa cho người học thấy tính tiên quyết:**
- 3/12 bài của lượt thật có tiên quyết, nhưng 0/3 có ý nhắc nền. Spec cũ không có luật bắt buộc phần này.
- Phần "học để làm gì" (`used_later`) chỉ là danh sách tên, từng đi ngược chiều (đã sửa ở SA-26), và nằm trong số khối bị cắt đầu tiên khi ngữ cảnh
  dài.

**Bản lùi của bài giảng:**
- Chủ dự án quyết bản lùi trích câu không bao giờ hiện cho người học.
- Mã hiện vẫn trả bản lùi và còn ghi nó vào cache vĩnh viễn.
- 5/12 bài của lượt thật hỏng cả hai lần sinh. Một nửa nguyên nhân là K6 dò sai, đã giao ở SA-30.

**Trần chi** hiện chỉ có cho mỗi tin nhắn và mỗi chức năng; chưa có trần theo người học hay cho cả hệ thống.

## Giải pháp

**Trang lộ trình** (nhóm web dựng, lõi cung cấp dữ liệu):
- danh sách module (tên, mô tả, tiến độ "xong x/y") và khái niệm;
- danh sách phiên: phiên toàn lộ trình, cộng 5 phiên module gần nhất có nhãn module; bộ lọc "tất cả";
- thư viện tài liệu và quiz của lộ trình;
- nút "Tạo tài liệu" và "Làm quiz".
  - Quiz cả lộ trình tối đa 10 câu, ưu tiên khái niệm đã học để ôn.
  - Tài liệu tối đa 5 module mỗi yêu cầu.

**Trang học** (một module):
- khái niệm theo thứ tự; bấm vào thì mở bài giảng;
- các phiên chat của module;
- thư viện của module: nội dung tạo ở module này, cộng nội dung tạo ở nơi khác mà có khái niệm thuộc module này;
- nút tạo tài liệu và làm quiz;
- nút "đã học" ở mỗi khái niệm.

**Phiên:**
- Phạm vi chỉ quyết phiên lưu ở đâu và trợ lý ưu tiên tìm ở đâu, không giới hạn chỗ tìm. Hỏi sang module khác vẫn được trả lời, kèm thẻ "nội dung ở
  module N, mở module".
- Phiên lưu đủ mọi lượt, nên mở lại được. Tiêu đề do mã đặt; người học sửa và xoá được.
- Khi đồ thị lên phiên bản mới, phiên tự trỏ sang module mới có nhiều khái niệm trùng nhất. Nếu không còn module nào đủ giống, phiên chạy như phiên toàn
  lộ trình, kèm ghi chú "module này đã đổi".

**Tiến độ:**
- Đánh dấu theo khái niệm, không chặn gì.
- Người học tự bấm "đã học"; hệ thống tự đánh dấu khi người học làm đúng một câu quiz của khái niệm đó.

**Bài giảng `lecture-2`:**
- **Đầu bài** gợi lại tiên quyết:
  - tên, module, câu định nghĩa (gập sẵn) do mã dựng;
  - một câu nối do LLM viết, chỉ dựa câu trích của cạnh;
  - nhãn "đã học / chưa học" gắn riêng cho từng người học.
- **Cuối bài** có khối "Tiếp theo" do mã dựng.
- **Hiện dần:** các ý chỉ bắt đầu hiện khi bài đã có đủ 2 ý giải thích đạt. Từ lúc đó bài không còn hỏng được nữa.
- **Bài hỏng hẳn:**
  - vẫn giữ phần mã dựng, kèm lời nhắn, nút "Đọc trang p trong sách", "Hỏi trợ lý", và "Thử lại" (chỉ khi lỗi mạng);
  - không có câu nào do máy tự chọn từ sách;
  - không cache.

**Trần chi:**
- mỗi người học tối đa 0,20 USD mỗi ngày cho trợ lý và tài liệu;
- nội dung dùng chung (bài giảng, ngân hàng quiz) có trần hệ thống khoảng 5 USD mỗi ngày;
- hết trần thì vẫn dùng được mọi thứ 0 USD.

## User story

**Trang lộ trình**
1. Là người học, tôi muốn trang lộ trình hiện module với tên, mô tả và tiến độ "xong x/y", để biết mình đang ở đâu trong cả cuốn sách.
2. Là người học, tôi muốn mở một phiên chat về cả lộ trình mà không phải chọn module, để hỏi những câu bao quát như "học hết sách cần đi qua gì".
3. Là người học, tôi muốn trang lộ trình hiện các phiên toàn lộ trình của tôi, cộng 5 phiên module gần nhất có nhãn module, để quay lại nhanh cuộc trò
   chuyện gần đây.
4. Là người học, tôi muốn bộ lọc "tất cả" ở trang lộ trình, để thấy mọi phiên của mọi module ở một chỗ.
5. Là người học, tôi muốn nút "Làm quiz" ở trang lộ trình tạo một lần làm tối đa 10 câu trải trên các module, ưu tiên khái niệm tôi đã học, để ôn tập.
6. Là người học, tôi muốn nút "Tạo tài liệu" ở trang lộ trình cho chọn tối đa 5 module, để có bản tổng hợp theo ý mình mà không chờ quá lâu.
7. Là người học, tôi muốn biết khi yêu cầu tài liệu vượt 5 module, trợ lý đề nghị tôi thu hẹp phạm vi, thay vì nhận một tài liệu hỏng.
8. Là người học, tôi muốn thư viện của trang lộ trình chứa tài liệu và quiz tôi tạo ở đó, để không bị lẫn với nội dung của từng module.

**Trang học**
9. Là người học, tôi muốn vào trang học của một module và thấy khái niệm theo thứ tự lộ trình, để học lần lượt.
10. Là người học, tôi muốn mỗi module có danh sách phiên chat riêng, để câu hỏi về module nào nằm ở module đó.
11. Là người học, tôi muốn thư viện của module chứa tài liệu và quiz tạo ở module này, để ôn lại đúng chỗ.
12. Là người học, tôi muốn thư viện của module hiện thêm cả nội dung tạo ở nơi khác mà nói về khái niệm của module này, kèm nhãn "tạo ở nơi khác", để
    không bỏ sót.
13. Là người học, tôi muốn nút "Tạo tài liệu" và "Làm quiz" ngay trong trang module, để không phải gõ yêu cầu vào chat.
14. Là người học, tôi muốn bấm "đã học" hay bỏ dấu ở mỗi khái niệm, để tự quản lý tiến độ.
15. Là người học, tôi muốn khái niệm được tự đánh dấu "đã học" khi tôi làm đúng một câu quiz của nó, để không phải bấm tay.
16. Là người học, tôi muốn việc tôi bỏ dấu một khái niệm được tôn trọng, nghĩa là quiz không tự đánh dấu lại, để tiến độ đúng như tôi muốn.
17. Là người học, tôi muốn module hiện "xong x/y", để biết còn bao nhiêu khái niệm.
18. Là người học, tôi muốn vẫn mở được mọi module dù chưa học xong module trước, vì tiến độ không chặn gì.

**Phiên chat**
19. Là người học, tôi muốn hỏi trong phiên module về một khái niệm của module khác mà vẫn được trả lời, kèm thẻ "nội dung ở module N, mở module", để
    không bị từ chối vô lý.
20. Là người học, tôi muốn trợ lý trong phiên module ưu tiên tìm trong module đó, để câu trả lời sát bài đang học.
21. Là người học, tôi muốn mở lại một phiên cũ và thấy đủ mọi lượt hỏi đáp, để học tiếp từ chỗ dừng.
22. Là người học, tôi muốn phiên có tiêu đề tự đặt theo khái niệm tôi hỏi đầu tiên, để nhận ra phiên trong danh sách.
23. Là người học, tôi muốn sửa tiêu đề phiên, và tiêu đề tôi đặt không bị máy ghi đè.
24. Là người học, tôi muốn xoá một phiên, còn tài liệu và quiz phiên đó tạo ra vẫn nằm trong thư viện.
25. Là người học, tôi muốn phiên toàn lộ trình không nhắc khái niệm nền, vì ở đó không có bài đang học để nhắc.
26. Là người học, tôi muốn phiên module nhắc tối đa 3 tiên quyết mà tôi **chưa** đánh dấu đã học, và không nhắc lại trong cùng phiên.
27. Là người học, tôi muốn khi sách được xử lý lại và module đổi, phiên cũ của tôi vẫn trỏ đúng module mới chứa các khái niệm cũ, hoặc báo rõ "module này
    đã đổi".
28. Là người học, tôi muốn tài liệu hay quiz do trợ lý tạo trong phiên nằm ở thư viện của phạm vi phiên đó.
29. Là người học, tôi muốn biết khi tôi đã dùng hết trần chi trong ngày; lúc đó bài giảng có sẵn, quiz có sẵn và khung bài vẫn dùng được.

**Bài giảng**
30. Là người học, tôi muốn đầu bài giảng gợi lại các tiên quyết, gồm tên, module và câu định nghĩa gập sẵn, để nhớ lại nếu cần mà không bị làm phiền nếu
    đã biết.
31. Là người học, tôi muốn mỗi tiên quyết có một câu ngắn nói khái niệm này dùng tiên quyết đó ra sao, có trích dẫn, để hiểu vì sao phải học trước.
32. Là người học, tôi muốn mỗi tiên quyết có nhãn "bạn đã học, module m" hay "chưa học, module m" theo tiến độ của tôi, để biết nên quay lại đâu.
33. Là người học, tôi muốn câu nối không bao giờ nói "như bạn đã học" khi tôi chưa học, vì bài giảng dùng chung cho mọi người.
34. Là người học, tôi muốn cuối bài có khối "Tiếp theo" nêu 1–2 khái niệm sau dùng tới khái niệm này, kèm module và câu trích, để biết học nó để làm gì.
35. Là người học, tôi muốn bài giảng chỉ bắt đầu hiện dần khi đã chắc tạo được, để không thấy vài ý hiện ra rồi bài báo hỏng.
36. Là người học, tôi muốn khung bài (vị trí, định nghĩa nguyên văn kèm trang, tiên quyết, hình) hiện ngay khi bấm, để có cái đọc trong lúc chờ.
37. Là người học, tôi muốn khi bài hỏng hẳn vẫn thấy khung bài, kèm lời nhắn rõ ràng và các nút "Đọc trang p trong sách", "Hỏi trợ lý", để học tiếp được.
38. Là người học, tôi muốn nút "Thử lại" chỉ hiện khi lỗi là tạm thời, để không bấm vô ích.
39. Là người học, tôi muốn một lần bấm không bắt tôi chờ quá 30 giây.
40. Là người học, tôi muốn không bao giờ thấy đoạn "bài giảng" do máy tự nhặt câu từ sách, vì chất lượng của nó thấp.
41. Là người học ở nhap-mon-ml hay naive-bayes, tôi muốn vẫn thấy tên, vị trí và câu định nghĩa của tiên quyết, dù đồ thị cũ không có câu trích để viết
    câu nối.

**Vận hành và nghiên cứu**
42. Là chủ dự án, tôi muốn bài hỏng vì luật kiểm được ghi nhớ 24 giờ, để không trả tiền sinh lại cùng một ngữ cảnh gần như chắc hỏng lại.
43. Là chủ dự án, tôi muốn bài hỏng vì lỗi mạng chỉ được ghi nhớ 60 giây, để người học thử lại được.
44. Là chủ dự án, tôi muốn đổi prompt hay luật kiểm thì mọi bài hỏng cũ tự được sinh lại, không phải xoá tay.
45. Là chủ dự án, tôi muốn trần chi mỗi người mỗi ngày và trần hệ thống mỗi ngày đặt ở cấu hình chung, để chỉnh mà không sửa mã.
46. Là chủ dự án, tôi muốn sổ chi ghi đủ người học và mục đích cho mọi lời gọi có tiền, để trần ngày tính đúng.
47. Là người nghiên cứu, tôi muốn đo tỉ lệ bài có câu nối cho mọi tiên quyết có câu trích, và tỉ lệ câu nối bị loại theo từng luật.
48. Là người nghiên cứu, tôi muốn đo thời gian tới khung bài, tới ý đầu (sau cổng) và tới khi xong bài ở p50 và p90.
49. Là người nghiên cứu, tôi muốn so lần sinh lại ở nhiệt độ 0 với nhiệt độ 1,0, để quyết bằng số.
50. Là thành viên nhóm web, tôi muốn hợp đồng JSON cho phiên, lượt, thư viện, tiến độ và bài giảng, có ví dụ thật, để dựng hai trang mà không phải đoán.
51. Là chủ dự án, tôi muốn trang xem thử cục bộ có đủ hai trang, để thử trên trình duyệt trước khi web xong.

---

## Quyết định triển khai

### 1. Phạm vi (theo ADR 0017)

**Đối tượng phạm vi** `scope-1`:

```json
{"kind": "roadmap"}
{"kind": "module", "node_ids": ["…"], "module_id_at_creation": "module_008", "graph_version_at_creation": 53}
```

- **Phạm vi module lưu danh sách khái niệm** của module lúc tạo. Mã module và phiên bản đồ thị chỉ là siêu dữ liệu.
- **Giải phạm vi** là một hàm thuần ở domain. Nhận phạm vi và đồ thị hiện hành, trả `{module_id | null, stale, jaccard}`:
  - `roadmap` thì trả `module_id = null`;
  - `module` thì tìm module hiện hành có Jaccard cao nhất trên tập khái niệm. Nếu Jaccard ≥ `scope_remap_min_jaccard` (0,5), trả module đó; nếu không,
    trả `module_id = null, stale = true`.
- **Phạm vi stale** chạy như phạm vi lộ trình và mang ghi chú "module này đã đổi". Phạm vi đã lưu không bị ghi lại.
- **Mọi chỗ cần module của một phạm vi đều qua hàm giải này:** trợ lý, thư viện, danh sách phiên.

### 2. Phiên và lượt

**Phiên** `session-1`, mỗi phiên một bản ghi:

| trường | ý nghĩa |
|---|---|
| `session_id`, `owner`, `doc_id`, `scope` | khoá và phạm vi |
| `title`, `title_source` ∈ {`rule`, `learner`} | tiêu đề |
| `created_at`, `updated_at`, `turn_count`, `last_question_preview` (≤ 80 ký tự) | cho danh sách |
| `artifact_refs` | tham chiếu tới tài liệu và lần làm quiz do phiên tạo |
| `state` | `reminded_node_ids`, `linked_node_ids`, `reminders_enabled` (giữ từ phiên cũ) |

**Lượt** `turn-1`: `{turn_id, session_id, client_turn_id, question, answer, created_at}`, với `answer` là đối tượng `answer-2`.
- Lưu **mọi** lượt.
- Ngữ cảnh gửi mô hình vẫn chỉ là 3 lượt cuối, ≤ 1.000 token, như cũ.

**Use case phiên:**
- `create_session(owner, doc_id, scope)`.
- `list_sessions(owner, doc_id, filter)`, với `filter` ∈ {`roadmap_page`, `module:<module_id>`, `all`}:
  - `roadmap_page` trả mọi phiên `roadmap`, cộng `roadmap_recent_module_sessions` (5) phiên module gần nhất, kèm nhãn module đã giải;
  - `module:X` trả các phiên giải ra module X;
  - phiên stale chỉ có ở `roadmap_page` và `all`, có ghi chú.
- `rename_session`: đặt `title_source = learner`.
- `delete_session`: xoá phiên và các lượt của nó, không xoá nội dung trong thư viện.
- `list_turns(owner, session_id)`.

Mọi use case kiểm `owner`.

**Tiêu đề do luật**, 0 USD:
- Đặt sau lượt có trả lời đầu tiên.
- Có khái niệm liên kết được thì lấy `display_name` của khái niệm đầu. Không có thì lấy câu hỏi, cắt ở ranh giới từ, ≤ `session_title_max_chars` (60).
- `title_source = learner` thì luật không bao giờ ghi đè.

### 3. Trợ lý `answer-2` (thay một phần mục 10 của spec Pha B)

- **Yêu cầu:** `doc_id`, `graph_version`, `session_id`, `question`, `client_turn_id`. Bỏ `current_module_id`, vì module đang mở được lấy từ phạm vi của
  phiên qua hàm giải.
- **Tiêu điểm `focus_node_id`** (tuỳ chọn, chủ dự án duyệt 2026-10-22, vé SA-56):
  - web gửi kèm mỗi lượt khi người học đang mở bài giảng của một khái niệm; không lưu vào phiên;
  - mô hình nhận khối `focus`: tên, module, câu định nghĩa dưới dạng nguồn `[S#]`, và các ý bài giảng nếu đã có trong cache (chỉ đọc, 0 USD). Khối này
    tối đa `assistant_focus_tokens` (400);
  - câu hỏi không nêu tên khái niệm thì khái niệm liên kết là tiêu điểm;
  - giá trị không phải khái niệm học được của đồ thị thì bị bỏ, kèm cảnh báo `focus_ignored`;
  - không có tiêu điểm thì đầu vào mô hình không đổi;
  - đầu ra thêm `focus_node_id`. Trường thêm vào và tuỳ chọn, nên vẫn là `answer-2`.
- **Phạm vi module:** giữ nguyên hành vi hiện tại: thẻ module, truy hồi ưu tiên module.
- **Phạm vi lộ trình hoặc stale:**
  - không ưu tiên module;
  - thay thẻ module bằng **thẻ lộ trình** gọn: số thứ tự, tên module, số khái niệm; khoảng 360–760 token;
  - khối nhắc khái niệm nền tắt.
- **Thẻ module ngoài phạm vi:** mọi khái niệm liên kết được mà nằm ngoài module đang mở đều có thẻ "nội dung ở module N" kèm `module_id` để web mở module.
  Ở phạm vi lộ trình, thẻ ghi "nằm ở module N".
- **Khối nhắc khái niệm nền** (thay luật cũ, chỉ ở phạm vi module):
  - nhắc tối đa 3 tiên quyết Hasse **chưa** đánh dấu đã học;
  - không nhắc lại trong cùng phiên;
  - không có ở câu từ chối;
  - tắt được.
- **Công cụ tạo nội dung:** `make_quiz` và `make_document` gán cho nội dung mới `home_scope` = phạm vi của phiên, `session_id`, và `origin = assistant`.
  Tham chiếu được thêm vào `artifact_refs` của phiên.
- **Trần ngày của người học:** xem mục 8. Hết trần thì `status = daily_limit` kèm câu thông báo do mã viết, 0 USD.
- **Phiên mở lại:** trạng thái nhắc nền (`reminded_node_ids`) giữ theo phiên.

### 4. Thư viện `library-1`

**Mỗi tài liệu và lần làm quiz có thêm năm trường:**
- `home_scope`: phạm vi nơi tạo;
- `session_id`, hoặc null nếu tạo bằng nút;
- `origin` ∈ {`button`, `assistant`};
- `node_ids`: các khái niệm nội dung bao phủ;
- `created_at`.

**`list_library(owner, doc_id, scope_filter)`:**
- **Module X**, hai nhóm:
  - nội dung có `home_scope` giải ra X: nhóm `here`;
  - nội dung tạo nơi khác mà `node_ids` giao với tập khái niệm hiện hành của X: nhóm `elsewhere`, có nhãn "tạo ở nơi khác".
- **Lộ trình:** nội dung có `home_scope = roadmap`, cộng bộ lọc `all`.

**Module của một nội dung được suy lúc liệt kê**, từ `node_ids` và đồ thị hiện hành, không lưu cứng.

Mỗi mục thư viện gồm `{kind: document | quiz_attempt, id, title, created_at, origin, group: here | elsewhere, module_labels}`. Mục quiz có thêm điểm nếu
đã nộp.

### 5. Tiến độ `progress-1` (theo ADR 0019)

**Bản ghi theo (owner, doc_id, node_id):** `{state: learned | not_learned, source: learner | quiz, updated_at}`.
- **Người học bấm:** đặt `state` theo lựa chọn, `source = learner`.
- **Quiz:** khi lần nộp có ít nhất một câu đúng của một khái niệm, khái niệm đó được đặt `learned` với `source = quiz`, **chỉ khi chưa có bản ghi
  `source = learner`**. Lựa chọn của người học luôn thắng.
- **Mở bài giảng không đánh dấu gì.**
- **Không chặn chức năng nào.** Đây là đánh dấu, không phải mô hình trình độ.

**Use case:**
- `set_progress(owner, doc_id, node_id, learned)`;
- `get_progress(owner, doc_id)`, trả trạng thái từng khái niệm và tóm tắt mỗi module `{module_id, learned, total}` theo đồ thị hiện hành.

**Khoá theo `node_id`,** nên tiến độ vẫn đúng khi đồ thị lên phiên bản mới.

### 6. Bài giảng `lecture-2` (theo ADR 0018; thay một phần mục 8 của spec Pha B)

**Phần mã dựng** (sự kiện `skeleton`, 0 USD):
- vị trí; câu định nghĩa nguyên văn kèm trang và ảnh công thức; media đã xác nhận.
- **`prerequisites[]`**, tối đa 3 tiên quyết Hasse. Mỗi tiên quyết có:
  - `recall`, gồm `node_id`, `name`, `module_index`, `module_title`, `order_note`, và `definition`, tức câu neo kèm trích dẫn. Web gập phần
    `definition` sẵn;
  - `bridge`, do LLM viết, hoặc null;
  - `learner_status`, gắn lúc đọc (mục 6.5).
- **`next_up[]`**, tối đa `next_up_max` (2) khái niệm.
  - Lấy theo cạnh `requires` đi ra, có câu trích, ưu tiên module gần nhất phía sau.
  - Mỗi mục có `{node_id, name, module_index, module_title, quote, citation}`.
  - Đồ thị không có câu trích (hai cuốn chuỗi v3) thì chỉ có tên và module, không có câu trích.
- `used_later` bị bỏ khỏi hợp đồng và khỏi prompt.

**Phần LLM viết**, thay `prereq_notes`:
- **`bridges`:** một câu nối cho mỗi tiên quyết có câu trích cạnh (`Q#`). Lược đồ `{prereq, text, sources, quote}`.
  - `text` tối đa `bridge_max_chars` (160 ký tự), giọng trung tính, ví dụ "Định thức dùng ma trận con để …".
  - `sources` gồm đúng nhãn `Q#` của tiên quyết đó.
  - `quote` nằm nguyên văn trong câu trích cạnh.
- **Tiên quyết `legacy_excerpt`** (không có câu trích cạnh) không được gửi để viết câu nối.
- `explanation` 2–6 ý, `example` 0–1, `contrasts` 0–2, `self_check`: như cũ.

**Luật kiểm mới**, cộng thêm vào K1–K9:

| # | luật | khi hỏng |
|---|---|---|
| K10 | mỗi tiên quyết có `Q#` có một câu nối đạt | không sinh lại; tiên quyết đó chỉ hiện `recall`; đếm |
| K11 | câu nối trích đúng `Q#` của chính tiên quyết đó, `quote` nguyên văn, `text` có tên hay alias của tiên quyết | bỏ câu nối |
| K12 | `text` ≤ `bridge_max_chars`; không có cụm nói về trạng thái người học ("như bạn đã học", "bạn đã biết", "ở bài trước"…), danh sách ở `BSettings` | bỏ câu nối |

**K6 chỉ dò trên chữ của ý,** đúng như SA-30.

**6.1 Stream sau cổng (S3).**
- **Trước cổng:** ý đạt luật cục bộ được giữ trong bộ đệm, chưa gửi.
- **Cổng mở** khi có đủ `lecture_min_explanations` (2) ý giải thích đạt. Khi đó gửi các ý trong bộ đệm theo thứ tự lược đồ, rồi stream các ý sau ngay khi
  chúng đạt.
- **Sau cổng, bài không còn hỏng được.**
  - Hết token, JSON vỡ ở đuôi, hay K6 sau cổng: giữ các ý đã đạt, bỏ phần còn lại. Trả `ready` kèm cảnh báo `cat_ngan`.
- **Bất biến:** không ý nào đã gửi bị rút lại.
- **Câu nối là ý LLM,** nên cũng chỉ gửi sau cổng. `recall` đã có ở `skeleton`.
- **Đo thêm:** khoảng cách từ cổng tới khi xong bài. Nếu p50 dưới 1 giây thì báo Claude để cân nhắc S2.

**6.2 Sinh lại và thời gian.**
- **Hỏng trước cổng** thì sinh lại 1 lần, ở nhiệt độ `lecture_retry_temperature`. Mặc định 0; lượt đo so 0 với 1,0.
- **Trần cả lần bấm:** `lecture_click_timeout_seconds` (30).
- **Thử lại ở tầng gọi mạng:** 1 lần trên đường người học đang chờ; 2 lần khi tải trước chạy nền.

**6.3 Bài hỏng hẳn.**
- `status = failed`, giữ mọi phần mã dựng, cộng đối tượng `failure`:

  ```json
  {"reason_code": "kiem_noi_dung | loi_mang | het_thoi_gian | tran_he_thong | khong_co_mo_hinh",
   "retryable": false, "read_page": {"page": 10, "chunk_id": "…"}, "ask_assistant": true}
  ```

- **`retryable`** là true với `loi_mang`, `het_thoi_gian`, và `tran_he_thong` (thử lại vào ngày sau).
- **`read_page`** lấy từ câu định nghĩa, hoặc chunk dạy đầu tiên. Web mở PDF gốc đúng trang. Máy chủ phải giữ PDF gốc; sáu cuốn phát triển có PDF ở 5/6
  cuốn.
- **Trạng thái `fallback` bị bỏ.** Không đường nào trả câu do TextRank chọn cho người học.
- **Hàm trích câu chỉ còn ở hai chỗ:**
  - mốc so sánh của vé đánh giá 21;
  - chế độ ngoại tuyến của trang xem thử. Ở chế độ này, bài vẫn trả `failed`, `reason_code = khong_co_mo_hinh`, không trả câu trích.

**6.4 Cache.**
- Chỉ bài `ready` vào cache chung.
- **Bản ghi hỏng:**
  - `kiem_noi_dung` được ghi nhớ `lecture_failure_ttl_seconds` (86.400);
  - `loi_mang` và `het_thoi_gian` được ghi nhớ `negative_cache_seconds` (60);
  - `tran_he_thong` được ghi nhớ tới hết ngày.
- Khoá bài gồm phiên bản luật kiểm và prompt, nên đổi một trong hai thì bản ghi hỏng cũ tự hết hiệu lực.

**6.5 Nhãn theo người học (theo ADR 0019).**
- Use case bài giảng trả nội dung lấy từ cache. Một bước gắn nhãn chạy lúc trả bài, thêm `learner_status` cho mỗi `prerequisites[]` và `next_up[]` từ
  tiến độ của người học:
  - `learned`, kèm `module_index`;
  - `not_learned`, kèm `module_index`;
  - `unknown`, khi không có `owner`.
- Nhãn này **không** vào cache, không vào `lecture_key`, và không bao giờ đi vào prompt.
- Bước gắn nhãn chạy cả ở đường nút bấm lẫn công cụ `get_lecture`.

**Chi phí ước:** câu nối thêm khoảng 0,0003 USD mỗi bài. Một bài tốn khoảng 0,0016–0,0030 USD.

### 7. Quiz `quiz-2` và tài liệu `document-2` (thay một phần mục 9, 11)

**Quiz:**
- `origin` ∈ {`button`, `assistant`}; có `home_scope`, `session_id`, `node_ids`.
- **Phạm vi lộ trình:** tối đa `quiz_roadmap_max_items` (10) câu.
  - Chọn khái niệm đã đánh dấu học trước, trải đều theo module.
  - Thiếu thì bù bằng khái niệm chưa học, cũng trải đều theo module.
  - Hạt giống cố định theo lần làm.
  - Ngân hàng chưa có thì sinh như cũ, tính vào trần hệ thống.
- **Nộp bài** thì cập nhật tiến độ theo mục 5.

**Tài liệu:**
- Có `home_scope`, `session_id`, `origin`, `node_ids`.
- **Phạm vi tối đa `document_max_modules` (5) module.** Vượt thì `status = failed`, `reason = scope_too_large`, 0 USD. Khi đó trợ lý đề nghị người học thu
  hẹp phạm vi.
- **Tạo bằng nút ở trang lộ trình** thì web gửi danh sách module hay khái niệm đã chọn.
- **Các sửa của SA-30** (câu trích do mã chọn, bỏ tiêu đề rỗng) là điều kiện trước.

### 8. Trần chi theo ngày

- **Trần người học:**
  - `learner_daily_max_usd` (0,20) mỗi người mỗi ngày;
  - chỉ tính `purpose` ∈ {`assistant`, `document`} của người học đó, đọc từ sổ chi;
  - kiểm trước mỗi lời gọi có tiền: chi hôm nay cộng ước của lời gọi, không được vượt trần;
  - công cụ `make_document` trong một lượt trợ lý tính vào cùng trần.
- **Trần hệ thống:**
  - `system_daily_max_usd` (5,0) cho nội dung dùng chung, gồm `lecture`, `quiz_gen`, `quiz_verify`;
  - hết trần thì bài giảng trả `failed` với `tran_he_thong`, còn quiz dùng ngân hàng sẵn có và câu điền khuyết.
- **"Ngày"** tính theo `spend_day_timezone` (Asia/Ho_Chi_Minh).
- **Sổ chi** phải có `learner_id` cho mọi dòng `assistant` và `document`; dòng thiếu thì test hỏng.
- **Đồng hồ** là một port nhỏ, để test cho thời gian chạy tới được.

### 9. Kho Pha B (thay một phần mục 12)

**Port lưu trữ:**
- Thêm `delete_record(kind, record_id)`.
- Thêm `list_records(kind, owner, doc_id)` có lọc theo `doc_id`.

**Loại bản ghi mới:** `session`, `turn`, `progress`, `lecture_failure`. Tài liệu và lần làm quiz thêm các trường ở mục 7.

Hai bản cài (JSON và bộ nhớ) qua chung một bộ test hợp đồng, như vé 01.

### 10. Hợp đồng dữ liệu (thay một phần mục 13)

**Phiên bản:** `session-1`, `turn-1`, `library-1`, `progress-1`, `scope-1` là mới. `lecture-2`, `answer-2`, `quiz-2`, `document-2` thay bản cũ, không giữ
tương thích ngược, vì nhóm web chưa dựng.

Phần mang quyết định của `lecture-2`:

```json
{"contract_version": "lecture-2", "status": "ready | generating | no_source | failed", "lecture_key": "sha256:…",
 "position": {"module_id": "…", "module_index": 3, "index_in_module": 2, "count_in_module": 6},
 "definition": {"quote": "…", "citation": {}, "formula_refs": []},
 "prerequisites": [{"recall": {"node_id": "…", "name": "…", "module_index": 2, "module_title": "…", "order_note": "module_truoc",
                               "definition": {"quote": "…", "citation": {}}},
                    "bridge": {"text": "…", "citations": [], "check": "pass"},
                    "learner_status": "learned | not_learned | unknown"}],
 "sections": [], "self_check": {}, "media": [],
 "next_up": [{"node_id": "…", "name": "…", "module_index": 5, "module_title": "…", "quote": "…", "citation": {}, "learner_status": "…"}],
 "failure": null, "warnings": ["cat_ngan"], "usage": {}}
```

**Sự kiện stream của bài giảng:**
- `skeleton`;
- `item`, chỉ sau cổng, kèm `section_kind` ∈ {`cau_noi`, `giai_thich`, `vi_du`, `phan_biet`, `tu_kiem_tra`};
- kết thúc bằng `final` hoặc `failure`.

**Đối tượng khác:**
- `answer-2` thêm `status = daily_limit`, `graph_card.scope_note` (cho phạm vi stale), và `graph_card.module_cards[]`.
- `session-1`, `turn-1`, `library-1`, `progress-1` có các trường như mục 2, 4, 5. Báo cáo của vé đính kèm ví dụ JSON thật cho nhóm web.

### 11. Trang xem thử (vé 24) thành hai trang

- **Trang lộ trình:** module kèm tiến độ, phiên toàn lộ trình cộng phiên gần đây, thư viện lộ trình, nút tạo quiz và tài liệu.
- **Trang học:** khái niệm, bài giảng `lecture-2` (tiên quyết gập sẵn, câu nối, "Tiếp theo", trạng thái hỏng), phiên module, thư viện module, nút "đã
  học".
- **An ninh giữ như vé 24:** chỉ localhost, chỉ sáu cuốn phát triển. Mặc định chạy chế độ phát lại hay mô hình giả.

### 12. Cấu hình mới trong `BSettings`

| khoá | mặc định |
|---|---|
| `scope_remap_min_jaccard` | 0,5 |
| `session_title_max_chars` | 60 |
| `roadmap_recent_module_sessions` | 5 |
| `learner_daily_max_usd` | 0,20 |
| `system_daily_max_usd` | 5,0 |
| `spend_day_timezone` | Asia/Ho_Chi_Minh |
| `quiz_roadmap_max_items` | 10 |
| `document_max_modules` | 5 |
| `bridge_max_chars` | 160 |
| `bridge_forbidden_phrases` | "như bạn đã học", "bạn đã biết", "ở bài trước", "như đã học" |
| `next_up_max` | 2 |
| `lecture_failure_ttl_seconds` | 86.400 |
| `lecture_click_timeout_seconds` | 30 |
| `lecture_click_transport_retries` | 1 |
| `lecture_preload_transport_retries` | 2 |
| `lecture_retry_temperature` | 0,0 |

Mọi giá trị mà prompt nhắc tới lấy từ đây, như vé 01.

---

## Quyết định kiểm thử

**Thế nào là một test tốt:** giữ như spec Pha B.
- Kiểm hành vi nhìn từ ngoài: đối tượng hợp đồng, bản ghi trong kho, số lời gọi mô hình.
- Mỗi bất biến có một test được thấy đỏ trước trên bản sai.
- Không dùng tập giữ lại.

**Đường nối kiểm thử: giữ một đường chính ở mức use case**, như đã duyệt cho Pha B.
- **Ba đồ giả như cũ:** mô hình giả theo kịch bản, embedding giả, kho trong bộ nhớ.
- **Thêm một đồ giả:** đồng hồ giả, cho trần ngày và thời hạn ghi nhớ bài hỏng.
- **Thêm một dữ liệu thử:** cặp đồ thị tổng hợp v1, v2 cùng tập khái niệm nhưng chia module khác nhau, có module "biến mất". Dùng cho phép giải phạm vi.

**Bất biến phải có test**, mỗi cái thấy đỏ trước:
1. Phiên module mà đồ thị đổi thì giải sang module có Jaccard cao nhất. Dưới 0,5 thì stale, và trợ lý chạy không ưu tiên module.
2. Phiên lưu đủ mọi lượt. Mở lại phiên thì `list_turns` trả đủ, nhưng mô hình chỉ nhận 3 lượt cuối.
3. Tiêu đề do luật không ghi đè tiêu đề người học đặt.
4. Xoá phiên thì nội dung phiên tạo vẫn có trong thư viện.
5. Thư viện của module X có nội dung tạo nơi khác mà `node_ids` thuộc X, với nhãn `elsewhere`. Module được suy theo đồ thị hiện hành, không theo mã lưu lúc
   tạo.
6. Lựa chọn của người học thắng: bỏ dấu một khái niệm rồi làm đúng quiz của nó thì nó vẫn `not_learned`.
7. Nhắc nền ở phạm vi module chỉ nhắc tiên quyết chưa học. Ở phạm vi lộ trình thì không nhắc.
8. `learner_status` không bao giờ có trong cache hay `lecture_key`. Hai người học có tiến độ khác nhau nhận cùng `lecture_key`, nhưng nhãn khác nhau.
9. Trước cổng không có sự kiện `item` nào. Sau cổng, JSON vỡ ở đuôi vẫn trả `ready` kèm `cat_ngan`, và không rút ý nào đã gửi.
10. Không đường nào trả `status = fallback`, hay câu do TextRank chọn, cho người học.
11. Bài `failed` vì luật kiểm được ghi nhớ 24 giờ: bấm lại thì 0 lời gọi. Hết hạn, hoặc đổi phiên bản luật, thì sinh lại. Bài `failed` vì mạng chỉ ghi nhớ
    60 giây.
12. Bài `failed` không bao giờ vào cache như bài `ready`.
13. Câu nối thiếu, hoặc vi phạm K11 hay K12, thì tiên quyết chỉ hiện `recall`, và không có lời gọi sinh lại vì câu nối.
14. Câu nối chứa "như bạn đã học" bị bỏ.
15. Tiên quyết `legacy_excerpt` không được gửi để viết câu nối.
16. `next_up` theo cạnh đi ra; ở đồ thị không có câu trích thì không có trường `quote`.
17. Trần người học: lời gọi làm chi trong ngày vượt 0,20 USD bị chặn trước khi gọi mô hình, kèm `daily_limit`. Sang ngày mới, theo đồng hồ giả, thì gọi lại
    được.
18. Trần hệ thống chặn sinh bài giảng và ngân hàng quiz, nhưng không chặn bài và ngân hàng đã có.
19. Quiz phạm vi lộ trình có ≤ 10 câu, ưu tiên khái niệm đã học, trải theo module.
20. Tài liệu vượt 5 module trả `scope_too_large`, 0 lời gọi.
21. Mọi use case phiên, thư viện, tiến độ đều từ chối `owner` khác.
22. Test kiến trúc vẫn xanh.

**Tiền lệ trong repo:**
- test trợ lý, gồm đồng thời và nội dung;
- test bài giảng của SA-26 (chẩn đoán từng lần sinh) và của SA-30;
- test quiz SA-27;
- test kho Pha B (test hợp đồng cho hai bản cài);
- test trang xem thử;
- bộ ghi và phát lại phiên mô hình.

**Lượt có tiền:** dry-run trước, chủ dự án duyệt.
- Một lượt thật nhỏ cho bài giảng `lecture-2`, khoảng 12 khái niệm có tiên quyết trên doc-1, xstk, doc-4. Đo thời gian ở mục 6.1 và tỉ lệ câu nối đạt;
  so lần sinh lại ở nhiệt độ 0 với 1,0.
- Ghi lại phản hồi để phát lại.

---

## Ngoài phạm vi

- **Tài liệu dạng cây cho cả sách:** tóm từng module, cache chung, rồi gộp. Làm ở vé sau nếu còn thời gian (Q4).
- **Dời phiên giữa phạm vi** (Q21) và **tiêu đề phiên do LLM đặt** (Q3).
- **Khoá chat khi đang làm quiz:** chỉ là ẩn khung chat ở trang quiz, do nhóm web làm (Q7).
- **Gợi mở do LLM viết** (Q18). **Chạy lại nhap-mon-ml và naive-bayes bằng chuỗi gộp** (Q17).
- **Mô hình trình độ, mở khoá module, ôn giãn cách:** vẫn ngoài phạm vi. Tiến độ ở đây chỉ là đánh dấu.
- **Đăng nhập, nhiều người dùng thật, cơ sở dữ liệu, giao diện React:** nhóm web.
- **Chính sách lưu trữ dài hạn và xoá tự động.** Trong đồ án không tự xoá; nhóm web ghi chính sách vào báo cáo (Q6).

## Ghi chú thêm

- **Thứ tự vé:**
  - SA-29 (tên module) và SA-30 (K6, cache bài hỏng, TTFT, câu trích, tài liệu) làm trước. SA-30 là điều kiện của mục 6 và 7.
  - Sau đó tới các vé của spec này: nền phạm vi, phiên và tiến độ, rồi trợ lý và thư viện, rồi bài giảng `lecture-2`, rồi trang xem thử.
  - Đánh giá 20–23 chạy sau, trên bản `lecture-2`.
- **Vé 21 (đánh giá bài giảng)** thêm vào rubric hai tiêu chí:
  - câu nối đúng quan hệ và đúng nguồn;
  - phần gợi lại có ích.

  Mốc trích câu vẫn là một cấu hình so sánh.
- **Rủi ro:** `gemini-3.1-flash-lite` bản ổn định tắt sớm nhất ngày 07/05/2027. Khoá cache gồm mô hình, nên bài sẽ sinh lại dần theo lượt bấm.
- **Phụ thuộc phía pha A:** chỉ đồ thị chuỗi gộp có câu trích cạnh. Hiện là doc-1, doc-4, xstk, doc-6; nhap-mon-ml và naive-bayes thì không, nên không có
  câu nối.
- **Một số ý về ChatGPT, Khanmigo, Coursera** trong báo cáo nghiên cứu lấy qua trích đoạn máy tìm kiếm. Muốn đưa vào báo cáo đồ án thì cần một người mở lại
  bằng trình duyệt và chụp màn hình.
