# DG-04 — Hợp đồng đánh giá, bộ xuất hệ chính, chấm A8/A10, đối chiếu bộ chấm cũ

**Nguồn:** spec mục 1, 2, 3, 8 (A8, A9/A10) và "Quyết định kiểm thử" (phép đối chiếu) · **Ai:** agent B · **Chi phí mô hình:** 0 · **Chặn bởi:** không ·
**Hạn:** 29/10 · **Trạng thái:** ready-for-agent

Đây là vé vạch đường của làn chấm: một đường mỏng chạy trọn từ artifact tới bảng số.

## Làm được gì

Hai lệnh:
- `xuat`: đọc graph trong kho artifact chung (chỉ đọc), ghi ra một tệp **hợp đồng đánh giá `danh-gia-xuat-1`**;
- `cham`: đọc hợp đồng, vàng G3/G4 và bảng căn, ghi ra bảng chỉ số theo chương và theo cuốn.

Vàng A8 cũ được đổi sang G3/G4 cộng bảng căn. Khi đó Q6, Q7, Q7b, P/R/F1 trực tiếp và bao đóng **bằng đúng** số của bộ chấm cũ.

Graph dùng để đối chiếu:
- xstk-ch3-1: v56 (cổng 19l) và v68 (đã ghim);
- doc-4: v23 (cổng 19l) và v27 (đã ghim);
- doc-1: v8 (dựng lại ngày 2026-10-20), chỉ khi bộ chấm cũ chuyển được id vàng sang graph này. Nếu không chuyển được thì ghi vào báo cáo, không ép.

## Việc

1. **JSON Schema `danh-gia-xuat-1`** (spec mục 2), gồm các khối:
   - `dinh_danh`: bản ghi lượt chạy, gồm commit, hash cấu hình, mô hình, transport, ngày, hệ, biến thể, lượt nhiễu;
   - `cau_truc`, `khai_niem`, `canh`, `cap_ung_vien`, `lo_trinh`, `chi_phi`.

   Phần nào hệ không có thì để `null`. Validator chỉ dùng thư viện chuẩn, kiểm lược đồ và tính nhất quán (cạnh trỏ tới khái niệm có thật, dãy học không lặp).
2. **Bộ xuất hệ chính** (seam xuất, được nhập mã pipeline để đọc kho):
   - đọc graph ở stage `stages`, canonical, chunks có vai trò, ứng viên, manifest từng stage;
   - đọc usage đặt tên module ở kho Pha B mà lượt chạy chỉ định;
   - trường thiếu thì báo lỗi rõ, không điền ngầm.

   Dùng kho artifact chung **chỉ đọc**. Không mở kho Pha B chung (`live.json`): test dùng một kho Pha B fixture.
3. **Bộ chuyển vàng cũ:** vàng A8 cũ (`xstk-ch3-1-10-13-vang.json`, `doc-4-chuong-8-vang.json`, `doc-1-10-12-vang.json`) sang G3 (mỗi khái niệm của vàng cũ thành một khái niệm, mã `G-…`)
   cộng G4 cộng bảng căn, trong đó mỗi id cũ căn `khop` với node tương ứng. Dùng bản đồ danh tính và bảng chuyển hướng như bộ chấm cũ.
4. **Lõi chấm** (seam chấm, thuần) cho A8 và A10, theo spec mục 8:
   - F1 trực tiếp và bao đóng, mức nghiêm và nới;
   - Q6 theo dãy học (ngược hoặc ngoài lộ trình, chia cho tổng);
   - Q7, Q7b;
   - số chu trình, số thành phần liên thông.

   Đầu ra là bảng số đếm theo chương, đúng định dạng DG-05 dùng, cộng thước theo cuốn.

## Phạm vi tệp

Gói `danhgia`: hợp đồng (schema, validator), xuất (hệ chính), vàng (chuyển vàng cũ), chấm (A8, A10), CLI. Test trong `tests/evaluation/`, cộng một test kiến
trúc: seam chấm không nhập `doc2roadmap`.

## Tiêu chí nghiệm thu

- [ ] Hợp đồng xuất từ các graph trên qua validator.
- [ ] **Phép đối chiếu:** trên cùng graph và cùng vàng, mọi chỉ số trùng đúng với bộ chấm cũ (`score_roadmap_order` và bộ chấm tập giữ lại v3), sai lệch 0.
  Ghi bảng so trong báo cáo.
- [ ] Ca biên của lõi chấm, mỗi ca một test với số tính tay: mẫu số 0 trả `None`; đầu cạnh không căn được; cạnh mềm; tranh chấp; nghiêm và nới khác nhau.
- [ ] Bộ xuất báo lỗi khi thiếu trường, có test.
- [ ] Bảng phá, gồm ít nhất:
  - tính Q6 với mẫu số chỉ gồm cạnh đã xếp;
  - quên ánh xạ danh tính;
  - tính bao đóng sau khi lọc phạm vi thay vì trước;
  - đếm cạnh mềm vào cạnh cứng.

## Ngoài phạm vi

Căn tự động với vàng mới (DG-09); thước A1–A5 (DG-10, DG-13); chi phí đầy đủ có giây chờ embedding (DG-06).
