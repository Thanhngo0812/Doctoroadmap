# Spec — Gộp khâu trước A8: neo, trạng thái dạy và danh tính chạy trong stage canonical

**Status:** ready-for-agent · soạn 2026-10-12 (Claude) · chủ dự án yêu cầu viết spec chi tiết rồi chia vé.

**Lịch: chỉ triển khai sau khi vòng 2 của pass phụ đo xong trên T-01.** Có hai lý do:
- vòng 2 phải đo trên chuỗi thượng nguồn đã đóng băng; đổi thượng nguồn giữa vòng đo thì không còn biết thay đổi nào tạo ra kết quả;
- phiếu vàng T-01 gắn với canonical v1 của hai cuốn giữ lại.

Vé có thể soạn và cài trước, nhưng chuỗi mới phải là tuỳ chọn, tắt mặc định, cho tới khi nghiệm thu xong và chủ dự án quyết bật.

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
- **Danh tính là gộp thực thể, cùng việc với A4, nhưng làm theo từng cặp.** Danh tính phán từng cặp một lời gọi, trong một stage riêng sau mention
  map. Trên ba tài liệu chạy A4 đầy đủ, nó phán 381, 169 và 901 cặp nhưng chỉ gộp thêm 11, 5 và 4 nút, trong đó ít nhất 3 lần gộp là sai theo vàng.

Đây không phải vấn đề chất lượng của LLM. LLM chọn câu neo đúng khoảng 94% (Claude đọc 84 câu neo của đích vàng). Phần mất cạnh lớn nhất ở thượng
nguồn đến từ hai luật không dùng LLM, thuộc vé 05. Vấn đề là cấu trúc: ba stage nối tiếp làm việc trùng lặp, tốn lời gọi và thời gian.

## Solution — Giải pháp

Giữ LLM, chỉ gộp khâu để bớt lời gọi và bớt stage nối tiếp. Chủ dự án đề xuất gộp danh tính vào A4, trạng thái dạy vào A3, và để A5 kiêm neo.
Spec này giữ hướng đó, với hai điều chỉnh có lý do (xem mục "Implementation Decisions").

Sau khi gộp, stage canonical (lệnh `a4` đầy đủ) làm ba việc nối tiếp nhau trong cùng một stage:
1. **Gộp ứng viên (A4):** giữ nguyên như hiện nay. Lời phán cụm cũ được tái dùng, nên tập node canonical và id node không đổi.
2. **A5 mới:** lời gọi mô tả và kiểm mô tả của A5 quyết định luôn câu neo và trạng thái dạy cho từng khái niệm, đúng ngữ nghĩa của C8. Câu ứng
   viên cho neo do mã dựng sẵn, như C8 đang làm. Chunk chứa câu neo được thêm vào chunk định nghĩa, thay cho phần việc của provenance.
3. **Danh tính:** chạy sau A5 mới, trên câu neo và mô tả cuối. Các cặp nghi trùng được phán theo cụm thay vì từng cặp, rồi xác minh cặp gộp.
   Kết quả là một bản đồ danh tính phủ lên node canonical, không sửa tập node.

Chuỗi đồ thị mới bỏ ba stage provenance, neo và danh tính. Bản đồ danh tính được áp ngay ở stage đầu (A6). A8 nhận đúng hợp đồng như hiện nay:
- node mang trạng thái dạy, câu neo, chunk dạy, vị trí dạy;
- bản đồ danh tính và danh sách node đã gộp.

Chuỗi cũ vẫn chạy được và là mặc định cho tới khi chủ dự án quyết đổi.

## User Stories

Danh sách dưới đây phủ các bên dùng hoặc chịu tác động của thay đổi: chủ dự án, người học, nhân viên cài đặt, Claude (kiểm thử và nghiên cứu),
người gán vàng, người duyệt danh tính, và các stage phía sau.

