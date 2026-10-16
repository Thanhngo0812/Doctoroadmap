# Spec — Gộp khâu trước A8: danh tính gộp vào A4, neo và trạng thái dạy vào A5

**Status:** ready-for-agent · soạn 2026-10-12 (Claude) · chủ dự án yêu cầu viết spec chi tiết rồi chia vé.

**Quyết định của chủ dự án (2026-10-12):**
- Danh tính gộp hẳn vào A4. Tập node đổi ngay ở A4 và không còn bản đồ danh tính (phương án 1 trong ba phương án đã đưa ra).
- Bộ vàng nào không chuyển sang được tập node mới thì để riêng, sau này dựng lại chỉ số đánh giá.

**Lịch (rà lại 2026-10-16):** vòng 2 của pass phụ đã xong và E5 đã vào sản phẩm (vé 18, ADR 0015). Chủ dự án cho cài vé 17 ngay. Chuỗi gộp là
tuỳ chọn, tắt mặc định, và chỉ bật khi đủ ba điều kiện: nghiệm thu xong, có số trên T-01, chủ dự án quyết. Lý do giữ tắt: phiếu vàng T-01 gắn với
canonical v1 của hai cuốn giữ lại, nên T-01 phải đo trên chuỗi v3.

**Nguồn:**
- [báo cáo quy lỗi thượng nguồn của A8](../report/quy-loi-thuong-nguon-a8-2026-10-12.md), mục 3, 4 và 4b;
- [luồng chi tiết provenance → neo → danh tính](../report/luong-chi-tiet-provenance-neo-danh-tinh.md);
- ADR 0004, 0005, 0006 và thuật ngữ trong `CONTEXT.md`.

## Problem Statement — Vấn đề

Giữa A4/A5 và A8, mỗi cuốn sách đi qua ba stage gọi LLM riêng, chạy nối tiếp: provenance, neo kiêm trạng thái dạy (C8), và danh tính. Trên
doc-4 trọn cuốn, ba stage này tốn khoảng 1.600 lời gọi và 0,76 USD. Mỗi stage là một lượt chờ riêng trước khi tới A8. Chủ dự án đặt ưu tiên số một
của v4 là phút/cuốn và USD/cuốn, nên các lượt chờ này đáng kể.

Ba stage này còn làm lại phần việc đã có ở thượng nguồn:
- **C8 chủ yếu chọn lại câu A3 đã trích.** Trên 19 cuốn (6.300 khái niệm được dạy có neo), câu neo của C8 trùng đúng câu bằng chứng A3 ở 88,6%
  khái niệm và cùng chunk ở 91,6%. A5 vốn đã đọc chính các chunk và bằng chứng này khi viết mô tả, nhưng C8 vẫn gọi riêng một lời cho mỗi khái niệm.
- **Provenance quyết định rất ít neo.** Chỉ 3% số neo phụ thuộc vào chunk do provenance thêm.
- **Danh tính là bước gộp thực thể thứ hai, làm cùng việc với A4.** Nó phán từng cặp một lời gọi: doc-1 381 cặp, xstk 169, doc-4 901, mỗi cuốn D-01
  334–2.034 cặp. Trên ba tài liệu chạy A4 đầy đủ, nó chỉ gộp thêm 20 nút, và ít nhất 3 lần gộp trong số đó là sai theo vàng.

Đây không phải vấn đề chất lượng của LLM. LLM chọn câu neo đúng khoảng 94% (Claude đọc 84 câu neo của đích vàng). Phần mất cạnh lớn nhất ở thượng
nguồn đến từ hai luật không dùng LLM, thuộc vé 05. Vấn đề là cấu trúc: hai bước gộp thực thể và ba stage nối tiếp làm việc trùng lặp, tốn lời gọi
và thời gian.

## Solution — Giải pháp

Giữ LLM, chỉ gộp khâu. Stage canonical (lệnh `a4` đầy đủ) còn hai bước, nối tiếp nhau:
1. **A4 gộp thực thể, kiêm luôn danh tính.**
   - A4 đề cử thêm các cặp nghi trùng mà danh tính vẫn bắt được: tên chuẩn hoá, viết tắt theo chữ đầu, tiền tố chung, câu bằng chứng trùng nhau, độ
     gần mô tả nháp.
   - Tiêu chí phán là cùng ngoại diên (R8b), dựa trên câu bằng chứng nguyên văn của A3.
   - Cặp gộp khác tên phải qua một lượt xác minh độc lập.
   - Lời phán sửa cho các cặp bị cắt ngang cụm được gom lô.
   - Kết quả là **tập node canonical cuối**. Không còn bản đồ danh tính.
2. **A5 mới: mô tả, neo và trạng thái dạy.**
   - Lời gọi mô tả và kiểm mô tả của A5 quyết định luôn câu neo và trạng thái dạy cho từng khái niệm, đúng ngữ nghĩa của C8. Câu ứng viên cho neo do
     mã dựng sẵn, như C8 đang làm.
   - Chunk chứa câu neo được thêm vào chunk định nghĩa, thay cho phần việc của provenance.

