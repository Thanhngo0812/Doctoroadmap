# 03 — Stage `mentions`: mention map, viện dẫn, cặp chạm, cặp nghi tiên quyết

**What to build:** Từ bảng node canonical và chunk, dựng **mention map** hai kênh rồi suy ra **viện dẫn**, **cặp
chạm**, **sổ cặp cụm** và **cặp nghi tiên quyết**. Dừng ở stage này vẫn **không có lời gọi mô hình phán nào** —
đây là cấu hình mà vé 05 và 12 dùng để đo.

Luật ở spec D4, D5.

**Blocked by:** 02 — cặp chạm cần `cluster_id`.

**Status:** done — 2026-09-16

- [x] Kênh exact: chuẩn hoá NFC, casefold, vị trí dấu thanh, biến thể i/y; **không bỏ dấu**; khớp dài nhất bên
      trái; bỏ khớp lồng; bỏ qua ký hiệu; loại tên quá chung.
- [x] Kênh dense: dùng lại vector chunk có sẵn trong artifact truy hồi, chỉ embed phía node theo kiểu
      `RETRIEVAL_QUERY`; chuẩn hoá hai phía; lọc top-k theo hàng. Kênh này **chỉ đề cử**.
- [x] Mention map ghi ba mức tin: định nghĩa, trích, nhắc. Độ tin tuyệt đối chỉ dành cho mức định nghĩa.
- [x] Viện dẫn **có hướng**; cặp chạm **vô hướng** và chỉ giữa hai cụm chủ đề khác nhau.
- [x] Sổ cặp cụm giữ **hai bộ đếm tách rời** cho hai kênh, trọng số hạ theo số khái niệm trong chunk, ngưỡng mở
      phiên là **tương đối** hoặc top-k, không phải số tuyệt đối.
- [x] Cặp nghi tiên quyết hợp đủ bốn nguồn ở D5; **mỗi cặp ghi rõ nguồn nào đề cử nó**.
- [x] Cờ khái niệm thiếu: cụm từ lặp nhiều không khớp node nào.
- [x] Số đo trên bốn tài liệu cũ dán vào vé: số mention theo từng mức và từng kênh, số cặp theo từng bộ sinh, số
      cặp chạm, số cặp nghi tiên quyết, số lượt embedding và chi phí.
- [x] Test theo hai seam như vé 02; đột biến tối thiểu: bật bỏ dấu, bỏ luật khớp dài nhất, trộn hai bộ đếm làm
      một, dùng ngưỡng tuyệt đối, để ký hiệu tham gia khớp.

## Feedback nghiệm thu

| Tài liệu | Mention (định nghĩa / trích / nhắc) | Kênh (provenance / extraction / exact / dense) | Viện dẫn | Cặp chạm | Cặp nghi | Cờ thiếu | Embed |
|---|---|---|---:|---:|---:|---:|---:|
| `baocao-canhan` | 132 (48 / 9 / 75) | 48 / 9 / 81 / 108 | 261 | 188 | 251 | 1 | 36 |
| `naive-bayes` | 147 (43 / 19 / 85) | 43 / 19 / 82 / 102 | 170 | 128 | 180 | 2 | 34 |
| `nhap-mon-ml` | 329 (85 / 18 / 226) | 85 / 18 / 198 / 225 | 843 | 854 | 1.057 | 3 | 75 |
| `xstk-ch3-1` | 776 (115 / 37 / 624) | 115 / 37 / 602 / 294 | 748 | 897 | 1.107 | 31 | 98 |

- Chi phí embedding không có usage token trả về trong artifact nên không giả làm số đo tuyệt đối. Ước tính bằng
  tokenizer cục bộ, theo giá paid Standard `gemini-embedding-001` 0,15 USD/1M token ngày 2026-09-16:
  `baocao-canhan` 3.632 token ≈ 0,000545 USD; `naive-bayes` 3.393 ≈ 0,000509 USD; `nhap-mon-ml` 5.498 ≈
  0,000825 USD; `xstk-ch3-1` 8.141 ≈ 0,001221 USD. Free tier là 0 USD. Nguồn giá:
  <https://ai.google.dev/gemini-api/docs/pricing>.
- Sổ từng cặp nghi ghi hợp nguồn `same_section`, `citation`, `contact`, `proposed_relation`; hai bộ đếm exact và
  dense không trộn.
- Mutation đã thử và đều bị test bắt: bỏ dấu; bỏ longest-leftmost; trộn bộ đếm; thay ngưỡng tương đối bằng
  ngưỡng tuyệt đối; thêm cosine floor tuyệt đối; cho ký hiệu tham gia exact match.
