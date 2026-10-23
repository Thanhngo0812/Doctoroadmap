# Sau A10 — Pha B: kế hoạch vé

**Nguồn chân lý:**
- [spec Pha B](../../doc/pha-b-spec.md), cùng ADR [0011](../../doc/adr/0011-noi-dung-hoc-sinh-khi-can-cache-theo-ngu-canh.md),
  [0012](../../doc/adr/0012-tro-ly-la-agent-goi-cong-cu.md), [0013](../../doc/adr/0013-lop-gan-module-va-media-da-xac-nhan.md) và
  [0014](../../doc/adr/0014-ten-module-do-llm-dat.md);
- bốn báo cáo nghiên cứu ngày 2026-10-11, dẫn trong spec.

**Quy trình:** Claude soạn vé, chủ dự án giao, nhân viên cài, Claude kiểm theo tiêu chí của vé. Vé 19 do Claude làm. Vé 20–23 do nhân viên
chạy, nhóm chấm, Claude phân tích.

## Điều kiện trước khi bắt đầu

Ba điều kiện áp cho mọi vé:
- **Phần `src` đang sửa dở phải được commit trước.** Ngày 2026-10-11 có năm tệp chưa commit: bộ điều phối, CLI, adapter Gemini cho LLM và
  embedding, khâu trích A3. Nhiều vé chạm đúng các tệp này, nên chưa commit thì chưa bắt đầu.
- **Không dùng tập giữ lại:** T-01 (`d01-t01`, `d01-t02`) và tập khoá D-02. Dữ liệu là sáu cuốn phát triển: doc-1, nhap-mon-ml, naive-bayes,
  doc-6, xstk-ch3-1, doc-4.
- **Lượt có tiền:** dry-run trước; chạy thật chỉ khi chủ dự án duyệt; trần chung của các lượt thử đầu là 16 USD.

## Phối hợp với việc ở Pha A

Hai việc ở Pha A ảnh hưởng tới các vé ở đây:
- **Vé v4-17, gộp khâu trước A8** ([spec](../../doc/gop-khau-truoc-a8-spec.md), phiên pass phụ, chỉ triển khai sau khi vòng 2 đo xong trên T-01):
  - Chuỗi mới vẫn ghi lên node các trường mà Pha B đọc (`anchor`, `teaching_status`, `teaching_chunk_ids`) và vẫn kết thúc ở A10 rồi khâu tên.
  - Nhưng chuỗi mới không còn `identity_map`. Vì vậy **mọi vé ở đây không được dựa vào `identity_map`**; "danh tính đã gộp" đọc từ alias của node.
  - Vé 05, 06 sửa khâu tên, còn v4-17 sửa phần lắp chuỗi trước A8. Ai làm sau thì rebase lên bản của bên kia; hai phiên không sửa tệp vé của nhau.
- **Vé v4-16, bộ đọc nhẹ:** đầu ra công thức và cây mục ảnh hưởng vé 04 (ảnh công thức) và vé 05, 06 (tên module). Vé 04 chỉ báo lại, không sửa A1.

## Luật chung của mọi vé

Bốn luật:
- **Test thấy đỏ trước** trên phiên bản sai rồi mới xanh (AGENTS.md mục 5). Đường nối là use case với mô hình giả theo kịch bản, embedding giả và
  kho lưu trữ trong bộ nhớ (spec, "Quyết định kiểm thử"). Lệnh CLI chỉ có test nối dây.
- **Số đo là thông tin, không phải cổng dừng.** Mỗi vé báo:
  - phút/cuốn hoặc giây chờ, USD/cuốn hoặc USD/thao tác, đo trước và sau;
  - số đo chất lượng của vé.

  Claude đọc rồi quyết. Chỉ trần chi và `--dry-run` là bắt buộc.
- **Commit chỉ đường dẫn của vé.** Phiên khác và nhân viên khác có thể đang stage dở. Nhánh, worktree và ghép vào main theo
  [quy trình nhánh và ghép main](../../doc/quy-trinh-nhanh-va-ghep-main.md).
- **Kiểm kiến trúc:** application không import infrastructure; domain chỉ dùng thư viện chuẩn.

## Vé

**Cập nhật 2026-10-15 (nhân viên):** vé 01–18 và 24 đã cài và chạy các lượt thử được duyệt. Xem [bàn giao](../../report/pha-b-ban-giao-2026-10-15.md).

**Cập nhật 2026-10-18 (Claude kiểm):** xem [báo cáo kiểm thử](../../report/kiem-thu-pha-b-2026-10-18.md).
- Hạ tầng đạt.
- Nội dung chưa đạt ở bốn nhóm, mỗi nhóm một vé sửa 25–28.
- Lượt thật của vé 08, 10, 13, 16 còn thiếu; chạy sau vé sửa tương ứng.
- **Điều kiện trước của 25–28:** nhân viên commit phần mã Pha B chưa commit (trợ lý, quiz, tài liệu, chỉ mục khái niệm, ảnh công thức, bộ lắp, adapter,
  CLI, trang xem thử, test).

