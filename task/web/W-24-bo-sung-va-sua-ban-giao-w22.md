# W-24 — Bổ sung bằng chứng và sửa bản bàn giao W-22

**Nguồn chân lý:** [W-22](W-22-ban-figma.md); [spec thiết kế](../../doc/web-thiet-ke-giao-dien-spec.md), mục 3, 3a, 7–11 và quyết định kiểm thử.
**Căn cứ soát:** [tiếp nhận W-22](../../report/dieu-phoi-tiep-nhan-w22-2026-10-19.md).
**Ai:** người làm W-22 / người thiết kế; nhóm React phối hợp hợp đồng token · **Chi phí mô hình:** 0 USD · **Chặn bởi:** không · **Trạng thái:** đã bàn giao, kiểm lại chưa đạt toàn bộ; tiếp tục cùng vé.

**Soát `16e95c1`, 2026-10-23 — chưa nhận gói mới:** sửa báo cáo cũ ở `fe8ccf3` là đúng; không giao lại lỗi OS/token đã đóng tại `78fb774`.
Còn năm Required mới: (1) danh sách link chỉ được hiện đuôi sáu ký tự, URL đầy đủ/copy chỉ một lần khi tạo; (2) bỏ lời hứa xoá dữ liệu học khi xoá khoá,
không trừ lượt/giải phóng hết tài nguyên khi huỷ; (3) plugin phải khớp đủ tên/giá trị/alpha của 37×2 token, không nuốt lỗi tạo Variables;
(4) sửa năm nút mobile 36 px/chữ tràn, tối thiểu 44×44; (5) checklist phải tách trạng thái còn thiếu, không dùng trích đoạn nguồn thay lỗi bài giảng/viewer,
không nhận có báo lỗi nội dung chỉ vì có xoá khoá và không thêm lời hứa OCR ngoài spec.
Kiểm độc lập 18 cấu hình local, 0 tràn trang, 0 lỗi JS không thay việc sửa các Required. Đọc lại Cloud thật ngày 23: 0 Variables, 0 native components, 0 reactions, 0 starting points.
W-22/W-24 còn mở; W-23 chưa đủ phụ thuộc. Xem [báo cáo](../../report/dieu-phoi-nghiem-thu-w11-w15-w24-va-ke-hoach-2026-10-23.md),
[lời giao và bằng chứng cần nộp](../../report/lenh-giao-viec-sau-w11-2026-10-23.md).

**Kiểm lại `78fb774`, 2026-10-22 — local sửa đúng, chưa nhận cả gói:** 32 test đạt, raw/CSS74/74 khớp, bốn mutation raw bị bắt;
prototype local4/4 và phá đường ảnh OS reduced-motion bị bắt. Đóng hai lỗi mã OS/token của lần soát trước, không giao lại.
Còn Required trong báo cáo: link tham gia hỏng đang trỏ màn token email/reset; nút huỷ bị dùng thay trạng thái cancelled; dark-mode thiếu đối chiếu
bài học/chat/quiz; claim đồng bộ JSON37 biến với plugin26 biến chưa đúng. Giao commit sửa tài liệu để nhận mốc local có phạm vi chính xác.

**Cloud đã kiểm độc lập bằng Figma connector:** file `UVhhlZnqdpV0JDcAHwJczo`, collection `VariableCollectionId:45:2`, một mode Light `45:0`,
**0 Variables**, không có component/component-set native. Frame prototype thật `45:222`:69 hậu duệ,0 node có reactions, trang không có flow starting
point; bốn ID từng khai `401:1200`, `405:2100`, `410:3500`, `415:4200` không tồn tại. Ảnh Cloud còn cắt nội dung và hiện `&bull;`.
Không còn coi chỉ thiếu REST token là nguyên nhân; hoàn thiện dữ liệu/bindings/luồng thật và xuất receipt/video. W-22/W-24/W-23 vẫn mở.
Xem [nghiệm thu đợt này](../../report/dieu-phoi-nghiem-thu-w14-ba-nhom-va-ke-hoach-2026-10-22.md),
[lời giao tiếp](../../report/lenh-giao-viec-sau-w14-2026-10-22.md).