1. Là chủ dự án, tôi muốn mỗi cuốn sách tốn ít lời gọi LLM hơn trước A8, để giảm phút/cuốn và USD/cuốn mà không hạ chất lượng.
2. Là chủ dự án, tôi muốn số phút, số lời gọi và USD của từng bước trong stage canonical được đo và ghi trước và sau khi gộp, để quyết bằng số.
3. Là chủ dự án, tôi muốn chuỗi mới tắt mặc định cho tới khi nghiệm thu xong, để vòng 2 của pass phụ chạy trên chuỗi cũ không bị ảnh hưởng.
4. Là chủ dự án, tôi muốn bật chuỗi mới bằng một tuỳ chọn duy nhất, ghi trong manifest, để biết mỗi artifact sinh từ chuỗi nào.
5. Là chủ dự án, tôi muốn `--dry-run` của chuỗi mới liệt kê dự toán của từng bước trong stage canonical (A5 mới, neo, danh tính), để duyệt chi
   trước khi chạy.
6. Là chủ dự án, tôi muốn mọi lời gọi tốn tiền của chuỗi mới vẫn đi qua chốt chặn chi (`--allow-spend`), như chuỗi cũ.
7. Là chủ dự án, tôi muốn vàng cũ (doc-1, xstk, doc-4) và vàng T-01 vẫn chấm được trên đồ thị của chuỗi mới, không phải gán lại.
8. Là người học, tôi muốn lộ trình từ chuỗi mới có chất lượng không kém chuỗi cũ: khái niệm được dạy vẫn vào dãy học, cạnh tiên quyết vẫn có căn cứ.
9. Là người học, tôi muốn tên hiển thị và dòng "cần:" không đổi vì lý do kỹ thuật, khi tài liệu không đổi.
10. Là Claude (kiểm thử), tôi muốn so từng khái niệm giữa chuỗi mới và chuỗi cũ trên cùng tài liệu: trạng thái dạy, câu neo, nhóm gộp danh tính.
11. Là Claude, tôi muốn chạy lại phép quy lỗi thượng nguồn và E4 trên đồ thị chuỗi mới mà không phải sửa công cụ, để đo chất lượng bằng cùng thước.
12. Là Claude, tôi muốn mỗi quyết định neo và trạng thái dạy có nhật ký đầu vào, đầu ra và lý do như C8 hiện nay, để đọc và phán lại khi cần.
13. Là Claude, tôi muốn biết khái niệm nào được quyết trong lô và khái niệm nào phải hỏi lại riêng, để đo tác động của việc gom lô.
14. Là Claude, tôi muốn kích thước lô của phần neo cấu hình được và nằm trong khoá cache, để so "neo trong lô A5" với "neo một khái niệm một lời
    gọi" trên cùng tài liệu.
15. Là nhân viên, tôi muốn phần dựng câu ứng viên cho neo là mã thuần chạy được ngay sau A4, để không phụ thuộc mention map hay embedding.
16. Là nhân viên, tôi muốn tái dùng các hàm miền đã có của C8 (dựng ứng viên, kiểm phản hồi, ghi trường neo) và của danh tính (sinh cặp, lập bản
    đồ, xác minh), để không viết lại luật đã kiểm.
17. Là nhân viên, tôi muốn lời phán gộp cụm cũ của A4 được tái dùng khi chỉ phần A5 đổi, để chạy lại stage canonical không tốn thêm lời gọi gộp.
18. Là nhân viên, tôi muốn phản hồi lô bị hỏng ở một khái niệm chỉ làm khái niệm đó bị hỏi lại riêng, không làm hỏng cả lô.
19. Là nhân viên, tôi muốn một khái niệm mà hỏi lại riêng vẫn hỏng thì nhận `uncertain` và được giữ lại, như C8 hiện nay.
20. Là nhân viên, tôi muốn khái niệm không có câu ứng viên nào được xếp `mentioned_only` hoặc `unchecked` bằng mã, không gọi LLM, như C8 hiện nay.
21. Là nhân viên, tôi muốn khái niệm được phán `prior_knowledge` vẫn qua lượt xác minh độc lập, như C8 hiện nay.
22. Là nhân viên, tôi muốn chunk chứa câu neo được thêm vào chunk định nghĩa theo luật chỉ thêm, không xoá, và vị trí dạy sớm nhất được tính lại.
23. Là nhân viên, tôi muốn danh tính trong stage canonical dùng đủ các nguồn đề cử hiện có: tên hoặc alias chuẩn hoá trùng, viết tắt theo chữ
    đầu, tiền tố chung lặp trong tài liệu, cùng câu neo, và độ gần mô tả.
