# 07 — Xác nhận trên tập giữ lại

**Nguồn chân lý:** spec v2, W18–W19

**What to build:** một lần chạy duy nhất, với cấu hình đã khoá (commit, `prompt_hash`, tham số), trên `xstk-ch3-1` và N2;
chấm Q1–Q9; báo nguyên kết quả kể cả trượt.

**Blocked by:** 02–06; vé 10 — T8 (vàng N2), T10 (duyệt cấu hình khoá)

**Status:** chờ

## Luật

- Trước lần chạy: ghi commit, `prompt_hash` từng khâu, tham số, SHA-256 của mọi tệp nhãn vào chính vé này.
- Chuyển `xstk-ch3-1-chuong-10-13-hoi-y-output.xlsx` thành JSON bằng `a8-gold-check` **ngay trước** lần chạy, không sớm hơn.
- Không chỉnh gì sau khi thấy số. Mọi thay đổi sau đó là hậu kiểm, báo tách riêng.
- Mỗi con số kèm khoảng tin cậy Wilson 95%; khoảng chứa vùng trượt thì kết luận là chưa đủ bằng chứng.

## N2 — chuẩn bị (2026-09-24)

- Tài liệu: `doc-4.pdf` (giáo trình Triết học Mác–Lênin, 214 trang, SHA-256 ghi ở manifest `artifacts/chunks/doc-4/v3`).
- Nhập: `ingest --pdf-backend pypdfium2 --heading-scheme vn-textbook` (docling-parse tách rời âm tiết; luật tiêu đề mặc
  định đặt mục con lên trên chương) → chunks v3: 672 chunk, 152k token.
- A3 candidates v1: 0,827 USD. A4/A5 canonical v1: 0,639 USD (`a4_gold_coverage=none`, cổng hồi quy
  `tests/fixtures/a4/gold-blind.json`). 620 khái niệm text.
- Chương gán vàng: **Chương VIII** (ordinal 9 ở `--chapter-level 2`), 47 khái niệm đích, 376 dòng quan hệ. Bảng
  `artifacts/a8-gold/doc-4-chuong-8-A1.xlsx`, `-A2.xlsx`; sinh **không** kèm `--graph` (chưa chạy A6–A8 trên doc-4), nên cột
  nơi dạy lấy từ A5.
- Luật: doc-4 là tập giữ lại. Không chạy A6–A10 trên doc-4 và không nhìn đồ thị của nó cho tới lần chạy duy nhất của vé này.

## T8 — nhận 2026-09-25

`a8-gold-check` qua cả hai bản, không lỗi: A1 65 cạnh, 13 cờ; A2 53 cạnh, 2 cờ; không bản nào ghi giờ. JSON:
`doc-4-chuong-8-A1.json`, `-A2.json`. Bảng hội ý `doc-4-chuong-8-hoi-y.xlsx` (`a8-gold-merge`): 41 dòng trùng, 36 dòng lệch,
concept_hash `7da62117ab70…`. Tôi không mở nội dung nhãn (tập giữ lại). Còn chờ: hội ý, rồi chuyển thành bộ vàng khoá.

## Bộ vàng N2 — khoá 2026-09-25

`a8-gold-merge --file doc-4-chuong-8-hoi-y-output.xlsx` → `artifacts/a8-gold/doc-4-chuong-8-vang.json`: 72 cạnh = 41 hai người
trùng + 31/36 cạnh lệch được giữ khi hội ý; 0 lỗi.
- SHA-256 bộ vàng: `df0c6cb9d42fffc4007f4e18c1922f1898ea932644fda4d5a483bfb05f8bc9ed`
- SHA-256 bảng hội ý đã điền: `bbb995017f297ed02bff2b3a7cd119e8aec9bf8f657bdbef650930ee5c3f9baa`
Tôi chỉ đọc số đếm, không mở nội dung nhãn. Không sửa tệp này nữa; chỉ mở ở lần chạy duy nhất của vé này.

## Q1 trên tập giữ lại (thêm 2026-09-25)

Q1 chưa có phép đo; thêm việc T12 (vé 10): sau lần chạy, bốc 50 khái niệm ngẫu nhiên từ lộ trình mỗi tài liệu giữ lại, người
kiểm tay. Seed ghi vào vé này trước khi bốc.

## Q7b (thêm 2026-09-25)

Chủ dự án thêm Q7b (độ chính xác tổ tiên trong chương, ≥ 70%); lần chạy của vé này chấm Q1–Q9 và Q7b.

## Chuỗi mặc định cho lần chạy (cập nhật 2026-09-26)

Chuỗi mặc định nay là `validated → teaching (neo C8 v3) → identity → stages`. Theo W15, trước khi chấm, mọi gộp danh tính chạm
khái niệm của bộ vàng giữ lại (xstk chương 10–13, doc-4 Chương VIII) phải được chủ dự án duyệt — thêm bảng duyệt kiểu T5 cho
hai tài liệu này trong lần chạy. Cần một cách nạp quyết định duyệt vào chuỗi (hiện chỉ script phát triển nạp được) — làm khi
chuẩn bị T10.

