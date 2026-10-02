# 20 — Tệp lộ trình giữ node hình/bảng để cạnh mở không bị treo

**Nguồn chân lý:** spec-addendum (cờ `learnable`; "loại cạnh khác thì mở … phục vụ agent pha B") · **Ai:** nhân viên ·
**Phụ thuộc:** — · **Chi phí mô hình:** 0 (A10 không gọi mô hình; bước tên module tái dùng, có thể hỏi lại < 0,01 USD)

**Trạng thái:** đã triển khai và chạy lại A10 sáu tài liệu (2026-10-03); số đo ở [báo cáo](../../report/v3-20-21-t10a-2026-10-03.md).

## Vì sao (Claude, 2026-10-02)
- Quan hệ mở của A3/A4 **được giữ trọn** tới tệp lộ trình cuối: `open_edges` có 245 cạnh ở doc-1 (`subtype_of`, `component_of`, `uses`,
  `computed_by`, `example_of`, `contrasts_with`, `illustrates`, `tabulates`…), 67 ở nhap-mon-ml. Chúng không vào dãy học, đúng thiết kế.
- Nhưng A10 (`BuildRoadmap`) chỉ đưa vào tệp các khái niệm học được. Node `learnable: false` (hình, bảng) có ở canonical và A9 nhưng **bị
  bỏ** khỏi tệp lộ trình.
- Hệ quả: các cạnh `illustrates` / `tabulates` trỏ tới node không có trong tệp. Đo trên lượt cuối `v3-r12-final-evaluation` v6:

  | tài liệu | cạnh mở bị treo |
  |---|---|
  | doc-1 | 22/245 |
  | nhap-mon-ml | 11/67 |
  | doc-3 | **105/129** |
  | naive-bayes | 21/57 |
  | doc-6 | 19/21 |

  Lý do của **mọi** cạnh treo là node media.
- Dữ liệu không mất, vì vẫn còn ở artifact A9. Nhưng ai chỉ đọc tệp lộ trình (giao diện web, bước tạo bài giảng sau này) thì mất mối nối
  hình/bảng → khái niệm, đúng loại thông tin cần cho bài giảng.

## Việc cần làm
- A10 mang thêm danh sách `non_learnable_nodes`: mọi node `learnable: false` của đầu vào — media (hình, bảng) và thực thể bối cảnh (ví dụ node `license` "Creative Commons…" của doc-2), giữ nguyên trường (`media_id`, `caption_source`,
  `source_chunk_ids`, `orphan_reason`…).
  - Không lọc ở đây. Hình rác (`orphan_reason: no_concept_in_chunk`, như ảnh trang trí slide) giữ nguyên cờ; tầng trình bày tự lọc.
- Không đổi `sequence`, `nodes`, `requires_edges`, `modules`.
- Bump `algorithm_id` của A10 để cache đúng. Bước tên module tái dùng tên cũ như vé 09d.

## Nghiệm thu
- Test bất biến:
  - **mọi đầu của mọi cạnh trong `open_edges` có mặt** trong một danh sách node của tệp lộ trình (`nodes`, `mentioned_nodes`,
    `merged_nodes`, `excluded_nodes`, `non_learnable_nodes`);
  - `sequence` và `requires_edges` không đổi so với trước sửa.
  - Test phải đỏ trên mã hiện tại.
- Chạy lại A10 và tên module cho sáu tài liệu trên kho đánh giá cuối (sau khi doc-2 xong pass phụ). Báo số cạnh treo trước/sau (phải về 0)
  và xác nhận dãy học, cạnh không đổi.
- **Tôi kiểm:** chạy test bất biến, đếm lại cạnh treo trên sáu tài liệu.
