# SA-02 — Đồ thị học: mô hình đọc, nhãn nguồn, công cụ tra đồ thị

**Nguồn chân lý:** [spec Pha B](../../doc/pha-b-spec.md), mục 6 và 10 (bảng công cụ), bất biến 4;
[báo cáo trợ lý](../../report/nghien-cuu-tro-ly-hoi-dap-do-thi-2026-10-11.md), mục 1.3, 1.5, 3.3.
**Ai:** nhân viên · Claude kiểm · **Chi phí mô hình:** 0 USD · **Chặn bởi:** không, làm ngay được · **Trạng thái:** ready-for-agent

## Vì sao

Bài giảng, quiz, trợ lý và tài liệu đều đọc cùng một đồ thị và phải tuân cùng các luật an toàn. Ví dụ: không hiện cạnh mở kiểu `requires` chưa
kiểm; chỉ hiện media đã xác nhận. Đặt mọi phép đọc vào một module thuần, nạp một lần, thì các luật này chỉ phải viết và kiểm ở một chỗ.

## Cần làm

**Mô hình đọc đồ thị học** nạp một lần cho mỗi cặp (tài liệu, phiên bản đồ thị). Nó đọc:
- artifact graph;
- chunk cùng phiên bản;
- chữ thô công thức từ cây parse.

**Bảng nhãn nguồn:** các nhãn `S#`, `N#`, `Q#`, `R#`, `H#`, `B#`, `CT#`, `K#`, `D#` ánh xạ hai chiều với `chunk_id`, trang, khoảng ký tự, đường mục.

**Sáu công cụ tra cứu.** Mỗi công cụ là hàm thuần, trả JSON có trần độ dài theo spec mục 10:

| công cụ | quy định |
|---|---|
| `lookup_concept` | Khớp tên, alias, `display_name` theo ranh giới âm tiết, tên dài nhất trước. **Tên phổ biến** chỉ được nhận khi câu hỏi gần như chỉ gồm tên đó. Ví dụ: "chất" có ở 297/671 chunk doc-4. Ngưỡng "phổ biến" nằm trong cấu hình. Tên trùng giữa hai khái niệm thì trả cả hai, không đoán |
| `get_module_info` | Thông tin module |
| `why_here` | Tối đa 3 tiên quyết Hasse, mỗi cái kèm `quote`, trang, `soft_reason`, `order_relation`. Cạnh `cong_cu` ghi "công cụ, không bắt buộc". Cạnh ngược thứ tự sách ghi "sách trình bày ở phần sau" |
| `path_to` | Bọc phép tính lộ trình tới khái niệm đích, bỏ cạnh mềm. Tối đa 12 module, phần còn lại gộp "và N module nữa" |
| `traverse` | `requires` chỉ đọc `requires_edges`. Cạnh mở kiểu `requires` **không bao giờ** ra. Cạnh mở không có câu trích thì không ra |
| `get_media` | Chỉ cạnh `confirmed`, tối đa 2, kèm `caption_source` |

**Quan hệ vị trí** của một module hay một chunk với module đang mở: `truoc`, `dang_mo`, `sau`, `khong_ro`. Vé này tính theo `chunk_module_map`;
vé 03 bổ sung gợi ý module.

**Lệnh CLI** gọi từng công cụ trên một tài liệu và in JSON.

## Tiêu chí nghiệm thu

- [ ] Chạy cả sáu công cụ trên sáu cuốn phát triển. Báo cỡ kết quả lớn nhất của từng công cụ (token ước), phải nằm trong trần.
- [ ] Test, mỗi cái thấy đỏ trước trên bản sai:
  - cạnh mở kiểu `requires` không bao giờ ra;
  - media chưa `confirmed` không bao giờ ra;
  - cạnh `cong_cu` và cạnh ngược thứ tự sách mang đúng ghi chú;
  - tên trùng trả nhiều ứng viên;
  - tên phổ biến bị chặn khi câu hỏi dài.
- [ ] `path_to` trên doc-4, với một đích có lộ trình dài, liệt kê không quá 12 module và có dòng "và N module nữa".
- [ ] Mọi nhãn trong một kết quả tra ngược được về `chunk_id`, trang, khoảng ký tự. Câu trích `Q#` trùng nguyên văn `quote` của cạnh.
- [ ] Báo giá trị ngưỡng "tên phổ biến" đã chọn, và số tên bị ảnh hưởng ở mỗi cuốn.
- [ ] 0 USD: không gọi mô hình, không gọi embedding.

## Ngoài vé

Ba việc không thuộc vé này:
- `search_document` (vé 03);
- tra khái niệm theo mô tả (vé 07);
- định nghĩa công cụ cho mô hình và vòng agent (vé 08).
