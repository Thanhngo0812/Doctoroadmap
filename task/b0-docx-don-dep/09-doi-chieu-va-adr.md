# 09 — Đối chiếu bốn tài liệu, ADR 0003 và cập nhật tài liệu

**What to build:** Đợt được đóng bằng chứng cứ, không bằng niềm tin: ingest **thật** lại cả bốn tài
liệu trên cây sạch và thi hành bảng dự-đoán-ảnh-hưởng-chéo của spec. Sai khác ngoài bảng ⇒ **dừng
và tìm ra vì sao** trước khi đóng đợt.

## Bảng dự đoán phải khớp

| Tài liệu | Được phép đổi | Phải giữ nguyên |
|---|---|---|
| nhap-mon-ml | dòng cảnh báo gom lại (nếu có trùng nguyên văn) | **toàn bộ định danh chunk**, cây 4 cấp, 9 tham chiếu hình |
| xstk-ch3-1 | dòng cảnh báo gom lại | **toàn bộ định danh chunk**, 263 công thức, 51 bảng |
| baocao-canhan | cây 2 cấp đủ 27 section; run nối; rác biến mất; ảnh raster có tham chiếu; thêm `missing_image` | nội dung văn bản thật không mất một câu |
| naive-bayes | 72 bullet biến mất; cảnh báo về một màn hình; chunk vượt trần có lý do | 32 công thức, 13 bảng, 2 ảnh; các tiêu đề bị hạ (F37) **giữ nguyên trạng** |

## Tài liệu và quyết định

- **ADR 0003 — tin dữ liệu khai báo, suy diễn là dự phòng:** mọi luật suy diễn phải khai nó là dự
  phòng cho trường hợp thiếu dữ liệu khai báo, và phải nhường khi dữ liệu khai báo có mặt và không
  thoái hoá. Ghi bối cảnh vòng 9: ba phát hiện lớn chung hình dạng *"luật hiệu chỉnh trên một thể
  loại thay thế dữ liệu thật của thể loại khác"*. Ghi cả vế đối ngẫu của bài học vòng 8: khi thư
  viện trả về thứ trông **đúng và đầy đủ** (cấp của Word), đừng thay nó bằng phỏng đoán của mình.
- Từ điển thuật ngữ thêm: *cây khai báo*, *cây thoái hoá*, *run định dạng*, *khối phi ngôn ngữ* —
  theo đúng khuôn các mục sẵn có, kèm phần *tránh dùng*.
- Báo cáo thường trực: mục nhánh DOCX viết lại cho đúng hành vi mới (ảnh, nối run, cấp khai báo);
  mục cảnh báo và trần cập nhật I25.
- Ghi số đo sau đợt cho **cả bốn** tài liệu để vòng sau đối chiếu — số vàng trong test chính là nơi
  ghi, chỉ cần trỏ tới.

**Blocked by:** 03, 04, 05, 06, 07, 08, 10 — mọi thay đổi phải nằm đủ trước khi đối chiếu mới có nghĩa.

**Status:** done

- [x] Ingest thật bốn tài liệu trên cây sạch; artifact phiên bản mới sinh đúng một lần cho mỗi tầng
      bị đổi (adapter nhích một, thuật toán chunk nhích một — cả đợt)
- [x] Bảng dự đoán khớp **từng ô**; mọi sai khác được điều tra và ghi lại trước khi đóng
- [x] Hai giáo trình: so trực tiếp phiên bản cũ ↔ mới như vòng 8 — định danh chunk không đổi
- [x] Số vàng cuối đợt = trạng thái sau đợt, commit cùng lời giải thích từng cú dịch
- [x] ADR 0003 viết xong; ADR 0002 đã có phần bổ sung (ticket 03); từ điển và báo cáo thường trực
      cập nhật
- [x] Toàn bộ bộ test xanh trên cây sạch
