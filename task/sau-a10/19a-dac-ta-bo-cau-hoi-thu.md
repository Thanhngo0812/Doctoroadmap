# SA-19a — Đặc tả bộ câu hỏi thử cho trợ lý Pha B (gửi chủ dự án)

**Thuộc vé:** [SA-19](19-dac-ta-bo-cau-hoi-thu.md). **Dùng ở:** [SA-23](23-danh-gia-tro-ly.md), đánh giá trợ lý.
**Ba tệp đi kèm:**
- hướng dẫn cho agentic: [report/huong-dan-agentic-cau-hoi-thu-pha-b.md](../../report/huong-dan-agentic-cau-hoi-thu-pha-b.md);
- script kiểm định dạng: `scripts/pha-b/kiem_cau_hoi_thu.py`, chỉ thư viện chuẩn, kèm 25 test trong `tests/unit/scripts/test_kiem_cau_hoi_thu.py`;
- script xuất gói đầu vào: `scripts/pha-b/xuat_goi_cau_hoi_thu.py`, 0 USD.

**Chi phí mô hình phía dự án:** 0 USD. Phí của dịch vụ agentic do chủ dự án chọn.
**Trạng thái:** chờ chủ dự án duyệt (mục 13).

## Vì sao

Vé 23 so bốn cấu hình trợ lý trên cùng một bộ câu:
- LLM không bằng chứng;
- RAG thuần;
- agent không có công cụ đồ thị;
- agent đầy đủ.

Bộ câu phải có bốn tính chất:
- **phủ các loại câu người học thật sự hỏi,** kể cả câu ngoài tài liệu và câu nối tiếp;
- **có đáp án tham chiếu trong sách,** để RAGAS đo context recall và để người chấm đối chiếu;
- **không thiên về cấu hình nào.** Câu phải đến từ việc đọc sách, không từ đồ thị. Nếu câu sinh từ cạnh đồ thị thì cấu hình có công cụ đồ thị thắng sẵn,
  và phép so mất giá trị;
- **làm đúng ngay lần đầu,** theo bài học của D-01: định dạng chặt, có script tự kiểm, có câu kiểm biết trước đáp án.

## 1. Phạm vi

**Sáu cuốn phát triển.** Gói xuất từ đồ thị A10 hiện hành:

| Cuốn | Đồ thị | Chuỗi | Module | Khái niệm | Đoạn |
|---|---|---|---:|---:|---:|
| doc-1 | v53 | gộp | 33 | 205 | 199 |
| doc-4 | v23 | gộp | 91 | 495 | 671 |
| xstk-ch3-1 | v64 | gộp | 14 | 82 | 126 |
| nhap-mon-ml | v46 | v3 | 15 | 75 | 41 |
| naive-bayes | v45 | v3 | 5 | 33 | 40 |
| doc-6 | v17 | v3 | 4 | 28 | 27 |

**Không dùng tập giữ lại.** Script xuất từ chối `d01-t01`, `d01-t02`.

**Đoạn tham chiếu dùng `chunk_id`.** Đoạn tham chiếu gắn với bản chunk của đồ thị trên. Vé 28 chỉ đổi tên module, không đổi chunk, nên bộ câu vẫn dùng
được. Nếu phía pha A chạy lại một cuốn thì phải xuất lại gói của cuốn đó, rồi kiểm lại `chunk_id`.

## 2. Quy trình

| Bước | Ai | Việc |
|---|---|---|
| 1 | Claude | Chạy script xuất gói cho sáu cuốn. Gói có văn bản các đoạn, danh sách module (tên, số thứ tự), danh sách khái niệm (tên, bí danh, module, mô tả ≤ 200 ký tự). **Không có cạnh đồ thị, câu neo, chunk dạy.** |
| 2 | Claude | Soạn 12 câu kiểm (2 mỗi cuốn) vào `goi/<doc>/cau_kiem.jsonl`. Đáp án giữ ở `Desktop\pha-b-cau-hoi-thu\khoa-kiem.jsonl`, ngoài repo |
| 3 | Chủ dự án | Chọn dịch vụ agentic (mục 10). Giao gói, hướng dẫn, script kiểm |
| 4 | Agentic | Soạn câu vào `cau/<doc>.jsonl`, điền câu kiểm vào `kiem/<doc>.jsonl`. Tự chạy script kiểm tới khi in "ĐẠT" |
| 5 | Claude | Chạy lại script kiểm; chấm câu kiểm; đọc toàn bộ cảnh báo; chọn mẫu duyệt 40 câu |
| 6 | Hai thành viên nhóm | Duyệt cùng 40 câu, độc lập (mục 9) |
| 7 | Claude | Tính tỉ lệ lỗi theo trường và độ đồng thuận; nhận, hoặc trả về agentic kèm danh sách lỗi |
| 8 | Claude | Sửa các lỗi duyệt đã thấy; chia dev và test; ghi bản `v1` và đóng băng (mục 11) |

