# Feedback — Pha B0.1–B0.4

- **Vòng 1** — 2026-08-14 · review code theo [`task/b0-chunking/`](../task/b0-chunking/) · F1–F10 · **đã xử lý xong**
- **Vòng 2** — 2026-08-15 · review **kết quả chạy thật** trên `nhap-mon-ml` · F11–F21 · **đã xử lý xong**
- **Vòng 3** — 2026-08-15 · review [`note.md`](../task/b0-va-cau-truc/note.md) (sửa reading order + stitch) · F22–F26 · **đã xử lý xong** ↓
- **Vòng 4** — 2026-08-20 · review đợt [`task/b0-anh/`](../task/b0-anh/) (lưu ảnh + tham chiếu) · F27 · **đã xử lý xong** → [chi tiết](./F11-b0-anh.md)
- **Vòng 5** — 2026-08-21 · review đợt [`task/b0-bang-tach-cau/`](../task/b0-bang-tach-cau/) (bảng + tách câu toàn cầu) · F28 · **đã xử lý xong** → [chi tiết](./F12-b0-bang-tach-cau.md)
- **Vòng 6** — 2026-08-21 · review đợt [`task/b0-tran-bang/`](../task/b0-tran-bang/) (ba trần token) · F29 · **1 mục mở, lỗi ticket của tôi** → [chi tiết](./F13-b0-tran-bang.md)
- **Vòng 7** — 2026-08-21 · soi chất lượng chunk trên **tài liệu thứ hai** `xstk-ch3-1` · F30–F33 · **4 mục mở** → [chi tiết](./F14-xstk-chat-luong-chunk.md)

