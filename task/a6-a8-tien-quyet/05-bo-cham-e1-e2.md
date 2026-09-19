# 05 — Bộ chấm E1 và E2

**What to build:** Có bộ vàng và artifact ở stage `mentions` là chấm được ngay hai câu hỏi quyết định, **không
tốn lời gọi mô hình nào**: cạnh tiên quyết nằm ở đâu trong tài liệu (E1), và bộ sinh cặp nào giữ được cạnh vàng
với ít cặp nhất (E2).

Luật ở spec D14.

**Blocked by:** 03, 04. (Việc của Claude.)

**Status:** done — 2026-09-18, trên nhánh `ve-05-bo-cham` (tách từ `ve-04-bo-vang`)

- [x] E1: chia cạnh vàng theo sáu loại vị trí của D14, kèm NMI giữa cụm chủ đề và chương.
- [x] E2: với từng bộ sinh và từng tổ hợp — số cặp, recall cạnh vàng, và **recall chỉ riêng nó có**. Gồm ba cấu
      hình định tuyến: chỉ trục chương, chỉ trục cụm, hợp cả hai.
- [x] Chấm được cả **cạnh trực tiếp** lẫn **bao đóng bắc cầu**.
- [x] Mọi chỉ số kèm khoảng tin cậy 95% bằng bootstrap lấy mẫu lại theo khái niệm đích.
- [x] Không gọi mô hình; chạy được khi chặn mạng.
- [x] Test trên một ví dụ dựng sẵn có đáp án tính tay; đột biến tối thiểu: nhầm chiều cạnh, bỏ bao đóng, bootstrap
      lấy mẫu theo cạnh thay vì theo khái niệm đích.

## Đã làm gì

- `src/doc2roadmap/domain/gold_scoring.py` — luật thuần: phân loại vị trí, bao đóng bắc cầu, P/R/F1, NMI, recall
  theo bộ sinh và theo tổ hợp, độ đồng thuận κ (có và không tính đồng thuận ngầm qua bắc cầu), và bootstrap.
- `src/doc2roadmap/application/use_cases/a8_score.py` — nạp bộ vàng cùng artifact `graph`, dựng báo cáo E1/E2.
- CLI `a8-score --doc-id --graph --gold [--gold] [--gold-mode] [--bootstrap] [--seed] [--output]`.
- Hai helper của vé 04 đổi thành công khai để dùng lại: `scope_inputs`, `chapter_lookup`.

## Quyết định thiết kế đáng ghi

- **Bộ chấm đọc artifact, không gọi vào code pipeline.** Nhánh này tách từ `85816ea` nên không có module A6–A10;
  đó lại là điều tốt: bộ chấm chỉ phụ thuộc *hình dạng artifact*, nên đổi code pipeline không làm hỏng phép đo.
- **Chốt phiên bản, không lấy "mới nhất".** Bộ vàng ghi `canonical_version`, `chapter`, `chapter_level` và
  `concept_hash`; bộ chấm dựng lại đúng phạm vi ấy từ kho và **từ chối chấm** nếu hash không khớp, hoặc nếu file
  vàng còn lỗi chưa sửa. Đây là chỗ F98 của pipeline đã sai, nên bộ chấm không lặp lại.
- **Phạm vi chấm bám PREAP:** chỉ tính cạnh có khái niệm đích nằm trong chương được gán. Cạnh pipeline trỏ tới
  khái niệm ngoài phạm vi không bị tính là sai, vì người gán không được hỏi về chúng.
- **Ba cấu hình định tuyến của E2 là định nghĩa đo, dựng lại từ artifact** (một cặp "nhìn thấy được" khi hai khái
  niệm cùng nằm trong một phiên của trục đó), vì pipeline chỉ chạy được một trục mỗi lượt.
- **Bootstrap không dùng `random`.** Tầng domain bị test kiến trúc cấm nhập `random`; hơn nữa dòng lấy mẫu là một
  phần của con số báo cáo, nên viết một LCG 64 bit ngay trong module và **ghim dòng số đầu tiên bằng test**.

## Bằng chứng

- **340/340 test xanh** khi chặn mạng (`HF_HUB_OFFLINE=1`, socket bị khoá), trong đó 20 test mới.
- **25/25 đột biến bị bắt**, gồm đúng ba con vé này yêu cầu: nhầm chiều cạnh (V1), bỏ bao đóng (V2), bootstrap lấy
  mẫu theo cạnh thay vì theo khái niệm đích (V3). Ba con lọt ở lượt đầu (F1 dùng trung bình cộng, không cắt cạnh
  vàng ngoài phạm vi, nhận cả cạnh kiểu mở) đã được vá bằng test mới rồi chạy lại.
- **Chạy thật trên `xstk-ch3-1`** (artifact `graph` v12, chương 10–13 cấp 2, 26 khái niệm đích, 98 khái niệm):
  báo cáo đầy đủ trong **3,9 giây** với 2.000 lần bootstrap, 0 lời gọi mô hình. Bộ vàng dùng để thử là **giả**,
  dựng từ node id thật, nên các con số chỉ chứng minh đường ống chạy, không có ý nghĩa khoa học.

## Còn chờ

Số thật của E1 và E2 cần bộ vàng do người gán (vé 12). Bộ chấm đã sẵn sàng nhận file JSON từ `a8-gold-check`.