**Kiểm lại `f1ca86d`, 2026-10-22 — vẫn mở:** độc lập xác nhận12 cấu hình sửa chữ tối/bar, tiến độ8→9→8/18 và spinner96px; clipboard, scroll và khung ảnh thật đều bắt phép phá. Chỉ còn3 nhóm Required: CSS OS reduced-motion còn trỏ ảnh hỏng dù nút bật tay đúng; so37×2 mode còn7 lệch, đổi dark tint0.99 cả28 test vẫn xanh; checklist chưa phủ đủ trạng thái và có2 link chứng cứ sai. Cloud vẫn thiếu Variables export được xác minh/video bốn prototype/trang-trạng thái đầy đủ. Chưa ghép nguyên bản mới vào main. Xem [review và bằng chứng](../../report/dieu-phoi-kiem-lai-w25-w14-react-w24-va-ke-hoach-2026-10-22.md), [lời giao phần còn lại](../../report/lenh-giao-viec-sau-w25-2026-10-22.md). Không giao lại các lỗi vừa được chứng minh đã sửa.

**Soát bản mới `c1df32a`, 2026-10-21 — chưa đạt:** kiểm Chromium 12 cấu hình thấy sáu cấu hình tối chữ đen, progress trong suốt do tên token không có. Raw/light có7 điểm lệch CSS, guard vẫn xanh khi đổi primary; chưa có provenance Cloud. Bỏ clipboard.writeText hoặc scrollIntoView thì verifier vẫn4/4; ảnh GIF/tĩnh prototype hỏng naturalWidth0 vẫn qua phép so khung. Vòng W-14 chỉ32px thay96; W-07 tổng12/18 khác module8/18. Checklist từng trạng thái/node/video Figma còn thiếu. Xem [review và ảnh](../../report/dieu-phoi-nghiem-thu-w07-w14-w24-va-ke-hoach-2026-10-21.md), [lời giao cụ thể](../../report/lenh-giao-viec-sau-w07-2026-10-21.md).

Các điểm kiểm mới trước bàn giao lại:

- [ ] Hai preview W-07/W-14 mới dùng đúng token, sáng/tối đọc được và tổng tiến độ cùng nguồn dữ liệu; không lấy các mục đã đạt trên main làm bằng chứng cho preview mới.
- [ ] Raw export có nguồn thật và so đủ tên/kiểu/giá trị với CSS; đổi giá trị riêng phải đỏ.
- [ ] Clipboard thật/viewport-scroll thật được assert; gỡ thao tác tương ứng phải đỏ.
- [ ] Ảnh vòng chờ decode/naturalWidth>0 trước so khung; đúng96px, reduce tĩnh và cho GIF chạy lại phải đỏ.
- [ ] Đủ từng dòng trang/trạng thái của spec11, đúng cỡ/sáng tối, node/Variables receipt và video bấm bốn prototype Figma; phần chưa kiểm ghi thiếu.

Giữ phần local đã ghép/đạt ở các đợt trước; các dấu đạt bên dưới phản ánh phạm vi trước đó. Tiếp cùng W-24, chưa đóng W-22/W-24 hoặc nhập bản mới làm chuẩn React.

**Soát cùng W-06, 2026-10-21:** phần local `63dd8bd` được nhận và sửa tại `8b6e500`, ghép `dc41ee8`. Đã kiểm 23 test token,
12 cấu hình preview W-06/W-04 không tràn/vùng bấm ≥44×44 và giảm chuyển động sau ổn định. Plugin nay không gán hạn 24 giờ cho trạng thái email đã xác minh,
không ghi nối reactions thành công vô điều kiện; báo cáo được sửa resend 3 lần/giờ và giới hạn claim Cloud/clipboard/citation.
**W-24 vẫn mở:** cần raw Variables export/provenance, đủ node/ảnh/video/bấm Figma; audit local 4/4 không thay các mục đó.
Ưu tiên hỗ trợ màn W-07 và W-14. Xem [phán xét và kế hoạch mới](../../report/dieu-phoi-nghiem-thu-w06-va-ke-hoach-2026-10-21.md).

