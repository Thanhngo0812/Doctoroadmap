# F85–F97 — Review đợt A6–A10 (cụm chủ đề, mention map, 2b, lộ trình)

Vòng review 30 · 2026-09-17 · Phạm vi: [`task/a6-a8-tien-quyet/`](../task/a6-a8-tien-quyet/) vé 01, 02, 03, 06, 07,
08, 09, 10 do nhân viên làm; vé 11 đang chờ tài liệu. Toàn bộ **chưa commit**, nằm trên cây `main`. Mốc so sánh:
`85816ea`. Nguồn chân lý: [spec A6–A8](../doc/A6-A8-cum-chu-de-mention-map-va-tien-quyet-spec.md), ADR 0008, 0009.

Mỗi lỗi ghi: **hiện tượng · bằng chứng · nguyên nhân · tác động · cách sửa · test · ai sửa**.

## Kết luận review ban đầu

- **Khối lượng đủ, tay nghề tốt.** Tám vé có code, test và số đo thật; 335/335 test xanh khi chặn mạng; chạy lại tốn 0
  lời gọi; chi phí mô hình được ghi đủ tới từng token (0,075 USD cho `baocao-canhan`). Prefactor vé 01 giữ nguyên A4:
  hash không đổi, bốn tài liệu vẫn `reused=true`.
- **Chưa nhận để chạy tài liệu dài, và chưa dùng cho E1/E2.** Hai lỗi làm sai đúng hai thứ đợt này định đo:
  - **F85:** định tuyến luôn chọn nhánh chương, và cả tài liệu thành một chương duy nhất.
  - **F86:** Leiden gần như không chia cụm; cụm chủ đề thực chất do vòng gộp tham lam tạo ra.
- **Một lỗi vận hành sẽ chặn vé 11 và 13 (F87):** mỗi checkpoint là một phiên bản artifact đầy đủ — 112 MB cho một tài
  liệu 26 chunk.
- **F88 đã được chủ dự án duyệt (2026-09-17)** và spec đã sửa: chu trình hai cạnh không còn đẩy cả tài liệu về lộ
  trình theo thứ tự chương; A10 xếp tầng trên đồ thị co.
- Còn lại là lệch spec vừa và nhỏ (F89–F97), cộng các lỗ test lộ ra khi chạy đột biến.

## Phản hồi thực thi của nhân viên — 2026-09-17

**Đã sửa:** F85–F95, gồm F88 sau khi chủ dự án chốt hướng c. F96–F97 là câu hỏi/phần việc riêng nên không bị đổi ngầm.

**Xác minh cuối:** 355/355 test xanh (gồm integration thật); cache-check F88 của `baocao-canhan` là `reused=true`.

Các thay đổi chính:

- Định tuyến bỏ section gốc cấp 0; chỉ coi là phân cấp thật khi dưới gốc có ít nhất hai cấp heading; chương là tổ tiên
  cấp 1. `naive-bayes` nay đi đúng nhánh `topic_cluster`.
- CPM γ mặc định bằng `sum(trọng số cạnh concept) / C(số concept, 2)`; manifest ghi công thức, mật độ và γ hiệu lực.
  Stats tách phân hoạch Leiden thô khỏi vòng gộp, số lần gộp và số/tỉ lệ concept bị vòng gộp tác động.
- Pass chính/phụ dùng checkpoint nguyên tử ngoài chuỗi version. Mỗi pass chỉ đóng một graph version khi hoàn tất;
  checkpoint được xoá sau khi đóng. Artifact `validated` từ chối edges chưa xong; `stages` chỉ nhận `validated`.
- Executor từ chối cạnh ngược chỉ có `mach_trinh_bay`; cạnh ngược tường minh bị trừ 0,1 và mức trừ nằm trong config.
- Viện dẫn bỏ ca đồng định nghĩa; mỗi viện dẫn ghi kênh và `hard`/`soft`; bộ sinh cặp dùng `citation_hard` hoặc
  `citation_soft`. Heuristic regex khái niệm thiếu bị tắt vì chưa đo precision; cờ `missing_node` của mô hình vẫn giữ.
- Lượt hỏi phụ thứ hai đảo thật `left/right`, `nodes`, `provenance_order`; cặp đã có cạnh trực tiếp ở bất kỳ chiều nào
  bị tỉa và ghi `pruned_direct_edge`.
- Bộ điều phối gọi `ValidateGraph` đúng một lần. Cắt chu trình vét cạn có trần 16 cạnh; thành phần lớn hơn dùng
  `eades_priority` và ghi phương pháp trong artifact.
- Chu trình hai node được giữ với cờ `two_way_requires` mang đủ hai cạnh/bằng chứng, không làm trượt quality gate.
  A10 co SCC hai node trước Kahn, cho hai khái niệm cùng tầng, và dừng nếu SCC lớn hơn hai node lọt qua tầng validate.

### Đột biến

- **Bị bắt bằng test mới:** R4, R8, R12, R14, R17, R20, R24, R27, R31, R32, R33, R34, R37, R40, R41.
- **Miễn có giải thích:** R13 chỉ đảo một thứ tự duyệt trước bộ sort tất định nên đầu ra và log không đổi; R25 là
  phòng thủ trùng với bộ lọc `edge_type == requires`, và test chu trình cạnh mở vẫn được giữ.
- Test hồi quy mới còn phủ root cấp 0/cây phẳng/hai làn chương, γ theo mật độ, Leiden thô hai cộng đồng, checkpoint
  resume không sinh version dở, A9/A10 từ chối edges dở, viện dẫn hard/soft, hai hồ sơ đảo thật, tỉa cạnh trực tiếp,
  validate duy nhất và heuristic chu trình 20 cạnh.

### Chạy thật lại bốn tài liệu

| Tài liệu | Route mới | Phiên chính | Làn chương | γ | Leiden thô (cụm; cụm 1–2) | Sau gộp | Gộp tác động |
|---|---|---:|---:|---:|---:|---:|---:|
| `baocao-canhan` | chapter | 16 | 5 | 0,04943 | 12; 4 | 8 | 20/36 |
| `naive-bayes` | **topic_cluster** | 6 | — | 0,04547 | 12; 5 | 7 | 22/34 |
| `nhap-mon-ml` | chapter | 19 | 2 | 0,02782 | 18; 4 | 14 | 19/75 |
| `xstk-ch3-1` | chapter | 38 | 1 | 0,01889 | 20; 6 | 14 | 38/98 |

| Tài liệu | Viện dẫn cũ → mới | Hard / soft mới | Graph version cũ → hiện tại | Dung lượng cũ → hiện tại | Version/dung lượng edges mới |
|---|---:|---:|---:|---:|---:|
| `baocao-canhan` | 261 → 164 | 66 / 98 | 68 → 78 | 117,00 → 134,60 MB | 2 / 3,47 MB |
| `naive-bayes` | 170 → 113 | 53 / 60 | 4 → 12 | 4,99 → 22,15 MB | 2 / 4,14 MB |
| `nhap-mon-ml` | 843 → 564 | 303 / 261 | 4 → 12 | 9,94 → 47,10 MB | 2 / 9,66 MB |
| `xstk-ch3-1` | 748 → 587 | 426 / 161 | 4 → 12 | 16,61 → 87,37 MB | 2 / 19,21 MB |

Mỗi tài liệu tăng đúng hai version `edges` hoàn chỉnh (main + secondary), không tăng theo số session/cặp. Tổng đợt tăng
8 version vì ngoài chuỗi sáu stage hoàn chỉnh còn có một lần đóng lại `validated` + `stages` sau khi thêm test/heuristic
R27 và F95; các lượt đó không gọi mô hình. Riêng `baocao-canhan` tăng thêm v77–v78 (4,00 MB) để nghiệm thu F88, cũng
không gọi lại mô hình. Checkpoint lớn nhất quan sát khi chạy `xstk-ch3-1` là khoảng 5,83 MB ở 150 cặp, sau đó được xoá.

## Đã kiểm

| Hạng mục | Cách kiểm | Kết quả |
|---|---|---|
| Phạm vi | `git status`, đọc toàn bộ ~2.100 dòng code mới và diff 14 file sửa | Đúng tám vé; vé 11 không có code |
| Test | toàn bộ, chặn socket/DNS, `HF_HUB_OFFLINE=1` | ✅ 335/335 |
| Vé 01 — bất biến A4 | test hash vàng; chạy `a4 … --gold` khi chặn mạng | ✅ bốn tài liệu `reused=true`, giữ v8/v7/v7/v7 |
| Tái lập | `roadmap` khi chặn mạng: `baocao-canhan` tới `stages`, ba tài liệu kia tới `mentions` | ✅ `reused=true`, không sinh phiên bản mới |
| Thư viện | kiểm thuộc tính của `leidenalg` 0.12.0 | ✅ `max_comm_size`, `community_constraint_enforcement` là thuộc tính thật |
| Đối chiếu spec | D1–D17 từng điểm | Phần lớn khớp; lệch ghi ở F85–F97 |
| Dữ liệu thật | phân tích artifact `graph` của bốn tài liệu | Ra F86, F88, F90, F91, F93 |
| Đột biến của reviewer | 41 đột biến trên bản chép | xem mục cuối |

**Làm đúng, đáng ghi nhận:**
- **Gọi mô hình:** cơ chế dùng chung gọn; usage token lấy từ API, chi phí ghi theo từng stage.
- **Executor và gộp:** executor kiểm bảy luật; nhật ký chỉ-thêm với bộ gộp tất định; pass phụ chỉ phán trong hồ sơ.
- **Tỉa và tầng 3:** chỉ tỉa qua đường có bằng chứng tường minh; chu trình giải theo thành phần liên thông mạnh với đúng
  thứ tự ưu tiên của D11; cạnh thừa chỉ đánh dấu; cờ không tự sinh node.
- **Mention map:** không bỏ dấu; khớp dài nhất bên trái; bỏ ký hiệu; kênh dense dùng lại vector chunk và chuẩn hoá hai
  phía; hai bộ đếm của sổ cặp cụm tách rời; ngưỡng tương đối.
- **A7:** trần cụm cứng, đếm theo khái niệm; không lọc thành phần liên thông lớn nhất.

---

## F85 ✅ — Định tuyến luôn chọn nhánh chương, và cả tài liệu là một chương — **đã sửa**

**Hiện tượng.**
- `plan_main_sessions` coi tài liệu là "có phân cấp" khi **bất kỳ** section nào có cha nằm trong danh sách. Chương của
  một section là tổ tiên cao nhất của nó.
- Mọi artifact chunk thật đều có section gốc `<document>` (cấp 0), mà mọi heading khác đều là con cháu của nó.

**Bằng chứng** — chạy `plan_main_sessions` thật trên sections và mention map thật:

| Tài liệu | Cấp heading dưới gốc | Định tuyến | Phiên | Số `chapter_id` khác nhau |
|---|---|---|---:|---:|
| `baocao-canhan` | 9 mục cấp 1, 17 mục cấp 2 | chapter | 16 | **1** (section gốc) |
| `naive-bayes` | **chỉ 31 mục cấp 1** | chapter | 19 | **1** (section gốc) |
| `nhap-mon-ml` | cấp 1–4 | chapter | 19 | **1** (section gốc) |
| `xstk-ch3-1` | 1 mục cấp 1, rồi cấp 2–3 | chapter | 38 | **1** (section gốc) |

- **`naive-bayes` là cây thoái hoá** theo đúng định nghĩa (mọi heading cùng một cấp), nên theo D6 phải chạy nhánh cụm.
  Code vẫn chọn nhánh chương. Lỗi đã xảy ra trên tài liệu thật của corpus.
- Làm phẳng cây của `xstk-ch3-1` (kéo mọi heading lên thẳng dưới gốc) vẫn ra `route = chapter`.
- `baocao-canhan` v66: phần "cạnh đã có trong chương" gửi cho mô hình tăng dần 2 → 955 → … → 12.565 ký tự qua 16 phiên.

**Nguyên nhân.** Fixture test không có section gốc — `parent_section_id=None` ngay ở heading — nên không bao giờ gặp
hình dạng dữ liệu thật.

**Tác động.**
- Nhánh cụm chủ đề **không bao giờ chạy**, kể cả với tài liệu phẳng chủ dự án sắp gửi riêng để thử nhánh này.
- Pass chính chạy **tuần tự toàn tài liệu**, không song song theo chương.
- Prompt phình theo số cạnh của cả tài liệu; với giáo trình vài trăm phiên sẽ lên hàng trăm nghìn ký tự.
- E2 không so được ba cấu hình định tuyến.

**Cách sửa.**
- Bỏ section cấp 0 khỏi mọi phép xét phân cấp và tìm chương.
- "Cây có phân cấp thật" nghĩa là **cây khai báo không thoái hoá**: dưới gốc có ít nhất hai cấp heading khác nhau
  (`CONTEXT.md`: Cây thoái hoá).
- Chương là tổ tiên ở **cấp chương**. Nên dùng chung luật với vé 04: một cấp heading chọn được, mặc định cấp 1, vì cây
  heading thật hay lệch khỏi chương của tác giả (spec D13).

**Test.**
- Fixture có section gốc cấp 0.
- Một tài liệu phẳng phải ra `topic_cluster`.
- Hai chương phải ra hai làn song song, và "cạnh trước" chỉ lấy trong chương.
- Thêm một test dựng từ `sections.json` thật của một tài liệu cũ.

## F86 ✅ — Leiden gần như không chia cụm — **đã sửa code; wording D3 do chủ spec chốt**

**Hiện tượng.** Với CPM, độ phân giải là mật độ tối thiểu của một cụm. Mặc định γ = 1,0, trong khi trọng số cạnh thật
có trung vị 0,29–1,28 và mật độ có trọng số của đồ thị chỉ khoảng 0,035.

**Bằng chứng.** Chạy **đúng hàm `cluster_nodes`** trên artifact `clusters` v3, chặn lời gọi tối ưu của Leiden để ghi lại
phân hoạch thô. Kết quả cuối khớp artifact ở từng node:

| Tài liệu | Leiden thô | Cụm lớn nhất | Sau vòng gộp | Khái niệm nằm trong cụm do vòng gộp tạo |
|---|---|---:|---|---:|
| `baocao-canhan` | 27 cụm, 25 cụm có 1–2 khái niệm | 3 | 8 cụm | 33/36 |
| `naive-bayes` | 23 cụm, 21 cụm có 1–2 khái niệm | 3 | 8 cụm | 34/34 |
| `nhap-mon-ml` | 55 cụm, 53 cụm có 1–2 khái niệm | 2 | 17 cụm | 75/75 |
| `xstk-ch3-1` | 74 cụm, 72 cụm có 1–2 khái niệm | 2 | 20 cụm | 98/98 |

Đổi γ bằng mật độ có trọng số (≈ 0,035): Leiden tự tạo cụm cỡ tới 11, và chỉ còn 4 (ML) và 8 (XSTK) cụm 1–2 khái niệm
cho vòng gộp.

**Tác động.**
- Cụm chủ đề cuối cùng thực chất là **gộp tham lam** theo trọng số và cosine tâm cụm, không phải Leiden.
- Báo cáo thực nghiệm sẽ mô tả sai thuật toán.
- Loại vị trí "cùng cụm" của E1, phép so chương–cụm (NMI), pass phụ và stage đều dựa vào cụm này.
- Mutation "bỏ trần" của vé 02 bị bắt vì test kiểm trần — không test nào kiểm Leiden có thật sự làm việc hay không.

**Cách sửa.**
- γ tính theo đồ thị: mặc định bằng **mật độ có trọng số** trên số khái niệm, ghi vào manifest cả công thức lẫn giá trị.
- Manifest và stats ghi **số lần gộp** và **tỉ lệ khái niệm có cụm do vòng gộp quyết**.
- Luật γ phải chốt **trước** E1 và ghi vào spec D3.

**Test.** Trên một đồ thị có hai cộng đồng rõ, Leiden thô (trước vòng gộp) phải tìm đúng hai cộng đồng; tỉ lệ khái niệm
do vòng gộp quyết phải xuất hiện trong stats.

## F87 ✅ — Mỗi checkpoint là một phiên bản artifact đầy đủ — **đã sửa**

**Hiện tượng.**
- Pass chính và pass phụ gọi `save_graph` sau **mỗi** phiên và **mỗi** cặp.
- Mỗi lần lưu chứa toàn bộ payload: node, vector, mention map, và nhật ký có đủ đầu vào gồm cả văn bản chunk.

**Bằng chứng.** `baocao-canhan` có 68 phiên bản, trong đó 62 ở stage `edges`, tổng **112 MB** cho một tài liệu 26 chunk.
Mỗi phiên bản `edges` khoảng 2 MB và lớn dần.

**Tác động.**
- Với giáo trình vài trăm trang, cần hàng trăm phiên chính và hàng trăm cặp phụ, mỗi phiên bản lớn hơn nhiều: ước tính
  **nhiều GB**.
- Kho chọn "mới nhất" theo số phiên bản, nên sau một lần hỏng giữa chừng, "mới nhất" là một checkpoint dở dang. Bộ điều
  phối hiện chạy lại được, nhưng không stage nào kiểm artifact `edges` đã **hoàn tất** trước khi dùng.

**Cách sửa.**
- Checkpoint là **tệp tiến độ** (nhật ký chỉ-thêm các phiên đã xong) nằm ngoài chuỗi phiên bản.
- Chỉ lưu phiên bản artifact khi stage xong.
- A9 và A10 từ chối artifact `edges` chưa hoàn tất.
- Có thể dọn các phiên bản checkpoint cũ của `baocao-canhan` **sau khi chủ dự án đồng ý**.

**Test.**
- Chạy một stage N phiên tạo **một** phiên bản.
- Hỏng giữa chừng rồi chạy lại vẫn tiếp tục được và vẫn chỉ ra một phiên bản.
- A10 từ chối artifact `edges` dở.

## F88 ✅ — Chu trình hai cạnh đẩy cả tài liệu về lộ trình theo thứ tự chương — **đã sửa spec và code**

**Hiện tượng.**
- Tầng 3 giữ nguyên chu trình hai cạnh (đúng D11), rồi thêm `passed = not identity_flags and …`.
- Vì Kahn không xếp tầng được khi còn vòng, **một** cặp như vậy làm cả tài liệu rơi về `document_order_fallback`.

**Bằng chứng.**
- `baocao-canhan`: cổng mật độ **đạt** (29 cạnh / 36 khái niệm, 14% cô lập). Tài liệu trượt **chỉ** vì hai chu trình:
  `ERD ↔ Thiết kế Cơ sở dữ liệu` và `Cơ chế đồng bộ hóa ↔ Race Condition`.
- Cả hai là **lẫn chiều**, không phải trùng danh tính. Mỗi chiều đến từ **một phiên section khác nhau**, cả bốn cạnh đều
  gắn `trong_dinh_nghia`; riêng cặp ERD có một chiều "thuận" và một chiều "ngược". Nhãn `possible_identity` là sai tên.

