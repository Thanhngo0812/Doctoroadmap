# SA-65 — Ảnh các trang có công thức, chụp lúc dựng sách, kèm lệnh chụp bù

**Nguồn:** [spec bài giảng 3](../../doc/bai-giang-3-spec.md) mục 3; [ADR 0025](../../doc/adr/0025-bai-giang-3-van-xuoi-tu-nhien.md). Bài giảng `lecture-3` cần ảnh
trang để mô hình đọc đúng công thức, vì văn bản trích thay công thức bằng `[formula]`.

**Ai:** agent Sonnet cài · Claude nghiệm thu, chạy lệnh chụp bù cho sáu cuốn, và ghép · **Chi phí mô hình:** 0 USD · **Chặn bởi:** SA-62 ghép, vì cùng sửa
`composition_build.py`. Làm sau SA-64 · **Trạng thái:** chờ SA-62

## Cần làm

1. **Use case chụp trang.** Đầu vào là PDF và bản parse. Ghi ảnh JPEG của mọi trang có công thức theo định dạng ở vé SA-64:
   - đường dẫn `phase_b/page_images/<doc_id>/parse-v<N>/`;
   - tỉ lệ 1,5, chất lượng 80;
   - `index.json` có `sha256` của từng tệp.

   Trang có công thức là trang có nút `formula` trong cây parse, hoặc có chunk mà văn bản chứa `[formula]`. Renderer tiêm vào, như `CutFormulaImages`; adapter
   dùng `pypdfium2`.
2. **Gọi lúc dựng:** trong `DocumentPipeline.learning_prep`, ngay sau phần ảnh công thức, chỉ với PDF. Trả số trang đã chụp trong metadata.
3. **Lệnh chụp bù:** `doc2roadmap phase-b page-images --doc <id> --pdf <đường dẫn>` cho sách đã dựng.
   - Kiểm số trang của PDF khớp bản parse, và văn bản trang khớp chunk ở vài trang mẫu. Lệch thì dừng, không ghi.
   - Chạy lại thì không ghi đè tệp có cùng `sha256`.

## Tiêu chí nghiệm thu

Mọi test phải **đỏ trên mã cũ** hoặc trên bản sai. Ghi trong báo cáo cách đã thấy chúng đỏ.

- [ ] Use case chỉ chụp trang có công thức, và đúng số trang. Test với renderer giả.
- [ ] Adapter đọc của SA-64 đọc được đúng ảnh mà use case này ghi: test khứ hồi.
- [ ] Lệnh chụp bù từ chối PDF lệch số trang hay lệch văn bản, và không ghi gì.
- [ ] `learning_prep` trên PDF nhỏ trong test ghi ảnh trang. Tệp không phải PDF thì bỏ qua.
- [ ] Cổng toàn repo xanh.

## Ngoài phạm vi

- Claude tự chạy lệnh chụp bù cho sáu cuốn phát triển sau khi ghép, với PDF ở `Desktop\danh-gia-pha-b\sa20-giao-nguoi-cham\pdf-sach\`.
- Web: tệp ảnh nằm trong kho artifact của máy chủ (ADR 0022).
