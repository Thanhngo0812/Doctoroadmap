# 11 — Nạp ba tài liệu mới qua A1–A5

**What to build:** Ba tài liệu chủ dự án gửi — hai giáo trình đầy đủ và một tài liệu phẳng — đi hết ingest, A3,
nhánh chỉ mục vector, A4 và A5, để có bảng node canonical làm đầu vào cho mọi thứ còn lại.

Không sửa code ở vé này. Nếu phải sửa thì dừng và báo, vì đó là thay đổi hành vi của phase đã đóng.

**Blocked by:** watermark của `doc-1` đã xử lý ở Vé 18; hiện còn kiểm chất lượng ngôn ngữ `doc-1` và mất khái niệm
ký hiệu của `doc-2` trước khi dùng hai chương này làm vàng.

**Status:** A1–A5 của cả ba tài liệu đã hoàn tất ngày 2026-09-22; A6–A10 đang chạy theo nhịp
vé 19–21. Các đoạn bên dưới giữ lại lịch sử lỗi của PDF cũ, không phải trạng thái hiện hành.

> **Ba tài liệu đã có trong workspace, đã nằm trong `.gitignore`.** Soi trước khi nạp (2026-09-18):
> - `doc-1.pdf` — *Bài giảng Đại số tuyến tính*, tiếng Việt, 159 trang, 208 nghìn ký tự, có `Chương` và ba cấp mục.
>   **Mọi trang đều có watermark Studocu kèm địa chỉ email cá nhân của chủ dự án.**
> - `doc-2.pdf` — *Linear Algebra Done Right, 4th ed.*, **tiếng Anh**, 404 trang, 788 nghìn ký tự, có `Chapter` và
>   `Section`. Đây là tài liệu lớn nhất, ước lượng 700–1.000 chunk.
> - `doc-3.pdf` — *15.773 Hands-on Deep Learning, Lecture 1*, **tiếng Anh**, slide, 110 trang nhưng chỉ 26 nghìn ký
>   tự, cấu trúc phẳng — đúng loại để thử nhánh cụm chủ đề.
>
> Thứ tự chạy: `doc-3` → `doc-1` → `doc-2`, và chỉ chạy `doc-2` sau khi F101 và F102 đã xong, vì nó là tài liệu
> chịu ảnh hưởng nặng nhất của hai lỗi đó.

- [x] Ba tài liệu ingest xong; dán cảnh báo parse của từng tài liệu vào vé.
- [x] A3, chỉ mục vector, A4 và A5 chạy xong cho cả ba.
- [x] Dán bảng cỡ tài liệu vào vé: số trang, chunk, section, node, node `learnable`, media, cạnh đề xuất — dùng
      để chọn chương gán nhãn và để biết định tuyến sẽ chọn nhánh nào.
- [x] Dán số lời gọi, token và **chi phí cộng dồn** của cả ba tài liệu; so với trần 50 USD.
- [x] Chạy lại khi chặn mạng: `reused=true` cho cả ba.
- [x] Không có tài liệu gốc nào bị commit vào repo.
- [x] **`doc-1`: kiểm và báo số chunk còn chứa watermark.** Dòng `lOMoARcPSD|…`, `Scan to open on Studeersnel` và
      dòng có email cá nhân xuất hiện ở **cả 159 trang**; parser đang bỏ được `page_footer` (chân trang của
      `xstk-ch3-1` không lọt vào chunk nào), nhưng watermark của Studocu có thể không được gắn nhãn như vậy. Nếu
      còn sót thì **dừng và báo**: dữ liệu này sẽ đi thẳng vào prompt gửi Gemini và nằm lại trong artifact.
- [x] Ghi rõ ngôn ngữ từng tài liệu vào bảng cỡ; `doc-2` và `doc-3` là tiếng Anh, nên phải kiểm luật ngôn ngữ của
      A5 (`token-majority-prose-vi20-v2`) có xử lý đúng không, và báo nếu mô tả sinh ra lẫn lộn hai thứ tiếng.

## Feedback bàn giao

- Vé không có thay đổi code và không giả lập dữ liệu. Ba PDF đều có trong workspace và vẫn bị Git bỏ qua.
- Chủ dự án mở chặn vé 16 ngày 2026-09-19. Đã bắt đầu đúng thứ tự `doc-3` → `doc-1` → `doc-2`, rồi dừng ở
  `doc-3` theo luật của vé khi gặp lỗi cần sửa phase đã đóng.
- Chưa chạy `doc-1`, nên chưa có PDF/chunk nào chứa watermark hoặc email được gửi tới Gemini. Chưa chạy `doc-2`.