**Nguyên nhân.** D11 bảo "giữ lại, ghi cờ cho A13", nhưng không nói A10 xếp tầng thế nào khi còn vòng. Nhân viên lấp lỗ
bằng cách cho trượt cổng.

**Quyết định của chủ dự án (2026-09-17): đồng ý.** Spec đã sửa D11 (bước 4 và 5) và D12. Nhân viên sửa code theo:
- Cổng chất lượng **chỉ** xét mật độ; bỏ điều kiện `not identity_flags`.
- Cờ đổi tên thành `two_way_requires`, kèm hai cạnh và bằng chứng của từng chiều.
- A10 xếp tầng trên **đồ thị co**: mỗi thành phần liên thông mạnh còn lại thành một khối, mọi khái niệm trong khối
  cùng tầng, tầng tính theo đường dài nhất. Còn thành phần lớn hơn hai node thì dừng với lỗi.

**Test.**
- Một chu trình hai cạnh cộng các cạnh khác: cổng vẫn đạt, hai khái niệm cùng tầng, các cạnh khác vẫn quyết định
  thứ tự.
- Một thành phần ba node lọt tới A10 thì phải báo lỗi.
- Chạy lại `baocao-canhan` phải ra `roadmap_mode = requires`, không còn `document_order_fallback`.

**Kết quả thật.** `baocao-canhan` v77/v78: quality gate đạt với 25 cạnh / 36 khái niệm, 8 node cô lập; còn một cờ
`two_way_requires`. SCC `ERD ↔ Thiết kế Cơ sở dữ liệu` được co, cả hai ở layer 1 và cùng stage;
`roadmap_mode=requires`, 5 layer, 19 stage. Chạy lại dùng đúng v78 với `reused=true`.

## F89 ✅ — Luật cạnh ngược thứ tự tài liệu chưa được cài — **đã sửa**

**Hiện tượng.** D10 bắt cạnh ngược thứ tự provenance chỉ được nhận khi có bằng chứng tường minh, và bị trừ 0,1. Code chỉ
ghi `order_relation`, không kiểm, không trừ.

**Bằng chứng.** `baocao-canhan`: 6/29 cạnh "ngược", trong đó 1 cạnh chỉ có bằng chứng `mach_trinh_bay`.

**Cách sửa.** Executor từ chối cạnh ngược không tường minh; cạnh ngược tường minh bị trừ 0,1; mức trừ ghi vào manifest,
để E8 hiệu chỉnh sau.

**Test.** Cạnh ngược + `mach_trinh_bay` bị từ chối; cạnh ngược + `noi_ro` được nhận với confidence 0,8.

## F90 ✅ — Viện dẫn nhiễu: phần lớn hai chiều — **đã sửa code; wording D4 do chủ spec chốt**

**Bằng chứng** (`mentions` v4):

| Tài liệu | Viện dẫn | Có cả chiều ngược | Chỉ do đồng định nghĩa | Chỉ từ kênh dense |
|---|---:|---:|---:|---:|
| `baocao-canhan` | 261 | 146 | 97 | 91 |
| `naive-bayes` | 170 | 102 | 57 | 59 |
| `nhap-mon-ml` | 843 | 390 | 279 | 255 |
| `xstk-ch3-1` | 748 | 270 | 161 | 156 |

**Nguyên nhân.** Viện dẫn lấy mọi khái niệm được nhắc trong chunk định nghĩa của A, **kể cả khái niệm cũng được định
nghĩa trong chính chunk đó**, và kể cả nhắc chỉ bắt được bằng dense.

**Tác động.** Tín hiệu chiều rẻ mà spec trông vào gần như vô dụng; E8 và bộ sinh "citation" của E2 đều nhiễu.

**Cách sửa.**
- Không tính chunk mà B cũng ở mức `định nghĩa`; trường hợp đó đã có nguồn `same_section`.
- Ghi kênh trên từng viện dẫn, và tách viện dẫn chỉ từ dense thành loại **mềm**.
- Bổ sung D4.

**Test.** Hai khái niệm cùng định nghĩa trong một chunk không sinh viện dẫn; viện dẫn mềm và cứng được đếm riêng.

## F91 ✅ — Cờ khái niệm thiếu gần như toàn rác — **đã tắt heuristic chưa đo precision**

**Bằng chứng.** Cờ ra được: "Khi đó", "Do đó", "để đảm", "Gọi N", "Hãy ước", "Not Spam"… (31 cờ trên `xstk-ch3-1`).
Lớp ký tự `[A-ZÀ-ỸĐ]` chứa cả chữ thường có dấu, vì dải À–Ỹ trong Unicode gồm cả hai kiểu chữ. Chưa kể kiểu viết hoa
từng chữ vốn hiếm trong tên khái niệm tiếng Việt.

**Tác động.** Cờ rác vào hàng chờ tầng 3 và lên trang xem, làm loãng việc duyệt ở A13.

**Cách sửa.** Hoặc bỏ heuristic này và dựa vào cờ `missing_node` của pass chính, hoặc làm lại: kiểm chữ hoa bằng
`str.isupper()`, loại từ nối đầu câu, đòi cụm danh từ lặp lại. Dù chọn cách nào, cờ này không lên trang xem nếu chưa đo
được precision.

## F92 ✅ — "Hỏi hai thứ tự" chỉ là hình thức — **đã sửa**

**Hiện tượng.** Hai lần hỏi chỉ khác trường `presentation_order`; mảng `nodes` và các trường `left`/`right` trong hồ sơ
giữ nguyên thứ tự.

**Cách sửa.** Lần hỏi thứ hai đảo thật: thứ tự `nodes`, `left`/`right` và `provenance_order`.

**Test.** Hai đầu vào khác nhau ở thứ tự node thật, không chỉ ở một trường phụ.

## F93 ✅ — Pass phụ hỏi lại cặp đã có cạnh trực tiếp — **đã sửa**

**Bằng chứng.** `baocao-canhan`: **4/46** cặp pass phụ đã phán vốn có sẵn cạnh trực tiếp từ pass chính; pass phụ ghi 4
lượt "created" nhưng chỉ thêm được 1 cạnh mới. Nếu pass phụ chọn chiều ngược với một cạnh `mach_trinh_bay` đã có, nó sinh
chu trình hai cạnh.

**Cách sửa.** Bỏ khỏi pass phụ mọi cặp đã có cạnh `requires` trực tiếp, theo bất kỳ chiều nào; ghi log lý do.

## F94 ✅ — Tầng 3 bị chép hai nơi — **đã sửa**

**Hiện tượng.** Use case `ValidateGraph` có test nhưng bộ điều phối không gọi. `BuildRoadmap` tự lắp lại toàn bộ phần
tầng 3 (gom cờ, khử trùng cạnh, số nguồn độc lập, luật chu trình, cổng).

**Tác động.** Hai bản chép sẽ trôi lệch; test của `ValidateGraph` đang giữ một đường không ai chạy.

**Cách sửa.** Bộ điều phối gọi `ValidateGraph` (stage `validated` đã có); `BuildRoadmap` chỉ đọc artifact `validated`.

## F95 ✅ — Tìm vét cạn tập cạnh cần cắt không có trần — **đã sửa**

**Hiện tượng.** `_feedback_edges` thử mọi tổ hợp cạnh nội bộ của một thành phần liên thông mạnh.

**Bằng chứng** (thành phần đủ cạnh, đo trực tiếp): 4 node / 12 cạnh mất 0,03 giây; 5 node / 20 cạnh mất 7 giây; 6 node
/ 30 cạnh **không xong sau 60 giây**. Mỗi node thêm vào làm thời gian tăng hàng trăm lần.

**Cách sửa.** Đặt trần số cạnh nội bộ, ví dụ 16. Vượt trần thì dùng heuristic Eades với cùng thứ tự ưu tiên, ghi log
phương pháp đã dùng.

**Test.** Một thành phần liên thông mạnh 20 cạnh phải chạy xong nhanh và ghi phương pháp.

## F96 ✅ — Kiểm "chunk bằng chứng nhắc cả hai đầu" — **chủ dự án đã chốt 2026-09-18: gắn cờ rồi đo**

Hai lựa chọn nhân viên tự chọn khi cài luật này:
- Mention bắt bằng **dense** (vốn chỉ để đề cử) vẫn được tính là "có nhắc".
- **Mọi** chunk được trích phải nhắc cả hai đầu, nên mô hình trích hai chunk bổ sung nhau thì cạnh bị loại.

**Đo trên bốn tài liệu** (so luật hiện tại với luật siết "ít nhất một chunk nhắc cả hai bằng kênh cứng"):

| Tài liệu | Cạnh đang nhận | Bị loại đúng vì luật này | Luật siết cứu được | Luật siết loại thêm |
|---|---:|---:|---:|---:|
| `baocao-canhan` | 31 | 0 | 0 | 3 |
| `naive-bayes` | 31 | 0 | 0 | 7 |
| `nhap-mon-ml` | 91 | 8 | 2 | 10 |
| `xstk-ch3-1` | 191 | 14 | 4 | 21 |
| **tổng** | **344** | **22** | **6** | **41** |

41 cạnh bị loại thêm là những cạnh mà bằng chứng nhắc cả hai đầu **chỉ dựa vào kênh dense**. Không có bộ vàng thì
không biết đó là bằng chứng giả hay là recall thật.

**Quyết định (hướng 3).** Giữ luật nhận như hiện tại, nhưng **mỗi cạnh mang cờ `evidence_hard`**: đúng khi ít nhất
một chunk được trích nhắc cả hai đầu bằng kênh cứng (provenance, trích, khớp tên đúng chữ). Đúng nếp "đánh dấu,
đừng xoá" mà D11 đã dùng cho cạnh thừa. Spec D9 đã ghi, cùng **luật đổi mặc định viết trước khi đo**: chỉ chuyển
sang đòi bằng chứng cứng khi precision của nhóm `evidence_hard = false` thấp hơn nhóm `true` ≥ 0,15, khoảng tin cậy
của hiệu không chứa 0, và recall tổng thể không giảm quá 0,05. E7 (spec D14) đo việc này.

**Việc của nhân viên:** thêm cờ `evidence_hard` cho mọi cạnh được nhận (cả pass chính và pass phụ), đếm hai nhóm vào
`stats`, và giữ nguyên nhật ký thao tác bị từ chối vì thiếu bằng chứng để E7 đo được phần bị cắt. Đột biến tối
thiểu: gắn cờ cho mọi cạnh; tính dense là kênh cứng; đòi mọi chunk phải cứng.

## F97 🟢 — Các điểm nhỏ — **nhân viên**

- **Chunks mới nhất:** A6/A7, mention map và pass chính dùng chunks **mới nhất** thay vì đúng phiên bản chunk mà
  canonical được dựng từ đó. Hôm nay bốn tài liệu khớp nhau, nhưng nếu cắt chunk lại thì provenance bị bỏ lặng lẽ. Dùng
  đúng chuỗi phiên bản, như vé 04 đã làm.
- **Hash vàng A8:** hash của hai prompt A8 chưa vào test hash vàng chung (`prompts/README.md` yêu cầu). Test hợp đồng
  vẫn giữ được việc đổi prompt, nên chỉ là cho đồng bộ quy ước.
- **Stage khi rơi về thứ tự chương:** đang cắt theo cửa sổ 8 khái niệm rồi chia theo cụm, ra 17 stage cỡ 1–3 cho 36
  khái niệm. Spec gốc muốn nhóm section liền kề.
- **`stage_id` về chunk:** mới có bản đồ trong artifact; chưa ghi vào chỉ mục truy hồi.
- **Trang xem:** hiện mã băm thay cho tên stage, và in cờ dạng JSON thô.

---

## Đột biến của reviewer

41 đột biến, chạy trên bản chép của cây làm việc (không đụng vào việc chưa commit của nhân viên), mỗi lần khôi phục
đúng từng byte. Lượt đầu chạy 16 file test của đợt; **24 bị bắt, 17 lọt**. Mỗi con lọt được chạy lại trên **toàn bộ
test suite** (xem cột cuối).

**Bị bắt (24):**
- R1 khớp dài nhất; R2 ký hiệu; R3 trộn bộ đếm; R5 đảo chiều viện dẫn; R6 top-k dense; R7 độ tin tuyệt đối;
- R9–R11 ba luật executor; R15 không bao giờ theo chương; R16 tỉa qua mọi đường; R18 nhánh chương xét cặp khác cụm;
  R19 cạnh ngoài hồ sơ;
- R21 confidence xếp đầu; R22 cắt chu trình hai cạnh; R23 xoá cạnh thừa; R26 tự quy đồng nghĩa `requires`;
- R28 bỏ trần stage; R29 gộp chưa xét vào đã xét; R30 chunk nhận stage muộn;
- R35 kNN một chiều; R36 bỏ hạ trọng số media; R38 bỏ retry; R39 cache bỏ qua validator.

**Lọt (17), cả 17 đều lọt thật khi chạy lại trên toàn bộ suite:**

| # | Đột biến | Luật bị hở | Loại | Toàn bộ suite |
|---|---|---|---|---|
| R4 | cặp chạm nhận cả cặp cùng cụm | định nghĩa cặp chạm (`CONTEXT.md`) | lỗ test | lọt thật (335/335 xanh) |
| R8 | "≤ 20 khái niệm" thành "< 20" | D6 | lỗ test | lọt thật (335/335 xanh) |
| R12 | "mạch trình bày" 0,7 thành 0,9 | D10 | lỗ test | lọt thật (335/335 xanh) |
| R13 | gộp đề xuất theo thứ tự ngược | D9 | gần tương đương (vẫn tất định) | lọt thật (335/335 xanh) |
| R14 | đảo "thuận"/"ngược" | D10, thứ tự ưu tiên của D11 | lỗ test | lọt thật (335/335 xanh) |
| R17 | hai lượt khác quyết định vẫn nhận | D8 | lỗ test | lọt thật (335/335 xanh) |
| R20 | chỉ dùng lượt hỏi đầu | D8 | lỗ test | lọt thật (335/335 xanh) |
| R24 | ngưỡng cổng 0,5 thành 0,4 | D11 | lỗ test | lọt thật (335/335 xanh) |
| R25 | cạnh kiểu mở vào phép xét chu trình | D11 | phòng thủ (pipeline chỉ đưa `requires` vào) | lọt thật (335/335 xanh) |
| R27 | Kahn xếp tầng theo cha thăm sau cùng | D12 | lỗ test | lọt thật (335/335 xanh) |
| R31 | media tính vào cỡ cụm khi Leiden tối ưu | D3 | lỗ test, bị F86 che | lọt thật (335/335 xanh) |
| R32 | chỉ gộp cụm 1 khái niệm | D3 | lỗ test | lọt thật (335/335 xanh) |
| R33 | ưu tiên độ giống hơn trọng số khi gộp | D3 | lỗ test | lọt thật (335/335 xanh) |
| R34 | bỏ cắt cạnh theo phân vị | D2 | lỗ test | lọt thật (335/335 xanh) |
| R37 | bỏ hạ trọng số chunk đông ở kênh đồng xuất hiện | D2 | lỗ test | lọt thật (335/335 xanh) |
| R40 | "cạnh trước trong chương" lấy cả chương khác | D7 | lỗ test, bị F85 che | lọt thật (335/335 xanh) |
| R41 | bỏ lượt sửa của executor | D9 | lỗ test | lọt thật (335/335 xanh) |

Nhân viên báo đã bắt được các đột biến "bỏ đối chiếu lượt hỏi thứ hai" và "tính media như khái niệm khi áp trần". Hai
con R17, R20 và R31 ở trên cho thấy các test đó chỉ giữ một nhánh của luật: test hai lượt chỉ kiểm hai lượt cùng
"create" nhưng khác chiều; trần cụm chỉ được kiểm ở phép kiểm cuối, không phải ở bước Leiden.

## Phạm vi A10 — chủ dự án chốt hướng (c), 2026-09-17

Spec mang tên A6–A8 nhưng D11 (A9) và D12 (A10) cùng vé 08, 09 đã kéo phạm vi tới A10, theo Q6 lúc grill. Phần nghiên
cứu cho A10 còn mỏng: báo cáo vòng 29 không tìm được tiền lệ trực tiếp cho luật "stage = tầng ∩ cụm".

| Hướng | Nghĩa |
|---|---|
| (a) | Giữ nguyên A6→A10 trong đợt này |
| (b) | Dừng ở A8: đợt này ra đồ thị cạnh, A9–A10 để đợt sau |
| (c) | Giữ A9 (2b cần nó). A10 làm bản tối thiểu để sản phẩm có lộ trình xem được, **không** đưa vào phần tuyên bố khoa học, và có một đợt nghiên cứu riêng trước khi chốt thiết kế A10 |

**Đã chốt (c).** Đã ghi vào đầu spec, kế hoạch 00, vé 09 và vé 14. Với nhân viên: vé 09 chỉ sửa theo F88 (xếp tầng trên
đồ thị co, tầng theo đường dài nhất), không tối ưu thêm A10; các điểm A10 nhỏ ở F97 (stage khi rơi về thứ tự chương,
ghi `stage_id` vào chỉ mục, trang xem) để lại cho đợt nghiên cứu A10.

## Điều kiện nhận lại

1. Sửa F85, F86, F87, F89, F90; F91–F95 nên làm cùng.
2. Thêm test cho các con lọt ở bảng đột biến. R13 và R25 được miễn nếu giải thích trong vé. Nộp lại danh sách đột biến:
   17 con này phải bị bắt, cộng các đột biến cho phần sửa F85–F95.
3. Sửa F88 theo spec D11/D12 mới (chủ dự án đã đồng ý 2026-09-17). Phạm vi A10 theo hướng (c).
4. Chạy lại `roadmap` trên bốn tài liệu cũ. Báo lại: định tuyến và số làn chương (`naive-bayes` phải ra nhánh cụm); Leiden
   thô so với sau gộp; số phiên bản artifact và dung lượng; thống kê viện dẫn sau khi sửa.
5. Chỉ sau đó mới chạy vé 11 trên tài liệu dài và mở E1/E2.

---

# Vòng 31 — Kiểm chứng sau sửa F85–F95 · 2026-09-18

Phạm vi: phần sửa của nhân viên trên cây `main` (chưa commit). Mọi phép thử chạy trên **bản chép** của `src`/`tests` và
bản chép artifact; cây làm việc và kho `artifacts/` thật không bị đụng. Hash 154 file nguồn/test được ghi lúc chép và
so lại giữa chừng: không đổi.

## Kết luận vòng 31

- **F85–F95 làm đúng và đủ ở mức code.** Mọi số nhân viên báo đều khớp khi đo lại trên artifact thật (bảng dưới).
  355/355 test xanh khi chặn mạng. `naive-bayes` ra nhánh cụm. Viện dẫn đồng định nghĩa còn 0. Hai hồ sơ pass phụ đảo
  thật ở 411/411 cặp. Không còn cặp nào vừa có cạnh trực tiếp vừa bị hỏi lại. Cắt chu trình có trần: sát trần 16 cạnh
  mất ≤ 0,38 giây, còn Eades xử lý 270 cạnh trong 0,02 giây.