## Kế hoạch lần chạy (lập 2026-09-26)

Q10 = Q1–Q9 và Q7b trên `xstk-ch3-1` (vàng: cấp 2, dải 10–13 = mục 2.1–2.4, 26 đích) và `doc-4` (vàng: Chương VIII, 47 đích).

| bước | việc | ai | phụ thuộc |
|---|---|---|---|
| 0 | **T13** liệt kê mù Q3 trên tập giữ lại — `liet-ke-mu-giu-lai.md` (seed 20260926: xstk 2.1, 2.3, 2.4; doc-4 I, II, III) | người | **làm ngay**, không cần đầu ra máy |
| 1 | T10 khoá cấu hình: commit, `prompt_hash` từng stage, tham số, ngưỡng (tôi sinh bảng) | chủ dự án | trước bước 2 |
| 2 | chạy chuỗi mặc định `roadmap --allow-spend` trên hai tài liệu (doc-4 cả cuốn: A6–A10 ước ≈ 2–4 USD) | tôi | 1 |
| 3 | **T14** duyệt gộp danh tính chạm vàng (bảng kiểu T5) → `--identity-review` → chạy lại `identity`/`stages` | chủ dự án | 2 |
| 4 | chuyển bảng hội ý xstk thành JSON (`a8-gold-check`) — ngay trước khi chấm | tôi | 3 |
| 5 | chấm tự động: Q2, Q5 (kèm đường cơ sở "n gần nhất"), Q6, Q7, Q7b | tôi | 4 |
| 6 | sinh bảng người: **T12** Q1 (50 khái niệm lộ trình / tài liệu), **T15** Q4 chấm mù cạnh dư (khuôn T1), **T16** Q9 kiểm 50 câu neo (khuôn T4), **T17** Q8 mạch lạc module (khuôn T6), đối chiếu tên Q3 (khuôn T7) | tôi → người | 5 |
| 7 | chấm, báo nguyên kết quả kể cả trượt, kèm Wilson | tôi | 6 |

Đã biết trước sẽ trượt trên dữ liệu phát triển: Q3 (81%), Q4 (0,72–0,90), Q5, Q7; Q7b trượt ở doc-1. Không sửa gì sau khi thấy số.

## T10 và T13 — chủ dự án giao tôi quyết (2026-09-26)

**T10 (khoá cấu hình): hoãn** tới khi vé v3-03 … v3-11 (spec v3) xong. Lý do: tập giữ lại chỉ mở một lần (W18); khoá bây giờ là
kiểm trên luồng chính tôi đã đánh giá chưa chuẩn (báo cáo 2026-09-26), sau v3 sẽ không còn tập sạch để kiểm lại. Khi v3 xong: chạy
lại `scripts/khoa-cau-hinh/tao_bang.py`, ghi bản khoá vào `07b-cau-hinh-khoa.md`, rồi mới chạy bước 2 của kế hoạch trên.

**T13 (liệt kê mù Q3 trên tập giữ lại): xong, do Claude làm** — không phải nhãn người; ghi rõ trong tệp.
- Mức mù: chưa xem danh sách khái niệm máy của các mục được bốc. Đã thấy trước: 47 khái niệm đích Chương VIII doc-4 (in ra khi sinh
  bảng T8) và vài tên trong cảnh báo A3 (chương II, IV, V, IX, XI doc-4); vài tên mục 3 (kiểm định) của xstk.
- Vì vậy **bốc lại doc-4** (seed 20260927) trong 21 mục của các chương chưa thấy tên (III, VI, VII, X, XII, XIII, XIV): VII-IV Tất
  nhiên và ngẫu nhiên (tr. PDF 109–111), VII-VII Khả năng và hiện thực (116–119), XII-I Nhà nước (174–180). xstk giữ mẫu seed 20260926:
  2.1 (21–23), 2.3 (30–33), 2.4 (33–35). Bốc lại dựa trên việc người làm đã thấy gì, không dựa trên kết quả máy.
- 84 khái niệm (xstk 34, doc-4 50), mỗi dòng một khái niệm, tính cả mệnh đề/phân loại có tên; 9 dòng đánh `(?)`.
- Tệp `artifacts/a8-gold/liet-ke-mu-giu-lai.md`, SHA-256 `40893176582ea921054632b0038fb08c232248c4068de8c11a794bf55c90a49f`. **Chưa chấm** — chấm Q3 ở lần chạy vé 07
  (`scripts/liet-ke-mu/cham_q3.py artifacts/a8-gold/liet-ke-mu-giu-lai.md <bảng đối chiếu>`); bước đối chiếu tên cũng do tôi làm,
  theo luật dòng ghép đã có.
