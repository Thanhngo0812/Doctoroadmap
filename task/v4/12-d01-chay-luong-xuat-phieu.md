# v4-12 — D-01 bước 2: chạy A2 → A9'' trên 16 cuốn học, xuất phiếu gán nhãn

**Nguồn chân lý:**
- [đặc tả D-01](D-01-dac-ta-du-lieu-pass-phu.md) (định dạng phiếu, kiểm chất lượng);
- [kiểm rộng 16 cuốn](../../report/v4-10-buoc-2b-kiem-rong-16-cuon-2026-10-05.md) (A1);
- [nghiên cứu pass phụ không LLM vòng 1](../../report/nghien-cuu-pass-phu-khong-llm-vong-1-2026-10-05.md).

**Ai:** nhân viên · **Phụ thuộc:** — · **Chi phí mô hình:** khoảng 20 USD qua Vertex. Chủ dự án duyệt ngày 2026-10-05: "duyệt chi tất cả tiền
miễn là dùng vertex".

**Trạng thái:** Claude chạy dở, bàn giao 2026-10-05 lúc 17:15 theo yêu cầu chủ dự án. Mọi tiến trình đã dừng; khâu xong đã lưu.

**Trạng thái hiện hành 2026-10-07:** 16/16 sách hoàn tất identity, ghim đúng chunks mới nhất.
Đã xuất và kiểm 5.901 phiếu / 65.525 cặp: 5.541 thật, 83 kiểm, 277 lặp. Đã kiểm định dạng toàn bộ và đọc 5 mẫu.
**Chưa đạt đủ điều kiện phiếu kiểm 5%:** chỉ có 83 mẫu sẵn có, thiếu 194 so với 277 dự kiến; không tự nhân bản vàng.
Còn cần chủ dự án/sếp chấp nhận giới hạn này hoặc bổ sung phiếu kiểm trước khi đóng đầy đủ nghiệm thu.
Bảng và giới hạn đo tại
[báo cáo 16 sách](../../report/v4-12-nghiem-thu-16-sach-2026-10-07.md).
Session pipeline 71357 và xuất phiếu 52508 đều thoát 0. Tệp bàn giao: `tmp/d01-phieu/phieu.jsonl`;
không giao `khoa.jsonl`. Không chạy A8. Guard cuối 43,2816245/75 USD; không phải billing đầy đủ.
Các dòng trạng thái phía dưới là lịch sử bàn giao, không phải trạng thái hiện hành.

**Duyệt chi mới 2026-10-06:** chủ dự án trả lời “cho phép” khi được hỏi vượt trần 25 USD để hoàn tất 16 sách qua Vertex.
Trần giám sát bảo thủ hiện hành nâng lên **75 USD**, thay các mốc 25 USD lịch sử bên dưới; không phải khoản sẽ tiêu chắc chắn.
Giữ Vertex/Flash Lite, không chạy A8; chạm 75 USD phải dừng và báo. Tạm dừng đúng cây tiến trình trước khi đổi bộ giám sát,
rồi nối checkpoint d01-12; không sửa prompt/mã pipeline/concurrency.

**Sửa kẹt 2026-10-07 theo yêu cầu chủ dự án:** D01-13 đứng ở 47 mục vì chờ limiter, không phải chờ HTTP/token.
Đã dừng luồng trước khi sửa; finally bảo đảm trả permit cho LLM/embedding, retry lỗi HTTP đọc thiếu/mất kết nối,
A3 ghi lớp lỗi theo section. Điều phối dừng/nối có giới hạn nếu 45 phút không có tiến độ, không cắt theo tổng thời gian sách.
10 test lỗi permit đã đỏ trước sửa; toàn bộ 900 test xanh. Chi tiết: `report/v4-12-ket-suat-dong-thoi-2026-10-07.md`.
Không đổi prompt/hash/model/concurrency; nối D01-13 qua Vertex, trần 75 USD, không A8. Vé vẫn chưa hoàn tất.

**Tạm ngưng theo chủ dự án 2026-10-07 07:05:** dừng cây D-01, xác nhận không còn tiến trình.
10/16 identity hoàn tất (02,03,04,08,09,10,11,12,13,16). D01-05 tới teaching v4, identity checkpoint giữ 1.088 quyết định.
Guard cuối 29,3348765/75 USD (provision, không phải billing đầy đủ). Session 80659 đã dừng.
Lệnh nối từ 05→06→07→14→15→01 nằm ở cuối `report/v4-12-ket-suat-dong-thoi-2026-10-07.md`.
Không tự chạy lại cho tới khi chủ dự án yêu cầu; vé vẫn chưa xuất phiếu/nghiệm thu cuối.

