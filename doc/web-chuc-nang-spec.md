# Spec Web — tài khoản, khoá học, chia sẻ, mức dùng, và lớp dịch vụ của lõi

**Ngày:** 2026-10-18. **Nhãn:** `ready-for-agent`. **Trạng thái:** chờ chia vé; vé sẽ ở `task/web/`.

**Phạm vi:** spec này đặc tả các **chức năng** của trang web nhiều người dùng, và cách **đóng gói** lõi (Pha A dựng một cuốn, Pha B học) thành một lớp
dịch vụ để FastAPI gọi. Hai spec viết sau sẽ dựa vào spec này:
- **thiết kế giao diện** (cho Figma): sơ đồ trang, bố cục, trạng thái, bộ thành phần;
- **thiết kế cơ sở dữ liệu**: bảng, khoá, chỉ mục, di trú. Mục 13 dưới đây chỉ ghi mức khái niệm.

**Quan hệ với spec khác:**
- [Spec Pha B](pha-b-spec.md) và [spec Pha B2](pha-b2-spec.md) định nghĩa nội dung học và hợp đồng dữ liệu. Spec này **không đổi** hành vi của chúng; nó
  chỉ quyết ai được gọi, với `owner` và `doc_id` nào.
- Spec Pha B2 ghi "đăng nhập, nhiều người dùng thật, cơ sở dữ liệu, giao diện React: nhóm web" ở mục Ngoài phạm vi. Spec này là phần đó.

**Quyết định kiến trúc đi kèm:**
- [ADR 0020](adr/0020-khoa-hoc-la-don-vi-chia-se-du-lieu-hoc-theo-nguoi-va-cuon.md): khoá học là đơn vị chia sẻ; dữ liệu học khoá theo người × cuốn;
  bản dựng dùng lại theo băm tệp.
- [ADR 0021](adr/0021-phien-dang-nhap-phia-may-chu-trong-cookie.md): đăng nhập bằng phiên phía máy chủ trong cookie, không dùng JWT.
- [ADR 0023](adr/0023-cloudinary-cho-tep-goc-va-anh.md): tệp gốc và ảnh ở Cloudinary, riêng tư; máy chủ chuyển ảnh, trình duyệt không cầm link Cloudinary.

**Quyết định của chủ dự án** (2026-10-18, mục "Quyết định của chủ dự án" cuối spec): web là **bản demo**, ai cũng tải sách được, khâu dựng không giới
hạn; khoá mẫu chỉ ở dev; gửi thư bằng Gmail SMTP; một tài khoản Cloudinary. Mọi con số nằm trong `WebSettings` (mục 12) để đổi không phải sửa mã.