## 3. Chỉ tiêu

Tổng 200 câu. Cuốn lớn nhận nhiều câu hơn; cuốn nhỏ vẫn đủ mỗi loại.

| Cuốn | định nghĩa | tiên quyết | so sánh | ví dụ | lộ trình | ngoài tài liệu | nhiều lượt | tổng |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| doc-1 | 8 | 6 | 6 | 4 | 4 | 6 | 6 | 40 |
| doc-4 | 10 | 7 | 8 | 5 | 5 | 8 | 7 | 50 |
| xstk-ch3-1 | 7 | 5 | 5 | 4 | 4 | 5 | 5 | 35 |
| nhap-mon-ml | 6 | 4 | 5 | 3 | 3 | 5 | 4 | 30 |
| naive-bayes | 5 | 3 | 4 | 3 | 2 | 4 | 4 | 25 |
| doc-6 | 4 | 3 | 3 | 2 | 2 | 3 | 3 | 20 |
| **tổng** | **40** | **28** | **31** | **21** | **20** | **31** | **29** | **200** |

Chỉ tiêu nằm trong gói (`thong_tin.json`); script kiểm báo lỗi khi thiếu hay vượt.

**Phân bố phụ:**
- **Module đang mở:** ≥ 15% khái niệm kỳ vọng nằm ở module sau module đang mở. Mục đích là thử ghi chú "học kỹ ở module N" và truy hồi ra ngoài module.
  Script cảnh báo khi dưới mức này.
- **Câu ngoài tài liệu:** ít nhất một nửa là "gần chủ đề". Đây là câu nghe như thuộc sách nhưng sách không dạy, ví dụ hỏi chéo hoá ma trận trong
  doc-1. Phần còn lại là "lạc đề". Script báo lỗi khi thiếu.
- **Văn phong:** ≥ 15% câu viết thân mật như người học nhắn tin, vẫn đủ dấu. Script cảnh báo.
- **Câu nối tiếp:** không quá một nửa câu cuối nêu thẳng tên khái niệm. Phần còn lại dùng "nó", "cái đó", "còn … thì sao". Script cảnh báo.

## 4. Bảy loại câu

| Mã | Loại | Người học hỏi gì | Trả lời được |
|---|---|---|---|
| `dinh_nghia` | định nghĩa | khái niệm X là gì, gồm gì | có |
| `tien_quyet` | vì sao tiên quyết | vì sao cần Y trước X; muốn hiểu X cần nắm gì. Sách phải có câu cho thấy X dùng Y | có |
| `so_sanh` | so sánh | X khác Y chỗ nào, khi nào dùng cái nào | có |
| `vi_du` | ví dụ | cho ví dụ về X, minh hoạ X. Sách phải có ví dụ | có |
| `lo_trinh` | lộ trình | muốn học tới X thì đi qua những gì; X nằm ở đâu trong sách | có |
| `ngoai_tai_lieu` | ngoài tài liệu | điều sách không dạy | không |
| `nhieu_luot` | nhiều lượt | 1–2 câu trước rồi một câu nối tiếp dựa vào ngữ cảnh | có |

Hai luật chung:
- Câu "trả lời được" phải trả lời được **chỉ bằng sách**, và agentic chỉ ra được 1–3 đoạn chứa câu trả lời.
- Câu ngoài tài liệu phải được agentic **tìm trong văn bản** ít nhất 2 từ khoá và ghi lại các từ đã tìm. Script cảnh báo nếu từ đã tìm có trong sách.

## 5. Trường của mỗi câu

Một dòng JSON mỗi câu.

