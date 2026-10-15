# SA-01 — Nền Pha B: kho lưu trữ, sổ chi, giới hạn dùng chung

**Nguồn chân lý:** [spec Pha B](../../doc/pha-b-spec.md), mục 7, 12, 15 và các bất biến 6, 13, 15 của phần "Quyết định kiểm thử".
**Ai:** nhân viên · Claude kiểm · **Chi phí mô hình:** 0 USD · **Chặn bởi:** không, làm ngay được · **Trạng thái:** ready-for-agent

## Vì sao

Bài giảng, quiz, trợ lý và tài liệu theo yêu cầu đều cần năm thứ giống nhau:
- một kho lưu trữ có cache chung và bản ghi theo người học;
- một sổ chi ghi mọi lời gọi;
- khoá chống sinh trùng;
- giới hạn dùng chung cho cả prompt lẫn luật kiểm;
- hàm kiểm câu trích nguyên văn.

Làm phần chung này trước để các vé sau chỉ còn phần riêng của mình.

## Cần làm

**Kho Pha B** là một port có hai bản cài: bản tệp JSON trong thư mục artifact (dùng cho CLI) và bản trong bộ nhớ (dùng cho test). Kho chứa:
- cache chung theo khoá;
- bản ghi theo người học: lần làm quiz, tài liệu, phiên hội thoại;
- phản hồi: báo sai quan hệ, báo câu hỏi lỗi, tắt nhắc khái niệm nền;
- sổ chi.

**Chống sinh trùng và cache âm:**
- Nhiều yêu cầu đồng thời cùng một khoá chỉ chạy một lần sinh; người đến sau nhận cùng kết quả.
- Lần sinh lỗi không vào cache, chỉ ghi cache âm có hạn (mặc định 60 giây).

**Sổ chi Pha B:**
- Mỗi lời gọi mô hình hay embedding ghi một dòng: mục đích, `model_id`, token vào/ra/suy nghĩ, USD tính theo bảng giá có sẵn của dự án, TTFT,
  tổng ms, `context_hash`, `doc_id`, người học nếu có.
- Lệnh CLI tóm tắt sổ chi theo tài liệu và mục đích: số lời gọi, token, USD, giây chờ ở p50 và p90.

**Giới hạn dùng chung:** mỗi chức năng khai báo giới hạn của mình ở một chỗ (độ dài, số mục, trần). Prompt đọc giá trị đó để viết vào chỉ dẫn, luật
kiểm đọc cùng giá trị. Lý do: ở xstk, mô hình hỏng 8/8 lời gọi vì một luật độ dài không có trong prompt.

**Cấu hình Pha B** theo spec mục 15: mô hình, nhiệt độ, `maxOutputTokens`, trần. Phần cấu hình ảnh hưởng đầu ra đi vào khoá cache.

**Câu trích nguyên văn:** dùng chung hàm kiểm câu trích nguyên văn đã có của A8 (NFC, chuẩn hoá khoảng trắng), không viết bản thứ hai.

## Tiêu chí nghiệm thu

- [ ] Một bộ test hợp đồng chạy trên cả hai bản cài của kho, cho cùng kết quả.
- [ ] Test đồng thời: N luồng cùng khoá thì hàm sinh chạy đúng một lần, mọi luồng nhận cùng kết quả. Lần sinh lỗi không vào cache, và cache âm hết
      hạn đúng lúc.
- [ ] Đổi một giới hạn ở nguồn chung thì chữ prompt và luật kiểm đổi theo. Test phải đỏ trên bản viết cứng giá trị ở hai nơi.
- [ ] Lệnh tóm tắt sổ chi chạy được trên sổ rỗng và trên sổ dữ liệu mẫu, không gọi mô hình.
- [ ] Test kiến trúc vẫn xanh: application không import infrastructure.

## Ngoài vé

Hai việc không thuộc vé này:
- lược đồ Postgres, việc của nhóm web theo hợp đồng của port;
- mọi lời gọi mô hình thật.