## Lượt chạy thật đầu tiên — `doc-3`, 2026-09-19

| Bước | Phiên bản | Kết quả | Cỡ artifact |
|---|---:|---|---:|
| parse tree | v1 | 110 trang; 93 section; giữ 483/488 node | 10,01 MiB |
| chunks | v1 | 94 chunk; 85 window | 0,14 MiB |
| A3 | v1 | 201 node, 105 `learnable`, 96 media, 120 cạnh; 0 section lỗi | 4,41 MiB |
| chỉ mục A3' | v1 | 94 chunk | 2,12 MiB |
| A4/A5 | — | **dừng**, chưa sinh canonical/nominations | — |

Parse bỏ 1 `caption` và 4 `formula`, sắp lại 9 trang; engine OCR báo nhiều vùng ảnh không phát hiện chữ. Cảnh báo
cấu trúc cuối: 1 caption mồ côi (URL Swarovski), 4 formula rỗng và heading `Deep Learning` lặp hai lần. A3 báo 5
window rỗng, 2 kiểu `learnable` độ tin cậy thấp và 16 ứng viên có evidence không chứa nguyên tên.

Phát lại khi đặt `HTTP_PROXY`/`HTTPS_PROXY` về `127.0.0.1:9`: `extract` trả **tái dùng** candidates v1 và `index`
trả **tái dùng** retrieval v1. A4 `--names-only` vẫn lỗi giống hệt, chứng minh blocker không phụ thuộc mạng hay
embedding.

### F107 — A3 cho biến đơn `X` thành node học được, A4 không thể dựng lớp tên

Ứng viên `candidate_e70160c0a9cacaf16e6e4a95` có `name="X"`, `node_type="concept"`, `learnable=true`, lấy từ chunk
`c_110c9d5cbcbb3a2cc1905eee`. Prompt A3 mặc định đã ghi rõ không trích variable symbols, nhưng đầu ra này vẫn lọt.
Cả `a4 --prepare` và `a4 --names-only` dừng xác định với:

```text
lỗi: node chỉ có tên ký hiệu: candidate_e70160c0a9cacaf16e6e4a95
```

Cần ticket sửa A3/A4 riêng, có test đột biến cho ký hiệu đơn được mô hình trả về. Vé 11 cấm sửa code nên dừng tại
đây; không âm thầm xoá ứng viên khỏi artifact.

### F108 — A3 không lưu usage token, không thể nghiệm thu chi phí của Vé 11

A3 lưu `llm_calls=256` nhưng payload/manifest không lưu `promptTokenCount`, `candidatesTokenCount`, tổng token hay
USD. Vì vậy chỉ có thể báo **256 lời gọi**, không thể tính chính xác token và chi phí đã phát sinh. Không ước lượng
từ độ dài text vì doc-3 có 92 ảnh và hội thoại nhiều lượt. Checklist chi phí của vé cần telemetry A3 trước khi chạy
hai giáo trình lớn.

### F109 — cổng gold A4 không có đường chạy cho tài liệu mới

Ngay cả sau khi sửa F107, CLI A4 đầy đủ yêu cầu `--gold` và từ chối nếu `doc_id` không có trong `documents` của bộ
vàng. `artifacts/a4-gold.json` và fixture đóng băng chỉ chứa `baocao-canhan`, `naive-bayes`, `nhap-mon-ml`,
`xstk-ch3-1`; kế hoạch chung đồng thời cấm sửa bộ vàng đã đóng băng. Cần chốt một trong hai hướng ở ticket riêng:
coi bộ vàng bốn tài liệu là cổng chất lượng toàn pipeline, hoặc gán mù thêm từng tài liệu mới trước A4. Không được
thêm `doc-3` rỗng vào JSON để lách guard.

## Lượt chạy tiếp sau Vé 17 — `doc-3` rồi `doc-1`, 2026-09-20

`doc-3` đã đi hết A1–A5. A3 v2 còn 198 ứng viên (102 learnable, 96 media), 117 cạnh; A4/A5 v1 ra 154 node và
129 cạnh. Tổng 312 lời gọi, 729.173 input + 63.973 output token, chi phí **0,27825275 USD**. A5 nhận đúng ngôn ngữ
`en`, và 58/58 mô tả node text qua bộ kiểm tiếng Anh. Replay không mạng tái dùng candidates v2, retrieval v1 và
canonical v1. Tài liệu mới không có bộ vàng A4 riêng; manifest ghi rõ coverage `none` và bộ vàng bốn tài liệu dùng
làm cổng hồi quy.