- **Chưa nhận để mở vé 11 và E1/E2.** Lý do là ba lỗi về cách chọn artifact và resume, cộng một lỗ báo cáo:
  - **F98 🔴:** stage sau không lấy đúng artifact stage trước vừa trả về. Đổi cấu hình rồi đổi lại thì luồng chạy tiếp
    trên chuỗi của cấu hình kia — đúng kiểu thao tác của E2.
  - **F104 🔴:** `upstream_version` của stage `clusters` là số phiên bản của tầng `canonical`, nhưng vòng lần ngược
    đọc nó như số của tầng `graph`. Vì vậy F98 không báo lỗi mà lặng lẽ nhận một artifact cũ bất kỳ: đo thật, pass phụ
    nhận nhầm `graph v8` — một artifact `edges` từ đợt trước.
  - **F99 🟠:** pass phụ rớt mạng giữa chừng rồi chạy tiếp cho kết quả khác chạy liền một mạch, **bỏ hẳn các cặp còn
    lại** (1 cạnh thay vì 3 trong phép thử), và cặp bị bỏ không để lại dòng log nào.
  - **F100 🟠:** ba trên bốn tài liệu chưa được chạy lại sau F88. Kho thật vẫn giữ tầng validate bản cũ, và
    `nhap-mon-ml`, `xstk-ch3-1` vẫn ra lộ trình theo thứ tự tài liệu.
- F101–F103 là điểm thiết kế và điểm nhỏ.
- F98 và F104 đã có từ vòng 30 nhưng **tôi bỏ sót** khi đó.

## Số đo lại khớp báo cáo nhân viên

| Tài liệu | Route · phiên · làn | γ = mật độ | Leiden thô (cụm; cụm 1–2) → sau gộp | Gộp tác động | Viện dẫn (hard/soft) | Version · MB |
|---|---|---:|---|---:|---|---|
| `baocao-canhan` | chapter · 16 · 5 | 0,04943 | 12; 4 → 8 | 20/36 | 164 (66/98) | 78 · 134,60 |
| `naive-bayes` | **topic_cluster** · 6 · — | 0,04547 | 12; 5 → 7 | 22/34 | 113 (53/60) | 12 · 22,15 |
| `nhap-mon-ml` | chapter · 19 · 2 | 0,02782 | 18; 4 → 14 | 19/75 | 564 (303/261) | 12 · 47,10 |
| `xstk-ch3-1` | chapter · 38 · 1 | 0,01889 | 20; 6 → 14 | 38/98 | 587 (426/161) | 12 · 87,37 |

Kiểm thêm:
- **Định tuyến:** lập lại kế hoạch phiên từ artifact thật khớp từng `session_id`. Mọi `chapter_id` đều ở cấp 1.
  Không có section cấp ≥ 2 nằm thẳng dưới gốc.
- **Viện dẫn hai chiều:** giảm từ 146 xuống còn 34 cặp ở `baocao-canhan`.
- **Cạnh ngược:** tất cả đều là `trong_dinh_nghia` với confidence 0,8. Executor từ chối 4 cạnh ngược không tường minh ở
  `baocao-canhan`.
- **Checkpoint:** không còn tệp checkpoint nào sót lại.
- **Tái lập:** `baocao-canhan` chạy tới `stages` cho `reused=true`, 0 lời gọi.
- **Chi phí lượt chạy lại:** 0,06 + 0,14 + 0,23 + 0,51 ≈ **0,94 USD**.

## F98 🔴 — Stage sau chọn đầu vào theo "bản graph mới nhất", không theo bản stage trước vừa trả về

**Hiện tượng.**
- `BuildMentions`, `BuildMainEdges`, `BuildSecondaryEdges`, `ValidateGraph` và `BuildRoadmap` đều bắt đầu từ
  `load_latest_graph` rồi lần ngược `upstream_version`.
- Khi stage trước **dùng lại** một bản cũ (`find_graph` trúng cache), bản mới nhất trong kho có thể thuộc một cấu hình
  khác. Stage sau khi đó đi theo chuỗi sai.

**Bằng chứng** — bản chép artifact của `baocao-canhan`, chặn mạng; embedding giả chỉ dùng cho lần dựng mention mới;
mô hình giả ném `ModelTransportError` như adapter thật:

| Lượt | Cấu hình | Kết quả |
|---|---|---|
| 1 | mặc định, tới `stages` | v78, `reused=true`, chuỗi v78 ← v77 ← v72 ← v71 ← **v70 (top_k=3)** ← v69 |
| 2 | `MENTION_DENSE_TOP_K=5`, tới `mentions` | v79 mới (top_k=5) |
| 3 | mặc định, tới `mentions` | v70, `reused=true` — đúng |
| 4 | mặc định, tới `stages` | **pass chính đòi gọi mô hình trên v79 (top_k=5)**, dù chuỗi mặc định v78 đã có đủ |

- Nếu có mạng, lượt 4 sẽ tốn tiền để dựng cạnh trên mention map của cấu hình khác, rồi trả `stages` mang cấu hình sai.
- Manifest vẫn trông hợp lệ, vì mỗi stage chỉ ghi `mentions_version` mà nó tự tìm được.

**Tác động.**
- E2 và mọi phép so cấu hình (top-k, γ, bộ sinh) đều đổi cấu hình qua lại trên cùng `doc_id`. Kết quả có thể trộn lặng
  lẽ giữa hai cấu hình.
- Vi phạm user story 32 ("không âm thầm trộn") và lời hứa của D1 ("không đổi gì thì `reused=true`, 0 lời gọi").

**Cách sửa.**
- Bộ điều phối truyền **đúng artifact** mà stage trước trả về cho stage sau, ví dụ `execute(doc_id, upstream=artifact)`.
- Khi gọi một stage lẻ, stage đó tìm đầu vào bằng cách **dựng lại khoá** của stage trước, không bằng "mới nhất".
- `load_latest_graph` chỉ còn dùng cho lệnh xem.

**Test.**
- Đổi cấu hình theo chuỗi A → B → A: lượt A thứ hai phải trả đúng chuỗi A với 0 lời gọi.
- Lượt B phải không đụng tới artifact của A.

**Ai sửa:** nhân viên.

## F104 🔴 — `upstream_version` của `clusters` trỏ sang tầng khác, nên vòng lần ngược đọc nhầm artifact

**Hiện tượng.**
- `BuildClusters` lưu `upstream_version=canonical.version`, tức **số phiên bản của tầng `canonical`**.
- Mọi vòng lần ngược (`_mentions`, `_edge_checkpoint`, `_edges`, `_validated`) lại đọc số đó bằng
  `store.load_graph(doc_id, upstream)`, tức **số phiên bản của tầng `graph`**.
- Khi vòng lần ngược đi qua một artifact `clusters` mà chưa tìm thấy stage cần, nó nhảy sang một artifact `graph`
  hoàn toàn khác cùng số hiệu, thay vì báo lỗi. Câu lỗi "artifact graph không trỏ về stage …" vì vậy gần như không
  bao giờ chạy tới.

**Bằng chứng** (đọc thuần, không giả lập, trên bản chép artifact của `baocao-canhan`):
- `clusters` v69 có `upstream_version = 8`, và `canonical_version` trong config cũng là 8 — đúng là số của tầng
  canonical (kho canonical có v1–v8).
- Với bản mới nhất là v79 (`mentions`), `BuildSecondaryEdges._edge_checkpoint` trả về **graph v8**, một artifact
  `edges` cũ từ tháng trước, coi như đó là checkpoint của pass chính.
- `ValidateGraph._edges` cũng đi tới v8 và chỉ dừng được nhờ cổng kiểm "edges phải hoàn tất cả hai pass".

**Tác động.**
- Đây là cái làm F98 trở thành **im lặng** thay vì báo lỗi: pipeline có thể dựng tiếp trên một artifact cũ bất kỳ.
- Nếu tầng canonical có nhiều phiên bản hơn tầng graph, lời gọi sẽ ném `FileNotFoundError` thay vì câu lỗi có nghĩa.

**Cách sửa.**
- `clusters` không ghi `upstream_version` của tầng khác. Canonical đã được ghi trong `config.canonical_version` rồi,
  nên chỉ cần để trống, hoặc ghi cả tên tầng: `{"artifact": "canonical", "version": 8}`.
- Vòng lần ngược dừng ngay khi gặp `stage == "clusters"` và báo lỗi rõ ràng.

**Test.** Với kho chỉ có `clusters`, gọi pass phụ hoặc tầng validate phải ném lỗi có nghĩa, không được trả artifact
khác.

**Ai sửa:** nhân viên.

## F99 🟠 — Pass phụ chạy có resume khác chạy liền một mạch

**Hiện tượng.**
- `select_secondary_pairs` chạy **một lần** lúc bắt đầu, trên cạnh pass chính cộng cạnh pass phụ đang có.
- Chạy liền: cạnh pass phụ ban đầu rỗng, nên các cặp phía sau không bị tỉa dù cặp trước vừa tạo đường tường minh.
- Chạy có resume: cạnh pass phụ đọc từ checkpoint đã có sẵn, nên chính các cặp đó bị tỉa.
- Nhật ký tỉa chỉ được ghi `if not resumable`, nên cặp bị tỉa lúc resume không để lại dấu vết nào.

**Bằng chứng** (fixture ba node a, b, c; có sẵn cạnh tường minh b → c; cặp p1 = (a, b), p2 = (a, c); mô hình tạo cạnh
cho cả hai):

| Cách chạy | Cạnh pass phụ | Cặp đã hỏi | Log | Thống kê cặp |
|---|---|---|---|---|
| Chạy liền | a→b, **a→c** | p1, p2 | p1 created, p2 created | 2 hỏi, 0 tỉa |
| Rớt mạng ở p2, rồi resume | a→b | p1 | p1 created — **p2 không có trong log** | 0 hỏi, 2 tỉa |

**Đo rộng hơn** (bốn node a, b, c, d; cạnh tường minh sẵn có b → c → d; ba cặp p1 = (a, b), p2 = (a, c), p3 = (a, d);
mô hình luôn tạo cạnh; thử rớt ở từng cặp):

| Lượt chạy | Cạnh pass phụ thu được | Cặp hỏi lại sau khi resume |
|---|---|---:|
| chạy liền một mạch | a→b, a→c, a→d | — |
| rớt ở p1 | a→b, a→c, a→d (giống) | 3 |
| **rớt ở p2** | **chỉ a→b** | **0** |
| **rớt ở p3** | **a→b, a→c** | **0** |

Nghĩa là một lần rớt mạng giữa chừng không chỉ làm kết quả khác đi, mà còn **bỏ hẳn các cặp còn lại** và đóng artifact
như thể đã xong.

**Tác động.**
- Kết quả phụ thuộc vào việc lượt chạy có bị ngắt hay không, và phần bị bỏ không hiện ra ở đâu cả.
- Vi phạm D8 ("mọi cặp bị tỉa đều ghi log").
- Với tài liệu dài, rớt mạng là chuyện thường gặp.
- Pass chính **không** có lỗi này: kế hoạch phiên không phụ thuộc cạnh, và "cạnh trước" chỉ lấy trong cùng chương nên
  hai phiên cùng một đợt không ảnh hưởng nhau.

**Cách sửa (đề xuất).**
- Tỉa **ngay trước khi hỏi từng cặp**, trên cạnh hiện có, và ghi log ở cả hai chế độ. Vòng cặp vốn chạy tuần tự nên
  kết quả vẫn tất định, và đúng tinh thần D8: không hỏi cặp đã có đường tường minh.
- Thống kê đếm theo log, không đếm theo danh sách tính lại.

**Test.** Cùng fixture: chạy liền và chạy "rớt ở cặp thứ k rồi resume" phải ra artifact giống nhau, với mọi k.

**Ai sửa:** nhân viên.

## F100 🟠 — Ba tài liệu chưa được chạy lại sau F88

**Bằng chứng.**
- Kho thật: `naive-bayes`, `nhap-mon-ml` và `xstk-ch3-1` có tầng validate v11 với `algorithm_id =
  a9-global-validation-v2` (trước F88), và `stages` v12 với `a10-kahn-stage-v3`.
- `nhap-mon-ml` và `xstk-ch3-1` vẫn ở `document_order_fallback` vì cờ `possible_identity` kiểu cũ.
- Chạy code hiện tại trên bản chép, chặn mạng, 0 lời gọi:

| Tài liệu | Cổng | Mode | Tầng · stage | Chu trình hai node | Cỡ stage |
|---|---|---|---|---:|---|
| `naive-bayes` | đạt (28 cạnh) | requires | 4 · 15 | 0 | 6 stage cỡ 1 |
| `nhap-mon-ml` | đạt (91) | requires | 10 · 41 | 1 | **21/41 stage cỡ 1** |
| `xstk-ch3-1` | đạt (191) | requires | 8 · 52 | 1 | **25/52 stage cỡ 1** |

**Cách sửa.**
- Chạy `roadmap --stop-after stages` cho ba tài liệu (0 lời gọi).
- Cập nhật bảng "Chạy thật lại" và ghi rõ mỗi dòng ứng với `algorithm_id` nào.

**Ai sửa:** nhân viên.

Stage cỡ 1 chiếm khoảng một nửa. Đây là điều A10 bản tối thiểu cho phép theo hướng (c); ghi lại làm đầu vào cho đợt
nghiên cứu A10, không sửa bây giờ.

## F101 🟡 — "Cạnh trước trong chương" tăng không chặn

**Bằng chứng.**
- `xstk-ch3-1` là một chương duy nhất với 38 phiên chạy tuần tự. Phần `previous_edges_in_chapter` lên tới **69.013 ký
  tự**, và input lớn nhất là 84.128 ký tự.
- `nhap-mon-ml`: 29.327 ký tự.
- Một chương giáo trình thật có thể dài hơn nhiều.

**Nguyên nhân.** D7 (của tôi) truyền mọi cạnh trước trong chương.

**Đo nếu lọc theo phiên** (chỉ giữ cạnh có ít nhất một đầu trong `allowed_node_ids`), tính trên chính nhật ký đã chạy:

| Tài liệu | Tổng ký tự cạnh trước | Sau khi lọc | Khối lớn nhất |
|---|---:|---:|---|
| `baocao-canhan` | 12.380 | 1.861 (15%) | 1.941 → 955 |
| `nhap-mon-ml` | 290.784 | 86.872 (30%) | 29.327 → 12.980 |
| `xstk-ch3-1` | 1.392.009 | 464.878 (33%) | 69.013 → 30.928 |

Tiền tiết kiệm không đáng kể (cỡ 15% input token của pass chính). Lý do chính là **khối lượng này tăng theo bình
phương số phiên trong một chương**, và nó làm mỗi phiên thấy một lượng ngữ cảnh khác hẳn nhau tuỳ vị trí trong chương —
một biến gây nhiễu cho E2 và E6.

**Đề xuất cho spec.** Chỉ truyền cạnh có ít nhất một đầu trong `allowed_node_ids` của phiên, ghi số cạnh bị lược vào
log. Đổi này làm đổi input của pass chính, nên cần chủ dự án duyệt trước vé 11.

## F102 🟡 — Mỗi version graph chép lại toàn bộ payload upstream

**Bằng chứng.** Mỗi stage lưu `{**upstream.payload, ...}`. `xstk-ch3-1`: 3,65 → 4,60 → 8,60 → 10,60 → 10,81 → 10,80 MB,
tức khoảng 49 MB cho một lượt sáu stage. Kho graph hiện tại: 291 MB cho bốn tài liệu ngắn.

Phần chiếm chỗ trong artifact cuối (`xstk-ch3-1` v12, 10,80 MB): `decision_log` 3,90 MB (36%, vì mỗi dòng chứa nguyên
input gồm văn bản chunk), `node_vectors` 2,58 MB (24%), phần còn lại là cạnh và cặp. `mention_map` chỉ 0,08 MB, nên
không phải thủ phạm.

**Tác động.** Giáo trình dài gấp nhiều lần, và E3 cần ba lượt chạy để đo Jaccard, cộng các cấu hình của E2 — dung lượng
sẽ lên hàng GB trên máy chủ dự án.

**Đề xuất, theo thứ tự công sức tăng dần.**
- **(a)** Không làm gì, chấp nhận dung lượng.
- **(b) Rẻ và đủ dùng:** hai khối nặng (`decision_log`, `node_vectors`) chỉ nằm ở stage sinh ra chúng; stage sau tham
  chiếu theo số phiên bản thay vì chép. Giữ nguyên mọi thứ khác.
- **(c) Triệt để:** payload mỗi stage chỉ chứa phần mới, loader tự ghép theo chuỗi.

Tôi đề xuất (b) trước vé 11. Lưu ý: cả (b) và (c) đều dựa vào chuỗi `upstream` đúng, nên phải sửa F104 và F98 trước.

## F103 🟢 — Điểm nhỏ

- **Mức trừ cạnh ngược:** báo cáo nói "mức trừ nằm trong config", nhưng thực tế là hằng `0.1` trong
  `prerequisites.py:187`, và manifest cũng ghi hằng. Hoặc đưa thành tham số, hoặc sửa câu báo cáo.
- **F85:** chưa có test dựng từ `sections.json` thật như đã yêu cầu; hiện chỉ có section gốc tổng hợp.
- **Độ phủ:** node đích của một phiên chính hỏng hẳn (`invalid_main_session`) vẫn được tính "đã xét". Nên tính là
  chưa xét. Dữ liệu hiện tại có 0 phiên hỏng nên chưa ảnh hưởng.
- **Khoá cấu hình pass chính:** khoá gồm cả `concurrency`, nên đổi số luồng làm mất cache dù kết quả không phụ thuộc số
  luồng.
- **`merge_affected_concept_count`:** chỉ số này đếm cả khái niệm của cụm nhận. Báo cáo phải định nghĩa đúng như vậy.
- **Prompt pass chính chưa nói luật cạnh ngược.** Executor từ chối cạnh ngược thứ tự tài liệu nếu bằng chứng không
  tường minh (D10), nhưng prompt không hề nhắc. Trên `baocao-canhan` đã có 4 lượt bị từ chối vì lý do này, mỗi lượt kéo
  theo một lời gọi sửa. Thêm một câu vào prompt là đủ; nên làm cùng lúc với lần chạy lại sắp tới, vì đổi prompt là đổi
  `prompt_hash` và phải ghi lại fixture hợp đồng.
- **Phiên bản chunk không nằm trong khoá của hai pass cạnh.** `base_config` của pass chính và pass phụ không ghi
  `chunks_version`, dù văn bản chunk đi thẳng vào prompt. Hôm nay vô hại vì mention map đã ghim chunk, nhưng cùng với
  F98/F104 thì đây là chỗ thứ hai cho phép trộn phiên bản.
