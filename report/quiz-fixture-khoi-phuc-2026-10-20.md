# Thay phụ thuộc graph v45 bằng fixture quiz trong repo

Hai kiểm hồi quy quiz đọc `artifacts/graph/doc-1/v45` ngoài repo và lỗi khi cache bị mất. Theo tin nhắn chủ dự án “duyệt tất cả làm end to end khôi phục đi”, chuyển đúng hai kiểm sang fixture tổng hợp nhỏ được lưu trong `tests/fixtures/phase_b_quiz_graph`.

Fixture được tạo bằng các hàm ghi thật của JsonArtifactStore từ mô hình Graph hình học đã có trong test: ba khái niệm, alias dạng dict, mỗi khái niệm hai câu nguồn. Graph v1 ghim chunks v1 và parse v1. Không dùng nội dung sách hay câu trả lời LLM. Test vẫn đi qua `load_learning_graph` thật, vẫn yêu cầu đủ năm câu, năm sự kiện item_ready, kết thúc done, không lộ đáp án; công cụ trợ lý chỉ trả tham chiếu và số câu.

Kiểm trước sửa trong worktree không có kho artifacts: **2 fail, 28 pass**, cả hai fail vì thiếu graph v45. Sau sửa, cùng lệnh: **30 pass**. Lệnh:

```text
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe scripts/w05_run_tests.py tests/unit/application/test_phase_b_quiz.py src/web/backend/tests/test_settings.py -o addopts= -q --basetemp=tmp/quiz-green --junitxml=tmp/quiz-green.xml
```

Bằng chứng RED/GREEN lưu trong worktree `tmp/quiz-red.xml` và `tmp/quiz-green.xml`; người điều phối lưu bản nghiệm thu khi ghép. Không sửa mã sản phẩm, kỳ vọng kiểm, migration hoặc dữ liệu ngoài repo.
