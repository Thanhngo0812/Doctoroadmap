# Pha B: read-model đồ thị, truy hồi và ảnh công thức — 2026-10-15

## Phạm vi và dữ liệu cố định

Đã nghiệm thu SA-02, SA-03, SA-04 và SA-07 trên sáu tài liệu phát triển, không dùng holdout. Loader mặc định bỏ qua artifact trung gian `stage=edges` và chọn artifact hoàn chỉnh `stage=stages`; phiên bản được ghim dưới đây khớp phiên bản hoàn chỉnh mới nhất. Tổng cộng có **159 module**.

| Tài liệu | Graph | Chunks | Parse | Modules | Nodes (learnable / excluded / mentioned / non-learnable) | Chunks nguồn |
|---|---:|---:|---:|---:|---:|---:|
| `doc-1` | 37 | 5 | 5 | 39 | 222 (218 / 4 / 0 / 0) | 199 |
| `nhap-mon-ml` | 37 | 2 | 2 | 15 | 75 (75 / 0 / 0 / 0) | 41 |
| `naive-bayes` | 37 | 1 | 1 | 5 | 34 (33 / 1 / 0 / 0) | 40 |
| `doc-6` | 8 | 2 | 2 | 4 | 28 (28 / 0 / 0 / 0) | 27 |
| `xstk-ch3-1` | 46 | 5 | 2 | 9 | 146 (72 / 1 / 20 / 53) | 126 |
| `doc-4` | 12 | 6 | 2 | 87 | 616 (489 / 0 / 127 / 0) | 671 |

Tất cả sáu retrieval index tương thích với tập chunk thực tế theo `chunk_id`, nội dung và đường mục; kiểm tra không yêu cầu số phiên bản artifact phải bằng nhau. Overlay gợi ý module được tính mà không sửa vectors hay chunk IDs:

| Tài liệu | Gán trực tiếp | Gợi ý từ chunk dạy gần nhất | Chưa gán |
|---|---:|---:|---:|
| `doc-1` | 98 | 98 | 3 |
| `nhap-mon-ml` | 31 | 9 | 1 |
| `naive-bayes` | 17 | 21 | 2 |
| `doc-6` | 12 | 12 | 3 |
| `xstk-ch3-1` | 35 | 90 | 1 |
| `doc-4` | 286 | 381 | 4 |

## Kiểm chứng graph tools và trích dẫn

Đã gọi các graph tools công khai trên từng module và node của sáu graph: **63.352 lời gọi**, tổng thời gian **68,76 giây** trong lần chạy này. Output lớn nhất là `why_here` với **5.649 byte** (ước tính 1.413 token); kết quả được giới hạn theo spec: tối đa 3 prerequisite, traversal tối đa 5 cạnh, module context tối đa 8 node. `why_here` dùng Hasse predecessor, không lấy tùy tiện ba cạnh đầu.

Các trích dẫn được kiểm tra bằng cách trích raw text theo absolute offsets rồi xác nhận đoạn cắt không có whitespace thừa ở hai đầu. Không còn span sai:

| Tài liệu | Edge quote hợp lệ / ứng viên | Anchor quote hợp lệ / ứng viên | Nguồn `why_here` |
|---|---:|---:|---|
| `doc-1` | 0 / 0 | 200 / 200 | 224 đoạn liên quan legacy, nhãn S; không gắn nhãn Q |
| `nhap-mon-ml` | 0 / 0 | 56 / 56 | 64 đoạn liên quan legacy, nhãn S; không gắn nhãn Q |
| `naive-bayes` | 0 / 0 | 20 / 20 | 23 đoạn liên quan legacy, nhãn S; không gắn nhãn Q |
| `doc-6` | 0 / 0 | 0 / 0 | 15 đoạn liên quan legacy, nhãn S; không gắn nhãn Q |
| `xstk-ch3-1` | 243 / 267 | 71 / 71 | 99 trích dẫn Q có câu quote trực tiếp |
| `doc-4` | 1.956 / 2.028 | 489 / 489 | 643 trích dẫn Q có câu quote trực tiếp |

