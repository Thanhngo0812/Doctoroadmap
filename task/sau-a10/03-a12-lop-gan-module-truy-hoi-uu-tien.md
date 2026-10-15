# SA-03 — A12: lớp gán module, truy hồi ưu tiên module, `search_document`

**Nguồn chân lý:** [ADR 0013](../../doc/adr/0013-lop-gan-module-va-media-da-xac-nhan.md); [spec Pha B](../../doc/pha-b-spec.md), mục 3 và 10,
bất biến 16; [báo cáo trợ lý](../../report/nghien-cuu-tro-ly-hoi-dap-do-thi-2026-10-11.md), mục 1.2, 1.4, 3.4.
**Ai:** nhân viên · Claude kiểm · **Chi phí mô hình:** 0 USD, trừ embedding câu truy vấn khi thử bằng CLI · **Chặn bởi:** không, làm ngay
được · **Trạng thái:** ready-for-agent

## Vì sao

Hiện trạng có ba vấn đề:
- Trường `stage_id` của chỉ mục luôn rỗng.
- `chunk_module_map` chỉ phủ 28–63% chỉ mục.
- Trợ lý cần ưu tiên module người học đang mở, nhưng không được chặn phần còn lại của tài liệu.

## Cần làm

**Lệnh A12** sinh lớp gán module cho mỗi cặp (phiên bản đồ thị, phiên bản chỉ mục):
- Mỗi chunk có `module_id`, `all_module_ids` và `module_source` ∈ {`chunk_module_map`, `hint`, `none`}.
- `hint` là module của chunk dạy gần nhất đứng trước chunk đó.
- Không ghi lại tệp vector.

**Đổi tên `stage_id` thành `module_id`** trong mô hình chỉ mục; vẫn đọc được artifact cũ.

**Truy hồi lai:**
- Giữ BM25, dense và RRF như hiện tại.
- Thêm bước xếp ưu tiên theo module đang mở:
  - lấy 20 đoạn đầu;
  - chia suất: tối đa 3 đoạn thuộc module đang mở hoặc module trước; tối đa 2 đoạn bất kỳ nếu nằm trong top 5 của cả tài liệu;
  - tổng không quá 6 đoạn.
- **Không lọc.** Mỗi đoạn mang quan hệ vị trí `truoc`, `dang_mo`, `sau` hoặc `khong_ro`.

**Công cụ** `search_document(query, scope, k)` theo spec mục 10, với `scope` ∈ {ưu tiên module, cả tài liệu, một module}.

**Lệnh tìm kiếm CLI** nhận module đang mở và in quan hệ vị trí của từng đoạn; cờ lọc theo stage cũ được thay.

**Từ chối chỉ mục lệch phiên bản chunk:** nếu chỉ mục không khớp chunk của đồ thị thì từ chối, kèm thông báo rõ. Ví dụ: doc-1 phải dùng chỉ mục
bản mới nhất; hai bản đầu đã cũ.

## Tiêu chí nghiệm thu

- [ ] Sáu cuốn: báo tỉ lệ chunk theo từng `module_source`. Số này là thông tin, không phải cổng; báo cáo nghiên cứu ước khoảng 74–99%.
- [ ] Băm tệp vector và tập `chunk_id` trước và sau A12 giống hệt.
- [ ] Test, mỗi cái thấy đỏ trước:
  - đoạn của module sau vẫn có mặt (không lọc);
  - hai đoạn cùng điểm thì đoạn thuộc module đang mở đứng trước;
  - chunk bài tập không có module vẫn được truy hồi;
  - chunk không dạy khái niệm nào nhận `hint` đúng theo chunk dạy đứng trước;
  - chỉ mục lệch phiên bản bị từ chối.
- [ ] Đo giây mỗi truy vấn trên doc-4, chỉ phần truy hồi cục bộ, không tính embedding.

## Ngoài vé

Hai việc không thuộc vé này:
- gắn media vào module;
- tách từ tiếng Việt cho BM25, vốn chỉ là nhánh thí nghiệm của vé 23.
