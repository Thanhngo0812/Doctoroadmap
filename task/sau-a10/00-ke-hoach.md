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

| vé | việc | chặn bởi | tiền mô hình | trạng thái |
|---|---|---|---|---|
| [01](01-nen-pha-b-kho-so-chi-gioi-han.md) | Nền Pha B: kho lưu trữ, sổ chi, giới hạn dùng chung | — | 0 | ready-for-agent |
| [02](02-do-thi-hoc-nhan-nguon-cong-cu-tra-cuu.md) | Đồ thị học: mô hình đọc, nhãn nguồn, công cụ tra đồ thị | — | 0 | ready-for-agent |
| [03](03-a12-lop-gan-module-truy-hoi-uu-tien.md) | A12: lớp gán module, truy hồi ưu tiên module, `search_document` | — | 0 (embedding truy vấn khi thử) | ready-for-agent |
| [04](04-anh-cong-thuc.md) | Ảnh công thức | — | 0 | ready-for-agent |
| [05](05-ten-module-luat-tat-dinh-duong-lui.md) | Tên module: luật tất định, đường lùi, mô tả khuôn | — | 0 | ready-for-agent |
| [06](06-ten-mo-ta-module-do-llm-dat.md) | Tên và mô tả module do LLM đặt | 05 | dưới 0,1 USD sáu cuốn | ready-for-agent |
| [07](07-chi-muc-khai-niem.md) | Chỉ mục khái niệm | 01, 02 | dưới 0,01 USD | ready-for-agent |
| [08](08-tro-ly-agent-lat-cat-dau.md) | Trợ lý agent, lát cắt đầu: port gọi công cụ, vòng lặp có trần | 01, 02, 03 | lượt nhỏ | ready-for-agent |
| [09](09-tro-ly-trich-dan-tu-choi-ngoai-tai-lieu.md) | Trợ lý: trích dẫn, từ chối, nội dung ngoài tài liệu | 08 | 0 (phát lại) | ready-for-agent |
| [10](10-tro-ly-du-cong-cu-nhac-nen-hoi-thoai.md) | Trợ lý: đủ công cụ, nhắc khái niệm nền, hội thoại nhiều lượt | 09 | lượt nhỏ | ready-for-agent |
| [11](11-bai-giang-khong-llm.md) | Bài giảng không LLM: khung do mã dựng và trích câu | 02 | 0 | ready-for-agent |
| [12](12-bai-giang-llm-kiem-va-cache.md) | Bài giảng LLM có kiểm và cache | 01, 11 | lượt nhỏ | ready-for-agent |
| [13](13-bai-giang-stream-tai-truoc.md) | Bài giảng stream và tải trước | 12 | lượt nhỏ | ready-for-agent |
| [14](14-cong-cu-get-lecture.md) | Công cụ `get_lecture` | 08, 12 | 0 | ready-for-agent |
| [15](15-quiz-dien-khuyet-dau-cuoi.md) | Quiz điền khuyết đầu-cuối | 01, 02 | 0 | ready-for-agent |
| [16](16-quiz-llm-theo-khai-niem.md) | Quiz LLM theo khái niệm | 15 | lượt nhỏ | ready-for-agent |
| [17](17-cong-cu-make-quiz.md) | Công cụ `make_quiz` | 08, 16 | 0 (dùng ngân hàng) | ready-for-agent |
| [18](18-tai-lieu-theo-yeu-cau.md) | Tài liệu theo yêu cầu (`make_document`) | 09, 12 | lượt nhỏ | ready-for-agent |
| [19](19-dac-ta-bo-cau-hoi-thu.md) | Đặc tả bộ câu hỏi thử cho trợ lý (**Claude**) | — | 0 | ready-for-agent |
| [20](20-danh-gia-ten-module.md) | Đánh giá tên module | 06 | dưới 1 USD | ready-for-agent |
| [21](21-danh-gia-bai-giang.md) | Đánh giá bài giảng | 04, 12 | trần 5 USD | ready-for-agent |
| [22](22-danh-gia-quiz.md) | Đánh giá quiz | 16 | khoảng 1,7 USD | ready-for-agent |
| [23](23-danh-gia-tro-ly.md) | Đánh giá trợ lý: 4 cấu hình, RAGAS | 07, 10, 19 | lượt 1 trần khoảng 8 USD | ready-for-agent |
| [24](24-trang-xem-thu-pha-b.md) | Trang xem thử Pha B trên máy cục bộ (chủ dự án yêu cầu 2026-10-15) | 06, 10, 13, 16 | 0 khi phát lại; có tiền khi bật `--allow-spend` | ready-for-agent |

"Lượt nhỏ" là lượt thử có tiền trong vé, mỗi lượt dưới 0,5 USD, cộng vào trần chung 16 USD và vẫn dry-run trước.

## Thứ tự

Vé 01–05 và 19 không có blocker, chạy song song được. Theo lịch đề cương, trợ lý ở tuần 7 (19–25/10) và bài giảng ở tuần 8, nên đường găng như sau:
- **Trợ lý:** 01, 02, 03 → 08 → 09 → 10.
- **Bài giảng:** 02 → 11 → 12 → 13.
- **Đánh giá:** chạy cuối mỗi nhánh.
- **Trang xem thử (vé 24):** làm ngay khi có đủ 06, 10, 13 và 16. Trước đó, mọi chức năng thử được bằng lệnh CLI của từng vé.

Không kịp lịch thì báo để dời. Không cắt luật kiểm để kịp.

`[CHÈN HÌNH 1 – Đồ thị phụ thuộc của 24 vé:]`
- Mỗi vé là một hộp đánh số, có mũi tên từ vé chặn tới vé bị chặn.
- Năm làn ngang theo đợt:
  - nền: 01–07;
  - trợ lý và bài giảng: 08–14;
  - quiz và tài liệu: 15–18;
  - đánh giá: 19–23;
  - xem thử: 24.
- Tô đậm đường găng của trợ lý: 01, 02, 03 → 08 → 09 → 10 → 23.