24. Là nhân viên, tôi muốn vector mô tả dùng để đề cử chỉ đề cử, không tự gộp (ADR 0006).
25. Là nhân viên, tôi muốn các cặp nghi trùng được gom thành cụm ứng viên danh tính và phán theo cụm, có trần cỡ cụm, để giảm số lời gọi.
26. Là nhân viên, tôi muốn chỉ nhóm mà mọi cặp đều được phán đồng nhất và qua xác minh độc lập mới được gộp.
27. Là người duyệt danh tính, tôi muốn quyết định của người thắng phán của mô hình như hiện nay, với cùng định dạng tệp duyệt.
28. Là người duyệt danh tính, tôi muốn mọi gộp chạm khái niệm của bộ vàng vẫn cần chủ dự án duyệt trước khi bật.
29. Là các stage phía sau, tôi muốn bản đồ danh tính được áp một lần ở stage đầu của chuỗi đồ thị. Khi đó A6, mention map, A8 và A10 cùng thấy
    một tập node đã gộp, với node bị gộp nằm trong danh sách node đã gộp.
30. Là A8, tôi muốn nhận được upstream của chuỗi mới và tự bật hợp đồng cạnh theo định nghĩa khi node mang câu neo từ stage canonical.
31. Là A10 và bộ chấm, tôi muốn payload cuối vẫn có `identity_map`, `merged_nodes`, nhật ký neo và nhật ký danh tính như trước.
32. Là người đọc artifact cũ, tôi muốn artifact sinh từ chuỗi cũ (có stage `identity`) vẫn đọc và chấm được bằng mã mới.
33. Là người gán vàng của tài liệu mới, tôi muốn phiếu gán sinh từ canonical của chuỗi gộp dùng được như phiếu cũ (cùng lệnh, cùng định dạng),
    để quy trình gán không đổi.
34. Là Claude, tôi muốn số lời gọi và token của từng phần trong stage canonical (gộp, mô tả, neo, danh tính, xác minh) nằm trong
    `cost_summary`, để báo một tổng chi duy nhất.
35. Là chủ dự án, tôi muốn có một ADR ghi quyết định gộp khâu, và `CONTEXT.md` cập nhật thuật ngữ liên quan, để người sau không đọc nhầm.
36. Là chủ dự án, tôi muốn sau này thay LLM ở neo, trạng thái dạy hay danh tính bằng mô hình không LLM (seminar) chỉ phải thay ở một chỗ trong
    stage canonical.

## Implementation Decisions

### 1. Hai điều chỉnh so với đề xuất ban đầu, có lý do

Chủ dự án đề xuất gộp danh tính vào A4, trạng thái dạy vào A3, và A5 kiêm neo. Spec giữ hướng nhưng điều chỉnh hai điểm.

**Danh tính không gộp thẳng vào tập node của A4. Nó chạy trong stage canonical, sau A5 mới, và ra một bản đồ phủ lên node.** Có ba lý do:
- Bộ chấm lộ trình (dùng cho Q6, Q7 và E4) đòi mọi khái niệm của bộ vàng có mặt trong đồ thị đang chấm, rồi áp bản đồ danh tính của đồ thị lên
  vàng. Gộp thẳng vào tập node sẽ đổi id của node bị gộp (ADR 0005, bảng chuyển hướng), làm vàng cũ và vàng T-01 không chấm được nữa. Bản đồ phủ
  giữ nguyên id, như hiện nay.
- Phán danh tính cần câu neo (tiêu chí cùng ngoại diên, R8b) và mô hình chọn đại diện cần trạng thái dạy. Hai thứ này chỉ có sau A5 mới.
- Thuật ngữ "Bản đồ danh tính" vốn đã là bản đồ phủ, không sửa canonical. Spec giữ nghĩa đó, chỉ đổi nơi tính và cách phán.

