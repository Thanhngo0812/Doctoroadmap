# v4-12 — D-01 bước 2: chạy A2 → A9'' trên 16 cuốn học, xuất phiếu gán nhãn

**Nguồn chân lý:**
- [đặc tả D-01](D-01-dac-ta-du-lieu-pass-phu.md) (định dạng phiếu, kiểm chất lượng);
- [kiểm rộng 16 cuốn](../../report/v4-10-buoc-2b-kiem-rong-16-cuon-2026-10-05.md) (A1);
- [nghiên cứu pass phụ không LLM vòng 1](../../report/nghien-cuu-pass-phu-khong-llm-vong-1-2026-10-05.md).

**Ai:** nhân viên · **Phụ thuộc:** — · **Chi phí mô hình:** khoảng 20 USD qua Vertex. Chủ dự án duyệt ngày 2026-10-05: "duyệt chi tất cả tiền
miễn là dùng vertex".

**Trạng thái:** Claude chạy dở, bàn giao 2026-10-05 lúc 17:15 theo yêu cầu chủ dự án. Mọi tiến trình đã dừng; khâu xong đã lưu.

## Quyết định đã chốt — không đổi trong vé này

- **Chỉ qua Vertex** (`llm_transport=vertex`), chỉ `gemini-3.1-flash-lite`. Script điều phối tự dừng nếu đường gọi không phải Vertex.
- **Quyền dùng sách:** chủ dự án đã tự kiểm định 16 cuốn, kể cả gửi lên Gemini. **Không mở 2 cuốn `document-data/test/`** (tập giữ lại T-01).
- **Dừng sau A9'' (danh tính), không chạy A8.** Chủ dự án đồng ý. Đo 0 USD cho thấy bỏ đặc trưng pass chính không làm hụt có ý nghĩa bộ kiểm cạnh.
- **A1 đã xong cho cả 16 cuốn.**
  - Bộ đọc chữ là `--pdf-backend pypdfium2`, vì docling-parse giải mã hỏng d01-01.
  - **Sơ đồ tiêu đề mặc định** (không `vn-textbook`): `vn-textbook` lồng sai "CHƯƠNG II" vào mục "BÀI TẬP CHƯƠNG I" ở d01-02.
- **Chuỗi lệnh theo đúng chuỗi v3** của tài liệu tiếng Việt (doc-4, xstk):
  `label-roles --allow-spend` → `a3` → `a4 --names-only` → `roadmap --dry-run --stop-after identity` →
  `roadmap --allow-spend --stop-after identity`.

## Trạng thái bàn giao

| cuốn | lĩnh vực | đã có | còn lại |
|---|---|---|---|
| d01-01 | Toán | chunk vai trò v3 (gán trên v2 pypdfium2) | A3 (3 lượt đều "coverage_incomplete", không lưu) → A4 → roadmap |
| d01-02 | Toán | **xong tới danh tính** (graph v5); 0,89 USD | — |
| d01-03 | Hoá | **xong tới danh tính** (graph v5); 1,50 USD | — |
| d01-04 | Hoá | tới C8 (graph v4); 1,57 USD | `roadmap --stop-after identity` (tự tái dùng v1–v4) |
| d01-05 | Sinh | chunk vai trò v2 | A3 (lượt dở bị dừng) → A4 → roadmap |
| d01-06 → d01-15 | 6 lĩnh vực | chunk v1 (A1) | A2 → A3 → A4 → roadmap |
| d01-16 | Nông nghiệp | chunk vai trò v2. Vòng A2 của Claude chưa dừng hẳn, chạy xong lúc 17:22, sau yêu cầu ngưng; khoảng 0,005 USD | A3 → A4 → roadmap |

Chi đã ghi trong manifest: 3,96 USD. Các lượt A3 hỏng của d01-01 và d01-05 không để lại số đo, ước 2–3 USD; số chính xác xem trên hoá đơn Vertex.
Nhật ký từng bước: `tmp/pass-phu-ml/d01-chay*.jsonl`.

## Việc cần làm

### 1. Sửa hai lỗi chặn trước khi chạy tiếp (đo được ngày 2026-10-05)