- **Vòng 8** — 2026-08-22 · review đợt [`task/b0-symbol-cong-thuc/`](../task/b0-symbol-cong-thuc/) (Symbol + công thức) · F34 · **1 mục nhỏ** → [chi tiết](./F15-b0-symbol-cong-thuc.md)
- **Vòng 9** — 2026-08-29 · soi hai tài liệu mới `baocao-canhan` (DOCX) + `naive-bayes` (slide) · F35–F40 · **thành spec đợt DOCX** → [báo cáo](../report/ra-soat-b0-sau-bon-tai-lieu.md)
- **Vòng 10** — 2026-08-29 · review đợt [`task/b0-docx-don-dep/`](../task/b0-docx-don-dep/) (10 ticket) · F41–F43 · **F41 mở: chưa ingest thật** → [chi tiết](./F16-b0-docx-don-dep.md)
- **Vòng 11** — 2026-08-29 · đối chiếu pipeline index với chuẩn quốc tế · **không phải review nhân viên** → [báo cáo](../report/doi-chieu-chuan-quoc-te-chunking.md)
- **Vòng 12** — 2026-08-29 · khảo sát phương pháp trích thực thể cho A3/A3' · **không phải review nhân viên** → [báo cáo](../report/nghien-cuu-a3-trich-xuat-thuc-the.md)
- **Vòng 13** — 2026-09-03 · review đợt [`task/a3-trich-thuc-the/`](../task/a3-trich-thuc-the/) (15 ticket) · F44–F50 · **đã xử lý F44–F46, F48–F50; F47 ghi tồn đọng có số** → [chi tiết](./F17-a3-trich-thuc-the.md)
- **Vòng 14** — 2026-09-04 · kiểm chứng sau sửa F44–F50, cộng tổ chức prompt và ngôn ngữ prompt · F51–F52 · **F44–F46, F48–F50 xác nhận xong; F47 và F51 mở** → [chi tiết](./F17-a3-trich-thuc-the.md)
- **Vòng 15** — 2026-09-04 · xử lý và A/B thật F51–F52 · **F51–F52 xong; F47 giữ tồn đọng có số** → [chi tiết](./F17-a3-trich-thuc-the.md)
- **Vòng 16** — 2026-09-08 · kiểm chứng độc lập F51–F52 và kiểm lại F44–F50 · **F53 đã triển khai registry bền, 202 test pass; F47 còn mở** → [kiểm chứng F53](../report/xu-ly-feedback-f53.md)
- **Vòng 17** — 2026-09-08 · kiểm chứng F53 bằng thực nghiệm · **F54 đã thêm CLI soát kiểu, kiểm trên corpus thật, 204 test pass; F47 còn mở** → [kiểm chứng F54](../report/xu-ly-feedback-f54.md)
- **Vòng 18** — 2026-09-08 · rà toàn luồng A3 (không theo feedback nào) · F55–F60 · **F54 xong và vượt yêu cầu; lỗi None-evidence tái hiện được, F56 đã rút lại sau phản biện, fixture replay tự so với chính nó** → [chi tiết](./F17-a3-trich-thuc-the.md)
- **Xử lý vòng 18** — 2026-09-11 · **F55/F57 đã sửa, F58 ghi chủ ý, 208 test pass; F47 đã thử hai few-shot thật nhưng chưa đạt; F59 chưa kiểm chứng, F60 thuộc 2b** → [kết quả và giới hạn](../report/xu-ly-feedback-f55-f60.md)
- **Vòng 19** — 2026-09-11 · khảo sát văn liệu + đo trên bốn tài liệu cho A4/A5 (Tầng 2a) · **không phải review nhân viên**; embedding mô tả không phải tín hiệu đồng nhất — luật ≥ 0,95 tự gộp đúng 8/62 cặp, ngưỡng 0,75 biến mỗi tài liệu thành một cụm → [báo cáo](../report/nghien-cuu-a4-a5-hop-nhat-thuc-the.md)
- **Vòng 20** — 2026-09-11 · review đợt [`task/a4-a5-hop-nhat/`](../task/a4-a5-hop-nhat/) (14 ticket) và lần chạy thật đầu tiên · F61–F69 · **mọi số báo cáo đúng khi đo lại; P 0,90 / R 0,55 trên nhãn AI; F61 (spec của tôi) làm mất cụm Naive Bayes; F63, F65 tái hiện được; F69 lượt vá sinh cả 3 ca gộp sai; 8 test đề xuất kèm bản vá thử** → [chi tiết](./F18-a4-a5-hop-nhat.md)
- **Xử lý vòng 20** — 2026-09-12 · **F61–F69 đã xử lý hết**; flash-lite đạt P 1,00 / R 0,66 / F1 0,795, A/B cao hơn Pro Preview dưới prompt hiện tại; 254 test xanh → [trạng thái và số đo](./F18-a4-a5-hop-nhat.md)
- **Vòng 21** — 2026-09-12 · kiểm chứng sau sửa F61–F69 · F70–F74 · **9/9 mục sửa đúng, mọi số khai khớp khi đo lại (31/0/16, A/B, quét cấu hình, cache ở 1 và 4 luồng); F70 `reply` chưa gán, F71 bốn guard chưa có test, F72 kết luận A/B phụ thuộc prompt (của tôi), F73 luật tên chuẩn đếm trùng tên lồng nhau (của tôi — **đã chốt luật, sửa spec D6, giao nhân viên cài và chạy lại**), F74 hai tick sai** → [chi tiết](./F18-a4-a5-hop-nhat.md)
- **Xử lý vòng 21** — 2026-09-12 · **F70/F71/F73/F74 đã xong; F72 vẫn thuộc reviewer**; luật tên `a4-names-v2` đổi đúng 8 tên, không đổi ID/thành viên/điểm vàng 31/0/16, 262 test xanh → [trạng thái và bằng chứng](./F18-a4-a5-hop-nhat.md)
- **Vòng 22** — 2026-09-12 · kiểm chứng sau sửa F70–F74 · **cả bốn mục làm đúng và đủ, không lỗi code mới: 8 đột biến bị test bắt, luật tên a4-names-v2 đổi đúng 8 tên với 0 lời gọi merge/vá và 8 lời gọi A5, điểm vàng giữ 31/0/16, 262/262 test; còn mở: tick khảo sát 50 mục ở ticket 06 chờ chủ dự án xác nhận, F72 của tôi** → [chi tiết](./F18-a4-a5-hop-nhat.md)
- **Vòng 23** — 2026-09-12 · rà soát chốt phase A4/A5 (bất biến artifact, CLI thật, 53 user story, tài liệu) · F75–F77 · **phase đạt để đóng: mọi bất biến cứng giữ, 262/262 test; F75 `subtype_of` lẫn quan hệ khác loại và chồng cạnh A3 (của tôi, quyết trước 2b cùng F72); F76 alias lặp tên chuẩn, F77 fixture LLM cũ thừa — nhân viên** → [chi tiết](./F18-a4-a5-hop-nhat.md)
- **Xử lý vòng 23** — 2026-09-12 · **F76/F77 đã xong; F75 do sếp đang xử lý**; `a4-names-v3` làm sạch 6 alias entry trên đúng 4 node, giữ nguyên cấu trúc và điểm 31/0/16; fixture LLM cũ đã xóa; 263 test xanh → [trạng thái và bằng chứng](./F18-a4-a5-hop-nhat.md)
- **Vòng 24** — 2026-09-12 · hoàn tất F72, F75 (của tôi), kiểm F76/F77 · **phase A4/A5 đóng: A/B hai prompt × hai model theo luật viết trước khi chạy → giữ flash-lite + prompt hiện hành (v2.1 trượt cổng P ≥ 0,95, v1.1 hậu kiểm cũng trượt); F75 đo ra luật xoá có hại (xoá 17 cạnh đúng, 2 sai) nên đổi thành chỉ ghi `subtype_conflicts_a3`, 0 lời gọi LLM khi chạy lại; F76/F77 đạt; 265/265 test; chủ dự án chốt dev chỉ dùng flash-lite** → [chi tiết](./F18-a4-a5-hop-nhat.md)
- **Vòng 25** — 2026-09-14 · kiểm thử đợt quan hệ kiểu mở ở 2a ([`task/a4-quan-he-mo-2a/`](../task/a4-quan-he-mo-2a/)) · F78–F81 · **nhân viên làm đúng ticket 02–06 (283/283 test, 12/14 đột biến bị bắt, tái lập 0 lời gọi, số khớp chấm độc lập); theo luật viết trước: không nhận vì precision gộp 0,809 < 0,95 — F78 prompt v3 của tôi làm node thành nhóm chủ đề (7/9 ca gộp sai có quan hệ tự mâu thuẫn trong node); F79 code v3 đang là mặc định trong cây chưa commit, cần dọn; F80–F81 lỗ test và chỗ đếm nhỏ** → [chi tiết](./F18-a4-a5-hop-nhat.md)
- **Xử lý vòng 25 — đợt 2 hướng 3** — 2026-09-14 · tickets 10–13 xong; R1/R2 retry đầu ra tự mâu thuẫn, cache cũ trượt luật được gọi lại, F80–F81 đóng, 294/294 test; arm mới 138 lời gọi + replay 0 lời gọi đạt F1 0,833 và precision `subtype_of` 0,658 nhưng **precision gộp 0,9459 < 0,95, nên ticket 15 vẫn khóa và chờ reviewer kết luận ticket 14** → [chi tiết](./F18-a4-a5-hop-nhat.md)
- **Vòng 26** — 2026-09-14 · kiểm thử đợt 2 (luật kiểm nhất quán trên v3) · F82–F83 · **nhân viên làm đúng ticket 10–13, đóng F80–F81 (294/294 test, 13/13 đột biến bị bắt, tái lập 0 lời gọi, số khớp chấm độc lập); theo luật viết trước: không nhận vì precision gộp 0,946 < 0,95, cách đúng một ca gộp sai — hai ca còn lại là lỗi hệ thống không mang tín hiệu mâu thuẫn; lượt thử lại tách cả node làm mất 4 cặp đúng (F83); main giữ mặc định, ticket 15 không làm** → [chi tiết](./F18-a4-a5-hop-nhat.md)
- **Quyết định sau vòng 26** — 2026-09-14 · **chủ dự án chấp nhận v3 + luật kiểm nhất quán dù precision gộp 0,946 < 0,95** (đổi lấy recall 0,745, F1 0,833 và quan hệ kiểu mở); đường vào `main`: ticket 01 (spec, ADR) → ticket 15 (mẫu thứ hai với ngưỡng xác nhận precision ≥ 0,93, rồi gộp nhánh và chạy kho chính) → đợt tổ chức prompt → [chi tiết](./F18-a4-a5-hop-nhat.md)
- **Vòng 27** — 2026-09-14 · hoàn tất phase A4 (ticket 01, 15, F82 — Claude làm theo yêu cầu chủ dự án) · **bản v3 + luật kiểm nhất quán là mặc định trên `main` (commit gộp `c418499`): 35/2/12, precision gộp 0,946, F1 0,833, precision `subtype_of` 0,658; mẫu xác nhận và kho chính qua ngưỡng 0,93 nhưng giống hệt nhau 217/217 quyết định vì temperature 0 (tái lập, không phải mẫu độc lập); F82 đóng; spec, ADR 0007, luồng 2a cập nhật; 296/296 test; bàn giao `task/to-chuc-prompt/` cho nhân viên** → [chi tiết](./F18-a4-a5-hop-nhat.md)
- **Xử lý bàn giao tổ chức prompt** — 2026-09-15 · [`task/to-chuc-prompt/`](../task/to-chuc-prompt/) tickets 01–04 xong trên `main`; 10 file đích giữ lịch sử `R100`, merge/vá dùng chung một prompt, 7 hash vàng không đổi, A4 tái dùng đủ bốn tài liệu, A3 khớp đủ bốn manifest, wheel đủ file, **299/299 test và 0 lời gọi mô hình** → [chi tiết](./F18-a4-a5-hop-nhat.md)
- **Vòng 28** — 2026-09-15 · kiểm thử đợt tổ chức prompt · F84 · **nhận: 7/7 hash vàng tính lại trên bản trước khi dời đều giống, 12/12 đột biến bị bắt, 299/299 test chặn mạng, A4 kho chính `reused=true` cả bốn tài liệu, A3 khớp bốn manifest, wheel đủ file; F84 (tài liệu luồng A3 còn trỏ thư mục phẳng, ngoài phạm vi ticket) đã sửa; đã commit, `.obsidian/` vào `.gitignore`** → [chi tiết](./F18-a4-a5-hop-nhat.md)
- **Vòng 30** — 2026-09-17 · kiểm thử đợt A6–A10 ([`task/a6-a8-tien-quyet/`](../task/a6-a8-tien-quyet/) vé 01–03, 06–10) · F85–F97 · **đã sửa F85–F95: 355/355 test; `naive-bayes` ra nhánh cụm; checkpoint không còn sinh version dở; F88 đã co chu trình hai node và `baocao-canhan` ra `roadmap_mode=requires`; F96–F97 chưa đổi** → [chi tiết](./F19-a6-a10-cum-chu-de-va-tien-quyet.md)
- **Vòng 31** — 2026-09-18 · kiểm chứng sau sửa F85–F95 · F98–F104 · **F85–F95 làm đúng ở mức code, mọi số khai khớp khi đo lại (355/355 test, γ = mật độ, `naive-bayes` ra nhánh cụm, viện dẫn đồng định nghĩa còn 0, 411/411 cặp pass phụ đảo hồ sơ thật, 64/85 đột biến bị bắt); chưa nhận vì F98 stage sau lấy sai chuỗi artifact khi đổi cấu hình qua lại, F104 vòng lần ngược đọc nhầm sang artifact khác tầng nên lỗi diễn ra lặng lẽ, F99 pass phụ rớt mạng rồi chạy tiếp thì bỏ hẳn các cặp còn lại, F100 ba tài liệu chưa chạy lại sau F88 (hai tài liệu vẫn `document_order_fallback` trong kho)** → [chi tiết](./F19-a6-a10-cum-chu-de-va-tien-quyet.md)
- **Bàn giao quan hệ mở 2a** — 2026-09-13 · [`task/a4-quan-he-mo-2a/`](../task/a4-quan-he-mo-2a/) tickets 02–06 xong; prompt/fixture `llm-v3`, arm riêng 4 tài liệu dùng 134 lời gọi thật, replay 0 lời gọi, 283 test xanh; **chờ reviewer làm ticket 01 và 07, ticket 08 vẫn khóa** → [chi tiết](./F18-a4-a5-hop-nhat.md)