**Trạng thái dạy không quyết ở A3. Nó quyết ở A5 mới, cùng câu neo.**
- A3 đọc từng cửa sổ và không thấy các cửa sổ khác. Còn "được dạy", "chỉ nhắc" hay "kiến thức nền" là kết luận trên cả tài liệu.
- C8 vốn đã quyết trạng thái dạy và câu neo trong cùng một lời phán, nên chuyển cả hai sang A5 là gọn nhất.
- Đổi prompt A3 làm mất cache A3 của mọi tài liệu, tức phải chạy lại A3 có tốn tiền.

### 2. Công tắc chuỗi và lịch

Thêm một tuỳ chọn cấu hình chọn chuỗi thượng nguồn: chuỗi v3 (hiện nay) hoặc chuỗi gộp. Quy định:
- **Mặc định là chuỗi v3** cho tới khi nghiệm thu xong và chủ dự án quyết đổi. Vòng 2 của pass phụ đo trên chuỗi v3.
- Chuỗi được ghi vào config của stage canonical và của chuỗi đồ thị, nên nằm trong khoá cache. Hai chuỗi không bao giờ dùng lẫn artifact của nhau.
- Canonical chỉ có lớp tên (`--names-only`, dùng cho dữ liệu D-01) vẫn chạy chuỗi v3. Chuỗi gộp đòi canonical đầy đủ (`stage = complete`) và
  dừng với thông báo rõ nếu không có.
- Mã của ba stage provenance, neo, danh tính trong chuỗi v3 giữ nguyên. Gỡ chúng là một vé riêng, sau khi chuỗi gộp thành mặc định.

### 3. Stage canonical — bước gộp ứng viên (A4)

Bước này không đổi: cùng lớp tên, cùng đề cử bằng vector tên, alias và độ giống chuỗi, cùng prompt phán cụm. Lời phán cũ được tái dùng theo khoá
đầu vào như hiện nay. Đó là điều kiện để tập node canonical và id node giữ nguyên giữa hai chuỗi.

### 4. Stage canonical — A5 mới: mô tả, neo và trạng thái dạy

**Câu ứng viên cho neo** được dựng bằng mã ngay sau bước gộp, với luật y hệt C8 hiện nay.
- Vùng tìm gồm:
  - chunk định nghĩa mà A5 chọn;
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

Nghiệm thu sẽ chọn mặc định.

**Các nhánh khác giữ nguyên ngữ nghĩa C8:**
- Không có ứng viên trong vùng nội dung thì không gọi LLM: tên chỉ xuất hiện ngoài vùng nội dung → `mentioned_only` (ghi vai trò vùng); không thấy
  ở đâu → `unchecked`.
- Lời phán `prior_knowledge` qua một lượt xác minh độc lập như hiện nay. Không xác nhận thì hạ xuống `uncertain`.
- Luật "khái niệm chỉ có căn cứ ngoài vùng nội dung thì không hỏi" **giữ nguyên**. Sửa nó thuộc vé 05, để đo riêng tác động.

**Ghi lên node** đúng các trường C8 đang ghi: `teaching_status`, `anchor`, `teaching_chunk_ids`, `teaching_order_index`, `teaching_conflict`.
Thêm hai việc:
- chunk chứa câu neo được thêm vào `defining_chunk_ids` theo luật chỉ thêm, bản trước giữ ở trường nguồn như provenance đang làm;
- vị trí dạy sớm nhất được tính lại.

Payload canonical có thêm nhật ký neo và nhật ký lời phán của phần neo, cùng dạng với chuỗi v3. Media không qua bước này.

### 5. Stage canonical — danh tính

- **Lọc node:** như hiện nay. Chỉ xét khái niệm học được không có trạng thái `prior_knowledge` hay `not_subject_matter`.
- **Đề cử:** các nguồn của danh tính hiện nay:
  - tên hoặc alias chuẩn hoá trùng;
  - viết tắt theo chữ đầu;
  - tiền tố chung lặp lại trong chính tài liệu;
  - cùng câu neo;
  - độ gần mô tả: top-3 mỗi phía, cosine ≥ 0,85, trên vector mô tả **cuối** của A5 mới.

  Các tham số nằm trong config. Vector mô tả được embed trong stage canonical bằng đúng mô hình embedding đã ghi ở manifest (ADR 0004). Vector chỉ
  đề cử (ADR 0006).
