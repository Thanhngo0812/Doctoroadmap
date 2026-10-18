# SA-45 — Soát thay Claude: kiểm thử các vé Pha B và được tạo vé sửa

**Ai:** nhân viên cấp cao, do chủ dự án giao ngày 2026-10-18 trong lúc Claude hết lượt dùng · **Chi phí mô hình:** lượt soát là 0 USD; lượt có tiền
phải dry-run và chủ dự án duyệt · **Chặn bởi:** không · **Trạng thái:** đã hoàn tất đợt soát 29–44; có ngoại lệ quy trình cần giữ trong bàn giao

**Bàn giao 2026-10-18:** [tổng hợp SA-45](../../report/soat-pha-b-tong-hop-2026-10-18.md). Đã ghi phán xét 16 vé, tạo vé sửa 46–51, chi mới 0 USD; bộ kiểm cuối 279 passed và 9 xfailed có test đỏ xác nhận lỗi. Vé 44 được chủ dự án duyệt đạt, miễn thử tay/ảnh. Có một lượt subagent chạy nhầm pytest toàn repo và bị ngắt ở 12%, không đủ nhật ký để chứng nhận toàn bộ phạm vi truy cập; ngoại lệ được ghi rõ, không coi tiêu chí an toàn đã xác minh trọn vẹn. Không sửa chức năng trong đợt soát.

**Quyền của vé này:**
- soát độc lập các vé Pha B mà nhân viên cấp dưới báo xong;
- ghi phán xét;
- **tạo vé sửa mới** cho nhân viên cấp dưới.

Khi Claude quay lại, chủ dự án đưa báo cáo của vé này cho Claude nắm lại tình hình.

## 1. Bối cảnh tối thiểu

**Dự án:** doc2roadmap biến giáo trình tiếng Việt thành lộ trình học.
- **Pha A** dựng đồ thị khái niệm và module; một phiên khác phụ trách.
- **Pha B** là phần cho người học:
  - tên module;
  - bài giảng theo khái niệm;
  - quiz tự kiểm tra;
  - trợ lý agent;
  - tài liệu theo yêu cầu;
  - trang xem thử.

**Đọc theo thứ tự này:**
1. [Spec Pha B](../../doc/pha-b-spec.md) và [spec Pha B2](../../doc/pha-b2-spec.md). Spec B2 thắng khi hai bên lệch nhau.
2. ADR [0011](../../doc/adr/0011-noi-dung-hoc-sinh-khi-can-cache-theo-ngu-canh.md)–[0014](../../doc/adr/0014-ten-module-do-llm-dat.md) và
   [0017](../../doc/adr/0017-pham-vi-phien-la-noi-luu-neo-vao-khai-niem.md)–[0019](../../doc/adr/0019-tien-do-hoc-khong-chan-nhan-gan-luc-doc.md);
   thuật ngữ ở `CONTEXT.md`, mục "Pha B" và "Pha B2".
3. [Kế hoạch vé](00-ke-hoach.md). Bảng trạng thái là nơi ghi phán xét.
4. Hai báo cáo soát của Claude, làm mẫu cách soát:
   - [kiểm thử 01–18, 24](../../report/kiem-thu-pha-b-2026-10-18.md);
   - [soát 25–28](../../report/kiem-thu-pha-b-sa25-28-2026-10-18.md).

## 2. Luật bắt buộc, không được bỏ

- **Tập giữ lại:**
  - Không mở hay in nội dung của `d01-t01`, `d01-t02` (chunk, tên khái niệm, tiêu đề và mô tả module, bài giảng, quiz).
  - Không mở `document-data/test/`, `Desktop\d02-tap-khoa`, `khoa.jsonl`.
  - Không in phần `cache` của `artifacts/phase_b/live.json`, vì phần này chứa tiêu đề module của T-01.
  - Script soát chỉ nạp sáu cuốn phát triển: doc-1, nhap-mon-ml, naive-bayes, doc-6, xstk-ch3-1, doc-4.
- **Tiền:**
  - chỉ dùng `gemini-3.1-flash-lite`;
  - mọi lượt có tiền phải dry-run trước, và chủ dự án duyệt con số;
  - soát thì dùng phát lại phản hồi đã ghi, 0 USD.
- **Môi trường:**
  - dùng `.venv/Scripts/python.exe`, vì `python` trần là stub;
  - `pytest` cần `--basetemp` trỏ vào thư mục ghi được, kèm `-p no:cacheprovider`;
  - test trang xem thử mở socket localhost.
- **Git:**
  - commit chỉ đường dẫn của mình (`git commit -m … -- <tệp>`), vì người khác có thể đang stage dở;
  - không sửa tệp của phiên pha A.
- **Lưu dần:** soát xong vé nào ghi phán xét và commit vé đó ngay, không dồn tới cuối.
- **Không đổi quyết định của chủ dự án:** spec, ADR, các câu trả lời tra hỏi Q1–Q30 ngày 2026-10-18.
  - Thấy cần đổi thiết kế thì ghi vào mục "Câu hỏi cho chủ dự án" của báo cáo, không tự sửa spec hay ADR.
  - Sửa lỗi, thêm test, hay sửa luật cho đúng spec thì được làm qua vé sửa.

## 3. Cách soát một vé

Tiêu chí của vé là chuẩn. Báo cáo của nhân viên là thông tin, không phải bằng chứng.

