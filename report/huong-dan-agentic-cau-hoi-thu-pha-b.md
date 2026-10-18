# Hướng dẫn cho agent: soạn bộ câu hỏi thử cho trợ lý học tập

Bạn là agent soạn câu hỏi. Đọc hết hướng dẫn này một lần trước khi bắt đầu, và mở lại khi phân vân.

**Bối cảnh.** Một trợ lý học tập trả lời câu hỏi của người học về một cuốn giáo trình tiếng Việt. Trợ lý chỉ được dùng nội dung cuốn sách đó. Bạn soạn
câu hỏi giống câu người học thật sự hỏi, kèm đáp án tham chiếu chỉ ra chỗ trong sách. Bộ câu dùng để chấm trợ lý, nên:
- **mỗi câu "trả lời được" phải trả lời được bằng chính cuốn sách,** và bạn chỉ ra được đoạn nào;
- **câu "ngoài tài liệu" phải thật sự không có trong sách,** và bạn đã tìm để chắc chắn.

**Chỉ dựa vào các tệp được giao:**
- không tra mạng để lấy nội dung sách;
- được dùng hiểu biết chung để **nghĩ ra** câu hỏi, nhất là câu ngoài tài liệu, nhưng đáp án tham chiếu luôn lấy từ sách.

## 1. Bạn nhận gì, trả gì

Mỗi cuốn có một mã `<doc>`.

| tệp nhận | nội dung |
|---|---|
| `goi/<doc>/thong_tin.json` | mã cuốn, số module, số khái niệm, và **chỉ tiêu** số câu mỗi loại |
| `goi/<doc>/module.jsonl` | mỗi module một dòng: `module_id`, `so_thu_tu` (thứ tự người học thấy), `ten`, `khai_niem` (các `node_id`) |
| `goi/<doc>/khai_niem.jsonl` | mỗi khái niệm một dòng: `node_id`, `ten`, `bi_danh`, `module_id`, `mo_ta` (tóm tắt máy viết, có thể sai) |
| `goi/<doc>/doan.jsonl` | mỗi đoạn sách một dòng: `chunk_id`, `trang`, `muc` (đường mục), `thu_tu`, `text` |
| `goi/<doc>/cau_kiem.jsonl` | vài câu hỏi có sẵn để bạn điền (mục 5) |
| `kiem_cau_hoi_thu.py` | script tự kiểm định dạng |

| tệp trả | nội dung |
|---|---|
| `cau/<doc>.jsonl` | câu bạn soạn, mỗi câu một dòng, đúng chỉ tiêu |
| `kiem/<doc>.jsonl` | câu kiểm đã điền, mỗi câu một dòng |
| `ghi-chu/<doc>.md` | agent và mô hình, thời gian, chỗ phân vân, đoạn khó |

**Hai lưu ý về dữ liệu:**
- **`text` của đoạn lấy từ PDF nên có thể lỗi:** âm tiết bị tách ("v ới"), công thức thành ký tự rác hoặc `[formula]`, hình thành `[figure]`. Đừng
  chọn đoạn chỉ có rác làm đoạn tham chiếu.
- **`mo_ta` của khái niệm do máy viết,** chỉ để bạn nhận ra khái niệm. Đừng lấy `mo_ta` làm đáp án; đáp án lấy từ `text` của đoạn.

## 2. Bảy loại câu

| `loai` | người học hỏi gì | trả lời được |
|---|---|---|
| `dinh_nghia` | X là gì, gồm những gì | có |
| `tien_quyet` | vì sao cần Y trước X; muốn hiểu X cần nắm gì trước | có |
| `so_sanh` | X khác Y chỗ nào; khi nào dùng cái nào | có |
| `vi_du` | cho ví dụ về X; sách minh hoạ X thế nào | có |
| `lo_trinh` | muốn học tới X thì đi qua những gì; X nằm ở đâu | có |
| `ngoai_tai_lieu` | điều sách không dạy | **không** |
| `nhieu_luot` | 1–2 câu trước, rồi một câu nối tiếp dựa vào ngữ cảnh | có |

**Luật riêng từng loại:**
- **`tien_quyet`:** chỉ viết khi sách có câu cho thấy X dùng Y, ví dụ định nghĩa X nhắc Y, hay chứng minh của X dùng Y. Đoạn tham chiếu là đoạn đó.
  Không tự suy ra quan hệ mà sách không nói.
