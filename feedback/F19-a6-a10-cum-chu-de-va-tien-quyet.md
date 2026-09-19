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