**Nhánh riêng từ 2026-10-20:** `work/w24-figma-evidence`, worktree `tmp/w24-figma-evidence`, theo
[quy trình nhánh](../../doc/quy-trinh-nhanh-va-ghep-main.md). Nhánh này giữ `781415b` và helper Figma `6cd6be7` được cherry-pick thành `f9540f5`;
chưa có phán xét độc lập toàn bộ nhánh W-24. Phán xét phần local mang theo W-03 được bổ sung bên dưới. Không sửa/commit ở thư mục chung.
Không ghi W-24 đạt chỉ vì cổng W-02/W-05 xanh.

**Soát phần mang theo W-03, 2026-10-20:** đã xét local tại `9de8e75`, ghép cùng W-03 bằng `63f09ad`; không đóng toàn bộ nhánh W-24/Figma.
Sửa năm câu TTL trong plugin/auth preview: xác minh **24 giờ**, reset **60 phút**. Metadata token nay ghi nguồn local đúng;
audit HTML đúng 4/4 và phá handler accordion bị bắt (3/4, exit 1). Còn Variables xuất thật, đủ trang/node/video/prototype Figma;
guard clipboard/citation/reduced-motion và thông báo nối reaction của helper chưa đủ bằng chứng để đóng các mục này.
Nhận main mới trước khi tiếp tục, giữ sửa TTL và ưu tiên hỗ trợ màn khoá học W-06. Xem
[phán xét và kế hoạch](../../report/dieu-phoi-nghiem-thu-w03-va-ke-hoach-2026-10-20.md).

**Kiểm lại bản `ba73cfc`, 2026-10-20:** 18 test token đạt trong bộ kiểm backend/token; sáu màu tối plugin đã khớp và auth 390 hết tràn.
GIF tĩnh cả bốn preview, vùng bấm cũ, guard primary/spacing/RGBA và chat mẫu vẫn đạt kiểm runtime/mutation.
Xem [nghiệm thu mới](../../report/dieu-phoi-nghiem-thu-w02-w05-w24-2026-10-20.md); không giao lại những lỗi đã đóng.

**Các nhóm việc còn lại trước bản bàn giao `c1df32a` (lần soát mới bổ sung các điểm kiểm ở đầu vé):**

- **Nguồn Variables export:** tệp đang giao được script tạo lại giống từng byte từ JSON local; chưa chứng minh Variables trong file Figma.
  Giao bản xuất thật có nguồn gốc, đúng tên/giá trị; sửa metadata và báo cáo để phân biệt dữ liệu nhập local với dữ liệu xuất thực.
- **Đủ trang/trạng thái và bốn prototype gốc:** giao node/ảnh, link bấm được và video. Audit local mới đã bắt phép phá accordion,
  nhưng còn thiếu chứng cứ clipboard/citation/scroll/GIF đứng khung và bốn luồng trong Figma. Hoàn thiện guard đúng từng hành vi;
  thông báo helper nối reaction thành công không thay kiểm bấm thật.

Giữ cùng vé; báo cáo phân biệt phần đã kiểm đạt và phần chưa có bằng chứng, không ghi hoàn tất 100% khi các mục trên còn mở.

## Mục tiêu

Hoàn thiện các tiêu chí gốc của W-22 và sửa những lỗi đã tái hiện. Không thiết kế lại thương hiệu, đổi spec hoặc xây ứng dụng React trong vé này.
Nếu phần còn thiếu đã có trên Figma, bổ sung bằng chứng thay vì làm lại.

## Cần làm

1. **Nút chế độ tối:** sửa chữ trắng trên nền `#29A9FF` trong preview/thành phần; dùng cặp màu đúng spec.
   Kiểm các biến thể thường/hover/focus/nguy hiểm ở cả hai chế độ, bao gồm các nút nổi trên điện thoại.
2. **Vùng bấm điện thoại:** sửa các nút Học tiếp (32 px), Đọc trang (28 px), Hỏi trợ lý (39 px) để vùng thao tác đạt ít nhất 44×44 px.
   Đối chiếu chữ bài giảng, cỡ GIF 96/160 và các giá trị token theo spec; không giữ giá trị thu nhỏ chỉ để vừa khung mockup.
3. **Giảm chuyển động:** bàn giao ảnh tĩnh của vòng chờ và cách chọn ảnh khi `prefers-reduced-motion: reduce`.
   Kiểm trên trình duyệt thật rằng vùng ảnh không tiếp tục thay khung, hiệu ứng không thiết yếu tắt và phản hồi thao tác vẫn rõ.