**Đã nối lại theo yêu cầu chủ dự án 2026-10-07:** session **77651**, kiểm không còn lượt cũ trước khi chạy.
Thứ tự 05→06→07→14→15→01, nối checkpoint D01-05; giữ nguyên Vertex/Flash Lite, trần 75 USD và không A8.

**Xử lý D01-01 ngay theo yêu cầu chủ dự án 2026-10-07:** đã chẩn đoán riêng trong lúc luồng chính chạy.
Mục lỗi chứa U+001A/U+001B trong câu evidence; mô hình chép literal control vào JSON, repair vẫn lỗi.
Tạm dừng luồng chính ở D01-07 trước sửa decoder chung; dùng stdlib strict=False chỉ cho phép control trong chuỗi,
không đổi evidence/nguồn/prompt và vẫn bác JSON sai cấu trúc. Test câu nguồn thật đỏ trước sửa.
Chi tiết và kết quả nghiệm thu: `report/v4-12-d01-01-json-2026-10-07.md`.

Toàn bộ 904 test xanh. Session chính 71357 chạy 07→14→15; session riêng 16996 xử lý 01 ngay,
nhật ký riêng `tmp/pass-phu-ml/d01-01-sua-json-20261007.jsonl`. D01-01 đã bỏ khỏi hàng đợi chính để không chạy trùng.
Trần 75 USD tính trên toàn bộ sách, không phải 75 USD mỗi luồng. Trước nối đã xong 12/16 (D01-06 cũng hoàn tất).

D01-01 A3 đã nghiệm thu trên sách thật: candidates v1, 179/179 mục hoàn tất, failed_section_count=0,
coverage_incomplete=false, failed_sections=[]; A4 canonical v1 đã xong. Session riêng tiếp tới identity.

**Cập nhật nhân viên, 2026-10-06:** sửa xong A2 dùng retry chung/tôn trọng Retry-After, A3 coverage_incomplete thoát khác 0
và in mục hỏng; script nhận lỗi ở cả stdout/stderr, kiểm cả Vertex và gemini-3.1-flash-lite.
Test A2/A3 đã đỏ trước sửa, xanh sau sửa. Vé 13 phát hiện 7 sách có chữ lỗi cục bộ; chưa tự truyền cờ bỏ qua.
Chưa gọi mô hình trả tiền mới, chưa xuất bộ phiếu đầy đủ; **vé 12 chưa hoàn tất**, danh tính vẫn 2/16.
Chờ quyết định làm sạch hoặc xác nhận lỗi ở d01-02, 04, 05, 06, 07, 14, 15.
Chi lịch sử chưa đo của A3 vẫn không được gán 0. Chạy tiếp phải giữ trần khoảng 25 USD và dừng sau identity.
Báo cáo bàn giao: [v4-12](../../report/v4-12-sua-loi-va-diem-dung-2026-10-06.md).

**Cập nhật tiếp 2026-10-06, chủ dự án duyệt làm sạch:** đã tạo parse v2 mới cho 7 sách lỗi, không sửa PDF/artifact cũ.
Chunk mới: d01-02 v5, d01-04/v05 v3, d01-06/v07/v14/v15 v2. 16/16 cây parse ghim hiện qua cổng chữ.
Đã thêm checkpoint A3 theo section, kiểm bằng nối lượt lỗi với đầu ra khớp lượt liền mạch; giữ hash/prompt A3.
Đã khởi chạy tuần tự qua Vertex, session 31492, nhật ký `tmp/pass-phu-ml/d01-chay-clean-20261006.jsonl`.
Ưu tiên 9 sách không cần sửa rồi 7 sách đã sửa. Không sửa src/prompt/config khi pipeline đang chạy.
Bộ giám sát trong điều phối kiểm trần bảo thủ 25 USD trước/sau stage và mỗi 10 giây, gồm 3 USD dự phòng chi lịch sử chưa đo.
Đây không phải đối soát hoá đơn: token thiếu không được coi là 0; embedding và checkpoint chồng nhau được dự phòng bảo thủ.
Báo cáo làm sạch/kiểm thử: [v4-12 làm sạch](../../report/v4-12-lam-sach-va-chay-tiep-2026-10-06.md).

**Nối lượt:** session 31492 đã dừng an toàn ở khoảng chờ retry sau A3; không còn lời gọi LLM đang chạy khi sửa mã.
Thêm test đỏ và chốt cổng 40% trên kết quả checkpoint phục hồi, 52 test liên quan xanh. D01-01 đã lưu 178/179 mục, 5 mục rỗng.
Session đang chạy thay thế: **77337**, cùng lệnh/nhật ký/model/config/trần chi. Không khởi chạy bản 31492 lần nữa.