Chuỗi đồ thị mới bỏ ba stage provenance, neo và danh tính. A8 nhận đúng hợp đồng neo và trạng thái dạy như hiện nay. Chuỗi cũ vẫn chạy được và là
mặc định cho tới khi chủ dự án quyết đổi.

Id node của những khái niệm bị gộp thêm sẽ đổi theo ADR 0005, có bảng chuyển hướng. Vàng cũ được chuyển sang id mới qua bảng này. Bộ nào không
chuyển trọn được thì để riêng và dựng lại sau.

## User Stories

Danh sách dưới đây phủ các bên dùng hoặc chịu tác động của thay đổi: chủ dự án, người học, nhân viên cài đặt, Claude (kiểm thử và nghiên cứu),
người gán vàng, người duyệt gộp, và các stage phía sau.

1. Là chủ dự án, tôi muốn mỗi cuốn sách tốn ít lời gọi LLM hơn trước A8, để giảm phút/cuốn và USD/cuốn mà không hạ chất lượng.
2. Là chủ dự án, tôi muốn chỉ còn một bước gộp thực thể, để luồng dễ hiểu và sau này thay bằng bản không LLM chỉ ở một chỗ.
3. Là chủ dự án, tôi muốn số phút, số lời gọi và USD của từng phần trong stage canonical được đo và ghi trước và sau khi gộp, để quyết bằng số.
4. Là chủ dự án, tôi muốn chuỗi mới tắt mặc định cho tới khi nghiệm thu xong, để T-01 đo trên chuỗi cũ không bị ảnh hưởng.
5. Là chủ dự án, tôi muốn bật chuỗi mới bằng một tuỳ chọn duy nhất, ghi trong manifest, để biết mỗi artifact sinh từ chuỗi nào.
6. Là chủ dự án, tôi muốn `--dry-run` của chuỗi mới liệt kê dự toán của từng phần trong stage canonical (gộp cụm, lời phán sửa, xác minh, mô tả,
   neo), để duyệt chi trước khi chạy.
7. Là chủ dự án, tôi muốn mọi lời gọi tốn tiền của chuỗi mới vẫn đi qua chốt chặn chi (`--allow-spend`), như chuỗi cũ.
8. Là chủ dự án, tôi muốn vàng cũ được chuyển sang id node mới một cách tự động, kèm báo cáo cạnh vàng nào bị gộp làm một và khái niệm nào không
   chuyển được, để biết bộ nào còn dùng được.
9. Là người học, tôi muốn lộ trình từ chuỗi mới có chất lượng không kém chuỗi cũ: khái niệm được dạy vẫn vào dãy học, cạnh tiên quyết vẫn có căn cứ,
   không gộp nhầm hai khái niệm khác nhau.
10. Là người học, tôi muốn một khái niệm có nhiều cách gọi (ví dụ tên chữ và ký hiệu) chỉ hiện một lần trong lộ trình, với các cách gọi khác là alias.
11. Là Claude (kiểm thử), tôi muốn so tập node, nhóm gộp, trạng thái dạy và câu neo giữa chuỗi mới và chuỗi cũ trên cùng tài liệu.
12. Là Claude, tôi muốn chạy lại phép quy lỗi thượng nguồn và E4 trên đồ thị chuỗi mới, với vàng đã chuyển id, để đo chất lượng bằng cùng thước.
13. Là Claude, tôi muốn mỗi lần gộp có nhật ký ghi nguồn đề cử, lời phán, quan hệ và kết quả xác minh, để đọc lại khi cần.
14. Là Claude, tôi muốn mỗi quyết định neo và trạng thái dạy có nhật ký đầu vào, đầu ra và lý do như C8 hiện nay.
15. Là Claude, tôi muốn biết khái niệm nào được quyết trong lô và khái niệm nào phải hỏi lại riêng, để đo tác động của việc gom lô.
16. Là Claude, tôi muốn kích thước lô của phần neo, của lời phán sửa và các ngưỡng đề cử cấu hình được và nằm trong khoá cache, để so trên cùng
    tài liệu.
17. Là Claude, tôi muốn số cặp nghi trùng được đếm theo từng nguồn đề cử, để thấy nguồn nào sinh nhiễu.
18. Là nhân viên, tôi muốn tái dùng các hàm miền đã có: sinh cặp danh tính, xác minh, dựng câu ứng viên neo, kiểm phản hồi neo, ghi trường neo.
    Như vậy không phải viết lại luật đã kiểm.
