# Kiểm lại W-13 và W-24 sau sửa — 2026-10-19

**Kết luận:** **W-13 đạt nghiệm thu trong phạm vi vé lõi.** Các lỗi runtime cũ của W-24 đã được sửa và kiểm lại đạt;
**W-22/W-24 còn mở phần Figma/trang/prototype và lỗi khung xem auth mới**. Không giữ lại các lỗi cũ như điều kiện chặn sau khi đã thấy sửa đúng.

Đầu vào: HEAD `7baa7d2`, W-13 bổ sung `66419a8`/`b0bdb5b`; [manifest SHA-256](../artifacts/coord-close-w13-w24-2026-10-19/manifest.json).
Điều phối không chạy thêm lượt có tiền. **Chi phí kiểm lại: 0 USD.**

## 1. W-13 — đã gỡ điều kiện chặn doc-6

Đã đọc [bàn giao hoàn tất](w13-hoan-tat-doc6-2026-10-19.md), [kết quả có tiền](w13-doc6-ket-qua-2026-10-19.json),
bản sửa đường cache Pha B và test hồi quy. Hai lượt có tiền do nhân viên chạy sau phê duyệt đã có kết quả `succeeded`:

| Kho | Graph | Module / khái niệm | Chi quy đổi được ghi |
|---|---:|---:|---:|
| Chép cache lịch sử, dựng lại | 37 | 2 / 11 | 0,1125263 USD; usage chưa đầy đủ |
| Bắt đầu từ kho rỗng | 8 | 2 / 14 | 0,1203762 USD; usage đầy đủ |

Tổng **0,2329025 USD** là chi quy đổi theo usage nhận được, không phải hoá đơn đã đối soát; không coi phần thiếu usage ở lượt đầu là 0 token.
Đã truy vấn độc lập hai SQLite, số chi khớp và cờ thiếu usage được giữ. Sau lượt kiểm của điều phối, mỗi kho có bốn hàng `succeeded`,
gồm ba hàng nhân viên báo và một hàng cache do điều phối vừa chạy; tổng chi không tăng.

**Chạy lại độc lập:** `scripts/w13_doc6_acceptance.py` và cùng lệnh với `--fresh-store`, không truyền `--allow-spend`.
Script chặn cả sinh, embedding và header ADC trước khi chạy. Cả hai **thành công, đủ bốn bước, 0 lời gọi mô hình, 0 USD**,
giữ nguyên graph 37/8; kiểm vật lý chunk trước/sau nhãn, canonical `coverage=none`/không vàng, graph hoàn tất, index công thức và JSON đã lưu DB đều đạt.
[Kết quả truy vấn/kiểm](../artifacts/coord-close-w13-w24-2026-10-19/w13-checks.json),
[lượt kho cache](../artifacts/coord-close-w13-w24-2026-10-19/w13-replay-cache.json),
[lượt kho ban đầu rỗng](../artifacts/coord-close-w13-w24-2026-10-19/w13-replay-fresh.json).

Đã băm lại doc-6 và PDF nhap-mon-ml được khôi phục: khớp bằng chứng; sáu phép hiệu chỉnh từ PDF gốc đã có trong bàn giao.
Không lặp lại bước hiệu chỉnh tất cả PDF trong lượt soát này.
Thử bỏ dòng chọn chung đường cache trong tiến trình: test `test_learning_prep_reuses_paid_concept_cache_without_spend` đỏ đúng lỗi hồi quy;
[kết quả mutation](../artifacts/coord-close-w13-w24-2026-10-19/w13-cache-mutation.json). Không sửa tệp nguồn.

**Kiểm hồi quy trọng tâm:** W-13/kiến trúc và token W-24 tổng cộng **83 passed**, 0 fail/error/skip;
[XML](../artifacts/coord-close-w13-w24-2026-10-19/regression-tests.xml).
Không tuyên bố đã tự chạy lại toàn bộ 1.878 unit test mà nhân viên báo.

## 2. W-24 — đóng các lỗi cũ đã kiểm đạt