- **`so_sanh`:** sách phải nói về cả hai khái niệm. Đoạn tham chiếu gồm đoạn của mỗi bên, hoặc đoạn so sánh trực tiếp nếu có.
- **`vi_du`:** sách phải có ví dụ, bài giải hay minh hoạ cho X. Đoạn tham chiếu là đoạn ví dụ, không phải đoạn định nghĩa.
- **`lo_trinh`:** khái niệm kỳ vọng là đích X. Đoạn tham chiếu là đoạn dạy X. Ý chính nêu những thứ sách dùng khi dạy X.
- **`ngoai_tai_lieu`** có hai kiểu:
  - `gan_chu_de`: nghe như thuộc sách nhưng sách không dạy, ví dụ một phương pháp cùng lĩnh vực mà sách không có. **Ít nhất một nửa** câu ngoài tài
    liệu phải là kiểu này.
  - `lac_de`: hỏi chuyện khác hẳn, ví dụ cài phần mềm, lịch thi.

  Với cả hai kiểu, **tìm ít nhất 2 từ khoá** trong `text` của mọi đoạn và ghi vào `da_tim`. Từ khoá có trong sách thì câu đó có thể không phải ngoài tài
  liệu: viết câu khác.
- **`nhieu_luot`:**
  - `luot_truoc` là 1–2 câu người học hỏi trước đó, thường là một câu `dinh_nghia` đơn giản.
  - `cau_hoi` là câu nối tiếp, cần ngữ cảnh mới hiểu: "Vậy nó dùng để làm gì?", "Còn cái kia thì sao?", "Cho ví dụ đi".
  - Không quá một nửa câu cuối nêu thẳng tên khái niệm.
  - Các trường đáp án mô tả câu cuối.

## 3. Từng trường

Mỗi dòng là một object JSON có **đúng** các trường sau, không thêm, không bớt.

| trường | luật |
|---|---|
| `cau_id` | `<doc>-q001`, `<doc>-q002`, … không lặp |
| `doc_id` | mã cuốn |
| `loai` | một trong bảy mã ở mục 2 |
| `module_dang_mo` | `module_id` của module người học đang mở khi hỏi (xem dưới) |
| `luot_truoc` | `[]`, trừ `nhieu_luot` |
| `cau_hoi` | lời người học, ≤ 300 ký tự |
| `van_phong` | `chuan`, hoặc `than_mat` cho câu kiểu nhắn tin (vẫn đủ dấu). Ít nhất 15% câu `than_mat` |
| `khai_niem_ky_vong` | `node_id` lấy từ `khai_niem.jsonl`: 1–3 khái niệm; `so_sanh` 2–3; ngoài tài liệu `[]` |
| `doan_tham_chieu` | `chunk_id` lấy từ `doan.jsonl`: 1–3 đoạn chứa câu trả lời; ngoài tài liệu `[]` |
| `tra_loi_duoc` | `false` khi và chỉ khi `ngoai_tai_lieu` |
| `y_chinh` | 1–3 ý của đáp án, mỗi ý `{"y": "…", "doan": "<chunk_id trong doan_tham_chieu>"}`, ≤ 200 ký tự, viết gọn bằng lời của bạn; ngoài tài liệu `[]` |
| `kieu_ngoai` | `gan_chu_de` hay `lac_de` cho ngoài tài liệu; còn lại `null` |
| `da_tim` | ngoài tài liệu: ≥ 2 từ khoá đã tìm; còn lại `[]` |
| `chua_chac` | `true` khi bạn không chắc một trường |
| `ghi_chu` | bắt buộc khi `chua_chac = true`: trường nào, vì sao |
| `nguoi_tao` | tên agent và mô hình |

**Cách chọn `module_dang_mo`:**
- Phần lớn câu: module chứa khái niệm kỳ vọng. Đây là người học hỏi về bài đang học.
- **Ít nhất 15% khái niệm kỳ vọng nằm ở module SAU module đang mở.** Đây là người học hỏi trước về bài chưa tới. Dùng `so_thu_tu` để biết trước sau.
- Một ít câu: module đang mở nằm sau khái niệm. Đây là người học hỏi lại bài cũ.
- Câu ngoài tài liệu: chọn module có chủ đề gần câu hỏi.