---

# VÒNG 8 — Review đợt Symbol và công thức (2026-08-22)

**Tiêu chí mạnh nhất khớp chính xác**, và lần này kiểm được **trực tiếp** vì cả hai tài liệu còn giữ artifact
cũ lẫn mới. Chi tiết: [F15-b0-symbol-cong-thuc.md](./F15-b0-symbol-cong-thuc.md)

```
tài liệu một: 41 -> 41 chunk · 39/41 id GIỮ NGUYÊN · đúng 2 đổi
  261tok ['text','formula','list_item']  <- chunk chứa công thức khôi phục
   41tok ['figure']                      <- chunk chứa dấu hiệu hình
```

| # | Mức | Vấn đề | Bằng chứng |
|---|---|---|---|
| F34 | 🟡 Thấp | Cảnh báo **có kèm nguyên văn** không bao giờ được khử trùng lặp, kể cả khi nguyên văn trùng nhau | 300 tiêu đề giống hệt ⇒ **300 dòng** |

Hai tiêu chí trong ticket `05` tôi viết **mâu thuẫn nhau** khi nguyên văn trùng, và ticket không nói cách gỡ.
Sửa: khử trùng lặp theo **chuỗi đầy đủ** thay vì theo loại.

## Đã chạy lại

| | |
|---|---|
| Test | ✅ **97 passed**, exit 0 |
| Tài liệu hai | ✅ 263 `formula_refs` · 51 `table_refs` · **0** lệch span · **0** ref mồ côi |
| Section | ✅ 67 → 42 — đúng 23 gạch đầu dòng + hai cụm nối |
| **I9** / **I20** | ✅ 0/126 vi phạm · 0 chunk vượt 6000 |
| Ánh xạ Symbol | ✅ **2368** ký tự; chỉ **2** còn sót trong chunk, và **có cảnh báo** |
| Không thoái lui | ✅ cây 4 cấp · 5/5 nối câu · glyph 0 · 9 tham chiếu hình · caption `Hình 2` còn |

## Hai chỗ bản bàn giao mô tả thiếu chính xác

*"Còn hai glyph U+F0E7 không có Unicode tương đương"* — thực tế **12 mã phân biệt / 78 ký tự** trên mọi
trường, trong đó **2** lọt vào chunk text; hai con số đo hai thứ khác nhau. Và chúng **có** Unicode tương
đương ở dải `U+23A7–U+23AD` — tệp ánh xạ chuẩn của Adobe ra đời trước dải đó nên trỏ về vùng dùng riêng.
Giới hạn của **bảng**, không phải của Unicode.

---

# VÒNG 7 — Soi `xstk-ch3-1`, tài liệu thứ hai (2026-08-21)

Xác suất thống kê chương 3, **59 trang** — tài liệu đầu tiên có **bảng thật** (51 bảng). Nó chất vấn những
giả định mà `nhap-mon-ml` không chạm tới. Chi tiết: [F14-xstk-chat-luong-chunk.md](./F14-xstk-chat-luong-chunk.md)

## Kết luận một dòng

**Cơ chế chạy tốt, nội dung thì hỏng.** Mọi bất biến xanh, bảng hoạt động đúng ngay lần đầu, phân bố token
chuẩn. Nhưng **61% số chunk chứa ký tự hỏng mã** — và đó là toàn bộ chữ Hy Lạp của một giáo trình thống kê.

| # | Mức | Vấn đề | Số đo |
|---|---|---|---|
| **F30** | 🔴 **Nặng** | Chữ Hy Lạp hỏng mã — font Symbol rơi vào vùng dùng riêng thay vì Unicode thật | **653** ký tự trong **80/132** chunk |
| **F31** | 🟠 TB | 264 công thức bị bỏ, và **danh sách cảnh báo bị ngập** 264 dòng giống hệt nhau — hai cảnh báo thật bị chôn | 264/992 item = **27%** |
| **F32** | 🟠 TB | Gạch đầu dòng thành section; `Trong đó:` viết hoa lọt qua bộ lọc tiêu đề giả | **23/67** section |
| F33 | 🟡 Thấp | Khoảng trắng chèn giữa từ (`' T ổng thể'`) | chưa đo được tần suất |

## Phần chạy đúng

| | |
|---|---|
| **I9** vị trí ký tự | ✅ **0/132** vi phạm |
| **I20** trần cứng | ✅ 0 chunk vượt 6000 · 0 chunk cần `oversize_reason` |
| **Bảng** — lần đầu gặp dữ liệu thật | ✅ **51 bảng, 51 tham chiếu**, markdown dựng chuẩn |
| **Trần bảng phát huy tác dụng** | ✅ 2 chunk **535** và **525** token — luật cũ đã cắt đôi chúng |
| Phân bố token | ✅ trung vị **261**, max 535, 77/132 trong dải 256–511 |
| Cây section | ✅ 3 cấp, `section_path` dài 2–3 ở 131/132 chunk |

