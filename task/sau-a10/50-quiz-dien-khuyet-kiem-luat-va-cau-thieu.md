# SA-50 — Quiz điền khuyết: giữ luật Q3/Q6 và bỏ câu thiếu phần quyết định

**Nguồn chân lý:** [spec Pha B](../../doc/pha-b-spec.md), mục 9, Q3/Q6/Q7; [SA-15](15-quiz-dien-khuyet-dau-cuoi.md), [SA-37](37-quiz-ca-lo-trinh-tai-lieu-nhieu-module.md); phát hiện SA-45.

**Ai:** nhân viên · nhân viên cấp cao kiểm · **Chi phí mô hình:** 0 USD · **Chặn bởi:** 46 (cùng `quiz.py`, tránh sửa chồng) · **Trạng thái:** ready-for-agent

## Vì sao

Đọc đầu ra thật phát hiện đường điền khuyết gắn cờ qua luật nhưng không kiểm đủ:

- Quiz doc-4 v27 seed 37: câu `qi_6fe378d5cc60b1daf14a5c2c` có cả "Chủ nghĩa duy vật" và "Chủ nghĩa duy vật chất phác"; câu `qi_dab727470c6d63e139326c1a` có "Phương pháp luận", "Phương pháp luận chung", "Phương pháp luận chung nhất". Các phương án chứa nhau, trái Q3. Bằng chứng `tmp/sa45-doc4-quiz.json`, tái lập bằng mô hình `None`, 0 USD.
- Ví dụ hợp đồng quiz doc-1 v57 có câu Tích trực tiếp chỉ còn "___ (hay ___) của hai tập hợp X và Y là tập hợp sau đây:"; câu Nhóm dừng ở "thỏa mãn ba điều kiện sau đây:". Phần xác định đáp án bị bỏ khỏi câu hỏi. Không được tự dựng phần công thức/điều kiện thiếu.
- `_cloze_bank` không chạy bộ lọc Q6: ca tổng hợp có câu neo "Tam giác được xác định bởi biểu thức [formula] sau đây." vẫn tạo câu hỏi chứa `[formula]`, không kèm ảnh.

Ba assertion cuối trong `tests/unit/application/test_phase_b_sa45_artifact_audit.py` tái hiện các nhóm lỗi. Test được giữ `xfail(strict=True)` chờ vé này; dùng `--runxfail` để thấy đỏ.

## Cần làm

- Dùng cùng bất biến Q3 về tên/alias/phương án chứa nhau cho câu điền khuyết; nếu không đủ hai nhiễu hợp lệ thì bỏ câu.
- Không dùng câu cần hình/bảng/công thức chưa hiển thị; loại dấu `[formula]` theo Q6.
- Bỏ câu dẫn định nghĩa tham chiếu phần "sau đây" còn thiếu, hoặc lấy đủ chứng cứ nguồn nếu biểu diễn hiện hành hỗ trợ mà không chép lại công thức. Không thay bằng nội dung suy đoán.
- Không chặn cả bộ khi bỏ câu; ghi lý do và số phủ còn lại. Đổi phiên bản khoá ngân hàng để câu lỗi cũ không trở lại từ cache.

## Tiêu chí nghiệm thu

- [ ] Ba test `test_cloze_rejects_sentence_that_requires_a_missing_formula`, `test_cloze_rejects_definition_lead_in_without_its_missing_conditions`, `test_cloze_options_do_not_contain_each_other` đỏ trước sửa và xanh sau sửa; bỏ nhãn xfail tương ứng.
- [ ] Thêm ca đối chứng có câu định nghĩa đầy đủ vẫn tạo quiz, không lộ đáp án; câu thiếu bị bỏ và không làm hỏng cả bộ.
- [ ] Phát lại 0 USD doc-4 v27 seed 37 và ví dụ doc-1; đọc từng câu, báo số câu/module còn hợp lệ. Không sửa PDF, neo hay mã Pha A để che lỗi đầu vào.
- [ ] Test quiz, cache, hợp đồng và kiến trúc xanh; cache trước luật mới không được dùng lại.

## Ngoài vé

Không cải tổ toàn bộ bộ sinh quiz, không thêm lời gọi mô hình kiểm câu điền khuyết, không chạy có tiền. Vấn đề ngữ nghĩa của nguồn OCR như `i = j` ở định nghĩa ma trận chéo báo phía Pha A, không tự sửa nguồn.
