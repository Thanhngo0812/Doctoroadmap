# SA-62 — Port kho Pha B cho `DocumentPipeline` và `PhaseBRuntime` (W-15 dựng thật trên PostgreSQL)

**Nguồn:** W-15 đề nghị port (`report/w15-noi-bo-dung-that-2026-10-22.md`, mục "Đề nghị port"); câu hỏi của người điều phối ở mục 8 bàn giao, 2026-10-23.
Claude chốt người làm, phạm vi và nguồn tính chi ngày 2026-10-23.

**Ai:** agent Sonnet cài · Claude nghiệm thu và ghép · **Chi phí mô hình:** 0 USD · **Chặn bởi:** không. Chạy sau khi agent SA-21 xong, để cổng không chạy
chồng lúc SA-21 đo giây · **Ghép:** Codex thực hiện theo quyền tự ghép trong lời bàn giao · **Trạng thái:** đạt, đã ghép/đẩy `9ac2a85`.

**Hoàn tất 2026-10-23:** test web bổ sung commit `ce5f581` trên chính nhánh SA-62; hai ca âm factory thiếu port giữ nguyên,
ca dương default factory ghi/đọc kho PG qua kết nối độc lập, guards provider/ADC/JSON/SQLite còn bật.
Cổng trước SA-64: 2.305 Python/143 React/build xanh. Đã kiểm chứng sau ghép cùng SA-64 tại `14110c0`: **2.355 Python đạt/0 fail/1 Cloudinary live không bật,
143 React/build**, mọi native exit 0. Giữ nhật ký việc main đổi trước lúc ghép và cả hai lượt kiểm.
[Báo cáo và JUnit](../../report/sa62-tiep-nhan-test-web-2026-10-23.md). SA-62 gỡ chờ port của W-15; toàn W-15 còn bước pipeline thật/cache/dry-run, chưa quyền chi.

## Vì sao

Pipeline dựng sách hiện tự tạo kho Pha B dạng JSON (`artifacts/phase_b/live.json`) ở hai chỗ:
- `graph()` tạo `JsonPhaseBStore` cho khâu tên module (`NameModulesB`);
- `learning_prep()` tạo `PhaseBRuntime`, mà runtime này lại tự tạo `JsonPhaseBStore` cho A12 và chỉ mục khái niệm.

Web cần mọi thứ đó ghi vào **cùng PostgreSQL** của web. Adapter W-15 đã xong và đang từ chối pipeline thật cho tới khi lõi có port này.

## Phạm vi tệp

Chỉ sửa:
- `src/doc2roadmap/composition_build.py`: `DocumentPipeline.__init__`, `graph()` (chỗ tạo `NameModulesB`), `learning_prep()`;
- `src/doc2roadmap/composition_phase_b.py`: `PhaseBRuntime.__init__`;
- test lõi mới trong `tests/`.

**Không sửa:**
- use case Pha A (`application/use_cases/*`) và `BuildDocument`;
- use case Pha B (`naming.py`, `concept_index.py`, `common.py`, `budget.py`);
- `src/web/`: phần web do người điều phối làm sau khi port lên main.

## Cần làm

1. **`DocumentPipeline(settings, *, allow_spend, phase_b_store=None)`.**
   - Có kho được tiêm thì `NameModulesB`, `PhaseBRuntime` con và `IndexConcepts` dùng **đúng đối tượng đó**, và **không tạo `JsonPhaseBStore` nào**.
   - Không tiêm thì giữ nguyên hành vi CLI hiện tại: cùng đường dẫn `artifact_dir/phase_b/live.json`, cùng thời điểm tạo.
2. **`PhaseBRuntime(..., store=None)`.**
   - Có `store` thì dùng nó cho `self.store` và `DailySpendGuard` **trước** khi tạo bất kỳ thứ gì khác, không tạo JSON rồi gán lại.
   - Truyền cả `store` lẫn `store_path` thì `ValueError`. `mode` (`offline`/`gemini`) giữ như cũ.
