# Đợt 19a–19i: triển khai và kiểm chứng

**Cập nhật tiếp theo:** 19j đã được Claude duyệt, 19k đã cài mặc định song song và cache vector query của 19g đã gỡ. Báo cáo này ghi lượt 19a–19i ban đầu; xem [báo cáo cập nhật 19k/19g](v4-19kg-song-song-va-go-cache-2026-10-17.md). Phép đo toàn stage mention chuyển sang cổng 19l.

Ngày 2026-10-17. Đọc spec, các vé và đường chạy trước khi chia việc: nhóm 19a–19c sửa A4; 19f rồi 19h sửa lõi neo và đồng thời; 19g/19i tối ưu CPU; phiên tích hợp làm 19d/19e, nối bộ đo và kiểm tra chéo. 19h chỉ bắt đầu sau khi 19f có băm ứng viên đúng và số đo doc-4.

## Phạm vi đã cài

| Vé | Kết quả |
|---|---|
| 19a | Louvain nhận id số nguyên đã sắp ở `gop`; hai hash seed cho cùng cụm và payload. |
| 19b | Tắt đề cử cùng bằng chứng; bỏ lời sửa cho cạnh cắt thuần ngram, giữ cạnh trong đồ thị, có log và số đếm. |
| 19c | Phục hồi nhóm chung tên chuẩn hoá, người duyệt vẫn ưu tiên, alias không buộc gộp; R2 bắt `coextensive_with`. Gỡ nhóm/cặp đã giải quyết khỏi backlog hoãn. |
| 19d | Neo mặc định `single`; `--names-only`/`--prepare` tự dùng v3 nếu chưa chỉ định chuỗi. Gop tường minh vẫn bị từ chối với hai chế độ thiếu này. |
| 19e | Đồ thị gop và v3 có `identity_map` không rỗng nạp được qua Pha B và dựng ngữ cảnh bài giảng, giữ neo/chunk/trích dẫn. Không sửa nguồn Pha B. |
| 19f | Dùng chung chuẩn hoá chunk và câu ứng viên; có số đo bốn phần CPU canonical và stage đặt tên module trong manifest. |
| 19g | NumPy cho dense, một lượt dò tên dùng chung, cache query đúng model/task/text; fallback thứ tự cộng cũ khi sai số có thể đổi thứ hạng/ngưỡng. Còn giới hạn nghiệm thu toàn stage bên dưới. |
| 19h | Canonical mặc định 16 worker, bỏ rào lô 8 ở neo canonical; limiter còn hiệu lực, teaching giữ checkpoint. Bỏ cấu hình `vertex_concurrency` không dùng. |
| 19i | Cache theo tài liệu cho chuẩn hoá, tách từ và cửa sổ có hướng; giữ nguyên đặc trưng, mô hình và luật ngưỡng. |

Các luật A4 mới có mục config riêng, đảo từng luật được và tái dùng lại artifact khi đảo về. Các tối ưu tốc độ giữ cache key. Băm v3 đóng băng vẫn được kiểm. **Chuỗi mặc định vẫn là `v3`**, chưa làm cổng đổi mặc định của 19m. Không chạy nghiên cứu trả phí hoặc mở rộng sang 19j–19o.

## Số đo trên doc-4

| Phần đo | Trước | Sau | Tăng tốc | Bảo toàn đầu ra |
|---|---:|---:|---:|---|
| Chuẩn bị neo, 630 node / 671 chunk | 257,526 s | 38,667 s | 6,66× | Băm ứng viên và vùng ngoài nội dung y hệt. |
| CPU mention, cùng vector lưu sẵn | 158,205 s | 14,652 s | 10,80× | Map bỏ riêng z và mọi thứ hạng y hệt; chênh z tối đa 2,69e-14. |
| Toàn stage pass phụ ML | 374,653 s | 197,569 s | 1,90× | Cùng băm 4.650 chiều × 82 đặc trưng, điểm, xác suất, ngưỡng, 877 cạnh và toàn payload. |

Chi phí dịch vụ mô hình/embedding của đợt này: **0 USD**. Dùng mô hình giả, HTTP giả, phản hồi ghi sẵn hoặc mô hình ML chạy tại máy. Kho tài liệu gốc chỉ đọc; đầu ra thử nằm trong `tmp/` và kho pytest.