- **Giá mô hình:** `PRICING_USD_PER_MILLION = {input 0,25; output 1,50}` không ghi nguồn. Báo cáo chi phí cần nói rõ
  bảng giá nào, ngày nào.

## Đột biến vòng 31

85 đột biến: 41 con của vòng 30 (ba con phải chỉnh lại neo vì code đã đổi) cộng 44 con mới nhắm thẳng vào phần sửa
F85–F95. Chạy trên bản chép, khôi phục đúng từng byte. **64 bị bắt, 21 lọt**; mỗi con lọt được chạy lại trên toàn bộ
355 test.

**Bị bắt (64).** Trong 44 con mới, 37 con bị bắt: gốc cấp 0 và cây thoái hoá (N1–N3), resume pass chính (N9, N10,
N17), validate từ chối edges dở (N14), luật cạnh ngược (N18, N19, N21), viện dẫn đồng định nghĩa và hard/soft (N22,
N23, N25), đảo hồ sơ pass phụ (N26, N27), tỉa cạnh trực tiếp (N29, N31), bộ điều phối gọi validate đúng một lần (N32,
N33), trần vét cạn (N34), cổng chất lượng và co SCC của F88 (N37–N40). **38 trong 41 con của vòng 30 nay đã bị bắt;
chỉ còn R13, R17 và R25.**

**Lọt (21), cả 21 đều lọt thật khi chạy lại trên toàn bộ suite (355/355 xanh mỗi lần):**

| # | Đột biến | Luật bị hở | Loại |
|---|---|---|---|
| R13 | gộp đề xuất theo thứ tự ngược | D9 | miễn — vẫn tất định, đã giải thích |
| R17 | hai lượt lệch nhau vẫn nhận | D8 | **lỗ test một nửa**: test chỉ phủ chiều "lượt đầu create"; chiều "lượt đầu không tạo cạnh, lượt sau create" cho ra `no_direct_relation` thay vì `defer` |
| R25 | cạnh kiểu mở vào phép xét chu trình | D11 | miễn — phòng thủ, đã giải thích |
| N4 | mật độ chia `n(n−1)` thay vì `C(n,2)` | D3 | lỗ test |
| N5 | mật độ tính cả cạnh media | D3 | lỗ test |
| **N6** | **γ quay lại cố định 1,0** | **D3** | **lỗ test — chính là lỗi F86, không test nào bắt** |
| N7 | tỉ lệ khái niệm do vòng gộp quyết chỉ đếm cụm nguồn | D3 | lỗ test |
| N11 | resume không kiểm `source_hash` của checkpoint | D1 | lỗ test |
| N12 | pass phụ bỏ hẳn resume | D1 | lỗ test — pass chính có test resume, pass phụ thì không |
| N13 | pass phụ không xoá checkpoint sau khi đóng | D1 | lỗ test |
| N15 | pass phụ nhận artifact pass chính chưa hoàn tất | D1 | lỗ test |
| N16 | ghi checkpoint không nguyên tử | D1 | khó test thật — chấp nhận nếu ghi rõ |
| N20 | cạnh ngược chỉ nhận `noi_ro` | D10 | lỗ test — test chỉ dùng một loại bằng chứng |
| N24 | "mềm" khi *một* chunk chỉ có dense | D4 | lỗ test |
| N28 | không đảo `provenance_order` | D8 | **tương đương**: prompt dựng bằng `json.dumps(..., sort_keys=True)`, nên thứ tự khoá không tới được mô hình — câu "đảo thật cả `provenance_order`" trong báo cáo không đúng |
| N30 | chỉ tỉa cạnh trực tiếp đúng một chiều | D8 | lỗ test |
| N35 | Eades chọn node nhỏ nhất thay vì lớn nhất | D11 | lỗ test — test chỉ kiểm chạy xong và ghi `method` |
| N36 | Eades bỏ thứ tự ưu tiên bằng chứng | D11 | lỗ test |
| N41 | ngưỡng cô lập 0,6 thành 0,7 | D11 | lỗ test |
| N42 | fallback tách hai node của một SCC ra hai tầng | D12 | lỗ test |
| N44 | viện dẫn không lọc nguồn phải học được | D4 | **tương đương**: mention map vốn chỉ chứa node học được |

## Chủ dự án chốt — 2026-09-18

| Mục | Quyết định | Spec đã sửa |
|---|---|---|
| **D3** | Đồng ý: γ mặc định = mật độ có trọng số trên khái niệm; manifest ghi công thức và giá trị; stats tách phân hoạch Leiden thô khỏi vòng gộp | D3 |
| **D4** | Đồng ý: bỏ viện dẫn đồng định nghĩa; tách viện dẫn **cứng** và **mềm**; bộ sinh dùng `citation_hard` và `citation_soft` riêng | D4 |
| **F101** | **Lọc:** cạnh trước trong chương chỉ truyền nếu có ít nhất một đầu trong danh sách khái niệm của phiên; nhật ký ghi số cạnh bị lược | D7 điểm 4 |
| **F102** | **Hướng (b):** nhật ký phán và vector node chỉ nằm ở stage sinh ra chúng, stage sau tham chiếu theo số phiên bản | D1 |
| **F96** | **Hướng (3):** giữ luật nhận hiện tại, mỗi cạnh mang cờ `evidence_hard`, đo ở E7 theo luật đổi mặc định viết trước | D9, D14 (E7) |

D3 và D4 chỉ là ghi lại điều code đã làm, không cần sửa code. F96, F101 và F102 là việc mới của nhân viên; F101 và
F102 phải xong **trước vé 11**, vì sau khi nạp giáo trình thật thì mỗi lần chạy lại đắt hơn nhiều.

## Việc của reviewer còn treo

- Không còn. Bộ chấm E1/E2 (vé 05) đã xong ở nhánh `ve-05-bo-cham`, sẵn sàng nhận file JSON của `a8-gold-check`; phần
  tách precision theo `evidence_hard` cho E7 sẽ thêm vào bộ chấm khi cờ này có trong artifact.

## Điều kiện nhận lại (vòng 31)

Làm theo đúng thứ tự này, vì mục 3 dựa vào mục 1.

1. **F104** (một dòng ở `BuildClusters` cộng chỗ dừng của vòng lần ngược), rồi **F98**, rồi **F99** — ba lỗi cùng một
   họ: chọn sai artifact và chạy tiếp sai. Kèm test như mô tả ở từng mục.
2. **F100:** chạy lại `stages` cho `naive-bayes`, `nhap-mon-ml`, `xstk-ch3-1` (0 lời gọi), cập nhật bảng số và ghi rõ
   `algorithm_id` của từng dòng.
3. **F96, F101 và F102 theo quyết định của chủ dự án ở trên.** F101 đổi `prompt_hash`, nên phải ghi lại fixture hợp
   đồng và chạy lại bốn tài liệu; gộp luôn lần chạy lại của mục 2 và cờ `evidence_hard` của F96 vào đây để chỉ tốn
   một lượt. Báo lại chi phí thật, và số cạnh của hai nhóm `evidence_hard`.
4. **Test cho các đột biến còn lọt** ở bảng trên. Ưu tiên N6 (γ quay lại 1,0 — chính lỗi F86 mà không test nào bắt),
   N12/N13/N15 (resume và checkpoint của pass phụ), R17 chiều còn lại, N41 (ngưỡng cô lập), N35/N36 (thứ tự ưu tiên của
   Eades). N28 và N44 là đột biến tương đương, không cần test; nhưng phải sửa câu "đảo thật cả `provenance_order`" trong
   báo cáo.
5. **F103** làm cùng. Trong đó câu prompt về luật cạnh ngược nên thêm **trong cùng lượt sửa F101**, vì cả hai đều đổi
   prompt pass chính và chỉ nên tốn một lần ghi lại fixture.
6. Chỉ sau khi vòng kiểm tiếp theo đạt mới mở vé 11 và E1/E2.

---

## F105 🟠 — Provenance trỏ vào chunk mở đề, không phải chunk có định nghĩa (phát hiện từ lượt gán thử)

**Nguồn.** Lượt gán thử của chủ dự án trên `xstk-ch3-1`, đơn vị 10–13 (§2 Ước lượng), 2026-09-18: 52 quan hệ và 27
cờ. Trong đó **4 cờ "nơi dạy sai"**, đều nói một điều: danh mục ghi nơi dạy sớm hơn chỗ định nghĩa thật một trang.

**Kiểm chứng.** Lấy ca `Hàm ước lượng`:

- Artifact ghi provenance là chunk trang 21 (sách 107). Đối chiếu văn bản PDF bằng phép khớp từ: chunk ấy **đúng**
  nằm trọn ở trang 21, nên **số trang không sai**.
- Nhưng chunk đó chỉ mở đề: "Để ước lượng số đặc trưng θ… ta có mẫu tổng quát (X1,…,Xn)".
- Câu định nghĩa thật — "Các thống kê X̄, S², F được gọi lần lượt là…" — nằm ở chunk trang 22, và chunk đó **không**
  nằm trong provenance của node.

Ba cờ còn lại (`Khoảng tin cậy`, `Xác suất mắc sai lầm`, `Độ tin cậy`) cùng hình dạng: định nghĩa ở trang kế tiếp.

**Tác động.**
- File gán chỉ người gán tới chunk mở đề, nên họ phải tự dò sang trang sau. 4 trên 26 khái niệm đích của đơn vị này.
- E1 phân loại vị trí theo provenance, nên cặp lẽ ra "cùng chunk" có thể rơi xuống "cùng mục" hoặc "cùng chương".
- Luật bằng chứng của D9 tra mention map theo chunk, nên chunk định nghĩa thật không nằm trong provenance cũng ảnh
  hưởng tới việc cạnh được nhận hay bị loại.

**Chưa sửa.** Đây là hành vi của A3/A4 — phase đã đóng — và vé 11 cấm sửa code. Ba đường:
(a) ghi thành giới hạn trong báo cáo và giữ nguyên;
(b) cho phép provenance gồm **cả chunk kế tiếp** khi định nghĩa bị cắt qua chunk, đo lại điểm vàng A4 trước khi nhận;
(c) để người gán sửa "nơi dạy" ngay trong file gán, rồi dùng cờ đó làm mẫu kiểm cho A13.

Tôi nghiêng về (c) cho đợt này, cộng (a) trong báo cáo: không đụng vào phase đã đóng, mà vẫn có số đo về mức lệch.
Chủ dự án quyết.

**Số cần báo trong báo cáo cuối:** tỉ lệ khái niệm đích bị gắn cờ "nơi dạy sai" trên cả hai chương vàng.

---

# Phản hồi thực thi vòng 32 — F96, F98–F105 và vé 16 · 2026-09-19

## Kết luận

- **F96, F98, F99, F101, F102, F103 và F104 đã sửa, có test và chạy thật.** F100 đã chạy lại đủ bốn tài liệu trong
  cùng lượt. F105 đã có stage `provenance` theo spec vá; cache và precision quan sát đạt cổng.
- Baseline A6–A10 đã commit ở `a033b89`. Các thay đổi vòng 32 và vé 16 đang chờ commit sau khi cập nhật feedback này.
- **Chưa mở vé 11.** Vé 16 còn thiếu đúng bảng E1 trước/sau vì file nhãn A1 trong scratchpad là template trống, dù
  F105 nhắc một lượt gán thử 52 quan hệ/27 cờ. Không tìm thấy file chứa 52 quan hệ trong workspace, worktree vé 04/05,
  Desktop, Documents hoặc Downloads.

## Sửa code và test

- F104/F98: `clusters.upstream_version=null`; bộ điều phối truyền chính artifact vừa tạo sang stage kế; walker dừng
  đúng ở `clusters`. Test A→B→A chứng minh không nhặt artifact của cấu hình khác.
- F99: pass phụ tỉa ngay trước từng cặp trên trạng thái cạnh hiện tại, luôn ghi log cặp bị tỉa, và resume cho kết quả
  giống chạy liền.
- F96: mọi cạnh nhận được có `evidence_hard`; kênh cứng là provenance/extraction/exact, dense-only là mềm. Artifact
  validated thật có **286 cạnh cứng / 41 cạnh mềm** (chi tiết ở bảng dưới).
- F101: cạnh trước chỉ giữ khi ít nhất một đầu thuộc phiên; log ghi `previous_edges_omitted_count`. Prompt nói rõ cạnh
  ngược chỉ nhận `noi_ro` hoặc `trong_dinh_nghia`.
- F102: vector node chỉ ở `clusters`; main log chỉ ở main; secondary log chỉ ở secondary; stage sau mang version tham
  chiếu. Chuỗi artifact ghim đúng version chunks/canonical.
- F103: concurrency ra khỏi cache key pass chính; phiên chính lỗi không còn tính node là đã xét; hằng mức trừ cạnh
  ngược là `REVERSE_ORDER_PENALTY=0.1`; fixture section thật của `naive-bayes`; prompt hash vàng A8; nguồn giá và ngày
  kiểm được ghi trong manifest. `merge_affected_concept_count` được hiểu là mọi concept trong cả cụm nguồn và cụm nhận.
- Các lỗ R17, N4–N7, N11–N13, N15, N20, N24, N30, N35–N36, N41–N42 đều có test. N16 đã có test ghi checkpoint
  nguyên tử. R13/R25 là phòng thủ/tương đương như giải thích cũ; N28 tương đương vì JSON `sort_keys`; N44 tương đương
  vì mention map chỉ chứa node học được.
- Vé 16 thêm stage `clusters → mentions → provenance → edges → validated → stages`; một job, tối đa một lần gọi cho
  mỗi khái niệm nghi; exact ∪ dense; trần 12; marker cấu hình; quote nguyên văn; add-only; dựng lại mention map và mọi
  phái sinh bằng hàm domain hiện có. Năm đột biến tối thiểu đều bị seam test bắt.
- Toàn bộ suite **383/383** chạy xanh với `HF_HUB_OFFLINE=1`; seam vé 16 riêng có **23 test xanh**.

## Chạy thật hợp nhất F100/F96/F101/F102/F103/vé 16

| Tài liệu | Route · phiên | γ | Leiden thô → sau gộp | Graph chain mới | Dung lượng 7 stage | Roadmap | Cạnh validated hard / soft |
|---|---|---:|---:|---|---:|---|---:|
| `baocao-canhan` | chapter · 16 | 0,04943 | 12 → 8 | 79→80→85→86→87→88→89 | 4,02 MB | requires · 22 stage / 6 lớp | 22 / 3 |
| `naive-bayes` | **topic_cluster · 6** | 0,04547 | 12 → 7 | 13→14→15→16→17→18→19 | 4,75 MB | requires · 16 / 6 | 30 / 8 |
| `nhap-mon-ml` | chapter · 19 | 0,02782 | 18 → 14 | 13→14→15→16→17→18→19 | 11,64 MB | requires · 43 / 9 | 74 / 10 |
| `xstk-ch3-1` | chapter · 38 | 0,01889 | 20 → 14 | 13→14→15→16→17→18→19 | 17,72 MB | requires · 63 / 13 | 160 / 20 |

`naive-bayes` có 6/6 phiên hợp lệ mang `route=topic_cluster`; các dòng repair không có route và không được tính là
phiên. Algorithm id của chuỗi cuối là: clusters v3, mentions v3, provenance v1, main v4, secondary v3, validation v4,
roadmap v5. Tổng bảy payload mới là **38,13 MB**, thay vì khoảng 49 MB chỉ riêng sáu stage của `xstk-ch3-1` trước F102.

| Tài liệu | Provenance call / USD | Main+repair call / USD | Secondary call / USD | Tổng USD |
|---|---:|---:|---:|---:|
| `baocao-canhan` | 0 / 0,000000 | 21 / 0,031879 | 72 / 0,030285 | 0,062164 |
| `naive-bayes` | 2 / 0,001373 | 8 / 0,022718 | 281 / 0,145733 | 0,169824 |
| `nhap-mon-ml` | 3 / 0,001574 | 25 / 0,076277 | 245 / 0,130178 | 0,208029 |
| `xstk-ch3-1` | 13 / 0,010456 | 47 / 0,172333 | 294 / 0,167239 | 0,350028 |
| **Tổng** | **18 / 0,013403** | **101 / 0,303207** | **892 / 0,473435** | **0,790044** |

Giá dùng để tính: Gemini 3.1 Flash-Lite, Developer API paid standard, input 0,25 USD/M token và output 1,50 USD/M
token, kiểm ngày 2026-09-18; URL nguồn nằm trong manifest. Lượt `baocao-canhan` v81–v84 đã hoàn tất ngay trước khi
tài liệu vé 16 xuất hiện, tốn thêm 0,062164 USD; ghi riêng, không nhập vào lượt hợp nhất ở bảng.

## Vé 16: số thật và kiểm tay

| Tài liệu | Xét | Hỏi | Thêm | Quote bị loại | Đổi thứ tự đầu | Token vào / ra | USD |
|---|---:|---:|---:|---:|---:|---:|---:|
| `baocao-canhan` | 36 | 0 | 0 | 0 | 0 | 0 / 0 | 0,000000 |
| `naive-bayes` | 34 | 2 | 0 | 0 | 0 | 4.999 / 82 | 0,001373 |
| `nhap-mon-ml` | 75 | 3 | 2 | 0 | 0 | 4.753 / 257 | 0,001574 |
| `xstk-ch3-1` | 98 | 13 | 7 | 0 | 1 | 34.912 / 1.152 | 0,010456 |

Chỉ có 9 chunk được thêm nên kiểm tay toàn bộ 9 thay vì giả vờ rút 30 mẫu: **9/9 đúng nơi dạy/định nghĩa**, precision
quan sát 1,00. Bất biến artifact thật đều đạt: source ⊆ refined; không node học được rỗng provenance; số node không
đổi; mọi quote trạng thái `added` khớp độc lập với chunk. Replay bốn tài liệu qua proxy đóng `127.0.0.1:9` trả đúng
v89/v19/v19/v19 và `reused=true` cả bốn.

## Cổng còn thiếu trước vé 11

Chạy chính bộ đọc của vé 04 trên file `xstk-ch3-1-chuong-10-13-A1.xlsx` tìm được trong scratchpad cho kết quả:
`annotator=A1`, `edges=0`, `flags=0`, thời gian gán/rà soát đều null, cảnh báo `chưa có quan hệ nào được ghi`. Đây là
template sinh ngày 2026-09-16, không phải dữ liệu lượt gán thử 52 quan hệ/27 cờ ở F105. Do đó chưa thể tính bảng E1
hai lần. Cần file Excel đã điền hoặc JSON sạch từ `a8-gold-check`; tới lúc đó vé 16 và vé 11 vẫn chặn đúng theo tài
liệu mới.

---

# Vòng 32 — Kiểm chứng sau sửa F96, F98–F105 và vé 16 · 2026-09-19

Kiểm trên bản chép của cây làm việc (commit `7dc89f7`) và trên artifact thật, chỉ đọc. Nhân viên đã commit cả
`a033b89` (A6–A10) lẫn `7dc89f7` (vòng 32 và vé 16), nên lần này không còn việc chưa commit nào.