## Quyết định đã chốt — không đổi trong vé này

- **Chỉ qua Vertex** (`llm_transport=vertex`), chỉ `gemini-3.1-flash-lite`. Script điều phối tự dừng nếu đường gọi không phải Vertex.
- **Quyền dùng sách:** chủ dự án đã tự kiểm định 16 cuốn, kể cả gửi lên Gemini. **Không mở 2 cuốn `document-data/test/`** (tập giữ lại T-01).
- **Dừng sau A9'' (danh tính), không chạy A8.** Chủ dự án đồng ý. Đo 0 USD cho thấy bỏ đặc trưng pass chính không làm hụt có ý nghĩa bộ kiểm cạnh.
- **A1 đã xong cho cả 16 cuốn.**
  - Bộ đọc chữ là `--pdf-backend pypdfium2`, vì docling-parse giải mã hỏng d01-01.
  - **Sơ đồ tiêu đề mặc định** (không `vn-textbook`): `vn-textbook` lồng sai "CHƯƠNG II" vào mục "BÀI TẬP CHƯƠNG I" ở d01-02.
- **Chuỗi lệnh theo đúng chuỗi v3** của tài liệu tiếng Việt (doc-4, xstk):
  `label-roles --allow-spend` → `a3` → `a4 --names-only` → `roadmap --dry-run --stop-after identity` →
  `roadmap --allow-spend --stop-after identity`.

## Trạng thái bàn giao

| cuốn | lĩnh vực | đã có | còn lại |
|---|---|---|---|
| d01-01 | Toán | chunk vai trò v3 (gán trên v2 pypdfium2) | A3 (3 lượt đều "coverage_incomplete", không lưu) → A4 → roadmap |
| d01-02 | Toán | **xong tới danh tính** (graph v5); 0,89 USD | — |
| d01-03 | Hoá | **xong tới danh tính** (graph v5); 1,50 USD | — |
| d01-04 | Hoá | tới C8 (graph v4); 1,57 USD | `roadmap --stop-after identity` (tự tái dùng v1–v4) |
| d01-05 | Sinh | chunk vai trò v2 | A3 (lượt dở bị dừng) → A4 → roadmap |
| d01-06 → d01-15 | 6 lĩnh vực | chunk v1 (A1) | A2 → A3 → A4 → roadmap |
| d01-16 | Nông nghiệp | chunk vai trò v2. Vòng A2 của Claude chưa dừng hẳn, chạy xong lúc 17:22, sau yêu cầu ngưng; khoảng 0,005 USD | A3 → A4 → roadmap |

Chi đã ghi trong manifest: 3,96 USD. Các lượt A3 hỏng của d01-01 và d01-05 không để lại số đo, ước 2–3 USD; số chính xác xem trên hoá đơn Vertex.
Nhật ký từng bước: `tmp/pass-phu-ml/d01-chay*.jsonl`.

## Việc cần làm

### 1. Sửa hai lỗi chặn trước khi chạy tiếp (đo được ngày 2026-10-05)

- **A2 không thử lại.**
  - `composition.build_region_roles` dựng mô hình với `max_retries=0`. Vertex trả **HTTP 429 RESOURCE_EXHAUSTED** (hạn mức dùng chung) mỗi khi
    có khâu khác cùng gọi, nên một lời gọi dính 429 là hỏng cả khâu. Đã gặp ở 10 cuốn, kể cả khi chạy tuần tự.
  - Sửa: cho A2 dùng cùng chính sách thử lại với các khâu khác, chờ tăng dần, tôn trọng `Retry-After`.
  - Không đổi prompt, khoá cache hay đầu ra.
  - Test: giả lập 429 rồi thành công thì khâu hoàn tất. Test phải đỏ trên mã hiện tại.
- **A3 báo thành công khi không ghi gì.**
  - Khi `coverage_incomplete` (có mục hỏng, ở đây do 429), lệnh `a3` in "artifact: không ghi vì coverage_incomplete" mà **vẫn thoát mã 0**.
  - Sửa: thoát mã khác 0 và in rõ các mục hỏng. Test.
- **Nên làm thêm, có thể tách vé:**
  - A3 không có điểm lưu, nên mỗi lần chạy lại tốn trọn chi phí (d01-01 đã mất 3 lượt). Cần lưu kết quả theo mục và tái dùng ở lượt sau,
    không đổi đầu ra.
  - Thử lại của A3 nên chờ lâu hơn khi gặp 429. Hiện chỉ chờ khoảng 1, 2, 4 giây.

