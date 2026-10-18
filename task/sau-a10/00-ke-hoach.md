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
- **Commit chỉ đường dẫn của vé.** Phiên khác và nhân viên khác có thể đang stage dở.
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
| [02](02-do-thi-hoc-nhan-nguon-cong-cu-tra-cuu.md) | Đồ thị học: mô hình đọc, nhãn nguồn, công cụ tra đồ thị | — | 0 | chưa đạt: test cạnh mở `requires` (sửa ở 25); thiếu số tên bị chặn vì "tên phổ biến" |
| [03](03-a12-lop-gan-module-truy-hoi-uu-tien.md) | A12: lớp gán module, truy hồi ưu tiên module, `search_document` | — | 0 (embedding truy vấn khi thử) | đạt; thiếu giây/truy vấn doc-4 |
| [04](04-anh-cong-thuc.md) | Ảnh công thức | — | 0 | đạt |
| [05](05-ten-module-luat-tat-dinh-duong-lui.md) | Tên module: luật tất định, đường lùi, mô tả khuôn | — | 0 | chưa đạt → 28 |
| [06](06-ten-mo-ta-module-do-llm-dat.md) | Tên và mô tả module do LLM đặt | 05 | dưới 0,1 USD sáu cuốn | chưa đạt → 28 |
| [07](07-chi-muc-khai-niem.md) | Chỉ mục khái niệm | 01, 02 | dưới 0,01 USD | đạt |
| [08](08-tro-ly-agent-lat-cat-dau.md) | Trợ lý agent, lát cắt đầu: port gọi công cụ, vòng lặp có trần | 01, 02, 03 | lượt nhỏ | test đạt; chờ lượt thật sau 25 |
| [09](09-tro-ly-trich-dan-tu-choi-ngoai-tai-lieu.md) | Trợ lý: trích dẫn, từ chối, nội dung ngoài tài liệu | 08 | 0 (phát lại) | chưa đạt → 25 |
| [10](10-tro-ly-du-cong-cu-nhac-nen-hoi-thoai.md) | Trợ lý: đủ công cụ, nhắc khái niệm nền, hội thoại nhiều lượt | 09 | lượt nhỏ | chưa đạt → 25; chờ lượt thật |
| [11](11-bai-giang-khong-llm.md) | Bài giảng không LLM: khung do mã dựng và trích câu | 02 | 0 | chưa đạt → 26 |
| [12](12-bai-giang-llm-kiem-va-cache.md) | Bài giảng LLM có kiểm và cache | 01, 11 | lượt nhỏ | chưa đạt → 26 |
| [13](13-bai-giang-stream-tai-truoc.md) | Bài giảng stream và tải trước | 12 | lượt nhỏ | chờ lượt thật sau 26 |
| [14](14-cong-cu-get-lecture.md) | Công cụ `get_lecture` | 08, 12 | 0 | đạt |
| [15](15-quiz-dien-khuyet-dau-cuoi.md) | Quiz điền khuyết đầu-cuối | 01, 02 | 0 | đạt |
| [16](16-quiz-llm-theo-khai-niem.md) | Quiz LLM theo khái niệm | 15 | lượt nhỏ | chưa đạt → 27 |
| [17](17-cong-cu-make-quiz.md) | Công cụ `make_quiz` | 08, 16 | 0 (dùng ngân hàng) | đạt |
| [18](18-tai-lieu-theo-yeu-cau.md) | Tài liệu theo yêu cầu (`make_document`) | 09, 12 | lượt nhỏ | chưa đạt → 25 |
| [19](19-dac-ta-bo-cau-hoi-thu.md) | Đặc tả bộ câu hỏi thử cho trợ lý (**Claude**) | — | 0 | chủ dự án duyệt 19a; gói và câu kiểm đã xuất 2026-10-18; chờ giao agentic |
| [20](20-danh-gia-ten-module.md) | Đánh giá tên module | 06, **28**, **29** | dưới 1 USD | ready-for-agent |
| [21](21-danh-gia-bai-giang.md) | Đánh giá bài giảng | 04, 12, **26**, **30**, **49**, **51** | trần 5 USD | chờ sửa câu nối và hoàn thiện bằng chứng SA-43 |
| [22](22-danh-gia-quiz.md) | Đánh giá quiz | 16, **27**, **46**, **50** | khoảng 1,7 USD | chờ sửa quiz lộ trình/điền khuyết, SA-45 |
| [23](23-danh-gia-tro-ly.md) | Đánh giá trợ lý: 4 cấu hình, RAGAS | 07, 10, 19, **25**, **30**, **46**, **47**, **48**, **50** | lượt 1 trần khoảng 8 USD | chờ sửa các đường công cụ/tiến độ/trần ngày |
| [24](24-trang-xem-thu-pha-b.md) | Trang xem thử Pha B trên máy cục bộ (chủ dự án yêu cầu 2026-10-15) | 06, 10, 13, 16 | 0 khi phát lại; có tiền khi bật `--allow-spend` | đạt |
| [25](25-hau-kiem-trich-dan-theo-cau.md) | Hậu kiểm trích dẫn theo câu cho trợ lý và tài liệu; bảng giá chung | commit mã | 0 (phát lại) | đạt, Claude soát 2026-10-18 [soát](../../report/kiem-thu-pha-b-sa25-28-2026-10-18.md); trình bày tài liệu → 30 |
| [26](26-bai-giang-chong-lap-ban-lui-sach.md) | Bài giảng: chống lặp ý, ghi lý do hỏng, `usage` đúng, `used_later` đúng chiều (bỏ phần bản lùi theo chủ dự án 2026-10-18) | commit mã | 0 (phát lại) | đạt [soát](../../report/kiem-thu-pha-b-sa25-28-2026-10-18.md); K6 dò sai, cache bài hỏng → 30 |
| [27](27-quiz-llm-do-luat-loai-va-nghiem-thu-lai.md) | Quiz LLM: ghi luật loại câu, sửa theo số đo, lượt thật vé 16 | commit mã | 0 phần đo; lượt thật 0,0782415 USD | đạt [soát](../../report/kiem-thu-pha-b-sa25-28-2026-10-18.md); Claude đồng ý luật tên có điều kiện |
| [28](28-ten-module-mo-ta-thanh-cau.md) | Tên module: mô tả thành câu, khuôn lùi không lộ mã, chặn tên chung | commit mã | lượt thật 0,12723425 USD | chưa đạt [soát](../../report/kiem-thu-pha-b-sa25-28-2026-10-18.md): 135/160 rơi đường lùi → 29 |
| [29](29-ten-module-tach-kiem-ten-mo-ta-tu-vung-theo-sach.md) | Tên module: tách kiểm tên và mô tả, từ vựng mô tả lấy từ chính cuốn sách, luật mượn từ bằng mã | — | cache/replay 0; lượt thật 0,142519 USD | đạt có ghi chú, SA-45 soát 2026-10-18 [báo cáo](../../report/soat-pha-b-29-2026-10-18.md); chất lượng tên rộng chuyển vé 20 |
| [30](30-sua-sau-soat-k6-cache-ttft-trich-dan.md) | Sửa sau soát: K6 dò sai, không cache bài hỏng, TTFT, câu trích cụt, tài liệu sau hậu kiểm | — | 0 (phát lại) | đạt có ghi chú, SA-45 [bài giảng](../../report/soat-pha-b-30-38-43-2026-10-18.md), [tài liệu](../../report/soat-pha-b-30-tai-lieu-37-2026-10-18.md); phát lại B1 không khớp prompt B2 |
| [31](31-nen-b2-pham-vi-ham-giai.md) | Nền B2: phạm vi `scope-1`, hàm giải phạm vi, port kho, đồng hồ, cấu hình | 30 | 0 | đạt có ghi chú, SA-45 [soát](../../report/soat-pha-b-31-36-42-2026-10-18.md) |
| [32](32-phien-module-luu-du-luot.md) | Phiên module lưu đủ lượt; trợ lý hỏi theo phiên (`answer-2`) | 31 | 0 | đạt có ghi chú, SA-45; replay phản hồi 0 USD [soát](../../report/soat-pha-b-31-36-42-2026-10-18.md) |
| [33](33-phien-toan-lo-trinh-pham-vi-da-cu.md) | Phiên toàn lộ trình, phạm vi đã cũ, thẻ module ngoài phạm vi | 32 | 0 | đạt có ghi chú, SA-45; thẻ doc-4 1.322 token còn cần quyết định [soát](../../report/soat-pha-b-31-36-42-2026-10-18.md) |
| [34](34-tien-do-hoc.md) | Tiến độ học theo khái niệm | 31, **47** | 0 | chưa đạt: quiz ghi đè lựa chọn learner khi đồng thời → 47 [soát](../../report/soat-pha-b-31-36-42-2026-10-18.md) |
| [35](35-thu-vien-theo-pham-vi.md) | Thư viện theo phạm vi; tạo bằng nút | 32 | 0 | đạt, SA-45 [soát](../../report/soat-pha-b-31-36-42-2026-10-18.md) |
| [36](36-nhac-nen-theo-tien-do.md) | Trợ lý nhắc khái niệm nền theo tiến độ | 33, 34, **47** | 0 | đạt phần nhắc nền, SA-45; chờ nền tiến độ sửa race [soát](../../report/soat-pha-b-31-36-42-2026-10-18.md) |
| [37](37-quiz-ca-lo-trinh-tai-lieu-nhieu-module.md) | Quiz cả lộ trình và tài liệu nhiều module | 34, 35, **46**, **50** | 0 | chưa đạt, SA-45 soát: phạm vi chuỗi bỏ trần, câu điền khuyết bỏ luật → 46/50; tài liệu đạt [soát](../../report/soat-pha-b-30-tai-lieu-37-2026-10-18.md) |
| [38](38-lecture-2-hong-han-cache-thoi-gian.md) | `lecture-2`: bài hỏng hẳn, bản ghi hỏng, cache, thời gian | 30 | 0 | đạt, SA-45 [soát](../../report/soat-pha-b-30-38-43-2026-10-18.md) |
| [39](39-stream-sau-cong.md) | Bài giảng stream sau cổng | 38 | 0 | đạt có ghi chú, SA-45; giữ S3, số đo nhỏ chuyển SA-51 [soát](../../report/soat-pha-b-30-38-43-2026-10-18.md) |
| [40](40-goi-lai-tien-quyet-cau-noi-tiep-theo.md) | Gợi lại tiên quyết, câu nối, khối "Tiếp theo" | 39, **49** | 0 | chưa đạt: hai câu nối cùng tiên quyết → 49 [soát](../../report/soat-pha-b-30-38-43-2026-10-18.md) |
| [41](41-nhan-theo-nguoi-hoc.md) | Nhãn theo người học trong bài giảng | 34, 40, **47**, **49** | 0 | đạt phần nhãn, SA-45; chờ nền tiến độ/câu nối sửa [soát](../../report/soat-pha-b-30-38-43-2026-10-18.md) |
| [42](42-tran-chi-theo-ngay.md) | Trần chi theo ngày: người học và hệ thống | 32, 38, **48** | 0 | chưa đạt: hai call đồng thời vượt trần ngày → 48 [soát](../../report/soat-pha-b-31-36-42-2026-10-18.md) |
| [43](43-luot-that-lecture-2.md) | Lượt thật `lecture-2` | 40, **51** | thật 0,06523425 USD / trần duyệt 0,50 USD | chưa đạt so sánh nhiệt độ: 2 fixture không khớp; đã đọc 12 bài → 51 [soát](../../report/soat-pha-b-30-38-43-2026-10-18.md) |
| [44](44-trang-xem-thu-hai-trang.md) | Trang xem thử hai trang | 33, 35, 36, 37, 41, 42 | 0 khi phát lại | đạt theo chủ dự án duyệt 2026-10-18; miễn 7 thao tác/ảnh, chưa thử tay; 11 test HTTP đạt |
| [45](45-soat-thay-claude-nhan-vien-cap-cao.md) | **Soát thay Claude** (nhân viên cấp cao, chủ dự án giao 2026-10-18): soát các vé Pha B, ghi phán xét, tạo vé sửa từ số 46 | — | 0 (soát); lượt có tiền cần duyệt | đã soát 29–44, tạo 46–51; có ngoại lệ phạm vi test được ghi rõ [tổng hợp](../../report/soat-pha-b-tong-hop-2026-10-18.md) |
| [46](46-quiz-roadmap-chuan-hoa-pham-vi-va-tran.md) | Quiz lộ trình: chuỗi phạm vi từ trợ lý, lấy mẫu và trần cấu hình | — | 0 | ready-for-agent; lỗi SA-37 phát hiện ở SA-45 |
| [47](47-tien-do-giu-lua-chon-khi-quiz-dong-thoi.md) | Tiến độ: giữ lựa chọn learner khi quiz hoàn tất đồng thời | — | 0 | đã vá/kiểm memory và JSON 2026-10-19; chờ ghép [bàn giao](../../report/pha-b-sa47-2026-10-19.md) |
| [48](48-tran-ngay-giu-cho-dong-thoi.md) | Trần ngày: tính lượt đang chạy, giữ chỗ nguyên tử | — | 0 | ready-for-agent; sửa SA-42 |
| [49](49-bai-giang-mot-cau-noi-moi-tien-quyet.md) | Bài giảng: một câu nối cho mỗi tiên quyết, stream/final nhất quán | — | 0 | ready-for-agent; sửa SA-40 |
| [50](50-quiz-dien-khuyet-kiem-luat-va-cau-thieu.md) | Quiz điền khuyết: Q3/Q6 và câu dẫn thiếu điều kiện | 46 | 0 | ready-for-agent; lỗi đọc đầu ra thật SA-37/SA-15 |
| [51](51-do-lai-so-sanh-retry-lecture-2.md) | Hoàn thiện so nhiệt độ/thời gian SA-43, matched subset và phần thiếu | 49, 48 | 0 phát lại; có tiền cần dry-run/duyệt mới | ready-for-agent (phát lại); sửa bằng chứng SA-43 |

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
