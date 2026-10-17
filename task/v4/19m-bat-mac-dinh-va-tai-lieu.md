# 19m — Bật mặc định chuỗi gộp, kèm tài liệu

**Nguồn chân lý:** [spec đổi mặc định chuỗi gộp](../../doc/doi-mac-dinh-chuoi-gop-spec.md), pha 4.
**Ai:** nhân viên (cấu hình, README) + Claude (ADR, `CONTEXT.md`, spec-addendum, bàn giao Pha B) · **Chi phí mô hình:** 0 USD · **Chặn bởi:** 19l qua
cổng · **Trạng thái:** xong 2026-10-17 — Claude kiểm đạt, commit chung một đợt

## Cần làm

**Nhân viên:**
- chuỗi thượng nguồn mặc định đổi từ `v3` sang `gop`; cập nhật `.env.example`;
- README ghi cách chọn chuỗi, và rằng chạy `a4` mặc định trên tài liệu cũ sẽ đổi chuỗi của lần `roadmap` sau.

**Claude:**
- **ADR 0016:**
  - danh tính là một phần của gộp ở A4;
  - neo và trạng thái dạy quyết ở A5, mỗi khái niệm một lời;
  - provenance rời chuỗi;
  - vì sao bỏ neo gom A5, đề cử theo mô tả và gom lô lời phán sửa.
- **ADR 0004:** thêm mục cập nhật.
- **`CONTEXT.md`, spec-addendum (sơ đồ A1 → A10), dòng "Lịch" của spec gộp khâu.**
- **Tệp bàn giao cho phiên Pha B:** id node đổi; cache bài giảng và quiz cũ mất hiệu lực.

Tài liệu và đổi cấu hình vào cùng một đợt commit.

## Phần Claude đã làm (2026-10-17)

- `doc/adr/0016-danh-tinh-trong-a4-neo-trong-a5.md` (mới);
- `doc/adr/0004-…`: thêm mục "Cập nhật 2026-10-17";
- `CONTEXT.md`:
  - sửa "Cặp nghi trùng" và "Provenance";
  - thêm "Câu neo" và "Trạng thái dạy";
  - "Bản đồ danh tính" và "Ứng viên danh tính mở rộng" ghi là chỉ còn ở artifact chuỗi v3;
  - "Xác minh danh tính" đổi thành "Xác minh cặp gộp khác tên";
- `doc/spec-addendum.md`:
  - ghi chú đầu tệp;
  - sơ đồ pha A theo luồng mới: A4 gộp kiêm danh tính, A5 mô tả và neo, A8 gồm pass chính LLM và pass phụ ML, bỏ A9′, A9″, A9‴;
  - mục dry-run;
  - các mục A4, A5, A8′, A9″, A10, Tầng 2b, B1 ghi rõ phần nào chỉ còn ở chuỗi v3;
- `doc/gop-khau-truoc-a8-spec.md`: sửa dòng "Lịch", và đánh dấu đã thay ở hai chỗ còn nói v3 là mặc định;
- `report/ban-giao-pha-b-chuoi-gop-2026-10-17.md` (mới): bàn giao cho phiên Pha B, có số id và module đổi trên 3 tài liệu vàng;
- vé 19n: ghi rõ `quote_is_verbatim` mà Pha B import từ `domain.provenance`.


## Ghi chú cho nhân viên

- **Chỗ đổi mặc định:** `Settings.upstream_chain` và `.env.example` (`DOC2ROADMAP_UPSTREAM_CHAIN`). `.env` của máy chủ dự án không đặt khoá này,
  nên đổi mặc định là đủ.
- **README đang mâu thuẫn với mặc định mới ở hai đoạn:**
  - "Chuỗi `v3` vẫn mặc định…";
  - đoạn nói `roadmap` theo chuỗi của canonical.

  Viết lại: chuỗi `gop` là mặc định; muốn chạy v3 thì chọn `--upstream-chain v3`. Thêm cảnh báo: chạy `a4` mặc định trên tài liệu cũ sẽ đổi chuỗi
  của lần `roadmap` sau.