- **GIF khi giảm chuyển động:** components, desktop sáng, desktop tối và mobile đều chọn PNG tĩnh; ba ảnh chụp liên tiếp của mỗi trang có hash giống nhau.
- **Vùng bấm:** không còn nút dưới 44×44 px trong các preview chính được kiểm ở 390; kiểm thêm 768/1280, không tràn ngang.
- **Guard token:** ba phép đổi riêng primary CSS, spacing JSON và RGBA tối CSS **đều làm bộ test đỏ**, thay vì hai phép còn xanh lần trước.
- **Chat mẫu:** payload thẻ HTML trước đây tạo được node nay hiển thị như văn bản, số node mang ID thử nghiệm bằng 0.
- **Bản vẽ tài khoản:** đã thêm `auth_screens.html` để nhóm W-02 dùng làm đầu vào thiết kế, có đăng nhập/đăng ký và các dải lỗi.

Bằng chứng: [runtime/ảnh/hash](../artifacts/coord-close-w13-w24-2026-10-19/design/runtime.json),
[mutation token](../artifacts/coord-close-w13-w24-2026-10-19/token-probes.json). Bộ token mới có **14 test đạt** trong 83 test ở trên.
Kết quả này xác nhận các nhánh đã thử, không xác nhận tuyên bố “an toàn tuyệt đối trước mọi chuỗi injection” trong báo cáo nhân viên.

## 3. Phần W-22/W-24 còn phải giao

1. **Đồng bộ Figma đúng dữ liệu thật.** Plugin mới đã có lệnh tạo Variables nhưng còn sáu màu tối lệch JSON/CSS đang bàn giao:
   ví dụ `color/bg` sinh `#0F172A`, trong token là `#0E1217`; `color/surface` sinh `#1E293B`, trong token là `#161B22`.
   [Bảng sáu cặp lệch](../artifacts/coord-close-w13-w24-2026-10-19/figma-plugin-drift.json). Đây là đối chiếu mã plugin, không phải export từ file Figma.
   Cần bản xuất Variables thực có nguồn gốc và mapping tên; nếu dùng plugin làm bằng chứng thì sửa dữ liệu của nó cho đúng trước.
2. **Đủ trang/trạng thái và bốn prototype thực.** Plugin tạo khung ghi chữ mô tả luồng, chưa có liên kết chuyển frame trong mã;
   chưa nhận node/ảnh từng trang, link chạy bốn luồng và video. Thêm một trang ghi đặc tả chưa thay cho prototype bấm được.
   Bảng 14 nhóm “đã có” vẫn lấy nút/thành phần làm bằng chứng cho một số trang. Giữ nguyên tiêu chí W-22/W-24 gốc, chỉ yêu cầu giao phần còn thiếu.
   Lần trước công cụ nhận 403 khi mở Figma; lần này không kiểm trực tiếp lại file và không kết luận file không tồn tại.
3. **Khung xem auth ở 390:** còn tràn ngang **20 px**, do khung mobile rộng cố định cộng lề ngoài.
   [Ảnh](../artifacts/coord-close-w13-w24-2026-10-19/design/auth_screens.html-390.png).
   Sửa trang xem hoặc giao frame/ảnh 390 đúng kích thước; đây là lỗi preview mới, không phải kết luận giao diện React W-02 đã bị lỗi.

## 4. Điều chỉnh kế hoạch

- **Lõi:** W-13 đã đạt, không còn chờ cache doc-6. Tiếp tục W-05 theo checkpoint nền W-01 đã thống nhất.
- **Web:** tiếp tục chốt snapshot W-01 và làm W-02; dùng bản auth mới theo spec, kiểm lại khi chuyển sang React.
- **Thiết kế:** chỉ xử lý ba nhóm việc còn lại ở mục 3; không yêu cầu sửa lại các lỗi cũ đã đạt ở mục 2.
- **W-15:** gỡ phụ thuộc chưa nghiệm thu W-13; vẫn chờ **W-14** nghiệm thu và tuân thủ phạm vi phê duyệt chi của lượt W-15.
- **W-23:** chưa mở; vẫn chờ W-22 cùng W-08/W-09/W-10 theo kế hoạch gốc. Tiếp tục Vertex đến khi chủ dự án chỉ thị đổi.