**Bổ sung giao diện theo chủ dự án 2026-10-18:** nhóm thiết kế và React phải làm giao diện đẹp, chỉn chu, nhất quán và có hiệu ứng tương tác phù hợp;
được phép dùng các skill trong bộ `taste-skill` do chủ dự án nạp. Yêu cầu thị giác, chuyển động và bằng chứng nghiệm thu theo
[spec thiết kế, mục 3a](web-thiet-ke-giao-dien-spec.md#3a-chất-lượng-thị-giác-hiệu-ứng-và-taste-skill).

**Quy trình:** Claude viết spec và vé; chủ dự án giao nhân viên và nhóm web; người soát kiểm theo vé.

---

## Vấn đề

Lõi hiện chỉ chạy cho **một người trên một máy**:
- giao diện duy nhất là CLI và trang xem thử trên `127.0.0.1`, với `owner = 'local'`;
- kho Pha B là một tệp JSON, và trang xem thử ghi rõ "không dùng kho JSON này đồng thời từ nhiều tiến trình".

**Không đưa được một cuốn mới vào hệ thống từ giao diện.**
- Dựng một cuốn cần chạy tay nhiều lệnh: `ingest`, `a4`, `roadmap`, rồi các bước chuẩn bị Pha B (`a12`, `concept-index`, `formulas`).
- `a4` còn đòi đường dẫn bộ vàng, kể cả khi cuốn không có vàng (`--gold … --no-gold-for-doc`).
- Không có dự toán trước cho người bấm, và không có trần chi theo người cho khâu dựng. Đây là khâu đắt nhất: D-01 đo 28,06 USD cho 16 cuốn ở chuỗi cũ,
  khoảng 1,75 USD/cuốn, mà chưa gồm pass chính A8; bài giảng chỉ khoảng 0,002 USD/bài. Chuỗi gộp hiện hành chưa có số đo USD/cuốn trên một cuốn mới
  hoàn toàn (doc-6 chạy lại ≈ 0,007 USD là nhờ cache).
- 16/20 sách mới kiểm ở D-02 là **bản quét**. Bộ đọc nhẹ không đọc được bản quét, mà hiện chưa có bước nào báo sớm cho người tải lên.

**Không có tài khoản, khoá học hay chia sẻ.**
- Một lớp muốn cùng học một giáo trình thì mỗi người phải tự dựng lại, tốn tiền gấp nhiều lần.
- Trong khi đó bài giảng và ngân hàng quiz **đã** cache chung theo nội dung (ADR 0011). Chia sẻ khoá học làm phần cache này có lợi thật: thêm người học
  không thêm chi phí bài giảng.

**Đa tiến trình:** `single_flight` (chống sinh trùng một bài khi nhiều người bấm cùng lúc) chỉ khoá trong một tiến trình. Máy chủ web chạy nhiều worker sẽ
sinh trùng và trả tiền hai lần.

**Nhóm web (4 người, FastAPI + React) chưa có đặc tả chức năng,** chưa biết gọi hàm nào của lõi, kiểm quyền ở đâu.

## Giải pháp

Người dùng thấy các chức năng sau:

**Tài khoản:**
- đăng ký bằng email và mật khẩu, xác minh email, đăng nhập, đăng xuất, quên mật khẩu;
- trang hồ sơ: đổi tên hiển thị, đổi mật khẩu, đăng xuất khỏi mọi thiết bị, xoá tài khoản.

**Tải giáo trình lên và dựng lộ trình:**
- tải một tệp PDF hoặc DOCX tiếng Việt, xác nhận có quyền dùng tài liệu;
- người dùng xác nhận mới xếp hàng; worker đọc tài liệu (0 USD), chặn sớm bản quét/chữ lỗi/không phải tiếng Việt, rồi dựng; không hiện dự toán hay chi phí;
- người dùng bấm "Dựng lộ trình", theo dõi tiến trình theo bốn bước, huỷ được, thử lại được khi lỗi;
- dựng xong thì thành một **khoá học** của người đó.
- Tệp đã có người dựng rồi (cùng băm) thì xong ngay, 0 USD, không trừ lượt dựng.

**Khoá học của tôi:** danh sách khoá mình tạo, khoá được chia sẻ, lời mời đang chờ, khoá học mẫu; mỗi khoá có "xong x/y" và nút "Học tiếp".

**Chia sẻ:**
- **link mời:** chủ khoá học tạo link có hạn dùng và số lượt tối đa, thu hồi được; ai có link và đã đăng nhập thì tham gia được;
- **mời theo email:** người đã có tài khoản thấy lời mời trong ứng dụng; người chưa có nhận email kèm link đăng ký;
- **thành viên:** chủ khoá xem danh sách, xoá thành viên; thành viên tự rời khoá được.

**Học trong khoá học:** đúng hai trang của spec Pha B2 (trang lộ trình, trang học), với bài giảng, trợ lý, phiên, quiz, tài liệu, thư viện, tiến độ, và
nút "Đọc trang p" mở tệp gốc. Mỗi thành viên có tiến độ, phiên chat và thư viện **riêng**. Bài giảng và ngân hàng quiz **dùng chung** cả khoá.

**Mức dùng:** mỗi người thấy hôm nay đã dùng bao nhiêu phần trần trợ lý và tài liệu, giờ đặt lại, và còn mấy lượt dựng trong tháng.

**Quản trị (admin):** người dùng, bản dựng, chi theo ngày và theo mục đích, trần hệ thống, báo lỗi nội dung, khoá học mẫu.

**Thêm, Claude đề xuất:**
- chủ khoá học xem **tiến độ tổng hợp** của thành viên (chỉ số khái niệm đã học, không bao giờ thấy chat);
- **báo lỗi nội dung** ở bài giảng, câu trả lời và câu quiz (đã có `report-question` cho quiz);
- **khoá học mẫu** từ sáu cuốn phát triển, để demo và để người mới thử ngay không phải tải sách;
- **dựng lại và phát hành phiên bản mới** khi Pha A tốt lên (vé để sau).

---

## User story

**Khách (chưa đăng nhập):**
1. Là khách, tôi muốn xem trang giới thiệu ngắn về hệ thống, để biết nó làm gì trước khi đăng ký.
2. Là khách, tôi muốn đăng ký bằng email và mật khẩu, để có tài khoản học.
3. Là khách cầm link mời, tôi muốn thấy tên khoá học và tên người mời trước khi đăng ký, để biết mình được mời vào đâu.
4. Là khách cầm link mời, tôi muốn sau khi đăng ký xong được đưa thẳng vào khoá học đó, để không phải tìm lại link.

**Tài khoản:**
5. Là người dùng mới, tôi muốn nhận email xác minh, để chứng minh email là của tôi.
6. Là người dùng chưa xác minh, tôi muốn vẫn đăng nhập và tham gia khoá học bằng link được, để không bị chặn khi email đến chậm.
7. Là người dùng chưa xác minh, tôi muốn gửi lại email xác minh, để xác minh khi lỡ mất email đầu.
8. Là người dùng, tôi muốn đăng nhập bằng email và mật khẩu, và được nhớ đăng nhập trên máy của mình, để không phải nhập lại mỗi lần.
9. Là người dùng, tôi muốn sai mật khẩu chỉ thấy một thông báo chung, để kẻ khác không dò được email nào đã đăng ký.
10. Là người dùng quên mật khẩu, tôi muốn đặt lại qua email, để lấy lại tài khoản.
11. Là người dùng, tôi muốn đổi mật khẩu, và mọi phiên đăng nhập khác bị thoát, để chặn người đang dùng trộm.
12. Là người dùng, tôi muốn đăng xuất khỏi mọi thiết bị, để an toàn khi lỡ đăng nhập ở máy lạ.
13. Là người dùng, tôi muốn đổi tên hiển thị, để chủ khoá học nhận ra tôi.
14. Là người dùng, tôi muốn xoá tài khoản và toàn bộ dữ liệu học của mình, để rời hệ thống sạch sẽ.
15. Là người dùng bị khoá tài khoản, tôi muốn thấy thông báo rõ khi đăng nhập, để biết liên hệ ai.

**Tải giáo trình và dựng:**
16. Là người dùng đã xác minh, tôi muốn tải lên một tệp PDF hoặc DOCX, để biến nó thành lộ trình học.
17. Là người tải lên, tôi muốn được hỏi xác nhận có quyền dùng và chia sẻ tài liệu, để rõ trách nhiệm bản quyền.
18. Là người tải lên, tôi muốn biết ngay khi tệp quá lớn, quá nhiều trang, bị mã hoá, hay sai định dạng, để không phải chờ vô ích.
19. Là người tải lên bản quét, tôi muốn được báo "tệp là bản quét, chưa hỗ trợ" sau bước đọc, không tốn tiền, để tìm bản có chữ.
20. Là người tải lên tài liệu không phải tiếng Việt, tôi muốn được báo chưa hỗ trợ, để không tốn tiền.
21. Là người tải lên, tôi muốn kiểm lại tệp đã chọn và bấm xác nhận trước khi dựng; không cần xem dự toán thời gian hay chi phí.
22. Là người tải lên, tôi muốn theo dõi tiến trình qua bốn bước "Đọc tài liệu", "Trích khái niệm", "Dựng đồ thị và lộ trình", "Chuẩn bị bài học", để
    biết còn bao lâu.
23. Là người tải lên, tôi muốn rời trang trong lúc dựng rồi quay lại vẫn thấy tiến trình, và nhận email khi xong, để không phải ngồi chờ.
24. Là người tải lên, tôi muốn huỷ một lần dựng đang chạy, để dừng chi khi tải nhầm tệp.
25. Là người tải lên, tôi muốn thử lại khi lần dựng lỗi, và lần sau chạy tiếp từ bước lỗi, để không trả lại tiền các bước đã xong.
26. Là người tải lên một tệp đã có người dựng, tôi muốn có khoá học ngay mà không tốn lượt dựng, để đỡ chờ.
27. Là người dùng, tôi muốn biết mình còn mấy lượt dựng trong tháng, để tự cân nhắc.
28. Là người dùng hết lượt dựng, tôi muốn được báo trước khi gửi tệp, để không mất công tải lên.

**Khoá học của tôi:**
29. Là người dùng, tôi muốn thấy khoá mình tạo và khoá được chia sẻ ở hai nhóm riêng, để dễ tìm.
30. Là người dùng, tôi muốn mỗi khoá hiện "xong x/y" và nút "Học tiếp" mở module gần nhất tôi học, để vào học nhanh.
31. Là chủ khoá học, tôi muốn đổi tên và mô tả khoá, để thành viên hiểu khoá học gì.
32. Là chủ khoá học, tôi muốn xoá khoá, để dọn khoá tạo nhầm.
33. Là người dùng mới, tôi muốn thấy khoá học mẫu để thử ngay, để hiểu hệ thống trước khi tải sách của mình.

**Chia sẻ:**
34. Là chủ khoá học, tôi muốn tạo link mời có hạn dùng và số lượt tối đa, để chia sẻ cho cả lớp qua nhóm chat.
35. Là chủ khoá học, tôi muốn thu hồi một link, để chặn người ngoài khi link bị lộ.
36. Là chủ khoá học, tôi muốn mời theo danh sách email, để mời đúng người.
37. Là người được mời theo email, tôi muốn thấy lời mời ở trang chủ và chấp nhận hay từ chối, để quyết có tham gia không.
38. Là người tham gia, tôi muốn được báo trước "chủ khoá học thấy số khái niệm bạn đã đánh dấu học, không thấy nội dung chat", để biết dữ liệu nào được
    chia sẻ.
39. Là chủ khoá học, tôi muốn xem danh sách thành viên, ngày tham gia, và lần học gần nhất, để quản lý lớp.
40. Là chủ khoá học, tôi muốn xoá một thành viên, để bỏ người không thuộc lớp.
41. Là thành viên, tôi muốn rời khoá học, để dọn danh sách của mình.
42. Là thành viên đã rời rồi tham gia lại, tôi muốn thấy lại tiến độ và phiên cũ, để học tiếp.
43. Là người cầm link hết hạn hay đã thu hồi, tôi muốn thấy thông báo rõ, để xin link mới.

**Học (thành viên):**
44. Là thành viên, tôi muốn trang lộ trình và trang học như spec Pha B2, để học theo module.
45. Là thành viên, tôi muốn tiến độ, phiên chat và thư viện của tôi là riêng, để người khác không đọc được.
46. Là thành viên, tôi muốn bài giảng hiện ngay nếu người khác trong khoá đã mở trước, để không phải chờ sinh.
47. Là thành viên, tôi muốn bấm "Đọc trang p" để mở đúng trang trong tệp gốc, để đối chiếu sách.
48. Là thành viên, tôi muốn trợ lý và bài giảng trả lời dần (stream), để không nhìn màn hình trống.
49. Là thành viên, tôi muốn báo lỗi một bài giảng, một câu trả lời hay một câu quiz, để chủ khoá và nhóm phát triển sửa.
50. Là thành viên ở hai khoá của cùng một cuốn, tôi muốn tiến độ được dùng chung, vì đó là cùng nội dung.

**Mức dùng:**
51. Là thành viên, tôi muốn thấy hôm nay đã dùng bao nhiêu phần trần trợ lý và tài liệu, và giờ đặt lại, để chia lượt hỏi.
52. Là thành viên hết trần ngày, tôi muốn vẫn đọc bài giảng có sẵn, làm quiz, và xem thư viện, để vẫn học được.
53. Là thành viên, tôi muốn trần ngày tính chung mọi khoá, để hiểu luật đơn giản.

**Chủ khoá học:**
54. Là chủ khoá học, tôi muốn xem bảng tiến độ tổng hợp: mỗi thành viên "xong x/y" theo module, để biết lớp đang ở đâu.
55. Là chủ khoá học, tôi muốn xem các báo lỗi nội dung của khoá mình, để biết chỗ nào đáng ngờ.
56. Là chủ khoá học, tôi muốn dựng lại khi hệ thống có bản Pha A mới, và chọn lúc phát hành cho thành viên, để không đổi lộ trình giữa buổi học.

**Quản trị:**
57. Là admin, tôi muốn xem danh sách người dùng, khoá tài khoản, và đổi số lượt dựng mỗi tháng của một người, để quản lý chi.
58. Là admin, tôi muốn xem mọi bản dựng: trạng thái, chi thật, lỗi, để gỡ lỗi.
59. Là admin, tôi muốn xem chi theo ngày, theo mục đích (dựng, bài giảng, quiz, trợ lý, tài liệu) và theo khoá học, để đối soát với hoá đơn.
60. Là admin, tôi muốn thấy trần hệ thống hôm nay còn bao nhiêu, để biết khi nào nội dung dùng chung ngừng sinh.
61. Là admin, tôi muốn đánh dấu một khoá là khoá mẫu, để mọi người dùng tham gia được không cần link.
62. Là admin, tôi muốn **không** đọc được chat và tài liệu riêng của người học, để người học tin hệ thống.
63. Là admin, tôi muốn có nhật ký các thao tác nhạy cảm (đăng nhập lỗi, đổi mật khẩu, tạo và thu hồi link, xoá thành viên, thao tác admin), để điều tra
    khi có sự cố.

**Nhóm web và nhân viên:**
64. Là lập trình viên web, tôi muốn một lớp dịch vụ duy nhất với danh sách hàm rõ ràng, để route FastAPI chỉ gọi hàm, không tự viết logic.
65. Là lập trình viên web, tôi muốn mọi kiểm quyền nằm ở một bảng luật duy nhất, để không route nào quên kiểm.
66. Là lập trình viên web, tôi muốn chạy toàn bộ test không cần mạng và không tốn tiền, với mô hình giả và bộ dựng giả, để làm việc hằng ngày.
67. Là lập trình viên web, tôi muốn bảng mã lỗi ổn định, để giao diện hiện đúng câu tiếng Việt.
68. Là người soát, tôi muốn một test tự liệt kê mọi route của khoá học và kiểm người ngoài khoá bị từ chối, để route mới thêm cũng được kiểm.

---

## Quyết định triển khai

### 1. Kiến trúc và lớp dịch vụ (đóng gói lõi)

**Nơi đặt mã** (chủ dự án chốt 2026-10-18): mọi mã web ở **`src/web/`**, tách khỏi lõi `src/doc2roadmap/`.

```
src/
  doc2roadmap/        lõi; web chỉ thêm build_document (W-13) và nới port sổ chi (W-05)
  web/
    backend/
      wayfinder/      gói Python của web: domain/, application/, infrastructure/, api/, worker, migrations/
      tests/
    frontend/         React + Vite + TypeScript
    docker-compose.yml  db (dev), db-test (test)
    .env.example
```

- **Phụ thuộc một chiều:** `wayfinder` gọi `doc2roadmap`; `doc2roadmap` không bao giờ import `wayfinder`. Có test kiến trúc cho luật này.
- **Tên gói Python là `wayfinder`,** không phải `web`: tên `web` quá chung và trùng thư viện `web.py`.
- **Một `pyproject.toml`, một `.venv`:** gói phụ thuộc của web (FastAPI, Uvicorn, SQLAlchemy, psycopg, Alembic, argon2-cffi, Cloudinary,
  python-multipart) nằm ở nhóm tuỳ chọn `web`, cài bằng `pip install -e .[web,dev]`. Lõi không phải cài chúng.
- **PostgreSQL chạy bằng Docker** trên máy dev (`src/web/docker-compose.yml`). Lúc dev chỉ cơ sở dữ liệu chạy trong Docker; API, worker và Vite chạy
  thẳng trên máy. Bản chạy đủ trong Docker là vé triển khai W-21.

**Đường gọi Gemini của web** (chủ dự án cập nhật 2026-10-19, thay quyết định Developer API ngày 2026-10-18): backend FastAPI và worker **tạm dùng
Vertex AI**. Chỉ chuyển sang Gemini Developer API khi chủ dự án yêu cầu lúc chuẩn bị demo; không tự chuyển theo ngày hay khi lỗi.
- Composition web nạp `Settings` lõi với `llm_transport = vertex`, dùng cho cả mô hình sinh và embedding, kể cả use case dựng sách gọi Pha A.
- Cấu hình phía máy chủ: `DOC2ROADMAP_LLM_TRANSPORT=vertex`, `DOC2ROADMAP_VERTEX_PROJECT`, `DOC2ROADMAP_VERTEX_LOCATION` (mặc định `global`), cùng
  thông tin xác thực ADC hợp lệ. Bí mật chỉ ở môi trường máy chủ/kho bí mật, không vào React, biến `VITE_*`, phản hồi API hay log.
- Chế độ thật kiểm cấu hình trước lời gọi: dùng Vertex và có project/thông tin xác thực hợp lệ; không bắt buộc Gemini API key trong giai đoạn này.
  Lỗi cấu hình/xác thực báo rõ, không tự chuyển sang Developer API. Test mô hình giả/phát lại vẫn 0 USD, không cần thông tin xác thực thật.
- Giữ khả năng chọn transport qua cấu hình hiện có để chuyển khi chủ dự án chỉ thị; không khoá cứng Vertex trong lõi. Báo cáo/recording lịch sử giữ nguyên.

**Bên trong `wayfinder`, bốn tầng như lõi:**
- **domain:** thực thể web (tài khoản, khoá học, thành viên, link mời, lời mời, bản dựng) và **bảng luật phân quyền** dạng hàm thuần;
- **application:** các **dịch vụ web** (mục dưới) và port mới; gọi use case Pha B có sẵn và use case "dựng một cuốn" mới;
- **infrastructure:** bản cài PostgreSQL của mọi port, **kể cả kho Pha B** (bản cài port `PhaseBStore` của lõi, để lõi không dính SQLAlchemy),
  Cloudinary (tệp gốc, ảnh), gửi thư, băm mật khẩu;
- **api:** ứng dụng FastAPI (mỏng: đọc yêu cầu, gọi dịch vụ, ghi phản hồi) và một tiến trình worker cho bản dựng.
- **Giao diện React** ở `src/web/frontend/`, chỉ nói chuyện với API HTTP.

**Luật tầng:** domain và application của `wayfinder` không import FastAPI, SQLAlchemy, SDK Cloudinary, hay thư viện băm mật khẩu; `doc2roadmap` không
import `wayfinder`.

**Mọi dịch vụ nhận một `Actor`** đã xác thực: `{user_id, role ∈ {user, admin}, email_verified, status}`, hoặc `None` với khách. Route không bao giờ tự
dựng `owner` hay `doc_id`; dịch vụ lấy chúng từ `Actor` và bản ghi khoá học.

**Các dịch vụ và hàm** (tên là hợp đồng giữa lõi và nhóm web):

| dịch vụ | hàm |
|---|---|
| `AccountService` | `register`, `verify_email`, `resend_verification`, `login`, `logout`, `logout_all`, `request_password_reset`, `reset_password`, `change_password`, `update_profile`, `delete_account`, `me` |
| `BuildService` | `create_upload`, `get_upload`, `confirm_build`, `get_build`, `cancel_build`, `retry_build`; phía worker: `run_next_job` |
| `CourseService` | `list_my_courses`, `get_course`, `update_course`, `delete_course`, `list_sample_courses`, `join_sample_course` |
| `SharingService` | `create_share_link`, `list_share_links`, `revoke_share_link`, `preview_share_link`, `join_by_link`, `invite_by_email`, `list_course_invitations`, `cancel_invitation`, `list_my_invitations`, `accept_invitation`, `decline_invitation`, `list_members`, `remove_member`, `leave_course`, `members_progress` |
| `LearningGateway` | bọc Pha B: `get_roadmap`, `get_lecture`, `stream_lecture`, `set_progress`, `get_progress`, `create_session`, `list_sessions`, `rename_session`, `delete_session`, `list_turns`, `ask_stream`, `make_quiz`, `submit_quiz`, `make_document`, `get_document`, `list_library`, `open_source_page`, `open_source_file`, `get_media`, `report_content` |
| `UsageService` | `my_usage`; admin: `spend_summary`, `system_caps_today` |
| `AdminService` | `list_users`, `update_user` (trạng thái, vai trò, lượt dựng), `list_builds`, `list_reports`, `set_sample_course` |

**`LearningGateway` là chỗ duy nhất gọi Pha B.** Mỗi hàm:
1. tải khoá học; kiểm `Actor` là thành viên qua bảng luật (mục 3);
2. gọi use case Pha B với `owner = actor.user_id`, `doc_id = course.doc_id`, `graph_version = course.published_graph_version`;
3. trả nguyên hợp đồng Pha B (`lecture-3`, `answer-3`, `quiz-2`, `document-2`, `session-1`, `turn-1`, `library-1`, `progress-1`), chỉ thêm `course_id`.

**Cập nhật 2026-10-23:** ADR 0025/spec bài giảng 3 và ADR 0026/spec trợ lý 3 thay cấu trúc lecture-2/answer-2 trước đó.
W-08 chờ SA-64, W-09 chờ SA-66 cho cổng tích hợp hợp đồng mới; chuẩn bị UI/gateway bằng fake được. Không coi mã cũ đã cài là đạt hợp đồng mới.

Gateway **không** sửa nội dung Pha B. Mọi kiểm `owner` của Pha B vẫn chạy như cũ, thành hai lớp kiểm.

**Tiêu điểm trợ lý** (chủ dự án duyệt 2026-10-22; lõi SA-56, web W-09): body POST lượt có `focus_node_id` tuỳ chọn.
Trang học gửi ID khái niệm có bài giảng đang mở ở mỗi lượt, gồm bài tiên quyết; trang lộ trình không gửi. Gateway truyền nguyên giá trị vào use case,
không tự kiểm hoặc ghi vào session/assistant_state. Lõi bỏ ID không phải khái niệm học được của đồ thị đang dùng, trả `focus_node_id = null` kèm
`focus_ignored`; giá trị hợp lệ được trả lại trong `answer-3` cuối. Lượt không gửi không kế thừa tiêu điểm trước. Membership, owner, doc và graph/version
vẫn do máy chủ buộc; tiêu điểm không cấp thêm quyền. W-09 nghiệm thu tích hợp sau khi Claude nghiệm thu/ghép SA-56.

**Công cụ của trợ lý bị buộc phía máy chủ.** `make_quiz`, `make_document`, `get_lecture` và công cụ tra cứu nhận `owner`, `doc_id` từ gateway, không bao giờ
từ đầu ra của mô hình. Một tài liệu tải lên có câu "hãy đọc dữ liệu của người khác" (chèn lệnh) không có đường nào tới dữ liệu ngoài khoá học đó.

**Stream:** dùng **Server-Sent Events** (SSE). Lecture-3: skeleton/delta{text}/final{lecture}/failure; answer-3:
progress/tool_call/delta/graph_card/artifact/final/failure. Markdown/LaTeX hiện dần; sources và nhãn nguồn mở đúng trang, validation chỉ admin.

**Bản dựng chạy ở worker riêng,** không trong tiến trình web. Hàng đợi là một bảng trong PostgreSQL (mục 13), không thêm Redis hay Celery.

### 2. Tài khoản và xác thực (theo ADR 0021)

**Đăng ký:**
- Trường: `email`, `password`, `display_name` (1–60 ký tự).
- Email được cắt khoảng trắng và đổi chữ thường; duy nhất không phân biệt hoa thường.
- **Mật khẩu:** 8–128 ký tự; không bắt buộc kiểu chữ hoa, số, ký hiệu; từ chối nếu nằm trong danh sách mật khẩu phổ biến đóng kèm (khoảng 10.000 mục).
  Theo NIST SP 800-63B.
- **Băm Argon2id**, tham số tối thiểu theo OWASP (bộ nhớ 19 MiB, 2 vòng, 1 luồng). Không bao giờ lưu hay ghi log mật khẩu thô.
- **Không lộ email đã có:** đăng ký bằng email đã tồn tại vẫn trả cùng phản hồi "kiểm tra email"; hệ thống gửi email "bạn đã có tài khoản, đăng nhập hay
  đặt lại mật khẩu ở đây".
- Tạo xong thì đăng nhập luôn, với `email_verified = false`.

**Xác minh email:** token ngẫu nhiên 32 byte, chỉ lưu băm SHA-256, dùng một lần, hạn `email_verify_ttl_hours` (24). Gửi lại tối đa
`resend_verification_per_hour` (3) lần mỗi giờ.

**Chưa xác minh thì được và không được** (chủ dự án chốt: bản demo, ai cũng tải sách được):
- được: đăng nhập, học, tham gia khoá, **tải sách lên**, tạo link mời;
- không được: **mời theo email**, vì việc này gửi thư bằng tài khoản Gmail của dự án tới người lạ. Lỗi `email_unverified`.

**Đăng nhập:**
- Sai email hay sai mật khẩu đều trả một lỗi chung `invalid_credentials`.
- **Giới hạn thử:** `login_max_failures` (5) lần sai mỗi email trong `login_failure_window_minutes` (15), và 20 lần mỗi IP trong cùng cửa sổ. Vượt thì
  `rate_limited` kèm `retry_after`.
- Đăng nhập đúng thì tạo **phiên phía máy chủ**:
  - token ngẫu nhiên 32 byte trong cookie `d2r_session`: `HttpOnly`, `Secure` (khi chạy HTTPS), `SameSite=Lax`, `Path=/`;
  - cơ sở dữ liệu chỉ lưu băm SHA-256 của token;
  - hết hạn khi không dùng `session_idle_days` (7), và tuyệt đối sau `session_absolute_days` (30).
- Tài khoản `disabled` không đăng nhập được: lỗi `account_disabled`, và mọi phiên đang có bị huỷ ngay khi admin khoá.

**Chống CSRF:** mỗi phiên có một `csrf_token` riêng, trả trong `GET /me`. Mọi yêu cầu đổi dữ liệu (POST, PUT, PATCH, DELETE) phải gửi header
`X-CSRF-Token` khớp, và header `Origin` phải nằm trong `allowed_origins`. Thiếu hay sai thì `csrf_failed`.

**Quên mật khẩu:** luôn trả "nếu email có tài khoản, bạn sẽ nhận thư". Token như xác minh, hạn `password_reset_ttl_minutes` (60), dùng một lần, tối đa 3
yêu cầu mỗi email mỗi giờ. Đặt lại thành công thì huỷ **mọi** phiên của tài khoản.

**Đổi mật khẩu** cần mật khẩu hiện tại; thành công thì huỷ mọi phiên khác, giữ phiên đang dùng. **Đăng xuất mọi nơi** huỷ mọi phiên, kể cả phiên hiện tại.

**Admin đầu tiên** tạo bằng lệnh CLI trên máy chủ. Không có đường nào tự đăng ký làm admin.

**Gửi thư** qua port `Mailer`:
- bản `console` cho dev và test, ghi thư ra log, và test đọc lại được;
- bản `smtp` cho triển khai.
- Mẫu thư tiếng Việt: xác minh, đặt lại mật khẩu, "bạn đã có tài khoản", lời mời, bản dựng xong, bản dựng lỗi.

### 3. Phân quyền

**Quyết định chủ dự án 2026-10-28 — bảo vệ admin đầu tiên:** tài khoản admin đầu tiên được bảo vệ khỏi khoá quản trị (status disabled), hạ quyền khỏi admin và xoá, kể cả tự thao tác hoặc admin khác thao tác. Định danh được giữ bền vững phía server; không suy lại từ role/status/thứ tự danh sách hoặc tài khoản thường tạo sớm được nâng admin sau. Thao tác bị cấm phải từ chối nguyên tử. Hồ sơ/mật khẩu và bảo vệ xác thực hiện hành vẫn giữ. Chủ dự án nói “admin đầu tiên ko đc khóa hay gì”; [ADR 0030](adr/0030-bao-ve-tai-khoan-admin-dau-tien.md). Bản W-17.1 9cf405ac chưa thực hiện đúng nên chưa ghép; cách lưu/migration/DTO được đề xuất trong bản sửa.

**Một hàm thuần ở domain**, `decide(actor, action, course, membership) → allow | deny(code)`. Mọi dịch vụ gọi hàm này trước khi làm việc. Bảng luật:

| hành động | khách | chưa xác minh | thành viên | chủ khoá | admin |
|---|---|---|---|---|---|
| xem trang giới thiệu của link mời còn hiệu lực | ✓ | ✓ | ✓ | ✓ | ✓ |
| tham gia bằng link, tham gia khoá mẫu | – | ✓ | – | – | ✓ |
| tải sách lên, dựng | – | ✓ | ✓ | ✓ | ✓ |
| học: bài giảng, trợ lý, phiên, quiz, tài liệu, thư viện, tiến độ, mở tệp gốc, báo lỗi | – | nếu là thành viên | ✓ | ✓ | chỉ khi là thành viên |
| đổi tên, mô tả, xoá khoá; tạo, thu hồi link; xoá thành viên; xem tiến độ tổng hợp; xem báo lỗi của khoá | – | – | – | ✓ | – |
| mời theo email | – | – | – | ✓ (đã xác minh) | – |
| rời khoá | – | thành viên | ✓ | – (chủ khoá xoá khoá) | – |
| quản trị người dùng, bản dựng, chi, khoá mẫu, mọi báo lỗi | – | – | – | – | ✓ |

**Luật quan trọng:**
- **Người không phải thành viên nhận `not_found`, không phải `forbidden`,** cho mọi đường nội dung/quản lý khoá học, để không lộ khoá học riêng tư có tồn tại.
  Tham gia khoá mẫu là hành động cấp quyền đã nêu trong bảng trên: tài khoản đăng nhập được tham gia khoá mẫu ở dev, không cần có membership từ trước;
  `join-sample` nhắm khoá riêng tư vẫn trả `not_found`. Không bỏ route này khỏi test tự liệt kê.
- **Admin không có quyền học** trong khoá mình không tham gia, và **không có hàm nào** trả chat, tài liệu hay câu trả lời quiz của người khác. Admin chỉ
  thấy siêu dữ liệu và số liệu chi.
- **Mỗi khoá có đúng một chủ.** Chủ khoá cũng là thành viên, có tiến độ và phiên riêng như mọi người. Đồng chủ khoá và chuyển chủ để sau.
- **Tài khoản `disabled`** bị từ chối mọi hành động.

### 4. Tải sách lên và bản dựng

**Kiểm tệp lúc nhận** (0 USD, trước khi lưu lâu dài):
- định dạng theo byte đầu (magic bytes), không theo đuôi tệp: PDF hoặc DOCX;
- ≤ `upload_max_mb` (10) MB, bằng giới hạn cỡ tệp của gói Cloudinary miễn phí (chủ dự án chốt 2026-10-18; số đúng lấy ở trang gói của tài khoản); PDF ≤
  `build_max_pages` trang (mặc định không giới hạn); PDF không bị mã hoá.
  - Số đo ngày 2026-10-18: sáu cuốn phát triển ≤ 3,2 MB; 0/16 sách học của D-01 quá 10 MB (trung vị 1,9 MB); 11/20 sách mới quá 10 MB, phần lớn là bản
    quét, vốn bị từ chối ở bước đọc. Trần 10 MB vì vậy chủ yếu chặn bản quét. Lỗi `file_too_large` khuyên tách tài liệu theo chương;
- người tải phải tick xác nhận có quyền dùng và chia sẻ tài liệu (`rights_confirmed = true`);
- nếu trần lượt dựng đang bật (mặc định tắt): còn lượt trong tháng. Hết lượt thì từ chối ngay, trước khi nhận tệp: giao diện gọi `GET /me/usage` trước
  khi tải.
- Tệp lưu ở **Cloudinary**, chế độ riêng tư (`authenticated`), với `public_id` ngẫu nhiên trong thư mục của môi trường (mục 7); tên gốc chỉ là siêu dữ
  liệu. Máy chủ tải lên từ phía mình, sau khi kiểm xong; trình duyệt không tải thẳng lên Cloudinary.

**Dùng lại bản dựng (ADR 0020):** tính SHA-256 của tệp.
- Đã có bản dựng **thành công** cùng băm và cùng `pipeline_version` thì tạo khoá học trỏ ngay vào `doc_id` đó: 0 USD, không trừ lượt.
- Đang có bản dựng cùng băm chạy dở thì khoá học mới chờ chung bản dựng đó.

**`doc_id` của tệp tải lên:** `u-` cộng 20 ký tự hex đầu của băm. Không đặt trùng mẫu của sáu cuốn phát triển hay của tập giữ lại.

**Trạng thái bản dựng** `build-1`:

```json
{"contract_version": "build-1", "build_id": "…", "course_id": "…",
 "status": "reading | rejected | awaiting_confirmation | queued | running | succeeded | failed | cancelled",
 "step": "doc_reading | concepts | graph | learning_prep | null", "step_index": 2, "step_count": 4,
 "started_at": "…", "finished_at": null,
 "error": {"code": "ban_quet | ngon_ngu_khong_ho_tro | chu_loi | loi_mang | loi_noi_bo | het_tran_he_thong", "message": "…", "retryable": true}}
```

**Luồng:**
1. **Chọn tệp:** người dùng kéo thả PDF/DOCX; sau kiểm định dạng/cỡ tệp thì `awaiting_confirmation`. Chưa dựng sách.
2. **Xác nhận:** người tải bấm "Dựng lộ trình" thì `queued`, trừ một lượt dựng nếu trần lượt đang bật. Không xác nhận trong
   `confirmation_ttl_hours` (72) thì hết hạn, không trừ lượt.
3. **`reading`:** worker chạy bước đọc (`ingest`, 0 USD), rồi ba kiểm sớm:
   - **chất lượng chữ:** cổng `require_text_quality` của lõi từ chối (chữ vỡ, mã hoá font lạ) thì `rejected` với `chu_loi`. Web không bao giờ truyền
     `allow_text_quality_reason`; chỉ chủ dự án được quyết, như T-01a;
   - **bản quét:** trung bình ký tự chữ mỗi trang < `scan_min_chars_per_page` (150 sau hiệu chỉnh W-13: doc-6 là 179,8), hay > `scan_max_empty_page_ratio` (50%) số trang không có chữ, thì
     `rejected` với `ban_quet`;
   - **ngôn ngữ:** tỉ lệ ký tự có dấu tiếng Việt trên ký tự chữ < `vi_min_diacritic_ratio` thì `rejected` với `ngon_ngu_khong_ho_tro`. Ngưỡng chỉnh trên
     sáu cuốn phát triển cộng vài tệp tiếng Anh, ghi số đo vào báo cáo vé.
4. **`running`:** worker chạy lần lượt `concepts` (`label-roles` → A3/A3′ → A4/A5), `graph` (roadmap tới A10 và tên module), `learning_prep` (A12, chỉ mục khái niệm, ảnh công
   thức). Mỗi bước ghi `step`, và ghi chi thật vào sổ chi với `purpose = build`, `user_id`, `doc_id`.
5. **Xong:** `succeeded`; khoá học chuyển `ready` với `published_graph_version` = bản A10 hoàn tất mới nhất. Gửi email "bản dựng xong".

**Chủ dự án cập nhật 2026-10-19:** không cần tính dự toán hoặc hiện chi phí/thời gian ước lượng cho người tải. Usage, chi phí quy đổi từ token thực trả
và thời gian thực tế được ghi vào DB khi kết thúc lượt chạy (kể cả lỗi/huỷ); thiếu usage phải có cờ phân biệt. `--dry-run` là công cụ kiểm nội bộ 0 USD.
Yêu cầu cũ về `build_max_estimate_usd`/`qua_du_toan` được bỏ khỏi luồng và tiêu chí nghiệm thu web. Thủ tục dry-run/duyệt tiền nội bộ của các lượt thử
có tiền vẫn giữ nguyên; nhân viên chuẩn bị con số đề nghị riêng, không thêm lại chức năng dự toán trên app.

**Huỷ:** đặt cờ huỷ; worker dừng ở ranh giới bước kế tiếp (không giết giữa lời gọi). Chi đã tiêu vẫn ghi sổ. Lượt dựng không hoàn lại.

**Lỗi và thử lại:**
- `retryable = true` với `loi_mang` và `het_tran_he_thong`. `retry_build` chạy tiếp từ bước lỗi. Cache của Pha A làm các bước đã xong gần 0 USD.
- `loi_noi_bo` không tự thử lại; admin thấy ở danh sách bản dựng.

**Worker chết giữa chừng:** mỗi bản dựng `running` có nhịp tim. Quá `build_heartbeat_timeout_minutes` (10) không có nhịp tim thì một worker khác nhận lại,
tối đa 1 lần; lần sau thì `failed` với `loi_noi_bo`.

**Trần chi khâu dựng — có trong mã, mặc định tắt.** Chủ dự án chốt 2026-10-18: "chỉ là web demo, không cần giới hạn"; cập nhật 2026-10-19 bỏ dự toán. Hai trần dưới đây cài đủ và có
test (test bật chúng bằng cấu hình), để bật lại bằng một biến môi trường nếu có lạm dụng:
- `build_monthly_max` lượt mỗi tài khoản mỗi tháng lịch theo giờ Việt Nam; admin đổi riêng cho từng người;
- `system_daily_build_max_usd`: tổng chi khâu dựng của cả hệ thống mỗi ngày. Chạm trần thì bản dựng mới chờ ở `queued` tới ngày sau; bản đang chạy
  dừng ở ranh giới bước với `het_tran_he_thong`, thử lại được.
Hai trần này **tách** khỏi trần người học (1,00 USD theo ADR 0026) và trần nội dung dùng chung (5 USD).

**Dựng một cuốn ở lõi** là một use case mới, `build_document`, gói chuỗi lệnh hiện có thành từng bước có thể dry-run và chạy tiếp:
- nhận đường dẫn tệp, `doc_id`, ngôn ngữ `vi`, và một hàm báo tiến trình;
- **chạy không cần bộ vàng.** Chế độ sản phẩm không đọc tệp vàng nào. Nếu A4 hiện chưa cho làm vậy, vé ghi yêu cầu sang phiên pha A, không tự sửa tệp của
  phiên đó;
- bản dựng đọc chuỗi mặc định hiện hành (chuỗi gộp) và ghi `pipeline_version` (commit, phiên bản cấu hình) vào bản ghi bản dựng;
- port `BuildRunner` để test web dùng **bộ dựng giả**: chép artifact sẵn có của một cuốn phát triển sang `doc_id` mới, báo đủ bốn bước, 0 USD.

### 5. Khoá học

**Bản ghi khoá học:** `course_id`, `owner_id`, `doc_id`, `title` (mặc định từ tiêu đề tài liệu hay tên tệp, ≤ 120 ký tự), `description` (≤ 1.000 ký tự),
`status ∈ {building, ready, failed}`, `published_graph_version`, `is_sample`, `created_at`.

**`list_my_courses`** trả ba nhóm: `owned`, `joined`, `samples` (khoá mẫu chưa tham gia). Mỗi mục có:
- `course_id`, `title`, `status`, `role`, tên chủ khoá, số module, số thành viên (chỉ chủ khoá thấy);
- tóm tắt tiến độ "xong x/y" của chính người hỏi, lấy từ `get_progress`;
- `resume`: module mở gần nhất của người hỏi, suy từ phiên và tiến độ gần nhất. Không có thì module 1.

**Xoá khoá** (chỉ chủ khoá, phải gõ lại tên khoá để xác nhận):
- xoá khoá học, thành viên, link, lời mời;
- **giữ** dữ liệu học của từng người (khoá theo người × cuốn, ADR 0020). Người đó gặp lại dữ liệu nếu sau này vào một khoá khác của cùng cuốn;
- giữ tệp và artifact của bản dựng khi còn khoá học khác trỏ vào cùng `doc_id`. Không còn khoá nào thì đánh dấu để admin dọn bằng lệnh; không tự xoá (Q6
  của Pha B2).

**Phát hành phiên bản mới:** khoá học ghim `published_graph_version`. Đồ thị của `doc_id` lên bản mới (dựng lại) **không** tự đổi khoá học; chủ khoá bấm
"Phát hành bản mới". Phạm vi phiên tự giải sang bản mới theo Jaccard (ADR 0017), tiến độ giữ nguyên vì khoá theo `node_id`. Chức năng dựng lại để vé sau.

**Khoá mẫu — chỉ ở dev** (chủ dự án chốt 2026-10-18). Lệnh tạo khoá mẫu từ chối chạy khi `env` không phải `dev`; bản demo không có khoá mẫu, nhóm
`samples` rỗng thì giao diện ẩn nhóm. Ở dev, admin đánh dấu `is_sample`; mọi tài khoản thấy ở nhóm `samples` và tham gia bằng một nút, không cần link. Lệnh tạo khoá mẫu chỉ nhận **sáu cuốn
phát triển** (doc-1, nhap-mon-ml, naive-bayes, doc-6, xstk-ch3-1, doc-4), theo danh sách cho phép trong mã; mọi `doc_id` khác bị từ chối.

### 6. Chia sẻ

**Link mời:**
- Chủ khoá tạo link: `expires_in_days` (mặc định `share_link_default_days` = 7; hoặc "không hết hạn"), `max_uses` (mặc định không giới hạn), vai trò cấp
  là `learner`.
- Token 32 byte ngẫu nhiên trong URL `/join/<token>`; cơ sở dữ liệu chỉ lưu băm. **Link chỉ hiện đủ một lần lúc tạo**; danh sách link chỉ hiện 6 ký tự
  cuối, ngày tạo, hạn, số lượt đã dùng, trạng thái.
- `preview_share_link` (khách cũng gọi được): trả tên khoá, tên chủ khoá, số module, số khái niệm. Link không hợp lệ, hết hạn, đã thu hồi hay hết lượt đều
  trả một lỗi chung `link_invalid`, không nói lý do cụ thể.
- `join_by_link` cần đăng nhập. Đã là thành viên thì trả thành công, không tính thêm lượt. Khoá đã đủ `course_max_members` (200) thì `course_full`.
- Thu hồi có hiệu lực ngay; thành viên đã vào **không** bị xoá theo.

**Mời theo email:**
- Chủ khoá nhập tối đa `invite_batch_max` (50) email mỗi lần.
- Email đã có tài khoản: tạo lời mời `pending`, hiện ở trang chủ của người đó, và gửi email báo.
- Email chưa có tài khoản: gửi email kèm link đăng ký mang token mời. Đăng ký **và xác minh** đúng email đó thì lời mời tự hiện, chờ chấp nhận.
- Lời mời hết hạn sau `invite_ttl_days` (7). Chủ khoá huỷ được lời mời đang chờ.
- Giới hạn gửi: `invite_emails_per_day` (200) mỗi chủ khoá mỗi ngày, chống dùng hệ thống để gửi thư rác.

**Thông báo dữ liệu khi tham gia:** màn hình tham gia ghi rõ chủ khoá thấy gì: tên hiển thị, ngày tham gia, lần học gần nhất, số khái niệm đã đánh dấu theo
module; **không** thấy chat, tài liệu, câu trả lời quiz.

**Thành viên:**
- `list_members`: chủ khoá thấy mọi thành viên `{user_id, display_name, joined_at, last_active_at, via ∈ {owner, link, email, sample}}`. Thành viên thường chỉ
  thấy tên chủ khoá và số thành viên.
- `remove_member`: chủ khoá xoá; người bị xoá mất quyền ngay, kể cả stream đang mở (lần gọi sau bị từ chối). Dữ liệu học của họ giữ như mục 5.
- `leave_course`: thành viên tự rời; vào lại bằng link mới thì gặp lại dữ liệu cũ.

**Tiến độ tổng hợp cho chủ khoá** (`members_progress`): mỗi thành viên, mỗi module `{learned, total}` theo đồ thị đã phát hành, cộng `last_active_at`. Không
có trường nào khác. Chủ dự án chốt 2026-10-18: **bật**, kèm thông báo dữ liệu khi tham gia.

### 7. Học trong khoá học

**Ánh xạ sang Pha B:** `owner = user_id`, `doc_id = course.doc_id`, `graph_version = course.published_graph_version`. Dữ liệu học (phiên, lượt, tiến độ,
tài liệu, lần làm quiz) vì vậy khoá theo **người × cuốn** (ADR 0020).
- Một người ở hai khoá của cùng một cuốn thấy chung tiến độ, phiên và thư viện. Giao diện ghi chú điều này ở trang khoá học khi xảy ra.

**Nội dung dùng chung:** bài giảng và ngân hàng quiz cache theo nội dung (ADR 0011), nên mọi thành viên của mọi khoá cùng `doc_id` và cùng phiên bản đồ
thị dùng chung. Nhãn theo người học vẫn gắn lúc đọc (ADR 0019).

**Tệp gốc và ảnh trên Cloudinary** ([ADR 0023](adr/0023-cloudinary-cho-tep-goc-va-anh.md); chủ dự án chốt 2026-10-18):
- **Cloudinary giữ:** tệp gốc PDF, DOCX; ảnh hiện cho người học, gồm ảnh công thức, media đã xác nhận, ảnh trang. **Đĩa máy chủ giữ:** artifact Pha A
  (đồ thị, chunk, vector).
- **Mọi tài sản đều riêng tư** (`authenticated`). Thư mục theo môi trường: `wayfinder/<env>/uploads/…`, `wayfinder/<env>/media/<doc_id>/…`.
- **Trình duyệt không bao giờ nhận link Cloudinary dùng lâu được.** Link có chữ ký của Cloudinary chống sửa link nhưng không tự hết hạn; link hết hạn theo
  thời gian (token) là tính năng gói cao. Vì vậy:
  - **ảnh trang và ảnh công thức, media:** máy chủ kiểm thành viên, lấy ảnh từ Cloudinary bằng link ký phía máy chủ, rồi chuyển cho trình duyệt với
    `Cache-Control: private, max-age=300`;
  - **mở cả tệp:** máy chủ kiểm thành viên rồi chuyển hướng (302) tới link tải riêng tư của Cloudinary có `expires_at` = bây giờ + `signed_url_ttl_seconds`
    (300).
- **"Đọc trang p"** (`open_source_page`): ảnh của đúng trang p, do Cloudinary cắt từ PDF (tham số trang, định dạng WebP, rộng `page_image_width` = 1.400
  px). Kèm nút phụ "Mở cả tệp" (`open_source_file`).
  - Trang p lấy từ `failure.read_page.page` hay từ trích dẫn; p ngoài khoảng 1…số trang thì `not_found`.
  - Tệp DOCX không có trang: nút báo "tài liệu không có trang", chỉ còn "Mở cả tệp".
- **Bài giảng trong cache chỉ chứa khoá tài sản** (`asset_key`), không chứa URL. Gateway đổi khoá thành đường của máy chủ (`/courses/{cid}/media/…`) lúc trả
  bài, như cách gắn nhãn theo người học.
- **Ảnh công thức và media** được tải lên Cloudinary ở cuối bước `learning_prep` của bản dựng, và ở lệnh tạo khoá mẫu.
- **Tín dụng của gói miễn phí:** ảnh trang là ảnh phái sinh, tính tín dụng ở lần tạo đầu, rồi Cloudinary giữ lại. Máy chủ chỉ xin đúng một cỡ ảnh mỗi
  trang, để không sinh nhiều bản phái sinh.

**Báo lỗi nội dung:** `report_content(target_kind ∈ {lecture, answer, quiz_item, document}, target_id, reason ∈ {sai_noi_dung, sai_trich_dan, kho_hieu,
khac}, note ≤ 500 ký tự)`. Câu quiz dùng lại `report_question` có sẵn. Mỗi báo lỗi lưu `lecture_key` hay mã đối tượng để nhóm phát triển tìm lại đúng
bản. Chủ khoá xem báo lỗi của khoá mình; admin xem tất cả.

**Giới hạn tần suất thêm** (ngoài trần tiền của Pha B2): `assistant_turns_per_minute` (10) mỗi người, `documents_per_hour` (10) mỗi người. Vượt thì
`rate_limited`.

### 8. Mức dùng và trần chi

**Bốn trần:**

| trần | giá trị mặc định | tính trên | khi chạm |
|---|---|---|---|
| người học mỗi ngày (ADR 0026 cập nhật Pha B2) | 1,00 USD | trợ lý, tài liệu của người đó, **mọi khoá** | `daily_limit`, vẫn dùng mọi thứ 0 USD |
| nội dung dùng chung mỗi ngày (Pha B2 mục 8) | 5,0 USD | bài giảng, sinh và kiểm quiz | bài giảng `tran_he_thong`; quiz dùng ngân hàng có sẵn |
| lượt dựng mỗi tài khoản mỗi tháng (mới) | **tắt** (bản demo) | bản dựng có chi (không tính bản dùng lại) | từ chối tải lên, `quota_exceeded` |
| khâu dựng toàn hệ thống mỗi ngày (mới) | **tắt** (bản demo) | `purpose = build` | bản dựng chờ, hay dừng ở ranh giới bước |

"Ngày" và "tháng" tính theo `spend_day_timezone` (Asia/Ho_Chi_Minh), như Pha B2.

**`my_usage`** trả cho người dùng:

```json
{"contract_version": "usage-1",
 "learner_today": {"used_ratio": 0.35, "resets_at": "2026-10-19T00:00:00+07:00", "limited": false},
 "builds_this_month": {"used": 1, "max": 3, "resets_at": "2026-11-01T00:00:00+07:00"},
 "shared_content_today": {"limited": false}}
```

- **Người dùng thường thấy tỉ lệ, không thấy USD.** Admin thấy USD.
- Hết trần thì giao diện hiện một dải thông báo cố định với giờ đặt lại.

**`spend_summary`** (admin): chi theo ngày × `purpose`, theo khoá học, và 20 tài khoản chi nhiều nhất, trong khoảng ngày chọn; kèm số lời gọi, p50, p90
giây. Nguồn là sổ chi; số này là **ước theo token**, không thay hoá đơn của nhà cung cấp.

### 9. Quản trị

- **Admin đầu tiên:** không được khoá, hạ quyền hoặc xoá theo quyết định 28/10 và ADR 0030; bảo vệ ở server, không chỉ ẩn nút React.

- **Người dùng:** tìm theo email; xem ngày tạo, lần đăng nhập gần nhất, số khoá sở hữu, lượt dựng tháng này; khoá hay mở tài khoản; đổi `build_monthly_max`
  riêng; nâng hay hạ vai trò admin (không tự hạ mình nếu là admin cuối cùng).
- **Bản dựng:** danh sách mọi bản dựng, lọc theo trạng thái; usage/chi phí thực quy đổi từ token, cờ thiếu usage, lỗi, `pipeline_version`; thử lại hay huỷ thay chủ khoá.
- **Chi:** `spend_summary`, trần hệ thống hôm nay.
- **Báo lỗi nội dung:** danh sách, lọc theo khoá học, đánh dấu đã xem.
- **Khoá mẫu:** đánh dấu và bỏ đánh dấu.
- **Nhật ký** (mục 10): xem, lọc theo người, theo loại.

### 10. An ninh

- **Tải tệp:** kiểm như mục 4; tên tệp ngẫu nhiên; không bao giờ phục vụ tệp theo đường dẫn do người dùng gửi.
- **Phản hồi HTTP:** `Content-Security-Policy` chặt cho trang React, `X-Content-Type-Options: nosniff`, `Referrer-Policy: same-origin`, không phục vụ
  stack trace. Lỗi nội bộ trả `internal_error` kèm mã tra cứu; chi tiết chỉ ở log.
- **CORS:** chỉ `allowed_origins`; mặc định cùng nguồn (React phục vụ cùng tên miền với API).
- **Nhật ký thao tác** `audit_event`: đăng nhập thành công, đăng nhập sai, khoá tài khoản do sai nhiều lần, đổi và đặt lại mật khẩu, đăng xuất mọi nơi, xoá
  tài khoản, tạo và thu hồi link, mời, xoá thành viên, xoá khoá, mọi thao tác admin. Mỗi dòng có thời gian, người làm, IP, đối tượng, không có mật khẩu hay
  token.
- **Log** không ghi câu hỏi, câu trả lời, nội dung tài liệu; chỉ ghi mã đối tượng và số đo.
- **Tập giữ lại:** máy chủ web không bao giờ nạp `d01-t01`, `d01-t02`, `document-data/test/`. Khoá mẫu chỉ nhận sáu cuốn phát triển. Bản dựng của tệp tải
  lên có `doc_id` dạng `u-…`, không trùng tên nào ở trên.
- **Chèn lệnh từ tài liệu:** xem mục 1, công cụ buộc phía máy chủ.

### 11. API HTTP

Mọi đường dưới `/api/v1`. Thân yêu cầu và phản hồi là JSON, trừ tải tệp (multipart), tệp gốc (PDF) và stream (SSE).

**Lỗi** có một khuôn: `{"error": {"code": "…", "message": "câu tiếng Việt", "retry_after": 30, "ref": "…"}}`. Mã ổn định:

| mã | HTTP | khi nào |
|---|---|---|
| `unauthenticated` | 401 | chưa đăng nhập, phiên hết hạn |
| `invalid_credentials` | 401 | sai email hay mật khẩu |
| `account_disabled` | 403 | tài khoản bị khoá |
| `email_unverified` | 403 | cần xác minh email |
| `forbidden` | 403 | thành viên nhưng không đủ quyền (ví dụ thành viên thường tạo link) |
| `csrf_failed` | 403 | thiếu hay sai `X-CSRF-Token`, sai `Origin` |
| `not_found` | 404 | không có, **hoặc không phải thành viên** |
| `conflict` | 409 | ví dụ đã là thành viên khi chấp nhận lời mời đã huỷ |
| `validation` | 422 | trường sai, kèm `fields` |
| `file_invalid`, `file_too_large`, `too_many_pages`, `file_encrypted` | 422 | tải tệp |
| `link_invalid`, `course_full` | 410, 409 | tham gia bằng link |
| `rate_limited` | 429 | vượt giới hạn tần suất, kèm `retry_after` |
| `quota_exceeded` | 429 | hết lượt dựng, kèm `retry_after` tới đầu tháng |
| `owns_shared_courses` | 409 | xoá tài khoản khi còn khoá có thành viên khác |
| `internal_error` | 500 | kèm `ref` |

`daily_limit` của trợ lý **không** phải lỗi HTTP: nó là status trong answer-3, HTTP 200.

**Điểm cuối:**

| nhóm | phương thức và đường | ghi chú |
|---|---|---|
| tài khoản | `POST /auth/register`, `POST /auth/verify-email`, `POST /auth/resend-verification`, `POST /auth/login`, `POST /auth/logout`, `POST /auth/logout-all`, `POST /auth/password-reset/request`, `POST /auth/password-reset/confirm` | đăng ký và đăng nhập đặt cookie |
| hồ sơ | `GET /me` (kèm `csrf_token`), `PATCH /me`, `POST /me/password`, `DELETE /me` (cần mật khẩu), `GET /me/usage`, `GET /me/invitations` | |
| tải và dựng | `POST /uploads` (multipart: `file`, `rights_confirmed`), `GET /uploads/{id}`, `POST /uploads/{id}/build`, `GET /builds/{id}`, `POST /builds/{id}/cancel`, `POST /builds/{id}/retry` | giao diện hỏi `GET /builds/{id}` mỗi 3 giây |
| khoá học | `GET /courses`, `GET /courses/{cid}`, `PATCH /courses/{cid}`, `DELETE /courses/{cid}`, `POST /courses/{cid}/join-sample` | |
| chia sẻ | `POST/GET /courses/{cid}/share-links`, `DELETE /courses/{cid}/share-links/{lid}`, `GET /join/{token}` (khách được), `POST /join/{token}`, `POST/GET /courses/{cid}/invitations`, `DELETE /courses/{cid}/invitations/{iid}`, `POST /invitations/{iid}/accept`, `POST /invitations/{iid}/decline`, `GET /courses/{cid}/members`, `DELETE /courses/{cid}/members/{uid}`, `POST /courses/{cid}/leave`, `GET /courses/{cid}/members/progress` | |
| học | `GET /courses/{cid}/roadmap`, `GET /courses/{cid}/concepts/{node_id}/lecture`, `GET /courses/{cid}/concepts/{node_id}/lecture/stream` (SSE), `GET /courses/{cid}/progress`, `PUT /courses/{cid}/progress/{node_id}`, `GET/POST /courses/{cid}/sessions`, `PATCH/DELETE /courses/{cid}/sessions/{sid}`, `GET /courses/{cid}/sessions/{sid}/turns`, `POST /courses/{cid}/sessions/{sid}/turns` (SSE), `POST /courses/{cid}/quizzes`, `POST /courses/{cid}/quizzes/{aid}/submit`, `POST /courses/{cid}/documents`, `GET /courses/{cid}/documents/{did}`, `GET /courses/{cid}/library?scope=roadmap\|module:<id>\|all`, `GET /courses/{cid}/source/pages/{p}` (ảnh trang, máy chủ chuyển), `GET /courses/{cid}/source` (302 tới link tải có hạn), `GET /courses/{cid}/media/{asset_key}` (máy chủ chuyển), `POST /courses/{cid}/reports` | trả hợp đồng Pha B, thêm `course_id` |
| quản trị | `GET /admin/users`, `PATCH /admin/users/{uid}`, `GET /admin/builds`, `POST /admin/builds/{id}/retry`, `GET /admin/spend`, `GET /admin/reports`, `PATCH /admin/reports/{id}`, `PATCH /admin/courses/{cid}` (`is_sample`), `GET /admin/audit` | chỉ admin |
| hệ thống | `GET /health` | không cần đăng nhập |

**Đề quiz** trả cho trình duyệt **không có đáp án**, như vé 24. Đáp án chỉ có trong phản hồi của `submit`.

**Một mô tả OpenAPI** sinh từ FastAPI là tài liệu chuẩn cho nhóm React; vé đầu tiên kiểm nó sinh được và có trong repo.

### 12. Cấu hình mới `WebSettings`

| khoá | mặc định |
|---|---|
| `allowed_origins` | cùng nguồn |
| `session_idle_days` / `session_absolute_days` | 7 / 30 |
| `login_max_failures` / `login_failure_window_minutes` | 5 / 15 |
| `email_verify_ttl_hours` / `resend_verification_per_hour` | 24 / 3 |
| `password_reset_ttl_minutes` | 60 |
| `upload_max_mb` / `build_max_pages` | 10 (gói Cloudinary miễn phí) / không giới hạn |
| `scan_min_chars_per_page` / `scan_max_empty_page_ratio` | 150 / 0,5 (hiệu chỉnh W-13, 2026-10-19) |
| `vi_min_diacritic_ratio` | chỉnh trên dữ liệu ở vé dựng |
| `build_monthly_max` | không giới hạn (gợi ý khi bật: 3) |
| `system_daily_build_max_usd` | không giới hạn (gợi ý khi bật: 10,0) |
| `env` | `dev` \| `prod`; khoá mẫu chỉ khi `dev` |
| `smtp_*` | Gmail SMTP (`smtp.gmail.com`, cổng 587, STARTTLS) với mật khẩu ứng dụng; chỉ ở `.env` |
| `confirmation_ttl_hours` | 72 |
| `build_heartbeat_timeout_minutes` | 10 |
| `share_link_default_days` | 7 |
| `course_max_members` | 200 |
| `invite_batch_max` / `invite_ttl_days` / `invite_emails_per_day` | 50 / 7 / 200 |
| `assistant_turns_per_minute` / `documents_per_hour` | 10 / 10 |
| `mailer` | `console` (dev), `smtp` (triển khai) |
| `artifact_root` | thư mục artifact Pha A trên đĩa, ngoài repo, cấu hình bằng biến môi trường |
| `cloudinary_url` | biến môi trường `CLOUDINARY_URL` (`cloudinary://<api_key>:<api_secret>@<cloud_name>`); chỉ ở `.env`, không bao giờ commit hay dán vào chat |
| `cloudinary_folder` | `wayfinder/<env>` (`dev`, `prod`) |
| `signed_url_ttl_seconds` | 300 |
| `page_image_width` | 1.400 |

Các trần Pha B (1,00 USD theo ADR 0026, 5 USD nội dung dùng chung) ở `BSettings`.

**Cấu hình Gemini dùng lại từ `Settings` lõi**, không thêm bộ khoá trùng trong `WebSettings`: tạm dùng `DOC2ROADMAP_LLM_TRANSPORT=vertex`,
`DOC2ROADMAP_VERTEX_PROJECT`, `DOC2ROADMAP_VERTEX_LOCATION` và ADC phía máy chủ. API/worker dùng cùng cấu hình; chỉ chuyển sang `developer_api` và
`DOC2ROADMAP_GEMINI_API_KEY` khi chủ dự án yêu cầu chuẩn bị demo, theo mục 1.

### 13. Lưu trữ (mức khái niệm; chi tiết ở spec cơ sở dữ liệu)

- **PostgreSQL** cho dữ liệu web và cho **kho Pha B**. Bản cài kho Pha B trên PostgreSQL qua **cùng bộ test hợp đồng** với bản JSON và bản bộ nhớ.
- **`single_flight` liên tiến trình:** bản PostgreSQL khoá bằng advisory lock theo băm của khoá cache, để hai worker web cùng sinh một bài thì chỉ một
  lời gọi mô hình.
- **Artifact Pha A** (đồ thị, chunk, vector) **giữ ở kho tệp trên đĩa** có phiên bản như hiện tại; cơ sở dữ liệu chỉ lưu `doc_id` và phiên bản.
- **Tệp tải lên và ảnh** ở **Cloudinary** (mục 7, ADR 0023), sau một port `MediaStore`; test dùng bản giả trong bộ nhớ. Worker tải tệp gốc về thư mục tạm
  bằng link ký phía máy chủ trước khi dựng, rồi xoá bản tạm.
- **Hàng đợi bản dựng** là bảng trong PostgreSQL; worker nhận việc bằng khoá hàng `SKIP LOCKED`.
- **Thực thể web:** tài khoản, phiên đăng nhập, token email, khoá học, thành viên, link mời, lời mời, tệp tải lên, bản dựng, báo lỗi nội dung, nhật ký thao
  tác, sổ chi (dùng chung với Pha B, thêm `purpose = build`).
- **Không nhập** `artifacts/phase_b/live.json` vào cơ sở dữ liệu: kho đó có cache của tập giữ lại. Bản triển khai bắt đầu rỗng, cộng khoá mẫu.

---

## Quyết định kiểm thử

**Thế nào là một test tốt:** như spec Pha B.
- Kiểm hành vi nhìn từ ngoài: phản hồi của dịch vụ, bản ghi trong kho, thư đã gửi, số lời gọi mô hình, mã lỗi.
- Mỗi bất biến có một test được thấy đỏ trước trên bản sai.
- Không dùng tập giữ lại; không gọi mạng; 0 USD.

**Đường nối kiểm thử — ba tầng, chính là tầng dịch vụ:**
1. **Tầng dịch vụ (đường nối chính).** Gọi thẳng các dịch vụ ở mục 1 với kho trong bộ nhớ, đồng hồ giả, `Mailer` giả (giữ thư để đọc), `BuildRunner` giả,
   và Pha B thật chạy trên ba đồ giả sẵn có (mô hình theo kịch bản, embedding giả, kho bộ nhớ). Hầu hết test ở đây.
2. **Tầng HTTP, mỏng.** `TestClient` của FastAPI, chỉ cho những thứ sống ở HTTP: cờ cookie, CSRF, mã HTTP của bảng lỗi, khung SSE, `429` kèm
   `retry_after`, header khi trả tệp gốc.
3. **Tầng lưu trữ:** mỗi port lưu trữ có một bộ test hợp đồng chạy trên bản bộ nhớ và bản PostgreSQL, như kho Pha B chạy trên bản JSON và bản bộ nhớ hôm
   nay.

Thêm một **bộ thử đầu-cuối nhỏ trên trình duyệt** (Playwright) cho vài luồng chính, chạy ở vé triển khai, không thay cho ba tầng trên.

**Bất biến phải có test**, mỗi cái thấy đỏ trước:
1. Một test **tự liệt kê mọi route** có `{cid}`, nhắm một **khoá riêng tư** bằng tài khoản không phải thành viên, và kỳ vọng `not_found`,
   gồm cả `join-sample`. Route mới thêm tự được kiểm. Test riêng chứng minh người đăng nhập chưa tham gia được `join-sample` với khoá mẫu ở dev;
   không cấp quyền này cho khách chưa đăng nhập hoặc khoá riêng tư. Đây là hai ngữ cảnh khác nhau, không phải miễn route khỏi bộ kiểm.
2. `owner` và `doc_id` gửi tới Pha B luôn là của phiên đăng nhập và khoá học; thân yêu cầu có `owner` lạ thì bị bỏ qua. Kiểm bằng kho: bản ghi mới có
   `owner` đúng.
3. Hai thành viên mở cùng một bài giảng: tổng cộng **1** lời gọi mô hình; `lecture_key` giống nhau; nhãn `learner_status` khác nhau theo tiến độ.
4. Thành viên B không đọc được phiên, lượt, thư viện, tiến độ của thành viên A cùng khoá; chủ khoá cũng không đọc được chat của thành viên.
5. Admin không có hàm nào trả lượt chat của người khác: test duyệt mọi hàm của `AdminService` và `UsageService`, kiểm phản hồi không có trường câu hỏi hay
   câu trả lời.
6. Link thu hồi, hết hạn, hay hết lượt đều bị từ chối với cùng mã `link_invalid`; cơ sở dữ liệu không có token thô (quét bảng tìm chuỗi token).
7. Mật khẩu lưu dạng Argon2id; đăng nhập sai trả `invalid_credentials` giống nhau cho email có và không có; lần sai thứ 6 trong 15 phút trả `rate_limited`.
8. Token đặt lại dùng hai lần thì lần hai bị từ chối; quá 60 phút theo đồng hồ giả thì bị từ chối; đặt lại xong thì mọi phiên cũ hết hiệu lực.
9. Đổi mật khẩu huỷ phiên khác, giữ phiên hiện tại.
10. Chưa xác minh email thì mời theo email bị `email_unverified`; tải sách, tạo link, tham gia bằng link thì được.
11. Cấu hình mặc định: tải và dựng nhiều cuốn liền không bị chặn. Bật `build_monthly_max = 3` trong test: lượt thứ 4 bị `quota_exceeded` trước khi worker
    chạy bước nào; sang tháng mới theo đồng hồ giả thì được.
12. Cùng một tệp tải hai lần (hai tài khoản): bản dựng thứ hai không gọi `BuildRunner`, 0 USD, không trừ lượt, và hai khoá trỏ cùng `doc_id`.
13. Bản quét và tài liệu không phải tiếng Việt bị `rejected` sau bước đọc, 0 lời gọi mô hình. Test dùng hai tệp nhỏ tạo trong test: một PDF chỉ có ảnh,
    một PDF chữ tiếng Anh.
14. Khi bật trần khâu dựng toàn hệ thống trong test: chạm trần thì bản dựng mới không chạy. Luồng tải/xác nhận và API người dùng không có dự toán/chi phí;
    kết quả thực của lượt chạy vẫn được ghi DB cho admin, kể cả lỗi/huỷ và cờ thiếu usage.
15. Huỷ trong lúc `running` thì dừng ở ranh giới bước kế tiếp; worker giả ghi lại không có bước nào bắt đầu sau khi có cờ huỷ.
16. Worker mất nhịp tim quá 10 phút theo đồng hồ giả thì bản dựng được nhận lại đúng 1 lần.
17. Trần người học tính chung mọi khoá: chi ở khoá A làm khoá B chạm `daily_limit`.
18. `single_flight` liên tiến trình: hai tiến trình cùng xin một bài trên bản PostgreSQL thì chỉ một lần sinh (test của bản PostgreSQL).
19. Xoá thành viên thì lần gọi kế tiếp của người đó bị `not_found`; dữ liệu học của họ vẫn còn trong kho; tham gia lại thì thấy lại.
20. Xoá tài khoản khi còn khoá có thành viên khác thì `owns_shared_courses`. Xoá được thì kho Pha B không còn bản ghi nào có `owner` là người đó, và sổ chi
    giữ số tiền nhưng thay `learner_id` bằng `deleted`.
21. Khoá mẫu chỉ tạo được từ sáu cuốn phát triển và chỉ khi `env = dev`; một `doc_id` giả mang tên giống tập giữ lại bị từ chối (bí mật giả, không dùng
    tên thật).
22. Mọi yêu cầu đổi dữ liệu thiếu `X-CSRF-Token` hay sai `Origin` bị `csrf_failed` (tầng HTTP, liệt kê mọi route không phải GET).
23. Đề quiz trả cho trình duyệt không có đáp án (tầng HTTP).
24. Test kiến trúc: domain và application không import FastAPI, SQLAlchemy, thư viện băm mật khẩu, SDK Cloudinary.
25. Không phản hồi JSON nào gửi trình duyệt chứa tên miền Cloudinary hay `public_id` (quét đệ quy mọi chuỗi), trừ chuyển hướng 302 của "Mở cả tệp" có
    `expires_at`. Cache bài giảng không chứa URL nào.
26. Ảnh trang, ảnh công thức, "Mở cả tệp" bởi người ngoài khoá thì `not_found`, và `MediaStore` giả ghi nhận 0 lần lấy từ Cloudinary.
27. Composition API/worker theo cấu hình tạm thời truyền `vertex` tới mô hình sinh và embedding, kể cả đường dựng sách; không đòi Gemini API key.
    Thiếu project/xác thực Vertex bị chặn trước lời gọi mô hình, không tự chuyển sang Developer API. Dùng bản giả xác thực và mô hình, không gọi mạng;
    thấy đỏ khi truyền nhầm transport hoặc bỏ kiểm cấu hình. Việc chuyển sang Developer API chờ chỉ thị riêng của chủ dự án.

**Tiền lệ trong repo:**
- test dịch vụ Pha B ở mức use case (trợ lý, bài giảng, quiz, phiên, tiến độ, thư viện);
- test hợp đồng kho Pha B cho hai bản cài;
- test trang xem thử (máy chủ HTTP thật trên localhost, kiểm Host và Origin, đề quiz không đáp án);
- test kiến trúc tầng;
- đồng hồ giả của Pha B2.

**Lượt có tiền:** chỉ ở vé nối bộ dựng thật. Chạy trên một cuốn phát triển đã có cache (doc-6, lần trước ≈ 0,007 USD). Dry-run trước, chủ dự án duyệt.

---

## Ngoài phạm vi

- **Đăng nhập bằng Google hay bên thứ ba khác.** Có thể thêm sau; thiết kế phiên ở ADR 0021 không cản.
- **Xác thực hai lớp (2FA).**
- **Đồng chủ khoá, chuyển chủ khoá, vai trò trợ giảng.**
- **Danh mục khoá học công khai** ngoài khoá mẫu do admin chọn.
- **Khoá học gồm nhiều tài liệu.** Một khoá là một tài liệu, vì Pha A dựng theo từng tài liệu.
- **Chia sẻ tài liệu hay quiz cá nhân cho cả lớp;** chủ khoá giao bài tập.
- **Thanh toán, gói trả phí.**
- **Thông báo trong ứng dụng dạng chuông,** thông báo đẩy. Chỉ có email và danh sách lời mời ở trang chủ.
- **Đọc bản quét bằng OCR.** Bản quét bị từ chối có lý do rõ.
- **Ứng dụng di động.** Web phải dùng được trên màn hình điện thoại (spec thiết kế giao diện).
- **Xuất dữ liệu cá nhân.**
- **Tải thẳng từ trình duyệt lên Cloudinary** (unsigned upload), **link Cloudinary hết hạn bằng token** (tính năng gói cao), **gói Cloudinary trả phí**.
- **Dựng lại và phát hành bản mới:** có trong thiết kế (mục 5), nhưng vé để sau.

## Quyết định của chủ dự án (2026-10-18)

Bảy câu hỏi mở của bản đầu đã được chủ dự án trả lời ngày 2026-10-18:

1. **Ai được tải sách lên:** bất kỳ ai đã đăng nhập, không cần xác minh email. "Chỉ là web demo, không cần giới hạn."
2. **Trần khâu dựng:** không giới hạn ở bản demo. Ba trần vẫn cài sẵn, mặc định tắt (mục 4). W-15 vẫn đo USD/cuốn thật, để biết bật ở mức nào khi cần.
3. **Chủ khoá xem tiến độ tổng hợp của thành viên:** có, báo trước khi tham gia (mục 6).
4. **Xác minh email để học:** không bắt buộc. Chỉ mời theo email mới cần xác minh.
5. **Khoá mẫu từ sáu cuốn phát triển:** chỉ ở dev; bản demo không có khoá mẫu.
6. **Thành viên mở tệp PDF gốc:** có. "Đọc trang p" mở ảnh của đúng trang; "Mở cả tệp" là nút phụ, qua link tải có hạn (mục 7).
7. **Gửi thư:** Gmail SMTP với mật khẩu ứng dụng. Gmail giới hạn khoảng 500 thư mỗi ngày; đủ cho demo.
8. **Cloudinary:** một tài khoản cho dev và demo, tách bằng thư mục `wayfinder/dev` và `wayfinder/prod`.
9. **Gemini cho backend web** (cập nhật trong chat điều phối 2026-10-19, thay quyết định ngày 2026-10-18): FastAPI và worker tạm dùng Vertex AI;
   khi chuẩn bị demo chủ dự án sẽ chỉ thị chuyển sang Gemini Developer API. Chi tiết cấu hình và kiểm thử ở mục 1, 12.

**Việc chủ dự án làm trên tài khoản:**
- Cloudinary:
  - đặt `CLOUDINARY_URL` vào `.env` trên máy dev và máy chủ; không gửi qua chat, không commit;
  - bật "Allow delivery of PDF and ZIP files" ở Settings → Security;
  - xem trang gói, báo cỡ tệp tối đa và tín dụng mỗi tháng;
- Gmail: tạo mật khẩu ứng dụng (cần bật xác minh hai bước), đặt vào `.env`.

**Trần Pha B cập nhật theo ADR 0026, 2026-10-23:** 1,00 USD mỗi người học mỗi ngày cho trợ lý/tài liệu (thay 0,20 USD trước đó),
giữ 5 USD mỗi ngày cho nội dung dùng chung. Câu "không cần giới hạn" ngày 2026-10-18 chỉ nói khâu dựng, không tự bỏ trần Pha B.

## Ghi chú thêm

- **Thứ tự đề xuất:** nền web → tài khoản → kho Pha B trên PostgreSQL và khoá mẫu → trang lộ trình → bài giảng, trợ lý, quiz và tài liệu → chia sẻ → tải sách
  và dựng → mức dùng và quản trị → triển khai.
  - Khoá mẫu đi trước tải sách, để nhóm web làm phần học mà không chờ khâu dựng.
  - Phần học bám các vé Pha B2 (31–44). Khi vé B2 chưa xong, gateway gọi bản hợp đồng đang có và đổi sau; nhóm web đã được báo hợp đồng còn đổi.
- **Hai spec viết sau:**
  - **thiết kế giao diện:** sơ đồ trang, bố cục từng trang ở điện thoại và máy tính, trạng thái rỗng, đang tải, lỗi, hết trần, bộ thành phần, màu và chữ
    lấy từ logo của chủ dự án. Bản Figma do người thiết kế vẽ theo spec đó;
  - **thiết kế cơ sở dữ liệu:** bảng, khoá ngoại, chỉ mục, ràng buộc, di trú, sao lưu.
- **Ranh giới phiên:** use case `build_document` gọi mã Pha A có sẵn. Cần đổi gì trong mã Pha A (ví dụ A4 chạy không cần tệp vàng) thì vé ghi yêu cầu cho
  phiên pha A, không sửa tệp của phiên đó.

### Quyết định chủ dự án bổ sung 2026-10-19 — W-02

Chủ dự án chọn giữ tự đăng nhập cho tài khoản vừa đăng ký. Email trùng sau chuẩn hoá trả cùng HTTP 200 và cùng thân thông báo chung, không cấp phiên mới, không sửa tài khoản cũ. Khác biệt Set-Cookie và kết quả `/me` vẫn cho phép suy ra email đã tồn tại; đây là giới hạn riêng tư được chấp nhận, vì vậy yêu cầu “không lộ email đã có” ở W-02 chỉ nghiệm thu tính đồng nhất status/thân phản hồi và không chiếm tài khoản. W-03 bổ sung thư theo phạm vi riêng.

Bằng chứng và quyết định phiên bị khoá: [báo cáo W-02](../report/w02-tai-khoan-phien-2026-10-19.md).