**Cách viết câu hỏi:**
- **Viết bằng lời người học,** không chép câu trong sách. Script cảnh báo khi câu hỏi chép nguyên văn từ 10 từ liền nhau trở lên.
- **Đa dạng cách hỏi.** Đừng để mọi câu đều là "X là gì?".
- **Không ghi mã nội bộ** (`node_…`, `c_…`, `module_…`) trong câu hỏi. Người học không thấy mã.
- **Trải đều câu trên các module.** Mọi module đều có câu. Với cuốn có từ 10 module trở lên, không module nào quá 3 câu.

## 4. Ví dụ (tự soạn, không lấy từ sách được giao)

Sách giả "sach-mau" về sinh học thực vật:

| module | `so_thu_tu` | khái niệm |
|---|---:|---|
| `module_001` Quang hợp | 1 | Quang hợp (`node_aaaaaa01`), Diệp lục (`node_aaaaaa02`), Lục lạp (`node_aaaaaa03`), Pha sáng (`node_aaaaaa04`), Pha tối (`node_aaaaaa05`) |
| `module_002` Trao đổi nước | 2 | Khí khổng (`node_aaaaaa06`), Thoát hơi nước (`node_aaaaaa07`), Mạch gỗ (`node_aaaaaa08`) |
| `module_003` Hô hấp | 3 | Hô hấp tế bào (`node_aaaaaa09`) |

Đoạn `c_aaaaaa02`: "Lục lạp là bào quan chứa diệp lục; quang hợp diễn ra trong lục lạp." Đoạn `c_aaaaaa05`: "Pha tối dùng ATP và NADPH do pha sáng tạo ra để cố
định CO2 thành đường."

**`dinh_nghia`:**
```json
{"cau_id": "sach-mau-q001", "doc_id": "sach-mau", "loai": "dinh_nghia", "module_dang_mo": "module_001", "luot_truoc": [], "cau_hoi": "Lục lạp là cái gì vậy?", "van_phong": "than_mat", "khai_niem_ky_vong": ["node_aaaaaa03"], "doan_tham_chieu": ["c_aaaaaa02"], "tra_loi_duoc": true, "y_chinh": [{"y": "Bào quan chứa diệp lục, nơi diễn ra quang hợp.", "doan": "c_aaaaaa02"}], "kieu_ngoai": null, "da_tim": [], "chua_chac": false, "ghi_chu": "", "nguoi_tao": "agent-x / model-y"}
```

**`tien_quyet`:** sách nói pha tối dùng sản phẩm của pha sáng, nên quan hệ có căn cứ.
```json
{"cau_id": "sach-mau-q002", "doc_id": "sach-mau", "loai": "tien_quyet", "module_dang_mo": "module_001", "luot_truoc": [], "cau_hoi": "Tại sao phải hiểu pha sáng rồi mới học pha tối?", "van_phong": "chuan", "khai_niem_ky_vong": ["node_aaaaaa05", "node_aaaaaa04"], "doan_tham_chieu": ["c_aaaaaa05"], "tra_loi_duoc": true, "y_chinh": [{"y": "Pha tối dùng ATP và NADPH do pha sáng tạo ra.", "doan": "c_aaaaaa05"}], "kieu_ngoai": null, "da_tim": [], "chua_chac": false, "ghi_chu": "", "nguoi_tao": "agent-x / model-y"}
```

**`ngoai_tai_lieu`, `gan_chu_de`:** sách dạy quang hợp nhưng không có thực vật CAM. Đã tìm "CAM" và "xương rồng", không thấy.
```json
{"cau_id": "sach-mau-q003", "doc_id": "sach-mau", "loai": "ngoai_tai_lieu", "module_dang_mo": "module_001", "luot_truoc": [], "cau_hoi": "Thực vật CAM quang hợp khác cây bình thường thế nào?", "van_phong": "chuan", "khai_niem_ky_vong": [], "doan_tham_chieu": [], "tra_loi_duoc": false, "y_chinh": [], "kieu_ngoai": "gan_chu_de", "da_tim": ["CAM", "xương rồng"], "chua_chac": false, "ghi_chu": "", "nguoi_tao": "agent-x / model-y"}
```