## Sửa gì trước

**Bảng tra Symbol → Unicode** — công nhỏ (một bảng ~190 mục, chuẩn công khai), giá trị rất lớn (sửa 61% số
chunk). Tôi đã thử giải mã bằng bảng gõ tay và phủ được **92%** ngay lần đầu; ba mẫu đọc lại đều **đúng hoàn
hảo**, kể cả `X ∼ N(μ; σ²)`.

**Gom cảnh báo trùng lặp** — công rất nhỏ, và nó làm hai cảnh báo chú thích mồ côi đang bị chôn nổi lên.

---

# VÒNG 6 — Review đợt ba trần token (2026-08-21)

**48/48 tiêu chí tick, 0 bỏ sót, mọi khẳng định đúng khi đo lại, không thoái lui qua năm đợt trước.**
Chi tiết: [F13-b0-tran-bang.md](./F13-b0-tran-bang.md)

| # | Mức | Vấn đề | Bằng chứng |
|---|---|---|---|
| F29 | 🟡 Thấp | **Cắt cưỡng bức xảy ra im lặng** khi bộ tách câu chạy tốt — thao tác phá hoại nhất lại là thao tác duy nhất không kêu | khối 13.903 tok, 3 mảnh cắt cưỡng bức, `structure_warnings` **rỗng** |

**Đây là lỗ hổng trong ticket tôi viết**, không phải trong việc họ làm — ticket `03` chỉ đòi lý do trên chunk,
không đòi cảnh báo ở mức tài liệu.

## Đã chạy lại, không đọc dấu tích

| | |
|---|---|
| Test | ✅ **85 passed**, exit 0 |
| **Tập chunk ID không đổi** | ✅ `726dce8b…d3d7a5` khớp **từng byte** với số tôi tự đo trước đợt |
| Ba trần + bump | ✅ 512 / 2048 / 6000 · `section-id-v6` · `adapter_version` giữ 6 |
| **Bảng 11 hàng** | ✅ **1 chunk** — ca mở đầu spec đã sửa |
| Câu dẫn gộp cùng bảng | ✅ `698tok ['text','table']` |
| Bảng nhỏ không hút văn xuôi | ✅ max 319, không gần 2048 |
| **I20** không ngoại lệ | ✅ khối 22.891 tok → 4 mảnh, max 5996 |
| CJK không khoảng trắng | ✅ cắt đúng tại 6000, ghép lại **y hệt gốc** |
| Không vỡ dấu tiếng Việt | ✅ **0** mảnh bắt đầu bằng dấu phụ |
| **I9** với mảnh cắt cưỡng bức | ✅ **0 vi phạm**, span liền mạch |
| Không thoái lui | ✅ char-span 0/41 · cây 4 cấp · 5/5 nối câu · 9/9 tham chiếu hình |

## Kiểm lại hai mục đợt trước báo đã xong

| | |
|---|---|
| **F27** `.gitignore` | ✅ đổi thành `/artifacts/` — `git check-ignore` xác nhận source **hết bị che**, thư mục output vẫn ignore |
| **F28** splitter chữ thường | ✅ cả ba ca cắt nhầm giờ ra 2 câu; hai ca hồi quy (Việt, CJK) vẫn đúng |

---

# VÒNG 5 — Review đợt bảng và tách câu (2026-08-21)

**Mọi khẳng định đều đúng khi đo lại, không thoái lui nào qua bốn đợt trước.** Chi tiết:
[F12-b0-bang-tach-cau.md](./F12-b0-bang-tach-cau.md)

| # | Mức | Vấn đề | Số đo |
|---|---|---|---|
| F28 | 🟡 Thấp | Bộ tách câu **chưa dùng luật chữ-thường** mà bộ nối câu qua trang đã dùng — cắt nhầm sau `…`, `U.S.A.`, `"!"` | **1** chỗ cắt nhầm / 18 block có chấm lửng |

**Xử lý:** ✅ Guard chữ-thường và ba regression test đã hoàn tất. Luật chữ cái viết hoa đơn được ghi nhận
riêng vì chưa có tiêu chí an toàn để phân biệt tên viết tắt với câu kết thúc thật.

Tác động hôm nay **bằng không** — bộ tách chưa từng chạy trên corpus này.

## Đã chạy lại, không đọc dấu tích

| | |
|---|---|
| Test | ✅ **71 passed**, exit 0 |
| **Tập chunk ID không đổi** | ✅ hash `726dce8b…d3d7a5` khớp, **và** hai chunk ID tôi ghi từ trước đợt vẫn còn |
| `table_refs` ngoài khoá băm | ✅ **41/41** id tái tạo đúng bằng công thức không có nó |
| Bộ tách câu | ✅ **10/10** ca, gồm ca hồi quy tiếng Việt |
| Bảng DOCX | ✅ `table_id` 64 hex · ref offset 50 → `\| Name \| Value \|` |
| **I18** mảnh bảng cùng id | ✅ bảng 41 hàng → 3 mảnh, **1** định danh |
| **I17** cảnh báo khi bó tay | ✅ có lý do **và** nêu rõ section |
| Bẫy `from_dict` | ✅ `ValueError` tường minh, không phải `TypeError` |
| Không thoái lui | ✅ char-span 0/41 · glyph 0 · cây 4 cấp · 5/5 nối câu · 9/9 tham chiếu hình |

## Một đính chính cho chính tôi

Vòng 3 tôi khuyên đổi marker `# ponytail:` sang `# NOTE:` vì *"không ai grep thì bằng không có dấu"*. **Sai** —
`ponytail` là quy ước thật của dự án, có hẳn một họ skill trong `.agents/skills/`. Tôi grep `src/` và `tests/`
rồi kết luận mà không grep `.agents/`. Lời khuyên đó sẽ **xoá mất thông tin**.

---

---

# VÒNG 4 — Review đợt B0 ảnh (2026-08-20)

**Đợt sạch nhất từ đầu dự án.** Mọi con số khai đều khớp chính xác khi đo lại, không thoái lui nào ở ba đợt
trước, và nhân viên **tìm ra một lỗi nghiêm trọng tôi bỏ sót** khi viết ticket. Chi tiết:
[F11-b0-anh.md](./F11-b0-anh.md)

| # | Mức | Vấn đề | Bằng chứng |
|---|---|---|---|
| **F27** | 🔴 **Nặng** | `.gitignore` mẫu `artifacts/` **che mất source code** — thiếu gạch chéo đầu nên khớp cả `src/…/infrastructure/artifacts/` | `git check-ignore` xác nhận **2 file**, tức toàn bộ package kho lưu trữ |

Repo **chưa từng commit gì**, nên lần `git add` đầu tiên sẽ âm thầm bỏ package này. Sửa: `/artifacts/`.

**Xử lý 2026-08-21:** ✅ Đã neo `/artifacts/`; source check trả exit 1 (không ignore), output root trả exit 0
(vẫn ignore). Không pattern cache nào khác trong file nhắm riêng một output root cùng tên package.

## Đã chạy lại, không đọc dấu tích

