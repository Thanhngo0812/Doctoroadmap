# D-04a — Xuất phiếu cạnh ngược thứ tự sách, kèm bộ kiểm định dạng

**Nguồn chân lý:** [đặc tả D-04](D-04-dac-ta-nhan-canh-nguoc.md), bước 1, bước 2, mục "Kiểm chất lượng"; báo cáo vòng 2, mục 8.12 và 8.13.
**Ai:** Claude (chủ dự án giao 2026-10-15, thay nhân viên) · **Chi phí mô hình:** 0 USD · **Chặn bởi:** không · **Trạng thái:** xong 2026-10-15

## Vì sao

E8 cần biết từng cạnh mà R17 làm mềm vì "ngược thứ tự sách" có đúng không, và nếu đúng thì có nên đảo thứ tự sách không. Vàng phát triển gần như
không chấm được các cạnh này. Vé này dựng gói phiếu để agentic gán nhãn.

## Cần làm

Một script nghiên cứu trong nhóm script pass phụ ML (không sửa `src/`), chạy từ gốc repo, 0 USD, không gọi mô hình. Script ghi vào `tmp/` (không vào git) bốn thứ:
- **phiếu:** đúng định dạng ở bước 2 của đặc tả, đã chèn phiếu lặp và xáo thứ tự;
- **khoá:** mỗi `phieu_id` kèm nguồn, hệ đề xuất (LLM v3, E5, cả hai), pass chính hay pass phụ, confidence, xác suất E5, nhãn D-01, `doc_id`,
  `x_id`, `y_id`, và phiếu lặp của phiếu nào;
- **bảng đếm:** số cặp theo nguồn, sách và tầng;
- **manifest:** hạt giống, băm SHA-256 của phiếu và khoá, phiên bản artifact đã đọc.

**Nguồn 1 (doc-1, xstk-ch3-1, doc-4):**
- Cặp là mọi cạnh mà R17 làm mềm vì "ngược thứ tự sách" khi phát lại A9 → A10, với cạnh pass phụ của LLM v3 và của E5 (`e5-a-hieu-chinh`).
- Dùng lại đường phát lại sẵn có của E4 và E8. Không dựng lại vị trí dạy theo cách khác.
- Gộp trùng theo (X, Y).

**Nguồn 2 (16 sách học D-01):**
- Đầu vào: bảng cặp D-01, nhãn lượt A, và điểm ngoài mẫu của E5.
- Vị trí dạy tính theo đúng khoá vị trí của A10: chunk dạy sớm nhất trong vùng nội dung. Bỏ cặp cùng chunk.
- Lấy mẫu như đặc tả: tối đa 60 cặp mỗi sách, chia hai tầng "cùng chương" và "khác chương", hạt giống cố định.

**Cửa sổ:** cửa sổ của Y và của X dựng bằng cùng hàm cửa sổ định nghĩa mà phiếu D-01 dùng, ở chỗ dạy của từng khái niệm.

**Bộ kiểm định dạng nhãn** (agentic chạy được, chỉ cần Python chuẩn) đọc phiếu cùng một tệp nhãn, rồi báo từng lỗi kèm `phieu_id`:
- dòng không đọc được, hoặc thiếu trường;
- nhãn ngoài bảy giá trị;
- phiếu thiếu nhãn, hoặc có nhiều hơn một nhãn trong một lượt;
- chỉ số câu nằm ngoài danh sách câu;
- `cau_giai_thich` có mặt mà nhãn khác `du_tai_cho`, hoặc vắng mặt khi nhãn là `du_tai_cho`.

Bộ kiểm không đọc khoá.

## Nghiệm thu

- [x] Tập (X, Y) của nguồn 1, theo từng tài liệu và từng hệ, trùng đúng tập cạnh bị làm mềm vì "ngược thứ tự sách" trong phương án `bat` của
      `thi_nghiem_e8.py`. Ở doc-4: 304 cạnh của E5 và 201 cạnh của LLM v3, trước khi gộp trùng.
- [x] Không phiếu nào thuộc hai sách T-01. Có test với một sách T-01 giả.
- [x] Phiếu không chứa trường nào của khoá. Test cài một giá trị giả vào khoá và kiểm nó không xuất hiện trong phiếu.
- [x] Nguồn 2: cặp nào cũng có X dạy sau Y; mỗi sách không quá 60 cặp; chạy lại với cùng hạt giống ra phiếu y hệt (cùng băm).
- [x] 5% phiếu lặp, mỗi phiếu lặp có thứ tự trình bày khác phiếu gốc; khoá ghi đúng cặp gốc–lặp.
- [x] Mỗi loại lỗi định dạng ở trên có một test thấy bộ kiểm bắt được, và một test thấy tệp nhãn hợp lệ qua được.
- [x] Báo bảng đếm, kèm năm phiếu mẫu để Claude đọc.

## Kết quả (Claude, 2026-10-15)

- Script `xuat_phieu_d04.py` và bộ kiểm `kiem_nhan_d04.py` (nhóm script pass phụ ML); test ở `tests/unit/scripts/test_xuat_phieu_d04.py`,
  `test_kiem_nhan_d04.py` (17 test; hai test bảo vệ đã thấy fail khi cố ý làm hỏng mã). Đầu ra ở `tmp/d04-phieu/`.
- Cả hai nguồn chạy qua A10 thật, dừng ngay tại R17. Nguồn 2 nạp cặp đề xuất làm cạnh `requires` vào artifact danh tính D-01.
- **1.368 phiếu:** 439 cặp nguồn 1 (doc-4 410, doc-1 23, xstk 6), 864 cặp nguồn 2 (16 sách, 10–60 mỗi sách), 65 phiếu lặp.
  Nguồn 1 trước gộp trùng: doc-4 E5 304, LLM v3 201; doc-1 19 và 8; xstk 6 và 2, trùng đúng phương án `bat` của E8. Không cặp nào mất vì thiếu cửa sổ.
- Chạy hai lần ra phiếu và khoá cùng băm.
- **Đổi so với đặc tả ban đầu:** bỏ `khoang_cach` khỏi phiếu, chỉ giữ ở khoá. Ở doc-4, cấp 1 của cây mục bao cả một phần sách, nên có phiếu ghi
  "cùng chương" mà cách nhau 128 mục. Đặc tả đã sửa theo.
- Đọc mẫu: nhiều cặp nguồn 2 là liệt kê anh em ("thu nhập, sở thích…") hoặc nghĩa khác ("Kích thước" thuộc tính tập tin → "Bộ nhớ vật lý"), đúng
  loại mà nhãn `khong_tien_quyet` và `nghia_khac` cần bắt.