Các artifact cũ của bốn tài liệu đầu không lưu quote của cạnh. `why_here` chỉ trả đoạn nguồn liên quan dưới nhãn S với cảnh báo `missing_edge_quote` và ghi chú “Đoạn liên quan; artifact cũ thiếu câu trích bằng chứng của cạnh”; nội dung `reason` do model sinh không được trình bày như lời trích. Q và N offsets dùng NFC/whitespace normalization nhưng vẫn ánh xạ về span raw. Regression test cho trường hợp quote bắt đầu bằng combining U+0338 sau newline tái hiện lỗi cũ rồi xác nhận span mới bắt đầu đúng ký tự.

## Ảnh công thức

Ảnh được crop từ PDF cục bộ và lưu riêng theo document/parse version trong `artifacts/phase_b/formula_images/`; không ghi ngược parse tree. Key occurrence giữ `formula_id`, page, reading order và bbox, nên các formula ID trùng không ghi đè ảnh của vị trí khác.

| Tài liệu | Formula node | Crop thành công | Ảnh PNG duy nhất | Ghi chú |
|---|---:|---:|---:|---|
| `doc-1` | 562 | 562 | 561 | PDF `doc-1.pdf`, 3,25 s |
| `xstk-ch3-1` | 263 | 263 | 240 | PDF `xstk-ch3-1.pdf`, 1,76 s |
| `naive-bayes` | 32 | 32 | 32 | PDF `5_Naive Bayes Classifier.pdf`, 3,51 s |
| `nhap-mon-ml` | 1 | 0 | 0 | Không có PDF cục bộ; index giữ trạng thái `missing_source_pdf` |
| `doc-6` | 0 | 0 | 0 | Không có formula node |
| `doc-4` | 0 | 0 | 0 | Không có formula node |

Đã xem contact sheet gồm 20 crop mỗi tài liệu có PDF, cùng raw text: [HTML](../artifacts/phase_b/formula_images/contact-sheet.html), [doc-1 PNG](../artifacts/phase_b/formula_images/contact-sheet-doc-1.png), [xstk PNG](../artifacts/phase_b/formula_images/contact-sheet-xstk-ch3-1.png), [naive-bayes PNG](../artifacts/phase_b/formula_images/contact-sheet-naive-bayes.png). Crop mẫu đúng công thức; một số bbox rộng bao gồm glyph/text kề bên ở công thức nhiều dòng hoặc dạng bảng. Không thấy lỗi lệch trang có tính hệ thống sau khi renderer batch gắn ảnh đúng occurrence.

Loader `load_learning_graph` đọc formula index cùng `parse-vN` của graph đã ghim và gắn `graph.formula_images`, map theo `formula_id@p<page>:r<reading_order>`. Kiểm tra end-to-end trên doc-1 xác nhận 562 ref đều trỏ đến file tồn tại; duplicate formula IDs vẫn có occurrence/page/bbox riêng. Parse Nhe sẵn có ghi nhận doc-1 có 2.602 formula nodes và xstk có 407; tất cả đều có bbox cùng raw text (`tmp/a1-v414-r25/trees/`). Không chạy lại A1.

## Tính toàn vẹn và chi phí

SHA-256 của 24 thư mục input (graph, chunks, parse tree và retrieval index cho mỗi tài liệu) trước/sau đều không đổi. Không sửa vector, chunk, graph hay parse artifact ghim; formula ảnh nằm trong vùng Phase B riêng. Không gọi LLM, không gọi mạng và không tạo chi phí: **$0.00**. Retrieval acceptance dùng index/embedding giả hoặc dữ liệu có sẵn; không gửi embedding query có trả phí.

Focused suite sau các thay đổi: **18 passed**. Chạy benchmark công khai toàn graph và kiểm tra formula-reference round-trip trên artifact thật cũng hoàn tất.