- **Phán theo cụm.** Các cặp nghi trùng được gom thành thành phần liên thông, cắt theo trần cỡ cụm cấu hình được, gọi là cụm ứng viên danh tính.
  Mỗi cụm một lời gọi. Đầu vào mỗi khái niệm: tên, alias, mô tả, câu neo. Đầu ra là phân hoạch cụm thành các nhóm, kèm quan hệ trong tập đóng
  hiện có: `dong_nhat`, `truong_hop_rieng`, `bang_nhau_theo_menh_de`, `menh_de_khac`, `doi_tuong_khac_loai`, `khac`. Tiêu chí là cùng ngoại
  diên (R8b). Prompt nhắc rằng một câu thường định nghĩa nhiều khái niệm khác nhau.
- **Xác minh:** mọi cặp được phán đồng nhất qua một lời gọi độc lập, chỉ thấy hai hồ sơ, như lượt xác minh hiện nay. Chỉ `dong_nhat` giữ gộp.
- **Luật gộp** như hiện nay:
  - chỉ gộp nhóm mà mọi cặp đều đồng nhất sau xác minh;
  - đại diện là thành viên được dạy sớm nhất, không có thì thành viên sớm nhất;
  - tên và alias của thành viên thành alias của đại diện, ghi nguồn danh tính;
  - nhóm thiếu phán là nhóm mở, tính vào Q2.
- **Đầu ra:** bản đồ danh tính (khái niệm → đại diện), nhóm và cặp còn mở, nhật ký danh tính và nhật ký lời phán. Tất cả nằm trong payload
  canonical. **Tập node canonical không đổi.**

### 6. Chuỗi đồ thị gộp

Thứ tự stage của chuỗi gộp như sau:

```
clusters (A6–A7, áp bản đồ danh tính) → mentions → main_edges → secondary_edges → validated (A9) → concept_labels → stages (A10) → module_titles
```

- **Áp bản đồ danh tính ở stage đầu:** node bị gộp rời `nodes` sang `merged_nodes`, alias của đại diện được cập nhật. Mọi stage sau làm việc trên
  tập node đã gộp. Quyết định của người duyệt (`--identity-review`) được áp tại đây, thắng phán của mô hình; định dạng tệp duyệt không đổi.
- **Mention map, viện dẫn và cặp nghi tiên quyết** dựng trên tập node đã gộp, với chunk định nghĩa đã có chunk neo.
- **A8:** pass chính và pass phụ nhận upstream `mentions` của chuỗi gộp. Hợp đồng cạnh theo định nghĩa và yêu cầu kiểu tiên quyết bật khi
  canonical khai báo đã có neo. Cửa sổ định nghĩa, bộ kiểm và các luật khác không đổi.
- **`--stop-after`:** giá trị `provenance`, `teaching`, `identity` không hợp lệ trong chuỗi gộp, báo lỗi kèm gợi ý "đã nằm trong stage canonical".
  `--dry-run` liệt kê các stage của chuỗi gộp.
- **Payload cuối** giữ đủ các trường mà A10, bộ chấm và công cụ nghiên cứu đang đọc: `identity_map`, `merged_nodes`, nhật ký neo, nhật ký danh
  tính, trường neo trên node.

### 7. Hợp đồng và tương thích

- **Đọc artifact cũ:** A8, A10, bộ chấm và công cụ chấm vẫn đọc được artifact sinh từ chuỗi v3 (có stage `identity`).
- **Vàng:** vì id node không đổi, vàng cũ và vàng T-01 chấm được trên đồ thị chuỗi gộp không cần chuyển đổi. Bộ chấm áp bản đồ danh tính lên vàng như
  hiện nay.
- **Chi phí:** `cost_summary` của stage canonical tách theo phần (gộp cụm, mô tả, neo, xác minh kiến thức nền, danh tính, xác minh danh tính) và
  có một tổng. Đo thời gian từng phần theo cơ chế đo stage hiện có.

### 8. Tài liệu đi kèm