## Kết luận: **nhận**

Mọi con số nhân viên khai đều khớp khi tôi đo lại độc lập, không sai một chữ số nào.

| Hạng mục | Cách tôi kiểm | Kết quả |
|---|---|---|
| Test | toàn bộ suite, chặn socket, `HF_HUB_OFFLINE=1` | ✅ **383/383** |
| F104 | đọc code; `clusters` nay ghi `upstream_version=None`, vòng lần ngược dừng và báo lỗi ở `clusters` | ✅ |
| F98 | bộ điều phối truyền thẳng artifact vừa tạo sang stage kế; mọi stage nhận `upstream=` | ✅ |
| F99 | chạy lại phép thử rớt-mạng của tôi (4 node, 3 cặp, rớt ở từng cặp) trên code mới | ✅ **cả bốn kịch bản ra artifact giống hệt nhau**, mọi cặp đều có dòng log |
| F100 | đọc artifact `stages` của bốn tài liệu | ✅ cả bốn `a10-kahn-stage-v5`, `mode=requires`, cổng đạt |
| F96 | đếm lại `evidence_hard` trên artifact `validated` | ✅ **286 cứng / 41 mềm**, khớp khai |
| F101 | đo lại khối "cạnh trước" trong nhật ký pass chính | ✅ `xstk` 69.013 → **29.609** ký tự chỗ lớn nhất, tổng 1.392.009 → **417.006**; log có `previous_edges_omitted_count` |
| F102 | đo cỡ payload từng stage | ✅ `xstk` bản cuối 10,80 → **2,07 MB**; bảy payload của cả lượt còn 17,72 MB |
| Vé 16 | đếm lại `provenance_log`, kiểm quote độc lập, kiểm bất biến add-only | ✅ 18 lời gọi, **9 chunk được thêm**, 0 quote sai, 0 vi phạm add-only, 0 node learnable rỗng provenance |
| Chi phí | cộng lại `usd` từ manifest của cả ba stage có gọi mô hình | ✅ **0,790044 USD**, đúng tới chữ số cuối |
| Tái lập | chạy `roadmap --stop-after stages` cho `naive-bayes` trên bản chép artifact, chặn socket | ✅ `v19`, `reused=true`, 0 lời gọi |

## Hai điều tôi kiểm khác kết luận của nhân viên

**Bốn cờ "nơi dạy sai" của người gán: một là lỗi provenance thật, ba là lỗi nhãn trang.** Tôi tra thẳng PDF:

- `Hàm ước lượng`: câu định nghĩa nằm ở chunk trang 22, trước đây không có trong provenance. Stage mới **thêm đúng
  chunk đó** — đây là ca F105 thật.
- `Khoảng tin cậy`, `Độ tin cậy`, `Xác suất mắc sai lầm`: cả ba **đã có sẵn** chunk `c_7d32d39dc6` trong provenance,
  và chunk ấy **thật sự chứa** câu "Số thực 1 − α được gọi là độ tin cậy của ước lượng, số thực α là xác suất mắc sai
  lầm của ước lượng". Nhân viên nói đúng. Nhưng câu đó nằm ở **PDF trang 23**, trong khi artifact ghi chunk ở
  `page: 22`, vì chunk **bắt đầu** ở trang 22 rồi vắt sang 23.

Nghĩa là ba cờ kia không phải lỗi provenance mà là **lỗi nhãn trang trong file gán** — cột "Nơi dạy" hiển thị trang
bắt đầu của chunk, nên người gán bị chỉ sớm một trang ở mọi chunk vắt trang. Đây là lỗi công cụ vé 04, **của tôi**,
ghi thành F106 dưới đây.

**File nhãn đã điền có tồn tại.** Nhân viên tìm trong scratchpad và kết luận chỉ có template trống; file thật nằm ở
`artifacts/a8-gold/xstk-ch3-1-chuong-10-13-A1-output.xlsx`, và bản JSON đã kiểm là `artifacts/a8-gold/A1.json`.
Tôi đã chạy cổng E1 trước/sau và dán bảng vào vé 16: vá làm **2 trong 52 cạnh** đổi loại vị trí, cả hai đi về "cùng
chunk". Vé 16 nay đủ cổng.

## F106 🟡 — Cột "Nơi dạy" chỉ trang bắt đầu của chunk, chunk vắt trang thì chỉ sai chỗ — **của tôi (vé 04)**

**Bằng chứng.** Chunk `c_7d32d39dc6` ghi `page: 22`; câu định nghĩa nó chứa nằm ở PDF trang 23. Người gán cắm ba cờ
"nơi dạy sai" chỉ vì lý do này, và mỗi cờ tốn công đọc dò của họ.

**Nguyên nhân.** Metadata chunk chỉ có **một** trường `page` — trang đầu — không có trang cuối. Công cụ vé 04 in
thẳng trường đó.

**Cách sửa, theo thứ tự rẻ dần.**
- (a) Hướng dẫn gán ghi rõ: "một đoạn có thể vắt sang trang kế; tìm câu định nghĩa quanh trang ghi trong cột". Sửa
  trong một câu, không đụng code.
- (b) Với node có chunk được stage `provenance` thêm vào, in luôn **câu định nghĩa** mà mô hình đã trích và code đã
  kiểm nguyên văn — người gán không phải dò trang nữa.
- (c) Ghi `page_start`/`page_end` cho chunk. Đúng nhất nhưng đụng phase B0 đã đóng.

Tôi làm (a) và (b) trước khi sinh file gán cho hai chương vàng; (c) để lại cho đợt nghiên cứu sau.

## Điều kiện để mở vé 11

Đã đủ. Vé 16 qua cổng, vé 11 không còn bị chặn về kỹ thuật. Trước khi chạy `doc-2` nên xem lại hai điểm đã ghi trong
vé 11: watermark của `doc-1` và luật ngôn ngữ của A5 với tài liệu tiếng Anh.

---

## Lượt gán thử hai người — `xstk-ch3-1` §2, 2026-09-19

Hai người gán độc lập trên cùng đơn vị 10–13 (26 khái niệm đích, 98 khái niệm cho phép chọn làm tiên quyết). Đây là
**lượt gán thử** trên tài liệu phát triển, không phải bộ vàng; giá trị của nó là đo xem giao thức có được hiểu giống
nhau không, **trước** khi tiêu công vào hai chương vàng thật.

| | A1 | A2 |
|---|---:|---:|
| Quan hệ ghi được | 52 | 55 |
| Cờ | 27 | 9 |
| Bộ đọc `a8-gold-check` | 0 lỗi | 0 lỗi |
| Thời gian gán / rà soát | chưa điền | chưa điền |

**Đồng thuận** (không gian 2.522 cặp ứng viên = 26 đích × mọi khái niệm):

| Cách tính | κ | Cùng ghi | Chỉ A1 | Chỉ A2 |
|---|---:|---:|---:|---:|
| Cạnh trực tiếp | **0,360** | 20 | 32 | 35 |
| Có tính đồng thuận ngầm qua bắc cầu | **0,429** | 75 | 44 | 130 |

**Đọc số này thế nào.** PREAP gốc báo κ 0,45–0,71 sau khi có hướng dẫn, gán thử và hội ý; các bộ dữ liệu tiên quyết
khác báo 0,16–0,60 và 0,01–0,27. Lượt này đạt 0,36 (0,43 nếu tính bắc cầu) **khi chưa có bước hội ý và chưa thống
nhất cách hiểu**, nên nằm đúng chỗ dự đoán được. Hai người chỉ trùng nhau 20 trên 87 cạnh của hợp — chênh lệch chủ
yếu là **mức chi tiết**: một người ghi chuỗi ngắn, người kia ghi thêm các cạnh bắc cầu; đúng cái mà phép tính có
đồng thuận ngầm làm nhẹ đi (20 → 75 cặp cùng khẳng định).

**Việc phải làm trước khi gán chương vàng thật:** hai người **hội ý** 67 cạnh lệch, chốt lại ba điểm — thế nào là
"trực tiếp", có ghi cạnh đã suy ra được qua bắc cầu không, và khi nào dùng mức *Hữu ích* thay vì *Bắt buộc*. Sau đó
mới gán `doc-1` và `doc-2`. Cũng nên điền hai ô thời gian, vì báo cáo cần chi phí công sức.

**E1/E2 trên bộ vàng hợp của lượt thử** (87 cạnh, chỉ để tham khảo, không phải số của báo cáo):

| Loại vị trí | Cạnh | Tỉ lệ | KTC 95% |
|---|---:|---:|---|
| cùng chunk | 19 | 21,8% | 12–34% |
| cùng mục | 3 | 3,4% | 0–10% |
| cùng chương | 9 | 10,3% | 4–17% |
| cùng cụm chủ đề | 5 | 5,7% | 1–11% |
| **bắc cầu (kênh cứng)** | **39** | **44,8%** | 34–55% |
| bắc cầu (chỉ dense) | 4 | 4,6% | 1–9% |
| ngầm | 8 | 9,2% | 3–17% |

Bộ sinh: `contact` một mình recall 0,62 với 848 cặp; `contact + same_section` 0,80; thêm `citation_hard` 0,87; thêm
`proposed_relation` 0,91; cả năm 0,92 với 1.104 cặp. `citation_soft` chỉ đóng góp **1** cạnh mà không bộ nào khác có.

## F106 — đã sửa, 2026-09-19

Cột "Nơi dạy" nay lấy từ artifact stage `provenance` khi truyền `--graph`, và sheet Khái niệm có thêm cột **"Câu định
nghĩa máy tìm được"** in nguyên văn câu mà stage provenance đã trích và code đã kiểm. Hướng dẫn gán và sheet Hướng dẫn
ghi rõ: cột Nơi dạy là **trang bắt đầu** của đoạn, đoạn có thể vắt sang trang kế. Hai test mới khoá hành vi: nơi dạy
đi theo provenance đã vá, câu trích bị loại không lên file gán, và đổi phạm vi đích thì `concept_hash` đổi theo.

---

# Vòng 33 — Chạy Vé 11, dừng tại `doc-3` · 2026-09-19

Chủ dự án xác nhận Vé 11 hết chặn và yêu cầu chạy đúng `doc-3` → `doc-1` → `doc-2`. Tôi chạy thật `doc-3`, không
sửa code. Ingest, A3 và A3' thành công; A4 dừng trước khi sinh artifact. Vì thứ tự của vé và điều khoản "cần sửa
code thì dừng và báo", `doc-1`/`doc-2` chưa được đụng tới.

| Số đo `doc-3` | Kết quả |
|---|---:|
| Trang / section / chunk / window | 110 / 93 / 94 / 85 |
| Node A3 / `learnable` / media / cạnh A3 | 201 / 105 / 96 / 120 |
| Lời gọi A3 | 256 |
| Cỡ parse tree / chunks / candidates / retrieval | 10,01 / 0,14 / 4,41 / 2,12 MiB |
| Phiên bản | parse v1, chunks v1, candidates v1, retrieval v1 |
| Cache khóa mạng | `extract` và `index` đều tái dùng v1 |

Parse giữ 483/488 node, bỏ 1 caption và 4 formula, sắp lại 9 trang; cảnh báo cuối gồm caption mồ côi, formula rỗng
và heading lặp. A3 không có section lỗi nhưng có 5 extraction rỗng, 16 `evidence_missing_name` và 2 kiểu
`learnable_low_confidence`.

## F107 🔴 — A3 trích biến `X` thành khái niệm học được, A4 dừng ở bất biến tên ký hiệu

Candidate `candidate_e70160c0a9cacaf16e6e4a95` là `X`, kiểu `concept`, `learnable=true`. Prompt mặc định đã cấm
variable symbols, nên đây là đầu ra lọt qua validation A3. Cả `a4 --prepare` và `a4 --names-only` đều dừng với
`node chỉ có tên ký hiệu`; lần `names-only` chứng minh lỗi không phụ thuộc mạng/embedding.

Không xoá tay candidate và không sửa A3/A4 trong Vé 11. Cần ticket regression riêng: mô hình trả entity chỉ là ký
hiệu đơn phải bị A3 loại hoặc chuyển thành symbol không học được, và test phải thấy đỏ khi bỏ guard.

## F108 🟡 — Telemetry A3 chỉ lưu calls, làm thiếu token và chi phí bắt buộc của Vé 11

Artifact ghi `llm_calls=256`, nhưng không giữ usage của từng reply hay tổng input/output token. Với 92 ảnh và hội
thoại nhiều lượt, không thể suy ngược chính xác từ text. Do đó lượt này chưa thể báo token/USD mà không bịa; phải
thêm telemetry A3 trước khi chạy `doc-1` và đặc biệt `doc-2` dưới trần 50 USD.

## F109 🔴 — Gold guard A4 mâu thuẫn với đường chạy tài liệu mới của Vé 11

CLI yêu cầu bộ vàng phải chứa chính `doc_id`. Hai file gold hiện hành chỉ chứa bốn tài liệu cũ, còn kế hoạch cấm sửa
fixture đóng băng. Vì vậy sau F107, `doc-3` vẫn không thể chạy A4/A5 đầy đủ. Cần quyết định rõ: gold bốn tài liệu là
cổng chất lượng toàn cục, hay mỗi tài liệu mới phải qua một lượt gán mù riêng. Không được thêm document rỗng để lách
guard.

**Kết luận vòng:** Vé 16 thật sự đã xong; Vé 11 được mở đúng nhưng phát hiện ba chặn mới. Watermark doc-1 và luật
ngôn ngữ A5 chưa được kiểm vì pipeline chưa được phép vượt doc-3.

---

# Vòng 33 — Kiểm chứng ba chặn của vé 11 · 2026-09-20

Nhân viên chạy thật `doc-3`, gặp ba chặn và **dừng đúng luật của vé** ("cần sửa code thì dừng và báo"), không tự sửa
phase đã đóng, không xoá tay ứng viên, không đụng `doc-1`/`doc-2`. Cách xử lý này đúng.

## Kiểm lại từng chặn

| Mã | Khai của nhân viên | Tôi kiểm | Kết luận |
|---|---|---|---|
| F107 | A3 trả ứng viên tên `X`, `learnable=true`; A4 dừng ở bất biến tên ký hiệu | đọc artifact `candidates/doc-3/v1`: đúng `candidate_e70160c0a9cacaf16e6e4a95` tên `X`, kiểu `concept`, bằng chứng *"X and Y can be anything…"*; còn một ứng viên tên `Y` cùng kiểu | ✅ đúng, và **nặng hơn một bậc**: luật cấm ký hiệu chỉ nằm trong prompt few-shot, code A3 không có guard nào — trái user story 40 |
| F108 | A3 chỉ lưu `llm_calls`, không có token | grep `extract_entities.py`: không bắt `usage`; manifest `doc-3` chỉ có `llm_calls=256` | ✅ đúng; và **A4/A5 cũng thiếu**, không riêng A3 |
| F109 | cổng bộ vàng A4 chặn tài liệu mới | `main.py:369` — `if args.doc_id not in gold["documents"]: raise` | ✅ đúng |

