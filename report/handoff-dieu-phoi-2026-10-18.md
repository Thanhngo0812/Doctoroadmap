# Bàn giao điều phối — Pha B, Pha B2, web WayFinder (2026-10-18)

**Dòng trạng thái:** viết xong 2026-10-18 tối, bởi Claude, trước khi hết lượt dùng. Người điều phối cập nhật **mục 10 (nhật ký điều phối)** mỗi ngày, và
sửa mục 2 khi trạng thái đổi.

**Tiếp nhận 2026-10-18:** Codex nhận vai trò điều phối theo yêu cầu trực tiếp của chủ dự án. Đã đối chiếu Git, mã, kế hoạch, spec, báo cáo và chạy lại
280 test Pha B/B2 cùng 7 phép thử sửa sai phần nền. Báo cáo tiếp nhận và lời giao việc cụ thể ở
[báo cáo điều phối](dieu-phoi-tiep-nhan-2026-10-18.md). Đây chưa phải phán xét nghiệm thu SA-45.

**Tài liệu này dành cho ai:** người điều phối thay Claude trong những ngày Claude không có lượt. Đó có thể là chủ dự án, một nhân viên cấp cao, hay một
agent khác. Người điều phối:
- theo dõi các bảng vé, chọn vé tiếp theo, soạn lời giao vé, nhắc chủ dự án;
- chuyển báo cáo của người làm sang người soát, ghi phán xét vào bảng;
- gom câu hỏi thiết kế cho chủ dự án và cho Claude.

**Người điều phối không được:**
- duyệt tiền: chỉ chủ dự án duyệt;
- đổi spec, ADR, hay quyết định của chủ dự án: ghi thành câu hỏi ở mục 8;
- tự viết mã sản phẩm;
- mở tập giữ lại (mục 7).

**Đọc theo thứ tự:** mục 1 → 3 → 4, rồi các mục khác khi cần.

---

## 1. Ai làm gì

| vai | ai | làm | không làm |
|---|---|---|---|
| chủ dự án | chủ dự án | duyệt tiền, chốt thiết kế, giao việc, cấp tài khoản và khoá (Cloudinary, Gmail, Gemini), cung cấp logo | |
| người điều phối | Codex, tiếp nhận 2026-10-18 | chọn vé, soạn lời giao vé, nhắc, gom câu hỏi, giữ nhật ký | duyệt tiền, đổi spec, tự viết mã sản phẩm |
| người soát cấp cao | nhân viên cấp cao, vé [SA-45](../task/sau-a10/45-soat-thay-claude-nhan-vien-cap-cao.md) | soát vé Pha B, ghi phán xét, tạo vé sửa từ SA-46; soát cả vé web, vé sửa web từ W-24 | đổi spec, ADR, quyết định Q1–Q30 |
| nhân viên lõi | nhân viên đã làm SA-01…44 | vé Pha B, phần lõi của web: W-05 (nới port), W-13, W-15 | sửa tệp của phiên pha A |
| nhóm web (4 người) | nhóm đồ án | vé W-01…W-21, W-23 | sửa lõi ngoài W-05, W-13 |
| người thiết kế | trong nhóm | W-22 (Figma) | vẽ lại logo |
| agentic | họ mô hình **khác Gemini** | bộ câu hỏi thử 19a | thấy đáp án câu kiểm |
| phiên pha A | phiên Claude riêng | đồ thị, chuỗi gộp | |
| Claude | khi có lượt | nghiên cứu, kiểm thử, soát, nhắc việc, điều phối, viết spec và vé | cài mã sản phẩm |

## 2. Tình hình lúc bàn giao

**Pha B (vé `task/sau-a10/`, [kế hoạch](../task/sau-a10/00-ke-hoach.md)):**
- **SA-01…28:** đã soát. Còn treo:
  - lượt thật của SA-08, 10, 13 chưa chạy lại sau các vé sửa;
  - SA-28 chưa đạt, đã giao sang SA-29.
- **SA-29** (tên module): đã cài và chạy (commit `2356ee8`), chi 0,1425 USD trong trần 0,50 USD chủ dự án duyệt. Kết quả: tên LLM 136/160, mô tả LLM 82/160.
  **Chưa soát.** Doc-1 chỉ còn 1/33 mô tả do LLM viết; cần đọc kỹ.
