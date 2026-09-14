# 04 — Nối run định dạng trên đường không-bố-cục (F38)

**What to build:** Câu bị Word xé vì chữ đậm giữa câu — `'+ Triển khai dự án bằng'` /
`'Docker Compose'` / `', thực hiện kiểm thử…'` — vào chunk thành **một** câu liền, không gãy dòng
giữa chừng. Đo hiện trạng: 25/240 khối văn bản của DOCX (10%) mở đầu như đứng giữa câu.

## Luật

Chạy cho node **không có khung toạ độ** (đường DOCX — dòng chảy logic; PDF có bbox không đi đường
này, phép nối trang PDF hiện hành giữ nguyên):

- Hai khối văn bản liền nhau, cùng section, khối trước **không kết thúc bằng dấu kết câu** ⇒ nối.
- **Guard:** khối sau mở đầu bằng dấu hiệu liệt kê hoặc đánh số (`+`, `-`, bullet, `1.`, `a)`…)
  ⇒ **không** nối — hai bullet thủ công liền nhau phải đứng riêng.
- **Nối theo chuỗi:** khối đã nối tiếp tục xét nối với khối sau — ca ba mảnh ở trên phải ra một khối
  qua hai lần nối, kể cả khi mảnh giữa mở đầu bằng chữ hoa (`Docker Compose`).
- Tái dùng bộ dấu kết câu và tập loại được-nối của phép nối trang PDF; chỉ bỏ điều kiện ranh trang.
- Mỗi lần nối đếm vào thống kê parse (`runs_stitched`), không cảnh báo từng dòng.

Rủi ro đã chấp nhận trong spec: văn bản cố tình xuống dòng không dấu câu (thơ, địa chỉ) sẽ bị nối —
chấp nhận cho thể loại tài liệu học thuật; guard liệt kê chặn phần lớn ca thật.

**Blocked by:** 03 — cùng vùng adapter, làm nối tiếp để không giẫm chân; phiên bản đã nhích ở 03,
ticket này **không** nhích nữa.

**Status:** done

- [x] Ca ba mảnh thật của tài liệu ra một khối: `'+ Triển khai dự án bằng Docker Compose, thực hiện
      kiểm thử đầu cuối…'`
- [x] Có test: hai bullet `+` liền nhau **không** dính
- [x] Có test: khối kết thúc bằng dấu kết câu **không** nối với khối sau
- [x] Có test: chuỗi ba mảnh nối qua hai bước, mảnh giữa mở đầu chữ hoa
- [x] Có test: node có bbox (đường PDF) không đi qua luật này
- [x] Trên fixture DOCX: số khối mở-đầu-như-giữa-câu giảm về gần 0; `runs_stitched` ghi số thật
- [x] Số vàng: DOCX đổi (văn bản chunk liền mạch, một số định danh đổi theo — liệt kê trong commit);
      **ba tài liệu PDF đứng yên mọi cột**
