# Bảo vệ tài khoản admin đầu tiên

**Status:** accepted — 2026-10-28, quyết định của chủ dự án; backend W-17.1 được nhận lần12/ghép local 4e6f33cb. DB dùng chung chưa migration/đối chiếu UUID.

**Admin đầu tiên không được khoá quản trị, hạ quyền hoặc xoá.** Định danh tài khoản được bảo vệ phải bền vững phía máy chủ, gắn với lần bootstrap admin đầu tiên. Đây không phải “hàng admin đầu tiên” trong một danh sách đang lọc, cũng không phải một tài khoản bất kỳ còn giữ role admin sau cùng.

**Căn cứ:** khi nghiệm thu W-17.1, người làm nêu spec cũ chỉ cấm hạ admin cuối, nhưng vẫn cho disable admin cuối và thu hồi mọi phiên. Chủ dự án trả lời nguyên văn:

> admin đầu tiên ko đc khóa hay gì

Điều phối đã ghi nhận phạm vi bảo vệ khỏi các thao tác làm mất tài khoản/quyền quản trị: status disabled, đổi role khỏi admin, xoá tài khoản. Áp dụng cả khi admin đầu tiên tự thao tác hoặc admin khác thao tác. Thay đổi hồ sơ/mật khẩu thông thường và các bảo vệ đăng nhập, CSRF, giới hạn thử sai của W-02/W-03 vẫn theo hợp đồng hiện hành.

**Considered Options**

- *Chỉ bảo vệ admin cuối, vẫn cho disable.* Không đáp ứng chỉ thị: với hai admin thì người đầu tiên vẫn bị hạ quyền; khi chỉ còn một admin vẫn có thể mất mọi phiên quản trị.
- *Tính người được bảo vệ lại từ role/status/thứ tự/created_at hiện hành.* Không ổn định: một tài khoản thường tạo sớm được nâng admin sau này không được thay thế định danh admin đầu tiên.
- *Chỉ ẩn nút ở React.* Không bảo vệ service/API hoặc trường hợp cạnh tranh. Bất biến phải được kiểm ở máy chủ, UI chỉ phản ánh hợp đồng.

**Consequences**

- W-17.1 phải giữ định danh bảo vệ qua việc thêm admin/đổi vai trò những người khác; không tạo thêm hệ vai trò ngoài user/admin chỉ để làm việc này.
- Từ chối disable/demote/delete tài khoản được bảo vệ nguyên tử, kể cả PATCH nhiều field; không đổi lén field còn lại, phiên hoặc ghi sự kiện thành công khi thao tác bị từ chối. Guard cũ về quyền, Actor hiện hành, cạnh tranh và rollback vẫn giữ.
- W-17.1 dùng registry bootstrap_admin singleton, trigger bảo vệ registry/account và giao dịch bootstrap/audit; migration w17_0009 nối w12_0008. DTO is_first_admin nullable; lỗi protected_admin/bootstrap_required. DB hiện hữu cần backup, đối chiếu UUID bằng hồ sơ rồi CLI máy chủ một lần; không đoán từ danh sách và không chuyển DB dùng chung trong lượt nghiệm thu.
- W-20 phải từ chối xoá tài khoản admin đầu tiên, kể cả đường tự xoá có mật khẩu. Không thay thủ tục bảo toàn dữ liệu học/sổ chi của các tài khoản khác.
- React dựa vào hợp đồng server để thể hiện tài khoản được bảo vệ, không suy từ hàng đầu bảng hay bộ lọc.
- Test mới theo quyết định này đã RED trên mốc 9cf405ac: test_new_owner_policy_first_admin_cannot_be_disabled, 1 assertion fail/0 setup error. Mốc đó chưa được ghép riêng. Bản sửa a07bff3f đã được nghiệm thu lần12 với các ca bảo vệ đầu tiên/DB delete, admin thêm sau, người thường cũ được nâng, nhiều field/cạnh tranh/rollback và SQL độc lập. CORE-R11-01 bổ sung guard chỉ kiểm khi thực sự giảm admin active, không chặn hạ một admin đã disabled. DELETE API W-20 vẫn chưa triển khai.

Xem [spec chức năng](../web-chuc-nang-spec.md), [W-17](../../task/web/W-17-quan-tri.md), [W-20](../../task/web/W-20-xoa-tai-khoan-xoa-khoa-hoc.md) và [nghiệm thu lần 10](../../report/dieu-phoi-nghiem-thu-ba-nhom-lan10-2026-10-28.md).

**Mốc triển khai:** [nghiệm thu lần12](../../report/dieu-phoi-nghiem-thu-ba-nhom-lan12-2026-10-28.md), source 34c1712f, cổng 3696 Python/259 React/build. Chỉ nhận backend Người dùng/Nhật ký; React và các mốc quản trị sau vẫn mở.