Sau đó ingest `doc-1` v1: 159 trang, 118 section, 229 chunk, 80 window; giữ 2.503/2.579 node, stitch 71 lần, sắp
lại 15 trang, 14 ảnh và 1 caption. Quét **trước A3** cho kết quả:

- 114 chunk trên 110 trang (trang 1–158) chứa `lOMoARcPSD`;
- 1 chunk còn dòng `Scan to open on Studeersnel`;
- regex email: 0 chunk, nhưng điều kiện dừng dùng watermark **hoặc** email nên vẫn dừng;
- chưa có byte nội dung doc-1 nào gửi Gemini; `doc-2` chưa ingest/chạy.

Muốn mở lại vé phải có quyết định và ticket riêng để làm sạch watermark rồi ingest lại; không được lặng lẽ lọc
ngay trong artifact đã sinh.

## Lượt chạy tiếp sau Vé 18 — 2026-09-21 (chưa nghiệm thu Vé 11)

Vé 18 đã làm sạch `doc-1` trước khi chia chunk: **229 → 218 chunk**, 118 section, 79 window. Ba mẫu và 140 dòng
bị tác động nằm trong manifest parse/chunk v3; quét `node.text`, `node.raw_text` và JSON chunk/section/document không
còn mã theo dõi, Studeersnel hoặc email. A3 v2 từ chunk v3: 153 ứng viên, 139 learnable, 14 media, 227 cạnh;
246 lời gọi, 1.597.617 input + 72.100 output token, 0,50755425 USD. Chỉ mục v2 có 218 chunk. A4/A5 canonical
v2 hoàn thành với 98 node (84 text, 14 media), 214 cạnh cuối; lượt mới dùng 54 lời gọi mô tả,
70.709 input + 14.151 output token, 0,03890375 USD; các quyết định gộp/vá trúng cache. Chạy lại A4 trả
`reused=true` ở v2. **Nhưng** luật A5 suy ra `document_language=en` cho giáo trình tiếng Việt vì chữ Docling
bị lỗi mã; 51 mô tả bị viết lại theo luật này và 27 fallback. Artifact tồn tại để chẩn đoán, **không đạt chất
lượng ngôn ngữ cho chương vàng `doc-1` Chương 5**. Parse còn 5.591 ký tự private-use, 15 trang đổi reading order,
71 đoạn nối, 14 ảnh, 1 caption mồ côi và cảnh báo heading lặp; đã bỏ 3 document_index + 2 formula rỗng.

`doc-2` (*Linear Algebra Done Right*, **en**) ingest v1: **404 trang, 557 section, 1.038 chunk, 521 window**;
7.062/7.087 node được giữ, 66 ảnh, 61 trang sắp lại, 1 stitch; bỏ 18 caption và 6 document_index. A3 sau
guard alias có bằng chứng (v2): **1.370 ứng viên, 1.298 learnable, 71 media, 606 cạnh**, 1.657 lời gọi,
3.670.371 input + 308.164 output token, 1,37983875 USD, 40 section rỗng, 0 lỗi; chỉ mục v1 có 1.038 chunk.
F111 ghi 47 lượt tên ký hiệu bị loại / 36 tên phân biệt; trong đó vẫn có `ℒ(V,W)`, `L(V,W)` và `𝐅^{m,n}`
(các biến thể khoảng trắng cũng có). Guard có thể đổi tên khi mô hình trả alias chữ xác thực, cứu được 3 ứng viên,
nhưng **không đủ cho mục 3C**. Heading `Exercises 3C` còn nằm dưới `3.56` trong cây parse, cần kiểm scope
trước khi gán vàng. Dừng trước A4/A5 `doc-2`, không giả định khái niệm bị loại là noise.

`doc-3` là tài liệu **en** và A5 đã qua bộ kiểm tiếng Anh 58/58 mô tả như lượt trước. Tổng USD của các lượt
**thành công và có telemetry** tới đây: 0,27825275 (`doc-3`) + 0,50755425 × 2 (A3 `doc-1` trước/sau v3)
+ 0,1146865 + 0,03890375 (A4/A5 `doc-1`) + 1,378743 + 1,37983875 (A3 `doc-2` trước/sau guard)
= **4,20553325 USD**, dưới trần 50 USD. Số này không gồm lượt A3 `doc-1` từng thất bại ở embedding
và chi phí embedding chưa được telemetry định giá; không gọi nó là tổng hóa đơn. `doc-1` và `doc-2` còn thiếu
nghiệm thu chất lượng/ngôn ngữ, nên các ô A1–A5, cache cả ba và bảng vàng vẫn để mở.

## Lượt nạp hợp lệ sau vé 19 — 2026-09-22

