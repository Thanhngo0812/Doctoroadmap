# Bàn giao cho phiên Pha B: chuỗi gộp thành mặc định (2026-10-17)

**Từ:** phiên pha A (Claude, vé 19m). **Gửi:** phiên Pha B (sau A10).

Đọc kèm:
- [ADR 0016](../doc/adr/0016-danh-tinh-trong-a4-neo-trong-a5.md);
- [spec đổi mặc định](../doc/doi-mac-dinh-chuoi-gop-spec.md), mục "Pha 4";
- [báo cáo cổng 19l](v4-19l-cong-doi-mac-dinh-2026-10-17.md).

## 1. Đổi gì

Từ commit bật mặc định của vé 19m, lệnh `a4` và `roadmap` chạy **chuỗi gộp** khi không đặt cấu hình gì.
- **Danh tính gộp hẳn vào A4.** Đồ thị mới không có `identity_map` và `merged_nodes`. Tên của các nhóm bị gộp nằm sẵn trong `aliases` của node, kèm
  câu bằng chứng. Không có `identity_aliases`.
- **Câu neo và trạng thái dạy** do A5 quyết. Node vẫn giữ đúng các trường cũ:
  - `anchor`, `teaching_status`, `teaching_chunk_ids`, `teaching_order_index`;
  - `defining_chunk_ids`, `defining_chunk_ids_source`.

  Trên doc-1, tập khoá của node v45 nằm trọn trong v53. v53 có thêm `display_prerequisites` và `display_prerequisites_more_count`.
- **Id node đổi** khi khái niệm bị gộp thêm hoặc đổi ứng viên neo (ADR 0005). Id cũ được ghi trong `redirects` của canonical. Muốn quy một id cũ thì
  lặp theo `redirects` tới khi gặp id hiện hành.
- **Dãy học và module đổi theo.** Lý do: khái niệm bị gộp thêm, trạng thái dạy được quyết lại, và cạnh tiên quyết được suy lại.

Các đồ thị Pha B đã dùng ngày 2026-10-15, so với đồ thị chuỗi gộp của cổng 19l ở kho chính:

| Tài liệu | Đồ thị Pha B → chuỗi gộp | Khái niệm | Id mất / id mới | Module | Module giữ nguyên tập khái niệm |
|---|---|---|---|---|---|
| doc-1 | v45 → v53 | 218 → 205 | 16 / 3 | 39 → 33 | 1 |
| xstk-ch3-1 | v48 → v56 | 72 → 73 | 0 / 1 | 9 → 13 | 0 |
| doc-4 | v15 → v23 | 489 → 495 | 9 / 15 | 87 → 91 | 3 |

Đọc bảng:
- **Id mất** gồm hai loại: id bị gộp, quy được qua `redirects`, và khái niệm rời dãy học vì trạng thái dạy đổi.
- **Ở mức canonical**, mọi id v3 vắng mặt đều quy được qua `redirects`: doc-1 6 id, nhap-mon-ml 2, doc-6 1, xstk 3, doc-4 4.
- **nhap-mon-ml, naive-bayes và doc-6** đã có canonical chuỗi gộp nhưng **chưa có đồ thị chuỗi gộp**. Đồ thị mới nhất của chúng vẫn là bản v3 mà
  Pha B đang dùng. Chạy `roadmap` cho ba tài liệu này sẽ dựng chuỗi gộp và tốn tiền, nên phải có `--allow-spend`.

## 2. Hệ quả cho Pha B

- **Cache bài giảng và quiz cũ mất hiệu lực.** Khoá cache bài giảng băm cả `node_id` lẫn ngữ cảnh đã lắp, mà cả hai đều đổi. Chủ dự án đã chấp nhận
  việc này trong đợt soát 2026-10-17. Không cần chuyển cache.
- **Bộ nạp đồ thị:** vé 19e đã có test tích hợp. Test nạp đồ thị `stages` của chuỗi gộp qua bộ nạp Pha B; node có câu neo và chunk dạy đúng dạng mà
  bài giảng đọc.
- **Hai test quiz đã được ghim vào đồ thị v45** (nhân viên làm ở vé 19m, trong `tests/unit/application/test_phase_b_quiz.py`).
  - Hai test này đọc đồ thị doc-1 mới nhất, cố định `module_023` và đòi quiz 5 câu. Sau cổng 19l, đồ thị mới nhất là v53, và module đó chỉ ra 4 câu.
  - Nhân viên chỉ đổi hai lời nạp sang `graph_version=45` và thêm một dòng chú thích; không đổi logic quiz hay assertion. Patch nằm ở
    `tmp/19m/quiz-fixture.patch`.
  - Tệp này của phiên Pha B và chưa được track, nên commit 19m không mang nó theo. Phiên Pha B nên xem lại: test đọc kho thật sẽ còn gãy mỗi khi
    đồ thị mới nhất đổi.
- **Không dựa vào** `identity_map`, `merged_nodes` hay `identity_aliases` khi đọc artifact mới. Artifact v3 cũ vẫn đọc được: thiếu `identity_map`
  được hiểu là bản đồ rỗng. Hiện quiz chỉ đọc `identity_aliases` với giá trị mặc định rỗng, nên không phải sửa.
- **Luật Q3 của quiz** (phương án không được là tên, alias hay danh tính đã gộp của đáp án) vẫn đúng, vì tên đã gộp nay nằm trong `aliases`.
- **Tiến độ người học, nếu sau này lưu theo `node_id`,** phải quy id qua `redirects` của canonical mà đồ thị đang dùng. Id đã dùng không bao giờ được
  cấp lại cho khái niệm khác (ADR 0005).
- **Số đánh giá đã đo** (SA-20 đến SA-23) là số trên đồ thị v3. Lần đo sau nên ghi rõ đồ thị thuộc chuỗi nào, đọc từ `config.upstream_chain` trong
  manifest.

## 3. Sắp tới ở pha A

- **19n:** gỡ ba stage cũ (provenance, `teaching`, `identity`) và nhánh A4/A5 v3 có gọi mô hình. Hợp đồng đọc artifact v3 cũ vẫn giữ.
- **19o:** gỡ ba tuỳ chọn đã đo là thua: neo gom vào A5, đề cử theo mô tả, gom lô lời phán sửa.
- **Hàm dùng chung phải giữ:** `quote_is_verbatim`. Pha B (`phase_b/common.py`) đang import hàm này từ `domain.provenance`, là module của stage sắp
  gỡ. Vé 19n bắt giữ hàm này và chuyển nó sang module trung tính, nên dòng import của Pha B sẽ phải đổi theo. Nhân viên 19n sửa luôn dòng import để
  test xanh. Phiên Pha B chỉ cần biết, không phải làm gì.
