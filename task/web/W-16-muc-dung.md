# W-16 — Trang mức dùng và dải hết trần

**Nghiệm thu lần 7, 2026-10-26: nhận mốc backend `d1bf42b`, ghép local `c5b4f5f`; toàn W-16 vẫn mở.** Projection qua usage_rows, ngày/tháng nửa mở theo giờ Việt Nam, counts_quota là lượt, tách purpose/actor và trace build không cộng trùng, max=null khi demo tắt, HTTP không USD. 13 ca PG nằm trong cổng ghép 2.735 Python/203 React/build; probe độc lập 12 đạt/7 mutant bị bắt. Web còn trang và dải React sau khi sửa/nhận W-10; không giao làm lại backend, không thay cấu hình giá/trần. [biên bản lần 7](../../report/dieu-phoi-nghiem-thu-ba-nhom-lan7-2026-10-26.md) và [lời giao](../../report/lenh-giao-viec-ba-nhom-lan7-2026-10-26.md).

**Phân công sau nghiệm thu lần 6, 2026-10-25:** W-09/W-14 đã đạt; W-15 đã nhận có ghi chú. Lõi nhận **mốc backend W-16** trong worktree riêng, soát/dùng lại usage-1/GET me/usage, truy vấn ledger/quota đã có từ W-09/W-14, chỉ bổ sung chỗ thiếu/sai với test. React do web làm sau W-10; backend đạt không đóng toàn vé. Kiểm ngày/tháng Việt Nam, cộng xuyên khoá, không USD cho người thường, max=null khi demo tắt; không đổi giá/trần/logic sinh-cache-retry của core. 0 USD, [biên bản lần 6](../../report/dieu-phoi-nghiem-thu-ba-nhom-lan6-2026-10-25.md) và [phạm vi tệp/lời giao](../../report/lenh-giao-viec-ba-nhom-lan6-2026-10-25.md).

**Nguồn chân lý:** [spec chức năng](../../doc/web-chuc-nang-spec.md), mục 8 (`usage-1`, bốn trần); [spec Pha B2](../../doc/pha-b2-spec.md), mục 8; spec thiết kế, trang
mức dùng và dải hết trần.
**Ai:** lõi làm mốc backend; web làm React/tích hợp · người soát kiểm · **Chi phí mô hình:** 0 USD · **Chặn bởi:** W-09, W-14 · **Trạng thái:** ready-for-agent

## Vì sao

Người dùng cần biết còn hỏi được bao nhiêu hôm nay và còn mấy lượt dựng, để không bất ngờ khi chạm trần.

## Cần làm

**`UsageService.my_usage`** trả `usage-1` đúng spec mục 8:
- tỉ lệ đã dùng của trần người học hôm nay, giờ đặt lại;
- lượt dựng tháng này, giờ đặt lại; trần tắt (bản demo) thì trả `max: null` và giao diện ghi "không giới hạn";
- trần nội dung dùng chung hôm nay có đang chạm không.
- **Người dùng thường không thấy USD.**
- Đọc sổ chi bằng bộ lọc mới của W-05 (`usage_rows(learner_id, since, purposes)`), không đọc cả sổ.

**HTTP:** `GET /me/usage`.

**Giao diện:**
- **trang "Mức dùng":** thanh tỉ lệ trần hôm nay, giờ đặt lại theo giờ Việt Nam, lượt dựng còn lại, giải thích ngắn "hết trần vẫn đọc bài có sẵn, làm quiz,
  xem thư viện";
- **dải cố định** khi `limited`: ở khung chat và ở nút tạo tài liệu, kèm giờ đặt lại;
- **khi trần nội dung dùng chung chạm:** bài giảng chưa có hiện lời nhắn `tran_he_thong` của W-08; trang mức dùng ghi "nội dung mới tạm dừng tới ngày mai".

## Tiêu chí nghiệm thu

Mỗi test thấy đỏ trước trên bản sai:
- [x] Phản hồi `my_usage` của người dùng thường không có trường nào chứa USD (quét đệ quy tên khoá có `usd`, `cost`).
- [x] Đầu ngày mới theo giờ Việt Nam (đồng hồ giả ở 16:59 và 17:00 UTC) thì tỉ lệ về 0.
- [x] Chi ở hai khoá cộng chung vào tỉ lệ.
- [ ] Ảnh chụp trang mức dùng ở ba trạng thái (còn nhiều, gần hết, hết) và dải hết trần trong khung chat.

## Ngoài vé

Trang chi theo USD cho admin (W-17).
