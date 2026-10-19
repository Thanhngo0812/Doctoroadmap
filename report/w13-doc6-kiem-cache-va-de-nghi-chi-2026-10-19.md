# W-13 — rà cache doc-6 và đề nghị hoàn tất, 2026-10-19

**Đã xử lý sau đề nghị:** chủ dự án duyệt “bao nhiêu cũng duyệt hoàn thành đi”. Đã dựng hết doc-6, gồm lượt từ kho rỗng và lượt cache 0 USD; PDF gốc nhap-mon-ml cũng đã được khôi phục và đo. [Báo cáo hoàn tất](w13-hoan-tat-doc6-2026-10-19.md) thay trạng thái đang chờ bên dưới; phần còn lại lưu lịch sử đề nghị trước khi được duyệt.

## Kết luận

Phần mã W-13 ở commit `e9ffce1` chưa đóng bằng chứng dựng hết doc-6. Phiên lõi đã dừng quá sớm ở việc báo cache miss; lượt bổ sung này kiểm cả kho cache lịch sử và chuẩn bị đề nghị chi riêng. **Chi mới: 0 USD; chưa có phê duyệt chạy có tiền.** Không bỏ `label-roles`, không đổi bộ đọc, không hạ cổng chữ và không sửa metadata cache để ép tái dùng.

## Kiểm lại với đầy đủ cache hiện có

Chạy từ gốc repo:

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/w13_doc6_cache_audit.py
```

Script chép riêng doc-6 từ parse/chunks/candidates/retrieval/canonical/graph/checkpoint hiện có sang một thư mục tạm mới. API sinh, embedding và lấy header ADC đều bị chặn; không ghi vào kho gốc. Kết quả và SQLite nằm trong thư mục `scratch_root` do script in ra.

Lượt đã chạy trên mã `de7946e` (mã W-13 không đổi so với `e9ffce1`), bằng chứng `tmp/w13-cache-audit-l5xwgnh1/audit.json`:

| Mục | Kết quả |
|---|---|
| Đọc PDF gốc bằng Nhe | 25 trang, 26 chunk, 78 section; qua các cổng sớm |
| Bản mới trong kho tạm | parse v3, chunk v5; băm chunk `bf363bcf0c60f814fc706670a01736b7f474173f55d78f0f45de9d0144171b0e` |
| Nhãn nghĩa | Không tìm thấy cache tương thích; dry-run còn 78 heading / 2 batch |
| Chuỗi thật không có quyền chi | Dừng `SpendNotAllowed` ở `concepts`; chỉ hoàn tất `doc_reading` |
| API / xác thực bị gọi | 0 |
| SQLite | `failed`, `model_calls=0`, `spent_usd=0` |
| A3 phía sau | 21 phần trích ứng viên, 27 ảnh ngữ cảnh; chưa chạy mô hình |

Cache nhãn lịch sử v4 dựa trên chunk v2; bản ứng viên cũ cũng có `chunks_config_hash=aaff7413d187732504e4fb52af01ad459e3050ba7a4615ea065d9bcdda4c8a83`. Chúng không thay cho cache của đầu vào mới. Chỉ cùng PDF hoặc cùng `source_hash` không đủ điều kiện tái dùng. Chưa thể tính cache hit cho A4/roadmap/Pha B trước khi có đầu ra mới ở các bước trước.

## Con số đề nghị duyệt riêng

**Đề nghị ngân sách 0,25 USD cho một lượt hoàn tất doc-6 bằng chuỗi sản phẩm hiện hành**, kể cả phần retry cần thiết. Đây là đề nghị nội bộ, không phải chức năng dự toán trên app hay số chi đã phát sinh.

| Khoản tham chiếu | USD | Căn cứ và giới hạn |
|---|---:|---|
| `label-roles` mới | 0,002936 | Dry-run trực tiếp: 2 batch, giả định 512 output token/lời gọi; chưa gồm nhãn sai cần hỏi lại |
| A3 cũ | 0,0565685 | `artifacts/candidates/doc-6/v1/manifest.json`: 27 phần, 81 lời gọi, 141.734 token vào / 14.090 ra; không phải giá chính xác của 21 phần mới |
| A4 cũ có làm mới | 0,0258755 | `artifacts/canonical/doc-6/v2/manifest.json`; v3 tái dùng 0 USD không đại diện một lần dựng mới |
| Roadmap và tên module cũ | khoảng 0,007 | Báo cáo chạy lại doc-6 ngày 2026-10-18; không gồm A3 |
| Tổng các số tham chiếu | khoảng 0,0924 | Chưa đủ embedding/A12/chỉ mục khái niệm và retry; cấu trúc mới làm số gọi thay đổi |

Mức 0,25 USD có phần dự phòng so với số liệu tham chiếu; không phải cam kết toàn chuỗi chắc chắn kết thúc với đúng số tiền đó. Giá tham chiếu dùng bảng ghim của repo (`domain/phase_b_pricing.py`), không suy ra từ hoá đơn mới. Trước lượt có tiền cần áp mức đã duyệt vào cơ chế chặn chi của lượt nghiệm thu, giữ riêng lượng đang chạy song song và phần usage chưa trả về; không chỉ kiểm tổng sau khi gọi xong.

## Lượt sẽ thực hiện khi được duyệt

1. Dùng kho doc-6 tạm riêng đã chép cache hợp lệ, Vertex và cùng cấu hình Nhe/default của W-13; ghim commit chạy. Chặn trước chi theo ngân sách được duyệt.
2. Chạy đúng `read → label-roles → A3/A3′ → A4/A5 coverage=none → roadmap → A12/concept-index/formulas`; không truyền `allow_text_quality_reason`, không đọc vàng.
3. Ghi số thực của mọi kết thúc vào SQLite; đối chiếu token/chi của lần này, graph hoàn tất và artifact chuẩn bị học. Không cộng số chi lịch sử.
4. Chạy tiếp một lượt không có quyền chi để kiểm tái dùng cache; xác nhận 0 lời gọi mới nếu các bước đã cache đầy đủ. Báo cả cache miss còn lại nếu có, không nhận đạt thay.
5. Cập nhật báo cáo và bàn giao commit bổ sung cho người soát. Nếu ngân sách không đủ, giữ checkpoint và xin duyệt phần tiếp theo trước khi chi thêm.

Giới hạn riêng vẫn còn: thiếu PDF gốc `nhap-mon-ml` để thay số đo parse cache một trang bằng số đo toàn cuốn; không tìm hoặc đọc tập giữ lại để thay nguồn.
