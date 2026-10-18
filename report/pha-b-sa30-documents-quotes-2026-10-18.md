# SA-30 — Tài liệu sau hậu kiểm và câu trích — 2026-10-18

Phạm vi của nhánh này: `documents.py`, `postcheck.py`, `_bounded_quote` trong `learning_graph.py`, và replay sáu tài liệu nhóm 2. Không gọi provider, không đọc cache live hay tập giữ lại. Chi phí replay: **$0.00**.

## Sửa

- Hậu kiểm bỏ dòng chỉ có dấu câu. Tiêu đề cấu trúc chỉ còn nếu phía dưới nó có nội dung đã qua hậu kiểm; tiêu đề H1 do renderer dựng cũng không xuất hiện nếu thân tài liệu rỗng. Replay bỏ đúng một tiêu đề trống `### Ghi chú thêm` ở nhap-mon-ml. Bộ kiểm câu tăng lên `sentence-postcheck-2`.
- Khi mô hình dùng nhãn nguồn có thật nhưng gửi quote không nguyên văn, tài liệu chọn câu nguồn có nhiều từ chung nhất với các câu trong Markdown gắn nhãn đó. Chỉ tìm trong văn bản gốc của nhãn đã có trong context/source registry; nhãn lạ vẫn bị loại. Citation lưu quote trích nguyên văn và vị trí ký tự từ registry.
- `_bounded_quote` dùng `BSettings.quote_max_chars` (mặc định 200), giữ trọn câu khi có ranh giới câu trong giới hạn, nếu không thì dừng ở ranh giới từ. `LearningGraph.why_here` nhận `settings` tùy chọn để dùng cùng giới hạn; mặc định vẫn là `BSettings()`.
- `documents` đưa `ttft_ms` từ kết quả `call_json` vào usage. Bản replay cũ không chứa TTFT nên giữ `null`, không suy đoán lại thời gian.

## Kiểm tra

Năm regression cốt lõi đã đỏ trước sửa: heading rỗng/dòng dấu câu còn lại, quote lỗi làm tài liệu không có câu trích, quote cạnh 180 ký tự bị giới hạn 120, và quote dài không chọn ranh giới câu. Một phép thử in-memory thay `_bounded_quote` về giới hạn 120 cũ cũng đỏ trên test quote 180 ký tự. Sau sửa, **54 test** trong bộ tài liệu, hậu kiểm và learning graph đều xanh; các test mới kiểm tra cả trích dẫn đúng offset tuyệt đối lẫn việc nhãn không tồn tại không được sửa thành nguồn.

Lệnh kiểm tra:

```powershell
.\.venv\Scripts\python.exe -B -X utf8 -m pytest -q -p no:cacheprovider --basetemp=tmp/pytest-sa30-green4 tests/unit/application/test_phase_b_sa30_documents.py tests/unit/application/test_phase_b_sa25.py tests/unit/application/test_phase_b_lectures_documents.py tests/unit/domain/test_learning_graph.py
```

## Replay sáu tài liệu

Runner `scripts/phase-b/sa30_documents_replay.py` ghép fixture nhóm 2, kiểm hash/prompt/schema qua `ReplayToolModel`, nạp các phiên bản đồ thị đã ghi và ghi sáu tài liệu mới vào `tmp/phaseb-sa30-documents/`. Kết quả máy đọc là `tmp/phaseb-sa30-documents-replay.json`. Không có lời gọi mạng.

| Tài liệu | Trạng thái cũ → mới | Quote được mã sửa | Câu không nguồn bị bỏ | Tiêu đề rỗng bỏ |
|---|---|---:|---:|---:|
| doc-1 | failed → ready | 2 | 0 | 0 |
| nhap-mon-ml | ready → ready | 4 | 2 | 1 (`### Ghi chú thêm`) |
| naive-bayes | failed → ready | 3 | 0 | 0 |
| doc-6 | ready → ready | 3 | 1 | 0 |
| xstk-ch3-1 | ready → ready | 1 | 0 | 0 |
| doc-4 | ready → ready | 4 | 0 | 0 |
| **Tổng** | **2 failed / 4 ready → 6 ready** | **17** | **3** | **1** |

Sáu dòng usage đều là replay và tổng chi phí bằng **$0.00**. TTFT của các fixture lịch sử là `null`. Kiểm tra lại vị trí từng citation trong sáu kết quả cho thấy **0 lỗi offset**; không còn dòng chỉ dấu câu. Ba câu không nguồn còn nhận diện được ở nhap-mon-ml và doc-6 đã bị loại khỏi tài liệu, các câu có nguồn còn lại đủ để kết quả ở trạng thái `ready`.

## Sáu tài liệu để Claude đọc

- [doc-1](../tmp/phaseb-sa30-documents/doc-1-document.md)
- [nhap-mon-ml](../tmp/phaseb-sa30-documents/nhap-mon-ml-document.md)
- [naive-bayes](../tmp/phaseb-sa30-documents/naive-bayes-document.md)
- [doc-6](../tmp/phaseb-sa30-documents/doc-6-document.md)
- [xstk-ch3-1](../tmp/phaseb-sa30-documents/xstk-ch3-1-document.md)
- [doc-4](../tmp/phaseb-sa30-documents/doc-4-document.md)

Replay là kiểm tính tái lập và chất lượng trích dẫn theo fixture, không thay thế việc Claude đọc nội dung sáu tài liệu. Các mẫu và fixture vẫn là dữ liệu cục bộ, không commit.
