# 05 — `a4-evaluate` đo quan hệ

**What to build:** Lệnh chấm in thêm các số cần cho luật đánh giá ở ticket 00, để ticket 07 không phải dùng script
riêng ngoài repo.

**Blocked by:** 01 — Spec và ADR 0007. Làm song song với 02 được.

**Status:** done

- [x] Giữ nguyên các khoá đang có (`subtype_recall`, `subtype_incorrect`…), để còn so với số cũ.
- [x] Thêm `subtype_precision`, tính giống bảng A/B trong báo cáo chạy thật:
  - cạnh đúng là cạnh `subtype_of` nằm trong tập cặp cha–con đúng chiều;
  - cạnh sai tính như `subtype_incorrect`;
  - precision = đúng / (đúng + sai).
- [x] Thêm `relations_2a_on_gold`: số cạnh có `"2a"` trong `origins` và khác `subtype_of`, nằm trên cặp có nhãn, chia
      theo nhãn vàng (`same`, `parent_child`, `related`, `different`).
- [x] Thêm tuỳ chọn loại một danh sách mục khỏi mẫu số recall `subtype_of`. Luật ticket 00 dùng nó cho 3 cặp bộ phận;
      mặc định không loại mục nào.
- [x] `a4-evaluate` và `scripts/run_a4_arm.py` in các số mới.
- [x] Test trên artifact giả, mỗi số có một ca đếm tay.
- [x] Toàn bộ test xanh, chặn mạng.

Ba giá trị dùng lặp `--exclude-subtype-item` để báo recall trên 44 cặp:

- `67f1356fee7c70e1b7fd206624ec2c7ce4d1d97a30e6f95ec6ec6190f12242dc`
- `67188bf62d359f140fd5062de76013da4ff1baef9b4a85c6499b588cd0f72659`
- `c0f3581825f6d36451236d4a673f597d7f6886452d9b2d260489295a20ec2d12`
