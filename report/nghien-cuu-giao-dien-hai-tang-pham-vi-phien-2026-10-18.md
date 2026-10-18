# Nghiên cứu: giao diện hai tầng và phạm vi phiên chat, tài liệu, quiz (Pha B) — 2026-10-18

Trạng thái: xong — mục 1–9, phụ lục 0 và A. Chưa duyệt; chờ chủ dự án đọc và đợt tra hỏi.

**Người viết:** Claude (phiên nghiên cứu). **Câu hỏi:** đề xuất giao diện hai trang của chủ dự án (trang lộ trình có phiên chat toàn cục; trang học, mỗi
module quản lý phiên, tài liệu, quiz của nó) cần đổi gì ở lõi Pha B, và sản phẩm thật làm thế nào.

## Mục lục

1. Tóm tắt khuyến nghị
2. Bảng so sánh sản phẩm
3. Phạm vi phiên: toàn cục và module
4. Liệt kê phiên, tiêu đề phiên, thư viện nội dung theo phạm vi
5. Tài liệu và quiz phạm vi lớn: kỹ thuật, chi phí
6. Bằng chứng học thuật
7. Đề xuất thay đổi hợp đồng dữ liệu (spec mục 13)
8. Câu hỏi mở cho chủ dự án
9. Nguồn
- Phụ lục 0. Hiện trạng trong mã và số đo doc-1, doc-4
- Phụ lục A. Ghi chép theo sản phẩm