| | |
|---|---|
| Test | ✅ **51 passed**, exit 0 |
| **Mìn base64** | ✅ **0** node > 2000 ký tự (trước khi vá: 1 node **295.568** ký tự) |
| Ảnh | ✅ 9 PNG, **821.359 byte** khớp đến từng byte; tên file == sha256 nội dung |
| **`image_refs` ngoài khoá băm** | ✅ **41/41** `chunk_id` tái tạo đúng bằng công thức **không có** `image_refs` |
| Tham chiếu | ✅ 9/9 resolve, 0 nằm ngoài span, 0 ảnh mồ côi |
| `block_types` | ✅ **14 chunk có `list_item`** (trước: 0); cước chú vẫn đứng riêng 3/3 |
| Caption mồ côi `Hình 2` | ✅ có trong cả cây parse lẫn chunk |
| Không thoái lui | ✅ cây 4 cấp · 5/5 stitch · glyph 0 · char-span 0/41 |

---

# VÒNG 3 — Review `note.md` (2026-08-15)

Thay đổi **ngoài phạm vi mọi ticket**, tự phát hiện tự sửa, đụng vào `reading_order` — thứ mà gán section đứng
lên trên. Chi tiết: [F10-note-sua-reading-order.md](./F10-note-sua-reading-order.md)

## Kiểm chứng sau sửa — 2026-08-16

Chạy lại **đúng những probe đã bắt lỗi**, không đọc dấu tích.

| # | Cách kiểm | Kết quả |
|---|---|---|
| **F22** | Chạy lại đúng script đã bắt lỗi | ✅ `'các c c c là nhãn lớp'` → `'các c là nhãn lớp'` — **biến `c` còn** (trước: mất hẳn). Bốn ca cũ vẫn đúng |
| **F23** | Đọc thân test mới | ✅ khẳng định `_is_single_column` trả **`False`** cho hai khối text tách rời ngang, **và** `_repair_pdf_order` giữ nguyên thứ tự Docling |
| **F24** | Chạy lại thí nghiệm "nâng ảnh giữa +2pt" | ✅ thứ tự đúng; thử tiếp **+20pt** vẫn đúng; hai hàng rời nhau vẫn sắp trên-xuống |
| F25 | — | ⏸ hoãn, lý do đúng: thêm `page_end` đổi schema và cần provenance theo span |
| F26 | — | ⏸ giữ nguyên, kèm comment trong code |
| Test | `pytest` toàn bộ | ✅ **44 passed** (trước 42), exit 0 |
| Artifact v3 | đọc manifest | ✅ `adapter_version=4`, `algorithm_id` giữ `section-id-v3` — phân biệt đúng |
| I9 trên v3 | `full[start:end] == text` | ✅ **0/49** vi phạm |
| `153 + 12 + 5 = 170` | đếm lại | ✅ khớp |

**Khẳng định mạnh nhất trong note, và nó đúng:** `chunks.json` của v3 **giống hệt từng byte** v2, tập
`chunk_id` trùng khớp hoàn toàn. Nghĩa là ba bản sửa đóng lỗ hổng mà **không đổi một chunk nào** — đúng bản
chất của việc vá lỗi tiềm ẩn.

### Hai chỗ làm tốt hơn đề nghị

**1. Gom hàng dùng *neo*, không dùng *hàng xóm*.**
```
if rows and cls._same_row(rows[-1][0], node):   # so với khối ĐẦU của hàng
```
Tôi chỉ nói "gom thành hàng theo độ chồng dọc". Nếu so với khối **liền trước** thì sẽ bị nối bắc cầu — A chồng
B, B chồng C, nhưng A không chồng C, cả ba vẫn thành một hàng và trôi dần xuống. So với **khối neo** chặn được
điều đó. Tôi đã thử ca bắc cầu: hàng không bị trôi.

**2. `test_pdf_row_order_uses_left_position_despite_small_top_offsets`** chính là thí nghiệm F24 của tôi được
dựng thành test thường trực — ba ảnh có `top` lệch **ngược** thứ tự `left`. Cùng cách xử lý đúng như bản vá F1
vòng một: không chỉ sửa lỗi mà đóng luôn đường về.

### Một chỗ vụn

Comment ở `docling_parser.py` dùng marker `# ponytail:` để đánh dấu chỗ cần xem lại. Marker này xuất hiện
**đúng một lần** trong toàn repo và không thuộc quy ước nào (`TODO`, `FIXME`, `NOTE`, `HACK`). Một dấu mà
không ai grep thì bằng không có dấu. Đổi sang `# NOTE:` hoặc `# TODO:` là xong.

## Kết luận

**Đúng hướng, làm cẩn thận, số liệu trong note khớp chính xác với đo lại.** Nhưng hai chỗ phải sửa trước khi
ingest tài liệu thứ hai.

| # | Mức | Vấn đề | Bằng chứng |
|---|---|---|---|
| **F22** | 🔴 **Nặng** | Regex gộp glyph **xoá mất ký hiệu toán** khi nó đứng sau từ tiếng Việt kết thúc bằng cùng chữ cái | `'các c c c là nhãn lớp'` → `'các là nhãn lớp'` |
| **F23** | 🔴 **Nặng** | Guard đa cột **chưa từng chạy nhánh chặn**; `two-column.pdf` không kiểm được nó vì Docling gộp cả trang thành **1 node** | `_is_single_column` = `True` ở **21/21** trang đã thử |
| F24 | 🟠 TB | Phép sắp không có dung sai dọc — thứ tự trong một hàng ảnh là **may** | nâng ảnh giữa **2 point** ⇒ thứ tự đảo |
| F25 | 🟡 Thấp | Chunk khai thiếu trang — **hoãn 2026-08-16**, chưa consumer nào đọc `page` | **9/49 = 18%** (không phải 5) |
| F26 | 🟡 Thấp | `_is_single_column` quét toàn bộ cặp, bình phương theo số node/trang | 66 cặp/trang ở đây |

F22 nguy hiểm hơn vì nó **mất dữ liệu im lặng** — không cảnh báo, không dấu vết.

## Phần đúng — đã chạy lại, không đọc dấu tích

| | |
|---|---|
| Test | ✅ **42 passed**, exit 0 |
| `153 + 12 + 5 = 170` | ✅ khớp chính xác |
| **I9** trên v2 | ✅ **0/49** vi phạm |
| `order_index` đơn điệu | ✅ |
| 5 chỗ stitch | ✅ đủ 5, đọc lên thành câu tự nhiên, 0 mảnh mồ côi |
| Glyph lặp ≥3 lần còn sót | ✅ 0 |
| Sắp lại trang 7 | ✅ **đúng ngữ nghĩa** — `trong đó:` giờ đứng ngay sau công thức nó giải thích |
| Blast radius | ✅ chỉ **1 chunk** đổi section, và đổi theo hướng đúng |
| Độ an toàn của phép sắp | ✅ **20/20** trang đủ điều kiện nhưng chỉ **1** trang đổi ⇒ đồng ý với Docling ở 19/20 |

---

---

# VÒNG 2 — Soi artifact `nhap-mon-ml` (2026-08-15)

## Trạng thái xử lý — hoàn tất 2026-08-15

