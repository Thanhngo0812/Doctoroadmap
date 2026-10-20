# Soát độc lập đợt khôi phục — 2026-10-20

Người điều phối tích hợp; agent `review_recovery` soát độc lập, không gọi API, không sửa mã hay dữ liệu. Các phán xét nhận trực tiếp trong phiên điều phối:

- Approve đúng `a69ebe2dce89dcb5ed2d64f82154f0f4069ed9f8`, diff từ `2bee226`: hai test giữ đủ assertion năm câu, sự kiện, ẩn đáp án và công cụ trợ lý; fixture qua loader thật và ghim đúng parse/chunks. Chạy độc lập 10 kiểm đạt; XML `quiz-independent-review.xml`.
- Budget guard: 12 kiểm đạt; giữ chỗ đồng bộ nhiều luồng, thiếu usage chặn phát lệnh sau. Resume cộng tiền cũ vào cùng trần 3 USD, không đặt lại. Guard chỉ phục vụ JSON, không hỗ trợ SSE; chuỗi dựng hiện dùng JSON nên không ảnh hưởng phạm vi chạy.
- Đối chiếu artifact, chi phí, replay và snapshot: approve, giữ cờ `pipeline_usage_complete=false` và không biến kiểm hash thành kết luận chất lượng nội dung.
- Sau góp ý về ảnh, bổ sung kiểm độc lập: 2.602 occurrence, 0 skip, 2.234 PNG duy nhất, SHA và giải mã pixel đạt. Ba phép thử ảnh hỏng/mất ảnh/index lệch parse đã từng fail trên bộ kiểm chưa đủ và pass sau bổ sung. Chưa đánh giá thị giác từng crop.
- Cache Pha B: approve phép kiểm 35 thẻ và 35 ngữ cảnh tên hiện tại, thay node ID tạo 1 miss, CLI đúng kho riêng và 0 API. Chưa đối chiếu cache v45/v57; quiz cloze offline chỉ 1/5 câu ở module thử, không chứng minh mọi quiz thật đủ năm câu.

Các kiểm có thể chạy lại: `test_budget_guard.py.txt`, `test_formula_guard.py.txt`, `verify.py.txt`, `check_phase_b_cache.py.txt` là mã harness được lưu nguyên để xem xét. Kết quả tương ứng nằm trong XML và JSON cùng thư mục. Không đưa artifact/cache/PDF vào Git.

Mốc ghép `34d2257` đã đẩy main, `src/` và `tests/` giống đỉnh đã soát/chạy cổng. Cổng sau dựng cuối có native runner exit 0, 1.999 đạt, 0 fail/error, 1 skip Cloudinary live. React 41 đạt và build đạt. Toàn bộ số liệu này có log/XML riêng; phán xét agent về cache không được dùng thay cho cổng test đang chạy ở thời điểm họ soát.
