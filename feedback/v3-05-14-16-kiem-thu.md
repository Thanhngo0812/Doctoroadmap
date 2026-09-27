# Feedback triển khai v3-05, v3-14, v3-16

**2026-09-27 — mã và kiểm thử hoàn tất, chờ reviewer nghiệm thu.** [Báo cáo đầy đủ](../report/v3-05-14-16-ket-qua-2026-09-27.md); [vé 05](../task/v3-lo-trinh-doc-duoc/05-neo-chi-tu-vung-day.md), [vé 14](../task/v3-lo-trinh-doc-duoc/14-vai-tro-cau-truc-da-ngon-ngu.md), [vé 16](../task/v3-lo-trinh-doc-duoc/16-ten-ky-hieu-da-chu-viet.md).

- 05: 0 neo ngoài `noi_dung`; doc-1 và nhap-mon-ml không mở bằng đề cương/lời mở đầu. Q6 tái áp dụng 10b: doc-1 3/39 so với 1/39 cũ; doc-2 2/57 so với 3/57 cũ. Hai lỗi tăng ở doc-1 là node chỉ được nhắc, chuyển xem ở vé 07.
- 14: nhãn nghĩa sáu vai trò đã chạy cho sáu tài liệu/bảy version chunk. Doc-2 v5 có 207 chunk bài tập so mốc tham khảo khoảng 161; reviewer cần kiểm. Không đổi hash chunk doc-1/doc-4/xstk.
- 16: 0 khác biệt tên, nhắc tên, BM25 trên sáu tài liệu phát triển; chưa có T19 để kiểm tài liệu thật ngoài vi/en.
- Unit/integration xanh; tổng chi 05+14 là 0,47219525/1,00 USD, không chạy lại A8. Vé 15/17/T19 vẫn hoãn theo yêu cầu.
