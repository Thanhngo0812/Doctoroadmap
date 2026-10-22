# W-25 — Đồng bộ xác nhận, huỷ và kết thúc bản dựng

**Nguồn chân lý:** [spec chức năng](../../doc/web-chuc-nang-spec.md), mục 4 (xác nhận/huỷ, ghi usage ở mọi kết thúc); [W-14](W-14-tai-sach-len-ban-dung.md); [quy trình nhánh](../../doc/quy-trinh-nhanh-va-ghep-main.md).
**Ai:** nhóm lõi/backend W-14 · người soát kiểm · **Chi phí mô hình:** 0 USD · **Chặn bởi:** mã backend W-14 tại `5b24ece`, không chờ W-14 được nghiệm thu · **Trạng thái:** đạt · đã ghép/đẩy `a572459`, mốc `4dbfe8e`.

**Nghiệm thu lại 2026-10-22:** nhận `c00c028` và main `cd22e9b`, mốc soát/cổng `4dbfe8e`. **2.163 Python đạt/0 fail/1 Cloudinary live không bật; 85 React nền/build; sáu guard W-25 bị assertion bắt**, source phục hồi. Test PostgreSQL kiểm hai thứ tự commit, graph/media/terminal, usage/receipt/lease/mail. Backend/schema W-14 đủ ghép, không đóng React hoặc toàn W-14. Xem [phán xét mới](../../report/dieu-phoi-kiem-lai-w25-w14-react-w24-va-ke-hoach-2026-10-22.md).

## Vì sao

Điều phối soát `5b24ece` và tái hiện trên worktree tích hợp `85ecce0` (W-07 + W-14, chỉ sinh lại OpenAPI khi ghép). Bộ 35 test W-14 hiện có đạt, nhưng hai ca PostgreSQL mới đều đỏ ở assertion nghiệp vụ, 0 setup error:

1. Xác nhận đọc `awaiting_confirmation`, yêu cầu huỷ ở connection độc lập commit trước, sau đó xác nhận ghi đè thành `queued`. DB có `cancel_requested=true`, `counts_quota=true`, course vẫn `failed`; worker bỏ qua việc này.
2. Worker đang đọc metadata graph để phát hành kết quả thành công thì yêu cầu huỷ commit. Worker vẫn ghi `succeeded`, course `ready` và gửi thư thành công dù cờ huỷ đã bật. Usage giả `.003` vẫn được ghi; sửa lỗi không được làm mất số đó.

Bằng chứng và mã tái hiện: [báo cáo soát](../../report/dieu-phoi-nghiem-thu-w07-w14-w24-va-ke-hoach-2026-10-21.md), [hai ca tái hiện](../../report/coord-w07-w14-w24-evidence-2026-10-21/w14-cancellation-repros.py.txt), [JUnit đỏ](../../report/coord-w07-w14-w24-evidence-2026-10-21/runs/w14-repro2.xml).

## Cần làm

- Giữ worktree W-14. Làm nhánh riêng `work/w25-build-cancellation`, worktree một cấp `tmp/w25-build-cancellation`, từ đúng mốc W-14 đã bàn giao; nhận main mới theo quy trình. Không sửa nhánh của web.
- Cho xác nhận và huỷ có một thứ tự nhất quán bằng transaction/khóa hàng hoặc chuyển trạng thái có điều kiện. Huỷ đã commit trước phải giữ huỷ, không bị đưa lại vào hàng đợi hoặc trừ lượt. Nếu xác nhận commit trước rồi huỷ thì giữ luật quota hiện hành; không tự hoàn lượt.
- Trong transaction kết thúc của lease hiện hành, đọc lại cờ huỷ dưới khóa trước khi chốt trạng thái. Kết quả bị huỷ không được trở thành course `ready`, phát hành phiên bản học được hoặc gửi thư thành công. Xét luôn huỷ khi đang tải media; nếu thao tác đang diễn ra không dừng được thì dừng tại ranh giới kế tiếp và giữ trạng thái cuối đúng.
- Giữ receipt/lease fence, callback muộn, usage thực và `usage_complete` kể cả khi huỷ hoặc publication lỗi. Không ghi chi 0 thay usage khác 0, không cộng receipt hai lần. Không mở rộng sang runner thật.
- Thêm test với hai engine/store/connection độc lập, ép cả hai thứ tự commit; quan sát trạng thái DB, quota, course, thư và usage. Mã tái hiện của điều phối là điểm bắt đầu; khi đổi cách khóa phải cập nhật điểm đồng bộ của test để không dựa cứng vào số lần gọi `get_job` hoặc tạo deadlock giả.
- Không thêm migration: giữ `w14_0006 → w06_0005`. Khi nhận W-07, sinh lại OpenAPI chứa cả progress và builds; không lấy đè toàn bộ JSON của một nhánh.

## Tiêu chí nghiệm thu

- [x] Hai lỗi trên thấy đỏ ở assertion trên mã cũ; bản sửa xanh, không lỗi setup hoặc dùng timeout thay bằng chứng trạng thái cuối.
- [x] Cả hai thứ tự xác nhận/huỷ và huỷ trong graph/media publication đều được kiểm PostgreSQL độc lập; không có `queued + cancel_requested` bị treo, không báo thành công sau huỷ đã được nhận trước terminal commit.
- [x] Usage giả khác 0 giữ nguyên và ghi đúng một lần sau huỷ; course không `ready`, không thư thành công. Callback lease cũ không đổi trạng thái lease mới.
- [x] Giữ các ca W-14 cũ và mutation có ý nghĩa; cổng toàn repo/PostgreSQL, React/build trên đúng mốc có main mới đều đạt. Alembic đúng một head `w14_0006`.
- [x] Báo cáo `report/w25-dong-bo-huy-ban-dung-<ngay>.md` có commit, RED/GREEN, SQL độc lập và phần React W-14 còn chờ; người soát xác nhận trước ghép.

## Ngoài vé

React W-14, W-11, chạy mô hình thật/chi phí W-15, thay đổi semantics hoàn quota. W-25 đạt và backend được ghép không tự đóng W-14 đầu-cuối.
