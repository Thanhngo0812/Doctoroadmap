# Vé 12 — trạng thái khi chủ dự án yêu cầu tạm ngưng (2026-09-29)

## Cập nhật 2026-10-01: tiếp tục và kiểm chứng pass phụ

Chủ dự án cho tiếp tục và duyệt ngân sách lớn, nhưng pilot 216 cặp được giữ làm cổng chất lượng trước khi chi cho 12.236 cặp toàn kho. Phiên pilot đầu bị ngắt sau 84/153 cặp doc-1: 80 phán quyết lỗi `unknown_evidence_kind`, do prompt/schema pass phụ không khóa ba giá trị hợp lệ. Đã viết test đỏ rồi sửa prompt và enum; hash mới tách checkpoint cũ. Không xóa checkpoint/ledger cũ. Pilot mới hoàn tất doc-1 và doc-2 ở kho đánh giá riêng, **không ghi pass phụ production**. Ledger chung hai lượt: 0,853544 USD, dưới trần 2 USD; chi tăng thêm sau tiếp tục là khoảng 0,536007 USD.

| Phạm vi vàng sau cùng phép map danh tính | Main cũ P/R trực tiếp | Main mới P/R trực tiếp | Main mới + pilot P/R trực tiếp | Cạnh cứng pilot |
|---|---:|---:|---:|---:|
| doc-1, 25 đích / 28 cạnh vàng | 17/21 · 17/28 | 11/14 · 11/28 | **14/29 · 14/28** | 15 (3 khớp vàng) |
| doc-2, 22 đích / 32 cạnh vàng | 12/21 · 12/32 | 7/11 · 7/32 | **9/13 · 9/32** | 2 (2 khớp vàng) |

Bao đóng: doc-1 main mới 23/24 P, 23/131 R → pilot 67/82 P, 67/131 R; doc-2 12/20 P, 12/68 R → pilot 14/27 P, 14/68 R. Doc-1 tăng độ phủ nhưng 12/15 cạnh cứng mới không khớp cạnh vàng **trực tiếp**. Trong số 15 cạnh đó, **10 cùng chiều với bao đóng vàng** (có thể là tiên quyết gián tiếp), **1 ngược chiều bao đóng vàng**, còn 4 ngoài cả hai chiều; vì vậy không được gọi cả 12 cạnh không khớp là sai kiến thức. Tuy nhiên đồ thị yêu cầu cạnh trực tiếp và cứng đáng tin: precision trực tiếp đo trên vàng của doc-1 rơi từ 0,786 xuống 0,483, thấp hơn cả main cũ 0,810; doc-2 recall vẫn chỉ 9/32. **Chưa đạt cổng chấp nhận chạy rộng**. Chi thêm khoảng 31,30 USD cho toàn pass phụ lúc này sẽ khuếch đại một hợp đồng chưa được chứng minh là đáng tin. Quyết định kỹ thuật: dừng paid secondary production dù ngân sách được duyệt; không coi vé 12 đã xong.

Sau pilot, việc cần làm trước lượt paid mới: đối chiếu mù các cạnh pilot không khớp vàng với sách (ưu tiên doc-1), xác định lỗi là vàng thiếu, mô hình suy diễn quá rộng, hay cửa sổ neo sai; sửa đúng nguyên nhân và chứng minh trên mẫu giữ lại độc lập. Sau đó mới dry-run lại và cân nhắc chạy production. Không được dùng tập vàng để chọn cặp production hoặc nhét nhãn vàng vào prompt.

**Tạm ngưng mọi lời gọi mô hình.** Mã chưa commit; A8 pass phụ production và pilot chưa chạy trả tiền. Không coi vé 12 đã hoàn tất hoặc đồ thị/lộ trình đã đạt chuẩn.

## Đã làm và kiểm tra

- Đổi luồng thành A6 → A7 → neo → danh tính → A8 main → A8 secondary → A9 → nhãn → A10. A8 chỉ nhận đại diện `taught`/`uncertain` làm đích; `mentioned_only` vẫn là ngữ cảnh. Cạnh `can_de_hieu` cần quote nguyên văn trong cửa sổ định nghĩa; `cong_cu` là cạnh mềm, hiển thị riêng và không vào phụ thuộc cứng. Prompt hash đổi có chủ đích. A6 dùng ngưỡng tần suất tên theo tài liệu; A7 bỏ cụm tín hiệu vi/en. A7 lượt thực tế vẫn dựa vào evidence A3 vì chạy trước neo; nhánh anchor chỉ áp dụng nếu đầu vào đã có neo.
- Test không mạng đã phủ quote đúng/sai cửa sổ, chunk khác, diễn đạt khác, edge công cụ, danh tính/mentioned-only, đa ngôn ngữ, và fallback pass phụ sau một lần sửa. Full unit+integration đã xanh trước khi thêm retry I/O Windows; sau đó riêng `tests/unit/infrastructure/test_a3_artifacts.py` xanh 17/17 (test mới đỏ trước fix). Chưa chạy lại full suite sau fix I/O.
- Sáu tài liệu hoàn tất A6/A7/neo/danh tính: doc-1 v38–41, doc-2 v30–33, doc-3 v21–24, doc-6 v10–13, naive-bayes v39–42, nhap-mon-ml v39–42. Sổ `artifacts/v3-r12-pre-a8`: 2.476 HTTP completion Vertex, 1,10131325 USD; embedding 858 text, **dự phòng trên theo byte** 0,029745 USD (không phải hoá đơn thực). Tên bị coi quá chung ở ngưỡng 50% chunk lần lượt: **0, 0, 0, 2, 0, 2**.
- A8 main sáu tài liệu hoàn tất: doc-1 v42 (62 phiên, artifact 0,346234 USD); doc-2 v34 (344, 1,610447); doc-3 v25 (31, 0,043298); doc-6 v14 (1, 0,004433); naive-bayes v43 (1, 0,01626125); nhap-mon-ml v43 (19, 0,111985). Sổ `artifacts/v3-r12-main-a8/llm-ledger.json`: **649 HTTP completion, 2,14138175 USD**, tất cả settled, dưới trần 2,50 USD. Sổ cao hơn tổng cost trong artifact 0,0087235 USD vì lỗi ghi checkpoint Windows sau lời gọi đã trả tiền; đã thêm retry ngắn cho `os.replace`, resume từ checkpoint, không làm lại các phiên đã lưu.