| # | Kết quả |
|---|---|
| F11 | ✅ Suy cấp từ đánh số; cây số có cấp 1→2→3, `a)`/`b)` ở cấp 4 |
| F12 | ✅ `structure_warnings` là danh sách lý do; có kiểm cây phẳng sau khi duyệt toàn cây |
| F13 | ✅ 8 hình dùng caption sạch, 1 hình rỗng bị bỏ; placeholder HTML về 0 |
| F14 | ✅ `trong đó:` bị hạ thành text và không còn trong danh sách section |
| F15 | ✅ Gộp glyph Latin lặp chỉ cho PDF; 29 node bẩn về 0, DOCX không bị đụng |
| F16 | ✅ Manifest parse ghi 170 item, 158 node giữ và số bỏ theo từng nhãn |
| F17 | ⏸ Giữ ngoài phạm vi theo spec: không thêm bộ tách từ chỉ để sửa hai heading front matter |
| F18 | ✅ Gộp leaf block trong section với `target_tokens=256` |
| F19 | ✅ Bỏ `min_tokens`; mọi tham số chunk còn lại đều ảnh hưởng hành vi/hash |
| F20 | ✅ Bảng dài cắt theo hàng, lặp header; ngoại lệ hàng quá dài có `oversize=true` |
| F21 | ✅ `adapter_version=2` tham gia parse hash; đổi version buộc parse lại |

Đối chiếu PDF thật sau sửa: **27 section, 50 chunk** (39 text chunk, median 248; 8 hình + 3 cước chú đứng
riêng), max 400 token, 0 chunk vượt trần, 0 placeholder, 0 glyph lặp, 0 span sai. Parse đầu mất 146,6 giây;
ingest lại dùng cache mất 0,74 giây. Full suite: **41 passed**.

Dữ liệu: `artifacts/parse_tree/nhap-mon-ml/v1` + `artifacts/chunks/nhap-mon-ml/v1`
Nguồn: `nhap_mon_hoc_may_va_khai_pha_du_lieu_5944.pdf` — 20 trang, 170 item Docling → 159 node → **28 section,
132 chunk, 9195 token**.

## Kết luận một dòng

**Code làm đúng thứ nó được đặc tả. Đặc tả đứng trên một giả định mà PDF thật không thoả** — rằng Docling biết
heading cấp mấy. Nó không biết. Kết quả là cây section phẳng hoàn toàn, và hệ thống **không hề báo**.

## Bảng phát hiện vòng 2

| # | Mức | Vấn đề | Số đo | Ở đâu |
|---|---|---|---|---|
| **F11** | 🔴 **Nặng** | **Cây section phẳng hoàn toàn** — Docling trả `level=1` cho cả 27 heading | `section_path` sâu 1: **132/132** chunk | [chi tiết](./F6-cay-section-phang.md) |
| **F12** | 🔴 **Nặng** | `structure_warning` **không bật** dù cây phẳng 100% — cờ chỉ bắt ca kẹp level | `"structure_warning": false` | [chi tiết](./F6-cay-section-phang.md) |
| **F13** | 🟠 TB | Thông báo lỗi của Docling nằm trong `text` và **đã thành chunk** | 9 chunk · 409 token · **4.4%** | [chi tiết](./F7-nhieu-trong-noi-dung.md) |
| **F14** | 🟠 TB | Heading giả `'trong đó:'` nuốt nội dung thật, cắt đôi window của `1.1.1` | 4 chunk · 257 token | [chi tiết](./F7-nhieu-trong-noi-dung.md) |
| **F15** | 🟠 TB | Ký hiệu toán bị **nhân bản glyph**: `P P P`, `x x x`, `{x x x1, x x x2}` | **29/132 = 22%** chunk | [chi tiết](./F7-nhieu-trong-noi-dung.md) |
| F16 | 🟡 Thấp | 11 node bị bỏ im lặng, gồm **1 `formula` mất hẳn**; không chỗ nào ghi lại | 170 → 159 | [chi tiết](./F8-chunk-vun-va-mat-mat-im-lang.md) |
| F17 | 🟡 Thấp | `MỤCLỤC`, `MỞĐẦU` mất dấu cách — lỗi Docling, không phải normalize | 2/27 heading | [chi tiết](./F8-chunk-vun-va-mat-mat-im-lang.md) |
| F18 | 🟡 Thấp | 20% chunk dưới `min_tokens`, nhỏ nhất **3 token** — `del min_tokens` là lỗ hổng chứ không phải quyết định tốt | 27/132 | [chi tiết](./F8-chunk-vun-va-mat-mat-im-lang.md) |
| **F19** | 🟠 TB | **Chunk nhỏ hơn ngân sách 8 lần**; cả 3 tham số cắt đều vô hiệu nhưng vẫn nằm trong `config_hash` | trung vị **62,5**/512 · **14%** | [chi tiết](./F9-kich-thuoc-chunk.md) |
| **F20** | 🟠 TB | **Bảng bỏ qua `max_tokens`** hoàn toàn — và không bất biến nào chặn | I1–I12 thiếu bài này | [chi tiết](./F9-kich-thuoc-chunk.md) |
| **F21** | 🟠 TB | **Sửa adapter không làm cây parse hết hạn** — `parser_config` chỉ gồm phiên bản thư viện, nên bản sửa im lặng không có tác dụng | `{"adapter": "docling:2.114.0"}` | dưới ↓ |

### F21 — sửa adapter xong chạy lại vẫn ra kết quả cũ

```python
# application/use_cases/ingest_document.py:74
parser_config = {"adapter": self.parser.identifier}
# infrastructure/parsing/docling_parser.py:28
return f"docling:{importlib.metadata.version('docling')}"
```

`parser_config_hash` phụ thuộc **duy nhất** vào phiên bản thư viện Docling. Sửa mã adapter (F13 hình, F15 gộp
glyph, F16 thống kê) mà thư viện giữ nguyên phiên bản ⇒ hash không đổi ⇒ `find_parse()` tìm thấy cây parse cũ
và **dùng lại**. Bản sửa không có tác dụng, và người sửa sẽ tưởng mình viết sai.

Chưa lộ vì đến giờ chưa ai sửa adapter sau khi đã ingest. Sẽ lộ **ngay ở ticket đầu tiên** của đợt này.

**Sửa:** adapter công bố thêm số phiên bản của riêng nó, tăng tay mỗi khi đổi cách dựng node, và số đó vào
`parser_config`. Đợt này phải tăng.

## Vì sao 25 test xanh mà vẫn ra thế này

Fixture ở seam thuần **dựng `DocumentTree` bằng tay** — và khi dựng tay thì ta tự gán `level=1,2,3` cho đúng ý
mình. Bất biến I2 đúng tuyệt đối *với đầu vào có phân tầng*. Không bài test nào hỏi câu **"nếu mọi level đều
bằng 1 thì sao"**, vì không ai nghĩ đó là chuyện có thể xảy ra.

Seam thuần kiểm **thuật toán** — thuật toán đúng.
Seam tích hợp kiểm **parse** — nhưng chỉ trên `smoke.pdf` do chính ta sinh ra, và ta sinh nó có heading phân cấp.