**Cập nhật 2026-10-18 (Codex triển khai):** điều kiện commit đã xong ở `bbcfcc6`. SA-25/26 đã sửa và phát lại 0 USD; SA-27 đã đo V1–V4 và chạy thật hai module (0,0782415 USD). SA-28 đã chạy 160 module trên sáu A10 (0,12723425 USD), nhưng 135 module dùng khuôn dự phòng nên nội dung toàn bộ chưa đạt. Chủ dự án duyệt SA-27/28 trần 0,50 USD mỗi lượt, tổng 1 USD; chi thực tế theo token 0,20547575 USD. Bộ kiểm ghép cuối có 169 test xanh. Xem [bàn giao SA-25–28](../../report/pha-b-sa25-28-ban-giao-2026-10-18.md); các phán xét nội dung của Claude vẫn chờ soát độc lập.

| vé | việc | chặn bởi | tiền mô hình | trạng thái |
|---|---|---|---|---|
| [01](01-nen-pha-b-kho-so-chi-gioi-han.md) | Nền Pha B: kho lưu trữ, sổ chi, giới hạn dùng chung | — | 0 | đạt; giá viết cứng sửa ở 25 |
| [02](02-do-thi-hoc-nhan-nguon-cong-cu-tra-cuu.md) | Đồ thị học: mô hình đọc, nhãn nguồn, công cụ tra đồ thị | — | 0 | đạt: M2 có test từ SA-25 (`test_traverse_never_leaks_distinct_open_requires_edge`); số tên phổ biến (ngưỡng 0,25) đo 2026-10-22: doc-1 3/223, nhap-mon-ml 5/75, naive-bayes 0/33, doc-6 3/11, xstk-ch3-1 4/82, doc-4 7/495 [soát 2026-10-22](../../report/soat-pha-b-46-47-49-50-51-2026-10-22.md) |
| [03](03-a12-lop-gan-module-truy-hoi-uu-tien.md) | A12: lớp gán module, truy hồi ưu tiên module, `search_document` | — | 0 (embedding truy vấn khi thử) | đạt; thiếu giây/truy vấn doc-4 |
| [04](04-anh-cong-thuc.md) | Ảnh công thức | — | 0 | đạt |
| [05](05-ten-module-luat-tat-dinh-duong-lui.md) | Tên module: luật tất định, đường lùi, mô tả khuôn | — | 0 | đạt qua SA-28 → SA-29: khuôn lùi không lộ mã; chất lượng tên đánh giá ở SA-20 |
| [06](06-ten-mo-ta-module-do-llm-dat.md) | Tên và mô tả module do LLM đặt | 05 | dưới 0,1 USD sáu cuốn | đạt qua SA-28 → SA-29 (đạt có ghi chú); chất lượng tên và mô tả đánh giá ở SA-20 |
| [07](07-chi-muc-khai-niem.md) | Chỉ mục khái niệm | 01, 02 | dưới 0,01 USD | đạt |
| [08](08-tro-ly-agent-lat-cat-dau.md) | Trợ lý agent, lát cắt đầu: port gọi công cụ, vòng lặp có trần | 01, 02, 03 | lượt nhỏ | đạt: lượt thật trong SA-55 (`ee79cae`), USD mỗi câu trung bình 0,0011; TTFT p50 15,8 s, phần lớn chờ trước lời gọi mô hình → **59** [báo cáo SA-55](../../report/pha-b-sa55-2026-10-22.md) |
| [09](09-tro-ly-trich-dan-tu-choi-ngoai-tai-lieu.md) | Trợ lý: trích dẫn, từ chối, nội dung ngoài tài liệu | 08 | 0 (phát lại) | đạt qua SA-25: hậu kiểm theo câu, nhãn bịa và câu không nguồn có test (mutation M5′, M5b′ bị bắt) [soát 2026-10-22](../../report/soat-pha-b-46-47-49-50-51-2026-10-22.md) |
| [10](10-tro-ly-du-cong-cu-nhac-nen-hoi-thoai.md) | Trợ lý: đủ công cụ, nhắc khái niệm nền, hội thoại nhiều lượt | 09 | lượt nhỏ | đạt: lượt thật trong SA-55, gọi công cụ sai 0/3; nhiều lượt và nhắc nền chạy đúng [báo cáo SA-55](../../report/pha-b-sa55-2026-10-22.md) |
| [11](11-bai-giang-khong-llm.md) | Bài giảng không LLM: khung do mã dựng và trích câu | 02 | 0 | đạt qua SA-26 và SA-30 (câu trích cụt) |
| [12](12-bai-giang-llm-kiem-va-cache.md) | Bài giảng LLM có kiểm và cache | 01, 11 | lượt nhỏ | đạt qua SA-26 và SA-30 (K6, không cache bài hỏng); bản lùi bỏ theo chủ dự án 2026-10-18; K5 chưa có test → **54** [soát 2026-10-22](../../report/soat-pha-b-46-47-49-50-51-2026-10-22.md) |
| [13](13-bai-giang-stream-tai-truoc.md) | Bài giảng stream và tải trước | 12 | lượt nhỏ | **đạt** 2026-10-23 qua SA-21 (Vertex, stream, tuần tự, kho rỗng, n=34): tới `skeleton` p50 0,015 s; tới ý đầu p50 2,03 s, p90 4,87 s; tới `final` p50 3,03 s, p90 6,65 s |
| [14](14-cong-cu-get-lecture.md) | Công cụ `get_lecture` | 08, 12 | 0 | đạt |
| [15](15-quiz-dien-khuyet-dau-cuoi.md) | Quiz điền khuyết đầu-cuối | 01, 02 | 0 | đạt |
| [16](16-quiz-llm-theo-khai-niem.md) | Quiz LLM theo khái niệm | 15 | lượt nhỏ | đạt qua SA-27; chất lượng câu đánh giá ở SA-22 |
| [17](17-cong-cu-make-quiz.md) | Công cụ `make_quiz` | 08, 16 | 0 (dùng ngân hàng) | đạt |
| [18](18-tai-lieu-theo-yeu-cau.md) | Tài liệu theo yêu cầu (`make_document`) | 09, 12 | lượt nhỏ | đạt qua SA-25 và SA-30 (tài liệu sau hậu kiểm) |
| [19](19-dac-ta-bo-cau-hoi-thu.md) | Đặc tả bộ câu hỏi thử cho trợ lý (**Claude**) | — | 0 | chủ dự án duyệt 19a; gói và câu kiểm đã xuất 2026-10-18; gói đã về (câu 18/10, câu kiểm 21/10). Claude kiểm 2026-10-23: script ĐẠT cả 6 cuốn, 200/200 câu, 0 cảnh báo; câu kiểm 12/12 (chặt 10/12), giữ mẫu duyệt 40. 5 cuốn khớp 100% graph ghim; **doc-1 lệch** vì dựng lại 20/10 (mã khái niệm 0/72, mã đoạn 0/47, `module_dang_mo` cùng mã khác module). Chủ dự án chọn cho agentic soạn lại doc-1: gói mới từ v8 ở `Desktop\pha-b-cau-hoi-thu\giao-agentic-doc1-v8\` (đọc `LAM-LAI-DOC-1.md` trước), câu kiểm mới k03/k04, đáp án ở thư mục người giữ (`khoa-kiem-doc1-v8.jsonl`); script kiểm đã thử chặn bài doc-1 cũ (121 lỗi). **Chờ chủ dự án giao và agentic trả** |
| [20](20-danh-gia-ten-module.md) | Đánh giá tên module | 06, **28**, **29** | dưới 1 USD | **chờ người chấm**: phiếu đã xuất (`a18713c`, [báo cáo](../../report/danh-gia-sa20-2026-10-22.md)), chi thật 0,22 USD. Gói gửi người chấm ở `Desktop\danh-gia-pha-b\sa20-giao-nguoi-cham\`; khoá và dữ liệu chạy ở `artifacts/phase_b/eval/sa20/`. Độ đo tự động: L1 rơi đường lùi 13,6% (> 10%) và mượn từ 1,85% (> 1%), cần đọc từng ca khi phân tích |
| [21](21-danh-gia-bai-giang.md) | Đánh giá bài giảng | 04, 12, **26**, **30**, **53** | trần 5 USD | **bỏ phần chấm người** (chủ dự án 2026-10-23: "bỏ luôn"; bài `lecture-2` được thay bằng `lecture-3`, SA-64). Gói đã chuyển sang `Desktop/danh-gia-pha-b/_khong-giao/`, không giao. Số máy giữ làm mốc. Trước đó: ghép `81f78e3`, [báo cáo](../../report/danh-gia-sa21-2026-10-23.md), chi 0,51 USD. Phần 1: 48 khái niệm, 169 bản; phần 2: 99 ý A2 (giao **sau khi** nộp phần 1). Gói ở `Desktop/danh-gia-pha-b/sa21-giao-nguoi-cham/`; khoá và dữ liệu chạy ở `artifacts/phase_b/eval/sa21/`. Nghiệm thu sửa: A2 tính theo lần bấm đầu (người chạy đã sinh lại một bài hỏng). Số máy: A2 hỏng hẳn **16/50 (32%)**, A4 (t=1,0) 14%; lặp ý A2 8,1%, vượt luật 2%; A3 (ảnh công thức) hỏng 62%. Từ ADR 0024 (2026-10-23), "hỏng hẳn" đọc là "trượt kiểm": bài vẫn hiện cho người học, nên sau khi cài cần lượt nhỏ chấm các bài trượt kiểm |
| [22](22-danh-gia-quiz.md) | Đánh giá quiz | 16, **27**, **52** | khoảng 1,7 USD | **chờ người chấm**: phiếu 254 câu (113 điền khuyết, 92 LLM qua kiểm, 49 LLM bị kiểm loại), ghép `2eaedab`, [báo cáo](../../report/danh-gia-sa22-2026-10-23.md), chi 1,20 USD. Gói ở `Desktop/danh-gia-pha-b/sa22-giao-nguoi-cham/`; khoá ở `artifacts/phase_b/eval/sa22/`. Ghi nhận: Q5 loại 58% câu LLM; độ phủ LLM 43,8%; lời gọi kiểm có lúc bị cắt ở trần 400 token |
| [23](23-danh-gia-tro-ly.md) | Đánh giá trợ lý: 4 cấu hình, RAGAS | 07, 10, 19, **25**, **30**, **52**, **56** | lượt 1 trần khoảng 8 USD | SA-56 đã ghép; gói 19a đã về và đạt kiểm. Chờ: xử lý 42 câu doc-1 lệch graph ghim, duyệt người 40 câu, chia dev/test; vé đã cập nhật theo graph ghim 2026-10-22 |
| [24](24-trang-xem-thu-pha-b.md) | Trang xem thử Pha B trên máy cục bộ (chủ dự án yêu cầu 2026-10-15) | 06, 10, 13, 16 | 0 khi phát lại; có tiền khi bật `--allow-spend` | đạt |
| [25](25-hau-kiem-trich-dan-theo-cau.md) | Hậu kiểm trích dẫn theo câu cho trợ lý và tài liệu; bảng giá chung | commit mã | 0 (phát lại) | đạt, Claude soát 2026-10-18 [soát](../../report/kiem-thu-pha-b-sa25-28-2026-10-18.md); trình bày tài liệu → 30 |
| [26](26-bai-giang-chong-lap-ban-lui-sach.md) | Bài giảng: chống lặp ý, ghi lý do hỏng, `usage` đúng, `used_later` đúng chiều (bỏ phần bản lùi theo chủ dự án 2026-10-18) | commit mã | 0 (phát lại) | đạt [soát](../../report/kiem-thu-pha-b-sa25-28-2026-10-18.md); K6 dò sai, cache bài hỏng → 30 |
| [27](27-quiz-llm-do-luat-loai-va-nghiem-thu-lai.md) | Quiz LLM: ghi luật loại câu, sửa theo số đo, lượt thật vé 16 | commit mã | 0 phần đo; lượt thật 0,0782415 USD | đạt [soát](../../report/kiem-thu-pha-b-sa25-28-2026-10-18.md); Claude đồng ý luật tên có điều kiện |
| [28](28-ten-module-mo-ta-thanh-cau.md) | Tên module: mô tả thành câu, khuôn lùi không lộ mã, chặn tên chung | commit mã | lượt thật 0,12723425 USD | thay bằng SA-29 (đạt có ghi chú) |
| [29](29-ten-module-tach-kiem-ten-mo-ta-tu-vung-theo-sach.md) | Tên module: tách kiểm tên và mô tả, từ vựng mô tả lấy từ chính cuốn sách, luật mượn từ bằng mã | — | cache/replay 0; lượt thật 0,142519 USD | đạt có ghi chú, SA-45 soát 2026-10-18 [báo cáo](../../report/soat-pha-b-29-2026-10-18.md); chất lượng tên rộng chuyển vé 20 |
| [30](30-sua-sau-soat-k6-cache-ttft-trich-dan.md) | Sửa sau soát: K6 dò sai, không cache bài hỏng, TTFT, câu trích cụt, tài liệu sau hậu kiểm | — | 0 (phát lại) | đạt có ghi chú, SA-45 [bài giảng](../../report/soat-pha-b-30-38-43-2026-10-18.md), [tài liệu](../../report/soat-pha-b-30-tai-lieu-37-2026-10-18.md); phát lại B1 không khớp prompt B2 |
| [31](31-nen-b2-pham-vi-ham-giai.md) | Nền B2: phạm vi `scope-1`, hàm giải phạm vi, port kho, đồng hồ, cấu hình | 30 | 0 | đạt có ghi chú, SA-45 [soát](../../report/soat-pha-b-31-36-42-2026-10-18.md) |
| [32](32-phien-module-luu-du-luot.md) | Phiên module lưu đủ lượt; trợ lý hỏi theo phiên (`answer-2`) | 31 | 0 | đạt có ghi chú, SA-45; replay phản hồi 0 USD [soát](../../report/soat-pha-b-31-36-42-2026-10-18.md) |
| [33](33-phien-toan-lo-trinh-pham-vi-da-cu.md) | Phiên toàn lộ trình, phạm vi đã cũ, thẻ module ngoài phạm vi | 32 | 0 | đạt có ghi chú, SA-45; thẻ doc-4 1.322 token còn cần quyết định [soát](../../report/soat-pha-b-31-36-42-2026-10-18.md) |
| [34](34-tien-do-hoc.md) | Tiến độ học theo khái niệm | 31, **47** | 0 | đạt sau SA-47, Claude [soát 2026-10-22](../../report/soat-pha-b-46-47-49-50-51-2026-10-22.md) |
| [35](35-thu-vien-theo-pham-vi.md) | Thư viện theo phạm vi; tạo bằng nút | 32 | 0 | đạt, SA-45 [soát](../../report/soat-pha-b-31-36-42-2026-10-18.md) |
| [36](36-nhac-nen-theo-tien-do.md) | Trợ lý nhắc khái niệm nền theo tiến độ | 33, 34, **47** | 0 | đạt; nền tiến độ đã sửa ở SA-47 [soát 2026-10-22](../../report/soat-pha-b-46-47-49-50-51-2026-10-22.md) |
| [37](37-quiz-ca-lo-trinh-tai-lieu-nhieu-module.md) | Quiz cả lộ trình và tài liệu nhiều module | 34, 35, **46**, **50** | 0 | đạt: phạm vi sau SA-46, câu điền khuyết sau SA-52 (`66cd439`), tài liệu đạt [soát 52–53](../../report/soat-pha-b-52-53-sonnet-2026-10-22.md) |
| [38](38-lecture-2-hong-han-cache-thoi-gian.md) | `lecture-2`: bài hỏng hẳn, bản ghi hỏng, cache, thời gian | 30 | 0 | đạt, SA-45 [soát](../../report/soat-pha-b-30-38-43-2026-10-18.md) |
| [39](39-stream-sau-cong.md) | Bài giảng stream sau cổng | 38 | 0 | đạt có ghi chú, SA-45; giữ S3, số đo nhỏ chuyển SA-51 [soát](../../report/soat-pha-b-30-38-43-2026-10-18.md) |
| [40](40-goi-lai-tien-quyet-cau-noi-tiep-theo.md) | Gợi lại tiên quyết, câu nối, khối "Tiếp theo" | 39, **49** | 0 | đạt qua SA-53 (`62dad5b`) [soát 52–53](../../report/soat-pha-b-52-53-sonnet-2026-10-22.md) |
| [41](41-nhan-theo-nguoi-hoc.md) | Nhãn theo người học trong bài giảng | 34, 40, **47**, **49** | 0 | đạt: nhãn và tiến độ (SA-47), câu nối qua SA-53 (`62dad5b`) [soát 52–53](../../report/soat-pha-b-52-53-sonnet-2026-10-22.md) |
| [42](42-tran-chi-theo-ngay.md) | Trần chi theo ngày: người học và hệ thống | 32, 38, **48** | 0 | đạt sau SA-48 ([soát SA-48](../../report/soat-pha-b-sa48-2026-10-19.md), lỗi ranh giới ngày đã sửa trong vé) |
| [43](43-luot-that-lecture-2.md) | Lượt thật `lecture-2` | 40, **51** | thật 0,06523425 USD / trần duyệt 0,50 USD | đạt có ghi chú sau SA-51: so nhiệt độ không kết luận được, giữ S3 và nhiệt độ sửa 0 [soát 2026-10-22](../../report/soat-pha-b-46-47-49-50-51-2026-10-22.md) |
| [44](44-trang-xem-thu-hai-trang.md) | Trang xem thử hai trang | 33, 35, 36, 37, 41, 42 | 0 khi phát lại | đạt theo chủ dự án duyệt 2026-10-18; miễn 7 thao tác/ảnh, chưa thử tay; 11 test HTTP đạt |
| [45](45-soat-thay-claude-nhan-vien-cap-cao.md) | **Soát thay Claude** (nhân viên cấp cao, chủ dự án giao 2026-10-18): soát các vé Pha B, ghi phán xét, tạo vé sửa từ số 46 | — | 0 (soát); lượt có tiền cần duyệt | đã soát 29–44, tạo 46–51; có ngoại lệ phạm vi test được ghi rõ [tổng hợp](../../report/soat-pha-b-tong-hop-2026-10-18.md) |
| [46](46-quiz-roadmap-chuan-hoa-pham-vi-va-tran.md) | Quiz lộ trình: chuỗi phạm vi từ trợ lý, lấy mẫu và trần cấu hình | — | 0 | đạt, Claude soát độc lập [soát 2026-10-22](../../report/soat-pha-b-46-47-49-50-51-2026-10-22.md) |
| [47](47-tien-do-giu-lua-chon-khi-quiz-dong-thoi.md) | Tiến độ: giữ lựa chọn learner khi quiz hoàn tất đồng thời | — | 0 | đạt, Claude soát độc lập; đường PostgreSQL có test W-07 [soát 2026-10-22](../../report/soat-pha-b-46-47-49-50-51-2026-10-22.md) |
| [48](48-tran-ngay-giu-cho-dong-thoi.md) | Trần ngày: tính lượt đang chạy, giữ chỗ nguyên tử | — | 0 | đạt, [soát độc lập](../../report/soat-pha-b-sa48-2026-10-19.md); lỗi ranh giới ngày đã sửa trong vé |
| [49](49-bai-giang-mot-cau-noi-moi-tien-quyet.md) | Bài giảng: một câu nối cho mỗi tiên quyết, stream/final nhất quán | — | 0 | đạt qua SA-53 (`62dad5b`) [soát 52–53](../../report/soat-pha-b-52-53-sonnet-2026-10-22.md) |
| [50](50-quiz-dien-khuyet-kiem-luat-va-cau-thieu.md) | Quiz điền khuyết: Q3/Q6 và câu dẫn thiếu điều kiện | 46 | 0 | đạt qua SA-52 (`66cd439`) [soát 52–53](../../report/soat-pha-b-52-53-sonnet-2026-10-22.md) |
| [51](51-do-lai-so-sanh-retry-lecture-2.md) | Hoàn thiện so nhiệt độ/thời gian SA-43, matched subset và phần thiếu | 49, 48 | 0 phát lại; không gọi thêm API | đạt, Claude kiểm lại số độc lập; giữ S3 và nhiệt độ sửa 0 [soát 2026-10-22](../../report/soat-pha-b-46-47-49-50-51-2026-10-22.md) |
| [52](52-cau-dien-khuyet-nhieu-va-cau-dan.md) | Câu điền khuyết: nhiễu không nằm trong câu, không khoét giữa thuật ngữ khác, nhiễu không là ký hiệu, bỏ câu dẫn kết bằng dấu hai chấm | — | 0 | đạt có ghi chú · đã ghép `66cd439` (cổng 2.170 đạt, 1 bỏ qua) [soát 52–53](../../report/soat-pha-b-52-53-sonnet-2026-10-22.md); khe thiếu test → **54** |
| [53](53-cau-noi-final-giu-chi-so-va-test-cache.md) | Bài giảng: lọc câu nối ở bản final giữ đúng chỉ số; test lớp lọc trước K6 và test cache theo hằng số thật | — | 0 | đạt có ghi chú · đã ghép `62dad5b` (cổng 2.174 đạt, 1 bỏ qua) [soát 52–53](../../report/soat-pha-b-52-53-sonnet-2026-10-22.md); khe thiếu test → **54** |
| [54](54-test-k5-tu-vung-ten-va-test-chap-chon.md) | Test cho K5 và luật từ vựng của tên module; ổn định hai test kho JSON chập chờn | — | 0 | đạt có ghi chú · đã ghép `7d195db` (cổng 2.183 đạt, 1 bỏ qua; React 85/85): mọi mutation bị bắt; chập chờn còn lại dưới tải nặng do `os.replace` của kho JSON → **57** |
| [55](55-luot-that-tro-ly-gop-08-10.md) | Lượt thật trợ lý gộp cho SA-08, SA-10 và SA-56: 36 lượt hỏi trên bốn cuốn, ghi phản hồi để phát lại; số đo của SA-13 lấy từ lượt sinh bài giảng SA-21 | 56 | dưới 0,40 USD, trần 0,50 USD | đạt có ghi chú · đã ghép `ee79cae` (cổng 2.228 đạt): 36/36 lượt, chi thật khoảng 0,043 USD/trần 0,50, phát lại khớp 36/36; lộ hai lỗi → **58**, chờ lâu → **59** [báo cáo SA-55](../../report/pha-b-sa55-2026-10-22.md) |
| [56](56-tro-ly-focus-node-id.md) | Trợ lý biết khái niệm đang mở: trường tuỳ chọn `focus_node_id` trong `answer-2` (chủ dự án duyệt 2026-10-22); phần web gửi kèm ở W-09 | — | 0 | đạt · đã ghép `04c3efa` (cổng chung 2.218 đạt, 1 bỏ qua; React 104/104): Claude nghiệm thu, mutation tự thử bị bắt; phần web gửi kèm ở W-09 |
| [57](57-kho-json-pha-b-thu-lai-os-replace.md) | Kho JSON Pha B: thử lại `os.replace` khi Windows báo `PermissionError` (nguồn chập chờn của SA-54 và `lecture_sa30`) | 54 | 0 | đạt · ghép `43e8dda`, revert `59e72a8` để giữ cửa W-14, ghép lại `04c3efa` (cổng chung 2.218 đạt) |
| [58](58-tro-ly-scope-tim-kiem-va-ghi-am-nhieu-vong.md) | Trợ lý: `scope` không khớp bộ tìm kiếm thật (phiên module hỏng ngay lượt đầu); ghi âm phản hồi nhiều vòng bị sai | — | 0 | đạt · đã ghép `e2cfbac` (cổng 2.235 đạt, 1 bỏ qua): 7 test đỏ trước rồi xanh; bản ghi mốc SA-55/56 chỉ đổi mô tả công cụ |
| [59](59-tro-ly-cho-truoc-loi-goi-dau.md) | Trợ lý: đo và cắt thời gian chờ trước lời gọi mô hình đầu tiên (TTFT p50 15,8 s, mô hình chỉ 0,95 s) | 58 | 0 | đạt · đã ghép `d2ea0f3` (cổng 2.249 đạt): chờ giả lập p50 863 → 398 ms, tìm kiếm không đổi; phần chờ thật còn lại → **60** |
| [60](60-do-thoi-gian-that-tung-khau-tro-ly.md) | Đo thời gian thật từng khâu của trợ lý (Vertex, Developer API, kho bộ nhớ) | — | trần 0,08 USD | đạt · đã ghép `db7a41d`, chi 0,06 USD: embedding Vertex khoảng 11,4 s mỗi request, chiếm 95% thời gian chờ; Developer API 0,63 s; ghi kho JSON khoảng 1,7 s mỗi lượt [báo cáo](../../report/pha-b-sa60-2026-10-22.md); Developer API trả 400 vì `additionalProperties` → **61** |
| [61](61-schema-tuong-thich-developer-api.md) | Schema gửi Gemini tương thích Developer API (`additionalProperties` ở công cụ trợ lý và schema quiz) | — | 0 | sẵn sàng; **phải ghép trước khi đổi sang Developer API cho demo (khoảng 2026-11-12)**; chủ dự án chốt 2026-10-22 ở lại Vertex tới demo |
| [62](62-port-kho-pha-b-cho-pipeline-dung.md) | Port kho Pha B cho `DocumentPipeline`/`PhaseBRuntime` (W-15 dựng trên PostgreSQL); nguồn chi build duy nhất là meter | — | 0 | **mã đạt nghiệm thu, chưa ghép** (nhánh `work/sa62-port-kho-pha-b`, `266dbdc`): cổng 2277 đạt/2 đỏ — hai test W-15 khẳng định lõi chưa có port; chờ người điều phối sửa rồi ghép chung (mục 10) |
| [63](63-bai-giang-luon-hien-luat-kiem-chi-log.md) | Bài giảng luôn hiện; luật kiểm chỉ ghi log (ADR 0024) | — | 0 | **thay bằng SA-64** (2026-10-23): agent đã dừng khi mới viết test; chính sách ADR 0024 cài trong SA-64 |
| [64](64-bai-giang-3-van-xuoi.md) | Bài giảng `lecture-3`: văn xuôi tự nhiên, tư liệu rộng, thấy ảnh trang (ADR 0025, [spec](../../doc/bai-giang-3-spec.md)) | — | 0 khi cài; lượt thật do Claude | sẵn sàng; giao Sonnet ngay. Bản thử 13 khái niệm 0,11 USD |
| [65](65-anh-trang-luc-dung-sach.md) | Ảnh các trang có công thức lúc dựng sách + lệnh chụp bù | **62** | 0 | chờ SA-62 ghép; sau SA-64 |
| [66](66-tro-ly-3-gia-su-tu-nhien.md) | Trợ lý `answer-3`: gia sư tự nhiên, ngữ cảnh lấy trước, công cụ khi cần, kiểm chỉ ghi log (ADR 0026, [spec](../../doc/tro-ly-3-spec.md)) | **64** | 0 khi cài; lượt thật do Claude | chờ SA-64 ghép. Bản thử 12 câu: cũ 3/12 rỗng, 3–29 s; mới 12/12, 1,9–6,7 s |
| 67 (chưa vé) | Tài liệu do người học yêu cầu: bỏ hậu kiểm xoá câu (`documents.py` dùng chung `check_text`) | 66 | — | ghi nhận 2026-10-23, làm sau trợ lý |

**Vá sau SA-45, 2026-10-19:** các lỗi 46–50 đã ghép và kiểm, SA-51 sửa phương pháp tổng hợp và phát lại đủ 12 mẫu, không dùng phê duyệt chi cũ cho lượt mới. Xem [bàn giao 46–51](../../report/pha-b-sa46-51-2026-10-19.md). Các phán xét SA-45 ở dòng 34–43 phía trên là lịch sử trước vá; lỗi tương ứng đã xử lý ở 46–50, giới hạn bằng chứng so nhiệt độ vẫn được giữ tại 51.

**Soát độc lập 46–51, 2026-10-22 (Claude):** đạt 46, 47, 51; SA-48 đã có soát độc lập 2026-10-19. Chưa đạt: 49 → 53 (câu nối bị K6 loại lọt vào final), 50 → 52 (luật câu điền khuyết). Dòng 34, 36, 42, 43 chuyển đạt theo các vé sửa đã đạt. Giữ S3 và nhiệt độ sửa 0. Xem [soát 2026-10-22](../../report/soat-pha-b-46-47-49-50-51-2026-10-22.md).

**Cập nhật SA-29–30, 2026-10-18 (Codex):** đã triển khai cùng ba subagent Luna. Vé 29 phục hồi 144 tên từ cache với 0 USD, rồi chạy 160 request Vertex trong khoản chủ dự án đã duyệt, chi ghi nhận 0,142519 USD / cap 0,50 USD. Lượt mới có 136 tên và 82 mô tả LLM, 78 mô tả khuôn; chờ đọc nội dung. Vé 30 phát lại 11/12 bài giảng ready và 6/6 tài liệu ready, chi phí 0 USD. Bộ ghép cuối 206 test xanh. Xem [bàn giao 29–30](../../report/pha-b-sa29-30-ban-giao-2026-10-18.md).

"Lượt nhỏ" là lượt thử có tiền trong vé, mỗi lượt dưới 0,5 USD, cộng vào trần chung 16 USD và vẫn dry-run trước.

## Thứ tự

Ban đầu, vé 01–05 và 19 không có blocker và chạy song song được. Đường găng theo lịch đề cương:
- **Trợ lý (tuần 7, 19–25/10):** 01, 02, 03 → 08 → 09 → 10.
- **Bài giảng (tuần 8):** 02 → 11 → 12 → 13.
- **Đánh giá:** chạy cuối mỗi nhánh.
- **Trang xem thử (vé 24):** làm khi có đủ 06, 10, 13 và 16.

**Từ 2026-10-18:**
1. Nhân viên commit mã còn dở.
2. Vé 25, 26, 27, 28 chạy song song được. Riêng bảng giá chung (vé 25) làm trước, vì ba vé kia cùng dùng.
3. Sau 25 và 26: một lượt thật gộp cho vé 08, 10, 13. Dry-run trước, chủ dự án duyệt.
4. Sau 27: lượt thật vé 16 nằm trong vé 27.
5. Rồi mới tới đánh giá 20–23. Đánh giá ghim phiên bản đồ thị và ghi `upstream_chain` của từng cuốn.

**Pha B2** ([spec](../../doc/pha-b2-spec.md); vé 31–44, chia ngày 2026-10-18):
- Sau vé 30 có hai nhánh chạy song song:
  - **nhánh phiên:** 31 → 32 → 33, 35; 34 chạy song song với 32; rồi 36, 37;
  - **nhánh bài giảng:** 38 → 39 → 40 → 41 và 43.
- Hai nhánh gặp nhau ở 42 và 44.
- Đánh giá 20–23 chạy sau, trên bản `lecture-2`. Vé 21 thêm tiêu chí câu nối và phần gợi lại.

**Đợt đánh giá 20–23 (cập nhật 2026-10-22, Claude).** Các vé 20–23 viết từ 2026-10-15, trên graph cũ. Từ nay áp luật chung sau:
- **Graph ghim:**

  | cuốn | doc-1 | nhap-mon-ml | naive-bayes | doc-6 | xstk-ch3-1 | doc-4 | tổng |
  |---|---|---|---|---|---|---|---|
  | graph | v8 | v50 | v49 | v29 | v68 | v27 | |
  | module | 35 | 15 | 5 | 2 | 14 | 91 | 162 |
  | khái niệm | 223 | 75 | 33 | 11 | 82 | 495 | 919 |

  Đếm ngày 2026-10-22. Mỗi báo cáo đánh giá ghi lại graph ghim và `upstream_chain` của từng cuốn. Số nào trong vé tính trên graph cũ, ví dụ "142
  module" hay "51 module loại E", phải đếm lại trên graph ghim.
- **Kho Pha B:** mỗi lượt chạy dùng một kho JSON riêng trong `tmp/` của worktree. doc-1 dùng **bản chép** của
  `artifacts/phase_b/doc-1-rebuild-20261020.json`. Không chạy trên `artifacts/phase_b/live.json`, vì kho này có cache của tập giữ lại. Cần lấy tên module
  đã có thì đọc qua use case theo khoá của sáu cuốn phát triển; không liệt kê, không in, không chép phần `cache` của `live.json`.
- **Người làm:** agent Sonnet dựng bộ chạy, dry-run, chạy thật sau khi chủ dự án duyệt, và xuất bảng chấm mù cùng tệp khoá để riêng. Claude nghiệm thu
  và phân tích. Người chấm là thành viên nhóm do chủ dự án sắp xếp.
- **Thứ tự:**
  - 20, 21, 22 chạy được ngay;
  - 23 chờ gói 19a do agentic trả về, và chờ SA-56 (`focus_node_id` đổi đầu vào của trợ lý), để đánh giá đúng bản cuối. Cập nhật 2026-10-23: cả hai
    đã xong; còn xử lý doc-1 lệch graph ghim và duyệt người 40 câu (xem dòng 19).
- **Tiền:** theo vé, 20 dưới 1 USD, 21 trần 5 USD, 22 khoảng 1,7 USD, 23 lượt 1 trần khoảng 8 USD; tổng khoảng 15,7 USD. **Chủ dự án duyệt
  2026-10-22** ("tiền duyệt"). Mỗi vé vẫn dry-run trước; dự toán trong trần của vé thì chạy luôn, vượt trần thì dừng và hỏi. Lượt 2 của 23
  vẫn xin duyệt riêng như vé ghi.
- **Người chấm:** chủ dự án báo đã có (2026-10-22). Hướng dẫn chấm ở [`doc/huong-dan-cham/`](../../doc/huong-dan-cham/00-chung.md), một tệp
  luật chung và một tệp mỗi đợt (19a, 20, 21, 22, 23), khoảng 29 giờ mỗi người. Bộ xuất phiếu của mỗi vé phải theo đúng các cột trong hướng dẫn.
- **SA-13:** số giây tới `skeleton`, tới ý đầu và tới `final` (p50, p90) lấy từ lượt sinh bài giảng của 21.

Không kịp lịch thì báo để dời. Không cắt luật kiểm để kịp.

`[CHÈN HÌNH 1 – Đồ thị phụ thuộc của 28 vé:]`
- Mỗi vé là một hộp đánh số, có mũi tên từ vé chặn tới vé bị chặn.
- Sáu làn ngang theo đợt:
  - nền: 01–07;
  - trợ lý và bài giảng: 08–14;
  - quiz và tài liệu: 15–18;
  - đánh giá: 19–23;
  - xem thử: 24;
  - sửa sau kiểm: 25–28, có mũi tên tới 20–23.
- Tô đậm đường găng của trợ lý: 01, 02, 03 → 08 → 09 → 10 → 23.