## Pass phụ: chỉ dry-run, chưa chi

| Tài liệu | Cặp pending | Cặp hỏi hai chiều | Calls dự kiến | USD planner |
|---|---:|---:|---:|---:|
| doc-1 | 3.471 | 3.103 | 6.206 | 7,607423 |
| doc-2 | 9.513 | 7.933 | 15.866 | 20,876407 |
| doc-3 | 248 | 239 | 478 | 0,498725 |
| doc-6 | 0 | 0 | 0 | 0 |
| naive-bayes | 0 | 0 | 0 | 0 |
| nhap-mon-ml | 997 | 961 | 1.922 | 2,316767 |
| **Tổng** | **14.229** | **12.236** | **24.472** | **31,299322** |

Planner không phải trần chi: cạnh mới có thể tỉa cặp, còn sửa JSON/retry có thể tăng calls. Không dùng trần A8 main còn dư để chạy secondary.

Số cặp lớn chủ yếu do luật F126 đã mở pass phụ tuyến `chapter` ra liên cụm, **không phải** riêng thay đổi hard-only ở vé 12. Trên main mới, nếu giả sử soft cũng đủ để tỉa thì chỉ giảm khoảng 380/12.236 cặp (3,1%). doc-2 main cũ v4 đã có 9.984 `suspected_pairs`; áp luật tuyển hiện nay lên artifact đó vẫn ra 7.446 cặp hỏi. Artifact secondary cũ v5 chỉ phán 565 cặp vì thuộc niên đại lọc cụm khác; không được dùng 565 làm baseline cùng luật. Sáu artifact secondary cũ ghi 3.668/565/67/151/124/157 cặp đã xử lý và nhận 245/49/4/1/15/20 cạnh lần lượt; các số này không phải precision vàng.

## Tín hiệu chất lượng main-only, chưa phải kết quả cuối

Chấm hai đầu trong cùng tập đích vàng, ánh xạ cả main cũ và mới về **cùng** đại diện danh tính mới. doc-1: 25 đích/28 cạnh vàng; direct cũ P=17/21, R=17/28; mới P=11/14, R=11/28. Bao đóng cũ P=55/55, R=55/131; mới P=23/24, R=23/131. doc-2: 22 đích/32 cạnh vàng; direct cũ P=12/21, R=12/32; mới P=7/11, R=7/32. Bao đóng cũ P=23/35, R=23/68; mới P=12/20, R=12/68. Độ phủ giảm đáng kể, nên phải kiểm pilot pass phụ trước khi kết luận R12 cải thiện đồ thị.

Pilot evaluation-only đã được **dry-run 0 USD**: chỉ chọn ID cặp có hai đầu thuộc tập đích vàng (không đưa nhãn cạnh vàng vào prompt), doc-1 153 cặp/306 calls/0,427065 USD planner; doc-2 63 cặp/126 calls/0,150134 USD; tổng 216 cặp/432 calls/0,577199 USD trước retry. Script `scripts/doc-lo-trinh/chay_a8_secondary_pilot_v3.py` dùng kho riêng `artifacts/v3-r12-secondary-pilot`, mặc định dry-run, hard cap tối đa 2 USD nếu về sau được duyệt. **Chưa có quyền chạy pilot trả tiền.**

## Khi được tiếp tục

1. Chạy lại full test sau fix I/O; kiểm pilot isolation test và review diff. Không tự chi tiền.
2. Nếu chủ dự án duyệt riêng pilot, chạy trong kho evaluation với sổ hard cap; chấm direct/closure vàng và lấy mẫu cạnh cứng/công cụ để chấm mù. Quyết định có chạy pass phụ toàn kho hay sửa hợp đồng dựa trên kết quả, không âm thầm tỉa generator production.
3. Sau khi A8 secondary được quyết và chạy, mới chạy A9/A10, chấm Q6/Q7/Q7b, `roadmap-target`, số cạnh cứng/mềm, và nghiệm thu đầy đủ vé 12. Hiện chưa có các số cuối này.