| Trường | Kiểu | Ý nghĩa |
|---|---|---|
| `cau_id` | chuỗi | `<doc>-q001`, tăng dần |
| `doc_id` | chuỗi | mã cuốn |
| `loai` | chuỗi | một trong bảy mã ở mục 4 |
| `module_dang_mo` | chuỗi | module người học đang mở khi hỏi |
| `luot_truoc` | danh sách chuỗi | câu hỏi của các lượt trước; chỉ `nhieu_luot` có, 1–2 câu |
| `cau_hoi` | chuỗi | câu cần chấm, ≤ 300 ký tự, lời người học, không chứa mã nội bộ |
| `van_phong` | `chuan` hay `than_mat` | |
| `khai_niem_ky_vong` | danh sách `node_id` | khái niệm câu hỏi nhắm tới: 1–3; `so_sanh` 2–3; ngoài tài liệu thì rỗng |
| `doan_tham_chieu` | danh sách `chunk_id` | 1–3 đoạn chứa câu trả lời; ngoài tài liệu thì rỗng |
| `tra_loi_duoc` | true/false | false đúng khi và chỉ khi là `ngoai_tai_lieu` |
| `y_chinh` | danh sách `{y, doan}` | 1–3 ý của đáp án, mỗi ý ≤ 200 ký tự, trỏ một đoạn trong `doan_tham_chieu`; ngoài tài liệu thì rỗng |
| `kieu_ngoai` | `gan_chu_de`, `lac_de` hay null | chỉ cho ngoài tài liệu |
| `da_tim` | danh sách chuỗi | từ khoá đã tìm trong sách; chỉ cho ngoài tài liệu, ít nhất 2 |
| `chua_chac` | true/false | true khi agentic không chắc một trường |
| `ghi_chu` | chuỗi | bắt buộc khi `chua_chac = true`: chưa chắc trường nào, vì sao |
| `nguoi_tao` | chuỗi | agent và mô hình |

**Lệch so với vé 19:** vé ghi `y_chinh` là tuỳ chọn. Đặc tả này bắt buộc `y_chinh` cho câu trả lời được, vì RAGAS cần đáp án tham chiếu để đo
context recall (vé 23).

## 6. Định dạng tệp và chia theo cuốn

| Thư mục | Ai ghi | Nội dung |
|---|---|---|
| `goi/<doc>/` | Claude | `thong_tin.json`, `module.jsonl`, `khai_niem.jsonl`, `doan.jsonl`, `cau_kiem.jsonl` |
| `cau/<doc>.jsonl` | agentic | câu tự soạn, đúng chỉ tiêu |
| `kiem/<doc>.jsonl` | agentic | câu kiểm đã điền, mỗi câu kiểm một dòng |
| `ghi-chu/<doc>.md` | agentic | thời gian, mô hình, chỗ phân vân, đoạn khó |

Mỗi cuốn một tệp, làm xong cuốn này mới sang cuốn khác. Lệnh kiểm:
`python kiem_cau_hoi_thu.py --doc <doc> --thu-muc .` (thêm `--mot-phan` khi đang làm dở).

## 7. Chỗ để trống khi không chắc

Bộ câu cần đúng hơn cần đủ nhanh:
- Không chắc một trường nào thì đặt `chua_chac = true` và ghi rõ trong `ghi_chu`. Không đoán cho đủ.
- Không tìm được đoạn tham chiếu cho một câu định viết thì **bỏ câu đó, viết câu khác**, không ghi đoạn gần đúng.
- Câu `chua_chac` vẫn tính vào chỉ tiêu. Claude xem hết các câu này ở bước 5.

## 8. Mẫu kiểm chất lượng

- **12 câu kiểm,** 2 mỗi cuốn, do Claude soạn từ sách, biết trước đáp án:
  - khái niệm kỳ vọng;
  - đoạn tham chiếu;
  - trả lời được hay không.
- **Một cuốn có một câu trả lời được và một câu ngoài tài liệu gần chủ đề.**
- **Agentic điền các trường còn lại,** không được sửa câu hỏi; script kiểm chặn việc sửa.
- **Cách Claude chấm:**
  - `tra_loi_duoc` phải đúng;
  - khái niệm kỳ vọng phải trùng;
  - đoạn tham chiếu được tính đúng nếu trùng, hoặc là đoạn liền kề cùng mục.
- **Ngưỡng:** đúng dưới 10/12 thì nâng mẫu duyệt người từ 40 lên 80 câu.
- **Ví dụ trong hướng dẫn cho agentic thuộc lĩnh vực sinh học thực vật, tự soạn.** Đã kiểm 16 tên ví dụ: không trùng tên hay bí danh nào trong 1.180
  tên và bí danh của sáu cuốn, cũng không xuất hiện trong văn bản sáu cuốn.

## 9. Duyệt người

**Mẫu:** 40 câu (20%), phân tầng theo cuốn × loại, Claude chọn bằng hạt giống cố định. Hai thành viên nhóm duyệt **cùng** 40 câu, **độc lập**, khoảng
40 phút mỗi người.

