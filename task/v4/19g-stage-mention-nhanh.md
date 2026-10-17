# 19g — Stage mention nhanh hơn

**Nguồn chân lý:** [spec đổi mặc định chuỗi gộp](../../doc/doi-mac-dinh-chuoi-gop-spec.md), pha 2 mục 3.
**Ai:** nhân viên · **Chi phí mô hình:** 0 USD (kiểm thử giả) · **Chặn bởi:** không · **Trạng thái:** hoàn thành theo đính chính, đã gỡ cache; đã đo toàn stage doc-4 ở cổng 19l

## Vì sao

Stage mention mất 400 giây trên doc-4 (nghiên cứu mục 4), vì ba chỗ:
- độ gần ngữ nghĩa tính bằng Python thuần;
- khớp tên chính xác chạy lặp;
- khoảng 630 tên bị embed lại, dù stage cụm đã embed.

## Cần làm

- Tính độ gần ngữ nghĩa bằng thư viện số học vector.
- Khớp tên chính xác một lần cho cả tài liệu.
- ~~Dùng lại vector tên đã có ở stage cụm, không embed lại~~ — bỏ theo đính chính spec 2026-10-17: hai stage dùng task embedding khác nhau.
- **Mention map phải giống hệt trước**, kể cả thứ tự và các trường số. Nếu có sai lệch số học nhỏ ở độ gần, ghi rõ và giữ thứ hạng không đổi.

## Nghiệm thu

- [x] Test trên fixture thật: mention map trước và sau cùng băm, hoặc chỉ lệch số học trong dung sai đã ghi mà thứ hạng y nguyên.
- Số lời gọi embedding giảm: bỏ yêu cầu theo đính chính spec; không lưu cache query trong manifest.
- [x] Đo thời gian toàn stage doc-4 ở cổng 19l: 744 giây trên Vertex. CPU khoảng 15 giây, phần còn lại là chờ embedding 630 câu truy vấn, mỗi câu một request, bị quota bóp (1.159 lời HTTP). Developer API gom lô thì còn 7 request. Xem [báo cáo cổng](../../report/v4-19l-cong-doi-mac-dinh-2026-10-17.md) mục 2.
- [x] Toàn bộ test qua sau khi gỡ cache query.

**Kiểm chứng ban đầu 2026-10-17:** CPU doc-4 trên cùng vector lưu sẵn: 158,205 → 14,652 giây (10,80 lần), thứ hạng giữ nguyên; chênh z tối đa 2,69e-14, dung sai tuyệt đối 1e-12. Không có vector `RETRIEVAL_QUERY` cũ để đo toàn stage 0 USD. Vector clusters dùng `SEMANTIC_SIMILARITY`, nên không dùng thay query. Cache query của lượt cài đầu đã gỡ theo kiểm bên dưới. Số đo CPU ở [báo cáo 19g–19i](../../report/v4-19gi-tang-toc-mentions-va-pass-phu-ml-2026-10-17.md).

Toàn kho sau gỡ cache: **1.621 test qua**, xem [báo cáo cập nhật](../../report/v4-19kg-song-song-va-go-cache-2026-10-17.md). Phép tính NumPy nằm ở application; domain giữ thư viện chuẩn.

## Kiểm của Claude 2026-10-17 — còn một việc

- **Gỡ cache vector query khỏi manifest.** Cache ghi khoảng 630 vector × 768 chiều vào `manifest.json`, có thụt lề: khoảng 14,6 MB mỗi
  manifest mentions của doc-4, mất 0,39 giây để parse. Mọi stage graph tra cache bằng cách đọc lần lượt mọi manifest, và cache cộng dồn
  qua các phiên bản, nên kho càng chạy lại càng chậm. Bộ tìm cache còn nạp cả payload của từng phiên bản graph cũ.

  Lợi ích chỉ có khi chạy lại mentions với cùng mô tả, mà sản phẩm gần như không làm thế. Embed lại 630 query tốn dưới 0,01 USD và vài
  giây. Mục "không embed lại tên" đã bỏ khỏi spec (pha 2 mục 3). Giữ NumPy, bước kiểm mơ hồ và lượt dò tên dùng chung.

  - [x] Không còn `query_embedding_cache` trong manifest. Mention map trên fixture thật vẫn cùng băm. Toàn bộ test qua.
- **Ô đo thời gian toàn stage doc-4** chuyển sang báo cáo cổng 19l. Cổng chạy embedding thật, chi phí vài xu.

**Đã sửa:** bỏ đọc lịch sử và ghi vector query; giữ cache artifact của stage. Băm toàn mention map fixture thật trước/sau gỡ cache giữ `00c96ea9b8c46e8585678c32a32ab57b7eb9eea390f25ec9646ac2f3c90ce68d`. Nhóm tập trung 36 test qua, tích hợp 43 test qua; toàn bộ 1.621 test qua. [Báo cáo cập nhật](../../report/v4-19kg-song-song-va-go-cache-2026-10-17.md).