**Cách làm.** Đọc trang trợ giúp và blog chính thức của nhà cung cấp, bài báo gốc (arXiv, PNAS, Scientific Reports qua Europe PMC, SIGCSE), trang
giá và trang mô hình của Google. Mọi nguồn mở ngày 2026-10-18. Ba trang trợ giúp chặn truy cập tự động (HTTP 403 ở `help.openai.com`,
`support.khanacademy.org`; `coursera.support` cần JavaScript); các ý từ ba trang này lấy qua trích đoạn máy tìm kiếm của chính trang đó, và được
ghi rõ tại chỗ. Số đo dự án lấy bằng script cục bộ chỉ đọc artifact doc-1 và doc-4 (mục [Phụ lục 0](#phụ-lục-0-hiện-trạng-trong-mã-đọc-ngày-2026-10-18)).
Không gọi mô hình, không sửa mã, không mở tập giữ lại hay cache của `live.json`.

**Quy ước.** Đoạn bắt đầu bằng *Suy luận:* là ý kiến người viết, chưa có số đo. "Không tìm thấy nguồn chính thức" nghĩa là đã tìm ở trang trợ giúp và
blog của nhà cung cấp mà không thấy.

---

## 1. Tóm tắt khuyến nghị

1. **Đề xuất hai trang khớp mẫu chung của thị trường, với một điểm mới.** Năm trong bảy sản phẩm được xem lấy một "vùng chứa" làm đơn vị phạm vi:
   notebook (NotebookLM, Gemini), project (ChatGPT, Claude, Perplexity). Phiên chat, tệp và chỉ dẫn thuộc vùng chứa. Khanmigo và Coursera thì gắn chat vào
   trang nội dung đang mở. Đề xuất của chủ dự án ghép hai mẫu: lộ trình là vùng chứa cha, module là vùng chứa con, và chat ở trang học biết module
   đang mở. **Không tìm thấy sản phẩm nào có hai cấp vùng chứa lồng nhau, mỗi cấp một danh sách phiên.** Đây là điểm riêng của doc2roadmap, nên
   phải tự quyết vài luật (mục 3, 4).
2. **Phạm vi phiên là nơi lưu và ngữ cảnh ưu tiên, không phải bộ lọc truy hồi.** Giữ quyết định của spec mục 10: trợ lý tìm cả tài liệu. Phiên
   module hỏi sang module khác thì vẫn trả lời; mã gắn thẻ "nội dung ở module N — mở module" (0 USD). Không tự dời phiên, không từ chối (mục 3.2).
3. **Phiên toàn lộ trình cần một thay đổi lõi nhỏ:** cho `current_module_id = null`. Lớp domain đã chịu `None` (`relation` trả `khong_ro`, truy hồi
   bỏ ưu tiên module); chỉ `AssistantUseCase._ask` đang chặn. Ngữ cảnh mồi thay thẻ module bằng thẻ lộ trình (tên module: khoảng 360 token ở doc-1,
   760 token ở doc-4, thêm khoảng 0,0001–0,0002 USD mỗi tin). Khối nhắc nền tắt mặc định ở phiên này, vì không có mốc "đã học" (mục 3.3).
4. **Phải lưu đủ từng lượt hội thoại.** Hiện phiên chỉ giữ 3 lượt cuối để làm ngữ cảnh; câu trả lời chỉ được lưu khi có `client_turn_id`, và không
   có số thứ tự hay thời điểm. Mở lại một phiên cũ trên web là không làm được. Đây là thay đổi lõi bắt buộc (mục 7).
5. **Mọi nội dung sinh ra mang dấu phạm vi.** Lần làm quiz và tài liệu thêm `session_id`, `home_scope`, `created_at`, `title`. Lõi có một use case
   liệt kê "thư viện" theo phạm vi. Trang lộ trình gom được mọi phiên và nội dung của các module bằng bộ lọc (mục 4, 7).
   **Phạm vi phải neo vào `node_id`, không vào `module_id`:** `module_id` là nhãn theo vị trí. Đo trên doc-1 v45 → v53: 33 mã module trùng tên nhưng chỉ
   2 module giữ cùng tập khái niệm, trong khi 202/205 `node_id` còn nguyên. Phiên ghim `module_008` có thể lặng lẽ trỏ sang module khác (câu hỏi mở 8).
6. **Tiêu đề phiên bằng luật, 0 USD:** tên khái niệm liên kết được ở lượt đầu; nếu không có thì câu hỏi đầu, cắt ≤ 60 ký tự. Sản phẩm thương mại không
   công bố cách đặt tiêu đề. Phần mềm mã mở dùng một lời gọi LLM nhỏ; với flash-lite là khoảng 0,00013 USD mỗi phiên. Để chủ dự án quyết có thêm
   tiêu đề LLM chạy nền hay không (mục 4.2).
7. **Tài liệu và quiz phạm vi lớn: dùng cây phân cấp có cache chung, không nhồi cả sách.** Nhồi cả doc-4 vào một lời gọi chỉ tốn khoảng 0,05 USD,
   nhưng đầu ra 3.000 token không đủ cho 91 module, và Google ghi độ chính xác giảm khi phải tìm nhiều mẩu thông tin cùng lúc. Đề xuất: khung do mã
   dựng (0 USD) → bản tóm module dùng chung (doc-4 khoảng 0,08–0,12 USD, một lần cho mỗi phiên bản đồ thị) → một lời gọi gộp theo yêu cầu (khoảng
   0,005–0,017 USD). Quiz cả sách lấy mẫu `n ≤ 10` như hiện nay, khoảng 0,025 USD khi chưa có cache (mục 5).
8. **Bằng chứng học thuật ủng hộ đưa ngữ cảnh bài đang học vào tutor, nhưng không có nghiên cứu so sánh trực tiếp "phiên theo module" với "phiên toàn
   khoá".** Khan Academy (A/B, blog, chưa bình duyệt): thêm tóm tắt lần làm gần đây và kỹ năng tiên quyết chưa vững thì tỉ lệ làm đúng câu kế tăng
   6,1%. Bastani và cộng sự (PNAS 2025, RCT gần 1.000 học sinh): tutor giống ChatGPT làm điểm thi giảm 17%; tutor có lời giải theo bài và luật "không
   đưa đáp án" thì không gây hại. Kestin và cộng sự (Sci. Rep. 2025, RCT 194 sinh viên): tutor theo cấu trúc bài học đạt hiệu ứng 0,73–1,3 SD so với
   lớp học tích cực (mục 6).

---

## 2. Bảng so sánh sản phẩm

Chi tiết và trích dẫn từng ô ở [Phụ lục A](#phụ-lục-a-ghi-chép-theo-sản-phẩm-đọc-ngày-2026-10-18). "—" là không áp dụng; "KTN" là không tìm thấy nguồn
chính thức.

| Sản phẩm | Đơn vị phạm vi | Phiên thuộc phạm vi | Nhiều phiên trong một phạm vi | Phiên đọc được phiên khác cùng phạm vi | Nội dung sinh ra nằm ở đâu | Dời phiên, nội dung | Chat biết "đang ở bài nào" | Ngoài phạm vi |
|---|---|---|---|---|---|---|---|---|
| NotebookLM | notebook | có | KTN (tài liệu chỉ mô tả một luồng chat mỗi notebook) | — | khung Studio của notebook; ghi chú | sao chép notebook mang Studio, không mang chat và ghi chú; dời một output: KTN | không; chỉ biết tập nguồn đang bật; mind map → chat theo nút | chỉ dùng nguồn; không xem notebook khác |
| Gemini notebooks | notebook (đồng bộ NotebookLM) | có | có | có, khi bật Keep Activity | study notebook gom "lessons, conversations, quizzes & tests"; chat thường: trong chat, Canvas | "Add to notebook" | study notebook có tiến độ theo mục tiêu; chat biết bài: KTN | nguồn notebook, có thể kèm web |
| ChatGPT Projects | project | có | có | có (project-only memory) | tệp ở Library/Space; liệt kê theo project: KTN | Move to / Remove from project | chỉ mức project | KTN về chặn; study mode không bật trong project |
| Claude Projects | project | có | có | có, qua bộ nhớ project và tìm chat cũ (chỉ trong project) | KTN | dời vào, ra, giữa project | chỉ mức project | KTN |
| Khanmigo | trang bài, video, bài tập | chat mở trên trang | lịch sử xem ở một chỗ chung (menu khung chat, Learner Home); nhóm theo bài: KTN | log 24 giờ cùng kỹ năng (thí nghiệm) | — | — | **có**: thấy bài tập đang làm | không có ở quiz, unit test |
| Coursera Coach | khoá học, mục đang mở | chat mở trong khoá | KTN | "chat memories" | KTN | — | KTN (chỉ có bài viết lại của bên thứ ba) | không có ở quiz, bài đánh giá |
| Perplexity Projects | project (trước là Spaces) | có | có | có ("Brain") | tệp, artifact trong project | "Convert session to project" | chỉ mức project | KTN |

Ba điểm rút ra:
- **Vùng chứa luôn sở hữu phiên.** Người dùng vào vùng chứa thì thấy phiên của nó. Bốn sản phẩm cho dời phiên giữa các vùng chứa.
- **Nội dung sinh ra được liệt kê theo vùng chứa ở NotebookLM và Gemini study notebook.** ChatGPT và Claude không công bố thư viện theo project.
- **Chỉ Khanmigo và Coursera gắn chat vào trang nội dung cụ thể**, và cả hai không có chat khi người học đang làm bài kiểm tra.

[CHÈN HÌNH 1 – Hai mẫu phạm vi. Bên trái "vùng chứa": một hộp "Project/Notebook" chứa ba ngăn "Phiên chat", "Nguồn/tệp", "Nội dung sinh ra" (ví
dụ NotebookLM, ChatGPT, Claude). Bên phải "gắn trang": một trang bài học có khung chat nhỏ ở góc, mũi tên "biết bài đang mở", và một danh sách lịch sử
chung tách riêng (ví dụ Khanmigo). Ở giữa: đề xuất doc2roadmap, hộp "Lộ trình" chứa ngăn "Phiên toàn lộ trình" và các hộp con "Module 1…N", mỗi hộp con
có ngăn "Phiên", "Quiz", "Tài liệu" và khung chat biết module đang mở.]

---

## 3. Phạm vi phiên: toàn cục và module

### 3.1 Hai mẫu thiết kế, và đề xuất nằm ở đâu

- **Mẫu vùng chứa.** Phạm vi là một tập tài liệu cộng chỉ dẫn và bộ nhớ. Chat không biết vị trí học, chỉ biết tập nguồn
  ([NotebookLM FAQ](https://support.google.com/notebooklm/answer/16269187?hl=en),
  [Claude projects](https://support.claude.com/en/articles/9517075-what-are-projects)).
- **Mẫu gắn trang.** Chat mở trên trang nội dung và đọc nội dung đó: "Khanmigo sees the problem they're working on"
  ([Khan Academy, 05/2026](https://blog.khanacademy.org/how-khan-academy-is-building-a-better-ai-tutor-our-most-recent-learnings/)).
- **Đề xuất doc2roadmap** dùng mẫu vùng chứa ở cả hai trang, cộng mẫu gắn trang ở trang học. Mã hiện tại đã theo mẫu gắn trang: mỗi câu hỏi bắt buộc có
  `current_module_id`, và ngữ cảnh mồi lấy thẻ module đó (spec mục 10, bước 1).

### 3.2 Phiên module hỏi sang module khác

**Sản phẩm làm gì:**
- NotebookLM giới hạn câu trả lời ở nguồn đang bật ("Chat responses… only use data from your sources") và không xem notebook khác
  ([Use chat](https://support.google.com/notebooklm/answer/16179559?hl=en),
  [Create a notebook](https://support.google.com/notebooklm/answer/16206563?hl=en)).
- ChatGPT, Claude, Perplexity giới hạn **bộ nhớ** theo project, không công bố việc chặn kiến thức chung (Phụ lục A.3, A.4, A.7).
- Khanmigo và Coursera chặn theo **loại hoạt động** (không có chat trong quiz, bài kiểm tra), không chặn theo chủ đề (Phụ lục A.5, A.6).
- **Không tìm thấy nguồn chính thức** về sản phẩm nào gợi ý "chuyển sang phạm vi khác" khi câu hỏi lệch phạm vi.

**Khuyến nghị cho doc2roadmap:**
- **Không chặn.** Spec đã chọn "ưu tiên, không chặn theo tiến độ" (user story 35, 36). Phạm vi chỉ đổi hai thứ: thẻ ngữ cảnh mồi, và thứ tự ưu tiên của
  truy hồi (`uu_tien_module`).
- **Thẻ chỉ đường do mã sinh.** Khi khái niệm liên kết được nằm ở module khác module của phiên, `graph_cards` thêm một mục `scope_hints`:
  `{node_id, module_id, module_index, title, relation}`; web hiện nút "mở module N". Hiện mã chỉ gắn "Học kỹ ở module N" khi module đó ở **sau**;
  khuyến nghị gắn cả khi module ở trước (ôn lại), với lời khác ("đã trình bày ở module N").
- **Không tự dời phiên.** Phiên sinh ra ở đâu thì ở đó. Lý do: người học tìm lại phiên theo nơi mình đã hỏi.
- **Giữ khối nhắc nền ở phiên module.** Thí nghiệm của Khan Academy cho thấy thêm "unmastered prerequisite skills with a brief review" tăng tỉ lệ làm
  đúng câu kế 2,7% trên 1,36 triệu luồng
  ([Khan Academy, 05/2026](https://blog.khanacademy.org/how-khan-academy-is-building-a-better-ai-tutor-our-most-recent-learnings/)). Khối
  nhắc nền của spec mục 10 làm đúng việc này, chỉ khác là không có mô hình người học.
- **Khoá chat khi đang làm quiz chưa nộp**, theo cách của Khanmigo và Coursera (Phụ lục A.5, A.6). *Suy luận:* nếu không, trợ lý có thể đọc đề và
  giải hộ; Bastani và cộng sự cho thấy tutor giống ChatGPT, không có luật "không đưa đáp án", làm điểm thi giảm (mục 6).

[CHÈN HÌNH 2 – Luồng câu hỏi chéo module. Người học ở phiên của module 5 hỏi về khái niệm X. Bước 1: mã liên kết X → X thuộc module 12. Bước 2: truy
hồi cả tài liệu, ưu tiên module 5 rồi module trước; đoạn của module 12 mang nhãn "sau". Bước 3: trợ lý trả lời có trích dẫn. Bước 4: mã gắn thẻ "Nội dung
ở module 12 — Mở module 12" (nút). Phiên vẫn nằm trong danh sách của module 5. Nếu người học bấm "tạo quiz về X", lần làm quiz lưu với `home_scope =
module 5`, `module_ids = [module 12]`.]

### 3.3 Phiên toàn lộ trình

**Hiện trạng:** `AssistantUseCase._ask` ném lỗi "Module đang mở không thuộc đồ thị" khi `current_module_id` không có trong đồ thị. Phần còn lại đã chịu
`None`:
- `LearningGraph.relation(module_id, None)` trả `khong_ro`;
- `get_module_info(module_id, None)` chạy được;
- truy hồi Pha B nhận `current_module_id=None` và chỉ ưu tiên module khi có giá trị.

**Khuyến nghị:**
- **Ngữ cảnh mồi:** thay thẻ module bằng **thẻ lộ trình**: số module, tên từng module theo thứ tự, không kèm mô tả. Tên module chiếm khoảng 902 ký tự ở
  doc-1 và 2.844 ký tự ở doc-4, tức khoảng 360 và 760 token (Phụ lục 0). Thêm khoảng 0,0001–0,0002 USD mỗi tin ở giá 0,25 USD/triệu token vào.
- **Truy hồi:** `ca_tai_lieu`. Nhãn vị trí của đoạn đổi từ "trước/sau" sang "module N".
- **Ghi chú module:** "nội dung ở module N" cho mọi khái niệm liên kết, không phân trước sau.
- **Khối nhắc nền:** tắt mặc định. Lý do: không có module đang mở thì không biết khái niệm nền nào "đã học". Câu dẫn của spec vốn dựa vào vị trí ("đã
  học ở module m").
- **Công cụ:** giữ đủ mười công cụ. `path_to` đặc biệt hợp với trang này: "muốn hiểu X cần học gì" là câu hỏi tự nhiên khi đang xem lộ trình.

---

## 4. Liệt kê phiên, tiêu đề phiên, thư viện nội dung theo phạm vi

### 4.1 Trang tổng có gom phiên con không

**Sản phẩm làm gì:**
- **ChatGPT:** ô tìm ở thanh bên lọc theo All, Chats, Images, Documents, Projects, khớp chữ trong tiêu đề và tin nhắn
  ([Finding your chats](https://help.openai.com/en/articles/10056348-finding-your-chats-projects-and-files-in-chatgpt), qua trích đoạn).
- **Claude:** tìm chat cũ tách theo project: "searches are limited to within each specific project"
  ([Chat search and memory](https://support.claude.com/en/articles/11817273-use-claude-s-chat-search-and-memory-to-build-on-previous-context)).
- **Khanmigo:** "Chat history" mở từ menu khung chat hoặc từ Learner Home; không tìm thấy nguồn chính thức nói danh sách được nhóm theo bài (Phụ lục A.5).
- **Open WebUI** (mã mở): nhóm theo thời gian ("Today, Yesterday, Previous 7 Days"), lọc `folder:`, `pinned:`, `archived:`
  ([History & Search](https://docs.openwebui.com/features/chat-conversations/chat-features/history-search/)).

**Khuyến nghị:**
- **Lõi có một hàm liệt kê có lọc:** `list_sessions(owner, doc_id, scope)` với `scope ∈ {roadmap, module:<id>, all}`, sắp theo `updated_at` giảm dần.
  Web quyết cách hiện.
- **Trang lộ trình:** mặc định hiện phiên toàn lộ trình, và một mục "gần đây ở các module" (ví dụ 5 phiên mới nhất, có nhãn module). Bộ lọc "tất cả" gom
  mọi phiên con.
- **Trang module:** chỉ phiên của module đó.
- **Phiên rỗng** (tạo nhưng chưa hỏi) không hiện trong danh sách.

### 4.2 Tiêu đề phiên

**Sản phẩm làm gì:**
- ChatGPT cho đổi tên ở thanh bên; **không tìm thấy nguồn chính thức** về cách sinh tiêu đề tự động của ChatGPT, Claude, Gemini, NotebookLM.
- Perplexity **gợi ý tiêu đề, mô tả và chỉ dẫn** khi tạo project từ một phiên có sẵn
  ([What are Projects?](https://www.perplexity.ai/help-center/en/articles/10352961-what-are-projects)).
- **Open WebUI:** tiêu đề do một "task model" sinh. Tài liệu khuyên mô hình "Small, fast and non-reasoning", vì "A reasoning model spends seconds thinking
  before producing a three-word title, and you pay for those thinking tokens"
  ([Task Models](https://docs.openwebui.com/features/administration/task-models/)). Prompt mặc định đòi tiêu đề "2-4 words", trả JSON, đọc 2 tin
  cuối (`{{MESSAGES:END:2}}`) ([mã nguồn config.py](https://github.com/open-webui/open-webui/blob/main/backend/open_webui/config.py)). Bật mặc định
  (`ENABLE_TITLE_GENERATION = True`) ([Environment config](https://docs.openwebui.com/reference/env-configuration/)).
- **LibreChat:** `titleConvo` mặc định `false`; `titleModel` chọn mô hình đặt tên, có thể là `current_model`; `titleMethod` là `completion` hoặc
  `structured`; prompt mặc định đòi "five words or less"
  ([Custom endpoint](https://www.librechat.ai/docs/configuration/librechat_yaml/object_structure/custom_endpoint)).

**Chi phí tiêu đề LLM với flash-lite** (*ước*): khoảng 400 token vào (prompt, câu hỏi đầu, 500 ký tự đầu câu trả lời) và 20 token ra, tức
0,0001 + 0,00003 ≈ **0,00013 USD mỗi phiên**, 0,13 USD mỗi 1.000 phiên. Tiền không đáng kể; cái giá thật là thêm một lời gọi, một dòng sổ chi, một chỗ có
thể hỏng.

**Khuyến nghị:**
- **Bản đầu dùng luật, 0 USD, có ngay khi lượt 1 xong:**
  - lượt 1 liên kết được khái niệm → `display_name` của khái niệm đầu, thêm "và N khái niệm khác" nếu có;
  - không thì câu hỏi đầu, bỏ khoảng trắng thừa, cắt ≤ 60 ký tự ở ranh giới âm tiết, thêm "…".
- **`title_source` ∈ {`concept`, `question`, `llm`, `user`}.** Người học đổi tên thì `user`, và không gì ghi đè nữa.
- **Tiêu đề LLM là tuỳ chọn** (câu hỏi mở 5): chạy nền sau lượt 1, thinking thấp nhất, tối đa 20 token ra, mục đích sổ chi `session_title`. Chỉ ghi khi
  `title_source` chưa là `user`.

### 4.3 Thư viện nội dung theo phạm vi

**Sản phẩm làm gì:**
- **NotebookLM:** khung Studio của notebook liệt kê mọi output, có chấm xanh cho output chưa mở; mind map là một ghi chú mở lại ở Studio
  ([Create a notebook](https://support.google.com/notebooklm/answer/16206563?hl=en),
  [Mind Maps](https://support.google.com/notebooklm/answer/16212283?hl=en)).
- **Gemini study notebook:** "Your lessons, conversations, quizzes & tests, and uploaded sources can all be found in your study notebook"
  ([Gemini Apps Help](https://support.google.com/gemini/answer/16972047?hl=en&co=GENIE.Platform%3DDesktop)).
- **Perplexity:** project giữ tệp và artifact của các phiên (Phụ lục A.7).

**Khuyến nghị:**
- **Trang module có bốn khu:**
  - **Khái niệm:** danh sách khái niệm, bấm vào là bài giảng. Bài giảng là cache dùng chung, không phải nội dung riêng của người học, nên không vào thư
    viện cá nhân.
  - **Phiên chat** của module.
  - **Quiz:** mọi lần làm có `module_ids` chứa module này, gồm cả quiz từ nút bấm (`module_button`) và quiz do trợ lý tạo (`assistant`).
  - **Tài liệu:** tài liệu có `home_scope` là module này, hoặc có `module_ids` chứa module này.
- **Trang lộ trình có ba khu:** danh sách module, phiên toàn lộ trình, và thư viện toàn lộ trình (nội dung tạo ở phiên lộ trình, cộng bộ lọc "tất cả").
- **Hai luật gán nội dung vào phạm vi:**
  - `home_scope`: phạm vi của phiên đã tạo ra nó (hoặc trang có nút bấm). Quyết định nó "nằm ở đâu".
  - `module_ids`: các module chứa khái niệm của nội dung, do mã suy từ `node_ids` **lúc liệt kê**, theo đồ thị hiện hành. Quyết định nó "liên quan tới
    đâu". Không lưu cứng, vì `module_id` đổi nghĩa giữa các phiên bản đồ thị (câu hỏi mở 8).
  - Trang module hiện cả hai nhóm, đánh dấu nhóm "tạo ở nơi khác".
- **Dời phiên và dời nội dung: không làm ở bản đầu.** Bốn sản phẩm cho dời chat giữa vùng chứa (Phụ lục A.2–A.4, A.7), nhưng ở doc2roadmap, `module_ids`
  đã cho nội dung hiện ở đúng module mà không cần dời. Giữ `scope` của phiên là trường đổi được, để web thêm sau nếu cần.

---

## 5. Tài liệu và quiz phạm vi lớn

### 5.1 Kỹ thuật

| Kỹ thuật | Cách làm | Nguồn | Hợp doc2roadmap? |
|---|---|---|---|
| Nhồi ngữ cảnh dài | đưa cả sách vào một lời gọi; flash-lite nhận 1.048.576 token vào, 65.536 token ra | [model card](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite) | rẻ, nhưng Google ghi: khi tìm nhiều mẩu thông tin, "the model does not perform with the same accuracy" ([Long context](https://ai.google.dev/gemini-api/docs/long-context)); 671 nhãn nguồn làm hậu kiểm trích dẫn khó |
| Truy hồi phần liên quan | chỉ nạp đoạn gần câu hỏi | NotebookLM: "retrieves the most relevant information based on your question" ([FAQ](https://support.google.com/notebooklm/answer/16269187?hl=en)); Claude bật RAG khi kiến thức gần chạm trần ([RAG for projects](https://support.claude.com/en/articles/11473015-retrieval-augmented-generation-rag-for-projects)) | đã có (`make_document` truy hồi theo yêu cầu); không đủ cho câu hỏi "toàn cục" kiểu "đề cương cả sách" |
| Map-reduce | mỗi phần một lời gọi, rồi một lời gọi gộp | GraphRAG: tóm tắt cộng đồng → câu trả lời từng phần → gộp; tốt hơn RAG thường ở câu hỏi toàn cục trên kho khoảng 1 triệu token ([Edge et al. 2024](https://arxiv.org/abs/2404.16130)) | hợp: module là đơn vị chia có sẵn |
| Hợp nhất phân cấp, cập nhật dần | gộp tóm tắt theo tầng, hoặc sửa một bản tóm chạy dần | BooookScore: cập nhật dần ít mạch lạc hơn nhưng chi tiết hơn hợp nhất phân cấp ([Chang et al., ICLR 2024](https://arxiv.org/abs/2310.00785)) | hợp nhất phân cấp hợp hơn, vì chạy song song được |
| Cây tóm tắt để truy hồi | tóm tắt theo cụm, nhiều tầng, truy hồi trên cây | RAPTOR ([Sarthi et al., ICLR 2024](https://arxiv.org/abs/2401.18059)) | hợp: cây khái niệm → module → sách có sẵn từ đồ thị |
| Khung do mã | phần cấu trúc (tên module, khái niệm, định nghĩa, trang) do mã dựng | nguyên tắc 1 của spec Pha B | hợp nhất, 0 USD |
| Lấy mẫu khái niệm | quiz không phủ mọi khái niệm, lấy mẫu theo tầng | `make_quiz` đã có `n ≤ 10` | hợp |
| Giới hạn phạm vi | từ chối hay đề nghị thu hẹp khi phạm vi quá lớn | `_cap_context` hiện cắt dần khái niệm cuối | là đường lùi |

### 5.2 Ước chi phí với flash-lite

**Giá dùng:** `gemini-3.1-flash-lite`, bậc trả tiền Standard, 0,25 USD/triệu token vào (chữ), 1,50 USD/triệu token ra (gồm thinking). Batch và Flex bằng nửa
giá: 0,125 và 0,75 ([trang giá, cập nhật 2026-10-16](https://ai.google.dev/gemini-api/docs/pricing)). Giá dùng trong mã (`0.25`/`1.5`) vẫn đúng.

**Embedding:** trang giá hiện hành **không còn liệt kê `gemini-embedding-001`**; chỉ có `gemini-embedding-2` ở 0,20 USD/triệu token chữ (Batch 0,10).
Giá 0,15 USD/triệu token của `gemini-embedding-001` lấy từ bài ra mắt ngày 14/07/2025
([Google Developers Blog](https://developers.googleblog.com/gemini-embedding-available-gemini-api/)). Trang ngừng hỗ trợ ghi `gemini-embedding-001` tắt
sớm nhất 14/05/2028, thay bằng `gemini-embedding-2`
([Deprecations, cập nhật 2026-10-12](https://ai.google.dev/gemini-api/docs/deprecations)). Kiểm thử 2026-10-18 mục 3.8 ghi chỉ mục khái niệm đang tính
embedding bằng giá vào của flash-lite (0,25); giá đúng theo nguồn còn thấy là 0,15, chênh nhỏ. Cùng trang ghi `gemini-3.1-flash-lite` bản ổn định tắt
sớm nhất **07/05/2027**, thay bằng `gemini-3.5-flash-lite`.

**Giả định:** token đếm bằng tokenizer Gemma của dự án (xấp xỉ token Gemini); cộng 20% cho JSON, nhãn nguồn, và 400 token chỉ dẫn mỗi lời gọi. Ký tự đổi
ra token theo tỉ lệ đo được: 2,52 ký tự/token ở doc-1, 3,73 ở doc-4. **Mọi số là ước; phải dry-run và đo.**

| Cách làm cho một "đề cương ôn cả sách" | doc-1 (33 module) | doc-4 (91 module) | Ghi chú |
|---|---:|---:|---|
| S1. Nhồi mọi chunk, 1 lời gọi, ra 3.000 token | 52,9 nghìn token vào; **0,018 USD** | 182,3 nghìn; **0,050 USD** | 3.000 token ra chia cho 91 module là khoảng 33 token mỗi module |
| S2. Chỉ chunk dạy, 1 lời gọi | 26,2 nghìn; 0,011 USD | 101,8 nghìn; 0,030 USD | như S1, mất phần ví dụ, bài tập |
| S3. Khung mã (tên module, mô tả, tên khái niệm, câu neo) + 1 lời gọi | 20,4 nghìn; 0,010 USD | 34,1 nghìn; 0,013 USD | khung đã là một đề cương có trang; LLM chỉ viết lời dẫn |
| S4. Map-reduce, 300 token ra mỗi module | 0,033 USD | 0,092 USD | tài liệu dài khoảng 11 nghìn và 28 nghìn token |
| S4'. Map-reduce, 600 token ra mỗi module | 0,051 USD | 0,141 USD | tài liệu dài khoảng 21 nghìn và 56 nghìn token |
| S5. S4 với bản tóm module **cache dùng chung**; mỗi yêu cầu chỉ trả bước gộp | 0,005–0,008 USD mỗi yêu cầu | 0,010–0,017 USD mỗi yêu cầu | bước map trả một lần cho mỗi phiên bản đồ thị (0,03–0,04 và 0,08–0,12 USD) |

| Quiz phạm vi lớn (0,0025 USD mỗi khái niệm, spec mục 9) | doc-1 | doc-4 |
|---|---:|---:|
| Mọi khái niệm, chưa cache (cận trên) | 0,51 USD | 1,24 USD |
| Một khái niệm mỗi module | 0,08 USD | 0,23 USD |
| `n = 10`, lấy mẫu theo tầng module | 0,025 USD | 0,025 USD |
| Ngân hàng đã cache | 0 USD | 0 USD |

**Đọc bảng:**
- Tiền không phải ràng buộc chính. Ngay S1 cho doc-4 cũng chỉ 0,05 USD. Ràng buộc là **độ dài đầu ra**, **độ tin của trích dẫn**, và **giây chờ**.
- Trần hiện hành 0,01 USD và 8.000 token ngữ cảnh mỗi tài liệu chỉ đủ cho khoảng một module (token chunk dạy mỗi module: trung vị 591–912, p90
  1.206–1.450, tối đa 2.237; Phụ lục 0), cộng truy hồi.
- *Suy luận:* bước map của S4 chạy song song; ở song song 16, 91 lời gọi là khoảng 6 đợt. Giây chờ phải đo.

[CHÈN HÌNH 3 – Cây phân cấp cho phạm vi lớn. Tầng dưới: các khái niệm, mỗi khái niệm có bài giảng (cache chung, đã có). Tầng giữa: mỗi module một "bản
tóm module" (cache chung theo băm ngữ cảnh, sinh khi lần đầu cần, song song). Tầng trên: "yêu cầu của người học" (ví dụ "đề cương ôn chương 2–4") đi qua
một lời gọi gộp, đọc các bản tóm module trong phạm vi, ra tài liệu riêng của người học. Bên cạnh: "khung do mã" (tên module, khái niệm, định nghĩa, trang)
nối thẳng vào tài liệu cuối, không qua LLM. Ghi chi phí ở mỗi tầng: 0 USD / một lần mỗi phiên bản đồ thị / mỗi yêu cầu.]

### 5.3 Khuyến nghị trần

- **Phạm vi ≤ 1 module, hoặc ≤ 8 khái niệm:** giữ đường hiện tại; trần 0,01 USD, 8.000 token ngữ cảnh.
- **Nhiều module hoặc cả sách:**
  - dựng khung bằng mã trước (0 USD); nếu yêu cầu chỉ cần khung (ví dụ "liệt kê khái niệm và định nghĩa chương 2"), trả khung, không gọi mô hình;
  - còn lại theo S5. Bản tóm module là nội dung mới, phải có luật kiểm trích dẫn như bài giảng, và cache theo băm ngữ cảnh như ADR 0011;
  - trần mỗi yêu cầu 0,03 USD (bước gộp, sau khi có cache); trần chi một lần cho bản tóm module 0,15 USD mỗi cuốn mỗi phiên bản đồ thị, qua dry-run;
  - đầu ra cuối vẫn ≤ 3.000 token; phần dài là khung do mã dựng nối vào, không do mô hình viết.
- **Quiz phạm vi lớn:** giữ `n ≤ 10`; mã lấy mẫu theo tầng: mỗi module trong phạm vi tối đa 1 khái niệm, ưu tiên khái niệm đã có ngân hàng (0 USD).
- **Mỗi người học mỗi ngày:** chưa có trần. *Suy luận:* trang lộ trình làm việc tạo tài liệu lớn dễ hơn; nên có trần theo người học (câu hỏi mở 9).

---

## 6. Bằng chứng học thuật

| Nghiên cứu | Thiết kế | Kết quả | Liên quan tới phạm vi |
|---|---|---|---|
| Bastani và cộng sự, *PNAS* 122(26), 2025 ([Europe PMC](https://europepmc.org/article/MED/40560616), doi 10.1073/pnas.2422633122) | RCT, gần 1.000 học sinh trung học, Thổ Nhĩ Kỳ; ba nhánh: GPT Base (giống ChatGPT, prompt có bài đang làm), GPT Tutor (thêm lời giải và lỗi thường gặp do giáo viên soạn, luật "không đưa đáp án"), đối chứng | Luyện tập: +48% (Base), +127% (Tutor). Thi không có AI: Base **−17%** so với đối chứng; Tutor không khác đối chứng | Cả hai nhánh đều biết bài đang làm. Khác biệt nằm ở nội dung riêng của bài cộng luật sư phạm. Ngữ cảnh bài học thôi chưa đủ |
| Kestin và cộng sự, *Scientific Reports* 15:17458, 2025 ([Europe PMC](https://europepmc.org/article/MED/40537565), doi 10.1038/s41598-025-97652-6) | RCT chéo, 194 sinh viên vật lý Harvard; tutor AI theo từng bài, prompt có lời giải từng bước, so với lớp học tích cực | Học nhiều hơn trong ít thời gian hơn; hiệu ứng 0,63 SD (hồi quy tuyến tính), 0,73–1,3 SD (hồi quy phân vị) | Tác giả thấy "a system prompt could not reliably provide enough structure", nên nền tảng dẫn người học đi tuần tự từng phần của bài. Gắn chặt bài học là chủ ý thiết kế |
| Khan Academy, blog 05/2026 ([link](https://blog.khanacademy.org/how-khan-academy-is-building-a-better-ai-tutor-our-most-recent-learnings/)) | khoảng 20 thử nghiệm A/B, hơn 15 triệu luồng | Thêm tóm tắt lần làm gần đây: +3,4% đúng câu kế; thêm tiên quyết chưa vững: +2,7%; cả hai: +6,1%; log chữ và các luồng 24 giờ cùng kỹ năng: +5,09% "cognitive engagement" | Bằng chứng gần nhất cho "ngữ cảnh của bài đang học + tiên quyết". Blog nhà sản xuất, chưa bình duyệt |
| Liu và cộng sự, SIGCSE 2024 ([PDF](https://cs.harvard.edu/malan/publications/V1fp0567-liu.pdf), doi 10.1145/3626252.3630938) | CS50 Duck: công cụ riêng của khoá, RAG trên phụ đề bài giảng, khoá hạn chế ChatGPT | 22/25 (88%) câu trả lời nội dung đúng (mùa hè 2023, một trợ giảng chấm); khảo sát tích cực | Không có nhóm so sánh với chat chung; số mẫu nhỏ |
| Taneja và cộng sự, AIED 2024 ([arXiv 2405.11070](https://arxiv.org/abs/2405.11070)) | Jill Watson (RAG trên giáo trình) so với OpenAI Assistants trên cùng tài liệu, 150 câu hỏi, κ = 0,76 | Đạt 76,7% so với 31,3%; câu có hại 5,7% so với 16,5% | So sánh hai cách gắn tài liệu, không so với chat chung |
| Schmucker và cộng sự, 2024 ([arXiv 2404.17460](https://arxiv.org/abs/2404.17460)) | Tutor sinh từ bài học (Ruffle&Riley) so với chatbot hỏi đáp và đọc bài, N = 200 | Người dùng thấy hữu ích hơn; điểm sau học không khác đáng kể so với đọc bài | Tutor bám bài không tự động học tốt hơn |
| Lehmann, Cornelius, Sting, 2024–2025 ([arXiv 2409.09047](https://arxiv.org/abs/2409.09047)) | Hai thí nghiệm phòng lab có đăng ký trước, cộng dữ liệu thực địa | Dùng LLM để thay việc làm bài thì hiểu kém đi; dùng để hỏi giải thích thì hiểu hơn | Cách dùng quan trọng hơn có dùng hay không |

**Kết luận cho doc2roadmap:**
- **Không tìm thấy** nghiên cứu nào so sánh trực tiếp chat gắn một module với chat cho cả khoá trong cùng một hệ.
- Bằng chứng gián tiếp ủng hộ ba điều spec đã có: phiên module nạp ngữ cảnh module; nhắc tiên quyết; trả lời có nguồn. Bastani thêm một điều: tutor
  giống ChatGPT, không có luật "không đưa đáp án", gây hại cho điểm thi. Nên khoá chat khi đang làm quiz (mục 3.2).
- Phiên toàn lộ trình không có bằng chứng ủng hộ hay phản đối. *Suy luận:* nó hợp cho câu hỏi định hướng ("học gì trước", "đề cương ôn"), ít hợp cho học
  một khái niệm cụ thể. Giao diện có thể gợi ý "mở module N để học" (mục 3.2).

---

## 7. Đề xuất thay đổi hợp đồng dữ liệu (spec mục 13)

### 7.1 Đối tượng mới

**Phiên** `session-1`:

```json
{"contract_version": "session-1", "session_id": "s_…", "owner": "…", "doc_id": "…",
 "scope": {"kind": "roadmap | module", "module_id": "module_008 | null", "node_ids": ["…"]},
 "graph_version_at_create": "…", "scope_stale": false,
 "title": "Hạng của ma trận", "title_source": "concept | question | llm | user",
 "created_at": "…", "updated_at": "…", "turn_count": 4, "last_question_preview": "…",
 "reminders_enabled": true, "archived": false,
 "artifact_refs": [{"kind": "quiz_attempt | document | lecture", "id": "…", "created_at": "…"}]}
```

- `session_id` do lõi sinh khi tạo phiên. Hiện web tự đặt `session_id`; khoá kho là băm của `[owner, doc_id, session_id]`.
- `scope.node_ids`: tập khái niệm của module lúc tạo phiên. `module_id` là nhãn theo vị trí và đổi nghĩa giữa các phiên bản đồ thị (câu hỏi mở 8);
  `node_id` thì gần như ổn định. Lõi dùng tập này để ánh xạ phạm vi sang đồ thị mới.
- `scope_stale`: không ánh xạ được phạm vi sang đồ thị hiện hành (câu hỏi mở 8).
- `artifact_refs` ghi ở phiên, để không phải quét mọi câu trả lời.

**Lượt** `turn-1`, một bản ghi mỗi lượt:

```json
{"contract_version": "turn-1", "session_id": "…", "turn_index": 3, "client_turn_id": "…", "created_at": "…",
 "current_module_id": "… | null", "question": "…", "answer": {"…": "đối tượng answer-1 đầy đủ"}}
```

Trạng thái ngữ cảnh 3 lượt, 1.000 token giữ nguyên; bản ghi lượt chỉ để hiện lại phiên.

**Mục thư viện** `library-1` (kết quả liệt kê, không phải bản ghi mới):

```json
{"contract_version": "library-1", "kind": "quiz_attempt | document", "id": "…", "title": "…",
 "created_at": "…", "origin": "assistant | module_button | button", "session_id": "… | null",
 "home_scope": {"kind": "roadmap | module", "module_id": "… | null"},
 "module_ids": ["…"], "status": "…", "summary": {"correct_count": 5, "question_count": 7}}
```

### 7.2 Đối tượng hiện có, trường thêm hoặc đổi

| Đối tượng | Thay đổi | Lý do |
|---|---|---|
| yêu cầu `answer-1` | `current_module_id` thành `string \| null`; phiên module thì lõi lấy từ `scope.module_id`, giá trị gửi lên phải khớp hoặc bỏ trống | phiên toàn lộ trình (mục 3.3) |
| `answer-1` final | thêm `session_scope`, `turn_index`; `graph_cards` thêm `scope_hints` | thẻ chỉ đường (mục 3.2) |
| `quiz-1` lần làm | thêm `session_id` (null nếu từ nút bấm), `home_scope`, `title`; `module_ids` **suy lúc liệt kê** từ `concept_ids` theo đồ thị hiện hành, không lưu cứng | lần làm từ danh sách khái niệm hiện có `module_id = null`, nên không liệt kê theo module được; `module_id` đổi nghĩa giữa phiên bản đồ thị |
| `quiz-1` lịch sử | `history(owner, doc_id, scope=None)` lọc theo `module_ids` | trang module |
| `document-1` | thêm `session_id`, `origin`, `home_scope`, `created_at`; `graph_version` có ở mọi `status`; `module_ids` suy lúc liệt kê từ `scope.node_ids` | bản hiện tại thiếu `created_at`; nhánh "vượt trần dự toán" (`estimated_cost_over_limit`) thiếu `graph_version` |
| `document-1` lịch sử | hàm liệt kê mới, theo `owner`, `doc_id`, phạm vi | chưa có hàm liệt kê tài liệu |
| công cụ `make_quiz`, `make_document` | nhận thêm `session_id` và `home_scope` từ phiên (mã truyền, mô hình không thấy) | gắn nội dung vào phiên |

### 7.3 Use case lõi mới

- `create_session(owner, doc_id, scope)` → `session-1`.
- `list_sessions(owner, doc_id, scope ∈ {roadmap, module:<id>, all}, include_archived=False)`.
- `get_session(owner, session_id)` kèm `list_turns(owner, session_id)`.
- `rename_session(owner, session_id, title)`; `archive_session(owner, session_id)`.
- `list_library(owner, doc_id, scope, kinds)` → danh sách `library-1`.
- Luật tiêu đề (mục 4.2) chạy trong `ask` ở lượt 1.

Port lưu trữ hiện có (`get_record`, `put_record`, `list_records(kind, owner)`) đủ cho bản JSON tệp. Bản Postgres của nhóm web cần chỉ mục theo
`(owner, doc_id, scope)` và `(session_id, turn_index)`.

[CHÈN HÌNH 4 – Sơ đồ quan hệ dữ liệu. Hộp "Tài liệu (doc_id)" 1–n "Phiên (session_id, scope)"; "Phiên" 1–n "Lượt (turn_index)"; "Phiên" 1–n "Nội dung sinh ra"
(hai loại: "Lần làm quiz", "Tài liệu"), cạnh ghi `session_id`; "Nội dung sinh ra" n–n "Module" qua `module_ids`, và n–1 "Phạm vi" qua `home_scope`. Tách riêng
hộp "Cache chung" chứa "Bài giảng" và "Ngân hàng quiz", nối nét đứt tới "Khái niệm", ghi chú "không thuộc người học".]

### 7.4 Phân việc: lõi và nhóm web

| Việc | Lõi (use case, CLI, test) | Nhóm web |
|---|---|---|
| Phiên có phạm vi, sinh `session_id` | ✔ | gọi, lưu vào trang |
| `current_module_id = null` cho phiên lộ trình, thẻ lộ trình, tắt nhắc nền | ✔ | — |
| Lưu từng lượt, đọc lại phiên | ✔ (port, bản JSON tệp) | bản Postgres, phân trang |
| `scope_hints` trong `graph_cards` | ✔ | nút "mở module N" |
| Gắn `session_id`, `home_scope`, `module_ids` vào quiz và tài liệu | ✔ | — |
| `list_sessions`, `list_library` có lọc | ✔ | bố cục, tab, tìm kiếm, chấm "chưa mở" |
| Tiêu đề luật | ✔ | ô đổi tên |
| Tiêu đề LLM (nếu duyệt) | ✔ (ghi sổ chi) | — |
| Khoá chat khi đang làm quiz | — (lõi chỉ cho biết lần làm chưa nộp) | ✔ |
| Phạm vi lớn: khung mã, bản tóm module, bước gộp | ✔ (spec riêng) | nút "tạo đề cương" nếu muốn |
| Lưu trữ, xoá, xuất | ✔ hàm `archive` | chính sách giữ, xoá vĩnh viễn |

---

## 8. Câu hỏi mở cho chủ dự án

1. **Phiên module có trả lời câu hỏi về module khác không?** Khuyến nghị: có, kèm thẻ "nội dung ở module N — mở module" do mã gắn; không chặn, không tự dời
   phiên (mục 3.2).
2. **Trang lộ trình có gom mọi phiên của các module không?** Khuyến nghị: có, qua bộ lọc "tất cả"; mặc định hiện phiên toàn lộ trình cộng 5 phiên gần nhất ở
   các module, có nhãn module (mục 4.1).
3. **Quiz hay tài liệu tạo trong phiên module A nhưng nội dung thuộc module B thì nằm ở đâu?** Khuyến nghị: nằm ở A (`home_scope`), và hiện thêm ở B nhờ
   `module_ids`, đánh dấu "tạo ở nơi khác" (mục 4.3).
4. **Có cho dời phiên giữa phạm vi không?** Khuyến nghị: không ở bản đầu. Giữ `scope` đổi được để thêm sau (mục 4.3).
5. **Tiêu đề phiên do luật hay LLM?** Khuyến nghị: luật, 0 USD. Tiêu đề LLM chạy nền chỉ khi chủ dự án muốn; khoảng 0,00013 USD mỗi phiên (mục 4.2).
6. **Phiên toàn lộ trình có khối nhắc khái niệm nền không?** Khuyến nghị: tắt mặc định, vì không có mốc "đã học" (mục 3.3).
7. **Có cho tài liệu phạm vi cả sách không, và theo cách nào?** Khuyến nghị: có, theo cây có cache chung: khung mã → bản tóm module → bước gộp. Trần 0,03 USD
   mỗi yêu cầu; trần một lần 0,15 USD mỗi cuốn mỗi phiên bản đồ thị cho bản tóm module. Việc này cần spec riêng, vì bản tóm module là loại nội dung mới,
   phải có luật kiểm và chấm (mục 5.3).
8. **Đồ thị lên phiên bản mới thì phạm vi module của phiên cũ trỏ vào đâu?** Số đo: `module_id` là nhãn theo vị trí, không phải danh tính. doc-1 v45 → v53
   (chuỗi v3 → chuỗi gộp): 33 mã `module_…` trùng tên, nhưng chỉ 2/33 module có cùng tập khái niệm, Jaccard trung bình 0,26. Trong khi đó 202/205
   `node_id` của v53 có ở v45. v52 → v53 và doc-4 v22 → v23 thì giữ nguyên 100%. Nghĩa là phiên ghim `module_008` có thể **lặng lẽ trỏ sang module khác**,
   không chỉ là "mất module". Khuyến nghị: phiên lưu `node_ids` của module lúc tạo; khi phiên bản đồ thị đổi, ánh xạ sang module có Jaccard cao nhất trên
   tập khái niệm; dưới ngưỡng (ví dụ 0,5) thì gắn `scope_stale = true`, hỏi tiếp như phiên toàn lộ trình, hiện ghi chú "module này đã đổi". Nội dung sinh ra
   lưu `node_ids` và suy `module_ids` lúc liệt kê, theo đồ thị hiện hành.
9. **Có trần chi theo người học mỗi ngày không?** Khuyến nghị: có, ví dụ 0,20 USD/người/ngày cho mọi lời gọi Pha B có tiền, đếm từ sổ chi; hết trần thì vẫn
   dùng được phần 0 USD (khung mã, bài giảng và ngân hàng đã cache). Spec hiện chỉ có trần mỗi tin và mỗi chức năng.
10. **Lưu lịch sử hội thoại bao lâu?** Khanmigo ghi giữ tới 365 ngày sau khi hội thoại kết thúc
    ([Deletion Practices](https://support.khanacademy.org/hc/en-us/articles/29415446635021-What-are-Khan-Academy-s-Deletion-Practices), qua trích đoạn). Khuyến nghị: trong đồ án không
    xoá tự động; người học có nút xoá; nhóm web ghi chính sách trong báo cáo.
11. **Có khoá chat khi người học đang làm quiz chưa nộp không?** Khuyến nghị: có, theo cách của Khanmigo và Coursera (mục 3.2). Lõi đã biết lần làm nào chưa nộp.
12. **Có nút tạo tài liệu hay quiz ngoài chat, như khung Studio của NotebookLM, không?** Khuyến nghị: bản đầu chỉ có nút "làm quiz" của module (đã có) và công cụ
    trong chat. Nếu thêm nút, web gọi thẳng `make_document` với `origin = button`; ngoài trường `origin` ở mục 7.2, lõi không phải đổi gì thêm.
13. **Có cần kiểm lại trang ChatGPT, Khanmigo, Coursera bằng trình duyệt không?** Ba trang chặn truy cập tự động; các ý về chúng lấy qua trích đoạn. Khuyến nghị:
    nếu đưa các ý này vào báo cáo đồ án, một người mở lại bằng trình duyệt và chụp màn hình làm bằng chứng.
14. **Lộ trình đổi mô hình:** `gemini-3.1-flash-lite` bản ổn định có ngày tắt sớm nhất 07/05/2027 (mục 5.2). Không ảnh hưởng đồ án, nhưng nên ghi vào rủi ro.

---

## 9. Nguồn

Mọi nguồn truy cập ngày **2026-10-18**. Tính năng sản phẩm có thể đã đổi sau ngày này.

**NotebookLM (Gemini Notebook):**
- FAQ: https://support.google.com/notebooklm/answer/16269187?hl=en
- Use chat: https://support.google.com/notebooklm/answer/16179559?hl=en
- Create a notebook: https://support.google.com/notebooklm/answer/16206563?hl=en
- Notes: https://support.google.com/notebooklm/answer/16262519?hl=en
- Flashcards or Quizzes: https://support.google.com/notebooklm/answer/16958963?hl=en
- Mind Maps: https://support.google.com/notebooklm/answer/16212283?hl=en
- Audio Overview: https://support.google.com/notebooklm/answer/16212820?hl=en
- Plans and limits: https://support.google.com/notebooklm/answer/16213268?hl=en
- Notebooks in Gemini Apps: https://support.google.com/notebooklm/answer/17003757?hl=en
- Blog 29/10/2025, chat upgrade: https://blog.google/innovation-and-ai/models-and-research/google-labs/notebooklm-custom-personas-engine-upgrade/
- Blog 15/09/2026, study tools: https://blog.google/innovation-and-ai/products/gemini-notebook/new-study-tools-september-2026/

**Gemini app:**
- Notebooks in Gemini Apps (Help): https://support.google.com/gemini/answer/16972047?hl=en&co=GENIE.Platform%3DDesktop
- Quizzes, flashcards (Help): https://support.google.com/gemini/answer/16275879?hl=en
- Blog 08/04/2026, notebooks: https://blog.google/innovation-and-ai/products/gemini-app/notebooks-gemini-notebooklm/
- Blog 25/06/2026, study notebooks: https://blog.google/innovation-and-ai/products/gemini-app/gemini-study-notebooks/
- Blog 06/08/2025, Guided Learning: https://blog.google/products-and-platforms/products/education/guided-learning/

**ChatGPT** (trang trả 403; đọc qua trích đoạn máy tìm kiếm):
- Projects in ChatGPT: https://help.openai.com/en/articles/10169521-projects-in-chatgpt
- Finding your chats, projects, and files: https://help.openai.com/en/articles/10056348-finding-your-chats-projects-and-files-in-chatgpt
- Using study mode: https://help.openai.com/en/articles/11780217-using-study-mode-in-chatgpt
- Getting started with Space: https://help.openai.com/en/articles/20001549

**Claude:**
- What are projects?: https://support.claude.com/en/articles/9517075-what-are-projects
- Create and manage projects: https://support.claude.com/en/articles/9519177-how-can-i-create-and-manage-projects
- Chat search and memory: https://support.claude.com/en/articles/11817273-use-claude-s-chat-search-and-memory-to-build-on-previous-context
- RAG for projects: https://support.claude.com/en/articles/11473015-retrieval-augmented-generation-rag-for-projects

**Khan Academy** (trang trợ giúp trả 403; đọc qua trích đoạn):
- Where can I access Khanmigo: https://support.khanacademy.org/hc/en-us/articles/13982530363533-Where-can-I-access-Khanmigo-while-working-on-Khan-Academy
- View my Khanmigo chat history: https://support.khanacademy.org/hc/en-us/articles/13982846291725-How-do-I-view-my-Khanmigo-chat-history
- Deletion practices: https://support.khanacademy.org/hc/en-us/articles/29415446635021-What-are-Khan-Academy-s-Deletion-Practices
- Blog 05/2026, building a better AI tutor: https://blog.khanacademy.org/how-khan-academy-is-building-a-better-ai-tutor-our-most-recent-learnings/

**Coursera** (trang trợ giúp cần JavaScript; đọc qua trích đoạn):
- Advance your learning with Coursera AI: https://www.coursera.support/s/article/learner-000002224-Advance-your-learning-with-Coursera-Coach
- Blog 05/06/2024: https://blog.coursera.org/coursera-coach-leveraging-genai-to-empower-learners/
- Blog 23/06/2025: https://blog.coursera.org/coach-wins-newsweek-ai-impact-award/

**Perplexity:**
- What are Projects?: https://www.perplexity.ai/help-center/en/articles/10352961-what-are-projects

**Phần mềm mã mở (tiêu đề phiên):**
- Open WebUI Task Models: https://docs.openwebui.com/features/administration/task-models/
- Open WebUI History & Search: https://docs.openwebui.com/features/chat-conversations/chat-features/history-search/
- Open WebUI env config: https://docs.openwebui.com/reference/env-configuration/
- Open WebUI `config.py` (prompt tiêu đề mặc định): https://github.com/open-webui/open-webui/blob/main/backend/open_webui/config.py
- LibreChat custom endpoint: https://www.librechat.ai/docs/configuration/librechat_yaml/object_structure/custom_endpoint

**Google Gemini API:**
- Pricing (cập nhật 2026-10-16): https://ai.google.dev/gemini-api/docs/pricing
- Deprecations (cập nhật 2026-10-12): https://ai.google.dev/gemini-api/docs/deprecations
- Model card gemini-3.1-flash-lite: https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite
- Long context (cập nhật 2026-10-15): https://ai.google.dev/gemini-api/docs/long-context
- Gemini Embedding GA, 14/07/2025: https://developers.googleblog.com/gemini-embedding-available-gemini-api/

**Bài báo:**
- Bastani H. và cộng sự (2025). Generative AI without guardrails can harm learning: Evidence from high school mathematics. *PNAS* 122(26):e2422633122.
  Đọc toàn văn qua Europe PMC (PMC12232635).
- Kestin G. và cộng sự (2025). AI tutoring outperforms in-class active learning: an RCT introducing a novel research-based design in an authentic
  educational setting. *Scientific Reports* 15:17458. Đọc toàn văn qua Europe PMC (PMC12179260).
- Liu R. và cộng sự (2024). Teaching CS50 with AI. *SIGCSE 2024*, 750–756. Đọc toàn văn PDF của tác giả.
- Taneja K. và cộng sự (2024). Jill Watson: A Virtual Teaching Assistant powered by ChatGPT. arXiv 2405.11070 (AIED 2024). Đọc phần đánh giá.
- Schmucker R. và cộng sự (2024). Ruffle&Riley. arXiv 2404.17460. Chỉ đọc tóm tắt.
- Lehmann M., Cornelius P. B., Sting F. J. (2024–2025). AI Meets the Classroom: When Do Large Language Models Harm Learning? arXiv 2409.09047. Chỉ đọc tóm tắt.
- Edge D. và cộng sự (2024). From Local to Global: A Graph RAG Approach to Query-Focused Summarization. arXiv 2404.16130. Chỉ đọc tóm tắt.
- Chang Y. và cộng sự (2024). BooookScore. ICLR 2024, arXiv 2310.00785. Chỉ đọc tóm tắt.
- Sarthi P. và cộng sự (2024). RAPTOR. ICLR 2024, arXiv 2401.18059. Chỉ đọc tóm tắt.

**Mã và tài liệu dự án:** `doc/pha-b-spec.md`; `src/doc2roadmap/application/phase_b/assistant.py`, `documents.py`, `quiz.py`;
`src/doc2roadmap/composition_phase_b.py`; `src/doc2roadmap/domain/learning_graph.py`; `report/kiem-thu-pha-b-2026-10-18.md`; artifact
`graph/doc-1/v53`, `chunks/doc-1/v7`, `graph/doc-4/v23`, `chunks/doc-4/v6`.

---

## Phụ lục 0. Hiện trạng trong mã (đọc ngày 2026-10-18)

- **Phiên chat** khoá theo `[owner, doc_id, session_id]` (`assistant.py`, `_session_key`). Bản ghi phiên chỉ có `turns` (tối đa 3 lượt, 1.000
  token), `reminded_node_ids`, `linked_node_ids`, `reminders_enabled`, `current_module_id` của lượt cuối. Không có tiêu đề, thời điểm tạo, phạm vi,
  hay danh sách nội dung đã tạo.
- **Mỗi câu hỏi bắt buộc có `current_module_id` thuộc đồ thị** (`_ask`: "Module đang mở không thuộc đồ thị"). Chưa có đường cho câu hỏi "không ở
  module nào".
- **Tài liệu** lưu ở bản ghi `documents`, có `owner`, `doc_id`, `scope.node_ids`, `scope.module_ids`. Không có `session_id`, không có
  `created_at`, không có hàm liệt kê theo người học hay theo module.
- **Lần làm quiz** có `owner`, `doc_id`, `module_id`, `origin` ∈ {`module_button`, `assistant`}, `created_at`. `history(owner, doc_id)` liệt kê
  được. Quiz tạo từ danh sách khái niệm qua `scope` dạng danh sách thì `module_id = None`. Không có `session_id`.
- **Quan hệ phiên → nội dung** chỉ nằm trong câu trả lời (`created_artifacts`), không nằm ở phiên. Muốn liệt kê "nội dung của phiên này" phải
  quét mọi câu trả lời.
- **Câu trả lời** chỉ được lưu (bản ghi `answer`, khoá băm `[owner, doc_id, session_id, client_turn_id]`) khi có `client_turn_id`; bản ghi không
  có số thứ tự lượt hay thời điểm. Không có hàm đọc lại toàn bộ một phiên.
- **Công cụ tạo nội dung** của trợ lý (`composition_phase_b.py`) gọi `make_quiz(…, module_id=None, scope=…, origin='assistant')` và
  `document(…, owner=…)`; không truyền `session_id`.
- **Lớp domain đã chịu module rỗng:** `LearningGraph.relation(module_id, None)` trả `khong_ro`; `get_module_info(…, None)` và `why_here(…, None)`
  chạy được; truy hồi Pha B (`retrieval.py`) chỉ ưu tiên module khi `current_module_id` có giá trị.
- **Port lưu trữ** có `get_record`, `put_record`, `list_records(kind, owner)`; đủ để liệt kê theo người học rồi lọc.
- **Độ ổn định của mã module giữa các phiên bản đồ thị** (so tập `node_ids` của cùng một `module_id`):

  | Cặp phiên bản | Module cũ → mới | Cùng tập khái niệm | Jaccard trung bình | `node_id` chung |
  |---|---|---:|---:|---|
  | doc-1 v45 → v53 (chuỗi v3 → chuỗi gộp) | 39 → 33 | 2/33 | 0,26 | 202/205 |
  | doc-1 v52 → v53 | 33 → 33 | 33/33 | 1,00 | — |
  | doc-4 v22 → v23 | 91 → 91 | 91/91 | 1,00 | — |

  `module_id` (`module_001` ứng với `index` 0, `module_002` với 1…) là nhãn theo vị trí; `node_id` gần như ổn định.

Số đo (artifact đồ thị đang dùng: doc-1 v53 với chunk v7, doc-4 v23 với chunk v6; token đếm bằng tokenizer Gemma của dự án, xấp xỉ):

| Cuốn | Module | Khái niệm | Chunk | Token toàn bộ chunk | Chunk dạy (khác nhau) | Token chunk dạy | Câu neo (tổng ký tự) | Mô tả A5 (tổng ký tự) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| doc-1 | 33 | 205 | 199 | 43.781 | 92 | 21.488 | 34.118 | 33.338 |
| doc-4 | 91 | 495 | 671 | 151.585 | 285 | 84.523 | 83.605 | 121.772 |

Mỗi module: trung vị 5–6 khái niệm, tối đa 8; token chunk dạy mỗi module trung vị 591 (doc-1) và 912 (doc-4), p90 1.206 và 1.450, tối đa 1.603
và 2.237.

---

## Phụ lục A. Ghi chép theo sản phẩm (đọc ngày 2026-10-18)

Tính năng của các sản phẩm này đổi nhanh. Mọi điều dưới đây đúng với trang trợ giúp ở ngày đọc; có thể đã đổi sau đó.

### A.1 NotebookLM (nay trang trợ giúp gọi là "Gemini Notebook")

Trang trợ giúp ngày 2026-10-18 dùng tên "Gemini Notebook" nhưng vẫn ở địa chỉ `support.google.com/notebooklm`
([FAQ](https://support.google.com/notebooklm/answer/16269187?hl=en)). Báo cáo gọi là NotebookLM cho quen.

- **Đơn vị phạm vi là notebook.** "Each notebook is independent. Gemini Notebook can't access information across multiple notebooks at the same
  time" ([Create a notebook](https://support.google.com/notebooklm/answer/16206563?hl=en)).
- **Ba khung:** Sources, Chat, Studio. Chat mở đầu bằng "a generated summary of all your sources"; Studio là nơi "outputs based on your sources
  are generated" ([Create a notebook](https://support.google.com/notebooklm/answer/16206563?hl=en)).
- **Chọn nguồn cho từng câu hỏi:** bật tắt từng nguồn ở khung Sources hoặc ở bộ chọn nguồn trong ô nhập. "Sources: Always used in either the
  entire set or the subset you select" ([Use chat](https://support.google.com/notebooklm/answer/16179559?hl=en),
  [FAQ](https://support.google.com/notebooklm/answer/16269187?hl=en)).
- **Nguồn lớn thì truy hồi:** "Gemini Notebook retrieves the most relevant information based on your question, then builds a response from it"
  ([FAQ](https://support.google.com/notebooklm/answer/16269187?hl=en)). Từ 29/10/2025, chat dùng "the full 1 million token context window" và
  "increased our capacity for multiturn conversation more than sixfold"
  ([blog Google, 29/10/2025](https://blog.google/innovation-and-ai/models-and-research/google-labs/notebooklm-custom-personas-engine-upgrade/)).
- **Phiên chat:** một luồng chat cho mỗi notebook theo tài liệu chính thức. Chat tự lưu từ 29/10/2025, đóng rồi mở lại được, xoá được; trong
  notebook chia sẻ thì "your chat is visible only to you" (blog trên). Trang trợ giúp chỉ có "Delete Chat History" cho cả khung chat
  ([Use chat](https://support.google.com/notebooklm/answer/16179559?hl=en)). **Không tìm thấy nguồn chính thức** về nhiều luồng chat trong một
  notebook hay về tiêu đề phiên.
- **Chat không biết "đang ở bài nào"** theo nghĩa vị trí học; phạm vi chỉ là tập nguồn đang bật. Có hai cầu nối từ nội dung sang chat: chọn một nút
  của mind map thì "ask questions in the Gemini Notebook chat about that specific topic"
  ([Mind Maps](https://support.google.com/notebooklm/answer/16212283?hl=en)); và hỏi chat về kết quả quiz, flashcard đã làm
  ([blog Google, 15/09/2026](https://blog.google/innovation-and-ai/products/gemini-notebook/new-study-tools-september-2026/)).
- **Ghi chú (notes):** "Save to note" giữ nguyên bảng và trích dẫn bấm được; ghi chú đổi thành nguồn được ("Convert", "Convert all notes to
  source"); ghi chú không được dùng cho chat trừ khi được chọn
  ([Notes](https://support.google.com/notebooklm/answer/16262519?hl=en), [FAQ](https://support.google.com/notebooklm/answer/16269187?hl=en)).
- **Studio:** Notes, Audio Overviews, Video Overviews, Mind maps, Reports, Data Tables, Flashcards or Quizzes, Slide Decks, Infographics. Reports có
  "FAQ, study guide, briefing document, or an AI suggested report type" hoặc tự viết yêu cầu. Nội dung mới có chấm xanh "unread"
  ([Create a notebook](https://support.google.com/notebooklm/answer/16206563?hl=en)). Mind map lưu thành một ghi chú, mở lại ở Studio
  ([Mind Maps](https://support.google.com/notebooklm/answer/16212283?hl=en)). Audio Overview mở lại ở Studio, chỉnh được "instructions to focus
  on specific topics" ([Audio Overview](https://support.google.com/notebooklm/answer/16212820?hl=en)). **Timeline:** không thấy trong danh sách
  Studio hiện hành; không tìm thấy trang trợ giúp hiện hành nói về timeline.
- **Flashcards, quiz:** chọn số lượng "fewer, standard, and more", độ khó "easy, medium, and hard", thêm prompt định hướng; flashcard nhớ tiến độ
  "Got it!/Missed it!" và tải CSV được ([Flashcards or Quizzes](https://support.google.com/notebooklm/answer/16958963?hl=en)). Trang không nói
  quiz có giới hạn theo một nguồn hay một chủ đề; chỉ có prompt định hướng.
- **Giới hạn:** 500.000 từ hoặc 200 MB mỗi nguồn ([FAQ](https://support.google.com/notebooklm/answer/16269187?hl=en)). Số nguồn mỗi notebook:
  Standard 50, Plus 100, Pro 300, Ultra 500–600; số notebook 100–500 mỗi người; bảng ghi "Subject to Change"
  ([Plans](https://support.google.com/notebooklm/answer/16213268?hl=en)).
- **Chuyển, dời:** sao chép notebook thì "Chat history & notes are not copied", nguồn và Studio thì có
  ([Create a notebook](https://support.google.com/notebooklm/answer/16206563?hl=en)). Ghi chú xuất ra Google Docs được
  ([Notes](https://support.google.com/notebooklm/answer/16262519?hl=en)). **Không tìm thấy nguồn chính thức** về dời một nội dung Studio sang
  notebook khác.

### A.2 Gemini app: notebooks, study notebooks, Guided Learning

- **Notebooks trong Gemini** (ra mắt 08/04/2026): "personal knowledge bases", gom chat và tệp theo dự án; dời chat cũ vào được ("You can move
  past chats into notebooks"); đồng bộ nguồn với NotebookLM
  ([blog Google, 08/04/2026](https://blog.google/innovation-and-ai/products/gemini-app/notebooks-gemini-notebooklm/)).
- **Nhiều chat trong một notebook**, có bộ nhớ chung: notebook "remembers your sources, instructions, and ongoing discussions"; thêm chat có sẵn
  bằng "Add to notebook"; tắt Keep Activity thì "Gemini cannot access or use past chats in a notebook when it responds"; xoá notebook thì xoá luôn
  nguồn và chat đã thêm vào; tối đa 600 nguồn tuỳ gói
  ([Gemini Apps Help](https://support.google.com/gemini/answer/16972047?hl=en&co=GENIE.Platform%3DDesktop)). Trang trợ giúp phía NotebookLM lại
  ghi khi xoá notebook thì "Gemini conversations return to your main Gemini chat list"
  ([Notebooks in Gemini Apps](https://support.google.com/notebooklm/answer/17003757?hl=en)). Hai trang lệch nhau; cần kiểm lại trên sản phẩm.
- **Chat của Gemini với notebook** hiện ở NotebookLM dưới dạng nguồn chỉ đọc
  ([Notebooks in Gemini Apps](https://support.google.com/notebooklm/answer/17003757?hl=en)).
- **Study notebooks** (25/06/2026): người học đặt mục tiêu, tải giáo trình; Gemini tách mục tiêu thành "more than 100 specific learning objectives"
  gom theo chủ đề; có quiz chẩn đoán, bài học ngắn, quiz luyện mỗi bài "based on class materials you uploaded", bảng tiến độ "Strengths / Focus
  areas / Not started"; hỏi được "right within your study notebook"
  ([blog Google, 25/06/2026](https://blog.google/innovation-and-ai/products/gemini-app/gemini-study-notebooks/)). Trang trợ giúp ghi "Your lessons,
  conversations, quizzes & tests, and uploaded sources can all be found in your study notebook"
  ([Gemini Apps Help](https://support.google.com/gemini/answer/16972047?hl=en&co=GENIE.Platform%3DDesktop)). Bài viết không nói chat có biết bài
  đang học hay không.
- **Quiz, flashcard trong Gemini** sinh từ prompt trong chat và mở ở Canvas; trang không nói nội dung được liệt kê ở đâu ngoài chính cuộc chat,
  trừ khi thêm vào study notebook ([Gemini Apps Help](https://support.google.com/gemini/answer/16275879?hl=en)).
- **Guided Learning** (06/08/2025): chế độ hỏi gợi mở, giải từng bước, có quiz; dựa trên LearnLM. Bài viết không nói phạm vi hay tài liệu tải lên
  ([blog Google, 06/08/2025](https://blog.google/products-and-platforms/products/education/guided-learning/)).

### A.3 ChatGPT Projects

**Cách đọc:** `help.openai.com` và `openai.com/academy` trả HTTP 403 khi mở trực tiếp (cả WebFetch lẫn curl). Các ý dưới đây lấy từ trích đoạn của
máy tìm kiếm cho chính trang trợ giúp, không phải bài viết lại. Mức tin thấp hơn các mục khác; nên mở lại trang bằng trình duyệt trước khi dùng
làm căn cứ.

- **Đơn vị phạm vi là project:** "Projects keep related chats, files, and instructions together"
  ([Projects in ChatGPT](https://help.openai.com/en/articles/10169521-projects-in-chatgpt)).
- **Phiên thuộc project.** Chat cũ dời vào được (kéo vào project ở thanh bên, hoặc "Move to project"), và "the chat inherits the project's
  instructions and file context"; dời ra bằng "Remove from project"; chat tạo bằng GPT thì không dời được (cùng trang).
- **Bộ nhớ hai chế độ:** mặc định, hoặc "project-only memory". Ở chế độ riêng: "Chats can reference other conversations within the same project.
  Chats cannot reference conversations outside the project… Chats outside the project cannot reference conversations from the project."
  Project chia sẻ luôn là project-only (cùng trang). Nghĩa là **các phiên trong cùng phạm vi đọc được nhau**.
- **Chỉ dẫn project** chỉ áp trong project và thay chỉ dẫn chung của tài khoản (cùng trang, theo trích đoạn).
- **Tệp:** Free 5, Go và Plus 25, Edu/Pro/Business/Enterprise 40 tệp mỗi project; 10 tệp mỗi lần tải (cùng trang, theo trích đoạn).
- **Xoá project** xoá chat, chỉ dẫn và tệp chỉ có trong project; tệp ở Library giữ lại (cùng trang).
- **Tìm và liệt kê:** ô tìm ở thanh bên lọc theo All, Chats, Images, Documents, Projects; khớp "words in a chat's title or messages"
  ([Finding your chats, projects, and files](https://help.openai.com/en/articles/10056348-finding-your-chats-projects-and-files-in-chatgpt)).
- **Nội dung sinh ra:** tệp quản lý ở Library; từ 2026 có "Space" chứa trang và tệp, tách khỏi Projects
  ([Getting started with Space](https://help.openai.com/en/articles/20001549)). Không tìm thấy nguồn chính thức nói nội dung sinh trong một chat
  của project được liệt kê theo project.
- **Study mode không bật được trong Projects** ("not available in Temporary Chats, GPTs, or Projects")
  ([Using study mode](https://help.openai.com/en/articles/11780217-using-study-mode-in-chatgpt)). Hai phần "học" và "phạm vi tài liệu" của
  ChatGPT đang tách nhau.
- **Tiêu đề phiên:** đổi tên được ở thanh bên; **không tìm thấy nguồn chính thức** nói tiêu đề tự động được sinh thế nào.
- **Chat biết "đang ở đâu":** chỉ biết đang ở project nào (qua tệp, chỉ dẫn, bộ nhớ); không có khái niệm vị trí trong tài liệu.

### A.4 Claude Projects

- **Đơn vị phạm vi là project:** "self-contained workspaces with their own chat histories and knowledge bases"
  ([What are projects?](https://support.claude.com/en/articles/9517075-what-are-projects)).
- **Phiên thuộc project, dời được:** "You can move a standalone chat into a project", "remove chats from projects, or move them between projects".
  Chỉ dẫn project áp cho "all the chats within the project". Ngữ cảnh không chia giữa các chat trừ khi "the information is added into the project
  knowledge base" ([Create and manage projects](https://support.claude.com/en/articles/9519177-how-can-i-create-and-manage-projects)).
- **Bộ nhớ và tìm chat theo project:** "Each project has its own memory"; tìm chat cũ "limited to within each specific project"; chat trong
  project dùng bộ nhớ project cộng bộ nhớ tài khoản, không dùng bộ nhớ của project khác; tắt "Use account memory" để cô lập hẳn
  ([Chat search and memory](https://support.claude.com/en/articles/11817273-use-claude-s-chat-search-and-memory-to-build-on-previous-context)).
- **Kiến thức lớn thì truy hồi:** khi kiến thức project gần chạm trần ngữ cảnh, Claude "seamlessly enables RAG mode to expand capacity by up to
  10x", chỉ ở gói trả tiền ([What are projects?](https://support.claude.com/en/articles/9517075-what-are-projects),
  [RAG for projects](https://support.claude.com/en/articles/11473015-retrieval-augmented-generation-rag-for-projects)).
- **Nội dung sinh ra** (artifact) không được hai trang trên mô tả theo project; **không tìm thấy nguồn chính thức** về thư viện nội dung theo
  project.
- **Chat biết "đang ở đâu":** chỉ ở mức project.

### A.5 Khanmigo (Khan Academy)

**Cách đọc:** trang `support.khanacademy.org` trả HTTP 403 khi mở trực tiếp; các ý từ trang trợ giúp lấy qua trích đoạn máy tìm kiếm. Blog Khan
Academy mở được.

- **Chat gắn trang nội dung.** Trên trang bài, video, bài tập có biểu tượng Khanmigo ở góc dưới phải, bấm thì mở khung chat; ngoài ra có trang
  "Activities" chung. Khanmigo **không có** ở quiz, unit test, course challenge, mastery challenge
  ([Where can I access Khanmigo](https://support.khanacademy.org/hc/en-us/articles/13982530363533-Where-can-I-access-Khanmigo-while-working-on-Khan-Academy),
  qua trích đoạn).
- **Chat biết bài đang làm:** "When a student opens Khanmigo during a practice exercise, Khanmigo sees the problem they're working on", nhưng
  "doesn't automatically know how the student has been performing"
  ([blog Khan Academy, 05/2026](https://blog.khanacademy.org/how-khan-academy-is-building-a-better-ai-tutor-our-most-recent-learnings/)).
- **Lịch sử chat là một danh sách chung** theo tài khoản: mở từ menu ba chấm của khung chat ("Chat history") hoặc ở Learner Home; phụ huynh và giáo
  viên xem được bản ghi ([View my Khanmigo chat history](https://support.khanacademy.org/hc/en-us/articles/13982846291725-How-do-I-view-my-Khanmigo-chat-history),
  qua trích đoạn). Không tìm thấy nguồn chính thức nói danh sách này được nhóm theo bài hay theo khoá.
- **Thí nghiệm A/B về ngữ cảnh** (khoảng 20 thử nghiệm, hơn 15 triệu luồng tutoring, 6 tháng; blog trên):
  - thêm tóm tắt các lần làm gần đây: đúng ở câu kế +3,4% (608.000 luồng);
  - thêm **kỹ năng tiên quyết chưa thành thạo kèm ôn ngắn**: +2,7% (1,36 triệu luồng);
  - cả hai: +6,1%;
  - thêm log hội thoại dạng chữ và các luồng 24 giờ trước **cùng kỹ năng**: mức "cognitive engagement" +5,09%. Log JSON thô thì không có tác dụng.
  - Số đo là "next-item correctness": làm đúng câu kế cùng kỹ năng mà không cần Khanmigo. Đây là blog của nhà sản xuất, chưa bình duyệt.

### A.6 Coursera Coach (nay trang trợ giúp gọi là "Coursera AI")

**Cách đọc:** trang `coursera.support` cần JavaScript, WebFetch chỉ thấy màn hình tải; các ý từ trang trợ giúp lấy qua trích đoạn máy tìm kiếm.

- **Chat gắn khoá học và mục đang mở.** Có ở trang chủ khoá, video, bài đọc, trang trước bài kiểm tra, Coursera Labs; **không có** trong quiz và bài
  đánh giá ([Advance your learning with Coursera AI](https://www.coursera.support/s/article/learner-000002224-Advance-your-learning-with-Coursera-Coach),
  qua trích đoạn). Pilot đầu tiên chạy "on the lecture pages in 2023"
  ([blog Coursera, 23/06/2025](https://blog.coursera.org/coach-wins-newsweek-ai-impact-award/)).
- **Nguồn:** dùng "learner profile data, and the expert content created by our industry and university partners"; người học xoá được lịch sử chat,
  xoá "chat memories", tắt lưu bộ nhớ (trang trợ giúp trên, qua trích đoạn).
- **Tính năng:** hỏi bất cứ lúc nào trong khoá, "Help Me Practice" trước bài chấm điểm, giải thích ví dụ
  ([blog Coursera, 05/06/2024](https://blog.coursera.org/coursera-coach-leveraging-genai-to-empower-learners/)).
- **Số đo:** chỉ có số dùng: "over 34 million messages with more than 2.4 million learners" (blog 23/06/2025). Không tìm thấy nguồn chính thức có
  số đo kết quả học có nhóm đối chứng.
- Không tìm thấy nguồn chính thức về: chat có biết đúng video đang xem hay không (chỉ có bài viết lại của bên thứ ba), danh sách phiên, nội dung sinh
  ra được lưu ở đâu.

### A.7 Perplexity Spaces (nay là "Projects")

- **Đơn vị phạm vi là Project**, giữ "your searches, Perplexity Computer tasks, files, instructions, and connected tools together"
  ([What are Projects?](https://www.perplexity.ai/help-center/en/articles/10352961-what-are-projects)). Trang này không còn dùng chữ "Spaces";
  địa chỉ cũ "spaces" trỏ về cùng số bài.
- **Bộ nhớ chung trong phạm vi:** "Brain builds ongoing memory for all work done in a Project"; chủ project bật tắt được việc dùng bộ nhớ cá nhân
  (cùng trang).
- **Tạo phạm vi từ phiên có sẵn:** "start a Project from an existing session", Perplexity **gợi ý tiêu đề, mô tả và chỉ dẫn**; "Convert session to
  project" mang theo tệp và artifact (cùng trang).
- **Giới hạn:** tiêu đề ≤ 50 ký tự, mô tả ≤ 1.000 ký tự, chỉ dẫn ≤ 8.000 ký tự, 10.000 tệp và 5 GB mỗi project, mỗi tệp ≤ 100 MB (cùng trang).
- Trang không nói tìm kiếm trong project có giới hạn ở tệp hay gồm cả web, và không nói danh sách luồng hiện thế nào.