**Mỗi câu chấm sáu ô đúng/sai:**
1. **Tự nhiên:** giống câu người học thật sự hỏi.
2. **Đúng loại.**
3. **Trả lời được đúng:** sách trả lời được câu này, hoặc với câu ngoài tài liệu thì sách thật không có. Người duyệt tìm trong PDF.
4. **Khái niệm kỳ vọng đúng.**
5. **Đoạn tham chiếu chứa câu trả lời.**
6. **Ý chính đúng nguồn.**

**Luật nhận, viết trước khi duyệt:**
- Ô nào có tỉ lệ sai > 15% ở cả hai người thì trả cả bộ về agentic sửa riêng ô đó, kèm danh sách câu sai.
- Ô "trả lời được" sai > 10% thì trả về, vì đây là ô quyết định cách chấm câu từ chối.
- Dưới ngưỡng: Claude sửa các câu sai đã thấy rồi nhận bộ.
- Claude tính κ theo từng ô và ghi vào báo cáo; κ thấp thì ghi hạn chế, không đổi luật nhận.

**Nhãn bộ câu:** "agentic soạn, người duyệt mẫu 20%". Không gọi là vàng người.

## 10. Tài liệu đi qua dịch vụ nào (chủ dự án quyết)

- Gói chứa **toàn văn sáu cuốn phát triển** (1,8 MB). Giao gói cho dịch vụ agentic nghĩa là gửi văn bản sách tới nhà cung cấp của dịch vụ đó.
- **Không cài khoá API hay `.env`** vào thư mục giao.
- **Nên dùng một họ mô hình khác Gemini để soạn câu.** Trợ lý được đánh giá chạy Gemini. Câu do Gemini soạn có nguy cơ hợp khẩu vị Gemini, làm số đẹp
  hơn thật. Nếu chỉ có Gemini thì ghi hạn chế này vào báo cáo của vé 23.

## 11. Cách Claude dùng bộ câu

- **Chia dev và test, phân tầng theo cuốn × loại, hạt giống cố định:**
  - **dev:** 50 câu, dùng để thử khi sửa prompt hay luật của trợ lý (vé 25 và lượt thật của vé 08, 10);
  - **test:** 150 câu, chỉ chạy ở vé 23.
- **Trước khi chạy test,** cấu hình trợ lý được đóng băng: ghi commit, prompt hash, mô hình. Sau đó không sửa theo kết quả test.
- **Câu từ chối chấm riêng** (vé 23), vì RAGAS cho câu từ chối relevancy bằng 0.
- **Độ chính xác liên kết khái niệm** đo bằng `khai_niem_ky_vong`.
- **Context recall** đo bằng `y_chinh` và `doan_tham_chieu`.
- **Bộ câu ghi ở `artifacts/phase_b/eval/cau-hoi-thu/v1/`,** kèm `thong_tin.json` của gói để biết phiên bản đồ thị và chunk.

## 12. Ví dụ lấy từ dữ liệu dự án

**Chỉ cho người đọc đặc tả.** Không đưa phần này cho agentic, vì sẽ trùng câu kiểm. Các ví dụ từ doc-1 (đại số tuyến tính):

| Loại | Câu |
|---|---|
| định nghĩa | "Ma trận bậc thang là gì?" |
| tiên quyết | "Sao phải học hạng của ma trận trước khi giải hệ phương trình tuyến tính?" |
| so sánh | "Đơn ánh với toàn ánh khác nhau chỗ nào?" |
| ví dụ | "Sách có ví dụ nào về ánh xạ tuyến tính không?" |
| lộ trình | "Muốn hiểu trị riêng thì mình cần học những phần nào trước?" |
| ngoài tài liệu, gần chủ đề | "Chéo hoá ma trận làm thế nào?" (doc-1 dạy trị riêng nhưng không có "chéo hoá") |
| ngoài tài liệu, lạc đề | "Cài numpy trên Windows thế nào?" |
| nhiều lượt | trước: "Định thức là gì?"; câu chấm: "Vậy tính nó bằng biến đổi sơ cấp được không?" |

## 13. Câu hỏi cho chủ dự án

1. **Duyệt chỉ tiêu và bảy loại câu** ở mục 3, 4. Đề xuất: giữ như trên.
2. **Dịch vụ agentic** nào được nhận toàn văn sáu cuốn? Đề xuất: một họ mô hình khác Gemini.
3. **Hai thành viên nào duyệt 40 câu?** Có thể là hai người chấm của vé 20–23.
4. **doc-6 đang là đồ thị chuỗi v3,** không có câu neo. Bộ câu không phụ thuộc câu neo nên vẫn làm được. Nhưng nếu phía pha A sẽ chạy lại doc-6, thì
   nên chạy trước khi xuất gói, để `chunk_id` không đổi sau khi đã soạn câu.