**Giới hạn 19g:** clusters dùng embedding `SEMANTIC_SIMILARITY`, mentions dùng `RETRIEVAL_QUERY`. Hai loại vector không thể thay nhau nếu phải giữ mention map. Kho cũ không lưu query doc-4, nên chưa thể nghiệm thu phép phát lại toàn stage trên query lịch sử bằng 0 USD. Số 10,80× chỉ là hai phần CPU với cùng vector có sẵn. Cache query mới giảm yêu cầu embedding ở lượt giả kế tiếp từ 2 xuống 0; không tuyên bố giảm lời ở lượt đầu bằng cách dùng nhầm vector clusters.

## Kiểm chứng

Các lỗi hồi quy đã được thấy đỏ trước khi nhận bản vá, gồm hash seed, same evidence, ngram, ràng buộc tên/người duyệt, R2, mặc định CLI, số worker, số lần chuẩn hoá, thiếu số đo và cặp hoãn đã gộp. Thử phá riêng luật ưu tiên người duyệt, alias, cache embedding, limiter và cache đặc trưng cũng làm assertion tương ứng trượt.

Lượt tập trung cuối cho A4, duyệt gộp và mention: **42 test qua**, gồm hai regression cặp hoãn mới. Lượt 19d/19e và phép đo module: **11 test qua**. Các lượt tập trung khác và băm đầy đủ được ghi trong báo cáo từng nhóm; các bộ có giao nhau nên không cộng số test.

Lượt toàn bộ đầu tiên: **1.616 qua, 1 lỗi kiến trúc** do NumPy trong domain. Đã chuyển phép nhân ma trận và kiểm sai số sang application, giữ phần xếp hạng Python trong domain; nhóm kiến trúc/mention sau sửa **18 test qua**. Băm toàn mention map doc-4 sau khi chuyển mã giống hệt bản tối ưu đã đo.

**Lượt toàn bộ cuối: 1.617 test qua, 0 lỗi, 458,03 giây; mã thoát 0.** Gồm tích hợp tài liệu thật, các stage cũ, Pha B, toàn bộ luật mới và kiểm kiến trúc. Báo cáo JUnit: `tmp/pytest-19-full-root-02.xml`. `git diff --check` cũng qua. Lệnh:

```powershell
$env:HF_HUB_OFFLINE='1'
$env:TRANSFORMERS_OFFLINE='1'
.venv\Scripts\python.exe -m pytest -p no:cacheprovider --basetemp=tmp/pytest-19-full-root-02 --junitxml=tmp/pytest-19-full-root-02.xml --tb=short
```

**18d phát lại:** 4.905 chiều có độ lệch điểm bằng 0. Doc-1/doc-4 đạt; xstk giữ đủ 59/59 cạnh chuẩn và thừa 1, đúng kết quả đã được vé 18d lượt 2 chấp nhận. Script vẫn trả mã 1 vì áp ngưỡng ±0,03 cho cả xstk; không tuyên bố script xanh hoặc thay luật chất lượng. Chi tiết số cạnh và E4 ở báo cáo 19g–19i.

Trạng thái chốt: 19a–19f, 19h đã đạt kiểm tra đã giao; 19i giữ đúng kết quả nghiệm thu 18d với ngoại lệ cũ nêu trên. 19g đã cài và test xanh, còn mở phép nghiệm thu thời gian toàn stage doc-4 do thiếu query lịch sử. Các vé đã cập nhật đúng trạng thái này.

## Bằng chứng chi tiết

- [19a–19c: luật A4, đỏ/xanh, đảo cache và băm v3](v4-19abc-sua-a4-2026-10-17.md).
- [19d–19e: neo mặc định, CLI, Pha B và đo module](v4-19de-mac-dinh-va-pha-b-2026-10-17.md).
- [19f–19h: băm ứng viên, thời gian, đồng thời, checkpoint và limiter](v4-19fh-neo-va-song-song-2026-10-17.md).
- [19g–19i: profile, giới hạn query cache, băm đặc trưng/điểm/cạnh](v4-19gi-tang-toc-mentions-va-pass-phu-ml-2026-10-17.md).
