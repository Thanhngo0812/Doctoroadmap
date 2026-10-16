# 19b — Bớt lời phán sửa vô ích ở A4

**Nguồn chân lý:** [spec đổi mặc định chuỗi gộp](../../doc/doi-mac-dinh-chuoi-gop-spec.md), pha 1a mục 1–2.
**Ai:** nhân viên · **Chi phí mô hình:** 0 USD · **Chặn bởi:** không (nên làm sau 19a vì cùng đoạn mã đề cử) · **Trạng thái:** sẵn sàng giao

## Vì sao

Trên 13 canonical chuỗi gộp có hai loại cặp tốn lời phán sửa mà chưa từng cho lần gộp nào (nghiên cứu mục 2):
- **Nguồn `same_evidence`:** 0 gộp, khoảng 112 lời phán sửa trên doc-4.
- **Cạnh cắt chỉ có nguồn `ngram`:** 0 gộp ở cấu hình mặc định, 116 lời trên doc-4.

## Cần làm

Chỉ áp ở chuỗi `gop`.
- Nguồn `same_evidence` không còn sinh cạnh đề cử.
- Cạnh `ngram` vẫn dùng để chia cụm. Cặp bị cắt mà nguồn duy nhất là `ngram` thì giữ tách, không gọi mô hình. Nhật ký ghi lý do riêng, và `stats` có số đếm.
- Cả hai luật có mục riêng trong config chuỗi `gop`.

## Nghiệm thu

- [ ] Test trên fixture thật với mô hình giả:
  - không cặp nào mang nguồn `same_evidence`;
  - cặp cắt chỉ có `ngram` không sinh lời gọi, giữ tách, và được đếm;
  - cặp cắt có thêm nguồn khác vẫn được phán sửa.
- [ ] Đổi luật thì khoá cache đổi. Băm config v3 giữ nguyên.
- [ ] Mỗi luật có test thấy nó trượt khi luật bị bỏ. Toàn bộ test qua.