### 2. Chạy tiếp, **mỗi lúc một cuốn**

- Chạy song song nhiều cuốn làm tăng 429 và không nhanh hơn.
- Dùng được `scripts/pass-phu-ml/chay_d01.py` của Claude:
  - chờ `ingest` xong;
  - chạy lại khi gặp lỗi tạm thời hoặc A3 thiếu mục;
  - kiểm có artifact ứng viên rồi mới sang A4;
  - ghi nhật ký.
- Lệnh mẫu: `.venv/Scripts/python.exe scripts/pass-phu-ml/chay_d01.py --chi=d01-04,d01-05,...,d01-16,d01-01 --nhat-ky=tmp/pass-phu-ml/d01-chay-nv.jsonl`.
  Cuốn đã xong khâu nào thì luồng tự tái dùng khâu đó.
- **Không bọc lệnh bằng `timeout`**: một cuốn có thể chạy quá 30 phút.

### 3. Xuất phiếu

- Môi trường riêng `tmp/venv-ml` (cần underthesea để khớp tên theo ranh giới từ). Cách dựng ở mục "Chạy lại" của báo cáo vòng 1.
- Lệnh: `tmp/venv-ml/Scripts/python.exe scripts/pass-phu-ml/xuat_phieu.py`.
- Đầu ra:
  - `tmp/d01-phieu/phieu.jsonl` (giao chủ dự án cho agentic);
  - `tmp/d01-phieu/khoa.jsonl` (đáp án phiếu kiểm và nguồn phiếu lặp). **Không giao `khoa.jsonl` cho agentic.**
- Đã thử trên xstk: 71 phiếu, 696 cặp, định dạng đúng D-01.

### 4. Sổ chi

`scripts/do-chi-phi/bao_cao.py <doc>` cho từng cuốn; cộng tổng. Báo kèm cờ "thiếu": Vertex đôi khi không trả số token.

## Nghiệm thu

- 16/16 cuốn có artifact `identity`. Bảng mỗi cuốn: số khái niệm; số khái niệm làm được đích (`taught`/`uncertain`, học được); phút; USD.
- Theo duyệt mới 2026-10-06: trần giám sát bảo thủ 75 USD cho 16 sách; chạm trần thì dừng và báo. Báo riêng chi đo được và giới hạn đo.
- Phiếu: số phiếu thật, phiếu kiểm, phiếu lặp, tổng cặp cần gán. Kiểm 5 phiếu ngẫu nhiên bằng mắt (câu cửa sổ, câu neo, ứng viên có tên trong câu).
- Sửa A2 và A3: test mới đỏ trên mã cũ, xanh sau sửa; toàn bộ test xanh; khoá cache các khâu không đổi.
- Không tệp nào trong `document-data/test/` bị đọc.

## Ghi nhận, không sửa trong vé này

- **A2 gán sai vùng ở d01-02:** trang 1–96 (Chương I–III) bị gán `mo_dau`.
  - Lỗi do luật cấu trúc tất định; LLM chỉ được hỏi 4 lần.
  - Có dòng đầu trang VNI "BOÄ MOÂN TOAÙN" bị nhận là tiêu đề.
  - Cuốn này vì thế ít khái niệm được dạy hơn. Để vé A2 sau.
- **`vn-textbook` đẩy tiêu đề không đánh số** ("BÀI TẬP CHƯƠNG I") lên trên "CHƯƠNG II". Để vé A1/A2 sau.

## Điểm bàn giao tạm ngưng — 2026-10-06 16:57

Chủ dự án yêu cầu dừng để tan làm. Đã dừng cây tiến trình D-01, xác nhận không còn tiến trình gọi mô hình của lượt này.
3/16 sách hoàn tất identity (03, 08, 09; đều v5). D01-10 dừng ở neo, checkpoint giữ 488 quyết định;
A2–A4 và graph tới provenance v3 đã xong. D01-01 giữ 178/179 mục A3, còn một mục lỗi sau năm lần thử.
Guard cuối 16,684124/25 USD gồm dự phòng, không phải tổng chi billing đầy đủ. Vé chưa hoàn tất, chưa xuất phiếu cuối.
Lệnh nối lại và giới hạn đo ghi trong `report/v4-12-lam-sach-va-chay-tiep-2026-10-06.md`.
Không tự khởi chạy lại cho tới khi chủ dự án yêu cầu tiếp tục.
