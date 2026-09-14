# Fixture A3 hiện hành

`a3-section-with-image.json` được ghi từ Gemini thật ngày 2026-09-11 bằng
`scripts/record_a3_fixture.py` với prompt mặc định, model và generation mặc định.
File `.context.json` đi kèm giữ section/chunk/formula/caption nguồn để replay qua use case;
ảnh được lấy từ request đã ghi. Không cần artifact trên máy người chạy test.

Ghi lại khi thay prompt, schema hoặc generation mặc định:

```powershell
.venv/Scripts/python.exe scripts/record_a3_fixture.py
.venv/Scripts/python.exe -m pytest tests/unit/infrastructure/test_a3_llm.py
```

Lệnh ghi cần mạng và API key, có chi phí; test replay không gọi mạng. Không chỉnh hash fixture
bằng tay để làm xanh test. Replay kiểm tương thích và xử lý phản hồi đã ghi, không đo khả năng
tái lập của mô hình. Fixture có ảnh không đồng nghĩa đã chứng minh ca khái niệm chỉ xuất hiện trong ảnh.