19. Là nhân viên, tôi muốn vector mô tả nháp mà A3 đã lưu được dùng để đề cử, không embed thêm, và chỉ đề cử chứ không tự gộp (ADR 0006).
20. Là nhân viên, tôi muốn cặp gộp khác tên trượt xác minh trở thành ràng buộc "khác" khi dựng nhóm gộp, bằng cơ chế ràng buộc cùng/khác sẵn có của A4.
21. Là nhân viên, tôi muốn lời phán sửa cho các cặp bị cắt ngang cụm được gom lô, mỗi cặp vẫn độc lập, và cặp hỏng chỉ bị hỏi lại riêng.
22. Là nhân viên, tôi muốn phần dựng câu ứng viên cho neo là mã thuần chạy được ngay sau bước gộp, không phụ thuộc mention map hay embedding.
23. Là nhân viên, tôi muốn phản hồi lô bị hỏng ở một khái niệm chỉ làm khái niệm đó bị hỏi lại riêng; vẫn hỏng thì nhận `uncertain` và được giữ.
24. Là nhân viên, tôi muốn khái niệm không có câu ứng viên được xếp `mentioned_only` hoặc `unchecked` bằng mã, không gọi LLM, như C8 hiện nay.
25. Là nhân viên, tôi muốn khái niệm được phán `prior_knowledge` vẫn qua lượt xác minh độc lập, như C8 hiện nay.
26. Là nhân viên, tôi muốn chunk chứa câu neo được thêm vào chunk định nghĩa theo luật chỉ thêm, và vị trí dạy sớm nhất được tính lại.
27. Là người duyệt gộp, tôi muốn quyết định của người (cùng hay khác) thắng phán của mô hình, áp ngay ở A4.
28. Là người duyệt gộp, tôi muốn danh sách các lần gộp khác tên để duyệt khi cần, kèm câu bằng chứng của hai bên.
29. Là các stage phía sau, tôi muốn nhận tập node cuối từ canonical, không phải áp thêm bản đồ nào.
30. Là A8, tôi muốn nhận được upstream của chuỗi mới và tự bật hợp đồng cạnh theo định nghĩa khi node mang câu neo từ stage canonical.
31. Là A10, bộ chấm và công cụ nghiên cứu, tôi muốn đọc được cả artifact chuỗi mới (không có bản đồ danh tính) lẫn artifact chuỗi cũ (có bản đồ).
32. Là người đọc artifact cũ, tôi muốn artifact sinh từ chuỗi cũ (có stage `identity`) vẫn đọc và chấm được bằng mã mới.
33. Là người gán vàng của tài liệu mới, tôi muốn phiếu gán sinh từ canonical của chuỗi gộp dùng được như phiếu cũ (cùng lệnh, cùng định dạng).
34. Là Claude, tôi muốn số lời gọi và token của từng phần trong stage canonical nằm trong `cost_summary`, để báo một tổng chi duy nhất.
35. Là chủ dự án, tôi muốn có một ADR ghi quyết định gộp khâu, và `CONTEXT.md` cập nhật thuật ngữ liên quan, để người sau không đọc nhầm.
36. Là chủ dự án, tôi muốn sau này thay LLM ở bước gộp thực thể hay ở phần neo và trạng thái dạy (seminar) chỉ phải thay ở đúng bước đó của stage
    canonical.

## Implementation Decisions

### 1. Quyết định và hệ quả

Ba quyết định đã chốt, kèm hệ quả của từng cái.

**Danh tính gộp hẳn vào A4 (chủ dự án chốt 2026-10-12).**
- Một bước gộp thực thể duy nhất; không còn bản đồ danh tính phủ lên node.
- Hệ quả phải chấp nhận:
  - id của khái niệm bị gộp thêm đổi theo ADR 0005, nên vàng cũ phải chuyển id (mục 6);
  - lúc phán chỉ có câu bằng chứng A3 và mô tả nháp, không có câu neo và mô tả cuối (câu bằng chứng trùng câu neo ở 89% khái niệm);
  - A4 phải đổi cách đề cử, tiêu chí phán và cách phán sửa.
