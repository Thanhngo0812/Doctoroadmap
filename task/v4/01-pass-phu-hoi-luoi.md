# v4-01 — A8 pass phụ hỏi lười thứ tự thứ hai

**Nguồn chân lý:** [nghiên cứu tiền và thời gian](../../report/nghien-cuu-v4-chi-phi-thoi-gian-2026-10-04.md), mục 4A · **Ai:** nhân viên ·
**Phụ thuộc:** — · **Chi phí mô hình:** 0 (nghiệm thu bằng phát lại nhật ký)

**Trạng thái:** đã triển khai và phát lại đủ 5 tài liệu (0 USD); chờ chốt điều kiện nghiệm thu về 4 cờ chẩn đoán. Cạnh và lộ trình y hệt. Xem [báo cáo](../../report/v4-01-02-nghiem-thu-2026-10-04.md).

## Vì sao (Claude, 2026-10-04)
- Pass phụ chiếm 91% tiền của một giáo trình trọn cuốn (doc-4: 45,9/50,4 USD).
- Mỗi cặp đang được hỏi hai lần, theo hai thứ tự trình bày, rồi gộp bằng `reconcile_pair_verdicts` (`domain/secondary.py`):
  - hai quyết định khác nhau → hoãn (`inconsistent_orders`);
  - có một bên lỗi sau mọi lần thử lại → hoãn (`invalid_or_outside_dossier`);
  - cùng "không quan hệ" → loại.
- Hệ quả, do mã bảo đảm: **thứ tự đầu nói "không quan hệ", hoặc lỗi, thì cặp chắc chắn không ra cạnh**, dù thứ tự sau trả gì.
- Phát lại trên nhật ký năm tài liệu: bỏ thứ tự sau khi thứ tự đầu nói "không" bớt 19–38% bản ghi lời gọi, **0 cạnh mất** (bảng ở báo cáo).

## Việc cần làm
- Với mỗi cặp: hỏi thứ tự đầu (`_left`) trước.
  - Nếu thứ tự đầu hợp lệ và quyết định không phải `create` → chốt bằng chính phán quyết đó, **không hỏi thứ tự sau**.
  - Nếu thứ tự đầu lỗi sau mọi lần thử lại → chốt hoãn như hiện nay, không hỏi thứ tự sau.
  - Nếu thứ tự đầu là `create` → hỏi thứ tự sau, gộp bằng `reconcile_pair_verdicts` như cũ.
- Giữ bảo đảm của vé 22: song song cấu hình được, **chốt theo thứ tự cặp**, kết quả y hệt chạy tuần tự. Thứ tự sau của một cặp chỉ gửi sau
  khi có kết quả thứ tự đầu của cặp đó; các cặp khác vẫn chạy song song.
- `secondary_log` ghi rõ cặp chốt sớm, ví dụ `reason: "first_order_final"`, để chẩn đoán tách được với loại "cả hai đều không".
- **Mẫu theo dõi độ lệch vị trí** (theo R-01): một mẫu 3% số cặp, chọn bằng băm `pair_id` với seed cố định, luôn hỏi đủ hai thứ tự. Mẫu này
  không đổi đầu ra (luật gộp như cũ) nhưng giữ được số đo độ lệch vị trí: báo tỉ lệ (không, có) và (có, không) theo tài liệu.
- Đổi `algorithm_id`/config của pass phụ để cache không lẫn với v3. Prompt, hồ sơ cặp và luật gộp giữ nguyên.

## Nghiệm thu
- **Test:**
  - thứ tự đầu "không" → đúng 1 lời gọi, phán quyết loại;
  - thứ tự đầu lỗi → không gọi thứ tự sau, phán quyết hoãn;
  - (create, create) cùng chiều → 2 lời gọi, cạnh như cũ; (create, không) → hoãn;
  - song song: kết quả và thứ tự chốt giống chạy tuần tự.
  - Hai test chốt sớm (thứ tự đầu "không", thứ tự đầu lỗi) phải đỏ trên mã hiện tại; các test còn lại giữ hành vi cũ.
- **Phát lại 0 USD** bằng mô hình giả trả đúng phản hồi đã ghi trong `decision_log`, trên doc-1, doc-2, nhap-mon-ml (kho
  `v3-r12-final-evaluation`), xstk v42 và doc-4 v8 (kho chính):
  - `secondary_edges` **y hệt** artifact hiện có;
  - A9 → A10 → tên module cho `sequence`, `requires_edges`, `modules` y hệt;
  - `secondary_flags` chỉ được giảm đúng số cặp (thứ tự đầu "không", thứ tự sau lỗi); báo số này;
  - báo số lời gọi bớt được mỗi tài liệu, phải khớp bảng của báo cáo (sai số do thử lại).
- **Tôi kiểm:** đọc diff, chạy test, tự phát lại một tài liệu.

## Bàn giao nhân viên — 2026-10-04

- `algorithm_id=a8-secondary-pass-lazy-v7`; lượt phải chỉ gửi sau khi lượt trái tạo cạnh (kể cả nhánh hạ xuống `cong_cu` sau sửa phản hồi).
- Giữ cửa sổ, tỉa động và thứ tự chốt của vé 22. Test `first_order_final` đã đỏ trên mã cũ; create/create, create/no và các cửa sổ
  1/4/50 tiếp tục qua.
- Phát lại xác nhận `secondary_edges`, `sequence`, `requires_edges`, `modules` y hệt trên cả 5 tài liệu. Không ghi đè artifact cũ.
- Có mâu thuẫn trong vé: luật triển khai bỏ lượt sau cho **mọi** quyết định không phải `create`, nhưng luật cờ nghiệm thu chỉ nhắc
  `no_direct_relation`. Doc-2 mất thêm 1 cờ sau `defer`, 1 sau `indirect_path`; doc-4 mất thêm 2 sau `indirect_path`. Đây đều là cờ
  `outside_or_invalid_secondary_edge` của lượt sau không còn chạy. Không thêm cờ và không mất cạnh.
- **Chưa tự sửa hợp đồng nghiệm thu:** đề nghị cho phép giảm cờ khi lượt đầu hợp lệ và không tạo cạnh, lượt sau cũ lỗi; đang chờ chủ dự án/sếp chốt.
- Bớt bản ghi hỏi mô hình: doc-1 2.194; doc-2 6.141; nhap-mon-ml 767; xstk 555; doc-4 17.029. Đây là số bản ghi, không phải số HTTP
  thực tế hay số phút đo được. Chênh với mục 4A được tách rõ trong báo cáo.
