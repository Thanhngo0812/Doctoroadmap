# W-06 — bàn giao snapshot bốn cuốn phát triển còn lại

**Ngày:** 2026-10-20 · **Điều phối:** Codex · **Trạng thái:** **dữ liệu đã kiểm đủ, đã gửi nhân viên lõi** theo chỉ thị chủ dự án. **Không phải nghiệm thu ứng dụng W-06.**

Chủ dự án yêu cầu: “vậy bạn làm rồi gửi nhân viên đó đi”. Người nhận là phiên lõi `01a14ef0-6db3-77c2-908e-fe8b0451b3e1`, đang làm trong `tmp/w06-courses-gateway` và chờ manifest bốn cuốn. Không gửi cho nhóm web hoặc thiết kế trong đợt này.

## 1. Đường dẫn dùng ngay

Mọi đường dẫn dưới đây tính từ thư mục chung `C:/Users/ngoco/Desktop/Doctoroadmap`, không phải gốc worktree nhân viên.

| Gói | Snapshot cục bộ, không ở Git | Manifest có ở Git |
|---|---|---|
| Doc-1 và doc-6, giữ nguyên gói đã chốt | `document-data/development-rebuilt-2026-10-20` | [manifest hai cuốn](doc1-rebuild-evidence-2026-10-20/development-fixtures.json) |
| Bốn cuốn bổ sung cho W-06 | `document-data/development-w06-four-books-2026-10-20` | [manifest bốn cuốn](w06-fixtures-evidence-2026-10-20/development-fixtures.json) |

[Danh mục hai gói và phiên bản sáu graph](w06-fixtures-evidence-2026-10-20/bundles.json) ghi manifest, hash của manifest, số tệp và số byte. Hai gói không trùng đường dẫn dữ liệu; hợp lại **3.145 tệp / 278.432.863 byte**, đã đối chiếu SHA-256 toàn bộ. Chỉ cần chép phần chưa có; không ghi đè một tệp khác hash.

Gói bốn cuốn có **64 tệp / 82.876.105 byte**. SHA-256 của manifest: `4f81f6d0f04e64bd02257aa873f9d68145bc121ec6e1ecf10d819458ed4d4a5a`.

Bản ZIP dự phòng: `document-data/development-w06-four-books-2026-10-20.zip`, **23.235.604 byte**, SHA-256 **`7b7ea4cbb5a33b240fa1763a63a4ba3d9eda50241e9541b4bdd89ee7f6499bd4`**. Đã kiểm CRC và SHA-256 từng entry. Không ghi PDF, graph, cache hay ZIP vào Git.

## 2. Phiên bản đã ghim và PDF

| doc_id | graph | chunks | parse | retrieval | module | khái niệm học được | PDF / số trang |
|---|---:|---:|---:|---:|---:|---:|---|
| nhap-mon-ml | 50 | 2 | 2 | 1 | 15 | 75 | `nhap-mon-ml.pdf` / 20 |
| naive-bayes | 49 | 1 | 1 | 1 | 5 | 33 | `5_Naive Bayes Classifier.pdf` / 36 |
| xstk-ch3-1 | 68 | 7 | 2 | 1 | 14 | 82 | `xstk-ch3-1.pdf` / 59 |
| doc-4 | 27 | 6 | 2 | 1 | 91 | 495 | `doc-4.pdf` / 214 |

Doc-1 tiếp tục **v8**, doc-6 **v29** trong gói cũ. Tên PDF của Naive Bayes được giữ nguyên để khớp `SAMPLE_DOCS`/lệnh seed, không đổi thành tên giả định `naive-bayes.pdf`.

Đã kiểm hash từng PDF bằng `source_hash` của parse tương ứng; cả bốn khớp. Graph ghim đúng chunks/parse. Chỉ mục truy hồi kiểm bằng chunk ID, văn bản và đường mục; cả bốn tương thích, không chỉ so số phiên bản.

## 3. Phạm vi và phép kiểm đã chạy

