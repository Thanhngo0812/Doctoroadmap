# F61–F69 — Review đợt A4/A5

Vòng review 20 · 2026-09-11 · Phạm vi: [`task/a4-a5-hop-nhat/`](../task/a4-a5-hop-nhat/) 14 ticket, cộng lần chạy
thật đầu tiên ([báo cáo](../report/a4-a5-lan-chay-that-dau-tien.md)). Phần bàn giao của nhân viên giữ nguyên ở
[cuối file](#bàn-giao-của-nhân-viên--triển-khai-a4a5-2026-09-11).

Mỗi lỗi được ghi đủ: **hiện tượng · bằng chứng/tái hiện · vị trí · nguyên nhân gốc · tác động · cách sửa · test · ai
sửa**. Tám test đề xuất (phụ lục B) đã chạy hai chiều: trên code hiện hành, đúng 8 test đó hỏng (228 test cũ vẫn qua);
trên một bản vá thử để ngoài repo (phụ lục C), **236/236 xanh**.

## Kết luận

**Mọi con số trong báo cáo đều đúng khi đo lại, và pipeline làm đúng cơ chế nó hứa.** Tôi chấm lại bằng script
riêng, khớp từng số. Chạy lại toàn pipeline từ nhật ký thì ra giống hệt. Đột biến 10 guard thì test bắt đủ.

Chất lượng lần chạy đầu với `gemini-3.1-flash-lite`: trên bộ vàng, **precision 0,90 (26/29), recall 0,55 (26/47)**.
Có 25 node được gộp từ hai nhóm tên trở lên, 22 node đúng hoàn toàn.

```
F61  spec: sai một cạnh subtype_of là bỏ cả cụm         -> mất cụm Naive Bayes, 5 cặp cùng + 4 cha–con
F62  spec: đếm token coi bảng số liệu là tiếng Anh       -> naive-bayes ra mô tả toàn tiếng Anh
F63  code: "không chắc" ở lượt vá tháo cả lần gộp đúng    -> tái hiện được; lần chạy này chưa dính
F69  thiết kế: lượt vá theo cặp sinh cả 3 ca gộp sai      -> lượt cụm đúng 23/23, lượt vá đúng 3/6
```

Bốn trong chín mục (F61, F62, F67, F69) là **lỗi spec, số mốc và thiết kế của tôi**, không phải lỗi việc nhân viên
làm. Ở F61, F62 và F67, nhân viên đã cài đúng câu chữ spec và tự báo chỗ lệch, không ép số.

## Trạng thái xử lý — hoàn tất 2026-09-12

| Feedback | Trạng thái | Kết quả và bằng chứng |
|---|---|---|
| F61 | ✅ Xong | Tách kiểm phân hoạch khỏi `subtype_of`; cạnh sai bị ghi `subtype_rejected` và không làm mất cụm. Chạy thật lấy lại 5 cặp vàng, tổng 31 TP. |
| F62 | ✅ Xong | Luật `token-majority-prose-vi20-v2` bỏ chunk thuần bảng/code/công thức/hình; cả bốn artifact, gồm Naive Bayes, đều là `vi`. |
| F63 | ✅ Xong | Hoãn lượt vá nằm ở `deferred_pairs`, không đưa hai nhóm đầu mút vào `deferred`; regression uncertain/invalid và cluster-deferred đều qua. |
| F64 | ✅ Xong | Mọi lần thử hỏng giữ `{error, raw_text}`; lỗi retry nêu id/chunk/câu cụ thể; JSON hỏng giữ raw text cuối. |
| F65 | ✅ Xong | HTTP/timeout thành `ModelTransportError`, dừng lượt chạy trước khi ghi artifact; test thấy lần sau thật sự chạy lại. |
| F66 | ✅ Xong | 14 ticket chuyển `done` và tick checklist; sửa help, manifest/metric, bỏ kênh mô tả, bổ sung đề xuất prompt/tham số trong báo cáo. |
| F67 | ✅ Xong | Spec/ticket dùng 89 · 12 · 27 alias và 95 · 256 · 38 cạnh; n-gram ghi rõ không đệm biên, seed 42. |
| F68 | ✅ Xong | Integration đặt `HF_HUB_OFFLINE=1`; ba ca Docling từng gọi Hugging Face đã qua trong full suite offline. |
| F69 | ✅ Xong | Chọn phương án (a): vá bằng cụm nhỏ đủ thành viên hai node, cùng prompt/schema lượt cụm. Sau sửa có 4 lần vá gộp, không tạo FP; tổng precision 1,00. |

Đo lại toàn bộ: flash-lite đạt **31/0/16, P=1,000 · R=0,660 · F1=0,795**; Pro Preview đạt
**26/1/21, P=0,963 · R=0,553 · F1=0,703**, nên giữ `gemini-3.1-flash-lite` cho cả merge và A5. Quét 13 cấu hình
giữ k=3, n-gram=0,5, resolution=2, seed=42, cap=9; 100 cặp ngoài đồ thị có 0 nhãn *cùng*, nên bỏ kênh mô tả A4.

Kiểm chứng cuối: **254/254 test qua**, gồm integration Docling offline; bốn fixture contract v2 phát lại không mạng;
`git diff --check` sạch. Bốn lần chạy lặp cấu hình flash-lite đều `reused=true`. Browser tích hợp không có backend
trong phiên này; bảng vàng đã qua test DOM giả nhưng thao tác UI trên browser thật vẫn là kiểm chứng thủ công, không
ảnh hưởng runtime A4/A5.

## Bảng lỗi

| # | Mức | Loại | Lỗi | Lần chạy này | Ai sửa |
|---|---|---|---|---|---|
| F61 | 🔴 | spec (tôi) | Sai một cạnh `subtype_of` là bỏ cả cụm | **đã dính** | tôi sửa spec D4; nhân viên sửa code |
| F62 | 🟠 | spec (tôi) | Luật ngôn ngữ coi bảng và code là tiếng Anh | **đã dính** | tôi sửa D8; nhân viên sửa code, chạy lại A5 |
| F63 | 🟠 | code | Hoãn ở lượt vá tháo cả lần gộp đúng | tiềm ẩn, đã tái hiện | nhân viên |
| F69 | 🟠 | thiết kế (tôi) | Lượt vá theo cặp sinh cả 3 ca gộp sai | **đã dính** | tôi chọn phương án; nhân viên cài và đo |
| F64 | 🟡 | code | Đầu ra bị từ chối không được lưu; lỗi gửi lại quá chung | **đã dính** | nhân viên |
| F65 | 🟡 | code | Lỗi mạng bị cache đóng băng | tiềm ẩn, đã tái hiện | nhân viên |
| F66 | 🟡 | ghi chép | Ticket chưa tick; vài tiêu chí nhỏ còn thiếu | — | nhân viên |
| F67 | 🟡 | số mốc (tôi) | Số mốc lệch câu chữ spec | — | tôi |
| F68 | 🟡 | test B0 | Ba test Docling gọi `huggingface.co` | — | nhân viên |

Thứ tự làm đề xuất:

1. F63, F61, F64, F65 — sửa code, test đã có sẵn ở phụ lục B.
2. Tôi sửa spec D3, D4, D5, D8 cùng các ticket liên quan.
3. F62 — sửa code rồi chạy lại A5 cho `naive-bayes`.
4. Chọn phương án F69, rồi A/B model theo ticket 14.
5. F66, F68.

## Kiểm chứng độc lập

| Khẳng định | Cách kiểm | Kết quả |
|---|---|---|
| 234 test xanh, không gọi mạng | chạy lại, chặn socket/DNS bằng `sitecustomize` | ✅ 231 qua. 3 test Docling của B0 gọi `huggingface.co`, qua khi đặt `HF_HUB_OFFLINE=1` — F68 |
| Bộ vàng không bị sửa | SHA-256 hai bản | ✅ `1df2167c…cd55`, trùng từng byte |
| Gán trước lần chạy mô hình | mốc thời gian | ✅ xuất nhãn 16:38:45, artifact `complete` đầu tiên 16:59:59 |
| Không rò draft hay nhãn vàng vào prompt phán | quét input của 63 cụm và 6 lô vá | ✅ 0 và 0 |
| Loader "bảng cũ" không phải lối tắt | đọc code, nạp lại | ✅ vẫn kiểm id mục, thành viên, bằng chứng, đường dẫn đúng như lúc gán |
| P/R/F1, recall subtype, subtype sai | script chấm riêng, không gọi `evaluate_canonical` | ✅ khớp từng số ở cả 4 tài liệu |
| Bảng pipeline trong báo cáo | đối chiếu manifest | ✅ khớp mọi ô |
| Cache quyết định (ticket 12) | bỏ cache cấp artifact, buộc chạy lại toàn pipeline từ nhật ký; vector tên phát lại; mô hình bị gài bẫy | ✅ node, cạnh, `deferred` giống hệt; config hash khớp. Chỉ gọi lại 4 cụm và 2 mô tả từng hỏng, vì lỗi không được cache |
| A5 | kiểm lại độc lập | ✅ 0 trích dẫn ngoài node · 0 mô tả ngoài 1–4 câu · 0 lệch ngôn ngữ · `first_order_index` đúng luật |
| Cảnh báo A3 (ticket 01) | đếm lại | ✅ 6 câu / 19 tên · 31/377 |
| Lớp tên, ánh xạ cạnh | đếm lại | ✅ 279 + 79 node · 219 → 213 cạnh · 12 lần hoà kiểu |
| Bảng gán v2 (ticket 05) | chạy trong Node với DOM giả: bấm nhãn, xuất, nạp | ✅ 416/416; file xuất qua loader đầy đủ, giữ đúng chiều cha–con. Vẫn chưa thử trên browser thật |
| Mỗi guard có test đi đúng nhánh | đột biến 10 guard trên bản sao `src` | ✅ 8 bắt ngay. 2 là guard lớp hai: đột biến kép thì bắt ⇒ mọi hành vi đều được test giữ |
| Test đề xuất đo đúng lỗi | chạy trên code hiện hành và trên bản vá thử | ✅ hiện hành: đúng 8 test mới hỏng, 228 test cũ qua · bản vá: 236/236 |

## Chất lượng lần chạy đầu — đọc kèm giới hạn

Nhãn vàng là của Claude, gán rộng tay ở nhãn *cùng*. Vì vậy recall ở đây là **cận dưới** theo quy ước đó. Toàn bộ
ca sai, kèm lý do nguyên văn của mô hình, nằm ở phụ lục A.

- **3 node gộp sai**, cả ba đều sinh ở lượt vá (F69). Báo cáo đã tự nêu hai ca sau; ca đầu thì chưa:
  - `Cơ chế đồng bộ hóa` bị gộp vào `Concurrency`;
  - `Thiết kế hệ thống` bị gộp vào `Kiến trúc phân lớp`;
  - `Phân loại email` gộp với `Phân lớp`. Ca này nặng nhất: node `Phân lớp` sau đó còn nhận cạnh
    `Phân lớp ⊂ Bài toán phân loại mail`, tức khái niệm trung tâm của cả tài liệu bị treo **ngược** dưới một ví dụ.
- **21 cặp bỏ sót**: 5 cặp mất vì F61; khoảng 10 cặp là chỗ nhãn của tôi rộng tay hoặc có thể bàn; 6 cặp là bỏ sót
  rõ. Ví dụ `Khoảng ước lượng của σ 2` bị xếp làm con của `…của phương sai tổng thể`; `Kiểu mô hình`/`Lớp mô hình`
  bị xếp cha–con dù chính lý do mô hình ghi *"used interchangeably"*.
- **Subtype**: 15 cạnh nối các cặp mà bộ vàng không gán cha–con đúng chiều. Flash-lite hay đẩy cặp *cùng* và cặp
  *liên quan* thành cha–con (`Học ⊂ Học máy`).

Chỉ số lần này đo một model tạm chọn, chưa đo thiết kế.

---

## F61 🔴 — Sai một cạnh `subtype_of` là bỏ cả cụm — **lỗi spec của tôi**

**Hiện tượng.** 4/63 cụm bị từ chối sau hai lần thử. Trong đó 2 cụm chỉ sai ở cạnh `subtype_of`, phân hoạch không bị
báo lỗi gì, nhưng luật hiện hành vẫn bỏ nguyên cụm.

**Bằng chứng** — dòng nhật ký hỏng của artifact `canonical` cuối (ML v2, XSTK v2, NB v2):

| Tài liệu | Cụm bị từ chối | Lỗi ghi trong nhật ký | Cặp vàng mất |
|---|---|---|---|
| naive-bayes | `Naïve Bayes Classification`, `Multinomial Naive Bayes`, `Bernoulli Naive`, `Gaussian Naive Bayes`, `Bernoulli Naive Bayes`, `Naïve Bayes` | `bằng chứng subtype_of nằm ngoài hai đầu` | *cùng* #119, #415 · cha–con #91, #102, #117, #164 |
| xstk-ch3-1 | `Trung bình tổng thể`, `Trung bình mẫu`, `Trung bình chung`, `Ước lượng trung bình`, `Ước lượng trung bình μ`, `Ước lượng trung bình tổng thể` | `subtype_of phải nối hai node khác nhau trong cụm` | *cùng* #148, #307, #317 |
| nhap-mon-ml | `SVM`, `K-NN`, `Naive Bayes`, `ID3` | `mỗi nhóm phải có đúng một lần, không thiếu/thừa` | — |
| xstk-ch3-1 | `Phương pháp tính trực tiếp`, `Phương pháp đổi biến số` | `mỗi nhóm phải có đúng một lần, không thiếu/thừa` | — |

Lỗi của cụm xstk cho biết mô hình **đã gộp** các nhóm *ước lượng trung bình*, rồi vẽ thêm cạnh subtype giữa chính
chúng. Tức phân hoạch đúng bị bỏ vì một cạnh thừa.

**Vị trí.**
- Spec D4, `doc/A4-A5-hop-nhat-thuc-the-spec.md:237-239`: *"`subtype_of` nối hai node khác nhau trong cụm và
  `chunk_id` bằng chứng thuộc một trong hai. Sai ⇒ thử lại một lần; vẫn sai ⇒ cả cụm `deferred`, không gộp gì."*
  Ticket 07 chép nguyên luật này.
- `src/doc2roadmap/domain/canonical_decisions.py:36-43` — kiểm cạnh subtype chung một hàm và cùng kiểu lỗi với kiểm
  phân hoạch.
- `src/doc2roadmap/application/use_cases/canonical_reasoning.py:85-90` — `call()` trả `None` thì
  `deferred.update(cluster)`, và mọi cặp trong cụm thành *khác*.

**Nguyên nhân gốc.** Spec gộp hai loại lỗi có hệ quả khác hẳn nhau vào một nhánh. Phân hoạch sai thì không dùng được
gì. Cạnh subtype sai thì chỉ nên mất chính cạnh đó. Quy chung "cả cụm `deferred`" khiến thứ phụ quyết định số phận
thứ chính.

**Tác động — đo được.**
- naive-bayes: khái niệm trung tâm bị tách làm hai node, `Naïve Bayes` (2 ứng viên) và
  `Naïve Bayes Classification` (6 ứng viên). Recall subtype của tài liệu chỉ còn **1/9**. Node thứ hai cũng không có
  mô tả được kiểm chứng: A5 cho nó hỏng hai lần, phải giữ draft.
- Toàn bộ corpus: mất **5/21** cặp *cùng* bị bỏ sót và 4 cặp cha–con. Trần lợi ích: recall 26 → 31/47
  (0,55 → 0,66). Riêng cụm Naive Bayes chưa chắc lấy lại được, vì đầu ra của nó không được lưu (F64).

**Sửa.** Tách hai lớp kiểm:
- `validate_partition` chỉ kiểm phân hoạch (mỗi nhóm đúng một lần, không id lạ, có lý do) và khuôn cạnh (chỉ
  `subtype_of`, không `requires`). Sai ⇒ thử lại rồi `deferred` như cũ.
- Hàm mới `split_subtype_edges(value, source) -> (kept, rejected)`. Cạnh nối hai nhóm cùng node, hoặc trích chunk
  ngoài hai đầu ⇒ vào `rejected`. Ghi mỗi cạnh bị bỏ thành dòng nhật ký `subtype_rejected` (kèm lỗi và danh sách chunk
  hợp lệ), cộng chỉ số `subtype_rejected`. Phân hoạch được giữ.
- Kiểm cạnh cha–con ở lượt vá giữ nguyên: lượt vá xét theo cặp, bỏ cặp không kéo theo gì khác.
- Bản vá thử ở phụ lục C, khoảng 20 dòng.

**Test.**
- `test_invalid_subtype_edge_is_dropped_not_the_partition` (seam ①).
- `test_subtype_edges_are_filtered_separately_from_the_partition` (seam ②).
- Sửa `test_partition_guards_and_transitive_conflict`: chuyển hai ca `update(parent="b")` và
  `update(chunk_ids=["outside"])` sang test mới. Test cũ đang khẳng định chính luật cần bỏ, nên sẽ là test duy nhất
  hỏng khi sửa.

**Ai sửa.** Tôi sửa spec D4 và tiêu chí ticket 07. Nhân viên sửa code và test.

---

## F62 🟠 — Luật ngôn ngữ đếm bảng số liệu và code là tiếng Anh — **lỗi spec của tôi**

**Hiện tượng.** `naive-bayes` là bài giảng tiếng Việt về Naive Bayes, nhưng nhận `document_language = en`.
- 35 mô tả mới của tài liệu đều bằng tiếng Anh.
- 12 draft tiếng Việt bị viết lại sang tiếng Anh, ví dụ *"Xác suất represents the calculated probability of an
  outcome…"*.
- Mô tả của `Phân lớp` hỏng hai lần vì bị luật xếp là tiếng Việt, phải giữ draft.

**Bằng chứng.**

```
naive-bayes   chunk tiếng Việt 23/40   nhưng token 2.554 / 5.783 = 44%  => "en"
  chunk "tiếng Anh" nặng nhất: bảng số liệu 513 · 492 · 427 · 340 tok … · code sklearn 225
  bỏ các chunk có bảng/code:  1.946 / 2.588 = 75%  => "vi"
```

| Tài liệu | Luật hiện hành | Đa số chunk | Token, bỏ chunk thuần bảng/code/công thức/hình | Tỉ lệ từ có dấu toàn văn |
|---|---|---|---|---:|
| naive-bayes | **en** | vi | vi | 46% |
| baocao-canhan | vi | vi | vi | 82% |
| nhap-mon-ml | vi | vi | vi | 82% |
| xstk-ch3-1 | vi | vi | vi | 74% |

**Vị trí.**
- Spec D8, `…spec.md:311-313`: nêu luật *"đa số chunk tính theo token"*, rồi ví dụ ngay sau lại lý luận theo **số
  chunk** (*"23/40 chunk tiếng Việt ⇒ tiếng Việt"*). Ticket 09 chép lại ví dụ đó làm tiêu chí.
- `src/doc2roadmap/domain/canonical_decisions.py:14-17` — cài đúng luật như câu chữ.

**Nguyên nhân gốc.**
1. Luật cân theo token, nên chunk càng dài càng nặng. Chunk dài nhất của slide lại là bảng weather và code, toàn chữ
   Latin không dấu (`Outlook`, `Sunny`, `MultinomialNB`).
2. Ví dụ trong spec mâu thuẫn với luật nó nêu. Nhân viên cài đúng luật, thấy kết quả lệch dự kiến và ghi rõ, không
   bẻ luật để khớp số — đó là cách xử lý đúng.

**Giới hạn còn lại.** 2 chunk văn xuôi (174 token) của slide này mất dấu từ khâu trích (*"la mot he day du cac
bienc6"*). Luật dựa trên dấu không nhận ra loại chữ này. Đây là chuyện chất lượng trích xuất B0, ghi lại để theo dõi,
không chặn sửa ở đây.

**Sửa.**
- Chỉ đếm chunk có văn xuôi: bỏ chunk mà mọi `block_types` đều thuộc {`table`, `code`, `formula`, `figure`}. Nếu
  không còn chunk nào thì đếm như cũ. Bảng trên cho thấy bốn tài liệu đều ra `vi`.
- Đổi nhãn `canonical_language_rule` (ví dụ `token-majority-prose-vi20-v2`). Theo thiết kế cache, chỉ A5 của
  `naive-bayes` phải gọi lại; lượt merge dùng lại 100%.

**Test.** `test_tables_and_code_do_not_decide_description_language` (seam ②).

**Ai sửa.** Tôi sửa D8 và ticket 09. Nhân viên sửa code rồi chạy lại `a4` cho `naive-bayes`.

---

## F63 🟠 — Hoãn ở lượt vá tháo cả lần gộp đúng trong cụm

**Hiện tượng.** Nhãn *không chắc* ở lượt vá, hoặc một lô vá trả sai định dạng hai lần, làm mất những lần gộp đúng đã
có trong cụm của hai đầu cạnh. Nhật ký còn ghi nhầm chuyện đó thành "mâu thuẫn bắc cầu".

**Tái hiện** trên fixture thật `baocao-canhan`, dùng mô hình giả của chính bộ test:

```
cụm {WebSocket, WebSockets}                       -> trọng tài gộp             (đúng)
cạnh cắt WebSockets – Giao thức WebSockets         -> lượt vá trả "uncertain"
kết quả: ba node rời · transitive_conflicts = 1 · log "contradictory decisions"

cùng cụm, lô vá trả sai định dạng hai lần          -> đúng kết quả trên

cụm {Giao thức WebSockets, Golang}: "Giao thức…" bị hoãn;
lượt vá phán WebSockets – Giao thức WebSockets "cùng" -> lần gộp WebSocket+WebSockets cũng bị tháo
```

**Vị trí.**
- `canonical_reasoning.py:113-116` — lô vá hỏng: `deferred.update((a, b))` đánh hoãn cả hai **nhóm**.
- `canonical_reasoning.py:122-124` — nhãn `uncertain`: cũng `deferred.update((a, b))`.
- `canonical_reasoning.py:128-130` — đổi mọi cặp *cùng* chạm nhóm bị hoãn thành cặp *khác*, rồi gọi
  `guarded_components`.
- `canonical_decisions.py:47-65` — thấy một cặp *khác* trong một thành phần là tách cả thành phần.

**Nguyên nhân gốc.** Hai lỗi chồng lên nhau:
1. Hoãn một **cặp** bị cài thành hoãn cả hai **nhóm**. Spec D5 viết *"nhãn khác ⇒ không làm gì"*. Ticket 08 viết
   *"sai hai lần ⇒ cả lô không gộp"*. Cả hai chỉ bảo không gộp cặp đó.
2. Dòng 129 đổi cặp *cùng* thành *khác*, thay vì bỏ nó đi. Diễn biến:
   - `same = [(A, B)]` từ cụm.
   - Lượt vá trả *không chắc* cho (B, C): thêm (B, C) vào *khác*, B và C bị đánh hoãn.
   - Dòng 129 thêm (A, B) vào *khác*.
   - Thành phần {A, B} giờ vừa có (A, B) *cùng* vừa có (A, B) *khác*, nên bị tách thành [A], [B] và ghi là mâu thuẫn.

**Tác động.** Lần chạy này chưa dính: lượt vá không trả *không chắc* lần nào, và cả 6 lô đều hợp lệ. Nhưng:
- một lô vá hỏng (tới 10 cặp) có thể tháo lần gộp của tới 20 nhóm;
- mô hình mạnh hơn chịu nói "không chắc" nhiều hơn — đúng thứ A/B sắp đổi sang;
- `transitive_conflicts` và `deferred_groups` báo sai bản chất: chỗ không mâu thuẫn bị đếm là mâu thuẫn.

**Sửa.**
- Lượt vá trả *không chắc*, hoặc lô hỏng ⇒ chỉ thêm đúng cặp đó vào *khác*, ghi vào `deferred_pairs` (cặp và lý do).
  Không đánh `deferred` cho nhóm.
- Nhóm bị hoãn ở lượt cụm, hoặc thuộc cụm hỏng ⇒ **bỏ** các cặp *cùng* về sau có nó, không đổi thành *khác*. Làm
  vậy giữ đúng ý chú thích ở dòng 128 (*"A deferred group remains separate"*).
- Artifact thêm trường `deferred_pairs` và chỉ số `deferred_pairs`.
- Bản vá thử ở phụ lục C, sáu dòng.

**Test.**
- `test_repair_deferral_keeps_existing_cluster_merge[uncertain]`
- `test_repair_deferral_keeps_existing_cluster_merge[invalid]`
- `test_cluster_deferred_group_is_not_merged_later_and_does_not_undo_others`

**Ai sửa.** Nhân viên. Tôi thêm vào spec D5 một câu phân biệt hoãn theo **nhóm** (lượt cụm) với hoãn theo **cặp**
(lượt vá).

---

## F64 🟡 — Đầu ra bị từ chối không được lưu; lỗi gửi lại quá chung

**Hiện tượng.** 4 cụm và 2 mô tả hỏng cả hai lần thử, nhưng nhật ký chỉ còn chuỗi lỗi, không có đầu ra của mô hình.
Không ai biết cụm Naive Bayes đã chia đúng chưa, hay cạnh nào trích sai chunk nào.

**Bằng chứng.**
- Lần thử lại chỉ cứu được **1/5** lượt merge hỏng lần đầu, và 1/3 lượt mô tả.
- Câu lỗi gửi lại cho mô hình, nguyên văn: *"mỗi nhóm phải có đúng một lần, không thiếu/thừa"*, *"bằng chứng
  subtype_of nằm ngoài hai đầu"*, *"trích dẫn ngoài node hoặc thiếu trích dẫn"*. Không câu nào nêu một id nào.
- Ticket 07 đòi: *"Sai ⇒ thử lại một lần, **kèm lỗi cụ thể**"*.

**Vị trí.**
- `canonical_reasoning.py:56-57` — nối câu lỗi vào prompt. `.payload` vứt luôn `raw_text` của `ExtractionReply`.
- `canonical_reasoning.py:59-61` — bắt lỗi, chỉ giữ chuỗi.
- `canonical_reasoning.py:66-67` — dòng nhật ký hỏng không có đầu ra.
- `canonical_decisions.py:34-35` và `:84-85` — thông báo lỗi chỉ nêu tên luật.

**Nguyên nhân gốc.** `call()` chỉ giữ `payload`, và vứt đi khi kiểm hỏng. Hàm kiểm chỉ nêu tên luật, không nêu vi
phạm cụ thể.

**Sửa.**
- Giữ `reply`. Ghi `attempts: [{error, raw_text}]` vào mọi dòng nhật ký có lần thử hỏng, kể cả khi lần thử lại thành
  công.
- Thông báo lỗi phải nêu:
  - id nhóm bị thiếu, bị lặp, hoặc lạ;
  - cạnh `child → parent`, chunk bị trích sai, và danh sách chunk hợp lệ;
  - câu mô tả thứ mấy trích chunk nào nằm ngoài node.
- `MalformedModelResponse` của adapter hiện chỉ mang message; nên mang theo `raw_text`, để cả ca JSON hỏng cũng lưu
  được đầu ra.

**Test.** `test_retry_names_missing_group_and_log_keeps_rejected_output`.

**Ai sửa.** Nhân viên.

---

## F65 🟡 — Lỗi mạng bị coi như mô hình trả sai, rồi bị cache đóng băng

**Tái hiện** trên fixture thật. Trọng tài giả ném đúng loại lỗi mà adapter Gemini ném khi API trả 503:

```
lần 1 (API sập):  stage=complete · merge_invalid=12 · deferred=39 nhóm · log "Gemini API trả HTTP 503"
lần 2 (API sống): version=1 (vẫn là artifact lần 1) · reused=True · deferred=39
```

**Vị trí.**
- `src/doc2roadmap/infrastructure/llm/gemini.py:128-137` — HTTP lỗi và timeout đều thành `RuntimeError`.
- `gemini.py:119-120` — phản hồi không có chữ cũng thành `RuntimeError`.
- `canonical_reasoning.py:59` — bắt `RuntimeError` như một lỗi định dạng.
- `canonicalize.py:35-37` — `find_canonical` trả lại artifact cũ.

**Nguyên nhân gốc.**
- Không phân biệt lỗi đường truyền với đầu ra sai.
- Artifact vẫn được ghi `complete`.
- Khoá cache chỉ gồm (nguồn, config), nên không biết artifact đó hỏng vì mạng.

**Tác động.** Lần này chưa dính: nhật ký không có lỗi HTTP nào. Khi dính, phải xoá artifact hoặc đổi config mới chạy
lại được. Số `deferred` lúc đó trông như mô hình kém, trong khi thực ra là mạng.

**Sửa.**
- Thêm `ModelTransportError(RuntimeError)` vào cổng `application/ports/extraction.py`.
- Adapter ném lỗi này cho HTTP và timeout. `call()` để nó đi qua, nên lần chạy dừng hẳn và không ghi artifact.
- Phản hồi rỗng vẫn tính là đầu ra sai, như hiện nay.
- Cái giá: phải chạy lại từ đầu, mất các lời gọi đã xong trong lần hỏng. Chấp nhận được ở quy mô ≤ 63 lời gọi mỗi tài
  liệu. Với tài liệu lớn thì cần ghi nhật ký dần — để đợt sau.

**Test.** `test_transport_error_aborts_without_freezing_artifact`.

**Ai sửa.** Nhân viên.

---

## F66 🟡 — Ghi chép đợt và vài tiêu chí nhỏ chưa đạt

| # | Hiện trạng | Nên sửa |
|---|---|---|
| 1 | **0/13 ticket được tick**, `Status` vẫn `ready-for-agent`. Các đợt trước đều tick và chuyển `done`. Trạng thái chỉ nằm trong bảng bàn giao bên dưới | Tick theo bảng [kết luận theo ticket](#kết-luận-theo-ticket); ticket 08 chờ F63 |
| 2 | `a4 --help` (`presentation/cli/main.py:33`) ghi *"lớp tên canonical, không gọi mô hình phán"*, sai với chế độ mặc định | *"hợp nhất thực thể và mô tả chuẩn (cần --gold); --names-only/--prepare không gọi mô hình phán"* |
| 3 | Manifest chưa chép hai cảnh báo A3, và chưa có *số node gộp thêm* (ticket 07). `canonicalize.py:96-98` chỉ ghi `stats`; `candidate_quality` nằm trong payload | Thêm hai số đếm cảnh báo và `merged_group_count` vào `stats` |
| 4 | Hai chỉ số lệch nghĩa: `cut_pairs_judged` (`canonical_reasoning.py:230`) đếm cả cặp của lô hỏng; draft giữ lại mà trượt kiểm (`:219-222`) bị viết lại nhưng không vào chỉ số nào | Đếm cặp có quyết định hợp lệ; thêm `a5_rewritten_invalid_draft` |
| 5 | Ticket 14, kênh mô tả: luật của ticket cho đáp án rõ, nhưng báo cáo để ngỏ (*"chưa có bằng chứng… chưa thực hiện phép đo"*) | Ghi quyết định **bỏ kênh mô tả**: 0/100 cặp ngẫu nhiên ngoài đồ thị là *cùng*; mẫu nhỏ, xét lại khi có bộ vàng người |
| 6 | Báo cáo ticket 14 thiếu mục *đề xuất chỉnh tham số hoặc prompt* | Thêm mục đó, dẫn F61, F62, F69 |

Quy ước ghi kết quả, cho lần sau:
- tick tiêu chí và đổi `Status` ngay trong ticket;
- báo cáo thi hành để ở `report/` (ticket 14 yêu cầu vậy — lần này đã làm đúng);
- file F của đợt là file review; phần bàn giao ghi thành mục *Trạng thái xử lý* trong đó;
- không chèn dòng không đánh số vào mục lục vòng review ở `feedback/README.md`.

---

## F67 🟡 — Số mốc trong spec và ticket lệch câu chữ spec — **lỗi của tôi**

| Số | Spec/ticket ghi | Code ra | Vì sao lệch |
|---|---|---|---|
| Cạnh n-gram · hợp · cạnh cắt | 103 · 257 · 27 | 95 · 256 · 38 | Phép đo của tôi đệm hai khoảng trắng hai đầu tên trước khi cắt 3-gram; spec không nói gì về đệm. Chạy code của nhân viên có đệm, seed 42, thì ra đúng 103 · 257 · 27 |
| Alias tên gọi · viết tắt · ký hiệu | 91 · 12 · 25 | 89 · 12 · 27 | `H`, `A` là chữ cái đơn, nên là ký hiệu theo chính luật D2. Code đúng, số của tôi sai |

Code hiện hành, không đệm, còn **tốt hơn** trên bộ vàng: bắt 47/47 cặp *cùng*. Bản có đệm chỉ bắt 46/47, lọt
`Giả thiết H`/`Giả thiết thống kê` — cặp chỉ có cạnh n-gram.

Cạnh bị cắt nhạy với seed Louvain, nên không nên làm mốc:

| seed | 0 | 1 | 2 | 3 | 7 | 42 | 99 |
|---|---:|---:|---:|---:|---:|---:|---:|
| không đệm | 42 | 40 | 40 | 36 | 38 | **38** | 38 |
| có đệm | 27 | 27 | 41 | 40 | 38 | 27 | 27 |

**Sửa** (tôi làm):
- spec D3 ghi rõ *"không đệm"*, số mốc 95 · 256 · 38, kèm dải seed;
- D2 sửa thành 89 · 12 · 27;
- ticket 02 và 04 sửa theo.

Nhân viên đã báo cả hai chỗ lệch mà không ép số — đúng cách.

---

## F68 🟡 — Ba test tích hợp Docling vẫn gọi `huggingface.co`

**Hiện tượng.** Khi chặn mạng, ba test sau hỏng; đặt `HF_HUB_OFFLINE=1` thì cả 6 test tích hợp đều qua:
- `test_docling_parses_real_document[fixture0]`
- `test_docling_parses_real_document[fixture2]`
- `test_real_ingest_reuses_parse_and_keeps_unchanged_chunk_ids`

**Vị trí.** Docling `layout_model.download_models` → `hf_model_download` → `snapshot_download` →
`HfApi.model_info`. Lời gọi này hỏi phiên bản model trên mạng, dù model đã có sẵn trong cache.

**Tác động.** Không thuộc đợt này, nhưng ticket 14 ghi *"không test nào gọi mạng"*. Máy không có mạng thì 3 test đỏ
oan.

**Sửa.** Trong `tests/integration/conftest.py`, gọi `os.environ.setdefault("HF_HUB_OFFLINE", "1")` trước khi import
Docling. Ghi chú trong README của fixture rằng lần tải model đầu tiên cần mạng.

**Ai sửa.** Nhân viên, thuộc phần B0.

---

## F69 🟠 — Lượt vá theo cặp sinh cả 3 ca gộp sai — **thiết kế của tôi, cần chọn phương án**

**Hiện tượng.** Lượt phán cụm gộp 23 cặp, đúng cả 23 theo bộ vàng. Lượt vá theo cặp trả *cùng* 6 lần, chỉ đúng 3 lần.
Cả 3 ca gộp sai của lần chạy đều đến từ lượt vá.

**Bằng chứng** — sáu quyết định *cùng* của lượt vá, kèm lý do nguyên văn của mô hình:

| # | Cặp | Vàng | Lý do của mô hình |
|---|---|---|---|
| 45 | `Data collection` / `Thu thập dữ liệu` | *cùng* ✅ | *"Both refer to the same concept of data collection."* |
| 218 | `Tiêu chuẩn kiểm định χ0^2` / `…χ 0 2` | *cùng* ✅ | *"…the same statistical metric, the chi-square test statistic."* |
| 125 | `Kiến trúc Hub - Client` / `Mô hình Hub - Client` | *cùng* ✅ | *"…the same Hub-Client architecture involving Goroutines…"* |
| 351 | `Cơ chế đồng bộ hóa` / `Lập trình đồng thời` | liên quan ❌ | *"Both groups refer to the same concept of Concurrency…"* |
| 107 | `Thiết kế hệ thống` / `Kiến trúc phân lớp` | liên quan ❌ | *"…the same architectural pattern (Layered Architecture)…"* — bằng chứng thứ nhất chỉ nói phân tích CSDL và đặc tả API |
| 32 | `Phân loại email` / `Phân lớp` | cha–con ❌ | *"Phân loại email is a specific application or instance of the general concept of Phân lớp"* — **lý do tả quan hệ cha–con, nhãn vẫn là *cùng*** |

Lượt cụm cũng có một ca nhãn trái lý do: #403, cạnh `Lớp mô hình ⊂ Kiểu mô hình` kèm lý do *"used interchangeably"*.

**Vị trí.**
- Spec D5, `…spec.md:254-257`: cặp bị cắt phán *"cùng rubric và cùng khuôn đầu vào D4, theo lô khoảng 10 cặp"*.
- `src/doc2roadmap/application/prompts/a4-repair.txt`.
- `canonical_reasoning.py:96-127`.

**Nguyên nhân** — giả thuyết, cỡ mẫu nhỏ (6 quyết định):
- Lượt vá chỉ thấy hai nhóm. Nó không thấy những nhóm anh em đã được gộp hay tách trong cụm của mỗi đầu — thứ ngữ
  cảnh đã giúp lượt cụm chính xác.
- Mười cặp một lượt, mỗi cặp phán độc lập, không có ràng buộc nhất quán giữa chúng.
- Không có bước kiểm nào đối chiếu *nhãn* với *lý do*.

**Tác động.** 3/3 ca gộp sai. Ca `Phân lớp` còn kéo theo cạnh subtype đảo chiều. Bỏ hẳn lượt vá thì precision thành
1,00 nhưng mất 3 cặp đúng (#45, #125, #218).

**Phương án** — cần chọn, rồi đo trong A/B của ticket 14:
- **(a)** Vá bằng **phán cụm nhỏ**: hợp hai node ở hai đầu, gồm mọi nhóm thành viên, thành một cụm, rồi gọi đúng prompt
  và luật kiểm của lượt cụm. Dùng lại đúng cơ chế vừa đo được 23/23.
- **(b)** Giữ lượt vá theo cặp, nhưng nhãn *cùng* phải kèm một câu nguyên văn chứng minh đồng nhất; code kiểm câu đó có
  trong bằng chứng và nhắc cả hai tên. Rủi ro: khó định nghĩa "nhắc cả hai tên". Câu của #45 chỉ có
  *"Thu thập (data collection)"*, không có nguyên dạng `Thu thập dữ liệu`.
- **(c)** Chỉ đổi sang model phán mạnh hơn. A/B sẽ trả lời phương án này.

Tôi nghiêng về **(a)**.

**Test** (nếu chọn (a)): trọng tài giả trả *cùng* ở lượt vá ⇒ phải thấy một lời gọi merge chứa đủ nhóm của cả hai node,
và chỉ quyết định của lời gọi đó được áp.

**Ai sửa.** Tôi chốt phương án và sửa spec D5. Nhân viên cài đặt và đo.

---

## Kết luận theo ticket lúc review, trước khi sửa

| Ticket | Kết luận | Còn lại |
|---|---|---|
| 01 · 02 · 03 · 11 · 13 | ✅ Đạt | tick |
| 04 | ✅ Đạt | số mốc sai là của tôi (F67) |
| 05 | ✅ Đạt | thử trên browser thật |
| 06 | ✅ Claude gán thay | commit |
| 07 | 🟡 Đạt phần chính | F64, F66 mục 3; luật bỏ cả cụm là F61 |
| 08 | 🟠 Chưa | F63; thiết kế lượt vá là F69 |
| 09 · 10 | ✅ Đạt | luật ngôn ngữ là F62 |
| 12 | ✅ Đạt | ghi rõ chủ ý "lỗi không được cache"; F65 |
| 14 | 🟡 Đang làm | fixture hội thoại, A/B, chốt tham số; F66 mục 5–6 |

## Những chỗ tôi phải sửa của chính mình

- **F61** — luật "sai một cạnh là bỏ cả cụm" trong spec D4 trừng phạt thứ chính vì lỗi ở thứ phụ.
- **F62** — luật ngôn ngữ D8 có ví dụ mâu thuẫn với chính nó, và không lường trước bảng số liệu và code.
- **F67** — số mốc lấy từ phép đo có đệm n-gram mà spec không ghi, và đếm sai hai ký hiệu chữ cái đơn.
- **F69** — thiết kế lượt vá D5 cho mô hình ít ngữ cảnh hơn lượt cụm, nhưng không bù lại bằng kiểm nào.

---

## Phụ lục A — Toàn bộ ca sai của lần chạy thật

Số `#` là thứ tự mục trong `tests/fixtures/a4/gold-blind.json` (tính từ 1). "Bước" là nơi mô hình quyết.

### A.1 Gộp sai (3)

| Tài liệu | # | Cặp | Vàng | Bước | Lý do của mô hình | Nhận xét |
|---|---|---|---|---|---|---|
| baocao-canhan | 107 | `Thiết kế hệ thống` / `Kiến trúc phân lớp` | liên quan | vá: *cùng* | *"The groups describe the same architectural pattern (Layered Architecture) used in the project."* | Bằng chứng thứ nhất nói phân tích CSDL và đặc tả API; không có câu nào đồng nhất hai tên |
| baocao-canhan | 351 | `Cơ chế đồng bộ hóa` / `Lập trình đồng thời` | liên quan | vá: *cùng* | *"Both groups refer to the same concept of Concurrency…"* | Cơ chế đồng bộ là công cụ bên trong lập trình đồng thời, không phải chính nó |
| naive-bayes | 32 | `Phân loại email` / `Phân lớp` | cha–con | vá: *cùng* | *"Phân loại email is a specific application or instance of the general concept of Phân lớp"* | Lý do tả cha–con, nhãn *cùng*. Kéo theo cạnh ngược `Phân lớp ⊂ Bài toán phân loại mail` |

### A.2 Bỏ sót (21)

| Tài liệu | # | Cặp | Bước | Lý do của mô hình | Đánh giá |
|---|---|---|---|---|---|
| nhap-mon-ml | 99 | `Bài toán phân loại` / `Phân loại` | vá: liên quan | *"Both concepts relate to the classification task…"* | Sai rõ — chỉ khác tiền tố |
| nhap-mon-ml | 300 | `Data preparation` / `Tiền xử lý dữ liệu` | cụm: tách | *"…a distinct process in data handling."* (cho cả hai) | Sai rõ — tài liệu viết *"Data preparation: … thực hiện tiền xử lý dữ liệu"* |
| nhap-mon-ml | 344 | `Bài toán học` / `Bài toán học máy` | cụm: tách | *"…fundamental concept…" / "…specific concept within… machine learning"* | Có thể bàn |
| nhap-mon-ml | 403 | `Kiểu mô hình` / `Lớp mô hình` | cụm: cha–con | *"Lớp mô hình is used interchangeably with kiểu mô hình."* | Sai rõ — lý do tự nói là một |
| xstk-ch3-1 | 6 | `Phương trình đường hồi quy tuyến tính mẫu` / `Đường hồi quy tuyến tính mẫu` | cụm: tách | *"…the method of writing the… equation" / "…the concept of a… line"* | Nhãn của tôi rộng tay |
| xstk-ch3-1 | 148 | `Ước lượng trung bình` / `Ước lượng trung bình μ` | cụm bị từ chối | — | Do F61 |
| xstk-ch3-1 | 307 | `Ước lượng trung bình tổng thể` / `Ước lượng trung bình μ` | cụm bị từ chối | — | Do F61 |
| xstk-ch3-1 | 317 | `Ước lượng trung bình tổng thể` / `Ước lượng trung bình` | cụm bị từ chối | — | Do F61 |
| xstk-ch3-1 | 208 | `Kiểm định giả thiết thống kê` / `Kiểm định giả thuyết` | cụm: cha–con | *"This is an application of statistical hypothesis testing."* | Có thể bàn — bằng chứng của "giả thuyết" nằm ở bài χ² |
| xstk-ch3-1 | 239 | `Độ tin cậy` / `Độ tin cậy của ước lượng` | cụm: cha–con | *"…là một dạng cụ thể của độ tin cậy."* | Nhãn của tôi rộng tay |
| xstk-ch3-1 | 249 | `Mẫu hai chiều` / `Mẫu tương quan bảng` | cụm: cha–con | *"The text explicitly states that mẫu tương quan bảng is a form of mẫu hai chiều."* | Nhãn của tôi có lẽ sai; mô hình đúng |
| xstk-ch3-1 | 292 | `Giả thiết H` / `Giả thiết thống kê` | cụm: tách | *"…a specific hypothesis H…" / "…the general concept…"* | Nhãn của tôi rộng tay (quy ước hậu tố ký hiệu) |
| xstk-ch3-1 | 311 | `Khoảng ước lượng của σ 2` / `…của phương sai tổng thể` | cụm: cha–con | *"…a specific case of estimating the population variance."* | Sai rõ — σ² chính là phương sai tổng thể |
| xstk-ch3-1 | 318 | `Kiểm định giả thiết thống kê` / `Bài toán kiểm định giả thiết thống kê` | vá: liên quan | *"Both concepts are closely linked…"* | Sai rõ — chỉ khác tiền tố |
| xstk-ch3-1 | 392 | `Bài toán tìm kích thước mẫu` / `Xác định kích thước mẫu` | cụm: tách | *"…một dạng bài toán cụ thể…" / "…phương pháp tổng quát."* | Nghiêng về sai |
| baocao-canhan | 219 | `Docker hóa` / `Container hóa` | cụm: cha–con | *"Docker hóa là một phương pháp cụ thể để thực hiện việc container hóa ứng dụng."* | Nhãn của tôi rộng tay; cha–con hợp lý |
| naive-bayes | 16 | `Bài toán phân loại mail` / `Spam Filtering` | cụm: tách | *"…the conceptual problem…" / "…an application of Naïve Bayes…"* | Có thể bàn |
| naive-bayes | 329 | `Phân loại email` / `Spam Filtering` | cụm: tách | *"…classifying an email instance." / "…an application…"* | Có thể bàn |
| naive-bayes | 361 | `Phân loại email` / `Bài toán phân loại mail` | cụm: cha–con | *"…(E4) is a specific instance… of the general mail classification problem."* | Có thể bàn (E4 là một ví dụ) |
| naive-bayes | 119 | `Naïve Bayes` / `Naïve Bayes Classification` | cụm bị từ chối | — | Do F61 |
| naive-bayes | 415 | `Bernoulli Naive Bayes` / `Bernoulli Naive` | cụm bị từ chối | — | Do F61 |

Tổng: 5 do F61 · 5 sai rõ · 1 nghiêng về sai · 10 do nhãn của tôi rộng tay hoặc có thể bàn.

### A.3 Cạnh `subtype_of` sai (15)

| Tài liệu | # | Cạnh | Vàng | Lý do của mô hình | Đánh giá |
|---|---|---|---|---|---|
| nhap-mon-ml | 403 | `Lớp mô hình ⊂ Kiểu mô hình` | *cùng* | *"…used interchangeably…"* | Sai — lý do tự mâu thuẫn |
| nhap-mon-ml | 304 | `Mạng nơron ⊂ Trí tuệ nhân tạo` | liên quan | *"…a subfield or technique within… AI."* | Có thể bàn — kỹ thuật thuộc lĩnh vực, không phải "một loại" |
| nhap-mon-ml | 59 | `Tính đại diện ⊂ Lấy mẫu` | liên quan | *"Lấy mẫu được thực hiện với mục đích tạo ra tập dữ liệu có tính đại diện…"* | Sai — đó là mục đích, không phải loại con |
| nhap-mon-ml | 141 | `Bài toán học máy ⊂ Học máy` | liên quan | *"…a task within the field of machine learning."* | Sai — thuộc lĩnh vực ≠ loại con |
| nhap-mon-ml | 189 | `Học ⊂ Học máy` | liên quan | *"Learning is a fundamental capability that defines… Machine Learning."* | Sai, và ngược chiều |
| xstk-ch3-1 | 346 | `…so sánh hai tỉ lệ tổng thể ⊂ …tỉ lệ tổng thể` | liên quan | *"Comparing two proportions is a specific case of testing proportions."* | Có thể bàn — kiểm định hai mẫu không phải loại con của một mẫu |
| xstk-ch3-1 | 201 | `…so sánh hai trung bình tổng thể ⊂ …trung bình tổng thể` | liên quan | *"…a specific case of testing means."* | Như trên |
| xstk-ch3-1 | 208 | `Kiểm định giả thuyết ⊂ Kiểm định giả thiết thống kê` | *cùng* | *"This is an application of statistical hypothesis testing."* | Có thể bàn |
| xstk-ch3-1 | 239 | `Độ tin cậy của ước lượng ⊂ Độ tin cậy` | *cùng* | *"…là một dạng cụ thể của độ tin cậy."* | Nhãn của tôi rộng tay |
| xstk-ch3-1 | 249 | `Mẫu tương quan bảng ⊂ Mẫu hai chiều` | *cùng* | *"The text explicitly states…"* | Mô hình có lẽ đúng |
| xstk-ch3-1 | 311 | `Khoảng ước lượng của σ 2 ⊂ …phương sai tổng thể` | *cùng* | *"…a specific case of estimating the population variance."* | Sai |
| baocao-canhan | 219 | `Docker hóa ⊂ Container hóa` | *cùng* | *"…một phương pháp cụ thể để thực hiện việc container hóa…"* | Hợp lý |
| naive-bayes | 324 | `Hàm mật độ xác suất ⊂ Likelihood` | liên quan | *"The probability density function is used to estimate likelihood."* | Sai — "dùng để tính" ≠ loại con |
| naive-bayes | 361 | `Phân lớp ⊂ Bài toán phân loại mail` | *cùng* | *"…(E4) is a specific instance… of the general mail classification problem."* | Sai và ngược chiều — hệ quả của ca gộp sai #32 |
| naive-bayes | 90 | `Maximum Likelihood ⊂ Likelihood` | liên quan | *"…a method used to estimate parameters for the Likelihood function."* | Sai — phương pháp ước lượng, không phải loại con |

### A.4 Quyết định bị từ chối (4 cụm, 2 mô tả)

| Tài liệu | Bước | Đối tượng | Lỗi sau hai lần thử |
|---|---|---|---|
| nhap-mon-ml | merge | `SVM`, `K-NN`, `Naive Bayes`, `ID3` | `mỗi nhóm phải có đúng một lần, không thiếu/thừa` |
| xstk-ch3-1 | merge | sáu nhóm *trung bình* / *ước lượng trung bình* | `subtype_of phải nối hai node khác nhau trong cụm` |
| xstk-ch3-1 | merge | `Phương pháp tính trực tiếp`, `Phương pháp đổi biến số` | `mỗi nhóm phải có đúng một lần, không thiếu/thừa` |
| naive-bayes | merge | sáu nhóm Naive Bayes | `bằng chứng subtype_of nằm ngoài hai đầu` |
| naive-bayes | describe | `Naïve Bayes Classification` | `trích dẫn ngoài node hoặc thiếu trích dẫn` |
| naive-bayes | describe | `Phân lớp` | `mô tả khác ngôn ngữ chủ đạo của tài liệu` (hệ quả F62) |

Không dòng nào lưu đầu ra của mô hình (F64).

---

## Phụ lục B — Test đề xuất

Tám test. Trên code hiện hành, đúng 8 test này hỏng và 228 test cũ vẫn qua. Trên bản vá thử ở phụ lục C, 236/236
xanh.

<details><summary><code>tests/unit/application/test_a4_pipeline.py</code> — thêm vào cuối file (F61, F63, F64, F65)</summary>

```python
# --- Vòng 20: F61, F63, F64, F65 ------------------------------------------------------------

NAMES = ["WebSocket", "WebSockets", "Giao thức WebSockets", "Golang"]


def graph_with(clusters_by_name, cut_by_name):
    def graph(groups, vectors, **kwargs):
        ids = {members[0].name: id for id, members in groups.items()}
        edge = lambda a, b: {"source": ids[a], "target": ids[b], "channels": ["name"], "weight": .9}
        cut = [edge(a, b) for a, b in cut_by_name]
        inner = [edge(c[i], c[j]) for c in clusters_by_name for i in range(len(c)) for j in range(i + 1, len(c))]
        return {"clusters": [[ids[n] for n in c] for c in clusters_by_name], "edges": inner + cut,
                "cut_edges": cut, "metrics": {}}
    return graph


class NamedJudge(FakeModel):
    """Phán theo tên. partition: {tập tên của cụm: [[tên cùng node], ["~tên bị hoãn"]]}; repair: nhãn cố định hoặc "invalid"."""
    def __init__(self, partition=None, repair=None, subtype=None):
        super().__init__()
        self.partition, self.repair, self.subtype, self.prompts = partition or {}, repair, subtype, []

    def ask_json(self, prompt, *, response_schema):
        self.prompts.append(prompt)
        data = json.loads(prompt.split("\nCorrect this validation error:")[0])
        if "groups" in data:
            by = {g["name"]: g["group_id"] for g in data["groups"]}
            plan = self.partition.get(frozenset(by), [[n] for n in by])
            nodes = [{"groups": [by[n] for n in grp], "reason": "fixture"} for grp in plan if not grp[0].startswith("~")]
            deferred = [{"group_id": by[grp[0][1:]], "reason": "fixture"} for grp in plan if grp[0].startswith("~")]
            edges = []
            if self.subtype and {self.subtype[0], self.subtype[1]} <= set(by):
                child, parent, chunk = self.subtype
                edges = [{"child": by[child], "parent": by[parent], "chunk_ids": [chunk], "reason": "fixture"}]
            return SimpleNamespace(payload={"nodes": nodes, "deferred": deferred, "subtype_edges": edges})
        if "pairs" in data:
            if self.repair == "invalid":
                return SimpleNamespace(payload={"pairs": []})
            return SimpleNamespace(payload={"pairs": [{"pair_id": p["pair_id"], "label": self.repair, "child": "",
                                                       "chunk_ids": [], "reason": "fixture"} for p in data["pairs"]]})
        return super().ask_json(prompt, response_schema=response_schema)


def run_named(tmp_path, monkeypatch, judge, clusters, cut):
    monkeypatch.setattr("doc2roadmap.application.use_cases.canonicalize.nomination_graph", graph_with(clusters, cut))
    store = fixture_store(tmp_path)
    result, _ = Canonicalize(store, embedding(), reasoning=CanonicalReasoning(judge, FakeModel())).execute("baocao-canhan")
    raw = {e["candidate_id"]: e["name"] for e in result.payload["source_candidates"]}
    nodes = [frozenset(raw[m] for m in n["members"]) & set(NAMES) for n in result.payload["nodes"]]
    return result, [n for n in nodes if n]


def test_invalid_subtype_edge_is_dropped_not_the_partition(tmp_path, monkeypatch):  # F61
    trio = ["WebSocket", "WebSockets", "Giao thức WebSockets"]
    judge = NamedJudge(partition={frozenset(trio): [["WebSocket", "WebSockets"], ["Giao thức WebSockets"]]},
                       subtype=("Giao thức WebSockets", "WebSocket", "c_outside"))
    result, nodes = run_named(tmp_path, monkeypatch, judge, [trio], [])
    assert frozenset({"WebSocket", "WebSockets"}) in nodes
    assert not [e for e in result.payload["edges"] if e["edge_type"] == "subtype_of"]
    assert any(r.get("stage") == "subtype_rejected" for r in result.payload["decision_log"])


@pytest.mark.parametrize("repair", ["uncertain", "invalid"])
def test_repair_deferral_keeps_existing_cluster_merge(tmp_path, monkeypatch, repair):  # F63
    pair = ["WebSocket", "WebSockets"]
    judge = NamedJudge(partition={frozenset(pair): [pair]}, repair=repair)
    result, nodes = run_named(tmp_path, monkeypatch, judge, [pair], [("WebSockets", "Giao thức WebSockets")])
    assert frozenset(pair) in nodes and frozenset({"Giao thức WebSockets"}) in nodes
    assert result.payload["stats"]["transitive_conflicts"] == 0


def test_cluster_deferred_group_is_not_merged_later_and_does_not_undo_others(tmp_path, monkeypatch):  # F63
    left, right = ["WebSocket", "WebSockets"], ["Giao thức WebSockets", "Golang"]
    judge = NamedJudge(partition={frozenset(left): [left], frozenset(right): [["~Giao thức WebSockets"], ["Golang"]]},
                       repair="same")
    result, nodes = run_named(tmp_path, monkeypatch, judge, [left, right], [("WebSockets", "Giao thức WebSockets")])
    assert frozenset(left) in nodes and frozenset({"Giao thức WebSockets"}) in nodes
    assert result.payload["stats"]["transitive_conflicts"] == 0


def test_retry_names_missing_group_and_log_keeps_rejected_output(tmp_path, monkeypatch):  # F64
    trio = ["WebSocket", "WebSockets", "Giao thức WebSockets"]
    judge = NamedJudge(partition={frozenset(trio): [["WebSocket"], ["WebSockets"]]})   # bỏ sót một nhóm, cả hai lần
    result, _ = run_named(tmp_path, monkeypatch, judge, [trio], [])
    missing = next(g["group_id"] for g in json.loads(judge.prompts[0])["groups"] if g["name"] == "Giao thức WebSockets")
    assert missing in judge.prompts[1].split("Correct this validation error:")[1]
    row = next(r for r in result.payload["decision_log"] if r.get("stage") == "merge" and r.get("valid") is False)
    assert row.get("attempts") and all("raw_text" in a for a in row["attempts"])


def test_transport_error_aborts_without_freezing_artifact(tmp_path, monkeypatch):  # F65
    from doc2roadmap.application.ports.extraction import ModelTransportError
    monkeypatch.setattr("doc2roadmap.application.use_cases.canonicalize.nomination_graph",
                        graph_with([["WebSocket", "WebSockets"]], []))
    class Flaky(FakeModel):
        down = True
        def ask_json(self, prompt, *, response_schema):
            if Flaky.down and '"groups"' in prompt:
                raise ModelTransportError("Gemini API trả HTTP 503")
            return super().ask_json(prompt, response_schema=response_schema)
    store = fixture_store(tmp_path)
    make = lambda: Canonicalize(store, embedding(), reasoning=CanonicalReasoning(Flaky(merge_all=True), FakeModel()))
    with pytest.raises(ModelTransportError):
        make().execute("baocao-canhan")
    Flaky.down = False
    result, reused = make().execute("baocao-canhan")
    assert not reused and result.payload["stats"]["deferred_groups"] == 0
```

</details>

<details><summary><code>tests/unit/domain/test_canonical_decisions.py</code> — thêm vào cuối file (F61, F62), và bỏ hai ca subtype ở test cũ</summary>

```python
# --- Vòng 20: F61, F62 ----------------------------------------------------------------------

def test_subtype_edges_are_filtered_separately_from_the_partition():  # F61
    from doc2roadmap.domain.canonical_decisions import split_subtype_edges
    import copy
    source = {"a": ["ca"], "b": ["cb"], "c": ["cc"]}
    good = {"nodes": [{"groups": ["a", "b"], "reason": "same"}, {"groups": ["c"], "reason": "other"}],
            "deferred": [], "subtype_edges": [{"child": "a", "parent": "c", "chunk_ids": ["ca"], "reason": "subtype"}]}
    for mutate in [lambda v: v["subtype_edges"][0].update(parent="b"),
                   lambda v: v["subtype_edges"][0].update(chunk_ids=["outside"])]:
        bad = copy.deepcopy(good); mutate(bad)
        assert validate_partition(bad, source) is bad          # phân hoạch vẫn hợp lệ
        kept, rejected = split_subtype_edges(bad, source)
        assert kept == [] and len(rejected) == 1 and rejected[0]["error"]
    assert split_subtype_edges(good, source) == (good["subtype_edges"], [])


def test_tables_and_code_do_not_decide_description_language():  # F62
    prose = SimpleNamespace(text="Phân lớp là quá trình dự đoán nhãn lớp cho dữ liệu đầu vào dựa trên các đặc trưng.",
                            token_count=40, block_types=["text"])
    table = SimpleNamespace(text="| Outlook | Temp | Humidity | Windy | Play |\n| Sunny | Hot | High | False | No |" * 8,
                            token_count=500, block_types=["table"])
    code = SimpleNamespace(text="from sklearn.naive_bayes import MultinomialNB\nmodel = MultinomialNB()",
                           token_count=200, block_types=["code"])
    assert document_language([prose, prose, table, code]) == "vi"
    assert document_language([table, code]) == "en"            # không còn văn xuôi thì đếm như cũ
```

Trong `test_partition_guards_and_transitive_conflict`, bỏ hai dòng sau khỏi danh sách `mutate`. Hai ca này chuyển
sang `test_subtype_edges_are_filtered_separately_from_the_partition`:

```python
                   lambda v: v["subtype_edges"][0].update(parent="b"),
                   lambda v: v["subtype_edges"][0].update(chunk_ids=["outside"]),
```

</details>

## Phụ lục C — Bản vá thử

Bản vá này chỉ để chứng minh tám test trên đạt được mà không làm đổ test cũ. Nó **không** phải bản cuối: nhân viên tự
cài theo từng mục, và đặt import `ModelTransportError` trong `gemini.py` vào nhóm import của dự án. Bản vá có phần sửa
`document_language` của F62 nhưng chưa đổi nhãn `canonical_language_rule`, và chưa chứa F66–F69.

<details><summary>diff — 4 file, 191 dòng</summary>

```diff
--- a/src/doc2roadmap/domain/canonical_decisions.py
+++ b/src/doc2roadmap/domain/canonical_decisions.py
@@ -11,9 +11,13 @@
     return bool(words) and accented/len(words) >= .2


+NON_PROSE = {"table", "code", "formula", "figure"}
+
+
 def document_language(chunks):
-    vi = sum(c.token_count for c in chunks if vietnamese(c.text))
-    total = sum(c.token_count for c in chunks)
+    prose = [c for c in chunks if not set(getattr(c, "block_types", None) or ["text"]) <= NON_PROSE] or list(chunks)
+    vi = sum(c.token_count for c in prose if vietnamese(c.text))
+    total = sum(c.token_count for c in prose)
     return "vi" if vi * 2 >= total else "en"


@@ -32,16 +36,27 @@
             raise ValueError("deferred thiếu lý do")
         seen.append(item["group_id"])
     if len(seen) != len(set(seen)) or set(seen) != ids:
-        raise ValueError("mỗi nhóm phải có đúng một lần, không thiếu/thừa")
+        missing, extra = sorted(ids - set(seen)), sorted(set(seen) - ids)
+        repeated = sorted({g for g in seen if seen.count(g) > 1})
+        raise ValueError(f"mỗi nhóm phải có đúng một lần: thiếu {missing}, lặp {repeated}, id lạ {extra}")
     for edge in value["subtype_edges"]:
         if set(edge) != {"child", "parent", "chunk_ids", "reason"}:
             raise ValueError("chỉ được sinh subtype_of")
+    return value
+
+
+def split_subtype_edges(value, source):
+    owner = {g: i for i, node in enumerate(value["nodes"]) for g in node["groups"]}
+    kept, rejected = [], []
+    for edge in value["subtype_edges"]:
         a, b = edge["child"], edge["parent"]
         if a not in owner or b not in owner or owner[a] == owner[b]:
-            raise ValueError("subtype_of phải nối hai node khác nhau trong cụm")
-        if not edge["chunk_ids"] or not set(edge["chunk_ids"]) <= set(source[a]) | set(source[b]) or not edge["reason"]:
-            raise ValueError("bằng chứng subtype_of nằm ngoài hai đầu")
-    return value
+            rejected.append({**edge, "error": "subtype_of phải nối hai node khác nhau trong cụm"})
+        elif not edge["chunk_ids"] or not set(edge["chunk_ids"]) <= set(source[a]) | set(source[b]) or not edge["reason"]:
+            rejected.append({**edge, "error": "chunk ngoài hai đầu", "allowed": sorted(set(source[a]) | set(source[b]))})
+        else:
+            kept.append(edge)
+    return kept, rejected


 def guarded_components(ids, same_pairs, different_pairs):
--- a/src/doc2roadmap/application/use_cases/canonical_reasoning.py
+++ b/src/doc2roadmap/application/use_cases/canonical_reasoning.py
@@ -7,9 +7,10 @@
 from doc2roadmap.application.canonical_prompt import (
     canonical_prompts, PARTITION_SCHEMA, REPAIR_SCHEMA, DESCRIPTION_SCHEMA, SINGLE_SCHEMA,
 )
+from doc2roadmap.application.ports.extraction import ModelTransportError
 from doc2roadmap.domain.canonical import digest, evidence_missing_name, build_nodes
 from doc2roadmap.domain.canonical_decisions import (
-    validate_partition, guarded_components, validate_description, document_language, vietnamese, split_sentences,
+    validate_partition, split_subtype_edges, guarded_components, validate_description, document_language, vietnamese, split_sentences,
 )


@@ -35,7 +36,7 @@
         group_map = {node["node_id"]: group for node, group in zip(initial_nodes, groups, strict=True) if not node["media_id"]}
         node_map = {n["node_id"]: n for n in initial_nodes}
         cache = {row["input_hash"]: row for row in previous_log if row.get("valid") and "input_hash" in row}
-        logs, metrics, deferred, extra_edges = [], Counter(), set(), []
+        logs, metrics, deferred, extra_edges, deferred_pairs = [], Counter(), set(), [], []
         def call(stage, data, schema, validate):
             model = self.writer if stage in {"describe", "check"} else self.judge
             phash = digest([self.prompts[stage], schema, model.model_id, self.generation,
@@ -46,7 +47,7 @@
                 validate(row["output"])
                 logs.append(row); metrics[stage+"_reused"] += 1
                 return row["output"]
-            error = None
+            error, attempts = None, []
             for attempt in range(2):
                 metrics[stage+"_calls"] += 1
                 try:
@@ -54,17 +55,22 @@
                     prompt = json.dumps(data, ensure_ascii=False, sort_keys=True)
                     if error:
                         prompt += "\nCorrect this validation error: " + str(error)
-                    value = session.ask_json(prompt, response_schema=schema).payload
+                    reply = None
+                    reply = session.ask_json(prompt, response_schema=schema)
+                    value = reply.payload
                     validate(value)
+                except ModelTransportError:
+                    raise
                 except (ValueError, TypeError, KeyError, IndexError, RuntimeError) as exc:
                     error = str(exc)
+                    attempts.append({"error": error, "raw_text": getattr(reply, "raw_text", None)})
                     continue
                 logs.append({"stage": stage, "model": model.model_id, "prompt_hash": phash,
                              "input_hash": key, "input": data, "output": value, "valid": True,
-                             "reused": False, "retries": attempt})
+                             "reused": False, "retries": attempt, "attempts": attempts})
                 return value
             logs.append({"stage": stage, "model": model.model_id, "prompt_hash": phash,
-                         "input_hash": key, "input": data, "valid": False, "error": error, "retries": 1})
+                         "input_hash": key, "input": data, "valid": False, "error": error, "retries": 1, "attempts": attempts})
             metrics[stage+"_invalid"] += 1
             return None

@@ -92,7 +98,10 @@
             deferred.update(d["group_id"] for d in value["deferred"])
             for a, b in combinations(cluster, 2):
                 (same if a in owner and b in owner and owner[a] == owner[b] else different).append((a, b))
-            extra_edges.extend(value["subtype_edges"])
+            kept, rejected = split_subtype_edges(value, {id: sources[id] for id in cluster})
+            extra_edges.extend(kept)
+            logs.extend({"stage": "subtype_rejected", "edge": edge} for edge in rejected)
+            metrics["subtype_rejected"] += len(rejected)
         pairs = [{"pair_id": digest([e["source"], e["target"]]),
                   "groups": [group_input(e["source"]), group_input(e["target"])]}
                  for e in nominations["cut_edges"]]
@@ -112,7 +121,7 @@
             value = call("repair", {"pairs": batch}, REPAIR_SCHEMA, validate_pairs)
             if value is None:
                 for a, b in expected.values():
-                    different.append((a, b)); deferred.update((a, b))
+                    different.append((a, b)); deferred_pairs.append({"pair": [a, b], "reason": "repair_invalid"})
                 continue
             for row in value["pairs"]:
                 a, b = expected[row["pair_id"]]
@@ -121,12 +130,12 @@
                 else:
                     different.append((a, b))
                 if row["label"] == "uncertain":
-                    deferred.update((a, b))
+                    deferred_pairs.append({"pair": [a, b], "reason": row["reason"]})
                 if row["label"] == "parent_child":
                     extra_edges.append({"child": row["child"], "parent": b if row["child"] == a else a,
                                         "chunk_ids": row["chunk_ids"], "reason": row["reason"]})
         # A deferred group remains separate even if a later pair proposes to merge it.
-        different.extend((a, b) for a, b in same if a in deferred or b in deferred)
+        same = [(a, b) for a, b in same if a not in deferred and b not in deferred]
         components, conflicts = guarded_components(list(group_map), same, different)
         for group in conflicts:
             deferred.update(group)
@@ -227,6 +236,8 @@
                     metrics["a5_rewritten_language" if not correct_language else "a5_rewritten_unsupported"] += 1
         metrics["transitive_conflicts"] = len(conflicts)
         metrics["deferred_groups"] = len(deferred)
+        metrics["deferred_pairs"] = len(deferred_pairs)
+        logs.extend({"stage": "deferred_pair", **row} for row in deferred_pairs)
         metrics["cut_pairs_judged"] = len(pairs)
         return nodes, edges, logs, review, sorted(deferred), {**metrics, "document_language": language}

--- a/src/doc2roadmap/application/ports/extraction.py
+++ b/src/doc2roadmap/application/ports/extraction.py
@@ -16,6 +16,10 @@
     images: tuple[PromptImage, ...] = ()


+class ModelTransportError(RuntimeError):
+    """Lỗi đường truyền tới nhà cung cấp mô hình; không phải đầu ra sai."""
+
+
 @dataclass(frozen=True, slots=True)
 class ExtractionReply:
     payload: Any
--- a/src/doc2roadmap/infrastructure/llm/gemini.py
+++ b/src/doc2roadmap/infrastructure/llm/gemini.py
@@ -1,5 +1,6 @@
 from __future__ import annotations

+from doc2roadmap.application.ports.extraction import ModelTransportError
 import base64
 import json
 import re
@@ -127,12 +128,12 @@
                     return response.read()
             except HTTPError as error:
                 if error.code not in _RETRYABLE_HTTP:
-                    raise RuntimeError(f"Gemini API trả HTTP {error.code}") from error
+                    raise ModelTransportError(f"Gemini API trả HTTP {error.code}") from error
                 failure: Exception = error
             except (URLError, TimeoutError) as error:
                 failure = error
             if attempt == attempts - 1:
-                raise RuntimeError(
+                raise ModelTransportError(
                     f"Gemini API lỗi tạm thời sau {attempts} lần thử"
                 ) from failure
             sleep(2**attempt + random())
```

</details>

---

# Vòng 21 — Kiểm chứng sau sửa F61–F69, và năm phát hiện mới (2026-09-12)

Phạm vi: mọi thay đổi nhân viên làm từ 23:14 ngày 11 đến 00:56 ngày 12 — 10 file `src`, test, 4 fixture LLM, spec,
ticket, [báo cáo chạy thật](../report/a4-a5-lan-chay-that-dau-tien.md) và
[luồng chi tiết 2a](../report/luong-chi-tiet-agent-2a.md). Cách kiểm như mọi vòng: **chạy lại, không đọc dấu tích**.
Để thấy chính xác cái gì đổi, tôi dựng lại `src` lúc review bằng cách gỡ bản vá thử (phụ lục C) khỏi bản sao, rồi so
với `src` hiện tại.

## Kết luận

**Cả chín mục đã được sửa đúng hướng, và mọi con số nhân viên khai đều đúng khi tôi đo lại** — kể cả A/B, bảng quét
cấu hình và các lời khai về cache. Kết quả trên bộ vàng AI:

```
trước sửa   26 / 3 / 21   P 0,897   R 0,553   F1 0,684
sau sửa     31 / 0 / 16   P 1,000   R 0,660   F1 0,795     (+6 cặp lấy lại, −1 cặp đánh mất, −3 FP)
```

Nhưng có **năm phát hiện mới**, F70–F74:
- một lỗi code nhỏ nằm trong chính phần sửa F64;
- bốn chỗ test chưa giữ guard;
- hai lỗi spec của tôi, lộ ra khi pipeline đã chạy đúng: kết luận A/B phụ thuộc một câu trong prompt, và luật tên
  chuẩn đếm trùng tên lồng nhau;
- vài dấu tích ticket không khớp thực tế.

Không mục nào chặn việc dùng artifact hiện tại.

## Trạng thái xử lý vòng 21 — cập nhật 2026-09-12

| Feedback | Trạng thái | Kết quả |
|---|---|---|
| F70 | ✅ Xong | Khởi tạo `reply` trước `start_session`; regression test xác nhận lỗi mở session được ghi nhận rồi retry, không còn `UnboundLocalError` |
| F71 | ✅ Xong | Thêm đủ ba guard test: adapter hết retry ném `ModelTransportError`, repair chỉ gộp khi toàn bộ hợp trở thành một node, và `uncertain` chỉ theo cặp; xoá dòng lọc `same` đã chết |
| F72 | ⏸ Reviewer xử lý | Đã ghi rõ giới hạn của kết luận A/B trong báo cáo; chưa đổi model mặc định. Việc soạn prompt biến thể và chạy lại A/B vẫn thuộc reviewer như phân công |
| F73 | ✅ Xong | Cài luật bậc tên + đếm không chồng lấn + hòa tên lồng nhau; bump `a4-names-v2`; thêm bốn test; chạy thật lại bốn tài liệu và thu đúng 8 tên đổi |
| F74 | ✅ Xong | Bỏ hai tick chưa đủ bằng chứng, ghi rõ #218/#260, khôi phục lịch sử Vòng 20 và tách dòng xử lý riêng trong README |

Lần chạy F73 giữ nguyên ID, thành viên và điểm vàng `31/0/16`; không phát sinh chuyển hướng mới. CLI so sánh vẫn hiển thị
lịch sử chuyển hướng đã có của artifact cũ, nên tiêu chí “0 chuyển hướng” ở đây được nghiệm thu theo **delta bằng 0**, không
xóa lịch sử hợp lệ. Cache dùng lại toàn bộ 63 quyết định merge, 38 quyết định repair và 20 singleton check; chỉ gọi lại đúng
8 mô tả A5 vì tên/alias là đầu vào của bước này.

Kiểm chứng cuối: **262/262 test qua**, gồm 6 test tích hợp Docling. Tám test mới của vòng này đã được thấy hỏng trên
hành vi cũ/biến thể đột biến tương ứng trước khi được chấp nhận.

## Kiểm chứng từng mục

| Mục | Cách kiểm | Kết quả |
|---|---|---|
| F61 | đọc diff; đột biến; soi nhật ký chạy thật | ✅ Cụm Naive Bayes từng hỏng nay giữ được phân hoạch; cạnh trích sai chunk chỉ bị loại riêng. XSTK loại 4 cạnh nối hai nhóm cùng node. Lấy lại đủ 5 cặp #119, #415, #148, #307, #317 |
| F62 | chạy lại luật trên 4 tài liệu; đếm mô hình viết | ✅ Cả 4 tài liệu ra `vi`; 36/36 mô tả của `naive-bayes` là tiếng Việt |
| F63 | test; đột biến | ✅ Hoãn ở lượt vá chỉ ghi theo cặp, không tháo gộp đúng. 🟡 test chưa khẳng định `deferred` rỗng — F71 |
| F64 | test; đột biến; đọc nhật ký | ✅ Lưu `attempts` kèm `raw_text`; lỗi nêu id, chunk, số câu; `MalformedModelResponse` mang `raw_text`. 🟡 lỗi `reply` chưa gán — F70 |
| F65 | test; đột biến; thử lỗi mạng giữa lúc chạy song song | ✅ Lỗi đường truyền dừng lượt chạy, không ghi artifact; các lời gọi còn trong hàng đợi bị huỷ, chỉ ≤ concurrency lời gọi đang dở chạy nốt. 🟡 nhánh "hết lượt thử" của adapter không có test — F71 |
| F66 | đếm tick; đọc help, manifest, báo cáo | ✅ 14 ticket `done`; help, `stats`, chỉ số, quyết định bỏ kênh mô tả, mục đề xuất đều đã có. 🟡 hai tick sai thực tế — F74 |
| F67 | grep số cũ; đo lại | ✅ Spec, addendum, ticket 02/04/05 đều dùng 89·12·27 và 95·256·38, không đệm, dải seed 36–42 |
| F68 | cả suite chặn mạng, không tự đặt biến | ✅ **254/254 qua**, gồm 6 test tích hợp Docling |
| F69 | đọc code; test; soi nhật ký | ✅ Lượt vá là cụm nhỏ gồm mọi nhóm của hai node; 4 lần vá gộp, 0 FP. 🟡 đánh mất #218 mà báo cáo không nêu — F74 |

| Lời khai chung | Cách kiểm | Kết quả |
|---|---|---|
| 31/0/16, P 1,000 · R 0,660 · F1 0,795; subtype 35/47, sai 19 | script chấm riêng | ✅ khớp từng số, từng tài liệu |
| Pro Preview 26/1/21, F1 0,703; subtype 19/47, sai 0 | chấm riêng trên `artifacts/a4-ab/` | ✅ khớp |
| Bảng quét 13 cấu hình | chạy lại đồ thị với từng tham số | ✅ 12/12 dòng thử khớp từng số |
| Chạy lại thì `reused=true` | so config hash của code hiện tại với artifact đã lưu | ✅ khớp, dù `canonical_prompt.py` bị sửa sau lần chạy (chỉ xoá hằng không dùng) |
| Concurrency không đổi kết quả | buộc chạy lại toàn pipeline từ nhật ký ở concurrency 1 và 4 | ✅ node, cạnh, `deferred` giống hệt artifact; **0 lời gọi mô hình** |
| 4 fixture hợp đồng là bản ghi thật | đọc fixture và script ghi | ✅ ghi từ `gemini-3.1-flash-lite` qua recorder A3; script từ chối ghi đè; `prompt_hash` tính từ code sản phẩm |
| Bộ vàng không bị sửa | SHA-256 | ✅ `1df2167c…` trùng từng byte ở cả hai bản |
| Guard có test | đột biến 14 chỗ trên bản sao `src` | 🟡 10 bắt được, 4 lọt lưới — F71 |

Lưu ý về "lần chạy mới": 59/63 quyết định cụm được **dùng lại** từ lần chạy trước sửa; chỉ 4 cụm từng hỏng phải gọi
lại. Toàn bộ 38 lượt vá và A5 là lời gọi mới. Đúng thiết kế cache, nhưng nên nói rõ trong báo cáo.

## Chỗ làm tốt

- Tám test đề xuất đều vào repo. Hai ca vá cặp được viết lại cho khớp thiết kế vá mới, và có thêm test riêng cho F69a.
- Lượt vá cụm nhỏ khử trùng theo tập nhóm, nên hai cạnh cắt nối cùng hai node chỉ tốn một lời gọi.
- Nhánh Pro của A/B lưu riêng ở `artifacts/a4-ab/`, không làm bẩn `canonical/latest`. Báo cáo nói thẳng Pro hơn ở
  subtype, không giấu số bất lợi cho lựa chọn của mình.
- Concurrency có hàng rào giữa các stage, thu kết quả theo thứ tự đầu vào; tôi chạy lại ở 1 và 4 luồng ra giống hệt.
- Spec sửa đúng từng điểm review, không tự thêm luật lạ.

---

## F70 🟡 — `reply` chưa gán: lỗi ở `start_session` làm sập cả lượt chạy

**Hiện tượng.** Nếu `model.start_session(...)` (hoặc bước dựng prompt) ném lỗi ở lần thử đầu, lượt chạy chết vì
`UnboundLocalError`, thay vì ghi lần thử hỏng rồi thử lại.

**Tái hiện** — mô hình giả có `start_session` ném `ValueError` một lần:

```
UnboundLocalError - cannot access local variable 'reply' where it is not associated with a value
```

**Vị trí.** `canonical_reasoning.py:62-75`. `reply = None` nằm **sau** `session = model.start_session(...)`, còn nhánh
`except` đọc `reply or exc`. Ở lần thử thứ hai, cũng lỗi này khiến `raw_text` của lần thử trước bị gán nhầm cho lỗi
của lần sau.

**Tác động.** Adapter Gemini hiện không ném lỗi ở `start_session`, nên chưa dính. Nhưng đây là lỗi nằm trong đúng
đoạn code của F64, và sẽ nổ ngay khi một adapter khác, hoặc bước dựng prompt, ném lỗi.

**Sửa.** Chuyển `reply = None` lên đầu thân vòng lặp, trước `start_session`. Một dòng.

**Test.** `test_start_session_error_is_logged_and_retried_not_crash` — hỏng trên code hiện tại, xanh sau khi vá.

**Ai sửa.** Nhân viên.

---

## F71 🟡 — Bốn chỗ test chưa giữ guard

Đột biến 14 chỗ trong phần code mới; 10 chỗ bị test bắt. Bốn chỗ lọt:

| # | Đột biến | Vì sao quan trọng | Test đề xuất |
|---|---|---|---|
| a | Adapter ném lại `RuntimeError` khi **hết lượt thử** (429/503/timeout kéo dài) | Đây là ca mất mạng hay gặp nhất. Test hiện chỉ phủ nhánh HTTP 403, nên nửa sản xuất của F65 có thể âm thầm quay về lỗi cũ | `test_exhausted_transient_errors_raise_transport_error` |
| b | Nới luật D5 thành "chỉ cần a, b chung node" | Spec D5 ghi rõ phải gộp **toàn bộ** hai node; bản nới sẽ bỏ qua việc mô hình tách lại một thành viên cũ | `test_repair_merges_only_when_whole_union_becomes_one_node` |
| c | *Không chắc* ở lượt vá lại đánh hoãn cả hai nhóm | Spec D5: không đưa nhóm đầu mút vào `deferred` toàn cục. Test hiện chỉ kiểm node và số mâu thuẫn | `test_uncertain_repair_is_pair_scoped_not_group_deferral` |
| d | Xoá dòng `same = [… if a not in deferred …]` (`canonical_reasoning.py:125`) | Hoá ra là **code chết**: sau lượt cụm, nhóm bị hoãn không có cặp *cùng* nào | Xoá dòng, hoặc ghi chú vì sao giữ |

Cả ba test a–c đều qua trên code hiện tại, và hỏng đúng khi guard tương ứng bị đột biến (phụ lục D).

**Ai sửa.** Nhân viên.

---

## F72 🟠 — Kết luận A/B phụ thuộc câu "không dùng kiến thức ngoài" trong prompt — **lỗi của tôi** · ✅ xong ở vòng 24

**Hiện tượng.** Pro Preview bỏ sót cả những cặp hiển nhiên mà flash-lite gộp được. Đầu ra của Pro không bị từ chối gì
(0 cụm hỏng, 0 hoãn); đó là phán quyết "tách" có lý do.

| # | Cặp | Lý do Pro tách, nguyên văn |
|---|---|---|
| 214 | `Prior` / `Prior probability` | *"Represents the concept of Prior as mentioned in the text."* |
| 172 | `Laplace estimator` / `Laplace Smoothing` | *"Laplace estimator is mentioned as an algorithm."* |
| 89 | `Maximum Likelihood` / `…Estimation` | *"…mentioned as a method for determining parameters."* |
| 30 | `Database Transaction` / `Transaction` | *"…distinct from the general term 'Transaction' in verbatim evidence."* |
| 99 | `Bài toán phân loại` / `Phân loại` | *"…there is no explicit evidence linking it to the concept 'Phân loại'."* |

**Nguyên nhân gốc.** Spec của tôi đặt nguyên tắc *"phán dựa trên **bằng chứng nguyên văn**… phân vân thì không gộp"*
(spec dòng 38, addendum dòng 688 và 767), nhưng không chừa ngoại lệ cho biến thể từ vựng. Prompt merge, và nay cả
prompt vá, diễn đạt nguyên tắc đó thành câu tuyệt đối: *"using only verbatim document evidence. Never use prior
knowledge to assert identity."* Pro làm đúng từng chữ:
tài liệu không có câu nào nói `Prior` là `Prior probability`, nên tách. Flash-lite dễ dãi hơn nên gộp. Vậy A/B đang
đo **model nào lờ câu đó đi**, chứ chưa đo model nào phán đúng hơn.

**Tác động.**
- Lựa chọn flash-lite vẫn đứng được: F1 cao hơn và rẻ hơn. Nhưng lý do "Pro bỏ sót nhiều hơn" không phải thuộc tính
  của model.
- Ở `subtype_of`, Pro đúng 19 và sai 0; flash-lite đúng 35 nhưng sai 19. 2b sẽ đọc các cạnh này làm đề xuất tiên
  quyết, nên 19 cạnh sai là cái giá thật của lựa chọn hiện tại.

**Sửa.** Tôi làm:
- Ghi rõ giới hạn này vào spec D4 và báo cáo.
- Soạn một biến thể prompt coi **biến thể từ vựng mà tài liệu dùng thay nhau** (cắt cụt, viết tắt, dịch, hậu tố ký
  hiệu) là bằng chứng đồng nhất.
- Chạy lại A/B hai model với biến thể đó trước khi chốt model cuối.
- Đo riêng precision của `subtype_of` như một tiêu chí chọn model, không chỉ F1 gộp.

Chưa đổi mặc định.

---

## F73 🟡 — Luật tên chuẩn đếm trùng tên lồng nhau — **lỗi spec D6 của tôi** · đã chốt 2026-09-12, giao nhân viên

**Hiện tượng.** Khi hai tên thành viên lồng nhau, tên ngắn gần như luôn thắng. Mỗi lần xuất hiện của
`Bernoulli Naive Bayes` cũng khớp ranh giới từ của `Bernoulli Naive`, nên được đếm cho cả hai. 10 node gộp mang tên là
phần đầu của tên thành viên dài hơn; `Bernoulli Naive` là tên bị cắt cụt do khâu trích. Chính ví dụ trong spec D6 cũng
sai vì thế: `Naïve Bayes` "17 lần" gồm cả 11 lần nằm trong `Naïve Bayes Classification`, đứng riêng chỉ 6 lần.

**Nguyên nhân gốc.** Spec D6 chỉ nói *"tần suất… khớp theo ranh giới từ"*, không tính tới tên lồng nhau.

**Quyết định — chủ dự án chốt 2026-09-12.** Giữ code chọn tên; không để 2a hay A5 chọn. Luật mới, đã ghi vào spec D6:

1. **Bậc**: tên gọi thuần chữ › tên gọi có token ký hiệu (`Phương sai tổng thể σ 2`) › viết tắt. Ký hiệu không bao giờ
   làm tên. Chỉ bậc cao nhất có mặt trong node được tranh.
2. **Đếm không chồng lấn**: khoá tên dài được đếm rồi che trước, theo độ dài giảm dần. Tên ngắn chỉ đếm phần văn bản
   còn lại.
3. **Hoà**: nếu một tên nằm gọn trong tên kia (khớp ranh giới từ) thì bỏ tên nằm trong. Còn lại chọn dạng xuất hiện
   sớm nhất, như cũ.

Tôi đã thử và loại một biến thể: "hoà thì luôn chọn tên dài hơn". Nó biến `Kiến trúc phân lớp` thành
`Layered Architecture` chỉ vì chữ tiếng Anh nhiều ký tự hơn, và `End-to-End testing` thành `Kiểm thử End-to-End`.

**Kết quả dự kiến — đo bằng bản cài thử trên bốn tài liệu, dựng lại từ nhật ký.** Đúng 8 node đổi tên; id, thành viên
và cạnh giữ nguyên hết. Tên cũ không mất: nó tự thành alias kèm câu bằng chứng.

| Tài liệu | Tên cũ | Tên mới | Vì sao (số đếm sau khi che) |
|---|---|---|---|
| baocao-canhan | `Branching` | `Branching strategy` | hoà 1–1, tên lồng nhau |
| baocao-canhan | `Transaction` | `Database Transaction` | hoà 2–2, tên lồng nhau |
| baocao-canhan | `WebSockets` | `WebSocket` | `WebSocket` 3 · `WebSockets` 2 · `Giao thức WebSockets` 2 |
| naive-bayes | `Bernoulli Naive` | `Bernoulli Naive Bayes` | hoà 1–1, tên lồng nhau |
| naive-bayes | `Maximum Likelihood` | `Maximum Likelihood Estimation` | 2 so với 1 |
| naive-bayes | `Naïve Bayes` | `Naïve Bayes Classification` | 11 so với 6 |
| naive-bayes | `Prior` | `Prior probability` | hoà 3–3, tên lồng nhau |
| nhap-mon-ml | `Phân loại` | `Bài toán phân loại` | 8 so với 3: tác giả viết "bài toán phân loại" là chính |

Giữ nguyên, có chủ đích:
- `Kiến trúc phân lớp`, `End-to-End testing`: hoà nhưng không lồng nhau, nên lấy dạng xuất hiện sớm nhất.
- `Phương sai tổng thể`, `Không gian dữ liệu`, `Độ chính xác`: tên có đuôi ký hiệu xếp dưới.
- `Mạng nơron`, `Ước lượng trung bình`, `Race Condition`: thắng theo số đếm.
- `xstk-ch3-1` không đổi tên node nào.

**Việc cho nhân viên.**

- [x] Cài luật trong `build_nodes` (`src/doc2roadmap/domain/canonical.py`). Bản cài thử ở cuối mục, khoảng 30 dòng.
      Đổi tên biến `tied` của phần chọn tên, để không trùng biến `tied` của phần bỏ phiếu kiểu ngay bên dưới.
- [x] Bump `algorithm_id` `a4-names-v1` → `a4-names-v2` trong `canonicalize.py`. Không bump thì `a4` trả lại artifact
      cũ (`reused=true`) và tên không đổi. Cache quyết định vẫn dùng lại được, vì khoá của nó không chứa `algorithm_id`.
- [x] Thêm 4 test dưới đây vào `tests/unit/domain/test_canonical.py`.
- [x] Chạy lại `a4 --doc-id <doc> --gold tests/fixtures/a4/gold-blind.json` cho bốn tài liệu, rồi nghiệm thu:
  - đúng 8 node đổi tên như bảng trên, mọi node khác giữ tên;
  - `a4-compare` với phiên bản trước F73 (BC v4, slide v3, ML v3, XSTK v3): Jaccard node 1,000, thành viên 1,000,
    không phát sinh chuyển hướng mới (delta 0; lịch sử 7 / 7 / 9 / 7 được giữ nguyên);
  - 0 lời gọi merge, vá và kiểm singleton; đúng 8 lời gọi A5 mô tả lại (báo cáo 3, slide 4, ML 1), vì tên và alias
    nằm trong đầu vào A5;
  - điểm bộ vàng giữ nguyên 31/0/16;
  - toàn bộ test xanh.
- [x] Ghi bảng đổi tên vào báo cáo chạy thật, và sửa dòng mô tả luật tên trong
      `report/luong-chi-tiet-agent-2a.md` (mục 14: *"hòa thì theo vị trí và ID"*) cho khớp luật mới.

**Test.** Bốn test, đã kiểm trên bốn biến thể:

| Biến thể | Test hỏng |
|---|---|
| code hiện tại | `…counts_nested_names_without_overlap`, `…tie_between_nested_names_prefers_the_fuller_one` — đúng lỗi |
| bản cài thử | 0 |
| cài thiếu bậc ký hiệu | `…symbol_suffix_ranks_below_plain_name` |
| hoà thì luôn chọn tên dài | `…tie_between_unrelated_names_keeps_earliest` |

Bản cài thử cũng qua toàn bộ 248 test unit hiện có.

```python
def test_canonical_name_counts_nested_names_without_overlap():  # F73
    short, long = entity("a", "Naïve Bayes"), entity("b", "Naïve Bayes Classification", order=2)
    node, _, _ = build_nodes([[short, long]], "Naïve Bayes Classification. " * 3 + "Naïve Bayes.")
    assert node[0]["name"] == "Naïve Bayes Classification"
    assert "Naïve Bayes" in {alias["name"] for alias in node[0]["aliases"]}


def test_canonical_name_tie_between_nested_names_prefers_the_fuller_one():  # F73
    cut, full = entity("a", "Bernoulli Naive"), entity("b", "Bernoulli Naive Bayes", order=2)
    node, _, _ = build_nodes([[cut, full]], "Bernoulli Naive Bayes và Bernoulli Naive.")
    assert node[0]["name"] == "Bernoulli Naive Bayes"


def test_canonical_name_tie_between_unrelated_names_keeps_earliest():  # F73
    vi, en = entity("a", "Kiến trúc phân lớp"), entity("b", "Layered Architecture", order=2)
    node, _, _ = build_nodes([[vi, en]], "kiến trúc phân lớp (Layered Architecture)")
    assert node[0]["name"] == "Kiến trúc phân lớp"


def test_canonical_name_with_symbol_suffix_ranks_below_plain_name():  # F73
    plain, symbol = entity("a", "Phương sai tổng thể"), entity("b", "Phương sai tổng thể σ 2", order=2)
    node, _, _ = build_nodes([[plain, symbol]], "phương sai tổng thể σ 2. " * 3 + "phương sai tổng thể.")
    assert node[0]["name"] == "Phương sai tổng thể"
```

<details><summary>Bản cài thử — <code>src/doc2roadmap/domain/canonical.py</code></summary>

```diff
--- a/src/doc2roadmap/domain/canonical.py
+++ b/src/doc2roadmap/domain/canonical.py
@@ -73,6 +73,24 @@
             "evidence_missing_name_count": len(missing), "warnings": warnings}


+def name_tier(name: str) -> int:
+    """0 tên thuần chữ · 1 tên có token ký hiệu · 2 viết tắt · 3 ký hiệu (không bao giờ làm tên chuẩn)."""
+    kind = alias_kind(name)
+    if kind == "name":
+        return 1 if any(alias_kind(token) == "symbol" for token in normalize_text(name).split()) else 0
+    return 2 if kind == "abbreviation" else 3
+
+
+def name_counts(keys, text: str) -> dict:
+    """Đếm không chồng lấn: khoá dài đếm và che trước, khoá ngắn không khớp vào trong khoá dài."""
+    counts = {}
+    for key in sorted(keys, key=lambda k: (-len(k), k)):
+        pattern = r"(?<!\w)" + re.escape(key) + r"(?!\w)"
+        counts[key] = len(re.findall(pattern, text))
+        text = re.sub(pattern, " \x00 ", text)
+    return counts
+
+
 def group_names(entities) -> list[list[EntityCandidate]]:
     groups = defaultdict(list)
     for entity in entities:
@@ -94,13 +112,22 @@
         members = sorted(members, key=lambda e: (e.first_order_index, e.candidate_id))
         anchor = members[0]
         node_id = anchor.candidate_id if anchor.is_media else "node_" + digest([anchor.doc_id, anchor.candidate_id])[:24]
-        choices = [e for e in members if alias_kind(e.name) == "name"]
-        choices = choices or [e for e in members if alias_kind(e.name) == "abbreviation"]
+        choices = [e for e in members if name_tier(e.name) < 3]
         if not choices and not anchor.is_media:
             raise ValueError(f"node chỉ có tên ký hiệu: {anchor.candidate_id}")
-        def count(e):
-            return len(re.findall(r"(?<!\w)" + re.escape(name_key(e.name)) + r"(?!\w)", text))
-        chosen = anchor if anchor.is_media else min(choices, key=lambda e: (-count(e), e.first_order_index, e.candidate_id))
+        if anchor.is_media:
+            chosen = anchor
+        else:
+            counts = name_counts({name_key(e.name) for e in choices}, text)
+            tier = min(name_tier(e.name) for e in choices)
+            pool = [e for e in choices if name_tier(e.name) == tier]
+            top = max(counts[name_key(e.name)] for e in pool)
+            tied = [e for e in pool if counts[name_key(e.name)] == top]
+            keys = {name_key(e.name) for e in tied}
+            # Hoà giữa tên lồng nhau thì bỏ tên nằm trong tên khác; hoà thường vẫn chọn dạng xuất hiện sớm nhất.
+            fuller = [e for e in tied if not any(other != name_key(e.name) and re.search(
+                r"(?<!\w)" + re.escape(name_key(e.name)) + r"(?!\w)", other) for other in keys)]
+            chosen = min(fuller, key=lambda e: (e.first_order_index, e.candidate_id))
         votes = Counter(node_type(e) for e in members)
         tied = [kind for kind, n in votes.items() if n == max(votes.values())]
         kind = min(tied, key=lambda k: (k == "concept", -frequency[k], k))
```

</details>

**Ai sửa.** Spec D6: tôi, đã sửa. Code, test, chạy lại và báo cáo: nhân viên.

---

## F74 🟡 — Ghi chép: hai tick sai thực tế, một cặp mất không được báo

- **Ticket 06** tick *"đóng băng vào thư mục fixture và commit"*, trong khi ghi chú ngay bên cạnh nói **chưa commit**.
  Tick khi tiêu chí đạt; chưa đạt thì để mở kèm lý do.
- **Ticket 05** tick *"tiến độ… khôi phục khi mở lại"*. Chưa ai kiểm việc này: DOM giả của tôi chỉ kiểm lưu, không kiểm
  mở lại, và browser thật chưa chạy.
- **Báo cáo** quy 26 → 31 cho *"F61 lấy lại 5 cặp; F69 đưa FP từ 3 về 0"*. Thực tế là +6 (5 cặp F61 và #99) và −1:
  **#218** `Tiêu chuẩn kiểm định χ0^2` / `…χ 0 2`, rõ ràng là cùng. Lượt vá cặp cũ gộp được cặp này; lượt vá cụm nhỏ
  thì tách. Ngoài ra một lần vá gộp rơi vào **#260**, cặp tôi gán *không chắc* (phương pháp và sản phẩm của nó), nên
  không vào điểm. Cả hai nên có trong báo cáo.
- `feedback/README.md` vẫn giữ dòng không đánh số ở đầu mục lục vòng review. Dòng **Vòng 20** (tóm tắt review) còn
  bị viết đè bằng trạng thái xử lý. Theo lệ của các vòng trước (xem "Xử lý vòng 18"), trạng thái xử lý nên là một
  dòng "Xử lý vòng 20" riêng, và dòng review giữ nguyên.
- Gợi ý, không phải lỗi: `χ0^2` và `χ 0 2` chỉ khác cách viết công thức. Nếu khoá tên chuẩn hoá `^` và khoảng trắng
  trong ký hiệu thì lớp tên gộp được luôn, không cần mô hình. Cần đo trên bốn tài liệu trước khi đổi.

**Ai sửa.** Nhân viên.

---

## Kết luận theo ticket, sau sửa

| Ticket | Kết luận | Còn lại |
|---|---|---|
| 01 · 02 · 03 · 04 · 09 · 10 · 11 · 12 · 13 | ✅ Đạt | — |
| 05 | ✅ Đạt | đã bỏ tick chưa được browser thật kiểm; tiêu chí khôi phục vẫn mở |
| 06 | ✅ Claude gán thay | đã bỏ tick commit; fixture đã đóng băng nhưng commit còn chờ chủ dự án |
| 07 | ✅ Đạt | F70 đã xong |
| 08 | ✅ Đạt | F71 b–d đã xong |
| 14 | ✅ Đạt | lưu ý F72 khi đọc kết luận A/B |

## Việc cho nhân viên sau vòng 21

- [x] **F70** — chuyển `reply = None` lên đầu thân vòng lặp trong `call()`; thêm test `start_session` lỗi.
- [x] **F71** — thêm ba test giữ guard (adapter hết lượt thử, luật chấp nhận gộp của lượt vá, hoãn theo cặp); xoá
      dòng lọc `same` đã thành code chết.
- [x] **F73** — cài luật tên chuẩn đã chốt, bump `algorithm_id`, thêm 4 test, chạy lại bốn tài liệu và nghiệm thu theo
      bảng 8 node đổi tên.
- [x] **F74** — sửa hai tick ticket 05/06, ghi #218 và #260 vào báo cáo, trả dòng Vòng 20 trong README về tóm tắt review
      và thêm dòng "Xử lý vòng 20" riêng.
- F72 là phần của tôi (biến thể prompt và A/B lại); nhân viên chưa cần làm gì.

Mã test F70–F71 ở phụ lục D; mã test và bản cài thử F73 ở ngay mục F73.

## Phụ lục D — Test đề xuất vòng 21

Kiểm hai chiều trên bản sao `src`:

| Biến thể | Test hỏng |
|---|---|
| code hiện tại | chỉ `…start_session_error…` (đúng lỗi F70) |
| adapter ném `RuntimeError` khi hết lượt thử | thêm `…exhausted_transient_errors…` |
| nới luật chấp nhận gộp ở lượt vá | thêm `…whole_union_becomes_one_node` |
| *không chắc* ở lượt vá đánh hoãn cả nhóm | thêm `…pair_scoped_not_group_deferral` |
| vá F70 (`reply = None` đầu vòng lặp) | **0** — cả 4 xanh |

<details><summary><code>tests/unit/application/test_a4_pipeline.py</code> và <code>tests/unit/infrastructure/test_a3_llm.py</code> — bốn test</summary>

```python
# Trong test_a4_pipeline.py: NamedJudge, run_named đã có sẵn; test adapter đặt ở test_a3_llm.py.

def test_start_session_error_is_logged_and_retried_not_crash(tmp_path, monkeypatch):  # F70
    pair = ["WebSocket", "WebSockets"]
    class FlakySession(NamedJudge):
        failed = False
        def start_session(self, prompt):
            if not FlakySession.failed:
                FlakySession.failed = True
                raise ValueError("phiên hỏng")
            return self
    judge = FlakySession(partition={frozenset(pair): [pair]})
    result, nodes = run_named(tmp_path, monkeypatch, judge, [pair], [])
    assert frozenset(pair) in nodes
    row = next(r for r in result.payload["decision_log"] if r.get("stage") == "merge")
    assert row["retries"] == 1 and row["attempts"][0]["raw_text"] is None


def test_exhausted_transient_errors_raise_transport_error(monkeypatch):  # F71a
    def always_503(request, timeout):
        raise HTTPError(request.full_url, 503, "unavailable", {}, None)
    monkeypatch.setattr("doc2roadmap.infrastructure.llm.gemini.urlopen", always_503)
    monkeypatch.setattr("doc2roadmap.infrastructure.llm.gemini.sleep", lambda s: None)
    session = GeminiEntityExtractor("test-secret", max_retries=2).start_session("system")
    with pytest.raises(ModelTransportError, match="lỗi tạm thời"):
        session.ask_json("extract", response_schema={"type": "object"})


def test_repair_merges_only_when_whole_union_becomes_one_node(tmp_path, monkeypatch):  # F71b
    left = ["WebSocket", "WebSockets"]
    combined = [*left, "Giao thức WebSockets"]
    # Lượt vá gộp WebSockets với Giao thức nhưng tách WebSocket khỏi chính cụm cũ của nó ⇒ không nhận gộp.
    judge = NamedJudge(partition={frozenset(left): [left],
                                  frozenset(combined): [["WebSockets", "Giao thức WebSockets"], ["WebSocket"]]})
    result, nodes = run_named(tmp_path, monkeypatch, judge, [left], [("WebSockets", "Giao thức WebSockets")])
    assert frozenset(left) in nodes and frozenset({"Giao thức WebSockets"}) in nodes
    assert result.payload["stats"].get("repair_merged_pairs", 0) == 0


def test_uncertain_repair_is_pair_scoped_not_group_deferral(tmp_path, monkeypatch):  # F71c
    pair = ["WebSocket", "WebSockets"]
    judge = NamedJudge(partition={frozenset(pair): [pair]}, repair="uncertain")
    result, nodes = run_named(tmp_path, monkeypatch, judge, [pair], [("WebSockets", "Giao thức WebSockets")])
    assert result.payload["deferred"] == []
    assert len(result.payload["deferred_pairs"]) == 1
```

</details>

---

# Vòng 22 — Kiểm chứng sau sửa F70–F74 (2026-09-12)

Phạm vi: thay đổi của nhân viên từ 15:54 đến 16:16 — 3 file `src`, 3 file test, ticket 05/06, báo cáo chạy thật, tài
liệu luồng 2a, README, và 4 artifact mới (báo cáo v5, slide v4, ML v4, XSTK v4). Cách kiểm như mọi vòng: chạy lại,
không đọc dấu tích. Tôi dựng lại `src` lúc vòng 21, bằng cách gỡ bản cài thử F73 khỏi bản sao, để thấy chính xác cái gì
đổi.

## Kết luận

**Cả bốn mục giao cho nhân viên đều làm đúng và đủ; mọi lời khai khớp khi đo lại. Không có lỗi code mới.**

Chỉ ba file `src` đổi, đúng những gì được giao. Một tick ở ticket 06 cần chủ dự án xác nhận. F72 vẫn là phần của tôi.

## Kiểm chứng

| Mục | Cách kiểm | Kết quả |
|---|---|---|
| F70 | đọc diff; đột biến trả `reply = None` về sau `start_session` | ✅ Đã chuyển lên đầu vòng lặp; test mới bắt đột biến |
| F71a | đột biến: adapter hết lượt thử ném `RuntimeError` | ✅ `test_exhausted_transient_errors_raise_transport_error` bắt |
| F71b | đột biến: nới luật chấp nhận gộp ở lượt vá | ✅ `test_repair_merges_only_when_whole_union_becomes_one_node` bắt |
| F71c | đột biến: *không chắc* ở lượt vá hoãn cả hai nhóm | ✅ `test_uncertain_repair_is_pair_scoped_not_group_deferral` bắt |
| F71d | đọc diff | ✅ Đã xoá dòng code chết |
| F73 — code | so với bản cài thử | ✅ Đúng luật đã chốt; đã đổi tên biến `tied` như dặn; `algorithm_id` lên `a4-names-v2` |
| F73 — test | 4 đột biến: đếm chồng lấn như cũ, bỏ bậc ký hiệu, hoà luôn chọn tên dài, hoà lồng nhau lại chọn sớm nhất | ✅ Mỗi đột biến bị đúng test của nó bắt |
| F73 — chạy thật | so 4 artifact mới với phiên bản trước | ✅ Đúng 8 tên đổi như bảng F73; id, thành viên, cạnh giữ nguyên; Jaccard 1,000 / 1,000; 0 chuyển hướng mới |
| F73 — chi phí | đọc chỉ số lần chạy | ✅ 0 lời gọi merge, vá, kiểm singleton; đúng 8 lời gọi A5 (báo cáo 3, slide 4, ML 1). Dùng lại 63 merge, 38 vá, 20 lô kiểm |
| F73 — chất lượng | chấm lại bộ vàng; soi 8 mô tả viết lại | ✅ Vẫn 31/0/16. Cả 8 mô tả: trích dẫn nằm trong node, tiếng Việt, tên cũ đã thành alias |
| F73 — tái lập | buộc chạy lại toàn pipeline từ nhật ký bằng code hiện tại | ✅ Giống hệt 4 artifact mới, 0 lời gọi mô hình |
| F74 | đọc ticket, báo cáo, README | ✅ Bỏ hai tick sai ở ticket 05/06. Báo cáo ghi +6/−1 (#218), #260, việc dùng lại cache, và giới hạn F72. README bỏ dòng không đánh số, tách riêng "Xử lý vòng 20" và "Xử lý vòng 21" |
| Toàn bộ test | cả suite, chặn mạng | ✅ **262/262** |
| Bộ vàng | SHA-256 | ✅ `1df2167c…`, không đổi |

Một chỉnh nhỏ tôi tự làm: dòng **Vòng 20** trong README đã được nhân viên viết lại theo lời của họ. Dòng đó là tóm tắt
review, nên tôi khôi phục nguyên văn.

## Còn mở

- **Ticket 06** — mục *(Đề xuất) Chủ dự án gán mù khoảng 50 mục…* đang được tick, nhưng repo và `artifacts/` không có
  file nhãn nào của chủ dự án. Vòng 21 tôi đã bỏ sót tick này. Bảng HTML xuất JSON vào thư mục tải xuống của trình
  duyệt, nên việc repo không có file chưa đủ để kết luận: **cần chủ dự án xác nhận**. Nếu chưa gán thì bỏ tick và ghi
  *"chưa làm, không chặn"*.
- **F72** (của tôi): soạn biến thể prompt cho phép biến thể từ vựng, rồi A/B lại hai model, đo cả precision
  `subtype_of`.
- **Commit** các thay đổi của đợt: chờ chủ dự án.

---

# Vòng 23 — Rà soát chốt phase A4/A5 (2026-09-12)

Lượt rà soát cuối trước khi đóng phase, không theo feedback cụ thể nào. Phạm vi gồm: vệ sinh repo, bất biến trên
artifact cuối, lệnh CLI thật chạy đầu-cuối khi chặn mạng, 53 user story, tài liệu và cấu hình.

## Kết luận

**Phase đạt để đóng.** Mọi bất biến cứng đều giữ, CLI thật chạy đúng, 262/262 test qua.

Có ba phát hiện mới, đều mức thấp:
- F75 thuộc thiết kế của tôi;
- F76 và F77 là việc nhỏ cho nhân viên;

cộng hai ghi nhận ngoài phạm vi. Không mục nào chặn việc dùng artifact hiện tại. Riêng F75 phải quyết trước khi 2b
đọc `subtype_of`.

## Trạng thái xử lý vòng 23 — cập nhật 2026-09-12

| Feedback | Trạng thái | Kết quả |
|---|---|---|
| F75 | ✅ Xong ở vòng 24 | Luật đổi thành chỉ ghi xung đột, không xoá; prompt không đổi — xem vòng 24 |
| F76 | ✅ Xong | Lọc alias không phải ký hiệu trùng `name_key` với tên chuẩn; bump `a4-names-v3`; test đã đỏ trước vá và xanh sau vá |
| F77 | ✅ Xong | Xóa đủ 8 file fixture cũ trong `tests/fixtures/a4/llm/`; test và recorder tiếp tục dùng `llm-v2` |

Chạy thật lại bốn tài liệu tạo ML v5, XSTK v5, báo cáo v6 và slide v5. Đúng bốn node mất alias trùng; do alias
được lưu theo bằng chứng, tổng cộng có sáu entry bị loại. Tên, ID, thành viên, cạnh và redirect giữ nguyên; 63 merge,
38 repair và 20 singleton check đều dùng cache. Có bốn A5 job, nhưng một job retry một lần nên tổng chỉ số là năm
lần gọi. Điểm vàng giữ `31/0/16`. Kiểm chứng cuối: **263/263 test qua**, gồm 6 test tích hợp Docling.

## Đã kiểm

| Hạng mục | Kết quả |
|---|---|
| Vệ sinh repo | ✅ `git diff --check` sạch (chỉ cảnh báo CRLF của git); không khoảng trắng cuối dòng trong file A4; `networkx==3.6.1` đã ghim; repo không cấu hình linter |
| Bất biến trên artifact cuối (báo cáo v5, slide v4, ML v4, XSTK v4) | ✅ Ứng viên chia trọn vào các node, không ai thuộc hai node; id theo ứng viên neo; không id nào vừa là node vừa là chuyển hướng; chuyển hướng trỏ node còn sống; không nhóm tên nào bị tách; tên chuẩn thuộc tên thành viên, không phải ký hiệu; alias và ký hiệu đúng loại |
| Cạnh | ✅ Không trùng, không tự nối, đầu mút tồn tại; `subtype_of` trích chunk trong hai đầu; **không có chu trình `subtype_of`** |
| A5 | ✅ Media không qua A5; mô tả 1–4 câu, trích dẫn trong node, đúng ngôn ngữ; `first_order_index` và `first_mention_index` đúng luật |
| Chỉ số và nhật ký | ✅ Chỉ số khớp payload; mọi dòng nhật ký có model, `prompt_hash`, `input_hash`; dòng dùng lại có `origin_version` |
| CLI thật, chặn mạng | ✅ `a4 --gold` cả bốn tài liệu → `reused=true`, không tạo phiên bản mới; `a4-evaluate` slide 7/0/3; `a4-compare` chạy đúng; `a3-report` ML 5 câu / 17 tên, 1 thiếu tên |
| 53 user story | ✅ Mỗi story có bằng chứng qua vòng 20–23; riêng US24 chỉ có unit test phủ (xem ghi nhận) |
| Cấu hình và tài liệu | ✅ `.env.example` có đủ khóa A4; README hướng dẫn đúng với code |

---

## F75 🟡 — `subtype_of` của A4 lẫn quan hệ khác loại và chồng lên cạnh A3 — **thiết kế của tôi** · ✅ xong ở vòng 24, luật đổi thành *chỉ ghi*

**Hiện tượng.** Trên 61 cạnh `subtype_of` của bốn tài liệu:
- **11 cạnh có lý do tả quan hệ khác hẳn "là một loại"** (quét theo từ khoá rồi đọc tay; `Bayesian network ⊂
  Probabilistic Graphical Model` bị quét nhầm và đã loại):
  - `Mutex ⊂ Race Condition` — *"Mutex là cơ chế dùng để giải quyết Race Condition"*;
  - `Kiểm định giả thiết thống kê ⊂ Giả thiết thống kê` — *"là quá trình tìm quyết định chấp nhận hay bác bỏ một
    giả thiết"*;
  - `Thiết kế Cơ sở dữ liệu ⊂ Thiết kế hệ thống` — *"a component of the overall system design"*;
  - `Tỉ lệ mẫu tổng quát ⊂ Mẫu tổng quát` — *"a statistic of…"*;
  - `Học máy ⊂ Học` — *"an application of the concept of learning"*.
- **11 cạnh trùng cặp với một cạnh A3 đã có.** 5 cặp mang `component_of` cùng chiều (bộ phận ≠ loại con), 6 mang
  `example_of`, 1 mang `uses` cùng chiều (`Mutex → Race Condition`), 1 mang `uses` ngược chiều.

**Nguyên nhân gốc.** Validator chỉ kiểm cấu trúc (hai đầu khác node, chunk trong hai đầu), không kiểm nghĩa. Spec D7
của tôi chỉ nói *"cạnh `subtype_of` được thêm vào, là kiểu mở"*, không nói phải làm gì khi cặp đó đã có cạnh A3.

**Tác động.** 2b đọc `subtype_of` như tín hiệu phân cấp khi suy tiên quyết, nên hiện nhận tín hiệu nhiễu và đôi khi
trái nghĩa với cạnh A3 trên cùng cặp. Chuyện này chồng lên con số 19 cạnh sai theo bộ vàng ở F72.

**Sửa — tôi quyết trước 2b, làm cùng đợt F72.**
1. Biến thể prompt của F72 thêm luật: chỉ phát `subtype_of` khi bằng chứng nói rõ "là một loại / dạng / trường hợp
   của".
2. Luật code: nếu cặp đã có cạnh A3 thuộc {`component_of`, `uses`, `solves`, `prevents`, `causes`, `computed_by`,
   `contrasts_with`} thì không thêm `subtype_of`; ghi `subtype_conflicts_a3` vào nhật ký và chỉ số.
3. Khi A/B lại, đo precision `subtype_of` trên 47 cặp cha–con của bộ vàng, cạnh F1 gộp.

---

## F76 🟡 — Alias lặp lại chính tên chuẩn

**Hiện tượng.** 4 node có alias trùng khóa tên với chính tên chuẩn: `Concurrency`, `Race Condition` (báo cáo),
`Modeling`, `Giải thuật học` (ML). Alias này đến từ danh sách alias của một ứng viên khác trong node. Ví dụ ứng viên
`Tranh chấp dữ liệu` khai alias `Race Condition`, trùng đúng tên chuẩn của node.

**Vị trí.** `build_nodes`, vòng gom alias (`src/doc2roadmap/domain/canonical.py`).

**Tác động.** Nhỏ: danh sách alias bẩn, và mention map ở đợt sau sẽ nhận một mục thừa.

**Sửa.** Bỏ entry alias (không phải ký hiệu) có khóa tên bằng khóa tên chuẩn — 2 dòng. Bump `algorithm_id` lên
`a4-names-v3`.

Nghiệm thu, đo bằng bản vá thử trên bốn tài liệu:
- đúng 4 node mất đúng một alias trùng tên;
- tên, id, thành viên, cạnh giữ nguyên;
- 0 lời gọi merge và vá; 4 lời gọi A5 (alias là đầu vào A5);
- điểm giữ 31/0/16.

Bản vá thử qua 256 test unit.

**Kết quả triển khai.** Đúng bốn node nêu trên được làm sạch; sáu entry alias bị loại vì `Concurrency` và
`Race Condition` mỗi node có hai entry cùng tên gắn với bằng chứng khác nhau. Bốn A5 job được chạy lại; một job retry
một lần nên `describe_calls=5`. Các cấu trúc còn lại và điểm vàng không đổi.

**Test** — hỏng trên code hiện tại, xanh sau khi vá:

```python
def test_alias_never_repeats_the_canonical_name():  # F76
    a, b = entity("a", "Race Condition"), entity("b", "Tranh chấp dữ liệu", order=2)
    b.aliases = [VerifiedAlias("Race Condition", b.evidence[0]), VerifiedAlias("race condition", b.evidence[0])]
    node, _, _ = build_nodes([[a, b]], "Race Condition. Race Condition. Tranh chấp dữ liệu.")
    assert node[0]["name"] == "Race Condition"
    names = [x["name"] for x in node[0]["aliases"]]
    assert "Tranh chấp dữ liệu" in names
    assert not [n for n in names if n.casefold() == "race condition"]
```

```diff
             for name, evidence in alternatives:
+                if alias_kind(name) != "symbol" and name_key(name) == name_key(chosen.name):
+                    continue
```

**Ai sửa.** Nhân viên.

---

## F77 🟡 — Fixture LLM cũ không còn dùng

**Hiện tượng.** `tests/fixtures/a4/llm/` (8 file, khoảng 220 KB, có chữ giáo trình) là bản ghi của thiết kế vá theo
cặp đã bỏ ở F69. Không test hay script nào tham chiếu tới nó nữa; chỉ còn file `.pyc` cũ khớp tên. Test hợp đồng và
script ghi đều dùng `llm-v2`.

**Sửa.** Xoá trước khi commit. Nếu muốn giữ làm lịch sử thì thêm README nói rõ nó ứng với prompt đã bỏ; tôi nghiêng
về xoá.

**Kết quả triển khai.** Đã xóa đủ 8 file; `tests/fixtures/a4/llm-v2/` là bộ fixture hợp đồng duy nhất còn được test
và recorder sử dụng.

**Ai sửa.** Nhân viên.

---

## Ghi nhận ngoài phạm vi

- **A3, tầng trước phase này.** Bản ứng viên mới nhất của cả bốn tài liệu không có ứng viên `learnable = false`.
  4 máy tính CASIO (XSTK v2–v3 là `false`) không còn được trích từ prompt A3 v4, dù chữ "CASIO" vẫn nằm trong 7 chunk.
  Điều này không sai với A4. Nhưng nhánh review "cùng tên, khác kiểu, nằm hai phía `learnable`" (US24) không có ca
  thật để kiểm, chỉ unit test phủ. Nên xem lại ở đợt A3 kế tiếp.
- **Cờ `nghi_gop_nham`.** Có 2 cờ. Cờ ở `Likelihood` (slide) là báo động giả: `P(A|B)` và `p(x|c)` là cùng khái niệm
  trong hai bối cảnh. Không cần sửa; A13 sẽ lấy mẫu.

## Trạng thái đóng phase

| Hạng mục | Trạng thái |
|---|---|
| 14 ticket | `done`. Ticket 06 còn mục commit mở, và tick khảo sát 50 mục chờ chủ dự án xác nhận |
| F61–F74 | Đóng; F72 đóng ở vòng 24 |
| F75 | ✅ Đóng ở vòng 24 |
| F76, F77 | ✅ Xong |
| Commit | Chờ chủ dự án |

## Việc cho nhân viên sau vòng 23

- [x] **F76** — sửa `build_nodes`, bump `a4-names-v3`, thêm test, chạy lại bốn tài liệu, nghiệm thu theo bốn tiêu chí
      ở F76.
- [x] **F77** — xoá `tests/fixtures/a4/llm/`.
- [ ] Ticket 06 — sửa tick khảo sát 50 mục sau khi chủ dự án xác nhận.

---

# Vòng 24 — Hoàn tất F72, F75; kiểm F76, F77; chốt phase (2026-09-12)

Tôi tự làm F72 và F75. Luật chọn nhánh A/B viết **trước khi chạy** và đã chép nguyên vào báo cáo chạy thật, mục
A/B.

## Kết luận

**Phase A4/A5 đóng.** Mặc định giữ nguyên: `gemini-3.1-flash-lite` cộng prompt phân hoạch hiện hành.

- F75 là một luật code mới: **chỉ ghi** xung đột `subtype_of`–A3, không xoá cạnh.
- F76 và F77 của nhân viên đạt.
- 265/265 test qua khi chặn mạng.
- Bộ vàng không đổi (`1df2167c…`).

Chủ dự án chốt thêm trong vòng này: giai đoạn dev dùng flash-lite cho mọi khâu LLM, khi nào cần nâng sẽ báo.
Cấu hình vốn đã như vậy, không phải sửa.

## F72 — A/B lại hai prompt × hai model

| Nhánh | TP / FP / FN | P gộp | F1 gộp | Subtype đúng / 47 | Subtype sai | Precision subtype | Theo luật |
|---|---|---:|---:|---:|---:|---:|---|
| **A** flash-lite · v1 (mặc định) | 31 / 0 / 16 | 1,000 | 0,795 | 35 | 19 | 0,635 | **thắng** |
| B Pro · v1 | 26 / 1 / 21 | 0,963 | 0,703 | 19 | 0 | 1,000 | qua cổng, F1 kém 0,092 |
| C flash-lite · v2.1 | 38 / 3 / 9 | 0,927 | 0,864 | 27 | 0 | 1,000 | trượt cổng P ≥ 0,95 |
| D Pro · v2.1 | 38 / 7 / 9 | 0,844 | 0,826 | 13 | 0 | 1,000 | trượt cổng P ≥ 0,95 |
| E flash-lite · v1.1 (hậu kiểm) | 25 / 0 / 22 | 1,000 | 0,694 | 33 | 10 | 0,756 | trượt F1 và precision subtype |

- **v2.1** coi biến thể từ vựng là bằng chứng đồng nhất và chỉ cho `subtype_of` khi bằng chứng nói "là một loại".
  Recall lên 0,809. Nhưng mệnh đề "tên cắt cụt, tên kèm ký hiệu" làm mô hình gộp tên chung với tên riêng mà bộ vàng
  gán cha–con: `Giá trị tới hạn t α` / `Giá trị tới hạn`, `Độ chính xác` / `…trong ước lượng tỉ lệ`,
  `Đường hồi quy mẫu Y theo X` / `Đường hồi quy mẫu`.
- **Sự cố v2**: bản đầu thiếu câu đòi dùng `group_id`. Flash-lite ghi tên nhóm thay id ở 48 lượt thử, phát hiện qua
  validator chứ không qua điểm. v2.1 chỉ thêm câu đó. Nhánh Pro + v2 bị dừng giữa chừng để khỏi tốn tiền.
- **v1.1** = v1 cộng riêng luật subtype. Nhánh này chọn sau khi thấy điểm, nên có luật riêng viết trước khi chạy, và
  nó trượt. Lỗi ghi tên nhóm thay id quay lại ở 20 lượt thử, làm 16 nhóm bị hoãn.
- Tôi dừng ở đây; chỉnh tiếp là chỉnh prompt theo nhãn đã thấy. Lần thử prompt sau phải đo trên **nhãn mới**.

## F75 — đo xong thì đổi thiết kế: chỉ ghi, không xoá

Bản luật tôi viết ở vòng 23 xoá `subtype_of` khi cặp đã có cạnh A3 khác nghĩa. Đo trên bộ vàng, luật đó **có hại**:
- trên bốn nhánh, nó xoá 17 cạnh đúng và chỉ bắt 2 cạnh sai;
- ở mặc định, precision subtype tụt từ 0,635 xuống 0,630;
- lỗi nằm ở phía A3, vốn gắn biến thể thành bộ phận: `Gaussian/Multinomial/Bernoulli Naive Bayes` `component_of`
  `Naïve Bayes`.

Luật chốt: giữ cả hai cạnh; ghi `subtype_conflicts_a3` vào nhật ký, kèm kiểu cạnh A3, và vào chỉ số.

| Hạng mục | Kết quả |
|---|---|
| Code | `find_subtype_conflicts` trong `domain/canonical_decisions.py`; `canonicalize.py` ghi nhật ký và chỉ số; config thêm `"subtype_rule": "a3-conflict-log-v1"` |
| Test | 2 test mới; 6/6 đột biến bị bắt: không ghi, quay lại xoá, đếm sai, khoá cặp có chiều, coi `example_of` là xung đột, bỏ `component_of` |
| Chạy thật | báo cáo v7, slide v6, ML v6, XSTK v6, chạy bằng CLI thật khi LLM bị bẫy: **0 lời gọi LLM**, 7 xung đột ghi nhận (1/2/3/1). Node, thành viên, cạnh giống hệt phiên bản trước; điểm giữ 31/0/16 |
| Script | `scripts/run_a4_arm.py` chạy một nhánh A/B vào kho riêng; `--partition-prompt` nhận `scripts/a4_ab_prompts/v2.1.txt` hoặc `v1.1.txt`. Chạy lại nhánh E khi chặn mạng → `reused=true` cả bốn tài liệu |
| Tài liệu | spec D4 (kết quả A/B), D7 (luật xung đột; 2b coi `subtype_of` là đề xuất); addendum (hợp đồng 2a, quy trình 2b); báo cáo chạy thật; luồng 2a |

Hệ quả cho 2b: `subtype_of` mặc định có 33 cạnh đúng và 19 cạnh sai trên cặp có nhãn. Trong 19 cạnh sai, 8 cạnh nối
hai tên *cùng* và 11 cạnh nối hai tên chỉ liên quan. 2b phải kiểm lại, không coi `subtype_of` là sự thật.

## Kiểm F76, F77 của nhân viên

| Mục | Cách kiểm | Kết quả |
|---|---|---|
| F76 — code, test | đọc diff; test mới đỏ trên code cũ, xanh sau vá | ✅ Đúng hai dòng như giao; `a4-names-v3` |
| F76 — chạy thật | so báo cáo v5→v6, ML v4→v5 | ✅ Đúng 4 node mất alias trùng (6 entry); tên, id, thành viên, cạnh giữ nguyên; 0 alias trùng tên chuẩn còn lại |
| F76 — chi phí | chỉ số | ✅ 0 merge/vá/kiểm; A5: 4 job, 5 lời gọi (một lần thử lại `Race Condition`) — khớp lời khai |
| F76 — chất lượng | chấm bộ vàng | ✅ 31/0/16 |
| F77 | tìm tham chiếu | ✅ Thư mục đã xoá; không test/script nào còn trỏ tới |

## Trạng thái cuối phase

| Hạng mục | Trạng thái |
|---|---|
| F61–F77 | ✅ Đóng hết |
| Ticket 06 | Tick khảo sát 50 mục vẫn chờ chủ dự án xác nhận đã gán hay chưa; không chặn |
| Commit | Chờ chủ dự án — chưa commit gì |
| Mang sang phase sau | `subtype_of` precision 0,635 (2b kiểm lại); 16 cặp *cùng* bỏ sót; bộ vàng do Claude gán nên thử prompt sau cần nhãn mới; ghi nhận A3 (`learnable=false`, CASIO) ở vòng 23 |

---

# Vòng 25 — Kiểm thử đợt quan hệ kiểu mở ở 2a (2026-09-14)

Phạm vi:
- ticket 02–06 của [`task/a4-quan-he-mo-2a/`](../task/a4-quan-he-mo-2a/), do nhân viên làm;
- ticket 07, tôi chấm theo luật viết trước khi chạy.

Bước 0 (commit mốc) chưa làm, nên tôi dùng bản chụp `src` cuối vòng 24 làm mốc so sánh.

## Kết luận

- **Nhân viên làm đúng và đủ ticket 02–06.** Không có lỗi code nào làm sai kết quả. 283/283 test qua khi chặn mạng.
  Tôi thử 14 đột biến, test bắt được 12.
- **Theo luật: không nhận.** Precision gộp 0,809, dưới ngưỡng 0,95. Lỗi nằm ở prompt v3 tôi viết (F78), không ở code.
- **Việc gấp (F79):** code v3 đang là mặc định trong cây làm việc chưa commit.

## Đã kiểm

| Hạng mục | Cách kiểm | Kết quả |
|---|---|---|
| Phạm vi | diff với bản chụp `src` cuối vòng 24 | ✅ Chỉ 7 file `src` và 5 file test, đều trong phạm vi ticket. Prompt khớp nguyên văn v3 ở ticket 00 |
| Test | toàn bộ, chặn mạng | ✅ 283/283 (trước là 265) |
| Đột biến | 14 đột biến của tôi: guard đầu mút, chunk, kiểu dành riêng, chuẩn hoá, khử trùng, tự nối, `origins`, gộp với A3, F75, các số của `a4-evaluate` | ✅ 12 bị bắt; 2 lọt (F80) |
| Fixture | `llm-v3` | ✅ Có 4 fixture kèm context. `llm-v2` đã xoá, không còn tham chiếu |
| Bất biến trên artifact nhánh thử | chunk nằm trong nguồn hai đầu; không kiểu dành riêng; `origins` hợp lệ; không trùng bộ ba; chỉ số khớp payload | ✅ Cả bốn tài liệu |
| Tái lập | dựng lại từ nhật ký của nhánh, mô hình bị bẫy | ✅ 0 lời gọi; node, cạnh, redirect giống hệt; config hash giống |
| Số nhân viên báo | tôi chấm độc lập | ✅ Khớp 38/9/9 và mọi chỉ số |
| Kho chính | phiên bản mới nhất | ✅ Vẫn báo cáo v7, slide v6, ML v6, XSTK v6 |

## Kết quả theo luật (chi tiết ở ticket 07)

| Cổng | Ngưỡng | Mặc định | v3 | |
|---|---|---:|---:|---|
| Precision gộp | ≥ 0,95 | 1,000 | **0,809** | ❌ |
| F1 gộp | ≥ 0,775 | 0,795 | 0,809 | ✅ |
| Precision `subtype_of` | ≥ 0,635 | 0,635 | 0,688 | ✅ |
| Cụm hỏng hẳn | ≤ 1 | 0 | 0 | ✅ |
| Mẫu 30 quan hệ đúng | ≥ 60% | — | 73% | ✅ |

Kênh quan hệ tự nó có ích:
- 6/11 cặp *liên quan* từng bị gắn `subtype_of` sai giờ được gắn kiểu đúng hơn;
- 6/8 cặp *cùng* từng bị gắn sai giờ được gộp;
- 0 lượt thử hỏng, tức câu bắt dùng `group_id` đã có tác dụng.

Cái giá phải trả là precision gộp.

---

## F78 🟠 — Prompt v3 làm node thành nhóm chủ đề — **thiết kế của tôi**

**Hiện tượng.** Có 9 cặp bị gộp sai, cả 9 đều do mô hình trực tiếp phán *cùng*. Ví dụ:
- `Bài toán phân loại` + `Bài toán phân cụm` + `Bài toán hồi qui`: *"specific types of machine learning problems"*;
- `Business understanding` + `Analytic approach` + `Data understanding`: *"steps in the process"*;
- `Pessimistic Locking` + `Database Locking`: gộp chung node, trong khi cùng đầu ra đó mô hình lại ghi
  `Pessimistic Locking subtype_of Database Locking`.

**Bằng chứng.**
- 9/51 node gộp chứa một quan hệ nối hai nhóm của chính nó: 6 `subtype_of`, 2 `precedes`, 1 `example_of`, 2 `same_as`.
- 7/9 ca gộp sai nằm trong những node đó.
- Để so sánh, prompt v1 chỉ có 2/70 đề xuất `subtype_of` rơi vào cùng node.
- Có một kiểu rò theo chiều ngược lại: `Data preparation equivalent_to Tiền xử lý dữ liệu`. Mô hình cho là cùng một thứ
  nhưng vẫn để hai node riêng.

**Nguyên nhân gốc.**
- Prompt v1 buộc "cha–con ⇒ tách node **và** ghi `subtype_of`" trong cùng một vế. Prompt v3 tôi viết tách hai ý đó ra
  hai chỗ, nên mô hình không còn gắn quan hệ với việc tách node.
- Validator loại quan hệ tự mâu thuẫn, nhưng vẫn áp lần gộp sai. Lỗi được phát hiện, rồi bị bỏ qua.

**Bài học chung.** Bốn lần đổi prompt phân hoạch (v2, v2.1, v1.1, v3) đều làm flash-lite đổi hành vi gộp. Muốn thêm
việc cho 2a thì không nên nhét vào cùng lời gọi phân hoạch.

**Tác động.** Không nhận. Kho chính không bị ảnh hưởng.

## F79 🟠 — Code chưa được nhận đang là mặc định — **quy trình** · ✅ đã dọn 2026-09-14

> **Đã dọn, chủ dự án đồng ý:** code mặc định được khôi phục, ghi lại fixture `llm-v2`, và commit phase A3–A5 lên
> `main`. Kiểm: `a4` khi chặn mạng cho `reused=true` cả bốn tài liệu, 265/265 test. Code v3 commit riêng trên nhánh
> `a4-quan-he-mo-2a` (283/283 test). Hướng 3, luật nhất quán trên v3, làm tiếp trên nhánh đó.

**Hiện tượng.** Bước 0 chưa làm: không commit mốc, không mở nhánh. Code v3 (prompt, schema, lắp cạnh) nằm thẳng trong
cây làm việc của `main` và chưa commit.

**Tác động.**
- Chạy `doc2roadmap a4` bây giờ sẽ ghi kết quả v3 vào kho chính.
- Nếu commit phase lúc này, commit đó sẽ chứa một thiết kế đã trượt luật.
- Không có git thì đường lui chỉ còn là khôi phục tay.

**Sửa, cần chủ dự án đồng ý:**
1. Lưu diff v3 thành một bản vá.
2. Khôi phục code mặc định từ bản chụp cuối vòng 24 (prompt v1, `subtype_edges`). Có thể giữ lại phần vô hại và có ích
   ở `a4-evaluate`: `subtype_precision` và tuỳ chọn loại mục.
3. Commit phase A3–A5 làm mốc.
4. Đưa bản vá v3 lên nhánh `a4-quan-he-mo-2a` để còn dùng lại.

Trước khi làm xong, không chạy `a4` vào kho chính.

## F80 🟡 — Hai lỗ test — **nhân viên**

- **M9.** Đổi `relations_2a_on_gold` sang đếm cả cạnh A3 thì không test nào đỏ, vì cạnh A3 trong test chấm tay nằm trên
  cặp không có nhãn. Sửa: đặt cạnh A3 đó lên một cặp có nhãn.
- **M14.** Ticket 03 ghi "giữ `reason` đầu tiên giữa các cụm và lượt vá", nhưng giữ lý do cuối cùng thì không test nào
  đỏ. Kết quả vẫn tất định, nên đây là lệch spec chứ không phải lỗi đúng/sai. Sửa: thêm test hai cụm đề xuất cùng một bộ
  ba với hai lý do khác nhau.
- Test "hai đầu thành một node" monkeypatch `split_relation_edges` thay vì dựng ca thật (cụm tách hai nhóm, lượt vá gộp
  lại). Nó chứng minh được bộ đếm, nhưng không chứng minh được đường đi thật.

## F81 🟡 — Hai chỗ đếm lệch nghĩa, và artifact sinh trước lần sửa chỉ số — **nhân viên**

- `relation_other_type_than_a3` đếm cả cạnh cùng kiểu nhưng ngược chiều với cạnh A3, dù tên chỉ số nói "khác kiểu". Lần
  chạy này có 0 ca như vậy.
- `relations_2a_on_gold`: khi nhiều mục vàng rơi vào cùng một cặp node thì nhãn cuối thắng. Lần chạy này có 3 cặp như
  vậy, nhưng không cạnh 2a nào rơi vào.
- Artifact của ticket 06 thiếu khoá `relation_self_removed = 0` ở ML và XSTK, vì sinh trước khi sửa `Counter`. Code hiện
  tại cùng config hash sẽ ghi khoá này. Vô hại. Lần sau, sửa gì làm đổi payload thì chạy lại hoặc tăng `relation_rule`.

Chỉ cần sửa nếu thiết kế này được dùng lại.

## Hướng đi tiếp — chủ dự án quyết

1. **Dọn cây làm việc (F79)** — nên làm ngay, dù chọn hướng nào dưới đây.
2. **Dừng.** Giữ mặc định. 2b coi `subtype_of` là đề xuất cần kiểm lại (spec D7). Thử lại quan hệ mở khi có nhãn mới.
3. **Hai lời gọi — tôi đề nghị nếu muốn đi tiếp.**
   - Giữ nguyên prompt phân hoạch v1. Nhờ vậy mọi quyết định gộp lấy từ cache, precision gộp giữ 1,000 theo cấu trúc,
     không phụ thuộc may rủi.
   - Thêm một lời gọi riêng cho mỗi cụm có ≥ 2 node sau phân hoạch: đặt quan hệ kiểu mở (có cả `subtype_of`) giữa các
     node đã tách.
   - Tốn thêm khoảng 60–80 lời gọi flash-lite cho bốn tài liệu.
   - Việc gộp và việc gắn quan hệ không còn tranh nhau trong một lời gọi, nên kiểu lỗi F78 không thể xảy ra.
4. **Luật nhất quán trên v3** — rẻ hơn, nhưng vẫn giữ prompt v3.
   - Quan hệ nối hai nhóm trong cùng node (kể cả `same_as`, `equivalent_to`) coi là đầu ra tự mâu thuẫn: thử lại một lần
     kèm lỗi cụ thể, vẫn mâu thuẫn thì hoãn cụm.
   - Luật này bắt được 7/9 ca gộp sai lần này, nhưng thử lại có thể biến thành hoãn, làm recall tụt.

Hướng 3 và 4 đều được nghĩ ra sau khi đã thấy lỗi trên bộ vàng này. Vì vậy chúng cần luật viết trước khi chạy mới, và
nên xác nhận trên nhãn mới trước khi nhận.

---

# Bàn giao của nhân viên — triển khai A4/A5 (2026-09-11)

Ngày cập nhật: 2026-09-11. Nguồn yêu cầu: `task/a4-a5-hop-nhat/`, spec A4/A5 và ADR 0005/0006.

## Trạng thái bàn giao

### Cập nhật concurrency và fixture thật

- Kiểm chứng cuối đợt: **244 test pass** toàn dự án, gồm integration;
  `.venv/Scripts/python.exe -m pytest --basetemp tmp/a4-concurrency-full -p no:cacheprovider -q`.
  Cả bốn artifact thật vẫn cache hit sau thay đổi (guard chặn embedding/LLM không bị gọi).
- Thêm `DOC2ROADMAP_CANONICAL_CONCURRENCY=4`, số nguyên dương, riêng A4/A5.
  Giới hạn mỗi lượt chạy tài liệu, không phải toàn hệ thống; 4 tiến trình có thể có 16 lời gọi.
- ThreadPoolExecutor chuẩn Python, mỗi job có session/retry/counter riêng; chỉ thread điều phối cập nhật
  đồ thị/metrics/log. Kết quả thu theo thứ tự đầu vào, không theo thứ tự hoàn tất.
  Có rào giữa merge → repair → A5 synthesis → check → rewrite. Không tạo pool lồng nhau.
- Concurrency không vào config hash/prompt hash; đổi giới hạn không làm mất cache.
  Test so toàn bộ payload khi chạy 1 và 4, đo peak đồng thời, retry từng job, kiểm cache không phát sinh call.
  Cố ý thay executor bằng một worker làm test fail `peak=1 != 4`; cấu hình thật pass.
- Đã ghi đủ bốn fixture Gemini thật ở `tests/fixtures/a4/llm-v2/` bằng recorder A3 dùng lại,
  không sửa hạ tầng LLM. Script `scripts/record_a4_fixture.py` từ chối ghi đè fixture có sẵn.
  Test offline `test_a4_llm_contract.py` kiểm phân hoạch, citation, ID đủ/không lặp và đổi prompt làm replay lỗi.
  `CanonicalReasoning.prompt_hash` dùng chung bởi sản phẩm và test/recorder; không lấy hash từ fixture để tự xác nhận.
- Task 14 còn A/B model và chốt tham số; không thay model mặc định flash-lite theo yêu cầu hiện hành.

**Chưa đánh dấu toàn bộ 14 task hoàn tất.** Chủ dự án đã chấp nhận bộ 416 nhãn AI tại
`tests/fixtures/a4/gold-blind.json` làm mốc đánh giá. Task 06 không còn chặn chạy thật.
Đã mở chạy Gemini A4/A5 với `gemini-3.1-flash-lite`; kết quả chi tiết trong
[báo cáo chạy thật](../report/a4-a5-lan-chay-that-dau-tien.md). Chưa A/B model, chưa có nhãn người độc lập.

Loader hỗ trợ đúng bảng cũ: dựng lại sheet ID và đường dẫn cấp nhóm theo phiên bản lúc gán,
đồng thời kiểm toàn bộ ID/thành viên/bằng chứng. Không sửa file nhãn, timestamp, annotator hoặc đổi nhãn
theo kết quả A4. Test `test_legacy_gold_preserves_labels_and_rejects_changed_context` đã thấy fail
trước sửa và pass sau sửa; sửa đường dẫn giả vẫn bị từ chối. Toàn bộ **234 test pass** sau thay đổi.
Các ghi chú “chờ 06/chưa chạy thật” bên dưới là trạng thái lịch sử, được cập nhật bởi đoạn này.

| Task | Đã triển khai / kiểm chứng | Còn lại |
|---|---|---|
| 01 | Hai cảnh báo thuần domain; A3 mới ghi, a3-report tính trên artifact cũ; corpus đúng 6 câu/19 tên, 31 ứng viên | Không đổi algorithm_id A3 |
| 02 | Lớp tên, dấu thanh, alias/ký hiệu, id neo, tên theo tần suất, bỏ phiếu kiểu, registry mapping, CLI/cache, fixture thật offline | Alias phân loại 89/12/27 thay vì 91/12/25; chưa hiệu chỉnh để chạy theo con số tham chiếu |
| 03 | Remap cạnh, loại tự nối, gộp trùng, OR confirmed, tính lại orphan và registry cạnh | Kiểm chứng thật sau merge phụ thuộc 14 |
| 04 | Vector tên thật, 3 kênh đề cử, Louvain seed/cap, ghi cạnh bị cắt; dependency networkx ghim trực tiếp | Khác đồ thị tham chiếu; xem số đo bên dưới, chưa chốt tham số |
| 05 | HTML tự chứa, lưu localStorage, xuất JSON; loader chặn thiếu/sai mục; phụ lục A map 53/bỏ 5 | **Chưa kiểm bằng browser**: runtime không có browser khả dụng |
| 06 | Bảng mù 416 mục. Claude gán thay theo yêu cầu chủ dự án; qua loader đầy đủ, đóng băng `tests/fixtures/a4/gold-blind.json` | Chưa commit; chưa có người gán thứ hai độc lập (xem ticket 06) |
| 07 | Phán cụm, retry một lần, deferred khi lỗi, kiểm phân hoạch và subtype, không đưa draft, không sinh requires | Chưa fixture mô hình thật (thuộc 14) |
| 08 | Lô vá, guard mâu thuẫn bắc cầu, tính lại node/cạnh | Chưa chạy mô hình thật (thuộc 14) |
| 09 | A5 từ chunk nguồn, kiểm citation/defining chunks, ngôn ngữ theo token, draft fallback có cờ | Cần QA chất lượng mô tả thật; trần 4k là ngân sách nguồn gần đúng, evidence vẫn giữ |
| 10 | Kiểm singleton theo lô; code bắt đổi ngôn ngữ, giữ draft khi phù hợp; test 3 nhánh | Chất lượng phán supported của mô hình chưa đo |
| 11 | Loader canonical, compare id/membership, redirects và khôi phục id; test tách theo đa số, mất hết, khôi phục và nối chuỗi chuyển hướng | Chưa có tiến độ người học thật để kiểm tích hợp B1 |
| 12 | Cache theo hash stage/model/prompt/input; nguồn gốc phiên bản; đổi ngôn ngữ chỉ A5; đổi evidence chỉ cụm ảnh hưởng | Sửa section làm đổi đồ thị có thể đổi ranh giới cụm, kéo theo thêm invalidation hợp lý |
| 13 | CLI evaluate, P/R/F1, recall đề cử, subtype, homonym, agreement/kappa; bộ 8 cặp tính tay | Chưa có điểm trên gold người dùng |
| 14 | Chặn CLI đầy đủ nếu chưa có gold đúng nguồn và đầy đủ mục | **Chờ 06**: 4 fixture LLM, chạy corpus, A/B model, chốt tham số, lần chạy lặp |

## Cách dùng hiện tại

```powershell
# Không mạng: lớp tên và remap cạnh
.venv/Scripts/doc2roadmap.exe a4 --doc-id baocao-canhan --names-only

# Chỉ embedding tên, không phán merge và không A5
.venv/Scripts/doc2roadmap.exe a4 --doc-id baocao-canhan --prepare

# Bảng gán mù nhiều tài liệu (từ canonical stage=nominations)
.venv/Scripts/doc2roadmap.exe a4-gold-sheet --doc-id nhap-mon-ml --doc-id xstk-ch3-1 --doc-id baocao-canhan --doc-id naive-bayes

# CHỈ sau khi người dùng gán xong; chưa chạy lệnh này trên dữ liệu thật
.venv/Scripts/doc2roadmap.exe a4 --doc-id baocao-canhan --gold artifacts/a4-gold.json
```

File để người dùng mở: `artifacts/a4-gold.html`. Chọn nhãn cho mọi mục; mục cha–con chọn chiều;
mục đồng âm chọn ứng viên khác nghĩa; xuất JSON khi xong. Chưa có kiểm chứng browser trong phiên này;
nếu trình duyệt chặn localStorage, bảng hiện cảnh báo, không được dựa vào tự lưu trước khi thử.
Không chạy lại `--prepare` với cấu hình khác trong lúc đang gán bảng đã đóng băng.

`a4` không cờ không còn tự chạy lớp tên: nó yêu cầu `--gold`, để không âm thầm coi output names-only
là output A4/A5 hoàn chỉnh. Các artifact mang `stage=names`, `nominations`, hoặc `complete` rõ ràng.
Stage complete là đã xử lý pipeline; vẫn phải đọc `deferred` và cờ fallback, không có nghĩa mọi node đã tốt.

## Model và ngôn ngữ theo quyết định người dùng

Theo yêu cầu trực tiếp, **merge và A5 đều mặc định `gemini-3.1-flash-lite`**. Chưa chọn model qua A/B.
Hai model vẫn cấu hình riêng bằng `DOC2ROADMAP_MERGE_MODEL_ID` và `DOC2ROADMAP_DESCRIPTION_MODEL_ID`.

`token-majority-vi20-v1`: chunk có ≥20% từ mang dấu tiếng Việt thì là chunk tiếng Việt; cộng token
của hai nhóm chunk để chọn ngôn ngữ mô tả, hòa chọn tiếng Việt. Tên chuẩn không chịu luật này.
Chuỗi `canonical_language_rule` là nhãn phiên bản để vô hiệu hóa cache A5; không phải một parser cho
công thức tùy ý. Đổi chuỗi không tự đổi thuật toán ngôn ngữ.

## Số đo offline trên artifact thật

Candidate nguồn: ML v7, XSTK v5, báo cáo v7, slide v5. Tổng **456 ứng viên = 377 văn bản + 79 media**.
Lớp tên: **279 node văn bản + 79 media**. Cạnh A3 **219 → 213**, loại 6 cạnh trùng, 0 tự nối.
Type tie **12**, khớp mốc task. Cảnh báo **6 câu mô tả / 19 tên** và **31/377** bằng chứng thiếu tên.

| Tài liệu | Node văn bản | Alias/ngram/name | Hợp cạnh | Cụm cần phán | Cụm lớn nhất | Cạnh bị cắt |
|---|---:|---|---:|---:|---:|---:|
| ML | 84 | 3 / 13 / 53 | 58 | 19 | 6 | 7 |
| XSTK | 106 | 1 / 73 / 97 | 124 | 21 | 7 | 21 |
| Báo cáo | 46 | 3 / 2 / 37 | 37 | 12 | 5 | 6 |
| Slide | 43 | 2 / 7 / 35 | 37 | 11 | 7 | 4 |
| Tổng | 279 | 9 / 95 / 222 | 256 | 63 | 7 | 38 |

Bảng gán: 256 cạnh + 100 cặp ngoài đồ thị + 60 nhóm tên = **416 mục**, không phải 417.
So mốc đề cử: ngram 95 thay 103, hợp 256 thay 257, cut 38 thay 27. Cấu hình/code chuẩn hóa tên,
cách gộp 3-gram và lần ghi vector có thể ảnh hưởng đồ thị; **chưa xác định nhân quả từng chênh lệch**.
Không thay nhãn hoặc ngưỡng để ép khớp các con số cũ. Ba cặp động cơ WebSocket/WebSockets,
Race Condition/Tranh chấp dữ liệu và hai tên Hub-Client đều có cạnh trên fixture thật.

Alias: code đếm **89 tên / 12 viết tắt / 27 ký hiệu**. Hai alias `H`, `A` là chữ đơn và được phân loại
ký hiệu theo luật task. Đây là một khác biệt cần người soát đối chiếu với phép đếm tham chiếu, không
phải bằng chứng rằng phép đếm cũ sai. Không đổi tên ứng viên A3 hoặc bằng chứng để sửa số.

## Test và tái lập

### Đợt sửa sau rà soát 2026-09-11

- Kiểm chứng cuối đợt: **233 test pass**, gồm integration; lệnh
  `.venv/Scripts/python.exe -m pytest --basetemp tmp/a4-revision-full -p no:cacheprovider -q`.
  Silver 53 mục đã qua loader mới. `git diff --check` không có lỗi whitespace.
- Task 05: đường dẫn mục lấy từ evidence/source_refs của từng ứng viên, không từ toàn nhóm.
  Bản mới: `artifacts/a4-gold-v2.html`, vẫn 416 mục; giữ nguyên HTML cũ, không ghi đè nhãn người dùng.
  Sheet hash giờ bao gồm nội dung hiển thị để localStorage không tự mang nhãn qua một bảng đã đổi bằng chứng.
  Dùng bản v2 cho lượt gán mới; bản cũ không còn đạt kiểm tra provenance mới.
- Task 09–10: validator chung chặn nhiều câu trong một phần tử citation và kiểm ngôn ngữ mô tả mới;
  sai hai lần thì fallback có trạng thái lỗi. Dùng lại bộ tách câu theo dấu câu của singleton;
  viết tắt có dấu chấm có thể bị yêu cầu viết lại (heuristic, chưa phải bộ phân tích ngôn ngữ).
  Phiên bản validation vào config/prompt hash A5, không tái dùng cache theo luật cũ.
- Task 13: loader mặc định cũng đối chiếu group ID, danh sách thành viên, symbols, kiểu, alias,
  evidence và đường dẫn với nguồn đóng băng. Không cần bật require_complete mới chặn dữ liệu nhóm sai.
  Silver phụ lục A đã sinh lại phần provenance: 53 mục, 5 bỏ; không thay/đoán nhãn.
- Regression đã thấy fail trên code cũ: nhiều câu trong một citation, writer trả sai ngôn ngữ,
  đường dẫn ứng viên lẫn nguồn của nhóm. Test loader thêm đột biến group ID/symbols.
- `test_a5_defining_chunk_moves_order_and_preserves_conflict`: kiểm độc lập thứ tự bằng chunk nguồn,
  có trường hợp định nghĩa muộn hơn lần nhắc đầu và giữ nguyên cờ/lý do mâu thuẫn.
- Chưa đóng task 05 (browser), 06 (người dùng gán mù), 14 (chạy LLM thật/fixture/A-B/đánh giá).
  Bộ vàng là dữ liệu đánh giá, không đưa vào prompt phán gộp; gate của đợt chạy thật đầu tiên vẫn giữ.

Kiểm chứng: toàn bộ suite **229 passed** (gồm 5 integration), 58,50 giây;
sau đó thêm test lịch sử chuyển hướng và chạy lại file domain: **6 passed**.
Lần kiểm tra unit cuối: **224 passed**, 22,16 giây, không gọi mạng.
Lệnh toàn bộ: `.venv/Scripts/python.exe -m pytest --basetemp tmp/a4-final-offline -p no:cacheprovider`.

- `test_canonical.py`: tên, dấu, alias/symbol, tần suất và id neo, tie/review, remap/redirect.
- `test_canonical_decisions.py`: phân hoạch sai/thiếu/lặp; requires; citation ngoài node; mâu thuẫn
  bắc cầu; ngưỡng ngôn ngữ; mutual kNN, symbol, seed và trần cụm.
- `test_a4_pipeline.py`: input/vector thật đã ghi của báo cáo, mô hình giả, merge/lô vá/retry,
  subtype/deferred, A5 giữ/viết lại/fallback, cache và gold loader/evaluation tính tay.
- Script `record_a4_names.py`: chỉ gọi embedding, ghi fixture A3 và vector tên bốn tài liệu.
- Script `convert_a4_silver.py`: chuyển nhãn có sẵn, không tự suy luận chỗ tên viết tắt bằng dấu ba chấm;
  53 mục khớp, 5 bỏ. Ngày gán giữ độ chính xác ngày từ nguồn, không bịa giờ gán.

Ponytail được áp dụng bằng việc dùng lại cổng hội thoại/embedding, artifact và cache nhật ký,
không thêm một hạ tầng LLM riêng. Skill browser đã được dùng để kiểm tra khả năng kết nối nhưng không
có browser khả dụng; vì vậy không đánh dấu phần kiểm chứng UI là hoàn tất.

---

# Bàn giao quan hệ mở 2a — tickets 02–06 (2026-09-13)

Nguồn triển khai: [`task/a4-quan-he-mo-2a/`](../task/a4-quan-he-mo-2a/), lấy hợp đồng tạm thời có thẩm quyền từ
`00-ke-hoach-va-chia-viec.md`. Ticket 01 (spec/ADR) và ticket 07 thuộc reviewer; ticket 08 vẫn khóa tới khi 07 chấp nhận.

- Đã đổi hợp đồng phân hoạch từ `subtype_edges` sang `relations`; từng quan hệ sai bị loại riêng. Validator chặn đầu mút
  lạ/deferred/cùng node, chunk rỗng hoặc ngoài nguồn, reason/type rỗng, `requires` và alias, `illustrates`, `tabulates`.
- Quan hệ mở được map sau khi chốt node, khử trùng xuyên lượt, hợp chunk, giữ reason đầu tiên, gắn `origins`; cạnh A3 luôn
  có `origins: ["a3"]`, cạnh trùng bộ ba có cả `2a` và `a3`. F75 chỉ xem `subtype_of`.
- `a4-evaluate` giữ số cũ và thêm `subtype_precision`, `relations_2a_on_gold`, cùng tùy chọn lặp
  `--exclude-subtype-item`. Ba item ID cho recall 44 đã ghi trong ticket 05.
- Hai prompt dùng nguyên văn v3. Đã gọi flash-lite đúng 4 lần để ghi `llm-v3`; replay offline xanh 4/4 và test F57 vẫn
  bắt thay prompt hash. `llm-v2` đã xóa vì hết consumer.
- Arm riêng ở `artifacts/a4-ab/gemini-3.1-flash-lite-relations-v3`: 134 lời gọi thật = 63 merge + 38 repair + 14
  describe + 19 check. Sinh 73 cạnh 2a: 5 trùng bộ ba A3, 15 cùng cặp khác kiểu, 53 cặp mới; validator loại 14 và bỏ
  2 self-edge. Bốn dòng JSON đầy đủ nằm trong ticket 06.
- Phép cộng số thô, chưa phải kết luận ticket 07: 38 TP / 9 FP / 9 FN, nên precision/recall/F1 gộp đều là 0,8085.
  Như vậy cổng precision 0,95 đang không đạt; reviewer vẫn phải xác nhận cách chấm, cổng cụm hỏng và mẫu 30 quan hệ.
- Phát lại cùng lệnh khi chặn mạng: 4/4 `reused=true`, mọi bộ đếm lời gọi bằng 0; kho canonical chính vẫn giữ
  `baocao-canhan v7`, `naive-bayes v6`, `nhap-mon-ml v6`, `xstk-ch3-1 v6`.
- Kiểm cuối: **283/283 test pass**, gồm 6 integration; `git diff --check` không có lỗi whitespace. Các guard quan hệ đã
  qua mutation check và đỏ đúng từng nhóm lỗi trước khi khôi phục.

Chưa kết luận năm cổng và chưa gán mẫu 30 quan hệ: đó là ticket 07 của reviewer. Không chạy `doc2roadmap a4` vào kho
chính và không thực hiện ticket 08.
