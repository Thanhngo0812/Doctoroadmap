# v3 — Lộ trình chuẩn chỉ và đọc được: kế hoạch vé

> **Kiểm thử 2026-10-01 (Claude), commit `64fbc24`, `57a7d8d`, `1ed9c34`:**
> - **09c đạt.** Bất biến dãy học và cạnh đúng ở sáu tài liệu; doc-2 module gọn trong một mục 42/53. Phát hiện thêm doc-3, naive-bayes cũng
>   từng có tên "document>"; tên thay thế là tên khái niệm đầu module → vé mới [09d](09d-ten-module-khong-co-muc.md).
> - **Vé 12:**
>   - phần đầu đạt về mã;
>   - mất độ phủ do cửa sổ định nghĩa tôi đặc tả sai, đã sửa;
>   - cổng pilot so nhầm mốc;
>   - [việc còn lại](12-canh-theo-dinh-nghia-a8.md#sửa-đặc-tả-claude-2026-10-01-và-việc-còn-lại).

> **Kiểm thử 2026-09-28 (Claude), commit `9cc8752`:**
> - **Đạt:** 19 (Vertex trung tính với cache, dry-run trùng từng byte; embedding lệch 8,5×10⁻⁹), 05b, 11b.
> - **09b:** luật phần phụ đạt, tên doc-2 chưa đạt → vé mới [09c](09c-module-theo-cay-sua.md) (module chia theo cây sửa, bỏ nút gốc
>   "document>", tiêu đề chỉ có mã).
> - **Q7 doc-2 = 0,469 không do neo:**
>   - 13 cạnh ngoài phạm vi = 9 vào định lý chỉ có trong bài tập + 3 vào tính chất nói một câu + 1 từ node A3 rác;
>   - phần còn lại là A8 thiếu cạnh so với vàng: 18/44 cạnh trong dãy học không có đường đi.
> - **Không đọc 18/44 là lộ trình sai.** Bằng chứng v2-06: thêm cạnh chủ yếu thừa ràng buộc (T11), độ phủ bao đóng thưởng cạnh theo thứ tự
>   sách, vàng doc-2 chỉ 59% cạnh được cả hai người cùng chọn.

> **Cập nhật nhân viên 2026-09-27:** 10b đã commit riêng (`dc0cbce`). Mã và phép đo 05, 14, 16 đã xong, chờ reviewer nghiệm thu;
> xem [báo cáo](../../report/v3-05-14-16-ket-qua-2026-09-27.md). Vé 07 và 11 được mở đường sau 05; vé 15, 17 và T19 để sau theo chủ dự án.

> **Kiểm thử 2026-09-27 (Claude):** 16 **đạt** (0/1.705 tên đổi phân loại, dry-run A6–A8 tái dùng); 05 **đạt về mã** ("Số phức", "Đa
> thức" chỉ-nhắc là đúng — sách không dạy; hai lỗi Q6 mới là nút chỉ-nhắc nằm tạm cuối dãy tới vé 07); 14 lớp cấu trúc **đạt**, lớp nhãn
> bằng mô hình **chưa đạt** — doc-2 cây cũ có 104 mục bài giảng bị gắn đề cương, làm 42 khái niệm mất trạng thái được dạy → vé mới
> [14b](14b-nhan-vai-tro-chia-lo.md). Vé 06, 07 làm được ngay; nghiệm thu 07 trên doc-2 chờ 14b.

> **Kiểm thử 2026-09-26 (Claude):** 01 đạt; 03 đạt, hai điều kiện chuyển sang vé 04; 10 đạt phần đề cử, còn áp tự động thì chưa
> đạt (27/44 phán `same` mới đúng, đại diện có thể là nút chỉ-nhắc, gỡ chu trình sau gộp xoá nhầm cạnh) → vé mới
> [10b](10b-danh-tinh-xac-minh.md). **Không chạy `roadmap --allow-spend` để xuất bản lộ trình trước khi 10b xong.** Báo cáo của nhân
> viên: [01/03/10](../../report/v3-01-03-10-ket-qua-2026-09-26.md).
> **Cập nhật:** 10b **đạt** (Claude đọc các cặp lệch, bỏ cổng số theo chủ trương tăng tốc, chạy ba tài liệu: 0 gộp sai rõ; doc-1 Q6
> về 1/39). Chờ nhân viên commit mã 10b; vé 07 chỉ còn chờ vé 05.

> **Rà soát đa ngôn ngữ 2026-09-26 (Claude, theo chủ dự án):** tài liệu có thể thuộc bất kỳ ngôn ngữ nào; spec v3 thêm mục "Nguyên tắc:
> tài liệu đa ngôn ngữ" kèm bảng các chỗ đang vi phạm. Vé mới: 14, 15, 16, 17, 02b, T19. Phần từ khoá của vé 03/04 được thay ở vé 14;
> vé 05, 09, 11, 12, 13 có thêm mục sửa. Nặng nhất là vé 16: tên chữ không Latin đang bị coi là ký hiệu, nên A3 loại gần hết khái niệm.

**Nguồn chân lý:** [spec v3](../../doc/v3-lo-trinh-doc-duoc-spec.md) · **Căn cứ:** [báo cáo đánh giá 2026-09-26](../../report/danh-gia-lo-trinh-2026-09-26.md)

**Quy trình (chủ dự án chốt 2026-09-26):** tôi viết spec và vé → chủ dự án giao nhân viên cài đặt → tôi kiểm thử theo mục
"Nghiệm thu" của từng vé và nghiên cứu tiếp. Nhân viên đọc spec v3 trước khi làm vé nào.

## Luật chung cho người làm

- **Tăng tốc (chủ dự án 2026-09-26):** số đo trong vé là thông tin cho reviewer, không phải cổng buộc dừng. Chạy đủ phần việc của vé
  (trong trần chi được duyệt) rồi báo số; reviewer đọc và quyết đạt hay chưa.
- Viết test đỏ trước cho bất biến của vé; test phải được thấy đỏ trên mã cũ.
- Sửa `doc/spec-addendum.md`, `CONTEXT.md` và spec liên quan **cùng commit** với mã.
- Mọi lệnh gọi mô hình đi qua `SpendGuard`; chạy `--allow-spend` trên tài liệu có artifact cũ chỉ sau khi chạy không cờ (hoặc
  `--dry-run` khi có vé 01) để biết stage nào định chi. Sự cố 2026-09-26: quên bước này tốn ≈ 0,64 USD.
- Không mở tập giữ lại (`artifacts/a8-gold/xstk-ch3-1-chuong-10-13-*`, `doc-4-chuong-8-vang.json`); không sửa bộ vàng đóng băng.
- Chỉ dùng `gemini-3.1-flash-lite`, temperature 0. Không đẩy nội dung sách ra dịch vụ nào khác Gemini.
- `artifacts/` và `tmp/` không commit.
- **Tài liệu đa ngôn ngữ** (spec v3, mục Nguyên tắc): không thêm danh sách từ hay regex của một ngôn ngữ vào luồng; dùng bằng chứng cấu
  trúc trong tài liệu hoặc một lời gọi mô hình với tập nhãn đóng. Test của vé chạm luật văn bản có fixture ở ít nhất hai ngôn ngữ ngoài
  vi/en (một chữ viết không Latin, một chữ viết không cách từ). Không vì sửa luật mà bắt chạy lại stage tốn tiền trên tài liệu hiện có:
  chạy `--dry-run` trên sáu tài liệu trước và sau.

## Vé

| vé | việc | pha | ai | phụ thuộc | chi phí mô hình |
|---|---|---|---|---|---|
| 01 | chạy thử có dự toán (R10) | CLI | nhân viên | — | 0 |
| 02 | bảng kiểm đọc được (R11) | kiểm thử | **tôi** | — | 0 |
| 02b | bảng kiểm không phụ thuộc ngôn ngữ (R11 sửa) | kiểm thử | **tôi** | 14 | 0 |
| 03 | vai trò vùng văn bản (R1) | A2 | nhân viên | — | 0 |
| 04 | cấu trúc mục kiểu sách toán (R2) | A2 | nhân viên | 03 | 0 |
| 05 | neo và vị trí chỉ từ vùng dạy (R3) | A9' | nhân viên | 03 | chạy lại neo ≈ 0,5 USD toàn kho phát triển |
| 05b | câu ứng viên của bước neo ưu tiên khối mang tên khái niệm; câu xem trước không phải nơi dạy (R3 bổ sung) — **ưu tiên** | A9' | nhân viên | 05 | chạy lại neo phần đổi ≈ 0,1–0,4 USD |
| 06 | cạnh không lấy căn cứ từ đề cương/lời nói đầu (R4) | A9 | nhân viên | 03 | 0 |
| 07 | dãy học chỉ gồm khái niệm được dạy (R5) | A10 | nhân viên | 05, 10b; nghiệm thu doc-2 chờ 14b | 0 |
| 08 | hiển thị tiên quyết rút gọn và phụ thuộc cấp module (R6) | A10, CLI | nhân viên | 07 | 0 |
| 09 | tên module theo nội dung (R7) | A10/A11 | nhân viên | 03 | ≈ 0,05 USD / tài liệu |
| 09b | tên module: phần phụ có nghĩa, tên nền từ cây đã sửa (R7 bổ sung) | A10 | nhân viên | 09 | ≈ 0,01 USD |
| 09c | module chia theo cây đã sửa; tên nền không lấy nút gốc, tiêu đề chỉ có mã hay nhãn đầu đoạn (R7 bổ sung lần 2) | A10 | nhân viên | 09b | ≈ 0,01 USD |
| 09d | module không có tiêu đề mục chung: sinh tên từ tên khái niệm (R7, nhánh chưa cài từ vé 09) | A10 | nhân viên | 09c | < 0,01 USD |
| 10 | danh tính mở rộng (R8) | A9'' | nhân viên | — | ≈ 0,05 USD / tài liệu |
| 10b | xác minh quan hệ danh tính, đại diện được dạy, gỡ chu trình theo vị trí đại diện (R8b) | A9'' | nhân viên | 10 | ≈ 0,02 USD xác minh (+ ≈ 0,28 USD lượt 1 nếu kho mặc định chưa có) |
| 11 | tên khái niệm có nội dung (R9) | sau A5 | nhân viên | 05 | ≈ 0,02 USD / tài liệu |
| 11b | tên khái niệm: căn cứ rộng hơn dòng nhãn, chống trùng tên (R9 bổ sung) | sau danh tính | nhân viên | 11 | ≈ 0,005 USD |
| 12 | cạnh theo định nghĩa ở A8 (R12; cập nhật 2026-09-28: cửa sổ định nghĩa, câu trích kiểm bằng mã) — **làm trước T10** | A8 | nhân viên | 03–11 | ≈ 1–7 USD / tài liệu, dự toán bằng dry-run — **chủ dự án duyệt trước khi chạy** |
| 13 | trích mệnh đề có tên ở A3 (R13) | A3 | nhân viên | sau vé 07 v2 | chạy lại A3–A10; cần kế hoạch ánh xạ vàng |
| 14 | vai trò vùng và cấu trúc mục không phụ thuộc ngôn ngữ (R1, R2 viết lại) | A2 | nhân viên | 03; làm tiếp trên vé 04 | ≈ 0,001–0,01 USD / tài liệu |
| 14b | nhãn vai trò chia lô theo chương, luật kiểm cấu trúc, chuyển vai trò sang chunk cũ (R1 bổ sung) — **ưu tiên** | A2 | nhân viên | 14 | ≈ 0,005–0,02 USD / tài liệu + chạy lại neo doc-2 ≈ 0,05 USD |
| 15 | ngôn ngữ tài liệu bất kỳ ở A5 (R14) | A5 | nhân viên | — | ≈ 0,0001 USD / tài liệu |
| 16 | tên, ký hiệu và tìm nhắc tên không phụ thuộc chữ viết (R15) — **ưu tiên** | A3, A4, A6 | nhân viên | — | 0 |
| 17 | tiền tố danh tính từ bằng chứng trong tài liệu (R16) | A9'' | nhân viên | 10b | ≈ 0,01 USD / tài liệu |
| 18 | cạnh ngược thứ tự sách không ép dãy học (R17) | A10 | nhân viên | — (làm cùng 07 được) | 0 |
| 19 | gọi mô hình qua Vertex AI để dùng credit Google Cloud (hạ tầng) | LLM | nhân viên | — | thử < 0,01 USD; chi qua Vertex tính vào trần dự án 50 USD (chủ dự án quyết 2026-09-28) |
| T19 | cung cấp tài liệu thật ngôn ngữ thứ ba: một chữ viết không Latin (ví dụ tiếng Trung, Nga) và một chữ Latin ngoài vi/en (ví dụ tiếng Pháp) | kiểm thử | **chủ dự án** | — | 0 |
| T10 · 07 v2 | khoá cấu hình và chạy tập giữ lại một lần — [giao thức](T10-07v2-giao-thuc-tap-giu-lai.md) soạn xong 2026-10-01, chưa khoá; mức tài liệu phát triển điền 2026-10-03; bảng khoá sinh bằng `scripts/khoa-cau-hinh/tao_bang.py`, chấm bằng `scripts/doc-lo-trinh/cham_tap_giu_lai.py` | kiểm thử | tôi (soạn, chấm) · nhân viên (chạy) · **chủ dự án** (duyệt khoá, chi, T14) | 12, 09d | ước 15–40 USD, dry-run theo bậc |
| T10b | chạy tập giữ lại một lần theo bậc, trần 50 USD — [vé](T10b-chay-tap-giu-lai.md) | kiểm thử | nhân viên · **chủ dự án** (duyệt chi, T14) | T10 đã khoá 2026-10-03 | ước 15–40 USD |
| T10a | lệnh chuẩn cho lượt tập giữ lại: `label-roles --transfer-from-chunks-version`, `roadmap --stop-after identity`, bảng duyệt danh tính không đọc vàng — [vé](T10a-cli-tap-giu-lai.md) | CLI | nhân viên | — (song song pass phụ vé 12) | 0 |
| 20 | tệp lộ trình giữ node hình/bảng và thực thể bối cảnh (`non_learnable_nodes`) để cạnh mở `illustrates`/`tabulates` không bị treo — [vé](20-giu-node-media-trong-lo-trinh.md) | A10 | nhân viên | — (trước T10) | 0 |
| 21 | "Tổng quan môn học" chỉ gồm khái niệm của đề cương/lời nói đầu; khái niệm chỉ-nhắc có căn cứ trong bài thì gắn vào module; nhóm bài tập/hành chính/cuối sách tách riêng — [vé](21-tong-quan-mon-hoc.md) | A10 | nhân viên | — (cùng lượt chạy lại A10 của vé 20, trước T10) | 0 |
| 22 | gọi mô hình song song cấu hình được (≥ 100): bộ giới hạn chung theo token/phút và 429, pass phụ "hỏi trước, chốt theo thứ tự" (kết quả y hệt tuần tự), điểm lưu theo lô — [vé](22-song-song-cau-hinh-duoc.md), [nghiên cứu](../../report/nghien-cuu-song-song-cao-2026-10-02.md) | hạ tầng | nhân viên | — (trước khi chạy tiếp doc-2 và T10) | 0 |
| 23 | tên module chỉ có mã mục ("6B", "Chapter 7") thì thêm tên khái niệm nguyên vẹn — [vé](23-ten-module-chi-co-ma.md) | tên module | nhân viên | — (làm trước khoá T10; nghiệm thu đạt 2026-10-03) | 0,0007 USD |
| T15-dev | chấm mù đối đầu cạnh dư đồ thị cũ và mới trên hai chương vàng phát triển — bộ tạo/chấm `scripts/cham-mu/tao_bang_v3.py`, `cham_bang_v3.py` (seed 20261001, ghi trước). **Bảng đã sinh 2026-10-01**: `artifacts/a8-gold/cham-mu-v3-doc-{1,2}.xlsx` (35 + 22 cặp), từ pass chính + pilot lượt ba sửa vì đồ thị cuối chưa có; chấm lại theo đồ thị cuối bằng `--moi-cuoi` | kiểm thử | tôi (sinh bảng, chấm) · **hai người chấm** do chủ dự án xếp | đồ thị cuối vé 12 | 0 USD, ≈ 1 giờ/người |

Có thể làm song song: 01, 03, 10 ngay; 04, 05, 06, 09 sau 03; 10b sau 10; 07 sau 05 và 10b; 08 sau 07; 11 sau 05; 16, 15 ngay; 14 làm
tiếp ngay trên vé 04 đang dở; 17 sau 10b. Phần R16 đi cùng vé 05, 12, 13. Chạy thử tài liệu T19 sau 14–17.

**Cập nhật nhân viên 2026-09-27:** vé 14b đã triển khai và đo trên doc-2, nhap-mon-ml, doc-3; [báo cáo](../../report/v3-14b-ket-qua-2026-09-27.md), chờ reviewer nghiệm thu.

**Cập nhật 2026-10-03 — xong pha A:**
- **Vé 12:** pass phụ doc-2 xong (9.513/9.513 cặp); sáu tài liệu đủ A9 → A10 → tên module.
  - Claude tái tạo mọi số và nghiệm thu phần chạy và đo: **đạt** (mục cuối [vé 12](12-canh-theo-dinh-nghia-a8.md)).
  - Đánh đổi: Q7b khoảng 0,87 ở cả hai chương vàng, 0 cạnh ngược; nhưng độ phủ thấp (Q7 doc-1 0,667, doc-2 0,395).
  - **Chủ dự án quyết** có khoá cấu hình này cho tập giữ lại không. Claude đề nghị khoá.
- **Vé 20, 21, T10a:** Claude nghiệm thu **đạt** (test đỏ trước sửa; đếm lại độc lập; kiểm tương đương 11/11 tầng; đột biến bị bắt).
  - Ba mục hành chính trong Tổng quan doc-1: nguyên nhân là neo C8 không hỏi `kind` với node chỉ có căn cứ ngoài nội dung, không phải nhãn
    vùng. Ghi giới hạn đã biết, đưa vào hướng v4.
- **Vé 23** (tên module chỉ có mã): làm trước khoá; Claude nghiệm thu **đạt** (doc-2: 5 tên chỉ có mã → 0; chi 0,0007 USD).
- **Giao thức T10/07 v2:** đã điền mức tài liệu phát triển và thông số vé 12. Bảng khoá nháp: cả 10 `prompt_hash` khớp lượt nghiệm thu.
- **Chi vé 12, cộng mọi sổ:** 36,59 USD theo usage; cận trên 38,98 USD nếu tính cả lời gọi bị ngắt.
- **Pha B bắt đầu:** chủ dự án duyệt bảng khoá (commit `2f03781`), nhận đánh đổi vé 12, trần 50 USD. Nhân viên chạy theo
  [T10b](T10b-chay-tap-giu-lai.md); chủ dự án duyệt chi từng bậc và T14; Claude chấm ở bậc 5.
  - **Bậc 1 xong** (2026-10-03, chi 0,036 USD). Claude kiểm số đếm và manifest, không đọc nội dung: cùng `source_hash`; doc-4 đọc bằng
    `pypdfium2` + `vn-textbook`; chuyển vai trò khớp 126/126 (xstk v2 → v5) và 671/671 (doc-4 v3 → v6); `load_role_chunks` của chuỗi sẽ
    lấy đúng v5/v6. **Theo dõi khi chấm:** xstk có 48/126 chunk (38%) nhãn `de_cuong`, cao hơn mọi tài liệu phát triển (doc-6 26%, còn
    lại ≤ 2%). Nếu A2 gán nhầm nội dung thành đề cương, bậc 5 sẽ thấy nhiều cạnh vàng xstk "ngoài phạm vi". Không sửa giữa lượt.
  - **Bậc 2 xong** (chi 0,94 USD, luỹ kế 0,97 USD + khoản chưa quan sát từ một lượt doc-4 bị ngắt). Claude kiểm manifest: chuỗi clusters →
    danh tính đúng prompt_hash bảng khoá; provenance dùng chunks gắn A3 (v2/v3), neo và danh tính dùng bản có vai trò (v5/v6), giống mẫu
    doc-1 phát triển. Danh tính: xstk 6 `same`; doc-4 6 `same` + 1 `sense_split`.
  - **Bậc 2b:** Claude sinh bảng T14 không vàng (không mở nội dung) ở `tmp/duyet-danh-tinh-giu-lai/`: xstk 6 cặp, doc-4 7 cặp. Chủ dự án đã duyệt đủ 13 cặp
    (xstk: 5 gộp, 1 không gộp; doc-4: 4 gộp, 2 không gộp, 1 hai nghĩa; 0 "không chắc"). JSON: `tmp/duyet-danh-tinh-giu-lai/t14-<doc>.json`.
  - **Bậc 3 dừng ở cổng ngân sách** (luỹ kế 6,04 USD): xstk xong lộ trình (v46); doc-4 xong A8 chính (v7). Pass phụ doc-4 dry-run 22.142
    cặp, 44.284 lời gọi, ≈ 68,9 USD trước retry, vượt trần 50 USD. Giao thức ước sai (15–40 USD) vì doc-4 cả cuốn. Chờ chủ dự án quyết
    nâng trần (đường sạch) hay dừng doc-4. Không cắt phạm vi pass phụ: đổi cấu hình giữa lượt là "không sạch".
    **Chủ dự án chọn nâng trần cả lượt lên 90 USD**; nhân viên chạy pass phụ doc-4 tới hết lộ trình, dừng nếu chi thật vượt 90 USD.

**Hiện tại (2026-10-02):**
- **Đã xong:** 01, 02, 02b, 03, 05, 05b, 06, 07, 08, 09, 09c, 10, 10b, 11, 11b, 14, 14b, 16, 18, 19; 09b đạt phần luật. Thêm 2026-10-03:
  09d, 20, 21, 22, T10a; vé 12 xong phần chạy và đo.
- **Vé 12 đang dở:**
  - Mã phần đầu đạt.
  - Pass chính mất độ phủ vì cửa sổ định nghĩa **tôi đặc tả sai**: thiếu các câu giả thiết đứng trước câu neo. Đặc tả đã sửa thành −4…+2.
  - Cổng pilot so nhầm mốc; mốc đúng là đồ thị cuối luồng cũ sau rút gọn. Chấm lại 0 USD cho thấy với cửa sổ sửa, doc-1 ngang luồng cũ về
    độ chính xác.
- **Cập nhật 2026-10-01 (kiểm thử lượt cửa sổ −4…+2, mã chưa commit):**
  - Kết quả đạt mốc: doc-1 bao đóng P 108/127, R 108/131, so với luồng cũ 106/129, 106/131.
  - Còn ba sửa nhỏ trước khi chi ≈ 31 USD cho pass phụ đầy đủ: so câu trích sau khi gộp khoảng trắng, gộp hai thứ tự bớt ngặt, câu trích phải
    từ chính định nghĩa.
  - 09d: cơ chế đạt, nhưng tên ghép liền mẩu tên → đổi sang chọn tên khái niệm nguyên vẹn rồi nối " · ".
- **Cập nhật 2026-10-01 (kiểm thử lượt ba sửa):**
  - Hợp đồng A8 **chốt**: trên hai chương vàng ngang luồng cũ trong nhiễu đo (mọi khoảng tin cậy Wilson chồng nhau).
  - **Cho chạy pass phụ đầy đủ.**
  - 09d **đạt**.
- **Cập nhật 2026-10-02:**
  - Chấm mù T15-dev: luồng mới ngang luồng cũ, 0 cạnh ngược.
  - Vé 22 (song song cấu hình được, giảm theo thế hệ) đã commit.
  - doc-2 chạy tiếp pass phụ bằng mã mới.
- **Lộ trình còn lại, theo thứ tự** (rà quy trình 2026-10-02):
  - **Pha A — xong tài liệu phát triển** (≈ 0 USD ngoài phần doc-2 còn lại):
    1. Nhân viên: doc-2 xong pass phụ → A9 → tên khái niệm → A10 → tên module. Báo cáo cuối vé 12 gồm:
       - tổng chi mọi sổ (một con số);
       - 429 theo thế hệ, lời gọi/phút;
       - cạnh cứng/mềm;
       - `cham_tap_giu_lai.py` doc-1, doc-2;
       - `kiem_doc_duoc.py` sáu tài liệu.
    2. Nhân viên: vé **20** và **21** (A10, 0 USD), chạy lại A10 và tên module sáu tài liệu trên kho cuối.
    3. Nhân viên: vé **T10a**, gồm **kiểm tương đương chuỗi**: lệnh `roadmap` phải "tái dùng" mọi stage trên artifact nghiệm thu.
    4. Nhân viên: commit hết, cây sạch.
    5. Tôi: nghiệm thu vé 12/20/21/22/T10a:
       - đọc lộ trình sáu tài liệu;
       - chấm lại chấm mù doc-2 theo đồ thị cuối (`cham_bang_v3.py --moi-cuoi`);
       - điền "mức tài liệu phát triển" vào [giao thức](T10-07v2-giao-thuc-tap-giu-lai.md).
  - **Pha B — khoá và tập giữ lại** (ước 15–40 USD, chạy một lần):
    1. Tôi sinh bảng khoá; chủ dự án duyệt và đặt trần chi.
    2. Nhân viên: bậc 1 (vai trò, chuyển sang chunks cũ) và bậc 2 (tới danh tính), dry-run trước, chủ dự án duyệt chi.
    3. Chủ dự án: T14, duyệt mọi cặp danh tính không "different" (không cần mở vàng).
    4. Nhân viên: bậc 3 (A8 → A10), dry-run trước, chủ dự án duyệt chi.
    5. Tôi: chấm theo giao thức, đọc hai lộ trình, báo kết quả kể cả xấu. Chấm người (T15, T12, T16, T17) nếu chủ dự án xếp được.
  - **Pha C — sau tập giữ lại:**
    - báo cáo tổng kết v3;
    - thử với 3–5 sinh viên học một chương;
    - rồi tới vé 13 (trích mệnh đề A3), tạo bài giảng (dùng cạnh mở, hình/bảng, cạnh công cụ), tích hợp web (giới hạn chung nhiều worker,
      hàng đợi), về Gemini API khi hết credit (chỉ đổi `.env`), thử Flex/Batch để giảm 50% chi phí, T19.
- **Luật quy trình bổ sung (rà 2026-10-02):**
  - Đổi hợp đồng có tốn tiền thì tôi **phát lại 0 USD trên nhật ký cũ trước**. Bài học: cửa sổ "+2 câu" của vé 12 tôi đặc tả mà chưa đo.
  - Nhân viên **commit trước khi báo kiểm thử**.
  - Đường chạy đo nghiệm thu phải là đường chạy sản phẩm (kiểm tương đương).
  - Mỗi báo cáo tốn tiền ghi một **tổng chi duy nhất** cộng mọi sổ.
- **Ngân sách:** chủ dự án đã duyệt ngân sách lớn (credit 300 USD).
  - Đã chi ≈ 31,1 USD tới lượt ba sửa, ước theo sổ token, chưa phải hoá đơn.
  - Dự kiến: pass phụ ≈ 31 USD và tập giữ lại 15–40 USD, tổng cuối ≈ 77–102 USD.
  - Cập nhật 2026-10-03: sổ kho cuối (pass phụ đầy đủ và các bước sau) 27,66 USD; cả vé 12 cộng mọi sổ 36,59 USD (cận trên 38,98). Số
    chốt là hoá đơn Google Cloud.
  - Vẫn chỉ dùng `gemini-3.1-flash-lite`.
- **Kho chính:** sáu tài liệu đã có A6 → A7 → neo → danh tính → A8 pass chính v5 (doc-1 v38–42, doc-2 v30–34…); pass phụ chưa chạy.
- **Không đề xuất dựng lại doc-2 từ A3** trên cây mục mới:
  - ID node đổi thì bộ vàng đóng băng không chấm được nếu chưa có kế hoạch ánh xạ (xem vé 13);
  - hệ quả của cây vỡ đã được xử lý ở tầng hiển thị (14b, 09b, 09c).
- **Hoãn theo chủ dự án:** 15, 17, T19.

## Hướng v4 (dự kiến, sau tập giữ lại) — nghiên cứu theo lỗi, không rải đều mọi khâu

**Nguyên tắc số một của đợt sửa tới (chủ dự án, 2026-10-03):** đây là ứng dụng phục vụ người dùng, nên phải **tối ưu thời gian tạo lộ
trình và tiền cho mỗi tài liệu** trước hết.
- Mỗi spec và vé v4 ghi và đo hai số, trước và sau sửa, trên cùng bộ tài liệu phát triển: **phút/cuốn** và **USD/cuốn**.
- Chất lượng vẫn đo trên vàng phát triển như v3. Cách giảm tiền hay thời gian nào làm tụt chất lượng thì báo đánh đổi bằng số, chủ
  dự án quyết; không hạ chất lượng ngầm.
- Mức v3 để so:
  - A1 parse khoảng 7,2 giây/trang ở máy này, tức khoảng 48 phút cho sách 400 trang;
  - pass phụ A8 hỏi gần như mọi cặp nên chi tăng theo bình phương số khái niệm: doc-4 (khoảng 616 khái niệm) 22.142 cặp, 44.284 lời
    gọi, khoảng 69 USD; doc-2 9.513 cặp, 18.945 lời gọi. Chạy mất nhiều giờ vì giới hạn 429;
  - kho đánh giá cuối vé 12 (pass phụ sáu tài liệu và các bước sau): 28,6 nghìn lời gọi, 27,7 USD.
- Hướng đã có bằng chứng: lọc cặp trước khi hỏi pass phụ, hỏi một chiều khi chắc chiều, Batch/Flex (giảm 50%), song song cao trên
  Developer API (vé 22), tăng tốc A1 (nghiên cứu dở, tạm ngưng 2026-10-02).
- Mục tiêu số cụ thể (USD/cuốn, phút/cuốn) chờ chủ dự án chốt. Không áp nguyên tắc này vào lượt tập giữ lại v3 đang chạy (đã khoá).

Cách làm:
1. Lấy kết quả tập giữ lại và tài liệu phát triển, truy **mỗi lỗi người học nhìn thấy về khâu gây ra nó**.
2. Xếp theo tác động lên người học và mức giảm phút/USD mỗi cuốn, nhân bằng chứng, chia chi phí làm.
3. Mỗi vòng chỉ sửa một–hai khâu, đo 0 USD trước khi chi.

Ứng viên đã có bằng chứng (Claude, 2026-10-02):

| khâu | vấn đề | bằng chứng |
|---|---|---|
| A1 | công thức thành `[formula]`, mô hình phán định nghĩa mà không thấy toán | doc-1: 80/199 câu neo (40%), 141/199 cửa sổ định nghĩa (71%) chứa `[formula]`; nhap-mon-ml, doc-3 gần 0. Hệ quả đã thấy: tên "Định lý 6" lấy từ giả thiết vì kết luận là `[formula]` |
| A1/A2 | trang mục lục mất; bộ tách câu gộp "(a)…(b)" trong định nghĩa liệt kê | doc-2: 6 tiêu đề chỉ có mã (09c); luật thử ở A9 bắt nhầm "Hệ sinh → Cơ sở" vì (a)/(b) chung một câu |
| A3 | thiếu kết quả có tên (vé 13); độ hạt (node ví dụ, node rác) | Q3 = 81%; "Hàm thực liên tục" là ví dụ C[a,b]; "Nonnegative integers" từ câu dẫn |
| C8 | node chỉ có căn cứ ngoài vùng nội dung không bao giờ được hỏi `kind`, nên mục hành chính lọt vào "Tổng quan môn học"; kết quả/tính chất không có câu dạy thành `mentioned_only` | doc-1: "Thi viết rọc phách", "Thang điểm chữ", "Điểm đánh giá học phần" (lời nói đầu); doc-2: 13 cạnh vàng ngoài phạm vi, đều qua node `mentioned_only` như "Injective operator equivalence" |
| chi phí A8 | pass phụ hỏi gần như mọi cặp nên chi tăng theo bình phương số khái niệm; không hợp để phục vụ người dùng | doc-4 cả cuốn (≈ 616 khái niệm): 22.142 cặp, 44.284 lời gọi, ≈ 69 USD. Hướng: lọc cặp trước khi hỏi (vị trí sách, nhắc tên trong cửa sổ định nghĩa, cụm), hỏi một chiều khi chắc chiều, Batch/Flex (−50%); đo độ phủ mất bao nhiêu trên vàng phát triển trước khi đổi |
| A6 | nhắc tên bằng diễn đạt khác không thành cặp ứng viên | cạnh vàng "Column vector → …" có căn cứ "the columns of A"; độ phủ cạnh còn ~2/3 |
| A8 | khoảng 1/3 cạnh dư không cần (chấm mù) | T15-dev; cẩn thận bài học v2-06: tăng độ phủ thường kéo theo cạnh thừa |
| đánh giá | vàng nhiễu; chưa thử với người học | doc-2: hai người gán chỉ cùng chọn 59% cạnh |

Ghi chú:
- **Gộp A1 (công thức) với lượt chạy lại A3 của vé 13.** Cả hai đổi đầu vào A3 trở xuống và buộc ánh xạ lại bộ vàng, nên chỉ trả một lần.
  Nhận dạng công thức phải chạy tại máy (ví dụ mô hình công thức của docling) hoặc qua Gemini; không gửi sách ra dịch vụ khác.
- **A1 tốc độ cho ứng dụng** (chủ dự án muốn A1 rất nhanh; tạm ngưng 2026-10-02, tính sau). Điều đã biết:
  - đo cũ ≈ 7,2 giây/trang trên máy này, tức ≈ 48 phút cho sách 400 trang;
  - `DoclingParser` để gần như mặc định: CPU, 4 luồng, OCR bật, bảng chế độ chính xác, ảnh 2×;
  - cả bốn PDF thử đều có lớp chữ, nên OCR gần như chạy thừa;
  - docling 2.114 có pipeline song song theo trang (`ThreadedStandardPdfPipeline`).
  Đổi tuỳ chọn nào làm đổi đầu ra parse thì đổi luôn chunk trở xuống, nên phải gộp vào lượt chạy lại v4. Đổi tuỳ chọn không đổi đầu ra
  (số luồng, song song theo trang, GPU) thì làm lúc nào cũng được. Script đo viết dở ở `tmp/thu-a1/do_toc_do_parse.py`, chưa có số.
- **Tập giữ lại chỉ dùng một lần.** Sau 07 v2, mọi cải tiến v4 cần **tập giữ lại mới** (tài liệu mới và vàng mới) mới chứng minh được.
  Nên chuẩn bị người gán sớm; tài liệu T19 (ngôn ngữ thứ ba) có thể kiêm.

## Tôi kiểm thử thế nào

Mỗi vé: đọc diff, chạy test (thấy đỏ trên mã cũ bằng `git stash` hoặc đột biến), chạy **bảng kiểm đọc được** (vé 02) trước/sau trên
doc-1, doc-2, doc-6, nhap-mon-ml, doc-3, naive-bayes, và **đọc lộ trình** trước/sau — ghi phán xét vào mục "Kiểm thử" của vé. Số đo cũ
(Q6, Q7, Q7b) báo kèm để bắt hồi quy. Vé chạm luật văn bản: kiểm thêm có fixture đa ngôn ngữ, không còn danh sách từ của một ngôn ngữ
trong phần mã mới, và `--dry-run` trước/sau.

## Liên quan tới vé 07 v2 (tập giữ lại)

Đề nghị hoãn duyệt T10 tới khi vé 03–11 xong, để khoá cấu hình một lần trên luồng đã sửa. T13 (liệt kê mù trên tập giữ lại) không
phụ thuộc luồng, làm lúc nào cũng được.
