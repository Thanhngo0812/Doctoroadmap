# 18 — Cạnh ngược thứ tự sách không ép dãy học

**Nguồn chân lý:** [spec v3](../../doc/v3-lo-trinh-doc-duoc-spec.md), R17 · **Ai:** nhân viên · **Phụ thuộc:** — (làm cùng lúc với vé 07
được: cùng chạm `build_roadmap`/`sequence`) · **Chi phí mô hình:** 0

**Trạng thái:** chờ giao

## Vì sao (đọc lộ trình doc-1 sau vé 05 và 10b, 2026-09-27)
- Mục 2.2 Định thức bị xé: phần khai triển định thức bị đẩy ra sau mục 2.3 vì cạnh "Định thức con cấp p (mục 2.4) → Công thức khai triển
  định thức theo hàng 1". "Nhóm → Giao hoán" kéo "Giao hoán" của mục 1.1 sang 1.3 (module 6 mang tên "1.3 … · 1.1 Tập hợp").
  "Tổ hợp tuyến tính → Định thức bằng không" kéo một tính chất của 2.2 ra sau chương 3, dù sách cố ý dùng "tổ hợp tuyến tính" không hình
  thức ở 2.2 rồi mới định nghĩa ở chương 3.
- Đo 2026-09-27: cạnh có nguồn được dạy **sau** đích chiếm 4% (doc-1, 20/462), 7% (doc-2, 35/536), 17% (nhap-mon-ml, 11/63); gần như
  toàn bộ căn cứ "trong định nghĩa". 6 cạnh ngược "nói rõ" của doc-2 đều sai hoặc thừa ("Linear map → Linear algebra" coi tên ngành là
  tiên quyết; "Orthonormal list → Pythagorean theorem" chỉ là phụ thuộc của phép chứng minh; "Norms of linear maps → triangle
  inequality" trộn hai bất đẳng thức), nên không giữ ngoại lệ theo loại căn cứ.
- Thí nghiệm ngoại tuyến (0 USD, `scripts/doc-lo-trinh/thu_canh_nguoc_mem.py`):
  - doc-1: chuyển 20/494 cạnh; mục bị xé 6 → 3; "cần" quá dài 35 → 29; tên module theo đúng thứ tự sách; Q6 giữ 3/39; Q7b
    58,9% → 64,2%; Q7 89,7% → 85,8% (khi không tính cạnh mềm).
  - doc-2: chuyển 35/836 cạnh; mục bị xé 15 → 9; "cần" quá dài 56 → 51; Q6 giữ 2/57; Q7b 92,1% → 94,7%; Q7 giữ 58,0%.

## Việc cần làm
- Khi dựng dãy học (A10): cạnh `requires` mà vị trí dạy của nguồn lớn hơn vị trí dạy của đích → chuyển sang `soft_backward_edges`
  (giữ nguyên bản ghi cạnh, thêm lý do "ngược thứ tự sách"). Cạnh mềm không ràng buộc dãy học, không hiện ở dòng "cần:", không vào đóng
  tiên quyết của `roadmap-target`.
- Cạnh cùng vị trí (cùng chunk) và cạnh thuận giữ như cũ. Cạnh có một đầu chưa có vị trí dạy (khái niệm chỉ-nhắc) để vé 07 xử lý bằng
  bắc cầu.
- Bộ chấm báo Q7 cả hai cách (không tính và có tính cạnh mềm), để không lặng lẽ đổi mẫu số.
- Config ghi luật (ví dụ `backward-edges-soft-v1`).

## Tệp liên quan
`domain/sequence.py`, `application/use_cases/build_roadmap.py`, `application/use_cases/a8_score.py` (Q7).

## Nghiệm thu
- Test: cạnh ngược không ép thứ tự (đích giữ vị trí sách); cạnh thuận vẫn ép; cạnh mềm không hiện ở "cần:" và không vào
  `roadmap-target`; payload giữ cạnh mềm có lý do.
- **Tôi kiểm:** đọc lộ trình doc-1, doc-2, nhap-mon-ml trước/sau; bảng kiểm R11 (nhất là mục bị xé); Q6/Q7/Q7b.
