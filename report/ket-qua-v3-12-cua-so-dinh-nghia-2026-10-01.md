# Vé 12 — cửa sổ định nghĩa −4…+2 và pilot A8

Ngày 2026-10-01. Kết quả **chỉ trong kho đánh giá** `artifacts/v3-r12-window-evaluation/`. Chưa chạy pass phụ đầy đủ hoặc ghi đè cache production. Mốc so sánh là đồ thị cuối luồng cũ (`artifacts/v3-05b-a9v10-evaluation`, v6) **sau rút gọn bắc cầu**, không phải riêng pass chính cũ. Có thể tái lập bảng bằng `python scripts/doc-lo-trinh/so_sanh_a8_cua_so_v3.py` (0 USD). Nhãn vàng chỉ dùng để chấm và chọn ID của hai chương; không vào prompt.

## Hợp đồng và kiểm chứng

- Cửa sổ = câu neo + tối đa 4 câu trước, 2 câu sau trong cùng đoạn định nghĩa của chunk neo (ranh giới đoạn lấy từ dòng trống); hai số câu cấu hình qua `DOC2ROADMAP_A8_DEFINITION_BEFORE/AFTER`, nằm trong hash cache. Giữ tiêu đề khối nếu có. Với PDF không có dấu tách đoạn, ranh giới tốt nhất hiện có là cùng chunk; đây là giới hạn dữ liệu đầu vào.
- Câu trích nằm trong cửa sổ nhưng quên `chunk_id` neo: tự gắn ID rồi kiểm tiếp. Câu trích ngoài cửa sổ không được nhận cạnh cứng. Test mới cũng chốt đích `mentioned_only` bị bác; test 09c chốt dòng đầu mở bằng chữ số đã nằm trong vé 09d.
- Unit test toàn bộ: xanh; nhóm A8 28/28 xanh. Dry-run A8 chính: 458 session, dự toán 1,102561 USD trước retry/repair. Chạy thật: 602 completion có usage, 3 bản ghi dự phòng không tất toán; usage 1,984191 USD, tổng ledger bảo thủ 2,035112 USD. Artifact pass chính sáu tài liệu đều v1 trong kho đánh giá.
- Pilot dry-run: 199 cặp còn cần phán, doc-1 138 và doc-2 61; ít hơn 216 cặp ban đầu vì cạnh pass chính mới đã cắt 17 cặp. Chạy thật 409 completion, usage/ledger 0,446412 USD. Artifact pilot hai tài liệu là v2; không chạy A8 phụ các tài liệu còn lại.

| Tài liệu | Cạnh pass chính | Cứng | Mềm |
|---|---:|---:|---:|
| doc-1 | 236 | 224 | 12 |
| doc-2 | 618 | 546 | 72 |
| doc-3 | 14 | 9 | 5 |
| doc-6 | 5 | 5 | 0 |
| naive-bayes | 7 | 7 | 0 |
| nhap-mon-ml | 49 | 43 | 6 |

Pilot tạo 28 cạnh thứ cấp ở doc-1 và 4 ở doc-2; lần lượt 41 và 19 cặp bị `defer`, còn lại không tạo cạnh trực tiếp/đã có đường gián tiếp. Log chính vẫn còn lỗi bác nổi bật: doc-1 `quote_outside_evidence_chunk` 27, `definition_chunk_not_cited` 12, `quote_outside_definition_window` 6; doc-2 tương ứng 71, 215, 24. Số log có thể gồm lần thử và repair, không đồng nghĩa số cạnh cuối bị mất. `definition_chunk_not_cited` còn xảy ra khi câu trích **không ở cửa sổ**, nên luật tự gắn không áp dụng; cần đọc log trước khi đổi thêm hợp đồng.

## Chấm hai chương vàng

Ký hiệu `P a/b` = `a` cạnh đúng trong `b` cạnh dự đoán; `R a/b` = `a` cạnh đúng trong `b` cạnh vàng. “Bao đóng” tính quan hệ đạt được theo đường đi. Hàng chính + pilot áp luật A9 hiện hành rồi rút gọn bắc cầu.

| Tài liệu | Đồ thị | Trực tiếp | Bao đóng |
|---|---|---|---|
| doc-1 | Luồng cũ cuối, rút gọn | P 18/29 · R 18/28 | P 106/129 · R 106/131 |
| doc-1 | Pass chính mới | P 14/18 · R 14/28 | P 47/47 · R 47/131 |
| doc-1 | Chính + pilot mới, A9, rút gọn | P 15/25 · R 15/28 | P 108/127 · R 108/131 |
| doc-2 | Luồng cũ cuối, rút gọn | P 11/17 · R 11/32 | P 22/23 · R 22/68 |
| doc-2 | Pass chính mới | P 9/13 · R 9/32 | P 14/22 · R 14/68 |
| doc-2 | Chính + pilot mới, A9, rút gọn | P 11/14 · R 11/32 | P 19/23 · R 19/68 |

Đọc kết quả: doc-1 tăng 2 quan hệ bao đóng đúng nhưng giảm 3 cạnh trực tiếp đúng, đồng thời có 19 quan hệ bao đóng ngoài vàng; doc-2 giữ 11 cạnh trực tiếp đúng nhưng mất 3 quan hệ bao đóng đúng so với luồng cũ. Vì vậy pilot **chưa chứng minh cải thiện tổng thể**. “Ngoài vàng” là chưa có nhãn trong bộ chấm, không tự động khẳng định sai; tuy nhiên vài cạnh dưới đây đáng đọc lại về mặt sư phạm.

## Cạnh cứng mới trong phạm vi vàng, sau A9 và rút gọn

So với đồ thị cuối luồng cũ, doc-1 có 9 cạnh mới:

| Cạnh | Nhãn vàng trực tiếp |
|---|---|
| Số chiều → Cơ sở chính tắc | Chưa có |
| Véc tơ → Phụ thuộc tuyến tính | Chưa có |
| Véc tơ → Phần tử đối | Chưa có |
| Véc tơ → Không gian véc tơ thực | Chưa có |
| Ma trận → Ma trận tọa độ | Chưa có |
| Phần tử trung hòa → Không gian véc tơ | Chưa có |
| Không gian véc tơ hữu hạn sinh → Không gian véc tơ vô hạn chiều | Chưa có |
| Cơ sở → Không gian véc tơ vô hạn chiều | Có |
| Độc lập tuyến tính → Tọa độ | Chưa có |

Doc-2 có 5 cạnh mới:

| Cạnh | Nhãn vàng trực tiếp |
|---|---|
| Row vector → Row rank | Có |
| Column rank → Column-row factorization | Có |
| Column vector → Row-column rule | Có |
| Row rank → Column rank | Chưa có |
| Scalar multiplication on matrices → dim F^m,n = mn | Có |

Các ID node chính xác và lệnh tái lập nằm trong output của `so_sanh_a8_cua_so_v3.py`. Nên đọc trước hai cạnh “Số chiều → Cơ sở chính tắc”, “Không gian véc tơ hữu hạn sinh → Không gian véc tơ vô hạn chiều” và chiều “Row rank → Column rank”; hiện chưa kết luận đúng/sai chỉ từ nhãn vàng.

**Điểm dừng:** đợi chủ dự án đọc bảng và cạnh. Không chạy pass phụ đầy đủ (~31 USD), A9/A10 production, hoặc thay chuẩn chấm trong lượt này.
