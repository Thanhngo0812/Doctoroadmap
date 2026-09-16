# 03 — Stage `mentions`: mention map, viện dẫn, cặp chạm, cặp nghi tiên quyết

**What to build:** Từ bảng node canonical và chunk, dựng **mention map** hai kênh rồi suy ra **viện dẫn**, **cặp
chạm**, **sổ cặp cụm** và **cặp nghi tiên quyết**. Dừng ở stage này vẫn **không có lời gọi mô hình phán nào** —
đây là cấu hình mà vé 05 và 12 dùng để đo.

Luật ở spec D4, D5.

**Blocked by:** 02 — cặp chạm cần `cluster_id`.

**Status:** ready-for-agent

- [ ] Kênh exact: chuẩn hoá NFC, casefold, vị trí dấu thanh, biến thể i/y; **không bỏ dấu**; khớp dài nhất bên
      trái; bỏ khớp lồng; bỏ qua ký hiệu; loại tên quá chung.
- [ ] Kênh dense: dùng lại vector chunk có sẵn trong artifact truy hồi, chỉ embed phía node theo kiểu
      `RETRIEVAL_QUERY`; chuẩn hoá hai phía; lọc top-k theo hàng. Kênh này **chỉ đề cử**.
- [ ] Mention map ghi ba mức tin: định nghĩa, trích, nhắc. Độ tin tuyệt đối chỉ dành cho mức định nghĩa.
- [ ] Viện dẫn **có hướng**; cặp chạm **vô hướng** và chỉ giữa hai cụm chủ đề khác nhau.
- [ ] Sổ cặp cụm giữ **hai bộ đếm tách rời** cho hai kênh, trọng số hạ theo số khái niệm trong chunk, ngưỡng mở
      phiên là **tương đối** hoặc top-k, không phải số tuyệt đối.
- [ ] Cặp nghi tiên quyết hợp đủ bốn nguồn ở D5; **mỗi cặp ghi rõ nguồn nào đề cử nó**.
- [ ] Cờ khái niệm thiếu: cụm từ lặp nhiều không khớp node nào.
- [ ] Số đo trên bốn tài liệu cũ dán vào vé: số mention theo từng mức và từng kênh, số cặp theo từng bộ sinh, số
      cặp chạm, số cặp nghi tiên quyết, số lượt embedding và chi phí.
- [ ] Test theo hai seam như vé 02; đột biến tối thiểu: bật bỏ dấu, bỏ luật khớp dài nhất, trộn hai bộ đếm làm
      một, dùng ngưỡng tuyệt đối, để ký hiệu tham gia khớp.