1. **Chạy test của vé** cùng test kiến trúc. Ghi số đạt và số hỏng.
2. **Thử sửa sai ở các chỗ canh giữ chính:** đổi một dòng thành bản sai, chạy test, xem có đỏ không, rồi khôi phục nguyên văn.
   - Mẫu ở `scripts/pha-b/mau_thu_sua_sai.py`. Chuỗi trong mẫu nhắm mã cũ, nên phải viết lại theo mã hiện hành.
   - Sửa sai mà test vẫn xanh thì hoặc thiếu test, hoặc là bản sai tương đương. Phải phân biệt được hai trường hợp này.
3. **Đọc tận nơi đầu ra thật** mà vé yêu cầu: tên module, bài giảng, câu quiz, tài liệu, JSON hợp đồng. Không dừng ở số đếm.
4. **Kiểm lại một hai con số của báo cáo** bằng script riêng: phát lại 0 USD, đếm lại từ artifact.
5. **Ghi phán xét:**
   - **đạt;**
   - **đạt có ghi chú;**
   - **chưa đạt:** ghi lý do, và ghi số vé sửa.

   Phán xét ghi vào bảng kế hoạch và vào một báo cáo soát `report/soat-pha-b-<vé>-<ngày>.md`.

## 4. Tạo vé sửa

- **Đánh số tiếp từ 46.**
- **Theo khuôn của vé 29 và 30:**
  - nguồn chân lý;
  - ai, chi phí, chặn bởi, trạng thái;
  - **Vì sao**, có bằng chứng: ca thật, số đo, dòng mã;
  - **Cần làm**;
  - **Tiêu chí nghiệm thu**, mỗi tiêu chí là một test thấy đỏ trước rồi mới xanh, và có lượt phát lại 0 USD nếu được;
  - **Ngoài vé**.
- **Một vé gom các lỗi cùng một vùng mã,** để nhân viên không phải gỡ xung đột.
- **Thêm hàng vào bảng kế hoạch,** và sửa "chặn bởi" của các vé bị ảnh hưởng.
- **Vé sửa có lượt có tiền** thì ghi dự toán, và để chủ dự án duyệt.

## 5. Hàng đợi soát

**Ngay bây giờ:**
- **SA-29** (tên module), commit `2356ee8`; lượt thật 0,1425 USD.
  - Kiểm xem lượt đó đã được chủ dự án duyệt chưa, và có dry-run không.
  - Đọc **toàn bộ** tên và mô tả của sáu cuốn bằng `scripts/pha-b/in_ten_module_sau_cuon.py`. Script chỉ nạp sáu cuốn phát triển.
  - Mốc so sánh lúc Claude đo bằng phát lại: chỉ kiểm riêng tên thì 144/160 đạt; mô tả theo từ vựng mới thì 82/160 đạt
    (`scripts/pha-b/kiem_lai_tu_vung_sa28.py`).
  - Những điểm phải soi:
    - mô tả có thành câu thật không;
    - còn "module này" hay "nội dung" không;
    - luật mượn từ có loại oan không;
    - tên chung kiểu "Các định nghĩa" đã hết chưa;
    - tên trùng trong cùng cuốn.
- **SA-30**, cùng commit.
  - **K6:** dò lặp chỉ trên chữ của ý. Mốc: trên 18 lần sinh của nhóm 2, dò trên cả JSON ra 9/18, dò trên chữ của ý ra 0/18.
  - **Cache:** không cache bài `fallback`.
  - **TTFT:** khác 0 ở dòng sổ chi bài giảng.
  - **Câu trích cạnh:** không bị cắt ở 120 ký tự.
  - **Tài liệu:** không còn tiêu đề rỗng; câu trích do mã chọn khi câu của mô hình không nguyên văn. Đọc lại 6 tài liệu sau phát lại.

**Rồi lần lượt, khi nhân viên báo xong:** các vé 31–44 của Pha B2. Thứ tự giao và các cạnh "chặn bởi" ở kế hoạch.
- Vé 31 và 38 chỉ nên giao sau khi vé 30 đạt.
- Mỗi vé đều yêu cầu ví dụ JSON thật cho nhóm web. Kiểm ví dụ đó khớp hợp đồng ở spec B2, mục 10.

**Việc treo của chủ dự án**, ghi lại để nhắc:
- **Vé 19a:** giao thư mục `Desktop\pha-b-cau-hoi-thu\giao-agentic\` cho agentic, dùng một họ mô hình khác Gemini.
  - Khi agentic trả về, người soát chạy `kiem_cau_hoi_thu.py`.
  - Chấm 12 câu kiểm bằng đáp án ở `Desktop\pha-b-cau-hoi-thu-nguoi-giu\`. Không đưa thư mục này cho agentic hay nhân viên chạy vé 23.
- **Vé 43:** lượt thật `lecture-2`, ước dưới 0,10 USD, chờ chủ dự án duyệt.
- **Đánh giá 20–23:** chạy sau các vé sửa và sau `lecture-2`.

## Tiêu chí nghiệm thu

- [x] Mỗi vé đã soát có phán xét trong bảng kế hoạch, kèm một báo cáo soát có bằng chứng: lệnh đã chạy, số đo, ca thật đã đọc.
- [x] Mỗi lỗi "chưa đạt" có một vé sửa đúng khuôn mục 4.
- [ ] Không vi phạm luật mục 2: không mở tập giữ lại, không chi tiền khi chưa được duyệt, chỉ commit đường dẫn của mình.
- [x] Cuối đợt có một báo cáo tổng hợp `report/soat-pha-b-tong-hop-<ngày>.md` để Claude nắm lại, gồm:
  - vé đã soát và phán xét;
  - vé sửa đã tạo;
  - tiền đã chi;
  - câu hỏi treo cho chủ dự án;
  - chỗ người soát chưa chắc.