- Bằng chứng ủng hộ trên ba tài liệu phát triển: danh tính tự nó cũng gộp sai ít nhất 3/20 lần ("Véc tơ tọa độ = Tọa độ", "Độ tin cậy = Độ tin cậy của
  ước lượng", "Xác định kích thước mẫu = … trong ước lượng trung bình"). Bỏ "ý kiến thứ hai" của nó chưa chắc làm kết quả kém đi.

**Trạng thái dạy quyết ở A5 mới cùng câu neo, không ở A3.** Có ba lý do:
- A3 chỉ đọc từng cửa sổ, còn "được dạy", "chỉ nhắc" hay "kiến thức nền" là kết luận trên cả tài liệu;
- C8 vốn đã quyết trạng thái dạy và câu neo trong cùng một lời phán;
- đổi prompt A3 làm mất cache A3 của mọi tài liệu.

**Provenance rời chuỗi mới.** Nó chỉ quyết định 3% số neo. Phần còn lại của việc nó làm, là thêm chunk định nghĩa, được thay bằng việc thêm chunk
chứa câu neo (mục 4).

### 2. Công tắc chuỗi và lịch

Thêm một tuỳ chọn cấu hình chọn chuỗi thượng nguồn: chuỗi v3 (hiện nay) hoặc chuỗi gộp. Quy định:
- **Mặc định là chuỗi v3** cho tới khi nghiệm thu xong, có số T-01 và chủ dự án quyết đổi.
- Chuỗi được ghi vào config của stage canonical và của chuỗi đồ thị, nên nằm trong khoá cache. Hai chuỗi không bao giờ dùng lẫn artifact của nhau.
- Canonical chỉ có lớp tên (`--names-only`, dùng cho dữ liệu D-01) vẫn chạy chuỗi v3. Chuỗi gộp đòi canonical đầy đủ và dừng với thông báo rõ nếu
  không có.
- Mã của ba stage provenance, neo, danh tính và đường A4 cũ giữ nguyên trong chuỗi v3. Gỡ chúng là một vé riêng, sau khi chuỗi gộp thành mặc định.

### 3. A4 gộp thực thể, kiêm danh tính

**3.1. Đề cử cặp nghi trùng.** Giữ các nguồn hiện có: alias, độ giống chuỗi của tên, láng giềng gần nhất theo vector tên. Thêm các nguồn mà danh tính
đang dùng, tính trên nhóm ứng viên:
- tên hoặc alias trùng nhau sau chuẩn hoá: NFKC, bỏ dấu LaTeX, gộp gạch nối;
- viết tắt theo chữ đầu, tên ít nhất hai từ;
- khác nhau đúng một tiền tố chung chung lặp lại trong chính tài liệu, như luật hiện có của danh tính;
- câu bằng chứng A3 trùng nhau, thay cho "cùng câu neo";
- độ gần mô tả nháp: top-3 mỗi phía, ngưỡng cosine cấu hình được, khởi điểm 0,85 như danh tính.

Tham số của các nguồn nằm trong config. Vector mô tả nháp là vector A3 **đã lưu**, nên không phải embed thêm. Đây là lần đầu A4 dùng vector này, nên
ADR 0004 phải ghi lại. Vector chỉ đề cử, không bao giờ tự gộp (ADR 0006).

Rủi ro đã biết: ADR 0006 đo thấy mô tả nháp rất nhiễu với các mục trong cùng một danh sách liệt kê. Số cặp đề cử theo từng nguồn phải được đếm và
ghi lại, để nghiệm thu thấy nguồn nào sinh nhiễu.

**Đính chính sau đo (2026-10-16, vé 17i/17k, chủ dự án duyệt):** rủi ro này xảy ra thật.
- Với tiêu chí cùng ngoại diên, khoảng 720 cặp chỉ có nguồn mô tả (4 tài liệu) chỉ ra 4 lần gộp, trong đó 1 đúng.
- Nguồn này lại sinh phần lớn lời phán sửa, làm chuỗi gộp đắt hơn v3 (doc-4 +60%).
- Vì vậy chuỗi gộp **mặc định tắt nguồn đề cử theo mô tả**; nguồn này chỉ còn là tuỳ chọn để đo.

**3.2. Chia cụm và lời phán sửa.** Chia cụm ứng viên giữ cách hiện có (Leiden, trần cỡ cụm). Cặp bị cắt ngang cụm vẫn được phán sửa, nhưng **gom
lô**: mỗi lời gọi chứa nhiều cặp, mỗi cặp phán độc lập, kích thước lô cấu hình được. Một cặp trượt kiểm thì chỉ cặp đó được hỏi lại riêng.

Lý do gom lô: thêm cạnh đề cử theo mô tả sẽ biến đồ thị đề cử thành gần như một khối liên thông. Đo trên nhật ký danh tính, ở doc-4 có 473/563 nút
nằm chung một khối. Như vậy số cặp bị cắt tăng mạnh, trong khi hiện A4 đã tốn 307 lời phán sửa trên doc-4, mỗi lời một cặp.

**Đính chính sau đo (2026-10-16, vé 17i/17j):** gom lô lời phán sửa làm mô hình né gộp các cặp đồng nghĩa và bản dịch. Trên nhap-mon-ml,
lô cỡ 10 gộp lại 1/5 cặp mà v3 có; hỏi từng mục thì gộp lại 5/5. Chi phí gần như bằng nhau (0,094 so với 0,111 USD), vì token vào chiếm phần lớn.
Vì vậy chuỗi gộp mặc định phán sửa **mỗi cặp một lời**; gom lô chỉ còn là tuỳ chọn để đo.

**3.3. Tiêu chí phán.** Prompt phán cụm và phán sửa dùng tiêu chí **cùng ngoại diên** (R8b): hai nhóm là một thực thể khi và chỉ khi cùng định
nghĩa, cùng tập đối tượng, chỉ khác cách gọi. Cách gọi khác gồm đồng nghĩa, ký hiệu, viết tắt, số ít/số nhiều, cách viết, bản dịch. Phán trên câu
bằng chứng nguyên văn. Prompt nhắc rằng một câu thường định nghĩa nhiều khái niệm khác nhau.

Các quan hệ không đồng nhất được ánh xạ như sau:
- trường hợp riêng, bằng nhau nhờ mệnh đề, mệnh đề khác, đối tượng khác loại: **giữ tách**;
- trường hợp riêng đi ra thành **quan hệ đề xuất** kiểu mở (ví dụ `subtype_of`), qua đúng đường quan hệ đề xuất 2a hiện có;
- đầu ra tự mâu thuẫn bị bắt phán lại như hiện nay.

**3.4. Xác minh cặp gộp khác tên.** Mỗi cặp nhóm được gộp mà không chung tên hay alias sau chuẩn hoá qua một lời gọi xác minh **độc lập**. Lời gọi
chỉ thấy hai hồ sơ (tên, alias, câu bằng chứng, mô tả nháp), không thấy lời phán lượt trước, như lượt xác minh danh tính hiện nay. Chỉ quan hệ
`dong_nhat` giữ gộp. Quan hệ khác trở thành ràng buộc "khác" khi dựng thành phần gộp, bằng cơ chế ràng buộc cùng/khác sẵn có. Cặp chung tên hay
alias không cần xác minh.

**3.5. Người duyệt.** Quyết định của người (cùng hoặc khác) được nạp ở A4 và thắng phán của mô hình, dưới dạng ràng buộc khi dựng thành phần gộp. Tệp
duyệt giữ các trường `left`, `right`, `decision`, dùng id node canonical. Id nào đã chuyển hướng thì được quy về id hiện hành qua bảng chuyển hướng.
Tệp của tài liệu khác bị từ chối. A4 xuất danh sách các lần gộp khác tên, kèm câu bằng chứng hai bên, để người duyệt dùng khi cần.

**3.6. Định danh và tên.** Id node theo ADR 0005 (băm ứng viên neo, tức ứng viên có vị trí sớm nhất trong node). Id biến mất được ghi vào bảng chuyển
hướng. Tên chuẩn theo luật hiện có (tên đầy đủ tài liệu dùng nhiều nhất). Tên của các nhóm thành viên thành alias kèm câu bằng chứng. Không còn khái
niệm "đại diện" của danh tính.

**3.7. Đầu ra.** Tập node canonical là tập cuối. Nhật ký quyết định có thêm, cho từng cặp nghi trùng: nguồn đề cử, lời phán, quan hệ, kết quả xác
minh. Số liệu có thêm:
- số cặp đề cử theo nguồn;
- số cặp bị cắt;
- số lời phán sửa và số lô;
- số lời xác minh;
- số lần gộp khác tên.

Artifact chuỗi gộp không có `identity_map`, hoặc có nhưng rỗng.

### 4. A5 mới: mô tả, neo và trạng thái dạy

**Câu ứng viên cho neo** được dựng bằng mã ngay sau bước gộp, với luật y hệt C8 hiện nay.
- Vùng tìm gồm:
  - chunk nguồn của node, thay cho chunk định nghĩa mà A5 chọn (sửa 2026-10-16). Khi phần neo gom vào lời gọi A5, câu ứng viên phải dựng
    trước lời gọi, lúc chưa biết A5 chọn chunk nào. Chunk A5 chọn luôn nằm trong chunk nguồn, nên hai cỡ lô của phần neo dùng cùng một tập
    ứng viên;
  - chunk có bằng chứng A3;
  - chunk có tên hoặc alias khớp chính xác, tính trực tiếp trên toàn văn bằng hàm khớp tên của mention map, không dùng kênh độ gần nghĩa;
  - chunk nhắc ký hiệu;
  - chunk có tiêu đề mang tên.
- Chỉ xét chunk có vai trò nội dung, đọc nhãn vai trò tương thích với phiên bản chunk của A3.
- Hạng, thứ tự và tối đa 6 câu ứng viên như C8. Không có ứng viên thì quét tên chính xác thêm một lần như C8.

**Lời gọi.** Câu ứng viên được gắn vào đúng lời gọi A5 sẵn có của khái niệm đó:
- node nhiều thành viên: lời gọi mô tả, mỗi node một lời gọi;
- node một thành viên: lời gọi kiểm mô tả theo lô.

Mỗi khái niệm trả thêm các trường của C8: trạng thái (6 giá trị: `defined_here`, `introduced_by_example`, `mentioned_only`, `prior_knowledge`,
`not_subject_matter`, `uncertain`), mã câu neo, câu trích, lý do. Prompt phần neo giữ đúng nội dung luật của prompt neo hiện nay.

**Kiểm phản hồi theo từng khái niệm**, đúng luật C8:
- câu neo phải là một ứng viên có thật;
- câu trích phải nằm trong ngữ cảnh của ứng viên tương ứng;
- không có trường `confidence`.

Khái niệm có phần neo trượt kiểm được **hỏi lại riêng** bằng lời gọi một khái niệm, theo đúng hợp đồng C8 (tối đa 2 lần). Vẫn hỏng thì nhận
`uncertain` và được giữ. Phần mô tả của khái niệm đó không bị gọi lại nếu đã hợp lệ.

**Kích thước lô của phần neo** là tham số trong khoá cache, gồm hai giá trị:
- "theo lô A5": mặc định đề xuất, cần nghiệm thu;
- "một khái niệm một lời gọi": vẫn trong stage canonical, dùng làm đối chứng với C8 cũ.

**Các nhánh khác giữ nguyên ngữ nghĩa C8:**
- Không có ứng viên trong vùng nội dung thì không gọi LLM: tên chỉ xuất hiện ngoài vùng nội dung → `mentioned_only`; không thấy ở đâu → `unchecked`.
- Lời phán `prior_knowledge` qua một lượt xác minh độc lập. Không xác nhận thì hạ xuống `uncertain`.
- Luật "khái niệm chỉ có căn cứ ngoài vùng nội dung thì không hỏi" **giữ nguyên**. Sửa nó thuộc vé 05, để đo riêng tác động.

**Ghi lên node** đúng các trường C8 đang ghi: `teaching_status`, `anchor`, `teaching_chunk_ids`, `teaching_order_index`, `teaching_conflict`.
Thêm hai việc:
- chunk chứa câu neo được thêm vào `defining_chunk_ids` theo luật chỉ thêm, bản trước giữ ở trường nguồn như provenance đang làm;
- vị trí dạy sớm nhất được tính lại.

Payload canonical có thêm nhật ký neo và nhật ký lời phán của phần neo, cùng dạng với chuỗi v3. Media không qua bước này.

Pass phụ ML (ADR 0015) đọc thẳng `teaching_status`, `anchor` và `defining_chunk_ids` để dựng đặc trưng (cửa sổ định nghĩa, vị trí chunk định
nghĩa, vai trò chunk neo). Vì vậy các trường này phải giữ đúng dạng của chuỗi v3. Chunk định nghĩa giờ có thêm chunk neo, thay cho chunk do
provenance vá, nên phân bố đặc trưng sẽ lệch. Nghiệm thu đo tác động này.

### 5. Chuỗi đồ thị gộp

Thứ tự stage của chuỗi gộp như sau:

```
clusters (A6–A7) → mentions → main_edges → secondary_edges → validated (A9) → concept_labels → stages (A10) → module_titles
```

- Mọi stage làm việc trên tập node canonical cuối. Không có bước áp bản đồ danh tính.
- Mention map, viện dẫn và cặp nghi tiên quyết dựng trên tập node đó, với chunk định nghĩa đã có chunk neo.
- **A8:** pass chính và pass phụ nhận upstream `mentions` của chuỗi gộp. Hợp đồng cạnh theo định nghĩa và yêu cầu kiểu tiên quyết bật khi canonical
  khai báo đã có neo. Cửa sổ định nghĩa, bộ kiểm và các luật khác không đổi. Hiện nay pass chính bật hợp đồng này khi upstream là stage
  `identity`, và chỉ nhận upstream `provenance` hoặc `identity`. Chuỗi gộp phải bật theo khai báo của canonical, không theo tên stage.
- **`--stop-after`:** giá trị `provenance`, `teaching`, `identity` không hợp lệ trong chuỗi gộp, báo lỗi kèm gợi ý "đã nằm trong stage canonical".
  `--dry-run` liệt kê các stage của chuỗi gộp.
- `--identity-review` của lệnh `roadmap` không dùng trong chuỗi gộp. Quyết định người duyệt nạp ở A4 (mục 3.5).

### 6. Hợp đồng, tương thích và vàng

- **Đọc artifact cũ:** A8, A10, bộ chấm và công cụ nghiên cứu vẫn đọc được artifact chuỗi v3 (có stage `identity` và bản đồ danh tính). Thiếu
  `identity_map` được hiểu là bản đồ rỗng.
- Bộ chấm hiện từ chối vàng có id không nằm trong đồ thị, và làm việc này **trước** khi áp bản đồ danh tính. Với chuỗi gộp, id phải được quy
  qua bảng chuyển hướng trước bước từ chối đó.
- **Chuyển vàng cũ sang id mới.** Thêm một công cụ chấm, không gọi mô hình, quy các id của bộ vàng về id hiện hành qua bảng chuyển hướng của canonical
  mà đồ thị đang dùng. Có thể làm thành tuỳ chọn của bộ chấm, áp như cách bộ chấm đang áp bản đồ danh tính. Tệp vàng gốc không bị sửa. Báo cáo của
  công cụ ghi:
  - cạnh vàng có hai đầu bị gộp làm một: rời phép chấm và được đếm, như `identity_dropped_gold_edges` hiện nay;
  - khái niệm của vàng không quy được về id nào, ví dụ vì node bị tách hay biến mất. Có khái niệm như vậy thì công cụ **từ chối chấm** bộ đó và
    liệt kê. Theo quyết định của chủ dự án, bộ đó để riêng và dựng lại chỉ số sau.
- **T-01:** đo trên chuỗi v3 với canonical v1, nên không bị ảnh hưởng.
- **Chi phí:** `cost_summary` của stage canonical tách theo phần (gộp cụm, phán sửa, xác minh gộp, mô tả, neo, xác minh kiến thức nền) và có một
  tổng. Đo thời gian từng phần theo cơ chế đo stage hiện có.

### 7. Tài liệu đi kèm

- **ADR mới (0016; số 0011–0015 đã dùng):** "danh tính là một phần của gộp thực thể ở A4; neo và trạng thái dạy quyết ở A5; provenance rời chuỗi".
- **ADR 0004:** thêm mục cập nhật, ghi rằng vector mô tả nháp của A3 nay được dùng để đề cử ở A4.
- **`CONTEXT.md`:**
  - "Cặp nghi trùng" thêm các nguồn đề cử mới;
  - "Xác minh danh tính" thành xác minh cặp gộp khác tên ở A4;
  - "Bản đồ danh tính" và "Ứng viên danh tính mở rộng" ghi là chỉ còn ở artifact chuỗi v3;
  - thêm mục "Câu neo" và "Trạng thái dạy" nếu domain-modeling thấy cần.
- **`doc/spec-addendum.md`:** sơ đồ pha A và các mục A4, A5, A9', A9'' trỏ sang spec này.

## Testing Decisions

**Một test tốt** kiểm hành vi nhìn từ ngoài: hợp đồng artifact, số lời gọi mô hình, việc tái dùng cache, việc từ chối hay dừng có thông báo.
Không kiểm chi tiết cài đặt bên trong. Mỗi luật chặn phải được thấy đỏ ít nhất một lần (AGENTS.md mục 5).

**Seam chính: stage canonical chạy trên fixture thật.** Mẫu sẵn có là các test pipeline A4: kho fixture từ tài liệu thật, mô hình giả trả lời
theo hình dạng đầu vào, embedding phát lại.

Test cho bước gộp:
- mỗi nguồn đề cử mới sinh cặp nghi trùng đúng loại. Không nguồn nào, kể cả cosine rất cao, tự gộp khi mô hình không phán gộp;
- cặp được phán "trường hợp riêng" giữ tách và ra một quan hệ đề xuất;
- cặp gộp khác tên trượt xác minh thì không gộp; cặp chung tên không sinh lời xác minh;
- lời phán sửa đi theo lô; một cặp hỏng trong lô chỉ làm cặp đó bị hỏi lại riêng;
- quyết định người duyệt thắng mô hình, kể cả khi tệp dùng id đã chuyển hướng;
- id biến mất được ghi vào bảng chuyển hướng và không bao giờ cấp lại cho khái niệm khác.

Test cho A5 mới:
- neo và trạng thái dạy được ghi đúng trường. Mã câu neo không có trong ứng viên thì bị bác; câu trích ngoài ngữ cảnh thì bị bác;
- một khái niệm hỏng phần neo trong lô chỉ làm khái niệm đó bị hỏi lại riêng; hỏng tiếp thì nhận `uncertain` và được giữ;
- khái niệm không có ứng viên không sinh lời gọi nào;
- `prior_knowledge` không được xác minh thì hạ xuống `uncertain`;
- chunk neo được thêm vào chunk định nghĩa và không xoá chunk cũ.

Test chung:
- chạy lại cùng cấu hình thì tái dùng toàn bộ;
- đổi kích thước lô, ngưỡng đề cử hay chuỗi thì đổi khoá cache.

**Seam phụ: bộ điều phối chuỗi đồ thị và đầu vào của A8.** Mẫu sẵn có là test điều phối với stage giả và test hợp đồng pass chính. Các test cần có:
- thứ tự stage của chuỗi gộp và chuỗi v3;
- `--stop-after` hợp lệ và không hợp lệ;
- `--dry-run` không gọi mô hình hay embedding;
- A8 bật hợp đồng cạnh theo định nghĩa với upstream chuỗi gộp và vẫn chạy với upstream chuỗi v3;
- A10 và bộ chấm chạy được khi không có bản đồ danh tính.

**Công cụ chuyển vàng.** Test trên vàng dựng tay:
- id quy qua bảng chuyển hướng;
- cạnh có hai đầu bị gộp được đếm và rời phép chấm;
- khái niệm không quy được làm công cụ từ chối và liệt kê;
- tệp vàng gốc không bị sửa.

**Test miền hiện có** của sinh cặp danh tính, xác minh, dựng câu ứng viên và kiểm phản hồi neo phải tiếp tục xanh, vì chuỗi gộp dùng lại các hàm đó.
**Hồi quy:** artifact chuỗi v3 trong fixture vẫn qua A8, A10 và bộ chấm; chuỗi v3 vẫn là mặc định.

**Nghiệm thu nghiên cứu (Claude, sau khi nhân viên báo xong).** Trên 6 tài liệu phát triển tiếng Việt có A4 đầy đủ (doc-1, nhap-mon-ml,
naive-bayes, doc-6, xstk-ch3-1, doc-4), so với artifact chuỗi v3:
- **Gộp:**
  - nhóm gộp so với A4 cũ cộng danh tính cũ: gộp nào mất, gộp nào mới;
  - Claude đọc mọi gộp khác tên mới;
  - số gộp sai mà vàng phát hiện được không tăng (mốc: 3);
  - số cặp đề cử theo nguồn.
- **Neo và trạng thái dạy:**
  - độ khớp theo từng khái niệm;
  - Claude đọc mọi chỗ lệch trên đích vàng và một mẫu chỗ lệch khác;
  - câu neo đúng trên đích vàng không thấp hơn mốc 79/84.
- **Chất lượng đầu cuối:** E4 trên doc-1, xstk, doc-4 với vàng đã chuyển id, pass phụ sản phẩm `a8-secondary-ml-v1` (mô hình đóng băng của vé 18) ở cả hai chuỗi, cộng phép quy lỗi thượng nguồn chạy lại. Hồi
  tưởng và độ chính xác bao đóng, Q7, Q7b không giảm quá mức nhiễu. Bộ vàng nào bị công cụ từ chối thì ghi lại và để riêng.
- **Chi phí:** số lời gọi, USD và phút của stage canonical và chuỗi đồ thị, trước và sau, trên doc-4.

Lượt này tốn tiền: chạy lại A4 và A5 mới trên 6 tài liệu, và pass chính trên 3 tài liệu vàng. Ước dưới 6 USD, phải dry-run và được chủ dự án duyệt
trước.

## Out of Scope

Spec này không làm các việc sau:
- **Bỏ LLM ở gộp thực thể, neo hay trạng thái dạy** (bản không LLM cho seminar). Spec chỉ gom chúng về một chỗ để việc thay sau này dễ hơn.
- **Cờ gợi ý "dạy ở đây" trong A3.** Đổi prompt A3 mất cache A3 của mọi tài liệu. Chỉ cân nhắc nếu nghiệm thu cho thấy A5 mới thiếu thông tin.
- **Sửa luật vai trò vùng A2** ("tiêu đề lặp ở đầu nhiều mục là đề cương") và **luật bỏ qua của C8**. Cả hai thuộc vé 05; spec này giữ nguyên
  hành vi để đo riêng.
- Chuỗi canonical chỉ có lớp tên (D-01) và bất kỳ việc xuất phiếu D-01 nào.
- Dựng lại chỉ số đánh giá cho bộ vàng không chuyển được: việc sau, theo quyết định của chủ dự án.
- Học lại mô hình pass phụ ML. Nếu nghiệm thu thấy E5 tụt trên chuỗi gộp thì học lại là vé riêng (ADR 0015: chỉ đổi tệp mô hình và phiên bản).
- Mở rộng cửa sổ định nghĩa hay ứng viên không nguyên văn (E7).
- `a8-gold-sheet` dùng trạng thái dạy để chọn khái niệm của chương: việc tiếp theo nếu cần.
- Tài liệu tiếng Anh, vì đồ án chỉ làm tiếng Việt.

## Further Notes

- **Số đo nền** (báo cáo quy lỗi, mục 4b; nhật ký danh tính của 19 cuốn):
  - câu neo trùng câu bằng chứng A3 ở 88,6% khái niệm, cùng chunk ở 91,6%;
  - provenance quyết định 3% số neo;
  - trên ba tài liệu phát triển, 13/20 lần gộp của danh tính chỉ được đề cử nhờ độ gần mô tả, ví dụ "Nhân = KerT", "Imf = Ảnh của ánh xạ tuyến
    tính", "Tự đồng cấu = Toán tử tuyến tính". Ở A4, các cặp này chỉ còn được đề cử nhờ mô tả nháp;
  - đồ thị cặp nghi trùng gần như là một khối liên thông (doc-4: 473/563 nút).
- **Lời gọi hiện nay trên doc-4**, khoảng 2.300 cho các bước canonical và ba stage:
  - A4: 180 lời phán cụm, 307 lời phán sửa;
  - A5: 174 lời mô tả, 46 lời kiểm;
  - provenance: 89;
  - C8: 618;
  - danh tính: 907.

  Ước sau khi gộp là khoảng 600–900 lời gọi, tuỳ số cặp đề cử thêm và kích thước lô. Số thật đo khi nghiệm thu.
- **Rủi ro chính và cách đo:**
  - mô tả nháp nhiễu có thể sinh nhiều cặp đề cử thừa. Đếm theo nguồn và chỉnh ngưỡng trên tài liệu phát triển;
  - phán gộp không có câu neo có thể kém hơn danh tính hiện nay. Lượt xác minh độc lập cho cặp gộp khác tên được giữ để chặn gộp sai;
  - gom lô lời phán sửa và gom lô phần neo có thể làm phán kém đi. Kích thước lô cấu hình được để đo cả hai cách trên cùng tài liệu;
  - id đổi làm một số bộ vàng không chấm được. Công cụ chuyển vàng báo rõ bộ nào, và chủ dự án đã chấp nhận dựng lại sau.
- **Quan hệ với vé khác:**
  - vé 05 (sửa luật A2 và C8) nên làm sau spec này và đo bằng cùng bộ công cụ;
  - việc thay LLM ở các khâu này (seminar) sẽ cắm vào đúng hai bước của stage canonical.
- **Sau khi chuỗi gộp thành mặc định:** một vé riêng gỡ ba stage cũ và đường A4 cũ khỏi mã, rồi chạy lại các tài liệu phát triển để có artifact
  chuẩn mới.