- ADR mới (0011): "neo, trạng thái dạy và danh tính chạy trong stage canonical; danh tính vẫn là bản đồ phủ".
- `CONTEXT.md` cập nhật hai mục. "Bản đồ danh tính": tính trong stage canonical, áp ở đầu chuỗi đồ thị. "Ứng viên danh tính mở rộng": vector mô tả
  cuối của A5 thay vector A6. Thêm mục "Câu neo" và "Trạng thái dạy" nếu domain-modeling thấy cần.
- `doc/spec-addendum.md`: sơ đồ pha A và mục A9', A9'' trỏ sang spec này.

## Testing Decisions

**Một test tốt** kiểm hành vi nhìn từ ngoài: hợp đồng artifact, số lời gọi mô hình, việc tái dùng cache, việc từ chối hay dừng có thông báo.
Không kiểm chi tiết cài đặt bên trong. Mỗi luật chặn phải được thấy đỏ ít nhất một lần (AGENTS.md mục 5).

**Seam chính: stage canonical chạy trên fixture thật.** Đây là seam đã có, cao nhất, và chứa phần lớn hành vi mới. Mẫu sẵn có là các test pipeline
A4: kho fixture từ tài liệu thật, mô hình giả trả lời theo hình dạng đầu vào, embedding phát lại. Các test cần có:
- neo và trạng thái dạy được ghi đúng trường trên node. Mã câu neo không có trong ứng viên thì bị bác; câu trích ngoài ngữ cảnh thì bị bác;
- một khái niệm hỏng trong lô chỉ làm khái niệm đó bị hỏi lại riêng. Hỏng tiếp thì nhận `uncertain` và được giữ;
- khái niệm không có ứng viên không sinh lời gọi nào;
- `prior_knowledge` không được xác minh thì hạ xuống `uncertain`;
- chunk neo được thêm vào chunk định nghĩa và không xoá chunk cũ;
- chỉ nhóm mà mọi cặp đồng nhất và qua xác minh mới vào bản đồ; một cặp bị xác minh bác thì cả nhóm không gộp;
- tập id node canonical của chuỗi gộp trùng chuỗi v3 trên cùng pool ứng viên, nên một bộ vàng gán trên canonical chuỗi v3 chấm được trên đồ thị
  chuỗi gộp;
- đổi riêng phần A5 thì không sinh lời gọi gộp cụm mới (lời phán cụm được tái dùng);
- đổi kích thước lô neo, ngưỡng đề cử hay chuỗi thì đổi khoá cache.

**Seam phụ: bộ điều phối chuỗi đồ thị và đầu vào của A8.** Mẫu sẵn có là test điều phối với stage giả và test hợp đồng pass chính. Các test cần có:
- thứ tự stage của chuỗi gộp và chuỗi v3;
- `--stop-after` hợp lệ và không hợp lệ;
- `--dry-run` không gọi mô hình hay embedding;
- bản đồ danh tính và quyết định người duyệt được áp đúng một lần ở stage đầu;
- A8 bật hợp đồng cạnh theo định nghĩa với upstream chuỗi gộp và vẫn chạy với upstream chuỗi v3.

**Test miền hiện có** của dựng câu ứng viên, kiểm phản hồi neo, sinh cặp danh tính, lập bản đồ, xác minh giữ nguyên và phải tiếp tục xanh, vì chuỗi
gộp dùng lại các hàm đó.

**Hồi quy:** artifact chuỗi v3 trong fixture vẫn qua A8, A10 và bộ chấm. Chuỗi v3 vẫn là mặc định.

**Nghiệm thu nghiên cứu (Claude, sau khi nhân viên báo xong).** Trên 6 tài liệu phát triển tiếng Việt có A4 đầy đủ (doc-1, nhap-mon-ml,
naive-bayes, doc-6, xstk-ch3-1, doc-4), so với artifact chuỗi v3 đã có:
- độ khớp trạng thái dạy và câu neo theo từng khái niệm. Claude đọc mọi chỗ lệch trên đích vàng và một mẫu chỗ lệch khác. Câu neo đúng trên đích
  vàng không thấp hơn mốc 79/84;
