# Bàn giao triển khai SA-25–28 — 2026-10-18

Điều kiện trước đã hoàn tất: commit `bbcfcc6` lưu 40 tệp Pha B còn dở; bộ kiểm trước sửa có 150 test xanh. Codex điều phối cùng ba subagent GPT-6 Luna theo yêu cầu chủ dự án. Báo cáo này ghi kết quả triển khai; Claude vẫn cần soát độc lập và đọc nội dung theo từng vé.

## Kết quả đã kiểm

| Vé | Thay đổi | Bằng chứng |
|---|---|---|
| [25](pha-b-sa25-2026-10-18.md) | Hậu kiểm theo câu dùng chung, nhãn ghép, định nghĩa ngoài tài liệu, H1, bảng giá chung | 12 phản hồi phát lại 0 USD; bỏ 35 câu thiếu nguồn, 33 nhãn và 4 khối ngoài; M2/M5/M6 bị test bắt |
| [26](pha-b-sa26-2026-10-18.md) | Chống lặp giữa các ý và hai lượt sinh, chẩn đoán từng lần, usage cộng đủ, used_later hướng ra | 12 bài phát lại: 7 → 9 ready, 5 → 3 fallback; 18 dòng usage và 18 dòng validation; 0 USD |
| [27](pha-b-sa27-2026-10-18.md) | Đo lý do loại từng ứng viên, giữ các luật nguồn và kiểm mù, sửa có điều kiện luật tên trong đề | Đã đo V1–V4; M10 chọn sai bị loại; lượt Vertex 2 module có 35 lời gọi, 0,0782415 USD; 11/15 khái niệm có câu hỏi, gồm 8 câu LLM và 3 điền khuyết được trả |
| [28](pha-b-sa28-2026-10-18.md) | Mô tả 1–2 câu theo A5, tên chung, trùng toàn sách, chữ hoa, mô tả phụ thuộc dễ đọc | Đã chạy 160 module, 0,12723425 USD; chỉ 25 đầu ra LLM được giữ, 135 dùng khuôn dự phòng. Mô tả LLM list-only 130/152 → 0/25; nội dung toàn bộ chưa đạt vì tỷ lệ dự phòng tăng mạnh |

Ngưỡng câu nối là 60 ký tự. Ngưỡng Jaccard bài giảng là 0,6 trên tập 3 âm tiết đã chuẩn hóa. Cache bài giảng, câu trả lời trợ lý và quiz được phân phiên bản khi luật tương ứng đổi. Lệnh `phase-b lecture-diagnostics` đọc các dòng chẩn đoán mà không gọi mô hình.

Đợt ghép cuối kiểm **169 test xanh**, gồm kiến trúc, các use case Pha B, adapter, cạnh requires mở, HTTP của trang xem thử và runner chặn chi lặp/quá trần. Hai cảnh báo SWIG là deprecation của thư viện. Lệnh: `.tools/uv.exe run pytest` với 23 tệp `test_phase_b*.py`, `test_learning_graph.py`, `test_formula_images.py`, `test_architecture.py` và `test_sa28_runner.py`, basetemp `tmp/pytest-sa2528-final-tracked-runners-20261018`, tắt pytest cache. Bộ kiểm HTTP phải chạy ngoài sandbox vì sandbox chặn socket localhost bằng WinError 10013.

Runner phát lại/đo và các phép sửa sai được lưu ở `scripts/phase-b/`; dữ liệu bài ghi và kết quả ở `tmp/`/`artifacts/` vẫn là dữ liệu cục bộ không commit. Runner quiz từ chối trước khi tạo runtime nếu kết quả paid đã tồn tại; runner tên chặn từng lần gửi trước network và từ chối ghi đè lượt đã có. Test đã bắt việc bỏ guard quiz và bỏ nối gate vào transport tên bằng các biến thể trong bộ nhớ; không gọi thêm provider để kiểm những guard này.

## Phạm vi và tiền

Chỉ dùng sáu tài liệu phát triển: doc-1, nhap-mon-ml, naive-bayes, doc-6, xstk-ch3-1, doc-4. Không mở tập giữ lại T-01 hay tập khóa D-02; không đọc các giá trị cache trong `artifacts/phase_b/live.json`.