- **A2 không thử lại.**
  - `composition.build_region_roles` dựng mô hình với `max_retries=0`. Vertex trả **HTTP 429 RESOURCE_EXHAUSTED** (hạn mức dùng chung) mỗi khi
    có khâu khác cùng gọi, nên một lời gọi dính 429 là hỏng cả khâu. Đã gặp ở 10 cuốn, kể cả khi chạy tuần tự.
  - Sửa: cho A2 dùng cùng chính sách thử lại với các khâu khác, chờ tăng dần, tôn trọng `Retry-After`.
  - Không đổi prompt, khoá cache hay đầu ra.
  - Test: giả lập 429 rồi thành công thì khâu hoàn tất. Test phải đỏ trên mã hiện tại.
- **A3 báo thành công khi không ghi gì.**
  - Khi `coverage_incomplete` (có mục hỏng, ở đây do 429), lệnh `a3` in "artifact: không ghi vì coverage_incomplete" mà **vẫn thoát mã 0**.
  - Sửa: thoát mã khác 0 và in rõ các mục hỏng. Test.
- **Nên làm thêm, có thể tách vé:**
  - A3 không có điểm lưu, nên mỗi lần chạy lại tốn trọn chi phí (d01-01 đã mất 3 lượt). Cần lưu kết quả theo mục và tái dùng ở lượt sau,
    không đổi đầu ra.
  - Thử lại của A3 nên chờ lâu hơn khi gặp 429. Hiện chỉ chờ khoảng 1, 2, 4 giây.

### 2. Chạy tiếp, **mỗi lúc một cuốn**

- Chạy song song nhiều cuốn làm tăng 429 và không nhanh hơn.
- Dùng được `scripts/pass-phu-ml/chay_d01.py` của Claude:
  - chờ `ingest` xong;
  - chạy lại khi gặp lỗi tạm thời hoặc A3 thiếu mục;
  - kiểm có artifact ứng viên rồi mới sang A4;
  - ghi nhật ký.
- Lệnh mẫu: `.venv/Scripts/python.exe scripts/pass-phu-ml/chay_d01.py --chi=d01-04,d01-05,...,d01-16,d01-01 --nhat-ky=tmp/pass-phu-ml/d01-chay-nv.jsonl`.
  Cuốn đã xong khâu nào thì luồng tự tái dùng khâu đó.
- **Không bọc lệnh bằng `timeout`**: một cuốn có thể chạy quá 30 phút.

### 3. Xuất phiếu

- Môi trường riêng `tmp/venv-ml` (cần underthesea để khớp tên theo ranh giới từ). Cách dựng ở mục "Chạy lại" của báo cáo vòng 1.
- Lệnh: `tmp/venv-ml/Scripts/python.exe scripts/pass-phu-ml/xuat_phieu.py`.
- Đầu ra:
  - `tmp/d01-phieu/phieu.jsonl` (giao chủ dự án cho agentic);
  - `tmp/d01-phieu/khoa.jsonl` (đáp án phiếu kiểm và nguồn phiếu lặp). **Không giao `khoa.jsonl` cho agentic.**
- Đã thử trên xstk: 71 phiếu, 696 cặp, định dạng đúng D-01.

### 4. Sổ chi

`scripts/do-chi-phi/bao_cao.py <doc>` cho từng cuốn; cộng tổng. Báo kèm cờ "thiếu": Vertex đôi khi không trả số token.

## Nghiệm thu

- 16/16 cuốn có artifact `identity`. Bảng mỗi cuốn: số khái niệm; số khái niệm làm được đích (`taught`/`uncertain`, học được); phút; USD.
- Tổng chi ≤ khoảng 25 USD. Vượt thì dừng và báo.
- Phiếu: số phiếu thật, phiếu kiểm, phiếu lặp, tổng cặp cần gán. Kiểm 5 phiếu ngẫu nhiên bằng mắt (câu cửa sổ, câu neo, ứng viên có tên trong câu).
- Sửa A2 và A3: test mới đỏ trên mã cũ, xanh sau sửa; toàn bộ test xanh; khoá cache các khâu không đổi.
- Không tệp nào trong `document-data/test/` bị đọc.

## Ghi nhận, không sửa trong vé này

- **A2 gán sai vùng ở d01-02:** trang 1–96 (Chương I–III) bị gán `mo_dau`.
  - Lỗi do luật cấu trúc tất định; LLM chỉ được hỏi 4 lần.
  - Có dòng đầu trang VNI "BOÄ MOÂN TOAÙN" bị nhận là tiêu đề.
  - Cuốn này vì thế ít khái niệm được dạy hơn. Để vé A2 sau.
- **`vn-textbook` đẩy tiêu đề không đánh số** ("BÀI TẬP CHƯƠNG I") lên trên "CHƯƠNG II". Để vé A1/A2 sau.