**Không seam nào kiểm giả định về đầu vào.** Đó là khoảng trống thật, và nó chỉ lộ ra khi đưa tài liệu thật vào.

## Thứ tự sửa — quan trọng

F11, F14, F15, F18 **đều làm đổi `chunk_id` và `section_id`**. Phải gộp thành **một đợt duy nhất**, bump
`algorithm_id` từ `section-id-v2` sang `v3` một lần. Làm bây giờ tốn 0 đồng vì chưa embed thật; làm sau khi có
vector store là một lần re-index toàn bộ.

| Bước | Việc | Vì sao trước |
|---|---|---|
| 1 | **F12** — cờ cảnh báo nhìn toàn cây | Làm trước để bước 2 có cách tự kiểm |
| 2 | **F11** — suy level từ đánh số tiêu đề | Nặng nhất; mọi thứ khác đứng trên nó |
| 3 | **F14** — lọc heading giả | Dùng chung luật đánh số của bước 2 |
| 4 | **F13** — figure: caption trước, strip placeholder | Độc lập, rẻ |
| 5 | **F15** — gộp glyph lặp | Cần test hai chiều: gộp `P P P`, **không** gộp `"ha ha ha"` |
| 6 | **F18 + F19** — luật gộp khối, đích **256** token | Cùng một luật giải quyết cả hai; chốt 3 câu hỏi thiết kế trước khi code |
| 7 | **F20** — cắt bảng theo hàng + bất biến **I15** `token_count <= max_tokens` | Độc lập, nhưng phải xong trước khi gặp tài liệu có bảng lớn |
| 8 | F16, F17 | Dọn khi tiện |

Sau bước 6, chạy lại `ingest` trên chính `nhap-mon-ml` và đối chiếu: cây phải có **3 cấp**, `CHƯƠNG 1` phải sở
hữu chunk qua các mục con, `trong đó:` phải biến mất khỏi danh sách section, và trung vị chunk phải quanh
**250 token** thay vì 62.

## Hai đính chính cho chính tôi

- **`del min_tokens`** — vòng 1 tôi xếp nó vào "làm tốt hơn yêu cầu". Sai. Trên dữ liệu thật nó là lỗ hổng
  (F18). Tôi khen vì chỉ nhìn code và fixture.
- **Docling ~1.8 giây/trang** — sai gấp 4. Tài liệu thật có hình: **7.2 giây/trang**. 500 trang là **~60 phút**,
  không phải 15. Bench vòng 1 chạy trên PDF tự sinh không có ảnh nào nên OCR không có gì để làm.

## Vẫn chạy đúng trên dữ liệu thật

| | |
|---|---|
| **I9** `full[start:end] == text` | ✅ 0/132 vi phạm |
| `chunk_id` / `section_id` trùng | ✅ 0 / 0 |
| **Bản vá F1** | ✅ xác nhận trên dữ liệu thật — một câu lặp 2 lần trong cùng section nhận 2 id khác nhau |
| Phủ trang | ✅ 20/20 |
| Tái dùng artifact | ✅ `parse_tree` không parse lại |

---

# VÒNG 1 — Review code (2026-08-14)

Phạm vi: toàn bộ 6 ticket trong [`task/b0-chunking/`](../task/b0-chunking/)

## Trạng thái xử lý — hoàn tất 2026-08-14

| # | Kết quả |
|---|---|
| F1 | ✅ `chunk_id` băm `parent_section_id`; bộ đếm occurrence được cô lập theo section và có regression test |
| F2 | ✅ I11 kiểm cả `section_id` và `parent_section_id` |
| F3 | ✅ Có test nội dung trùng trong cùng section và section anh em trùng tên |
| F4 | ✅ Test kiến trúc phân tích AST và chỉ cho phép stdlib trong domain |
| F5 | ✅ Chốt giữ heading ngoài `normalized_full_text`; đặc tả ghi rõ đây là không gian tọa độ leaf block |
| F6 | ✅ Sửa offset, dấu nối, công thức và cách tuần tự hoá hash trong tài liệu phân tích luồng |
| F7 | ✅ Test chặn mọi import trực tiếp từ application sang infrastructure |
| F8 | ✅ Test ranh giới câu có viết tắt, số thập phân và dấu `!`, `?` |
| F9 | ✅ `windows` chỉ được dựng ở application qua `assemble_windows` |
| F10 | ✅ `DocumentConverter` được khởi tạo lười và tái sử dụng trong một parser instance |

Các mô tả bên dưới được giữ lại làm lịch sử review. Kết quả kiểm thử sau sửa nằm ở cuối tài liệu này.

## Kiểm chứng độc lập — 2026-08-14

Bảng trên là bản tự báo. Dưới đây là kết quả tôi **chạy lại**, không đọc dấu tích.

| # | Cách kiểm | Kết quả |
|---|---|---|
| F1 | Chạy lại đúng probe đã bắt lỗi | ✅ id **giữ nguyên** (trước: đổi) |
| F2 | Đọc thân test I11 | ✅ có khẳng định `section_id` + `parent_section_id` |
| F3 | Đọc test mới | ✅ kiểm số id phân biệt bằng số chunk |
| F4 | Dựng thử `import torch` trong domain | ✅ trượt test |
| F5 | Probe `normalized_full_text` + đọc spec | ✅ hành vi và tài liệu đã khớp nhau |
| F6 | `grep` hash trong tài liệu; đối chiếu offset với code | ✅ hash gỡ hẳn; `[0,115)` `[116,199)` khớp **chính xác** |
| F7 | Đọc thân test | ✅ phân tích `ast`, không so khớp chuỗi |
| F8 | Đọc test mới | ✅ cắt khối có `TS.` và số thập phân |
| F9 | `grep` toàn bộ `src/` | ✅ chỉ còn một đường dựng `windows` |
| F10 | Đo lại thời gian test tích hợp | ✅ 27.6s → **23.2s** |

**Test: 25 passed** (trước 21), gồm 5 bài tích hợp chạy Docling thật.

Bài `test_duplicate_sibling_sections_do_not_share_chunk_occurrences` chính là probe F1 của tôi được dựng thành
test thường trực — nghĩa là lỗi đó không quay lại được nữa. Đây là cách xử lý đúng: không chỉ sửa lỗi mà còn
đóng đường về.

### Ba chỗ vụn còn sót — không chặn gì

**R1 — `doc/B0-phan-tich-luong.md` mục 8 ghi "dịch 70 ký tự", thực tế **69**.**
Số cũ còn sót từ hồi dấu phân cách là `\n\n` (2 ký tự). Đổi sang `\n` thì độ dịch thành
`len(đoạn chèn) + 1 = 69`. Mục 5 đã tính lại đúng, riêng con số ở mục 8 bị bỏ quên.

**R2 — Test kiến trúc vẫn bỏ qua import tương đối.**
`_imports()` có trả `level`, nhưng cả hai bài chỉ khẳng định khi `level == 0`. Dòng
`from ..application.ports import DocumentParser` đặt trong tầng miền có `level=2` nên **lọt lưới**. Đã kiểm
bằng `ast`. Hiếm gặp; muốn bịt thì phải phân giải đích của import tương đối rồi kiểm nó còn nằm trong `domain/`.

