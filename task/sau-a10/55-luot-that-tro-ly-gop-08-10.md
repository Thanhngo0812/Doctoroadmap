# SA-55 — Lượt thật trợ lý gộp cho SA-08 và SA-10: 30 lượt hỏi trên bốn cuốn, có ghi phản hồi để phát lại

**Nguồn chân lý:**
- [SA-08](08-tro-ly-agent-lat-cat-dau.md) và [SA-10](10-tro-ly-du-cong-cu-nhac-nen-hoi-thoai.md), mục "Tiêu chí nghiệm thu", phần lượt thật;
- [ADR 0012](../../doc/adr/0012-tro-ly-la-agent-goi-cong-cu.md): tối đa 5 vòng, khoảng 0,01 USD mỗi lượt;
- [spec B2](../../doc/pha-b2-spec.md): phiên module, phiên toàn lộ trình, `answer-2`;
- khuôn bộ chạy có tiền: `scripts/phase-b/sa43_dryrun.py`, `scripts/phase-b/sa43_acceptance.py`.

**Ai:** agent Sonnet dựng bộ chạy và dry-run · chủ dự án duyệt tiền · agent chạy thật · Claude nghiệm thu ·
**Chi phí mô hình:** dự kiến dưới 0,35 USD, trần cứng 0,50 USD, chỉ `gemini-3.1-flash-lite`; dry-run trước · **Chặn bởi:** không · **Trạng thái:** sẵn sàng

## Vì sao

SA-08 và SA-10 có test đạt từ lâu nhưng còn thiếu lượt thật: USD mỗi câu, thời gian chờ, số vòng, tỉ lệ gọi công cụ sai. Gộp hai lượt thành một bộ chạy,
một lần dry-run, một lần duyệt tiền.

SA-13, số giây của bài giảng, **không chạy riêng**. Số đo lấy từ lượt sinh bài giảng của SA-21, để khỏi trả tiền hai lần.

## Dữ liệu

Graph ghim:

| cuốn | graph | kho Pha B dùng trong lượt chạy |
|---|---|---|
| doc-6 | v29 | kho JSON mới, rỗng, trong `tmp/` của worktree |
| naive-bayes | v49 | kho JSON mới, rỗng, trong `tmp/` của worktree |
| doc-1 | v8 | **bản chép** của `artifacts/phase_b/doc-1-rebuild-20261020.json`, đặt trong `tmp/` của worktree |
| nhap-mon-ml | v50 | kho JSON mới, rỗng, trong `tmp/` của worktree |

**Không dùng `artifacts/phase_b/live.json`.** Kho này có cache của tập giữ lại. Dữ liệu vào worktree theo `doc/du-lieu-phat-trien-va-fixture.md`: chỉ chép,
không liên kết.

## Bộ câu hỏi (Claude soạn ngày 2026-10-22)

`m` là phiên module theo `module_id` của graph ghim; `lộ trình` là phiên toàn lộ trình. Lượt nhiều câu chạy liên tiếp trong cùng một phiên.

**Phần SA-08** (doc-6, naive-bayes; mỗi dòng một lượt):

| # | cuốn | phiên | loại | câu hỏi |
|---|---|---|---|---|
| 1 | doc-6 | m `module_001` | định nghĩa | Cơ sở dữ liệu là gì? |
| 2 | doc-6 | m `module_002` | vì sao tiên quyết | Vì sao phải hiểu cơ sở dữ liệu trước khi học hệ quản trị CSDL? |
| 3 | doc-6 | m `module_002` | so sánh | Mức ngoài và mức quan niệm khác nhau thế nào? |
| 4 | doc-6 | lộ trình | lộ trình | Tôi muốn hiểu ba mức của một hệ CSDL thì nên học theo thứ tự nào? |
| 5 | doc-6 | lộ trình | ngoài tài liệu | Cách tối ưu chỉ mục B-tree trong PostgreSQL 16 là gì? |
| 6 | naive-bayes | m `module_002` | định nghĩa | Prior probability là gì? |
| 7 | naive-bayes | m `module_002` | vì sao tiên quyết | Vì sao cần hiểu prior probability trước posterior probability? |
| 8 | naive-bayes | m `module_003` | ví dụ | Cho một ví dụ về vấn đề xác suất bằng 0 và cách Laplace Smoothing xử lý nó. |
| 9 | naive-bayes | m `module_004` | so sánh | Bernoulli Naive Bayes khác Gaussian Naive Bayes ở điểm nào? |
| 10 | naive-bayes | m `module_005` | ngoài tài liệu | Naive Bayes so với Transformer thì cái nào dịch máy tốt hơn? |

**Phần SA-10** (doc-1 v8, nhap-mon-ml; chuỗi nhiều lượt ghi bằng "→"):