- **SA-30** (K6, cache bài hỏng, TTFT, câu trích, tài liệu): đã cài, cùng commit. **Chưa soát.**
- **SA-31…44** (Pha B2):
  - nhân viên báo đã cài; bản bàn giao mới ghi 280 test đạt, ở [report/pha-b2-ban-giao-31-44-2026-10-18.md](pha-b2-ban-giao-31-44-2026-10-18.md) cùng 4 báo cáo con;
  - **đã commit:** `a7f57d0` ghép B2, `3871c85` sửa cắt đuôi bài giảng sau lỗi hậu cổng. Lúc Codex tiếp nhận, không có thay đổi chưa commit trong `src/`;
    đã chạy lại **280/280 test đạt**, cùng **7/7** bản sửa sai phần nền bị test bắt. **Vẫn chờ soát độc lập**, không giao lại việc commit B2;
  - **SA-43:** lượt thật đã chạy trong trần 0,50 USD chủ dự án duyệt, chi 0,0652 USD. Còn chờ soát nội dung 12 bài;
  - **SA-44:** còn 7 thao tác thử tay và ảnh chụp, vì công cụ trình duyệt của nhân viên bị chặn;
  - **ví dụ JSON thật cho nhóm web** ở `report/pha-b2-contract-examples-2026-10-18.json`.