**R3 — Cache converter là theo instance**, nên `tests/integration/test_docling_parser.py` không hưởng lợi (mỗi
ca parametrize dựng `DoclingParser()` mới). Đường chạy thật thì đúng — `composition.py` dựng một parser và
`IngestDocument` giữ nó. Đó là lý do test tích hợp chỉ nhanh hơn 16% chứ không nhiều hơn.

## Kết luận ngắn

**Chất lượng tốt.** Không có ticket nào bị báo xong khống — tôi chạy lại toàn bộ và mọi thứ hoạt động thật.
Có **một lỗi thật** cần sửa trước khi sang T1, cộng vài lỗ hổng test và vài chỗ tài liệu lệch code.

Điều đáng nói: lỗi đó **không đọc code mà thấy được**. Cả 21 test đều xanh, cả 12 bất biến đều được khẳng
định. Tôi chỉ tìm ra nó khi dựng một tài liệu có **hai section anh em trùng tên** — thứ không có trong fixture
nào.

## Snapshot kiểm chứng lúc review — trước khi sửa

| Kiểm | Kết quả |
|---|---|
| `pytest tests/unit` | **16 passed** |
| `pytest tests/integration` | **5 passed** (27.6s, Docling chạy thật) |
| Docling trên Python 3.12 / Windows | **cài và chạy được** — rủi ro lớn nhất của pha này đã gỡ |
| Tokenizer Gemma offline | **vendored thật** tại `vendor/gemma/tokenizer.model` |
| `occurrence` chống đụng độ id | **hoạt động đúng** |
| `section_id` ổn định khi chèn đoạn | **hoạt động đúng** |
| Hai section anh em trùng tên | ❌ **rò rỉ định danh** — xem F1 |

## Bảng phát hiện lúc review

| # | Mức | Vấn đề | Ở đâu |
|---|---|---|---|
| **F1** | 🔴 **Cao** | Sửa nội dung ở section trùng tên thứ nhất làm **đổi `chunk_id`** ở section trùng tên thứ hai | [chi tiết](./F1-ro-ri-dinh-danh-giua-section-trung-ten.md) |
| F2 | 🟠 TB | I11 chỉ kiểm `chunk_id`, **không kiểm `section_id`** — ADR vá cả hai | [chi tiết](./F2-lo-hong-test.md) |
| F3 | 🟠 TB | `occurrence` **không có test nào** dù là cơ chế chống đụng độ id | [chi tiết](./F2-lo-hong-test.md) |
| F4 | 🟠 TB | Tên test **nói dối**: `..._does_not_import_project_or_external_packages` không hề kiểm external | [chi tiết](./F2-lo-hong-test.md) |
| F5 | 🟠 TB | `normalized_full_text` **loại bỏ heading** — lệch mô hình đã ghi trong tài liệu | [chi tiết](./F3-lech-giua-tai-lieu-va-code.md) |
| F6 | 🟠 TB | Hash trong `doc/B0-phan-tich-luong.md` **không khớp code** — *lỗi của tôi, không phải bạn* | [chi tiết](./F3-lech-giua-tai-lieu-va-code.md) |
| F7 | 🟡 Thấp | Test kiến trúc lọt lưới module chỉ import infrastructure | [chi tiết](./F2-lo-hong-test.md) |
| F8 | 🟡 Thấp | I7 test chỉ khẳng định `endswith(".")` trên fixture toàn dấu chấm | [chi tiết](./F2-lo-hong-test.md) |
| F9 | 🟡 Thấp | `windows` được tính **hai lần** bằng hai đoạn code khác nhau | [chi tiết](./F4-trung-lap-va-don-dep.md) |
| **F10** | 🟠 TB | `DocumentConverter` **dựng lại mỗi lần `parse()`** — lãng phí ~4.7s mỗi lời gọi | [chi tiết](./F5-hieu-nang-docling.md) |

## Làm tốt hơn yêu cầu — ghi nhận cụ thể

Đây không phải lời khen xã giao; bốn chỗ dưới đây là quyết định đúng mà ticket **không** yêu cầu:

**1. `min_tokens` được `del` kèm lời giải thích.**
```python
del min_tokens  # Short blocks deliberately remain one block; the threshold is manifest metadata.
```
Spec ghi `min_tokens` là tham số cấu hình, nhưng luật "khối ngắn giữ nguyên, không gộp" khiến nó **không có
hành vi nào**. Nhận ra điều đó và ghi rõ, thay vì viết một nhánh `if` vô nghĩa cho có, là dấu hiệu đã đọc spec
tới nơi.

**2. `tokenizer_id` chứa digest nội dung file model, không phải chuỗi phiên bản.**
```python
digest = hashlib.sha256(model_path.read_bytes()).hexdigest()[:12]
self._identifier = f"{model_id}:{digest}"
```
Ticket chỉ đòi "ghim phiên bản". Băm nội dung mạnh hơn hẳn: nếu ai đó thay file tokenizer mà giữ nguyên tên,
manifest **vẫn** phát hiện được và biết phải cắt lại chunk.

**3. Dùng `tree_depth` làm bằng chứng độc lập trước khi kẹp cấp heading.**
Spec §4.3 nói "heading con có cấp nhỏ hơn cha thì kẹp lại". Nhưng heading cấp 1 xuất hiện sau heading cấp 2
là **chuyện bình thường** — chương mới. Chỉ kẹp khi parser cho biết nó thật sự lồng bên trong (`tree_depth`
lớn hơn) là đúng hơn spec.

**4. `validate_doc_id` chặn đầu vào bậy trước khi gọi parser.**
Không có trong ticket. Nhưng `doc_id` đi thẳng vào mọi phép băm **và** vào đường dẫn file artifact — chặn sớm
là đúng.

## Kế hoạch review ban đầu — đã hoàn tất

1. **Sửa F1** — đổi `chunk_id` sang băm `section_id` thay vì `section_path`. Sửa ngay bây giờ là rẻ nhất:
   chưa có dữ liệu nào tồn tại, chưa bước nào phía sau tham chiếu tới `chunk_id`.
2. **Thêm ba test** cho F2, F3, F4 — chúng bảo vệ đúng thứ ADR 0001 tồn tại để bảo vệ.
3. **Chốt F5** — heading có nằm trong `normalized_full_text` hay không. Đây là quyết định của bạn, không phải
   lỗi; nhưng phải chốt và ghi lại, vì tài liệu và code đang nói hai chuyện khác nhau.
4. **Tôi sửa F6** — tài liệu phân tích luồng do tôi viết đang ghi sai hash.
5. F7, F8, F9 — dọn khi tiện, không chặn gì.

## Kiểm chứng sau sửa

- `pytest tests/unit -q`: **20 passed**.
- `pytest -q`: **25 passed** trong 35,4 giây, gồm **5 integration test** chạy Docling thật.
- Quét trailing whitespace trên toàn bộ tệp đã sửa: không phát hiện lỗi.
