# SA-46 — Quiz lộ trình: chuẩn hoá phạm vi và giữ trần cấu hình

**Nguồn chân lý:** [SA-37](37-quiz-ca-lo-trinh-tai-lieu-nhieu-module.md), [spec B2](../../doc/pha-b2-spec.md), mục 7; phát hiện ở SA-45.

**Ai:** nhân viên · nhân viên cấp cao kiểm · **Chi phí mô hình:** 0 USD (ngân hàng giả/phát lại) · **Chặn bởi:** không · **Trạng thái:** đã vá/kiểm thử 2026-10-19; chờ kiểm ghép

**Bàn giao:** [SA-46/50](../../report/pha-b-sa46-50-2026-10-19.md). Scope chuỗi/object cùng lấy mẫu, trần giữ theo cấu hình và `n`, mỗi khái niệm lấy mẫu chỉ một câu; không bù bằng biến thể của khái niệm khác. Giữ thuật toán round-robin cũ, 0 USD.

## Vì sao

Ba assertion trong `tests/unit/application/test_phase_b_sa45_artifact_audit.py` đã đỏ trên mã hiện hành ngày 2026-10-18:

- `test_assistant_roadmap_string_obeys_ten_question_cap`: 18 câu thay vì tối đa 10, trên đồ thị 6 module × 3 khái niệm, ngân hàng giả hợp lệ cho mọi khái niệm.
- `test_assistant_roadmap_string_matches_canonical_scope_sample`: cùng seed nhưng chuỗi `roadmap` lấy cả 18 khái niệm, đối tượng `{"kind":"roadmap"}` lấy mẫu 10.
- `test_roadmap_with_configured_cap_also_limits_explicit_n`: cấu hình trần 3 nhưng `n=10` sinh 10 câu.

`QuizUseCase.make_quiz` chỉ đặt `roadmap_scope` cho đối tượng có `kind`. Trong khi `PhaseBRuntime.assistant` truyền nguyên phạm vi chuỗi từ công cụ, `_resolve_scope('roadmap')` chỉ trả `(None, None)` và không kích hoạt lấy mẫu. Nhánh `cap = min(n or setting, 10)` cũng bỏ trần cấu hình khi có `n`.

## Cần làm

- Chuẩn hoá các dạng phạm vi lộ trình được công cụ/CLI hỗ trợ trước khi chọn khái niệm; mọi dạng phải cùng đường lấy mẫu, ưu tiên đã học, luân phiên module và seed.
- Trần số câu lộ trình là min của yêu cầu `n` (nếu có), `quiz_roadmap_max_items` và trần hợp đồng 10.
- Giữ `home_scope`, nguồn tạo, tham chiếu phiên và ngân hàng/cache theo hợp đồng B2. Không gọi thêm mô hình chỉ để đủ số câu khi thiếu câu hợp lệ.

## Tiêu chí nghiệm thu

- [ ] Chạy `python -m pytest ... --runxfail tests/unit/application/test_phase_b_sa45_artifact_audit.py -k "assistant_roadmap or configured_cap"`: ba test trên phải đỏ trước sửa, rồi xanh sau sửa và bỏ nhãn xfail. Ba test câu điền khuyết trong cùng file thuộc SA-50.
- [ ] Bổ sung kiểm qua công cụ `make_quiz` của trợ lý: đầu vào `scope='roadmap'` và `n` không vượt trần, có ưu tiên tiến độ và seed lưu được.
- [ ] Test bảo vệ phạm vi module/danh sách khái niệm vẫn xanh; đề công khai không lộ đáp án.
- [ ] Phát lại 0 USD trên doc-4, ghi số câu/module phủ, seed và 0 lời gọi mạng; chạy test kiến trúc.

## Ngoài vé

Không đổi số câu mặc định của quiz module; không sửa tiến độ, phiên hay bộ luật chất lượng câu hỏi. Không chạy lượt có tiền.
