# 07 — CONTEXT, ADR 0002 và đối chiếu tài liệu thật

**What to build:** Từ điển thuật ngữ nói đúng sự thật, quyết định kiến trúc được ghi lại để không ai vô tình
phá, và toàn bộ đợt được **nhìn bằng mắt** trên giáo trình thật.

Phép kiểm bằng mắt trên tài liệu thật là thứ đã phát hiện ra cả ba đợt vá trước — mỗi lần bộ test đều xanh và
không cái nào thấy gì. Vì vậy nó là một ticket riêng, không phải một dòng nghiệm thu bị lướt qua ở cuối ticket
khác.

**Blocked by:** 03 và 06 — mọi thay đổi phải nằm đủ trước khi đối chiếu mới có nghĩa.

**Status:** completed — 2026-08-20

## Từ điển thuật ngữ

- [x] Sửa mục **Chunk**: nó vẫn định nghĩa chunk là *một khối lá sau khi chuẩn hoá*, trong khi từ đợt gộp khối
      một chunk là **một nhóm khối lá liền kề trong cùng một section** — và sau đợt này còn có thể chứa cả văn
      bản, hình lẫn bảng
- [x] Thêm ba thuật ngữ: **hình**, **tham chiếu hình**, **chú thích mồ côi**
- [x] Mỗi thuật ngữ kèm mục *tránh dùng*, theo đúng khuôn của các mục sẵn có

## ADR 0002

- [x] Ghi **bốn quyết định như một khối gắn liền**, vì tách rời ra thì từng cái đều có vẻ tuỳ tiện: hình là sản
      phẩm của parse; định danh hình băm theo nội dung; tham chiếu hình đứng **ngoài** khoá băm chunk; bước
      ingest không biết đồ thị tồn tại
- [x] Ghi rõ điểm yếu còn lại: đổi độ phân giải trích ảnh làm đổi **mọi** định danh hình
- [x] Ghi rõ vì sao chấp nhận được: vì quyết định thứ ba khiến định danh chunk **không gãy theo**
- [x] Ghi các phương án đã cân nhắc và bị loại, kèm lý do — đặc biệt là kho ảnh dùng chung giữa các tài liệu

## Đối chiếu trên `nhap-mon-ml`

- [x] Xoá artifact cũ rồi ingest lại từ đầu
- [x] **Chín** file ảnh có mặt trên đĩa, trong thư mục của phiên bản parse
- [x] Bức hình bên phải trang 9 — trước nay mất hẳn — **có node và có chunk**
- [x] Chú thích cụm hình trang 7 có mặt trong chuỗi văn bản đầy đủ
- [x] **Không node nào** có phần văn bản dài bất thường — mìn base64 không quay lại
- [x] Không còn chunk nào dưới 32 token chỉ vì nó là chú thích hình
- [x] Có chunk khai loại mục danh sách — hiện tại không có cái nào
- [x] Tập định danh chunk **khác** tập cũ, đúng như dự kiến của đợt này
- [x] Bất biến vị trí ký tự vẫn đúng với mọi chunk
- [x] Manifest ghi đủ: phiên bản adapter mới, phiên bản thuật toán `section-id-v4`, độ phân giải trích ảnh

## Đóng đợt

- [x] Toàn bộ bộ test xanh
- [x] Ghi lại số đo sau đợt để lần sau còn đối chiếu: số ảnh, số chunk, trung vị token, dung lượng ảnh