Chủ dự án xác nhận thay `doc-1.pdf` bằng bản mới SHA-256
`f55d6fde678bd441473327f430755e70ac87c498888e6712546dec6fea943ace`.
Bản mới **102 trang**, không phải 159 trang của lịch sử trên; ingest không `--strip-line`, quét
parse/chunk cho **0 watermark và 0 email**. Cổng chất lượng chữ không cảnh báo bản mới, nhưng
cảnh báo đúng chunk v3 của bản cũ. Ngôn ngữ A5: `doc-3=en`, `doc-1=vi`, `doc-2=en`, đều
`language_decision=detected`. Mô tả trong phạm vi vàng doc-1 qua bộ kiểm tiếng Việt **45/45**
sau provenance; mô tả doc-2 không thấy câu tiếng Việt khi soát dấu (dấu Latin nằm trong tên
riêng André/René).

| Tài liệu | Trang | Section | Chunk | A3 ứng viên | Canonical node | Learnable | Media | Cạnh A4/A5 | Ngôn ngữ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `doc-3` | 110 | 93 | 94 | 198 | 154 | 58 | 96 | 129 | en |
| `doc-1` mới | 102 | 99 | 199 | 339 | 231 | 225 | 6 | 245 | vi |
| `doc-2` | 404 | 557 | 1.038 | 1.394 | 510 | 438 | 71 | 836 | en |

| Tài liệu | A3 lời gọi | A3 input/output token | A3 USD | A4/A5 input/output token | A4/A5 USD | Cộng A3–A5 USD |
|---|---:|---:|---:|---:|---:|---:|
| `doc-3` | 256 | 671.846 / 47.240 | 0,2388215 | 57.327 / 16.733 | 0,03943125 | 0,27825275 |
| `doc-1` mới | 258 | 752.507 / 66.250 | 0,28750175 | 354.435 / 77.743 | 0,20522325 | 0,492725 |
| `doc-2` | 1.654 | 3.664.939 / 307.473 | 1,37744425 | 1.387.456 / 217.303 | 0,6728185 | 2,05026275 |

**Cộng ba artifact A3–A5 đang dùng: 2,8212405 USD**, dưới trần 50 USD. Đây là tổng
telemetry của phiên bản hiện hành, **không phải tổng hóa đơn**: không cộng lượt thử lỗi/phiên
bản cũ, embedding và các bước A6–A8. A4/A5 chạy lặp `reused=true` ở cả ba; A3 `doc-1`
v3 còn theo thuật toán v8, còn `doc-2` v5 theo v9, đúng ghi chú mixed-config ở vé 19.

Sau A1–A5: cả ba đã qua A6–A10 theo đúng thứ tự cạnh A8 trước, A9/A10 sau.
`doc-3` A9 DAG 58 node/41 cạnh, 8 stage; `doc-1` DAG 225 node/337 cạnh, 29 stage;
`doc-2` DAG 438 node/864 cạnh, 55 stage. Cổng A9 của cả ba đều mở, SCC lớn nhất = 1,
mọi node learnable nằm trong đúng một stage, không stage nào quá 8 node. `doc-2` A8
hoàn tất 352 phiên chính/565 cặp phụ sau một lần tiếp tục từ checkpoint. Bảng vàng trống đã tạo:
`doc-1` Chương 3 mục 3.1–3.4 có 45 đích sau provenance; `doc-2` mục 3C có 24 đích.
Hai người gán chưa điền nhãn, nên E1/E2 và các vé phụ thuộc bộ vàng vẫn chờ con người.

| Tài liệu | Provenance lời gọi / USD | A8 chính / phụ | A8 input/output token | A8 USD | Tổng A3–A8 của artifact hiện hành |
|---|---:|---:|---:|---:|---:|
| `doc-3` | 1 / 0,0003165 | 40 / 89 | 194.482 / 21.786 | 0,0812995 | 0,35986875 |
| `doc-1` mới | 47 / 0,0417175 | 67 / 707 | 1.723.799 / 129.026 | 0,62448875 | 1,15893125 |
| `doc-2` | 51 / 0,05083575 | 363 / 682 | 5.858.770 / 269.927 | 1,869583 | 3,9706815 |

**Tổng ba artifact A3–A8 hiện hành: 5,4894815 USD** theo telemetry, vẫn dưới trần
50 USD; không phải hoá đơn API lịch sử vì các phiên bản cũ, lần lỗi và embedding không nằm
trong tổng này. A9/A10 không gọi mô hình. Phát lại cả ba lệnh `roadmap --stop-after stages`
với `HTTP_PROXY`/`HTTPS_PROXY` trỏ `127.0.0.1:9` đều trả `reused=true` ở v7, không gọi API.
