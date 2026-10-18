# SA-51 — Hoàn thiện bằng chứng so retry và thời gian của SA-43

**Nguồn chân lý:** [SA-43](43-luot-that-lecture-2.md), [spec B2](../../doc/pha-b2-spec.md), mục 6.1 và lượt thật; phát hiện trong SA-45.

**Ai:** nhân viên chạy · nhân viên cấp cao đọc/kiểm · **Chi phí mô hình:** 0 USD bước phát lại; bước bổ sung có tiền phải dry-run và chủ dự án duyệt riêng · **Chặn bởi:** 49, 48 · **Trạng thái:** ready-for-agent (phát lại)

## Vì sao

Lượt SA-43 đã được chủ dự án duyệt trần 0,50 USD, chi thực tế 0,06523425 USD, 30 HTTP attempts. Sau sửa lỗi runtime, phát lại có hai prompt sửa ở nhánh nhiệt độ 1 không khớp bản ghi. Vì thế số 10/12 ready ở nhánh 0 và 9/12 ở nhánh 1 **không phải so sánh cặp công bằng**. Không được xem thiếu fixture là mô hình sinh bài kém.

Chỉ có bốn mẫu timing thật đầy đủ sau khi loại lỗi runtime, p50 cổng→final 939 ms, p90 1.574 ms. Không được lấy thời gian đọc fixture làm độ trễ provider. SA-43 còn thiếu bằng chứng kết luận retry temperature trên đầy đủ cặp hợp lệ.

## Cần làm

- Kiểm runner và ghi rõ từng cặp: phiên bản graph/node, context/prompt/schema, lần đầu dùng chung, candidate sửa nhiệt độ 0 và 1, số lần gọi, USD, nguyên nhân loại hay thiếu fixture.
- Phát lại 0 USD các phản hồi thực sự khớp, tách matched/unmatched. Tính so sánh trên tập cặp chung; thiếu dữ liệu ghi thiếu, không đổi hash/đầu vào để ép khớp và không gán failed-content cho lỗi fixture.
- Báo số tiên quyết có Q, số cặp `(bài, tiên quyết)` có bridge đạt, số bị bỏ K10/K11/K12 với mẫu số rõ ràng. Không lấy số item bridge trùng làm số tiên quyết được phủ.
- Kiểm metric từ ledger timing thật, bỏ dòng phát lại/duplicate, ghi n cùng p50/p90 và quy tắc percentile. Viết kiến nghị S2/S3 và retry temperature để chủ dự án quyết; chưa tự đổi thiết kế.
- Nếu cần hoàn tất đủ 12 cặp bằng lời gọi mới: ghim mẫu/cấu hình sau SA-49, dry-run riêng số call/USD/trần cứng (gồm retry mạng), xin duyệt rồi mới chạy. Dữ liệu thiếu do prompt mới không thể được tạo thêm bằng phát lại 0 USD.

## Tiêu chí nghiệm thu

- [ ] Test với fixture giả có một cặp lệch prompt: runner báo unmatched riêng, không đếm là lỗi nội dung hoặc đưa vào mẫu so nhiệt độ; cùng lần đầu chỉ tính tiền một lần. Test đỏ trên cách tổng hợp sai trước khi xanh.
- [ ] Test metric bỏ replay/duplicate và tách thời gian click của người học khỏi timestamp sinh; dùng bộ số biết trước để kiểm độc lập p50/p90.
- [ ] Báo cáo 0 USD có bảng đủ 12 mẫu và tập cặp thực sự so được; mọi số đọc lại từ artifact, không chỉ chép báo cáo cũ.
- [ ] Nếu chạy bổ sung: có dry-run + duyệt trước, ghi đầy đủ phản hồi/usage và giới hạn chi. Chưa được duyệt thì dừng phần có tiền và bàn giao rõ phần còn thiếu.
- [ ] Người soát đọc cả 12 bài và câu nối/recall, ghi đề xuất S2/S3/retry theo số liệu; không coi `ready` là chứng nhận đúng ngữ nghĩa.

## Ngoài vé

Không mở tập giữ lại, không thay mô hình, không tái sử dụng phê duyệt SA-43 cho lượt mới, không viết lại nội dung recording cũ. Không tự sửa spec/ADR.