Chủ dự án đã duyệt hai lượt mới, mỗi lượt tối đa 0,50 USD, tổng tối đa 1 USD. Model cấu hình là `gemini-3.1-flash-lite` qua Vertex AI vùng global. Bảng giá và nguồn kiểm ở báo cáo SA-25. Các lượt phát lại SA-25, SA-26 và V1–V4 SA-27 có chi phí phát sinh 0 USD.

| Lượt | Số dòng gọi mô hình | USD ledger |
|---|---:|---:|
| Quiz hai module | 35 | 0,07824150 |
| Đặt tên sáu cuốn | 160 | 0,12723425 |
| **Tổng mới** | **195** | **0,20547575 / trần 1,00** |

Hai lượt đều dưới trần riêng 0,50 USD. Gate ở transport đặt tên giữ khoản dự phòng bảo thủ cho mọi lần gửi, tổng 0,38842550 USD; đó không phải chi phí đã tính theo token. Lần quiz bị sandbox chặn trước đó được tách riêng, không coi là nghiệm thu Vertex thành công. Lỗi in JSON cuối runner quiz do encoding Windows xảy ra sau khi kết quả đã lưu đầy đủ và không dẫn tới lặp API.

## Đồ thị tên mới và giới hạn nội dung

| Cuốn | A10 nguồn → bản mới | Module | LLM giữ / dự phòng |
|---|---|---:|---:|
| doc-1 | v52 → v54 | 33 | 6 / 27 |
| nhap-mon-ml | v37 → v47 | 15 | 8 / 7 |
| naive-bayes | v37 → v46 | 5 | 0 / 5 |
| doc-6 | v24 → v26 | 2 | 1 / 1 |
| xstk-ch3-1 | v63 → v65 | 14 | 3 / 11 |
| doc-4 | v22 → v24 | 91 | 7 / 84 |
| **Tổng** | | **160** | **25 / 135** |

Cả sáu bản mới giữ nguyên các trường ngoài tên/mô tả và metadata đặt tên: nodes, dãy học, cạnh, thành viên module đều được so bằng payload chính xác. Không có `module_` hoặc `node_` trong mô tả. Lượt tên chạy 8,07 phút, không có dòng usage thất bại.

**Chưa đạt mục tiêu nội dung toàn bộ:** đường dự phòng tăng từ 8/160 lên 135/160 (84,4%). Có 122 cờ `vocabulary`, 10 `generic_title`, 3 `title_form`. Tỷ lệ 0/25 list-only chỉ nói về 25 mô tả LLM vượt kiểm; 135 mô tả khuôn vẫn liệt kê khái niệm. Không được trình bày con số 0 ấy như mọi module đã có mô tả thành câu. Theo yêu cầu vé 28, giữ luật từ vựng và đưa mẫu cho Claude quyết định; không tự nới hoặc gọi thêm một lượt.

## Việc còn lại theo kế hoạch

- Claude đọc lại sáu tài liệu sau hậu kiểm, toàn bộ tên/mô tả mới và mọi câu quiz LLM được chấp nhận, rồi ghi phán xét vào vé.
- Claude quyết định hướng sửa xung đột giữa mô tả thành câu và luật từ vựng ở SA-28; xem mẫu trong báo cáo riêng. Việc triển khai và lượt đo hoàn tất, nhưng chất lượng tên/mô tả toàn bộ chưa được nghiệm thu.
- Ba bài giảng phát lại vẫn hỏng. Theo chỉ đạo của chủ dự án, chưa đầu tư thêm vào bản lùi, chưa đổi prompt hoặc chính sách cuối khi bài hỏng.
- Lượt thật gộp của vé 08, 10, 13 chưa thuộc hai khoản duyệt hiện tại; dry-run và duyệt riêng theo kế hoạch. Đánh giá 20–23 thực hiện sau các vé sửa, không được coi kết quả replay là đánh giá chất lượng cuối.
- Không tự nhận phán xét nghiệm thu của Claude. Các thay đổi Pha A và tệp ngoài phạm vi trong workspace được giữ nguyên.