- **Đồ thị hiện hành** (bản tên mới nhất): doc-1 v57, nhap-mon-ml v50, naive-bayes v49, doc-6 v29, xstk-ch3-1 v68, doc-4 v27.
- **SA-19a** (bộ câu hỏi thử): gói đã xuất ở `Desktop\pha-b-cau-hoi-thu\giao-agentic\`. **Chưa giao agentic.**
- **SA-20…23** (đánh giá): chạy sau khi soát xong các vé sửa và B2.
- **SA-45** (người soát cấp cao): vé sẵn, **chưa giao**.

**Web WayFinder (vé `task/web/`, [kế hoạch](../task/web/00-ke-hoach.md)):**
- Đã có:
  - [spec chức năng](../doc/web-chuc-nang-spec.md), [spec cơ sở dữ liệu](../doc/web-co-so-du-lieu-spec.md), [spec thiết kế](../doc/web-thiet-ke-giao-dien-spec.md);
  - ADR 0020–0023;
  - 23 vé gốc W-01…W-23; chủ dự án đã cho W-01/W-13/W-22 khởi động. Trạng thái hiện hành xem kế hoạch web; vé sửa sau soát bắt đầu từ W-24.
- **Quyết định của chủ dự án ngày 2026-10-18:**
  - mã web gom vào `src/web`; PostgreSQL chạy bằng Docker;
  - Cloudinary giữ tệp gốc và ảnh, tài sản riêng tư;
  - bản demo: ai cũng tải sách được, khâu dựng không giới hạn;
  - khoá mẫu chỉ có ở dev;
  - gửi thư bằng Gmail SMTP; dùng một tài khoản Cloudinary;
  - chủ khoá xem được tiến độ lớp.
- **Tệp thương hiệu** ở `design/` (chưa commit, của chủ dự án):
  - 6 favicon (`OTP1`–`OTP6`) và GIF chờ (7,4 MB);
  - **cập nhật 2026-10-19:** logo thực là 20 tệp `Artboard 9.png` đến `Artboard 28.png`, đã có đủ trong `design/`, thay tên giả định `logo1`–`logo8`.
    Đã xem ảnh: Artboard 21–24 đen nền trong, 25–28 trắng nền trong. W-01/W-22 không còn chờ logo; bảng dùng theo spec thiết kế mục 1.

**Cập nhật tiếp nhận W-13 ngày 2026-10-19:** W-13 đã có mã lõi/báo cáo triển khai nhưng **chưa commit, chưa soát độc lập** tại lượt kiểm đó; xem
[tiếp nhận W-13](dieu-phoi-tiep-nhan-w13-2026-10-19.md). Điều phối chạy lại 65 test W-13 + 2 kiến trúc đạt, bốn mutation bị bắt. CLI ghi SQLite;
PostgreSQL/worker web còn thuộc W-14. Doc-6 toàn chuỗi còn thiếu cache label-roles. Không coi báo triển khai là phán xét đạt.

**Tiếp nhận W-22 ngày 2026-10-19:** đã có token, preview, ảnh và link Figma; **chưa đủ nghiệm thu**. Điều phối chạy lại 20 test/17 cặp màu đạt,
nhưng kiểm Chrome thấy nút tối thiếu tương phản, vùng bấm mobile dưới 44 px, GIF vẫn chạy khi giảm chuyển động; đổi sai CSS mà 20 test vẫn xanh.
Chưa xác minh được đủ trang/trạng thái và bốn prototype trong Figma. Đã soạn [W-24](../task/web/W-24-bo-sung-va-sua-ban-giao-w22.md), chờ chủ dự án giao;
xem [tiếp nhận W-22](dieu-phoi-tiep-nhan-w22-2026-10-19.md). W-01 tiếp tục nền; W-23 chờ W-22 nghiệm thu.
Tại lượt này đã thấy `src/web/`, chưa soát hay xác nhận nghiệm thu W-01.

**Kiểm lại sau ba nhóm báo xong, 2026-10-19:** xem [soát ba nhóm và kế hoạch tiếp](dieu-phoi-soat-ba-nhom-2026-10-19.md).
W-01 đạt nền local: React 23 test/build, trình duyệt 6 tổ hợp đạt; `src/web/` chưa được Git theo dõi, cần ghim commit đúng phạm vi.
W-13 đã commit `e9ffce1`, điều phối chạy lại 68 test và 4 mutation đạt; doc-6 hết chuỗi vẫn thiếu cache, chưa đóng phần này.
W-24 đã bàn giao và sửa một phần nhưng chưa đạt toàn bộ: desktop GIF còn chạy khi giảm chuyển động, guard spacing/RGBA còn lọt,
bằng chứng đủ trang/Variables/bốn prototype Figma còn thiếu. Sau checkpoint W-01 mở W-02 cho web, W-05 cho lõi; thiết kế tiếp tục W-24.
Migration theo tuyến W-01 → W-05 → W-02, không tự tạo hai head; chưa mở W-15/W-23.

**Cập nhật sau bản sửa `7baa7d2`, 2026-10-19:** [kiểm lại W-13/W-24](dieu-phoi-kiem-lai-w13-w24-2026-10-19.md).
W-13 **đạt nghiệm thu**, đã kiểm độc lập doc-6 ở cả hai kho đủ bốn bước, graph 37/8, không gọi mô hình; 83 test W-13/kiến trúc/token đạt.
Nhân viên đã chạy hai lượt có tiền sau duyệt, tổng chi usage ghi nhận 0,2329025 USD, một lượt có cờ thiếu usage; đợt điều phối không phát sinh chi.
W-24 đã sửa đạt GIF/vùng bấm/guard/chat cũ; còn Variables thực (plugin lệch sáu màu tối), đủ trang/prototype và khung auth 390 tràn 20 px.
Không giao lại lỗi đã đóng. W-15 gỡ điểm chờ W-13, vẫn chờ W-14; kế hoạch W-02/W-05 tiếp tục, W-23 chưa mở.

## 3. Việc ngay, theo thứ tự

Mỗi việc ghi ai làm, và xong thì người điều phối đánh dấu ở mục 10.

1. **[Đã xong, Codex kiểm chứng] Mã SA-31…44 đã có commit để soát.**
   - Ghim `a7f57d0` và bản sửa `3871c85`; bộ kiểm Pha B/B2 của đợt tiếp nhận đạt 280 test. Đây không phải toàn bộ test của repo.
   - Thư mục làm việc vẫn còn tệp dở của người khác: `.gitignore`, `scripts/pass-phu-ml/*`, `task/v4/*`,
     `report/huong-dan-agentic-gan-nhan-d02.md` và tệp chưa được theo dõi. Không stage hay commit lẫn.
   - **Việc ưu tiên hiện tại chuyển sang giao SA-45**, không yêu cầu nhân viên commit lại B2.
2. **[Chủ dự án] Giao SA-45 cho nhân viên cấp cao.** Hàng đợi soát: SA-29 → SA-30 → SA-31…44 (đọc bàn giao B2 trước) → nội dung 12 bài của SA-43.
3. **[Chủ dự án] Làm 7 thao tác thử tay của SA-44**, hoặc bật quyền trình duyệt cho nhân viên.
   - Máy chủ xem thử ngoại tuyến: `http://127.0.0.1:18765/`, kho `tmp/b2-preview-manual.json`.
   - Danh sách 7 thao tác ở `report/pha-b2-sa37-44-2026-10-18.md` và ở vé SA-44.
   - Chụp ảnh từng thao tác, gửi người soát.
4. **[Chủ dự án] Giao gói 19a cho agentic** (họ mô hình khác Gemini).
   - Thư mục giao: `Desktop\pha-b-cau-hoi-thu\giao-agentic\`.
   - **Không** giao `Desktop\pha-b-cau-hoi-thu-nguoi-giu\`.
   - Agentic trả về thì người soát chạy `scripts/pha-b/kiem_cau_hoi_thu.py`, rồi chấm 12 câu kiểm bằng đáp án ở thư mục người giữ.
5. **[Chủ dự án] Chuẩn bị tài khoản cho web:**
   - `CLOUDINARY_URL` vào `.env`; bật "Allow delivery of PDF and ZIP files" (Settings → Security); xem cỡ tệp tối đa và tín dụng của gói;
   - Gmail: bật xác minh hai bước, tạo mật khẩu ứng dụng, đặt vào `.env`;
   - Docker Desktop (nền WSL2) trên máy của nhóm web;
   - logo đã có đủ Artboard 9–28, gồm PNG nền trong; SVG có thể bổ sung nếu có. Tệp gốc GIF là phần riêng, gửi nếu có để xuất lại vòng chờ.
6. **[Chủ dự án giao] Ba vé web chạy song song:**
   - **W-01** cho nhóm web, được bắt đầu ngay;
   - **W-13** nhân viên lõi đã triển khai; bước tiếp là commit đúng phạm vi, chuyển người soát và xử lý phần doc-6 thiếu cache, không tự chi tiền;
    - **W-22** đã có bàn giao; người thiết kế tiếp tục sửa/bổ sung theo W-24 trước khi nghiệm thu. Thương hiệu dùng Artboard 9–28 theo spec mục 1.

## 4. Cách giao một vé

**Chọn vé:** chỉ giao vé có mọi vé ở cột "chặn bởi" đã **đạt**, tức đã soát. Báo xong mà chưa soát thì chưa tính.

**Không giao song song hai vé sửa cùng một vùng mã.** Các cặp dễ đụng nhau:
- W-05 và mọi vé sửa kho Pha B (SA-46+ nếu chạm `phase_b_store.py`, `ports/phase_b.py`);
- W-13 và mọi vé của phiên pha A;
- W-06 với W-07…W-10, vì cả năm vé cùng thêm hàm vào `LearningGateway`. W-07 xong rồi mới giao song song W-08, W-09, W-10, mỗi vé một người.

**Lời giao vé mẫu** (dán cho người nhận, thay phần trong ngoặc):

> Bạn nhận vé [mã vé] ([đường dẫn tệp vé]). Đọc theo thứ tự: vé, kế hoạch vé ([đường dẫn 00-ke-hoach.md]) mục "Luật chung", rồi các spec mà vé dẫn ở
> dòng "Nguồn chân lý".
>
> Luật bắt buộc:
> - Lưu dần: làm tới đâu commit tới đó. Báo cáo vé có dòng trạng thái ở đầu.
> - Chỉ commit đường dẫn của vé, bằng `git commit -m … -- <tệp>`.
> - Không mở tập giữ lại: `d01-t01`, `d01-t02`, `document-data/test/`, `Desktop\d02-tap-khoa`; không in phần `cache` của `artifacts/phase_b/live.json`.
> - Lượt có tiền thì dry-run trước, gửi con số, chờ chủ dự án duyệt rồi mới chạy. Chỉ dùng `gemini-3.1-flash-lite`.
> - Mỗi tiêu chí nghiệm thu là một test thấy đỏ trên bản sai trước rồi mới xanh. Ghi lệnh đã chạy và số test vào báo cáo.
> - Thấy spec sai hay thiếu thì ghi vào mục "Câu hỏi" của báo cáo, không tự đổi spec.
> - Bí mật (`CLOUDINARY_URL`, mật khẩu Gmail, khoá Gemini) chỉ ở `.env`; không dán vào báo cáo hay chat.
>
> Xong thì báo cáo ở [report/<tên-vé>-<ngày>.md], kèm ảnh chụp (vé có giao diện) và ví dụ JSON thật (vé có điểm cuối mới).

**Nhận báo cáo:**
1. Kiểm báo cáo có đủ: lệnh đã chạy, số test, ảnh chụp hay ví dụ JSON nếu vé yêu cầu, tiền đã chi.
2. Chuyển cho người soát (SA-45). Người soát làm theo SA-45 mục 3: chạy test, thử sửa sai, đọc tận nơi đầu ra, kiểm lại một hai con số.
3. Ghi phán xét vào cột trạng thái của bảng kế hoạch: **đạt**, **đạt có ghi chú**, hay **chưa đạt → vé sửa số …**.
4. **Chưa đạt:** người soát tạo vé sửa theo khuôn của SA-45 mục 4, đánh số SA-46+ cho Pha B hay W-24+ cho web. Người điều phối sửa cột "chặn bởi" của các vé bị
   ảnh hưởng.

**Lượt có tiền:**
1. Người làm chạy dry-run và gửi con số.
2. Người điều phối chuyển con số cho chủ dự án, nói rõ lượt này để làm gì.
3. Chủ dự án trả lời bằng tin nhắn; người làm trích tin nhắn đó vào báo cáo.
4. Chạy xong thì ghi chi thật vào mục 10.

Hiện chỉ W-15 lượt 2 (dựng một cuốn mới, ước dưới 3 USD) và các lượt thật của SA-08, 10, 13 còn chờ chạy.

## 5. Lịch giao theo làn

Bốn làn chạy song song; trong mỗi làn, làm theo thứ tự.

| làn | thứ tự | ghi chú |
|---|---|---|
| **soát Pha B** (người soát) | SA-29 → SA-30 → SA-31…44 → nội dung SA-43 → các vé sửa SA-46+ → lượt thật SA-08, 10, 13 (chủ dự án duyệt) → SA-20…23 | SA-20…23 chỉ chạy khi mọi vé sửa đạt |
| **lõi** (nhân viên lõi) | commit B2 (đã xong) → các vé sửa SA-46+ nếu có → W-13 → W-05 (phần nới port, sau khi vé sửa kho Pha B xong) → W-15 | W-15 cần W-14 xong trước |
| **web** (nhóm web) | W-01 → W-02 → (W-03 ∥ W-04) → W-06 (cần W-05) → W-07 → (W-08 ∥ W-09 ∥ W-10) → (W-11 → W-12) ∥ W-14 → W-16 → W-17 ∥ W-18 ∥ W-19 → W-20 → W-21 → W-23 | phần học W-07…W-10 cần SA-32…42 **đạt** |
| **thiết kế** (người thiết kế) | W-22 (sau khi có logo) → duyệt ảnh chụp của từng vé web → W-23 cùng nhóm web | |

Lịch theo làn là hướng dẫn phân người, không thêm cạnh chặn mới. Khi chọn vé, kiểm bảng phụ thuộc trong kế hoạch web: W-11 có thể bắt đầu sau W-06;
W-18 sau W-07/W-11; W-20 sau W-11/W-14. Không bắt các vé này chờ toàn bộ phần học nếu không có xung đột tệp thực tế.

**Điểm chờ dễ kẹt:**
- W-06 cần W-05. Nhân viên lõi làm W-05 chậm thì nhóm web bị chặn ở W-06. Nên giao W-05 sớm.
- W-05 làm cả phần lõi (nới port) lẫn phần web (bản PostgreSQL). Hai người làm thì phần lõi xong trước.
- W-08, W-09, W-10 cần các vé B2 được soát **đạt**. Người soát nên ưu tiên SA-32, 33, 35, 37, 39, 40, 41, 42.

## 6. Khi nào gọi chủ dự án ngay

Nhắn chủ dự án ngay, không chờ, khi có một trong các việc sau:
- một lượt cần chi tiền;
- người làm muốn đổi spec, ADR, hay quyết định;
- có người lỡ mở tập giữ lại, hay in nội dung của nó. Dừng vé đó lại, ghi chính xác đã thấy gì;
- test trên nhánh chính đỏ sau một commit;
- commit lẫn tệp của người khác;
- thiếu khoá hay tài khoản (Cloudinary, Gmail, Gemini);
- tín dụng Cloudinary trong tháng dùng quá 70%, hay Gmail báo vượt giới hạn gửi;
- câu hỏi cần phiên pha A trả lời (W-13);
- hai người làm cùng sửa một vùng mã.

## 7. Luật bắt buộc

**Tập giữ lại**, không ai được mở:
- `d01-t01`, `d01-t02`: chunk, tên khái niệm, tiêu đề và mô tả module, bài giảng, quiz;
- `document-data/test/`, `Desktop\d02-tap-khoa`, mọi tệp `khoa.jsonl`.
- Phần `cache` của `artifacts/phase_b/live.json` có tiêu đề module của T-01: không in, không nhập vào cơ sở dữ liệu.
- Khi thống kê usage, bỏ các dòng có `doc_id` bắt đầu bằng `d01-t0`.
- Script chỉ nạp sáu cuốn phát triển: doc-1, nhap-mon-ml, naive-bayes, doc-6, xstk-ch3-1, doc-4.
- Checker chạy trên tập giữ lại chỉ in các trường số có trong danh sách cho phép.

**Tiền:**
- chỉ dùng `gemini-3.1-flash-lite`;
- dry-run trước, chủ dự án duyệt;
- soát bằng cách phát lại phản hồi đã ghi, 0 USD.

**Git:** chỉ commit đường dẫn của mình. Không sửa tệp của phiên pha A.

**Môi trường:**
- `.venv/Scripts/python.exe`, vì `python` trần chỉ là stub;
- `pytest` cần `--basetemp` trỏ vào một thư mục ghi được, kèm `-p no:cacheprovider`.

**Lưu dần:** mọi người và mọi agent ghi tệp theo từng phần, có dòng trạng thái. Agent nền chạy từng cái một.

**Bí mật:** chỉ ở `.env`.

## 8. Câu hỏi treo

**Cho Claude, khi quay lại:**
1. **S3 hay S2** (stream bài giảng): ở SA-43, khoảng từ cổng tới khi xong bài có p50 = 939 ms, đo trên 4 mẫu. Spec ghi "dưới 1 giây thì báo Claude". 4 mẫu là
   chưa đủ để quyết.
2. **Nhiệt độ của lần sinh lại:** nhánh 1,0 có hai prompt sửa không còn khớp bản ghi, nên chưa so được với nhánh 0.
3. **Thẻ lộ trình doc-4** ước 1.322 token, quá ngưỡng khoảng 800. Cần chọn: tên ngắn, hay lấy chi tiết module khi cần.
4. **Mô tả module của doc-1:** chỉ 1/33 do LLM viết. Xem lại luật từ vựng của mô tả.

**Cho chủ dự án:**
1. **Đã rõ theo spec hiện hành, không cần hỏi lại:** giữ trần Pha B 0,20 USD mỗi người học mỗi ngày và 5 USD mỗi ngày cho nội dung dùng chung.
   Spec chức năng web, mục "Quyết định của chủ dự án", đã tách rõ câu "không giới hạn" chỉ áp cho khâu dựng. Chỉ mở lại khi chủ dự án muốn đổi.
2. **Đã giải quyết 2026-10-19:** chủ dự án xác nhận logo là Artboard 9–28; đã kiểm đủ tệp và cập nhật bảng trong spec thiết kế mục 1.
3. **Ghi nhận lịch sử 2026-10-18:** lúc tiếp nhận chưa thấy logo theo tên giả định; nay đã có Artboard 9–28, không còn yêu cầu cung cấp tám logo cũ.

**Cho phiên pha A, qua chủ dự án/nhân viên lõi khi giao W-13:**
1. **2026-10-18, Codex:** xác nhận vị trí A3 tạo ứng viên, chỉ mục A3′ và `label-roles` trong bốn bước công khai của `build_document` cho cuốn mới.
   `Canonicalize._run` đang đọc `load_latest_candidates`; `BuildMentions` đọc `load_latest_retrieval`. Danh sách lệnh dự kiến của W-13 chưa nêu A3/A3′;
   lượt doc-6 dùng dữ liệu cũ không đủ chứng minh chuỗi cho tệp mới. Ghi câu trả lời vào báo cáo W-13, không tự sửa spec hay mã của phiên pha A.

**Người điều phối thêm câu mới vào đây,** kèm ngày và người hỏi.

## 9. Khi Claude quay lại

Claude đọc theo thứ tự:
1. mục 10 của tài liệu này;
2. `report/soat-pha-b-tong-hop-*.md` (SA-45 viết);
3. bảng trạng thái của `task/sau-a10/00-ke-hoach.md` và `task/web/00-ke-hoach.md`;
4. mục 8.

Chủ dự án tóm thêm tình hình bằng lời.

## 10. Nhật ký điều phối

Người điều phối ghi mỗi việc một dòng, mới nhất ở dưới cùng.

| ngày | việc | ai | trạng thái | ghi chú |
|---|---|---|---|---|
| 2026-10-18 | bàn giao điều phối | Claude | xong | spec web, ADR 0020–0023, vé W-01…W-23 đã commit |
| 2026-10-18 | commit mã SA-31…44 | nhân viên lõi | xong, Codex đã đối chiếu | `a7f57d0`, bản sửa `3871c85`; chưa thay thế soát SA-45 |
| | giao SA-45 | chủ dự án | chờ | |
| | 7 thao tác thử tay SA-44 | chủ dự án | chờ | |
| | giao 19a cho agentic | chủ dự án | chờ | |
| | tài khoản Cloudinary, Gmail, Docker; logo | chủ dự án | chờ | |
| | giao W-01, W-13, W-22 | chủ dự án | chờ | |
| 2026-10-18 | chính thức tiếp nhận điều phối | Codex | đã nhận | chủ dự án yêu cầu trực tiếp trong chat; giữ phạm vi vai trò ở mục 1 |
| 2026-10-18 | chạy lại kiểm Pha B/B2 và kiến trúc | Codex | 280/280 đạt | lần sandbox: 272 đạt, 8 lỗi quyền socket; chạy lại có quyền localhost: 280 đạt; không gọi mô hình trả phí |
| 2026-10-18 | kiểm phép sửa sai nền B2 | Codex | 7/7 bị test bắt | `scripts/phase-b/b2_foundation_mutations.py`; chỉ thay trong tiến trình thử |
| 2026-10-18 | đối chiếu sáu đồ thị phát triển | Codex | xong | 160 module, 901 khái niệm học; 136 tên LLM, 82 mô tả LLM; doc-1: 1/33 mô tả LLM |
| 2026-10-18 | đối chiếu web, thương hiệu, trần học | Codex | xong, còn việc giao | chưa có `src/web`; chưa thấy tám logo; trần học đã rõ trong spec, không hỏi lại |
| 2026-10-18 | soạn đợt giao việc tiếp theo | Codex | đã soạn, chưa gửi sang phiên khác | SA-45 ưu tiên; W-01 bắt đầu; W-13 xác nhận chuỗi mới; W-22 chuẩn bị phần không phụ thuộc logo; xem báo cáo tiếp nhận |
| 2026-10-18 | bổ sung yêu cầu giao diện theo chỉ thị chủ dự án | Codex | đã cập nhật spec và vé | Figma/React phải đẹp, chỉn chu, hiệu ứng phù hợp; được dùng `taste-skill` do chủ dự án nạp; tiêu chí ở spec thiết kế mục 3a, luật chung web, W-01/W-22/W-23 |
| 2026-10-18 | chốt đường Gemini backend web theo chỉ thị chủ dự án | Codex | đã cập nhật spec và vé | FastAPI/worker dùng Gemini Developer API bằng API key, không dùng Vertex; đồng bộ W-01/W-06/W-13/W-15/W-21 và luật chung; chưa sửa runtime sản phẩm |
| 2026-10-19 | đổi lại đường Gemini backend web theo chỉ thị mới | Codex | thay quyết định 2026-10-18 | FastAPI/worker tạm dùng Vertex cho sinh/embedding/dựng sách; chỉ chuyển Developer API khi chủ dự án yêu cầu chuẩn bị demo; đã đồng bộ spec và các vé, chưa sửa runtime hay bí mật |
| 2026-10-19 | xác nhận bộ logo thực tế theo chủ dự án | Codex | đủ 20 tệp, gỡ chờ logo | Artboard 9–28 trong `design/`; đã xem hình/alpha, cập nhật spec, W-01/W-22, luật chung và lời giao việc; thanh trên sáng/tối dùng Artboard 24/28 |
| 2026-10-19 | tiếp nhận triển khai W-13 | Codex | đã triển khai, chờ commit/soát | tự chạy lại 67 test đạt và 4/4 mutation bị bắt; kiểm XML nhân viên 1868/65 đều xanh; doc-6 toàn chuỗi chưa hoàn tất, PostgreSQL thuộc W-14; xem báo cáo tiếp nhận |
| 2026-10-19 | đồng bộ luồng dựng theo quyết định trong spec mục 4 | Codex | đã cập nhật tài liệu phụ thuộc | thả tệp → xác nhận → dựng; không dự toán/chi phí cho người dùng; ghi usage thực vào DB, kể cả lỗi/huỷ; W-14/W-15/W-21 và spec chức năng/CSDL đã đồng bộ, duyệt tiền nội bộ vẫn bắt buộc |
| 2026-10-19 | tiếp nhận và kiểm W-22 | Codex | chưa đủ nghiệm thu | 20 test/17 cặp đạt; 56 giá trị JSON/CSS khớp trong phạm vi kiểm; Chrome tái hiện lỗi nút tối, vùng bấm, GIF; phép đổi sai CSS không bị test bắt; Figma chưa xác minh trực tiếp |
| 2026-10-19 | soạn W-24 sửa/bổ sung W-22 | Codex | đã soạn, chưa gửi phiên khác | người làm W-22 sửa và bổ sung node/Variables/ảnh/video; W-01 tiếp tục nền theo spec, W-23 chờ W-22 nghiệm thu; bằng chứng ở artifacts/coord-w22-2026-10-19 |
| 2026-10-19 | kiểm lại bàn giao ba nhóm W-01/W-13/W-22-W-24 | Codex | nền local và lõi đã kiểm; thiết kế còn mở | 68 test W-13, 71 test web/token + 1 Cloudinary không bật, 23 React/build; browser W-01 đạt; W-13 4 mutation bị bắt; W-24 còn GIF/guard/vùng bấm và bằng chứng Figma |
| 2026-10-19 | soạn đợt W-02/W-05 và tiếp tục W-24 | Codex | đã cập nhật kế hoạch/vé, chưa gửi phiên khác | chốt commit W-01 trước; migration một tuyến W-01→W-05→W-02; giữ phần dựng hết cuốn W-13 mở, chưa duyệt chi hay mở W-15/W-23 |
| 2026-10-19 | kiểm lại W-13 sau doc-6 hoàn tất | Codex | đạt nghiệm thu W-13 | hai kho tái lập succeeded, đủ bốn bước, 0 lời gọi/0 USD; DB/artifact/PDF khớp; 83 test gộp đạt, mutation bỏ sửa cache bị bắt |
| 2026-10-19 | kiểm lại W-24 bản 7baa7d2 | Codex | đóng lỗi runtime cũ, chưa đóng toàn vé | GIF tĩnh bốn preview, vùng bấm cũ đạt, ba mutation token bị bắt, chat an toàn với payload thử; còn Figma/trang/prototype và khung auth 390 |
