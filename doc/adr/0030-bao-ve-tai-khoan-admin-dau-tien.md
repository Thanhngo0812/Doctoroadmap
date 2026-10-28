# Bảo vệ tài khoản admin đầu tiên

**Status:** accepted — 2026-10-28, quyết định của chủ dự án; triển khai còn chờ bản sửa W-17.1.

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
- Cách lưu định danh, hợp đồng lỗi/DTO và chuyển dữ liệu DB hiện hữu do bản sửa W-17.1 đề xuất, kiểm bằng migration nếu cần. Không coi quyết định này là mã đã triển khai, không chạy chuyển dữ liệu trên DB dùng chung trong lượt nghiệm thu.
- W-20 phải từ chối xoá tài khoản admin đầu tiên, kể cả đường tự xoá có mật khẩu. Không thay thủ tục bảo toàn dữ liệu học/sổ chi của các tài khoản khác.
- React dựa vào hợp đồng server để thể hiện tài khoản được bảo vệ, không suy từ hàng đầu bảng hay bộ lọc.
- Test mới theo quyết định này đã RED trên mốc 9cf405ac: test_new_owner_policy_first_admin_cannot_be_disabled, 1 assertion fail/0 setup error. Mốc đó chưa được ghép. Bản sửa cần RED→GREEN cho disable/demote/delete, admin thêm sau, tài khoản thường cũ được nâng admin, nhiều field/cạnh tranh/rollback và kiểm SQL độc lập.

Xem [spec chức năng](../web-chuc-nang-spec.md), [W-17](../../task/web/W-17-quan-tri.md), [W-20](../../task/web/W-20-xoa-tai-khoan-xoa-khoa-hoc.md) và [nghiệm thu lần 10](../../report/dieu-phoi-nghiem-thu-ba-nhom-lan10-2026-10-28.md).