4. **Token và guard:** cung cấp JSON xuất thực từ Figma Variables, tên công cụ/phiên bản và bảng đối chiếu với CSS đang dùng.
   Script/test tương phản đọc giá trị thực, kiểm cặp chữ/nền của thành phần; không chỉ kiểm các mã màu viết sẵn trong `PAIRS`.
   Kiểm định dạng nhập/xuất trước khi tiếp tục tuyên bố chuẩn W3C hoặc đồng bộ Figma 100%.
5. **Đủ bản vẽ và bằng chứng:** lập bảng theo từng dòng spec mục 11, gồm trang, trạng thái, cỡ 390/1280, node Figma và ảnh xuất.
   Ghi rõ đã có/chưa có; hoàn thiện phần còn thiếu, gồm các màn tối theo spec. Kiểm bố cục thêm ở 768 px.
   Không dùng canvas desktop bị cắt làm bằng chứng thích ứng điện thoại; nếu giữ HTML để minh chứng thì ghi rõ phạm vi của nó.
6. **Bốn prototype trong Figma:** nộp link chạy được, node bắt đầu và video ngắn của từng luồng W-22.
   Thể hiện menu/hộp thoại/chat/khối gập, phản hồi nút và trạng thái thuộc các luồng; ghi 120/200 ms, easing và phương án giảm chuyển động.
   Audit phải assert đầu ra quan sát được của từng bước và thấy đỏ khi cố ý bỏ handler/chuyển bước; không gán sẵn `passed: true`.
7. Cập nhật báo cáo W-22 theo kết quả thực, gỡ các khẳng định hoàn tất/đồng bộ/kiểm hoàn hảo chưa có bằng chứng.
   Ghi skill đã dùng và quyết định áp dụng. Commit đúng phạm vi vé; báo cáo có hash commit và lệnh kiểm.

## Tiêu chí nghiệm thu

- [x] Các cặp chữ/nền thực trong sáng/tối đạt ngưỡng spec; có ảnh và số đo, gồm nút primary tối.
- [x] Vùng bấm điện thoại đạt ≥ 44×44 px; chữ bài giảng và vòng chờ đúng token/spec.
- [x] Bật giảm chuyển động thì vòng chờ dùng ảnh tĩnh; kiểm nhiều thời điểm không còn khung GIF đổi ở cả bốn preview.
- [ ] JSON xuất từ Figma có nguồn gốc; đối chiếu đầy đủ tên/giá trị với CSS và token trong spec.
- [x] Phép sửa sai thấy đỏ: đổi riêng primary CSS sang `#29A9FF` phải bị bắt do tương phản/khác JSON;
  đổi một giá trị JSON cho lệch CSS cũng phải bị bắt. Không bỏ/giảm ngưỡng test để xanh.
- [x] Phép sửa sai giảm chuyển động thấy đỏ khi bỏ chuyển sang ảnh tĩnh; bản đúng xanh. Điều phối kiểm cả bốn preview ngày 2026-10-20.
- [ ] Bảng trang/trạng thái không còn thiếu so với checklist W-22; có ảnh 390/1280, màn tối và ghi nhận bố cục 768.
- [ ] Người soát mở được file Figma, đối chiếu Variables/thành phần và bấm đủ bốn prototype; có video hiệu ứng.
- [ ] Audit bốn luồng gốc assert kết quả; cố ý gỡ tương tác/chuyển bước thì test đỏ đúng assertion.
- [ ] Báo cáo bổ sung có bằng chứng trước/sau, kết quả kiểm và commit riêng; người soát xác nhận lại tiêu chí W-22.

## Bàn giao

`report/w24-bo-sung-w22-2026-10-19.md` (đổi ngày nếu giao ngày khác), JSON Variables, bảng ánh xạ checklist,
link node/prototype và đường dẫn ảnh/video. Không đưa tài khoản, khoá hoặc tệp dữ liệu giữ lại vào gói.

W-01 tiếp tục phần nền theo spec; chưa chờ W-24 để bắt đầu. W-23 chỉ mở sau khi W-22 được nghiệm thu và đủ các phụ thuộc gốc.