- Gói bổ sung chỉ gồm PDF gốc, một phiên bản graph A10 hoàn tất, chunks/parse đã ghim cùng các tệp của phiên bản đó, và retrieval tương thích của đúng bốn doc_id cho phép. Không thu gom lịch sử dựng hoặc kho Pha B live chung.
- Chép byte độc lập sang snapshot và một bản kiểm tại `tmp/coord-w06-fixtures-20261020/verified-copy`; đối chiếu source/snapshot/copy/ZIP. Từ chối reparse point, symlink, hardlink và đường dẫn thoát gốc. Không tạo liên kết hoặc dọn worktree.
- Đã dùng `load_learning_graph` thật trên snapshot và bản kiểm để tải lại cả bốn graph, kiểm số module/khái niệm và retrieval. Sau đó kiểm lại toàn bộ 3.081 tệp của gói cũ và tải đủ sáu graph từ hai gói.
- Phép sửa sai chỉ trên bản kiểm: thêm một byte xuống dòng làm SHA-256 lệch, được bắt; chép lại từ snapshot thì hash khớp. Đường dẫn `../must-not-exist` bị từ chối trước khi ghi. Snapshot không bị sửa trong phép phá.
- Chặn mạng trong tiến trình đóng gói; **0 lần thử mạng, 0 lời gọi mô hình, 0 USD**. Không chạy seed Cloudinary thật hay gửi email.
- Đây là gói dữ liệu đủ cho seed/roadmap W-06, chưa phải nghiệm thu ảnh công thức/media W-08, mọi bài giảng/chat/quiz hoặc ứng dụng W-06 đầu-cuối.

Lệnh chạy thành công từ thư mục chung:

```text
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe -X utf8 tmp/coord-w06-fixtures-20261020/snapshot_four_books.py
```

[Mã harness đã chạy](w06-fixtures-evidence-2026-10-20/snapshot_four_books.py.txt), [kết quả kiểm](w06-fixtures-evidence-2026-10-20/snapshot-result.json). Harness được giữ để đối chiếu; không chạy lại vào các đường dẫn snapshot đã tồn tại. Lượt chuẩn bị đầu dừng ở import `pypdf` trước khi tạo snapshot; lượt chốt dùng `pypdfium2` đã có, không cài thêm thư viện, exit 0.

## 4. Nhân viên lõi dùng thế nào

1. Đọc báo cáo và hai manifest ở thư mục chung, hoặc đọc bản Git trên main mới. Không cần đổi nhánh thư mục chung; nhận main mới trong worktree riêng trước cổng nghiệm thu cuối.
2. Theo [runbook dữ liệu](../doc/du-lieu-phat-trien-va-fixture.md), lấy từng `files[].path` tương đối với `snapshot` tương ứng; kiểm SHA-256 nguồn, chép bằng `shutil.copyfile` vào đúng vị trí dưới gốc worktree, rồi kiểm SHA-256 đích. Kiểm reparse point cả tệp lẫn thư mục cha, từ chối hardlink và đường dẫn thoát gốc. Tệp đích đã cùng hash thì giữ; khác hash thì dừng báo điều phối, không xoá hoặc ghi đè để ép khớp.
3. Giữ doc-1/doc-6 đã chép đúng hash từ gói cũ. Nếu cây artifact đích có phiên bản khác cao hơn, dùng một gốc dữ liệu kiểm sạch hoặc báo điều phối; không xoá lịch sử, không cho `latest` chọn lẫn ngoài sáu phiên bản đã chốt.
4. Chạy seed đủ sáu cuốn bằng **MediaStore và mô hình giả**, HTTP/PostgreSQL thật. Bàn giao JSON thật, log/JUnit, số khoá và membership, idempotency, test người ngoài, owner/store/transport. Các ảnh công thức/media hoàn thiện ở vé tương ứng.
5. Chưa ghi W-06 đạt chỉ vì dữ liệu đã đủ; điều phối nghiệm thu tổng sau khi web tích hợp và cổng đúng commit xanh.

## 5. Thông báo người nhận

Đã gửi đúng phiên lõi `01a14ef0-6db3-77c2-908e-fe8b0451b3e1` bằng `codex_tui.send_message_to_thread`, công cụ trả thành công (`isError=false`).
Nội dung trỏ tới báo cáo này trong thư mục chung, hai gói/manifest, số tệp đã kiểm và cách dùng an toàn; yêu cầu kiểm seed sáu cuốn với MediaStore/mô hình giả, HTTP/PostgreSQL thật, chưa ghi W-06 đạt.
Biên nhận và nguyên văn thông báo ở [notification.json](w06-fixtures-evidence-2026-10-20/notification.json). Không gửi sang phiên web hoặc thiết kế.