Hai điểm tôi bổ sung so với báo cáo của nhân viên: guard ký hiệu **chưa từng tồn tại trong code** (không phải "lọt qua
validation"), và telemetry thiếu ở **cả A4/A5**, nên vé 17 gộp luôn.

## Quyết định

- **F107 — sửa A3, giữ nguyên bất biến A4.** Loại ứng viên có tên chỉ gồm ký hiệu ngay ở validation của A3, đếm vào
  stats. Viết tắt (`DL`, `AI`) phải sống sót. Bất biến `node chỉ có tên ký hiệu` của `canonical.py` giữ nguyên làm
  chốt cuối. Đây là đưa một luật đang nằm trong prompt về đúng chỗ của nó là code.
- **F108 — thêm telemetry cho A3 và A4/A5**, đúng khuôn `model_calls.py` của A8, kèm nguồn bảng giá và ngày kiểm.
  Bắt buộc phải có **trước** `doc-2`, nếu không thì không giữ được trần 50 USD.
- **F109 — không gán bộ vàng A4 mới cho tài liệu mới.** Căn cứ có sẵn ở spec D13: cờ node sai của người gán nhãn
  tiên quyết chính là mẫu kiểm A4 cho tài liệu mới. `a4` vẫn bắt buộc một bộ vàng hợp lệ làm **cổng hồi quy**, nhưng
  tài liệu ngoài bộ vàng chạy được bằng một cờ tường minh, và manifest ghi `a4_gold_coverage: "none"`. Báo cáo cuối
  phải nói rõ hạn chế này.

Cả ba nằm trong **vé 17**. Vé 11 chặn cho tới khi vé 17 xong.

## Một điều cần chủ dự án đồng ý

Vé 17 **sửa code trong hai phase đã đóng** (A3 và A4). Tôi đề nghị đồng ý, vì cả ba mục đều hẹp, có test riêng, và
không đổi hành vi trên bốn tài liệu cũ: guard ký hiệu chỉ chạm ứng viên mà A4 vốn đã từ chối, telemetry chỉ thêm
trường vào manifest, cổng bộ vàng chỉ nới cho tài liệu **không** có trong bộ vàng. Điều kiện nhận: sau khi sửa,
bốn tài liệu cũ chạy lại phải cho `reused=true` và điểm vàng A4 giữ nguyên 31/0/16.

---

# Vòng 34 — Hoàn tất Vé 17, chạy tiếp Vé 11 và dừng ở watermark · 2026-09-20

Ba sửa hẹp F107–F109 đã hoàn tất. A3 loại tên chính có `alias_kind == symbol` nhưng giữ viết tắt và alias ký hiệu;
A3 cùng A4/A5 ghi `cost_summary`; A4 chỉ cho tài liệu ngoài bộ vàng đi tiếp khi có `--no-gold-for-doc`, đồng thời
ghi coverage `none` và `gold_sheet_id`. Bộ vàng đóng băng không đổi.

## Bằng chứng code, test và hồi quy

- Test mới đã đỏ trên hành vi cũ cho cả ba lỗi rồi xanh sau vá. Mutation đổi `symbol → abbreviation`, loại alias
  ký hiệu, bỏ thought token và bỏ cổng cờ đều bị test bắt. Ca không có usage ghi 0 thay vì lỗi.
- Toàn suite **434/434** xanh. Bốn A4 cũ chạy trong sandbox mạng cho `reused=true` ở v8/v7/v7/v7.
- Ticket ghi baseline `31/0/16`, nhưng đó là A4 v1 trước quyết định Vòng 27. `main` hiện hành đã nhận quan hệ mở v3;
  số đúng không đổi là **35/2/12** (11/0/0, 10/0/0, 7/1/3, 7/1/9). Không sinh artifact A4 cũ mới.

## Số thật `doc-3`

| Bước | Kết quả | Token / chi phí |
|---|---|---|
| A3 v2 | 201→198 ứng viên; 105→102 learnable; guard loại `X`, `Y`; 117 cạnh | 256 calls; 671.846 in + 47.240 out; **0,2388215 USD** |
| A3' | 94 chunk, tái dùng v1 | 0 lời gọi |
| A4/A5 v1 | 154 node (58 text, 96 media), 129 cạnh; ngôn ngữ `en` | 56 calls; 57.327 in + 16.733 out; **0,03943125 USD** |
| Tổng | 312 calls | 729.173 in + 63.973 out; **0,27825275 USD** |

Guard đếm đúng 2. Tổng ứng viên giảm 3 vì ngoài `X`, `Y`, một bản lặp `Deep Learning` ở section khác không xuất hiện
trong lần gọi thật mới; đây là biến thiên model, không phải guard. Manifest canonical ghi coverage `none`; 58/58 mô
tả text qua luật tiếng Anh. Replay A3/A4 không mạng đều tái dùng.

## Điều kiện dừng ở `doc-1`

Ingest `doc-1` v1 hoàn tất: 159 trang, 118 section, 229 chunk, 80 window. Trước bất kỳ lời gọi A3 nào, quét chunk
tìm thấy **114/229 chunk trên 110 trang** còn chuỗi `lOMoARcPSD`; một chunk còn `Scan to open on Studeersnel`.
Regex email không thấy địa chỉ, nhưng watermark một mình đã đủ kích hoạt điều kiện dừng. Không nội dung doc-1 nào được
gửi Gemini; `doc-2` chưa chạy. Vé 11 vì vậy chặn ở khâu làm sạch dữ liệu, không còn chặn ở code F107–F109.

---

# Vòng 34 — Hội ý bộ vàng, và kiểm vé 17 · 2026-09-20

## Hội ý: giao thức chạy được, và cả hai người đều đóng góp

Chủ dự án chọn hướng (a) — hội ý thật từng cạnh lệch — và đã làm xong trên lượt gán thử `xstk-ch3-1` §2.

| | Số |
|---|---:|
| Cả hai cùng ghi, vào thẳng bộ vàng | 20 |
| Cạnh lệch phải quyết | 67 |
| Quyết **Giữ** | 42 |
| Quyết **Bỏ** | 25 |
| **Bộ vàng cuối** | **62 cạnh / 26 khái niệm đích** |

Phân bố quyết định theo người đề xuất: của A1 giữ 25 bỏ 7; của A2 giữ 17 bỏ 18. Nghĩa là **cả hai người đều đóng
góp cạnh đúng**, và nếu lúc đầu lấy nguyên nhãn của một người thì mất 17 hoặc 25 cạnh thật. Đây là lý do spec D13
bắt buộc hội ý, và lượt này chứng minh luật ấy đáng giá.

**Cả 67 dòng đều có ghi lý do.** Ba kiểu lý do hay gặp, đáng đưa vào báo cáo làm ví dụ: cạnh bắc cầu đã suy ra được
từ hai cạnh khác nên bỏ; "bài toán ngược" là quan hệ đối sánh chứ không phải tiên quyết; và cạnh đi thẳng từ công
thức nên giữ dù người kia không ghi.

## E1 và E2 trên bộ vàng đã hội ý

Vẫn là tài liệu phát triển nên **không phải số của báo cáo**, nhưng đây là hình dạng thật mà hai chương vàng sẽ cho.

| Loại vị trí | Hội ý (62 cạnh) | Nếu lấy hợp (87 cạnh) |
|---|---:|---:|
| cùng chunk | 13 · 21,0% | 19 |
| cùng mục | 2 · 3,2% | 3 |
| cùng chương | 7 · 11,3% | 9 |
| cùng cụm chủ đề | 3 · 4,8% | 5 |
| **bắc cầu (kênh cứng)** | **30 · 48,4%** | 39 |
| bắc cầu (chỉ dense) | 3 · 4,8% | 4 |
| ngầm | 4 · 6,5% | 8 |

Kết luận trung tâm **không đổi khi siết bộ vàng**: khoảng một nửa số cạnh tiên quyết không nằm cùng chương lẫn cùng
cụm, chỉ nối được nhờ một chunk nhắc cả hai đầu. Hội ý làm giảm đều cả bảy loại chứ không cắt riêng loại nào.

E2 trên bộ vàng hội ý: `contact` một mình recall 0,65 với 848 cặp; `contact + same_section` 0,84; thêm
`proposed_relation` 0,90; thêm `citation_hard` 0,94; cả năm 0,95 với 1.104 cặp. `citation_soft` vẫn chỉ có **1**
cạnh riêng nó. Trục chương một mình phủ 0,97.

## Kiểm vé 17 — nhận

| Khai của nhân viên | Tôi đếm lại | |
|---|---|---|
| A3 `doc-3` 201 → 198 ứng viên, guard loại đúng `X` và `Y` | v1 có `X`, `Y`; v2 không còn, `DL`/`AI` vẫn sống | ✅ |
| `rejected_symbol_only_name = 2` | đúng 2 | ✅ |
| Telemetry A3 671.846 / 47.240 token, 0,2388215 USD | khớp manifest, kèm `pricing_source` có URL và ngày kiểm | ✅ |
| A4/A5 `doc-3` 0,03943125 USD, `a4_gold_coverage=none` | khớp, có cả `gold_sheet_id` của bộ vàng cổng hồi quy | ✅ |
| `doc-1`: 114/229 chunk còn watermark, 0 chunk có email | đếm lại đúng 114 và 0 | ✅ |

Nhân viên dừng đúng chỗ ở `doc-1` thay vì lặng lẽ lọc trong artifact. Chặn này thành **vé 18**.

## Việc còn treo

- **Vé 18** cần chủ dự án chọn hướng làm sạch watermark; tôi đề xuất (a) — ingest nhận mẫu dòng cần bỏ, mặc định
  không đổi nên bốn tài liệu cũ không bị ảnh hưởng.
- Sau đó vé 11 chạy tiếp `doc-1` rồi `doc-2`, và hai chương vàng đã chốt là `doc-1` Chương 5 và `doc-2` mục 3C.

---

# Vòng 35 — Kiểm thử chi tiết vé 17 · 2026-09-20

Vòng 34 mới đếm artifact. Vòng này đọc code, chạy suite, chạy đột biến và tính lại mốc điểm vàng.

## Kết luận: **nhận vé 17**, kèm ba mục phải làm trước khi `doc-2` thành chương vàng

| Hạng mục | Cách kiểm | Kết quả |
|---|---|---|
| Suite | toàn bộ trên bản chép, chặn socket, `HF_HUB_OFFLINE=1` | ✅ **434/434** |
| Đột biến | 12 con nhắm thẳng ba guard của vé | **11 bắt, 1 lọt** (xem F112) |
| Guard ký hiệu | đọc code: nằm trong nhánh phân tích entity, sau khi kiểm tên rỗng, trước mọi thứ khác | ✅ chỉ chạm **tên node**, không chạm alias |
| A3 `doc-3` | đếm lại candidates v1 → v2 | ✅ 201 → 198; `X`, `Y` mất; `DL`, `AI` còn; `rejected_symbol_only_name = 2` |
| Telemetry A3 | đọc manifest v2 | ✅ 671.846 / 47.240 token, 0,2388215 USD, kèm `pricing_source` có URL và ngày kiểm |
| Telemetry A4/A5 | đọc manifest canonical `doc-3` | ✅ 57.327 / 16.733 token, 0,03943125 USD |
| Cổng bộ vàng | đọc code CLI | ✅ vẫn bắt buộc bộ vàng hợp lệ; tài liệu ngoài bộ vàng cần cờ tường minh; manifest ghi `a4_gold_coverage=none` và `gold_sheet_id` |
| `doc-1` | đếm lại chunk | ✅ 114/229 còn watermark, **0** chunk có email — đúng khai |

## Nhân viên đính chính tôi, và họ đúng

Tôi đặt điều kiện nhận lại là điểm vàng A4 giữ **31/0/16**. Nhân viên chỉ ra đó là baseline v1 cũ. Tôi chạy lại
`a4-evaluate` trên bốn artifact hiện hành: **11/0/0 · 10/0/0 · 7/1/3 · 7/1/9**, tổng **35/2/12**. Đúng như họ nói.
Mốc nghiệm thu đúng từ nay là 35/2/12; tôi sửa lại điều kiện trong vé.

## F110 🟠 — Guard tên ký hiệu sẽ loại cả khái niệm được gọi bằng ký hiệu, và `doc-2` đầy loại đó

Guard đúng với ca của `doc-3`: `X` và `Y` trong câu *"X and Y can be anything"* không phải khái niệm. Nhưng luật là
`alias_kind(name) == "symbol"`, và trên tên kiểu Axler nó cho:

| Tên | `alias_kind` | |
|---|---|---|
| `X`, `Y`, `π`, `χ²` | symbol | đúng, nên loại |
| `DL`, `AI`, `ERD`, `S²` | abbreviation | đúng, được giữ |
| **`R^n`, `F^n`, `L(V,W)`, `P(F)`, `𝐅`, `𝐑𝑛`** | **symbol** | **sẽ bị loại — nhưng đây là khái niệm trung tâm của `doc-2`** |

`doc-2` là *Linear Algebra Done Right*, và mục 3C đã chọn làm chương vàng nói suốt về `ℒ(V,W)`, `𝐅^{m,n}`, `𝐅ⁿ`.
Nếu A3 trả các khái niệm ấy bằng tên ký hiệu thì guard loại **im lặng**, và bộ vàng sẽ có khái niệm đích mà pipeline
không hề biết.

**Không sửa vội.** Có thể mô hình vẫn đặt tên chữ cho chúng ("the vector space of linear maps") và để ký hiệu vào
trường `symbols`, đúng như `CONTEXT.md` mô tả. Nhưng phải **đo trước khi dùng `doc-2` làm chương vàng**:

- [ ] Sau khi `doc-2` chạy A3: đọc `rejected_symbol_only_name` và **danh sách tên bị loại** (cần F111), lọc riêng
      các trang của mục 3C.
- [ ] Nếu có khái niệm thật bị loại: đổi guard thành "loại tên ký hiệu **chỉ khi** entity không có alias nào là tên
      chữ; có alias chữ thì lấy alias làm tên và giữ ký hiệu vào `symbols`".

## F111 🟡 — Guard chỉ đếm, không ghi tên bị loại

`stats["rejected_symbol_only_name"]` là một con số; artifact không giữ tên nào. Không có nó thì F110 không kiểm
được, và người đọc báo cáo cũng không biết đã mất gì. Thêm một danh sách có trần, ví dụ 50 tên, vào `warnings` hoặc
một khoá riêng. Việc nhỏ, nên làm cùng vé 18.

## F112 🟢 — Một đột biến lọt: bộ vàng không cần "hoàn chỉnh"

Đổi `load_gold(..., require_complete=True)` thành `False` không làm test nào đỏ. Cả lý do giữ `--gold` bắt buộc là
để nó làm **cổng hồi quy**; bộ vàng rút gọn thì cổng ấy vô nghĩa. Thêm một test ghim `require_complete`.

## Một chỗ nữa cần ghi vào báo cáo

`algorithm_id` của A3 lên `a3-section-conversation-v5`. Bốn tài liệu phát triển giữ artifact cũ sinh bởi **v4**, ba
tài liệu mới dùng **v5**. Không ai sai, nhưng corpus có **hai cấu hình A3 khác nhau**, và báo cáo phải nói rõ thay
vì để người đọc tự phát hiện.

## Một lỗi sổ sách của tôi

Code vé 17 nằm trong commit `3bcf9cc` mang thông điệp review của tôi, vì nhân viên đã `git add` sẵn và lệnh commit
của tôi cuốn theo. Nội dung repo không sai, nhưng thông điệp commit không mô tả đúng thứ nó chứa. Tôi không viết lại
lịch sử vì nhân viên đã commit tiếp lên trên; ghi lại ở đây để ai đọc `git log` sau này không bị lạc.

---

# Xử lý Vé 18 và chạy tiếp Vé 11 · 2026-09-21

Vé 18 cài hướng (a): `ingest --strip-line` lặp lại, so khớp sau chuẩn hóa khoảng trắng trước cắt chunk; không
khai mẫu thì config/hash và nội dung giữ nguyên. Manifest parse/chunk cùng ghi mẫu và số dòng bị tác động. Test
đã thấy đỏ khi bỏ chuẩn hóa khoảng trắng, dời lọc sau lưu parse và quên manifest chunk; thêm ca `raw_text`, đếm
một dòng dù khớp hai lần, giữ nguyên text khi không có mẫu. Toàn bộ suite xanh. `baocao-canhan` và `doc-3`
tái dùng artifact không mẫu; chưa thể nghiệm thu đủ **4/4** tài liệu cũ: hai artifact cũ có adapter config khác
hiện hành (đã dừng parse trước khi ghi version), còn PDF `nhap-mon-ml` không có trong workspace.

`doc-1`: 229 → **218 chunk**; 140 dòng bị tác động. Kiểm độc lập toàn bộ parse v3 (`text` và `raw_text`) và
JSON chunk/section/document v3: **0** mã theo dõi, **0** Studeersnel, **0** email. Phát lại ingest tái dùng v3.
`raw_text` của bản v2 từng còn 140 node có mã; bản v3 đã sạch. Các artifact v1/v2 nhạy cảm vẫn nằm ở kho cục bộ,
không tự ý xóa. A3 v2 từ v3: 153 ứng viên/139 learnable/227 cạnh; chỉ mục v2 218 chunk; A4/A5 canonical v2
98 node/214 cạnh, replay `reused=true`. Chi phí mới A3 0,50755425 USD, A4/A5 0,03890375 USD; xem [Vé 11](../task/a6-a8-tien-quyet/11-nap-ba-tai-lieu-moi.md)
để phân biệt tổng các lần chạy khỏi hóa đơn thực.

**F111 đóng:** A3 ghi danh sách tên ký hiệu bị loại, khử trùng lặp và trần 50, bên cạnh số lượt; có test 51
tên. **F112 đóng:** test CLI ghim `load_gold(..., require_complete=True)` ở cả nhánh từ chối và nhánh chấp
nhận tài liệu mới; đột biến đổi `False` đã bị bắt.

**F110 vẫn mở về chất lượng `doc-2`:** guard đã cứu tên ký hiệu khi có alias chữ và evidence xác thực (ký hiệu
được giữ làm alias, endpoint cạnh được nối lại; test đỏ trước sửa). Nhưng A3 `doc-2` v2 vẫn loại **47 lượt/36
tên**; `ℒ(V,W)`, `L(V,W)`, `𝐅^{m,n}` trong số đó. A3 có 1.370 ứng viên, 1.298 learnable, 606 cạnh; chỉ mục
1.038 chunk. Không chạy A4/A5 hay lấy mục 3C làm vàng khi các khái niệm trung tâm còn mất. Cây parse còn gắn
`Exercises 3C` dưới `3.56`, nên cần kiểm scope chương. **Vấn đề mới về `doc-1`:** A5 phân loại `en` cho PDF
tiếng Việt bị lỗi mã; 51 mô tả viết lại, 27 fallback. Artifact canonical hoàn thành về mặt kỹ thuật nhưng không
đạt chất lượng ngôn ngữ để gán vàng. Vé 11 vẫn mở; cần ticket riêng cho hai vấn đề đầu vào/chất lượng này.

---

# Vòng 36 — Nghiên cứu A9/A10, kiểm thử vé 18, và đợt vá vé 19–22 · 2026-09-22

Vòng này có ba phần: một đợt khảo sát văn liệu cho A9/A10, kiểm thử vé 18, và một spec vá cắt thành bốn vé.
Toàn bộ căn cứ nằm ở [`report/nghien-cuu-a9-a10-kiem-dinh-va-lo-trinh.md`](../report/nghien-cuu-a9-a10-kiem-dinh-va-lo-trinh.md)
cùng hai phụ lục văn liệu; spec ở
[`doc/va-a9-a10-do-thi-tot-va-lo-trinh-dung-duoc-spec.md`](../doc/va-a9-a10-do-thi-tot-va-lo-trinh-dung-duoc-spec.md).

## Kết luận vé 18: **nhận**

| Hạng mục | Cách kiểm | Kết quả |
|---|---|---|
| Suite | toàn bộ, chặn socket, `HF_HUB_OFFLINE=1` | ✅ thoát mã 0 |
| `doc-1` sạch watermark | đếm lại trên `chunks.json` cả ba phiên bản | ✅ v1 có **159** lần `lOMoARcPSD` và 2 lần `Studeersnel`; v2/v3 **0 và 0**; 229 → 218 chunk |
| Tương thích ngược | đọc mã | ✅ `strip_lines` chỉ vào `parser_config` **khi có mẫu**, nên bốn tài liệu cũ giữ nguyên hash |
| F111 | đọc artifact `doc-2` | ✅ `rejected_symbol_only_names` có 36 mục, trần 50 |
| F112 | đọc test | ✅ ghim `require_complete=True` ở cả hai nhánh |

**Nhân viên làm vượt vé, và báo cáo trung thực về chỗ nó không đủ.** Vé 18 chỉ yêu cầu *ghi* tên bị loại (F111).
Họ cài luôn bản sửa F110 mà vòng 35 đề xuất — có alias chữ thì lấy alias làm tên, giữ ký hiệu làm alias — rồi **tự
đo và nói thẳng rằng nó chỉ cứu được 3 ứng viên, không đủ cho mục 3C**. `algorithm_id` lên `a3-section-conversation-v6`.

## F110 nay là số đo, không còn là cảnh báo

Tôi đọc lại danh sách 36 tên bị loại trên `doc-2`. Guard đang làm lẫn hai việc:

- **Loại đúng:** `i`, `0`, `{0}`, `V`, `C`, `F`, `R` — ký hiệu trơ. Và `3.65`, `3.68`, `3.94`, `6.49`, `6.54` —
  **số hiệu định lý**.
- **Loại sai:** `ℒ(V,W)`, `ℒ(𝑉, 𝑊)`, `L(V, W)`, `ℒ(𝑉)`, `𝐅^{m,n}`, `F^m,n`, `F^n`, `𝒫(𝐅)`, `𝒫ₙ(𝐅)`, `𝒫 2(𝐑)`,
  `P4(R)`, `ℳ`, `B(V, W)`, `S ⊗ T`, `V^m`, `𝐶[-𝜋 , 𝜋]` — **đúng những đối tượng mà mục 3C nói về**.

Luật `alias_kind` cho ra `symbol` khi không có từ nào dài hơn một ký tự chứa chữ Latin. `ℒ(V,W)` rơi vào đó vì
`ℒ`, `V`, `W` đều dài một ký tự. → vé 19 V1.

## F114 🔴 — A5 đoán sai ngôn ngữ của `doc-1`, và nó chặn chương vàng tiếng Việt

Đây là phát hiện nặng nhất của vòng, do nhân viên nêu và tôi kiểm lại độc lập trên `artifacts/canonical/doc-1/v2`:

- manifest: `document_language = 'en'`, `a5_rewritten_language = 51`, `a5_fallback = 27`
- **81/98 tên node có dấu tiếng Việt** — nội dung đúng là tiếng Việt
- **61/98 mô tả không có dấu tiếng Việt** — tức được viết bằng tiếng Anh

Gốc: parse còn **5.591 ký tự vùng dùng riêng**, nên bộ đoán ngôn ngữ đọc chúng như chữ lạ. Hệ quả: `doc-1` Chương 5
**không dùng làm chương vàng được** — người gán sẽ đọc mô tả tiếng Anh cho một giáo trình tiếng Việt. → vé 19 V2.

## F113 🟢 — cờ rỗng lọt vào trang duyệt

`nhap-mon-ml` có **hai cờ rỗng `{}`** trong `secondary_flags`. Chúng qua A9 thành `{"status": "unresolved"}` không
`kind`, không `node_id`, không lý do, rồi vào `display_flags`. Không ai xử lý được, và chúng làm phồng
`validation_flag_count`. Gốc: `domain/secondary.py:139` kiểm kiểu của **danh sách**, không kiểm **từng phần tử**.
→ vé 20 V11.

## F115 🟢 — bước bỏ watermark hứa nhiều hơn nó làm

`strip_line_algorithm` tên là `normalized-substring-all-fields-v2`, nhưng `_strip_line_patterns` chỉ chạm
`node.text` và `node.raw_text`. `DocumentNode` còn có `table_rows` và `context_prefix`. Với `doc-1` thì đủ (quét độc
lập cho 0 kết quả), nhưng một watermark nằm trong ô bảng sẽ lọt im lặng. Hoặc phủ đủ, hoặc đổi tên. → vé 19 V11.

## F116 🟡 — A3 trích số hiệu định lý làm tên khái niệm

`3.65`, `3.68`, `3.94`, `6.49`, `6.54` xuất hiện trong danh sách tên bị loại của `doc-2`, tức A3 **đã** đề cử chúng
làm khái niệm. Guard ký hiệu đang che việc đó. Khi vé 19 nới guard, chúng phải tiếp tục bị loại — nhưng nguyên nhân
gốc nằm ở prompt/luật của A3, không ở guard. Ghi lại để đợt A3 sau xử lý; chưa cắt vé.

## Một việc dở của tôi, đã xong trong vòng này

Lệnh CLI `a8-gold-merge` (hội ý bộ vàng) **chưa từng được commit và không có test nào phủ**: commit `c8700bf` chỉ
mang các hàm ở tầng use-case cùng test của chúng, còn phần nối vào CLI nằm lại trên máy tôi.

*(Đính chính bản nháp đầu của mục này: tôi có viết "toàn bộ mặt CLI của nhóm `a8-gold` chưa có test nào" — sai.
`a8-gold-sheet` và `a8-gold-check` **có** test CLI, nằm ở `tests/unit/application/test_a8_gold.py` chứ không ở
`tests/unit/presentation/test_cli.py`, nên lượt grep đầu của tôi không thấy. Lỗ hổng thật chỉ gồm `a8-gold-merge`
— nay đã vá — và **`a8-score` vẫn chưa có test CLI nào**.)*

Đã thêm một test hành vi ghim bốn thứ: `--graph` phải đi tới scope dưới dạng provenance đã vá (D13, F105/F106);
phải nhận **cả hai** người gán, vì rơi mất một người thì mọi cạnh lệch thành cạnh đồng thuận; có lỗi thì **không
ghi** bộ vàng ra đĩa; và không ghi được ra ngoài `artifact_dir`. **4/4 đột biến bị bắt.**

## Đợt vá: vé 19–22

Chủ dự án chốt ba hướng ngày 2026-09-22: **(1)** sửa cả hai chặn, giữ nguyên hai chương vàng; **(2)** stage vẫn là
**nhóm học song song được**, đổi thuật toán chứ không đổi định nghĩa; **(3)** chu trình hai cạnh được **gắn cờ nghi
lỗi kiểu quan hệ và loại khỏi `requires`**.

| Vé | Nội dung | Ai | Chặn bởi |
|---|---|---|---|
| **19** | Mở khoá hai chương vàng (V1 tên ký hiệu, V2 ngôn ngữ, F115) | nhân viên | — **đường găng của cả đợt** |
| **20** | A9 v2: MFAS có trọng số giải chính xác, cặp hai chiều, thứ tự bước, cổng, F113 | nhân viên | — |
| **21** | A10 v2: Coffman–Graham có trần độ rộng, bỏ phép giao cụm | nhân viên | vé 20 |
| **22** | Hai chỉ số đánh giá lộ trình: τ so mục lục, tỉ lệ vi phạm cạnh vàng | Claude | vé 21 |

Ba số đo quyết định hướng đi, tất cả lấy từ artifact thật:

- `xstk-ch3-1`: 98 khái niệm → **63 stage, 39 stage một khái niệm**, trong khi cận dưới lý thuyết là **13**.
  Bỏ phép giao cụm và thêm trần độ rộng cho **16 stage**, tầng 1 từ 12 xuống 8, **không mất bất biến nào**.
- Lộ trình trùng thứ tự giáo trình ở **51,0%** số cặp trên `baocao-canhan` — không phân biệt được với tung đồng xu.
- Trên bộ vàng hội ý: cạnh vàng cho τ **+0,803**, cạnh máy cho **+0,603**, và **11/62 cạnh vàng bị lộ trình máy xếp
  ngược**.

Và hai chỗ spec đang dẫn nguồn sai, phải viết lại: lý lẽ giữ chu trình hai cạnh (tác giả bộ dữ liệu viết ngược lại
điều ta đang dẫn họ), và mọi viện dẫn tâm lý học cho con số 5–8 (chính tác giả của "7±2" gọi nó là trùng hợp tai hại).

---

# Vòng 37 — Kiểm thử vé 20 (A9 v2) · 2026-09-22

Kiểm trên **bản chép** cây làm việc, vì nhân viên đang làm song song vé 19, 20 và 21 và chưa commit gì. Bản chép
dùng `PYTHONPATH` trỏ vào `src` của nó nên không nạp nhầm mã thật.

## Kết luận: **nhận vé 20**, kèm hai mục phải làm và một chỗ repo đang đỏ

| Hạng mục | Cách kiểm | Kết quả |
|---|---|---|
| Bốn tài liệu, số khai trong vé | đọc thẳng artifact mới sinh | ✅ **khớp từng con số** |
| Đồ thị sau A9 là DAG | tự chạy SCC trên `requires_edges` | ✅ SCC lớn nhất = 1 ở cả bốn |
| `confidence` ra khỏi quyết định | đọc `cycle_keep_order` trong manifest | ✅ `['evidence_kind','provenance_order','independent_source_count']` |
| Mã hoá trọng số theo bậc cơ số | đọc mã, kiểm bất đẳng thức | ✅ `evidence_base` lớn hơn **tổng** mọi số hạng bậc dưới trên toàn bộ cạnh |
| Liệt kê chu trình đơn | đọc mã | ✅ dạng chuẩn tắc Johnson (chỉ đi tới node lớn hơn node gốc) → đầy đủ khi chưa bị chặn |
| Phủ tập hợp | đọc mã | ✅ nhánh trên **một** chu trình chưa phủ → đúng là lời giải chính xác |
| Cặp hai chiều | đọc mã + artifact | ✅ tìm **toàn cục** chứ không theo từng SCC, nên bắt được cả cặp nằm trong SCC lớn |
| Đột biến | 12 phép, nhắm thẳng luật của vé | **11 bắt, 1 lọt** |
| Suite | toàn bộ, chặn socket | 456 xanh · 1 đỏ thật (xem F119) · 1 đỏ do bản chép thiếu `.env.example` |

Số khớp: `naive-bayes` 38/9/24 · `nhap-mon-ml` 84/11/8 · `baocao-canhan` 20/1/10 · `xstk-ch3-1` 180/51/19
(cạnh / cạnh thừa / cờ duyệt).

**Cặp hai chiều: 1 → 4 trên `baocao-canhan`.** Luật cũ chỉ bắt cặp khi SCC đúng hai node; luật mới tìm toàn cục nên
ba cặp nữa lộ ra từ trong hai SCC lớn. Hệ quả: 29 cạnh thô → 20 cạnh (8 cạnh thành cờ, 1 cạnh gỡ `exact`). Cạnh bị
gỡ là `trong_dinh_nghia / ngược / 0.8` — bị gỡ vì **ngược thứ tự trình bày**, không vì confidence thấp, đúng luật mới.

## F117 🟠 — `cycle_budget = 1000` không chặn thời gian chạy

Vé 20 sinh ra để sửa chuyện "vét cạn không mở rộng được". Tôi đo nhánh **chính xác** của bản mới trên đồ thị đầy đủ
có hướng:

| n | cạnh | chu trình đơn | thời gian |
|---|---|---|---|
| 3 | 6 | 5 | 0,00 s |
| 4 | 12 | 20 | 0,00 s |
| 5 | 20 | 84 | **0,04 s** |
| 6 | 30 | 409 | **14,72 s** |

Từ 84 lên 409 chu trình, thời gian tăng **370 lần**. Ngân sách đang đặt ở **1.000** — tức nó cho phép chạy xa hơn
điểm đo 14,7 giây rất nhiều trước khi kịp bật. Ngân sách đếm **đúng đại lượng về khái niệm** (số chu trình, không
phải số tập con cạnh) nhưng **sai đại lượng về chi phí**.

Đáng chú ý: bản cũ chặn ở 16 cạnh nội bộ, tức tối đa `2¹⁶` tập con, đo được **217 ms** — tức **luật cũ chặn thời
gian chạy tốt hơn luật mới**, dù nó chặn sai thứ về mặt khái niệm.

Trên corpus hiện tại chuyện này chưa cắn: SCC lớn nhất có 3 cạnh nội bộ và 1 chu trình. Nhưng một SCC 6 node mà mọi
cặp đòi nhau không phải điều không thể xảy ra từ A8.

**Đề xuất:** giữ ngân sách theo số chu trình, **thêm một ngân sách công việc hoặc thời gian bên trong bộ giải phủ
tập hợp**, và rơi về `approximate` khi chạm. Sửa nhỏ, và làm cho lời hứa "chính xác" thành lời hứa đúng.

## F118 🟡 — guard phi chu trình không có test, và biến mất khi chạy `-O`

`assert _acyclic(learnable, kept)` là bất biến mà **toàn bộ A10 dựa vào**. Nhưng:

- Xoá nó đi **không test nào đỏ** (đột biến V8 và V13 đều lọt).
- `assert` bị **tước bỏ hoàn toàn** khi chạy `python -O`. Một lượt chạy tối ưu hoá sẽ không có guard này.

**Đề xuất:** đổi thành một phép kiểm thật có `raise`, và ghim bằng một test dựng đồ thị còn chu trình rồi kỳ vọng
nó nổ. Rẻ, và nó là bất biến quan trọng nhất mà A9 giao cho A10.

## F119 🔴 — repo đang đỏ, và không phải lỗi vé 20

`tests/unit/test_architecture.py::test_domain_only_uses_stdlib_and_specified_graph_dependency` **đỏ trong repo
thật**:

```
src\doc2roadmap\domain\roadmap.py: heapq
assert 'heapq' in {'__future__', 'collections', 'dataclasses', 'hashlib', 'itertools', 'json', ...}
```

Đây là việc vé 21 đang làm dở: `domain/roadmap.py` vừa nhập `heapq`, mà tầng domain có danh sách cho phép và
`heapq` không nằm trong đó. Cần **một quyết định tường minh** — thêm `heapq` vào danh sách cho phép vì nó là thư
viện chuẩn thuần tuý, hoặc bỏ lời nhập — chứ không để test đỏ qua đêm. Ghi ở đây để vé 21 không quên.

## Một chỗ cần theo dõi, chưa thành finding

`baocao-canhan` mất 8 cạnh vào cờ hai chiều, nên mật độ cạnh không thừa tụt **0,64 → 0,528** và tỉ lệ node cô lập
tăng **0,139 → 0,278**. Đúng ý thiết kế — những cặp ấy là nghi lỗi kiểu quan hệ. Nhưng đây là tài liệu gần cổng
nhất, và nếu cờ hai chiều nhiều lên ở tài liệu khác thì cổng sẽ là chỗ đầu tiên kêu. Vé 22 nên đưa mật độ trước/sau
khi tách cặp hai chiều vào bảng theo dõi.

## Hai quyết định của chủ dự án, ghi ngày 2026-09-22

- **Chương vàng của `doc-1`: Chương 3 — Không gian véc tơ** (tr. 44–74, 5 mục). Nếu chương cho dưới 15 hoặc trên 45
  khái niệm đích thì chỉnh phạm vi bằng cơ chế dải mục của vé 04, không đổi chương.
- **`V(2)`, `V(m)` và `𝛼𝑇` đều bị loại** — là thể hiện ký hiệu, không phải khái niệm được định nghĩa. Đã vào danh
  sách "phải loại" của điều kiện nhận vé 19.

## Phản hồi thực thi tiếp — 2026-09-22

- **F117 đã sửa:** A9 v9 thêm ngân sách 10.000 lượt gọi trong bộ giải phủ chu trình, độc lập với trần
  1.000 chu trình. Chạm một trần thì dùng `approximate`, ghi tách `work_budget_exceeded` và
  `simple_cycle_count_capped`. SCC đầy đủ 6 node/409 chu trình rơi về xấp xỉ trong 0,126 giây;
  test ép chạm ngân sách công việc đỏ trên mã v8, xanh trên v9.
- **F118 đã sửa:** kiểm DAG sau cắt chu trình dùng `raise ValueError`, không còn `assert` bị tước khi
  chạy `-O`. Test giả lập bộ giải trả thiếu cạnh chứng minh guard thực sự nổ.
- **F119 đã sửa:** `heapq` là thư viện chuẩn được thêm vào allowlist kiến trúc; suite đầy đủ xanh.
- **Vé 20–21 đã chạy thật trên bốn tài liệu cũ:** A9 v9 giao DAG không còn SCC >1; A10 v7 giảm số
  stage `naive-bayes` 16→6, `nhap-mon-ml` 43→10, `baocao-canhan` 22→5,
  `xstk-ch3-1` 63→13. Không stage nào quá 8 node, không cạnh `requires` cùng stage hoặc đi ngược;
  chạy lại A9/A10 đều `reused=true`, không tốn mô hình. Bảng cỡ chi tiết ở [vé 21](../task/a6-a8-tien-quyet/21-a10-xep-tang-co-tran-do-rong.md).
- **Vé 19 đang kiểm trên nguồn thật:** PDF `doc-1` mới đã ingest không strip, 99 section/199 chunk,
  0 watermark/email; cổng chất lượng cảnh báo đúng bản cũ nhưng không báo nhầm bản mới hay hai tài liệu
  tiếng Anh. A3 `doc-1` mới có 339 ứng viên, 333 học được, 258 lời gọi, 752.507 input + 66.250 output
  token, 0,28750175 USD. A4/A5 `doc-1` và A3 `doc-2` còn đang chạy; chưa đánh dấu vé 19/11 hoàn tất.

## Phản hồi thực thi tiếp — A1–A10 tài liệu mới, 2026-09-22

- **Vé 19, A1–A5 đã chạy xong trên ba PDF hợp lệ.** `doc-1` mới: A3 339 ứng viên/333 learnable,
  A4/A5 231 node (225 learnable), `vi`; `doc-2`: A3 v5 1.394 ứng viên/1.322 learnable,
  A4/A5 510 node (438 learnable), `en`; `doc-3`: 154 canonical node (58 learnable), `en`.
  Tổng telemetry của các artifact A3–A5 hiện hành là **2,8212405 USD** (không tính bản cũ,
  lượt lỗi, embedding và A6–A8). Bảng chi tiết ở [vé 11](../task/a6-a8-tien-quyet/11-nap-ba-tai-lieu-moi.md).
- **Tên ký hiệu trên PDF thật:** `𝐅^{m,n}`, `ℳ`, `L(V, W)`, `B(V, W)` được giữ; `3.65`,
  `3.68`, `3.94`, `6.49`, `6.54`, `i`, `0`, `V`, `C`, `F`, `R`, `{0}`, `V(2)`,
  `V(m)`, `𝛼𝑇` bị loại. PDF mã hoá hai biểu thức còn lại thành `ℒ (𝑉 , 𝑊)`/`ℒ(V, W)`
  và `𝒫 𝑛 (𝐅)`; tên ứng viên giữ nguyên nguồn theo V1. Vì điều kiện vé 19 viết đúng từng byte
  `ℒ(V,W)` và `𝒫ₙ(𝐅)`, ô ấy vẫn mở để reviewer chấp nhận tương đương hình thức, không
  âm thầm sửa tên làm đứt evidence. `ℳ` được cứu bằng tín hiệu định nghĩa xuyên chunk.
- **Lỗi provenance mới lộ trên doc-1:** node fallback `Tổ hợp tuyến tính` thiếu khóa
  `defining_chunk_ids`; `BuildProvenance` truy cập trực tiếp khiến bước A8 dừng. Test hồi quy
  đỏ trên mã cũ, sửa khởi tạo danh sách trước khi thêm quote, test và suite đầy đủ xanh.
- **Vé 11 nhịp 1:** `doc-3` qua A6–A8 ($0,0812995 cho A8), A9 v9 giao DAG 58 node,
  A10 v7 ra 8 stage. `doc-1` provenance 47 lời gọi/$0,0417175, A8 67 phiên chính +
  513 cặp phụ/$0,62448875; A9 giao DAG 225 node/337 cạnh, A10 ra 29 stage. `doc-2`
  mentions 7.050, provenance 51 lời gọi/$0,05083575; A8 đang chạy một lượt có checkpoint.
  A9/A10 `doc-2` chỉ chạy sau khi A8 kết thúc.
- **Bộ vàng hai chương đã sẵn bảng trống cho người gán:** `doc-1` Chương 3 mục 3.1–3.4
  có 45 đích sau provenance, hai bảng A1/A2 mỗi bảng 360 dòng quan hệ; `doc-2` mục 3C
  có 24 đích, hai bảng mỗi bảng 200 dòng. Chưa có nhãn người thật, nên E1/E2, hội ý và
  các kết luận dựa trên vàng chưa được nhận là hoàn tất.
- **Sự cố vận hành A8 doc-2:** Windows từ chối `os.replace` file checkpoint; khả năng cao
  trùng đúng lúc lệnh soi tiến độ đang mở file để đọc. Checkpoint chính còn nguyên; đã chạy
  tiếp từ đó và ngừng đọc file
  checkpoint trong lúc mô hình ghi. Không xoá checkpoint hoặc chạy lại từ đầu.

### Chốt lượt chạy ba tài liệu

`doc-2` A8 đã kết thúc từ checkpoint: **352 phiên chính**, **565 cặp phụ**, 821 cạnh chính +
49 cạnh phụ, 5.858.770 input + 269.927 output token, **1,869583 USD**. A9 v9 trên edge
artifact v5 giao DAG 438 node học được/864 cạnh `requires`, 602 cạnh không thừa, cổng cấu
trúc mở; A10 v7 xếp đủ 438 node thành **55 stage**, cỡ lớn nhất 8, không thiếu node.

Ba artifact A3–A8 hiện hành cộng **5,4894815 USD** telemetry; con số này không phải hoá
đơn tích luỹ mọi lượt cũ. A9/A10 của `doc-3`, `doc-1`, `doc-2` lần lượt ra 8/29/55 stage;
cả ba là DAG, qua cổng, phủ đủ 58/225/438 node học được. Phát lại
`roadmap --stop-after stages` với proxy trỏ `127.0.0.1:9` đều `reused=true` ở graph v7. Suite đầy đủ xanh,
`git diff --check` không có lỗi khoảng trắng. Vé 11, 20, 21 và phần triển khai vé 19 đã
chạy xong; **E1/E2 và các kết luận dựa trên vàng chưa thể chạy** vì hai người chưa nộp nhãn.
Điều kiện tên `ℒ(V,W)`/`𝒫ₙ(𝐅)` đúng từng byte còn chờ chủ dự án quyết định có chấp nhận
biến thể OCR tương đương nhưng giữ nguyên bằng chứng nguồn hay không.

---

# Vòng 38 — Kiểm thử vé 19, 20 (v9) và 21 · 2026-09-22

Cây làm việc sạch, mọi thứ đã commit ở `7a88104`, nên kiểm thẳng trên repo.

## Kết luận: **nhận cả ba vé.** Ba finding của vòng 37 đều đóng.

| Vòng 37 | Đã sửa thế nào | Kiểm lại |
|---|---|---|
| **F117** ngân sách không chặn thời gian | thêm `work_budget=10000` **bên trong** bộ giải, ném `_CycleWorkLimit`, ghi `work_budget_exceeded` vào artifact | ✅ SCC 6 node / 409 chu trình: **14,72 s → 0,29 s**, tự gắn nhãn `approximate`, kết quả vẫn phi chu trình |
| **F118** guard không có test, mất khi `-O` | `assert` → `if not _acyclic(...): raise ValueError(...)` | ✅ `raise` thật, không bị `-O` tước |
| **F119** repo đỏ vì `heapq` | thêm `heapq` vào danh sách cho phép của tầng domain | ✅ quyết định tường minh, có trong `test_architecture.py` |

**Suite: 466 xanh, 0 đỏ, chặn mạng.**

## Vé 19 — điều kiện nhận V1 **đạt**

`doc-2` A3 v9: tên ký hiệu bị loại giảm từ **47 lượt / 36 tên** xuống **22 lượt / 17 tên**. Và quan trọng hơn con số
là danh tính: kiểm trực tiếp trong 1.394 ứng viên, **mọi khái niệm trung tâm của mục 3C đều có mặt** —
`ℒ(V, W)`, `ℒ(𝑉, 𝑊)`, `ℒ (𝑉)`, `L(V, W)`, `𝐅^{m,n}`, `F^m,n`, `F^n`, `𝒫 (𝐅)`, `𝒫 𝑛 (𝐅)`, **`ℳ`**, `B(V, W)`,
`S ⊗ T`, `V^m`, `𝐶[-𝜋 , 𝜋]`.

17 tên còn bị loại: `i` `F` `R` `C` `V` `0` `{0}` (ký hiệu trơ) · `3.65` `3.68` `3.94` `6.49` `6.54` (số hiệu định
lý) · `V(2)` `V(m)` `𝛼𝑇` (chủ dự án đã phán) · `𝐂 4` · **`𝐅 ∞`**.

**Vé 19 — V2 cũng đạt.** `doc-1` mới qua toàn bộ A1–A5: `document_language = vi`, `language_decision = detected`,
**231/231 mô tả có dấu tiếng Việt** (trước: 37/98), `a5_rewritten_language` từ 51 xuống **2**, `a5_fallback` từ 27
xuống **1**. Mô tả đọc được: *"Tập hợp tất cả các tổ hợp tuyến tính của các véc tơ trong một tập hợp S."*

## Vé 21 — A10 đạt **tối ưu lý thuyết trên cả bảy tài liệu**

| tài liệu | node | tầng | tầng 1 | stage | stage 1 khái niệm | cỡ TB | cận dưới | đạt? |
|---|---|---|---|---|---|---|---|---|
| `baocao-canhan` | 36 | 5 | 7 | 5 | **0** | 7,2 | 5 | ✅ |
| `naive-bayes` | 34 | 6 | 7 | 6 | **0** | 5,7 | 6 | ✅ |
| `nhap-mon-ml` | 75 | 10 | 8 | 10 | **0** | 7,5 | 10 | ✅ |
| `xstk-ch3-1` | 98 | 13 | 8 | **13** | **0** | 7,5 | 13 | ✅ |
| `doc-1` | 225 | 29 | 8 | 29 | **0** | 7,8 | 29 | ✅ |
| `doc-2` | 438 | 55 | 8 | 55 | **0** | 8,0 | 55 | ✅ |
| `doc-3` | 58 | 8 | 8 | 8 | **0** | 7,2 | 8 | ✅ |

`xstk-ch3-1` đi từ **63 stage / 39 stage đơn lẻ** xuống **13 stage / 0 stage đơn lẻ**, tức đúng bằng
`max(xích dài nhất, ⌈n/8⌉)`. Không phải "nằm trong cận (2 − 2/W)" mà là **đạt cận dưới**. Và **0 cạnh tiên quyết
nào nằm gọn trong một stage** ở cả bảy — bất biến mà chủ dự án chốt được giữ tuyệt đối.

**Và bảy tài liệu giờ chạy trọn A1→A10.** Lần đầu tiên trong đợt. Chi phí cộng dồn **9,50 / 50 USD**.

## Đột biến

**Vé 20:** 11/12 bắt (vòng 37), và F118 giờ đã đóng nên phép lọt duy nhất ấy hết hiệu lực.

**Vé 21:** tôi thử 8 phép, **3 bắt, 5 lọt**. Nhưng phải nói thẳng: **hai phép là tôi nhắm hỏng, một phép quá yếu.**

- **A1** tôi sửa chuỗi `len(stages[layer]) < width` tưởng là ở bước xếp tầng, hoá ra nó nằm trong `_balance` dòng 58,
  và ở đó nó **thừa** vì đã có guard `len(stages[new]) < len(stages[old])` ngay sau. Phép đột biến vô hiệu, không
  phải lỗ hổng test.
- **A6** hạ `stage_floor` từ 3 xuống 1: đầu ra **y hệt** trên `doc-1` (29 stage, cùng phân bố cỡ). Sàn chưa bao giờ
  ràng buộc vì Coffman–Graham cộng bước cân bằng đã cho stage cỡ 5–8. Phép vô hiệu — nhưng nó phát hiện ra rằng
  **sàn hiện là mã chết trên corpus này**, nên đừng ai tưởng nó đang làm việc.
- **A5** đổi phá hoà từ số hậu duệ sang chỉ khoá stage: vẫn **không dùng thứ tự chương**, nên vẫn thoả yêu cầu của
  Đ13. Phép yếu, không phải lỗ hổng.

Còn lại **hai lỗ hổng thật**, và cả hai đúng loại mà `AGENTS.md` §5 vừa đặt tên.

## F120 ✅ — bất biến trung tâm của A10 có test trực tiếp

`_order_stages` có `raise AssertionError("cạnh requires nằm trong cùng stage")`. Thay nó bằng `pass` thì
**không test nào đỏ**.

Đây không phải guard phụ: nó **chính là định nghĩa "stage" mà chủ dự án đã chốt** — nhóm học song song được. Toàn
bộ lý do bác phương án D (τ 0,98 nhưng 34–64% cạnh nằm trong stage) nằm ở bất biến này. Mà hiện không có gì ngăn
ai đó gỡ nó.

`AGENTS.md` §5 nói đúng ca này: *"Exercise the branch that the guard claims to protect, not only the happy path"* và
*"Trace every documented invariant to a named runnable assertion"*. Cách sửa rẻ: gọi thẳng `_order_stages` với một
danh sách stage dựng tay có cạnh nội bộ, kỳ vọng nó ném.

**Đã đóng ngày 2026-09-23:** `test_stage_rejects_an_internal_requires_edge` dựng một stage chứa hai node và một
cạnh `requires` nội bộ, rồi kiểm đúng `AssertionError`. Test đi thẳng vào nhánh guard, không suy ra gián tiếp từ
đầu ra thuận.

## F121 ✅ — kiểm đầu vào `stage_cap` có test biên

Vô hiệu hoá `if type(stage_cap) is not int or stage_cap < 1` thì không gì đỏ. Việc nhỏ, ghép cùng F120.

**Đã đóng ngày 2026-09-23:** `test_stage_cap_must_be_a_positive_integer` kiểm cả `0` và `True`; ca `True` bảo vệ
riêng điều kiện kiểu vì Python coi `bool` là lớp con của `int`.

## F122 ✅ — `𝐅 ∞` được giữ, số cụ thể bị loại nhất quán

`𝐅^∞` (không gian dãy vô hạn) được định nghĩa ở mục 1B của `doc-2`. Predicate `structured_symbol` trượt nó vì nhánh
"hai phần" đòi **cả hai** phần là ký tự MATHEMATICAL, mà `∞` thì không — trong khi `𝐅 𝑛` và `𝐅 𝑆` qua được vì `𝑛`,
`𝑆` là MATHEMATICAL. Nới nhánh ấy cho phần sau là MATHEMATICAL **hoặc** `∞` là đủ.

Ghi kèm: **`𝐂 4` bị loại còn `P4(R)` và `𝒫 2(𝐑)` được giữ** — ba cái cùng dạng "đối số là con số cụ thể" nhưng ba
kết quả khác nhau. Đây là **mâu thuẫn trong danh sách điều kiện nhận của tôi**, không phải lỗi của nhân viên: tôi
xếp `P4(R)` vào vế giữ trong khi chủ dự án sau đó phán `V(2)` cùng dạng là loại. Cần một đường ranh, đề xuất:
**giữ khi số mũ/đối số là ký hiệu (`n`, `m`, `S`, `∞`), loại khi là con số cụ thể.**

**Đã đóng ngày 2026-09-23:** `structured_symbol` chấp nhận `∞` ở phần ký hiệu thứ hai và loại tên có chữ số cụ
thể trước các nhánh cấu trúc. Test A3 giữ `𝐅 ∞`, đồng thời loại `𝐂 4`, `P4(R)` và `𝒫 2(𝐑)`; các ca ký hiệu
`𝐅^{m,n}`, `F^n`, `𝒫ₙ(𝐅)` vẫn được giữ. `algorithm_id` tăng thành `a3-section-conversation-v10` để artifact cũ
không bị tái dùng nhầm. Lượt sửa nhỏ này không gọi mô hình; artifact `doc-2/candidates/v5` vẫn ghi trung thực A3
v9 và sẽ chỉ được thay khi chủ động chạy lại A3. Suite đầy đủ: **469 test xanh**.

## Một chỗ cần nói lại cho đúng

Vé 20 ghi "gỡ chu trình bằng nghiệm **chính xác** ở mọi cỡ". Sau khi thêm `work_budget`, ranh giới thật là: nhánh
chính xác chạy tới khoảng **80–90 chu trình đơn**, trên đó rơi sang xấp xỉ. Ví dụ đo được: SCC 7 node / 22 cạnh /
79 chu trình → `exact`; 10 node / 27 cạnh / 99 chu trình → `approximate`.

Đây **không phải lỗi** — artifact ghi trung thực `method` và `work_budget_exceeded`, và trên corpus thật SCC lớn
nhất chỉ có 1 chu trình nên luôn `exact`. Nhưng câu chữ trong vé và trong báo cáo phải nói "chính xác trong ngân
sách, xấp xỉ có ghi nhãn ngoài ngân sách", không nói "chính xác ở mọi cỡ".

## Số đo quan trọng nhất của vòng này

τ so thứ tự giáo trình, **sau khi Đ13 gỡ bỏ phá hoà theo thứ tự chương**:

| `baocao-canhan` | `naive-bayes` | `nhap-mon-ml` | `xstk-ch3-1` | `doc-1` | `doc-2` | `doc-3` |
|---|---|---|---|---|---|---|
| 0,01 | **−0,09** | 0,17 | 0,18 | 0,09 | 0,12 | **−0,02** |

Trước đây τ dao động 0,02–0,53, nhưng con số ấy **nhiễm đối chứng** vì thứ tự chương vừa dùng để phá hoà vừa dùng
để chấm. Giờ đã sạch, và câu trả lời thật là: **thứ tự lộ trình gần như không tương quan với thứ tự giáo trình**,
hai tài liệu còn âm nhẹ.

Đây **không phải lỗi của vé 21** — vé 21 làm đúng thứ được giao, và chính việc sửa Đ13 mới làm con số trở nên
trung thực. Nhưng nó đặt câu hỏi khoa học trung tâm của cả đợt lên bàn: **đồ thị sai, hay thứ tự sách không liên
quan tới tiên quyết?** Chỉ bộ vàng trả lời được, và vé 22 là dụng cụ đo.

---

# Vòng 39 — Vé 22 và phép đo đầu tiên của lộ trình trên bộ vàng thật · 2026-09-23

Vé 22 xong: hai chỉ số, lệnh `a8-roadmap-score`, 7 test mới với **7/7 đột biến bị bắt**, suite **477 xanh** khi
chặn mạng. Nhưng thứ đáng nói không phải là mã, mà là con số nó đo ra.

## Lộ trình vi phạm 15–26% cạnh vàng

Chấm lộ trình thật (`doc-1/v7`, `doc-2/v7`) trên bộ vàng đã gán, lấy **giao nhãn** của hai người:

| | stage | τ so mục lục | cạnh vàng | tôn trọng | **vi phạm** | cùng stage | ngoài phạm vi |
|---|---|---|---|---|---|---|---|
| `doc-1` Chương 3 | 29 | +0,087 | 23 | 17 | **6 (26,1%)** | 0 | 0 |
| `doc-2` mục 3C | 55 | +0,125 | 46 | 39 | **7 (15,2%)** | 0 | 0 |

Trên **hợp nhãn**: 12/49 (24,5%) và 13/66 (19,7%). Đây là phép chấm đúng/sai đầu tiên của lộ trình, và nó là con
số thật chứ không còn là suy đoán.

## Và nguyên nhân không nằm ở A10

Với mỗi cạnh vàng bị xếp ngược, tôi tra xem đồ thị máy **có cạnh ấy không**:

| | cạnh bị xếp ngược | máy có cạnh trực tiếp | máy chỉ có đường bắc cầu | **máy không có gì** |
|---|---|---|---|---|
| `doc-1` | 6 | 0 | 0 | **6** |
| `doc-2` | 7 | 0 | 0 | **7** |

**13 trên 13.** Không một ca vi phạm nào là do A10 xếp sai một cạnh nó biết — **mọi ca đều là cạnh A8 không tìm ra**.
Nói cách khác: **A10 tôn trọng 100% số cạnh tiên quyết được giao cho nó.** Trần chất lượng của lộ trình do **recall
của A8** đặt ra, không do thuật toán xếp tầng.

Recall thô của A8 trên giao nhãn: **16/23 = 70%** (`doc-1`), **25/46 = 54%** (`doc-2`).

Các ca vi phạm đọc rất rõ, và đều cùng một hình dạng — **khái niệm nền rơi xuống cuối**:

- `doc-1`: cần *Vô hướng* (stage 12) và *Véc tơ* (stage 14) trước *Tổ hợp tuyến tính*, nhưng máy đặt *Tổ hợp tuyến
  tính* ở **stage 0**. Nó thành gốc vì không có cạnh nào đi vào nó.
- `doc-2`: cần *Matrix addition* (stage 54) trước *additive identity of 𝐅^{m,n}* (stage 25) và trước *dim 𝐅^{m,n} =
  mn* (stage 45). Phép cộng ma trận nằm ở stage 54 trên 55 là sai rõ ràng.

## Điều này đổi thứ tự ưu tiên của cả đợt

Vòng 36 đặt câu hỏi: **đồ thị sai, hay thứ tự sách không liên quan tới tiên quyết?** Giờ có câu trả lời, và nó là
vế thứ nhất — nhưng sai ở **A8 thiếu cạnh**, không phải ở A9 hay A10.

Hệ quả cho kế hoạch:

1. **Vé 21 đúng nhưng không phải nút thắt.** Nó sửa hình dạng lộ trình (63 → 13 stage, hết stage đơn lẻ) và đạt tối
   ưu lý thuyết. Nhưng hình dạng đẹp trên một đồ thị thiếu 30–46% cạnh vẫn cho lộ trình sai 15–26%.
2. **τ gần bằng 0 giờ giải thích được.** Nó không phải bằng chứng A10 hỏng, cũng không phải bằng chứng sách sắp
   xếp kém — nó là **bóng của recall thấp**: thiếu cạnh thì nhiều khái niệm thành gốc, và thứ tự trôi tự do.
3. **Việc đáng làm tiếp là nâng recall của A8**, không phải tinh chỉnh A10. E2 (bộ sinh cặp) và E6 (trích mở so
   kiểm cặp) là hai thí nghiệm đã thiết kế sẵn để trả lời *cạnh bị mất ở đâu* — chúng vừa chuyển từ "nên chạy"
   sang "phải chạy trước".
4. **Một phép chẩn đoán rẻ nên làm ngay ở vé 13:** với mỗi cạnh vàng máy không tìm ra, tra xem nó thuộc loại vị
   trí nào trong sáu loại của E1. Nếu cạnh mất tập trung ở một loại — ví dụ xuyên chương, hay nối qua một lần
   nhắc tên — thì biết ngay phải sửa bộ sinh nào.

## Về hai chỉ số

τ và tỉ lệ vi phạm **không thay thế nhau**. τ đo lệch mục lục và là **dấu hiệu chẩn đoán** — thứ tự sách không phải
chân lý về tiên quyết, nên τ thấp tự nó không kết tội ai. Tỉ lệ vi phạm cạnh vàng mới là phép chấm đúng/sai. Lệnh
trả cả hai, kèm cảnh báo *single reference* của Lapata 2006 ngay trong báo cáo JSON để không ai trích τ trần trụi.

Bốn rổ của tỉ lệ vi phạm không chồng nhau — tôn trọng, vi phạm, **cùng stage**, **ngoài phạm vi** — và tỉ lệ chỉ
tính trên cặp thật sự được xếp thứ tự. Rổ "cùng stage" tồn tại vì với định nghĩa stage mà chủ dự án chốt, một cặp
tiên quyết nằm chung stage **không phải** tôn trọng: lộ trình không xếp thứ tự cho nó. Trên hai chương thật rổ ấy
bằng 0, đúng như bất biến của vé 21 hứa.