- nhóm gộp danh tính: số gộp sai mà vàng phát hiện được không tăng (mốc: 3);
- E4 trên doc-1, xstk, doc-4 với pass phụ ML cấu hình E5, và phép quy lỗi thượng nguồn chạy lại: hồi tưởng và độ chính xác bao đóng, Q7, Q7b
  không giảm quá mức nhiễu;
- số lời gọi, USD và phút của stage canonical và chuỗi đồ thị, trước và sau, trên doc-4.

Lượt này tốn tiền vì phải chạy lại A5 mới trên 6 tài liệu và pass chính trên 3 tài liệu vàng; ước dưới 5 USD. Phải dry-run và được chủ dự án duyệt
trước.

## Out of Scope

Spec này không làm các việc sau:
- **Bỏ LLM ở neo, trạng thái dạy hay danh tính** (bản không LLM cho seminar). Spec chỉ gom chúng về một chỗ để việc thay sau này dễ hơn.
- **Cờ gợi ý "dạy ở đây" trong A3.** Đổi prompt A3 mất cache A3 của mọi tài liệu. Chỉ cân nhắc nếu nghiệm thu cho thấy A5 mới thiếu thông tin.
- **Sửa luật vai trò vùng A2** ("tiêu đề lặp ở đầu nhiều mục là đề cương") và **luật bỏ qua của C8**. Cả hai thuộc vé 05; spec này giữ nguyên hành
  vi để đo riêng.
- **Gộp danh tính thẳng vào tập node của A4**, vì sẽ đổi id node và làm vàng hết khớp (mục 1).
- Chuỗi canonical chỉ có lớp tên (D-01) và bất kỳ việc xuất phiếu D-01 nào.
- Pass phụ ML (vé 11) và việc tích hợp nó; mở rộng cửa sổ định nghĩa hay ứng viên không nguyên văn (E7).
- `a8-gold-sheet` dùng trạng thái dạy để chọn khái niệm của chương: việc tiếp theo nếu cần.
- Tài liệu tiếng Anh, vì đồ án chỉ làm tiếng Việt.

## Further Notes

- **Số đo nền** (báo cáo quy lỗi, mục 4b):
  - câu neo trùng câu bằng chứng A3 ở 88,6% khái niệm, cùng chunk ở 91,6%;
  - provenance quyết định 3% số neo; phần C8 tự tìm bằng mã chiếm 5,2%;
  - nguồn gộp chính của danh tính là độ gần mô tả.
- **Chi phí hiện nay trên doc-4:** provenance 89 lời gọi (0,086 USD), C8 618 lời gọi (0,402 USD), danh tính 907 lời gọi (0,270 USD). Gộp bỏ chắc
  chắn được ba stage nối tiếp và phần lớn số lời gọi. Tiền bớt ít hơn 0,76 USD vì câu ứng viên và hồ sơ danh tính vẫn phải gửi đi; con số thật
  đo khi nghiệm thu.
- **Rủi ro chính và cách đo:**
  - C8 cố ý phán một khái niệm mỗi lời gọi; gom vào lô A5 có thể làm neo kém đi. Tham số lô neo cho phép đo cả hai trên cùng tài liệu;
  - phán danh tính theo cụm có thể gộp sai nhiều hơn phán từng cặp. Lượt xác minh từng cặp đồng nhất được giữ để chặn;
  - vector mô tả cuối được embed sớm hơn (ở stage canonical); mô hình và số chiều không đổi nên tập cặp đề cử phải giống chuỗi v3 trên cùng mô
    tả. Lệch thì đó là dấu hiệu lỗi cài đặt.
- **Quan hệ với vé khác:**
  - vé 05 (sửa luật A2 và C8) nên làm sau spec này và đo bằng cùng bộ công cụ;
  - việc thay LLM ở các khâu này (seminar) sẽ cắm vào đúng hai chỗ: phần neo và trạng thái dạy của A5 mới, và phần phán danh tính.
- **Sau khi chuỗi gộp thành mặc định:** một vé riêng gỡ ba stage cũ khỏi mã, và chạy lại các tài liệu phát triển để có artifact chuẩn mới.