- **Test:** có thể đang có test khẳng định mặc định là `v3`. Sửa theo mặc định mới. Phải giữ test `--names-only` / `--prepare` chạy v3 (19d).

## Nghiệm thu

- [x] Không đặt cấu hình thì `a4` và `roadmap` chạy chuỗi gộp. `a4 --names-only` vẫn chạy chuỗi v3 (19d).
- [x] Tài liệu không còn mô tả ba stage cũ như luồng mặc định. Toàn bộ test qua.

## Phần nhân viên hoàn thành (2026-10-17, chờ commit chung)

- Đổi `Settings.upstream_chain` và `.env.example` sang `gop`; `Settings()` thực tế trên máy cũng ra `gop`, không sửa `.env`.
- README ghi chọn lại v3, giữ ngoại lệ `--names-only`/`--prepare`, và cảnh báo chạy A4 mặc định trên tài liệu cũ sẽ đổi chuỗi roadmap sau. Roadmap vẫn theo canonical mới nhất, không tự đổi artifact v3 cũ.
- Test CLI/composition thật với mô hình giả xác nhận chuyển canonical v3 sang gop, có neo, và roadmap đi theo các stage gop; chọn v3 tường minh giữ luồng v3. Hai ca mặc định mới đỏ trước sửa rồi xanh; các test ngoại lệ 19d vẫn qua.
- Cập nhật một stub CLI nhận các keyword hiện có. Ghim hai test quiz Pha B vào doc-1 graph v45 vì chúng cố định module_023 và đòi 5 câu; graph mới nhất v53 sau cổng chỉ sinh 4 câu. Đã đối chiếu config cũ v3 vẫn lỗi như nhau trước khi ghim; không sửa logic quiz hoặc nới assertion.
- **Toàn bộ 1.638 test qua**, mã thoát 0, 243,95 giây, 0 USD API. Nhóm liên quan 51 test và bộ CLI 11 test qua; các số có giao với lượt toàn kho. `git diff --check` qua.

[Báo cáo phần nhân viên và lệnh nghiệm thu](../../report/v4-19m-phan-nhan-vien-2026-10-17.md). Chưa stage/commit riêng; giữ phần tài liệu của Claude để kiểm và commit chung như yêu cầu ở trên.

## Kiểm của Claude 2026-10-17 — đạt

- **Mặc định trên kho thật** (không truyền `--upstream-chain`, chỉ dry-run, 0 USD, không ghi artifact):
  - `a4 --doc-id doc-1 … --dry-run` ra `upstream_chain: gop` và tái dùng mọi phần của canonical v5. Nghĩa là cấu hình mặc định mới cho đúng
    config hash của cổng 19l.
  - `roadmap --dry-run` của doc-1 và doc-4 đi đúng các stage chuỗi gộp và tái dùng tới `stages` (doc-1 v52, doc-4 v22).
  - `module_titles` báo "sẽ chạy" nhưng ước 0 lời gọi, vì tên được cache theo ngữ cảnh.
- **Test bắt được lỗi:** chạy test 19d trên bản sao `src` đặt lại mặc định `v3` thì hai ca mặc định đỏ; ca chọn `v3` tường minh vẫn xanh.
- **`a4 --names-only` chạy v3:** không chạy trên kho thật, vì sẽ ghi một canonical lớp tên làm bản mới nhất. Đã được phủ bằng test 19d
  `test_incomplete_cli_uses_v3_under_gop_default`; test này xanh với mặc định `gop`.
- **Toàn kho:** 1.638 test qua, mã thoát 0. Con số gồm cả test Pha B chưa được track.
- **Ngoài phạm vi vé:** nhân viên ghim hai test quiz Pha B vào đồ thị v45. Hai test này gãy vì cổng 19l ghi đồ thị mới, không vì 19m. Tệp đó
  thuộc phiên Pha B, chưa được track, nên không vào commit này. Đã ghi vào tệp bàn giao Pha B.
