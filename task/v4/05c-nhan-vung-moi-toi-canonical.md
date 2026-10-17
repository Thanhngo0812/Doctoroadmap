# 05c — Nhãn vùng gán lại phải tới được canonical khi A3 chạy trên bản chunk đã gán nhãn

**Nguồn chân lý:** phát hiện khi chuẩn bị vé [T-01b](T-01b-do-t01-hai-chuoi.md) (nhánh C), 2026-10-17.
**Ai:** nhân viên · **Chi phí mô hình:** 0 USD · **Chặn bởi:** không · **Trạng thái:** mã/test xong 2026-10-17, chưa commit; chưa chạy trên kho chính

## Vì sao

**Hai cách luồng có thể đã chạy:**
- **Kiểu 05b** (xstk, doc-4, doc-1): A3 chạy trên bản chunk **chưa** gán nhãn N. `label-roles` tạo bản nhãn mới với `roles_from_chunks_version = N`, và
  canonical tìm đúng bản đó qua `load_role_chunks(doc, N)`.
- **Kiểu T-01 và D-01:** `label-roles` chạy trước A3. Bản nhãn v2 (gán từ v1) trở thành đầu vào của A3, nên canonical gọi `load_role_chunks(doc, 2)`.

**Lỗi ở kiểu T-01, D-01.** Gán lại nhãn sau đó (ví dụ để áp luật mới của 05a):
- `label-roles` luôn quay về bản gốc chưa gán nhãn (v1), nên bản nhãn mới ghi `roles_from_chunks_version = 1`;
- `load_role_chunks(doc, 2)` chỉ nhận bản ghi `roles_from_chunks_version = 2`, nên trả lại v2 cũ;
- **nhãn mới bị bỏ qua mà không báo gì**, và canonical vẫn neo theo nhãn cũ.

Hệ quả: luật 05a không áp được cho hai cuốn T-01 và 16 cuốn D-01 nếu không chạy lại A3 (tốn tiền). Sách mới đi theo kiểu này cũng gặp lỗi.

## Cần làm

- **Khi canonical cần nhãn của bản chunk N mà N tự nó là bản nhãn** (`semantic_roles`, gán từ bản gốc R), dùng **bản nhãn mới nhất gán từ R**:
  - cùng `source_hash`;
  - cùng `chunk_id`, văn bản và offset với N (đã có kiểm này);
  - không có bản nhãn nào mới hơn N thì trả lại chính N, như hiện nay.
- **Giữ nguyên kiểu 05b:** N chưa gán nhãn thì vẫn tìm bản gán từ N.
- **Không đổi** `chunk_id`, khoá cache của chunk hay A3. Canonical đã ghi `anchor_chunks_version`, nên dùng bản nhãn mới sẽ tự sinh canonical mới. Lời gộp
  và mô tả vẫn tái dùng theo nhật ký.
- **`a4 --dry-run`** phải báo đúng bản nhãn sẽ dùng.

## Không làm

- Không chạy lại `label-roles`, `a4` hay `roadmap` có chi. Nhánh C của T-01b do Claude chạy sau khi vé này xong.
- Không sửa 16 cuốn D-01 (đã đóng băng).

## Nghiệm thu

- [x] Test dựng kho theo kiểu T-01: chunk v1 chưa nhãn; v2 gán nhãn từ v1; ứng viên A3 trên v2; gán lại nhãn ra v3 (gán từ v1).
  `load_role_chunks(doc, 2)` trả v3. **Phải đỏ trên mã hiện nay.**
- [x] Test kiểu 05b giữ nguyên: ứng viên trên bản chưa nhãn N, bản nhãn gán từ N được dùng.
- [x] Test bản nhãn mới có `chunk_id` hoặc văn bản khác thì bị từ chối như hiện nay.
- [x] Toàn bộ test qua.

## Bàn giao nhân viên 2026-10-17

Sửa bộ nạp để bản nhãn N dùng bản mới nhất từ cùng bản gốc R, chỉ nhận version
mới hơn N và giữ kiểm source/ID/text/offset. Không đổi cache chunk hay A3.
Dry-run báo version qua `phases.anchor.note` (`anchor_chunks_version=<version>`),
cả khi tái dùng cache.

14 ca mới: **7 đỏ trước sửa**, 14 xanh sau sửa. Nhóm liên quan **62 passed**;
toàn kho **1.572 passed**, 7 cảnh báo deprecation, exit 0. Test tích hợp dùng
fixture phát triển và mô hình giả chứng minh neo lấy nhãn mới, canonical đổi
hash, lời gộp/mô tả tái dùng và tệp A3/chunk gốc giữ nguyên bytes.

Trong lúc nhánh B đang chạy, chỉ sửa mã và chạy test trên kho tạm; không chạy
lệnh ghi `artifacts/`, không mở nội dung T-01 hoặc sửa D-01. Các lượt test green
và toàn kho có audit hook riêng chặn ghi kho chính, đã thử nhánh từ chối trước
khi tạo tệp. Chi mô hình **0 USD**. Chưa commit, chưa chạy nhánh C; Claude ghim
mã và chạy nhánh C sau khi lượt hiện tại cho phép.

[Báo cáo 05c](../../report/v4-05c-nhan-vung-moi-toi-canonical-2026-10-17.md).