3. **Một nguồn tính chi build:**
   - **Chi của một lượt dựng là delta của `DocumentPipeline.usage()`** (`BuildUsage`, qua `MeteredModel`/`MeteredEmbedding`, token thật nhà cung cấp
     trả). Receipt và ledger web `purpose=build` lấy từ đây, như adapter W-15 đang làm.
   - Các dòng usage mà use case Pha B tự ghi vào kho Pha B trong lúc dựng chỉ là **vết, không phải chi**. Gồm `module_title` của `NameModulesB` qua
     `call_json`, và `embedding`/`concept_index` của `IndexConcepts`, vốn là số ước lượng.
   - Pipeline bọc kho Pha B, tiêm hay mặc định, bằng một lớp mỏng **ở tầng composition**. Lớp này thêm `counted_in: "build"` vào mỗi dòng
     `append_usage`; mọi phương thức khác chuyển thẳng xuống kho gốc. Không sửa use case.
   - `DailySpendGuard` **giữ nguyên**: chỉ cộng purpose lecture/quiz/assistant/document. Trace module_title/embedding của lượt dựng không vào trần ngày Pha B.
     Khâu dựng dùng guard riêng của web theo purpose=build; không lấy test một dòng lecture để suy ra guard tính trace dựng.
   - Mọi phép cộng chi nhà cung cấp (receipt, ledger, báo cáo, bảng chi quản trị) **không cộng** dòng có `counted_in = "build"`. Phía lõi: ghi luật này
     vào docstring của lớp bọc. Phía web: người điều phối áp khi đọc bảng usage Pha B.

## Tiêu chí nghiệm thu

Mọi test phải **đỏ trên mã cũ**. Ghi trong báo cáo cách đã thấy chúng đỏ.

- [ ] **Không tạo JSON khi đã tiêm kho:** gián điệp thay hàm dựng `JsonPhaseBStore` ở cả hai module composition, gọi là raise. Chạy `graph()`
      (đoạn tên module) và `learning_prep()` với kho được tiêm, mô hình và embedding giả. Không lần nào gọi tới hàm dựng JSON.
- [ ] **Cùng một kho, kiểm bằng hệ quả quan sát được:**
  - một bản ghi `module_assignment` do A12 ghi đọc lại được từ kho tiêm;
  - cache tên module và cache chỉ mục khái niệm nằm trong kho tiêm;
  - `DailySpendGuard` của runtime con đọc đúng các dòng usage của kho tiêm.

  So danh tính đối tượng thì chỉ được kèm thêm, không thay cho các phép kiểm này.
- [ ] **Mặc định CLI không đổi:** không tiêm thì kho trỏ đúng `artifact_dir/phase_b/live.json` trên một `artifact_dir` tạm. Test cũ
      `tests/unit/application/test_build_pipeline.py` và `tests/integration/test_w13_build.py` xanh, không sửa assertion cũ.
- [ ] **`PhaseBRuntime`:** truyền `store` thì không gọi hàm dựng JSON; truyền cả `store` lẫn `store_path` thì `ValueError`.
- [ ] **Nguồn chi duy nhất:** một lượt dựng giả có một lời gọi tên module và một lần dựng chỉ mục khái niệm.
  - Meter đếm đúng một lần cho mỗi lời gọi.
  - Mọi dòng usage Pha B sinh trong lượt có `counted_in = "build"`.
  - Tổng chi các dòng **không** có cờ này bằng 0.
- [ ] Test kiến trúc, test Pha B, và **cổng toàn repo** qua `scripts/w05_run_tests.py` xanh, gồm test web W-15 hiện có.

## Ngoài phạm vi

- Lượt chạy có tiền và dry-run thật (thuộc W-15, cần chủ dự án duyệt riêng).
- `record_dir` mặc định của `PhaseBRuntime` khi `allow_spend`: ghi chú cho web nếu thấy ảnh hưởng, không sửa ở vé này.
- Helper version có Git HEAD (`_pipeline_version`).
- Developer API (SA-61).