| # | cuốn | phiên | loại | câu hỏi |
|---|---|---|---|---|
| 11 | doc-1 | m `module_007` | định nghĩa | Song ánh là gì? |
| 12 | doc-1 | m `module_007` | nhiều lượt | Đơn ánh khác toàn ánh thế nào? → Còn song ánh thì sao? → Cho một ví dụ về cái đó. |
| 13 | doc-1 | m `module_008` | vì sao tiên quyết | Vì sao học nhóm abel cần biết phép tích trước? |
| 14 | doc-1 | lộ trình | lộ trình | Tôi muốn học không gian Euclid thì cần học những gì trước? |
| 15 | doc-1 | m `module_012` | ví dụ | Cho ví dụ về một ma trận chéo. |
| 16 | doc-1 | m `module_009` | so sánh | Vành khác trường ở điểm nào? |
| 17 | doc-1 | m `module_003` | nhiều lượt | Phép hợp và phép giao là gì? → Còn phần bù thì sao? |
| 18 | doc-1 | lộ trình | ngoài tài liệu | Ma trận được dùng trong đồ họa 3D OpenGL như thế nào? |
| 19 | nhap-mon-ml | m `module_009` | định nghĩa | Kém khớp là gì? |
| 20 | nhap-mon-ml | m `module_011` | vì sao tiên quyết | Vì sao cần hiểu tập huấn luyện trước khi học học có giám sát? |
| 21 | nhap-mon-ml | m `module_004` | so sánh | Phân loại và hồi qui khác nhau thế nào? |
| 22 | nhap-mon-ml | m `module_002` | ví dụ | Cho ví dụ về bài toán lọc thư rác như một bài toán học máy. |
| 23 | nhap-mon-ml | lộ trình | lộ trình | Muốn hiểu quá khớp thì nên học những khái niệm nào trước? |
| 24 | nhap-mon-ml | m `module_001` | nhiều lượt | Ridge là gì? → Còn LASSO thì sao? → Hai cái đó khác nhau ở đâu? |
| 25 | nhap-mon-ml | lộ trình | ngoài tài liệu | GPT-4 được huấn luyện với bao nhiêu tham số? |
| 26 | nhap-mon-ml | m `module_005` | hình | Phần cây quyết định có hình minh họa nào không? |
| 27 | nhap-mon-ml | lộ trình | đường học | Đường học từ dữ liệu tới mô hình đã được huấn luyện gồm những bước nào? |

Tổng: phần SA-08 có 10 lượt. Phần SA-10 có 17 dòng; ba chuỗi nhiều lượt (12, 17, 24) thêm 5 lượt, thành 22 lượt. Tổng cộng **32 lượt hỏi**; dry-run
tính trên cả 32 lượt. Với khoảng 0,01 USD mỗi lượt, dự kiến khoảng 0,32 USD.

## Cần làm

- **Bộ chạy** `scripts/phase-b/sa55_assistant_run.py`, dựng theo khuôn SA-43:
  - đọc kế hoạch JSON, gồm bảng trên, graph ghim và trần;
  - `--dry-run` in số lượt, số lời gọi tối đa (5 vòng mỗi lượt), USD tối đa theo bảng giá chung, và không gọi mạng;
  - khi chạy thật: chặn trần cứng 0,50 USD gồm cả lời gọi thử lại; ghi phản hồi từng phiên để phát lại 0 USD (`RecordingToolModel`).
- **Chặn chi phụ:** trợ lý gọi `get_lecture`, `make_quiz` hay `make_document` thì **không sinh nội dung mới có tiền**. Công cụ trả "chưa có" hoặc cache,
  và bộ chạy đếm số lần gọi. Ba công cụ này thuộc SA-14, 17, 18, nằm ngoài lượt này.
- **Báo cáo** `report/pha-b-sa55-2026-10-xx.md`, mỗi lượt một dòng:
  - USD, TTFT, tổng giây, số vòng, công cụ đã gọi, lỗi gọi công cụ;
  - có khối nhắc nền không; câu ngoài tài liệu có được gắn cờ hay từ chối không.
  
  Phần tổng hợp gồm p50 và p90 của TTFT và tổng giây, USD mỗi câu, và tỉ lệ gọi công cụ sai theo từng công cụ.
- **Phát lại 0 USD** toàn bộ phản hồi đã ghi phải ra cùng kết quả. Thêm một test phát lại vào bộ test.

## Tiêu chí nghiệm thu

- [ ] Dry-run có số lượt, số lời gọi tối đa, USD tối đa, không gọi mạng. Kết quả gửi chủ dự án; chỉ chạy thật sau khi chủ dự án duyệt bằng tin nhắn, và trích
  tin nhắn đó vào báo cáo.
- [ ] Lượt thật nằm dưới trần 0,50 USD. Chi thật lấy từ token trả về, không lấy dự toán.
- [ ] Báo đủ các số SA-08 và SA-10 yêu cầu. Tỉ lệ gọi công cụ sai của một công cụ nào đó quá 10% thì ghi nổi bật để báo chủ dự án; không tự đổi mô hình.
- [ ] Phát lại 0 USD khớp lượt thật; có test phát lại; test Pha B, kiến trúc và cổng toàn repo xanh.

## Ngoài vé

- Không đánh giá chất lượng câu trả lời bằng chấm điểm; việc đó là của SA-23.
- Không sửa prompt hay công cụ.
- Không dùng tập giữ lại, không dùng `live.json`, không gọi mô hình nào khác `gemini-3.1-flash-lite`.
