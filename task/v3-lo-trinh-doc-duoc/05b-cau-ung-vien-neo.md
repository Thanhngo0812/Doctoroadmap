# 05b — Câu ứng viên của bước neo: ưu tiên khối mang tên khái niệm; câu xem trước không phải nơi dạy

**Nguồn chân lý:** [spec v3](../../doc/v3-lo-trinh-doc-duoc-spec.md), R3 (bổ sung 2026-09-28) · **Ai:** nhân viên · **Phụ thuộc:** 05 ·
**Chi phí mô hình:** chạy lại neo phần đầu vào đổi trên kho phát triển (ước bằng `--dry-run` trước; dự kiến ≈ 0,1–0,4 USD)

**Trạng thái (2026-09-28):** đã triển khai và chạy end-to-end sáu tài liệu trên A9 v10; **chưa đạt mục tiêu chất lượng doc-2**. Neo "Matrix of a linear map" đã chuyển tới khối dạy ở thứ tự 343, "Column-row factorization" ở 391; "Matrix" vẫn là node A3 nhập nhằng nghĩa với ma trận của ánh xạ tuyến tính, còn "Jordan basis" chưa đủ căn cứ (`uncertain`). Q7 doc-2 = 0,469; 13/57 cạnh vàng ngoài phạm vi. [Báo cáo](../../report/ket-qua-v3-05b-09b-11b-vertex-2026-09-28.md).

## Vì sao (kiểm thử vé 07, 18, 2026-09-28)
- doc-2: "Matrix of a linear map" bị neo vào câu xem trước đầu chương 3 ("A major concept that we will introduce in this chapter is the
  matrix associated with a linear map…"); "Matrix" bị neo vào một câu chỉ nhắc tên; "Column-row factorization" thành chỉ-nhắc.
- Câu định nghĩa thật **không có trong 6 câu ứng viên** đưa cho mô hình, vì:
  - tên khái niệm chỉ nằm ở tiêu đề khối ("3.32 definition: matrix of a linear map", "3.56 column-row factorization"), còn thân khối
    không lặp lại tên nên bộ tìm theo tên bỏ sót;
  - xếp hạng theo `DEFAULT_DEFINITION_SIGNALS` (cụm vi/en "is called", "we define") đẩy lên câu định nghĩa khái niệm **khác** có chứa tên
    ("A square matrix is called invertible…"), đẩy câu định nghĩa thật ("An m-by-n matrix A is a rectangular array…") ra khỏi top 6.
- Hệ quả: neo sớm sai biến cạnh đúng "Linear map → Matrix of a linear map" thành ngược thứ tự sách, bị R17 làm mềm; khái niệm đích rời dãy
  học. Q7 doc-2 0,576 → 0,402, 19 cạnh vàng ngoài phạm vi.

## Việc cần làm
- Thứ hạng câu ứng viên, không dùng danh sách từ của ngôn ngữ nào:
  1. câu chứa căn cứ A3 (như cũ);
  2. chunk có tiêu đề mục — hoặc dòng mở khối, với cây mục mới — chứa tên hay alias của khái niệm (so sau `_compact`): lấy dòng tiêu đề
     khối kèm một–hai câu đầu của chunk làm một ứng viên; neo trỏ vào câu đầu của chunk;
  3. câu nhắc tên còn lại, theo vị trí.
- Bỏ `DEFAULT_DEFINITION_SIGNALS` khỏi xếp hạng câu ứng viên (R16; vốn định làm cùng vé 12, nay làm luôn vì đang gây sai).
- Prompt neo: câu chỉ báo trước một chủ đề sẽ học hoặc chỉ nhắc lại điều đã học là nhắc tên, không phải nơi dạy. Viết bằng định nghĩa
  chức năng trong khung prompt tiếng Anh, không dùng danh sách cụm từ.
- Chạy lại neo sáu tài liệu (tái dùng phán theo hash đầu vào), rồi danh tính (luật 10b), A9 (06) và A10 (07, 18, 08) **end-to-end trong
  một kho thử** — không dùng phép đo composite nữa.

## Tệp liên quan
`domain/anchors.py` (`candidate_sentences`), `application/use_cases/anchor_concepts.py`, `application/prompts/a10/anchor.txt`.

## Nghiệm thu
- Test: khối có tên khái niệm ở tiêu đề → câu đầu của khối là ứng viên hạng 2; câu định nghĩa khái niệm khác (có tên nhưng là chủ thể
  khác) không còn vượt câu định nghĩa thật; fixture ở ít nhất hai ngôn ngữ ngoài vi/en.
- **Tôi kiểm:** đọc neo của "Matrix", "Matrix of a linear map", "Column-row factorization", "Jordan basis" (doc-2) và vài khái niệm doc-1;
  Q6/Q7/Q7b doc-1, doc-2 end-to-end sau danh tính; bảng kiểm R11 sáu tài liệu.