**`nhieu_luot`:** câu cuối không nêu tên khái niệm. Người học đang ở module 1 nên đây cũng là ca hỏi trước bài sau.
```json
{"cau_id": "sach-mau-q004", "doc_id": "sach-mau", "loai": "nhieu_luot", "module_dang_mo": "module_001", "luot_truoc": ["Khí khổng là gì?"], "cau_hoi": "Nó đóng mở để làm gì?", "van_phong": "than_mat", "khai_niem_ky_vong": ["node_aaaaaa06"], "doan_tham_chieu": ["c_aaaaaa06"], "tra_loi_duoc": true, "y_chinh": [{"y": "Điều chỉnh lượng nước thoát ra và khí trao đổi.", "doan": "c_aaaaaa06"}], "kieu_ngoai": null, "da_tim": [], "chua_chac": false, "ghi_chu": "", "nguoi_tao": "agent-x / model-y"}
```

**Câu hỏi mẫu cho ba loại còn lại:**
- `so_sanh`: "Mạch gỗ với thoát hơi nước liên quan gì nhau?"
- `vi_du`: "Sách có ví dụ nào cho thấy cây mất nước qua lá không?"
- `lo_trinh`: "Muốn hiểu hô hấp tế bào thì mình nên đọc những phần nào trước?"
- `ngoai_tai_lieu`, `lac_de`: "Trường mình thi cuối kỳ môn này vào tuần nào?"

**Câu xấu, đừng viết:**

| câu | vì sao xấu |
|---|---|
| "Lục lạp là bào quan chứa diệp lục; quang hợp diễn ra ở đâu?" | chép nguyên câu sách vào câu hỏi, lộ đáp án |
| `tien_quyet` "Vì sao cần học khí khổng trước hô hấp tế bào?" | sách không nói quan hệ này; tự suy ra |
| `ngoai_tai_lieu` "Diệp lục có màu gì?" | sách có nói, tức là trả lời được |
| `dinh_nghia` mà đoạn tham chiếu là `[figure]` | đoạn không chứa câu trả lời |

## 5. Câu kiểm

`goi/<doc>/cau_kiem.jsonl` có vài câu với `cau_id` dạng `<doc>-k01`, đã có sẵn `loai`, `module_dang_mo`, `luot_truoc`, `cau_hoi`.
- Chép các trường đó **nguyên văn** sang `kiem/<doc>.jsonl`, rồi điền các trường còn lại theo đúng luật ở mục 3.
- Không sửa câu hỏi. Script báo lỗi nếu bạn sửa.
- Câu kiểm không tính vào chỉ tiêu.

## 6. Cách làm và tự kiểm

1. **Làm từng cuốn.** Đọc `module.jsonl` và `khai_niem.jsonl` trước để biết sách dạy gì, rồi đọc lướt `doan.jsonl`.
2. **Mỗi câu:** chọn khái niệm, tìm đoạn chứa câu trả lời bằng cách tìm tên và bí danh trong `text`, đọc đoạn, rồi mới viết câu hỏi và ý chính.
3. **Sau mỗi khoảng 10 câu,** chạy:

   ```
   python kiem_cau_hoi_thu.py --doc <doc> --thu-muc . --mot-phan
   ```

   Sửa hết dòng `LỖI`. Đọc mọi dòng `CẢNH BÁO` và sửa nếu đúng là vấn đề.
4. **Xong cuốn,** chạy lại không có `--mot-phan`. Phải in `ĐẠT`.
5. **Làm tiếp sau khi dừng:** đọc dòng cuối của `cau/<doc>.jsonl` để biết số `cau_id` đã tới. Không viết lại câu đã có.
6. **Không chắc** thì đặt `chua_chac: true` và ghi lý do. Không tìm được đoạn tham chiếu thì bỏ câu đó, viết câu khác.

## 7. Bàn giao

- [ ] `kiem_cau_hoi_thu.py` in `ĐẠT` cho cả sáu cuốn (không `--mot-phan`).
- [ ] Đủ chỉ tiêu mỗi loại theo `thong_tin.json`.
- [ ] Mỗi câu kiểm có đúng một dòng trong `kiem/<doc>.jsonl`.
- [ ] Mỗi câu ngoài tài liệu có ≥ 2 từ khoá đã tìm, và không từ nào có trong sách.
- [ ] Có `ghi-chu/<doc>.md` cho từng cuốn.
