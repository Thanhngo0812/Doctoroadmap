# SA-28 — Tên module: mô tả thành câu, khuôn lùi không lộ mã, chặn tên chung

**Nguồn chân lý:** [ADR 0014](../../doc/adr/0014-ten-module-do-llm-dat.md); [spec Pha B](../../doc/pha-b-spec.md), mục 2 (tên và mô tả module);
[báo cáo kiểm thử 2026-10-18](../../report/kiem-thu-pha-b-2026-10-18.md), mục 3.1.
**Ai:** nhân viên · Claude kiểm và đọc lại toàn bộ · **Chi phí mô hình:** chạy lại sáu cuốn, khoảng 0,2–0,3 USD theo lượt nhóm 1, dry-run trước, chủ
dự án duyệt · **Chặn bởi:** nhân viên commit mã Pha B còn dở · **Trạng thái:** đã triển khai và chạy sáu cuốn; nội dung chưa đạt, chờ Claude quyết định

**Bàn giao 2026-10-18:** mã nền đã commit ở `bbcfcc6`; chủ dự án duyệt lượt mới trần 0,50 USD trong tổng 1 USD cho SA-27/28. Đã chạy 160 module, 0,12723425 USD, giữ nguyên nodes/dãy học/cạnh/thành viên module. Mô tả LLM list-only giảm từ 130/152 xuống 0/25, nhưng 135/160 module rơi về khuôn dự phòng (122 do từ vựng); không coi nội dung toàn bộ là đạt. Không tự nới luật hoặc gọi thêm lượt. Xem [báo cáo SA-28](../../report/pha-b-sa28-2026-10-18.md) và [bàn giao tổng hợp](../../report/pha-b-sa25-28-ban-giao-2026-10-18.md). Doc-6 dùng A10 v24 hiện hành sau commit `7fed604`, thay bản v17 ghi lúc lập vé. Các ô nghiệm thu của Claude vẫn để người soát quyết định.

## Vì sao

Claude đọc 162 module trên đồ thị hiện hành ngày 2026-10-18. Tên đạt, nhưng có bốn lỗi:
- **Mô tả LLM chỉ là danh sách tên khái niệm** ở 132/154 module, ví dụ "Phụ thuộc hàm, Dạng chuẩn.".
  - Trang lộ trình đã hiện danh sách khái niệm, nên mô tả kiểu này không thêm gì.
  - Nguyên nhân là prompt bảo "chỉ liệt kê tên khái niệm nguyên vẹn".
  - Mô tả A5 vốn đã nằm trong từ vựng được phép. 22 mô tả còn lại viết được câu thật, ví dụ "Độ chính xác trong ước lượng tỉ lệ là đại lượng đo lường
    sai số ε của ước lượng tỉ lệ p."
- **Khuôn mô tả của đường lùi lộ mã kỹ thuật:** "Cần trước: module_015, module_023." ở 6 module.
- **Tên chung, không nói nội dung:** "Các định nghĩa" (doc-1, module dạy trị riêng), "Tư tưởng triết học" (doc-4, module dạy Đạo, Vô vi).
- **Trùng tên trong cùng cuốn:** nhap-mon-ml module 9 và 13 cùng "Vài vấn đề cần biết khi dùng học máy", cách nhau 4 nên luật ±2 không bắt. Ngoài ra
  có một tên viết thường chữ đầu.

## Cần làm

**1. Mô tả thành câu.**
- Prompt bỏ chỉ dẫn "chỉ liệt kê". Yêu cầu 1–2 câu nói module dạy gì và để làm gì, dựng từ mô tả A5 của các khái niệm.
  - Vẫn giữ năm luật kiểm.
  - Vẫn không lời dẫn sáo rỗng ("tìm hiểu", "nắm vững") nếu các từ đó không có trong từ vựng.
- `format_example` đổi thành một câu dựng từ mô tả A5 của khái niệm đầu module, thay cho danh sách tên.
- **Đo trước và sau trên cùng sáu cuốn:**
  - tỉ lệ mô tả chỉ là danh sách tên. Cách đo như script của báo cáo kiểm thử: mọi mảnh tách theo dấu phẩy và "và" đều là tên khái niệm;
  - tỉ lệ rơi đường lùi theo từng luật.

  Nếu luật từ vựng làm rơi đường lùi nhiều lên rõ, báo Claude kèm mẫu; không tự nới luật.

**2. Khuôn lùi không lộ mã.** "Cần trước: <tên module> (module n)", với n là số thứ tự hiển thị, đúng như spec. Không mô tả nào chứa `module_` hay
`node_`.

**3. Chặn tên chung.**
- Tên LLM phải chứa ít nhất một âm tiết nội dung có trong `display_name` hay alias của các khái niệm trong module.
- Âm tiết chức năng tính theo tần suất trong cuốn, như luật từ vựng.
- Hỏng thì đi đường lùi, cờ `generic_title`.

**4. Trùng tên trong cả cuốn.**
- Hai module trùng tên sau chuẩn hoá, ở bất kỳ khoảng cách nào:
  - nếu cùng `section_code`, module sau thêm hậu tố " (tiếp)";
  - nếu khác, module sau đi đường lùi, cờ `duplicate`.
- Luật ±2 trong prompt giữ nguyên.

**5. Viết hoa chữ đầu tên** nếu tên bắt đầu bằng chữ thường. Không đổi tên riêng hay ký hiệu ở giữa tên.

**6. Chạy lại** trên đồ thị A10 hiện hành của sáu cuốn: doc-1 v53, nhap-mon-ml v46, naive-bayes v45, doc-6 v17, xstk-ch3-1 v64, doc-4 v23. Dry-run
trước, chủ dự án duyệt. Khâu tên chỉ ghi một phiên bản đồ thị mới, không đổi dãy học, thành viên module hay cạnh.

## Tiêu chí nghiệm thu

- [ ] Test với mô hình giả, mỗi cái thấy đỏ trên mã hiện tại rồi mới xanh:
  - module có phụ thuộc rơi đường lùi thì mô tả không chứa `module_`, và có số thứ tự module;
  - tên "Các định nghĩa" cho module không có khái niệm nào chứa âm tiết "định nghĩa" thì bị loại, cờ `generic_title`;
  - hai module cách nhau 4, cùng tên, cùng `section_code` thì module sau có " (tiếp)";
  - tên bắt đầu bằng chữ thường được viết hoa;
  - prompt không còn chữ "chỉ liệt kê", và `format_example` là một câu có động từ.
- [ ] Dry-run sáu cuốn: số lời gọi và USD ước. Chạy thật sau khi duyệt. Báo cho từng cuốn:
  - số tên LLM và số đường lùi theo từng luật;
  - tỉ lệ mô tả chỉ là danh sách, trước và sau;
  - USD và phút.
- [ ] Ngoài tên và mô tả, artifact không đổi gì (so như vé 05).
- [ ] Claude đọc lại toàn bộ tên và mô tả của sáu cuốn, ghi phán xét vào vé.

## Ngoài vé

Hai việc không thuộc vé này: đổi thành viên module hay thứ tự (A10), và đánh giá tên bằng người chấm (vé 20, chạy sau vé này).
