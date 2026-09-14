# 08 — Cảnh báo khử theo chuỗi đầy đủ và I25 lý do vượt trần (F34 + F29)

**What to build:** Hai món nợ quan sát được trả cùng nhau:

**Một.** Người vận hành mở danh sách cảnh báo của slide thấy `rejected_heading_repeated: Naïve Bayes
Classification ×7` — **một dòng**, không phải bảy dòng giống hệt. Đây là chỗ hở F34 vòng 8 đã dự
đoán nguyên văn (*"cùng một tiêu đề lặp ở nhiều chương sẽ làm ngập lại"*) và slide vừa làm đúng thế.

**Hai.** Mọi chunk vượt trần áp dụng cho nó mang `oversize_reason` gọi tên đường vượt — không còn
vượt trần im lặng.

## Luật

- **Khử theo chuỗi đầy đủ, bỏ miễn-trừ-theo-loại:** hai dòng giống hệt từng ký tự ⇒ một dòng `×N`;
  khác bất kỳ đâu — kể cả chỉ khác nguyên văn kèm theo — ⇒ giữ riêng. Đây là cách sửa đã chốt trong
  biên bản vòng 8: vừa giữ nguyên văn từng ca, vừa không ngập. Thứ tự ổn định giữa hai lần chạy
  giữ nguyên.
- **Bất biến mới I25:** chunk có số token vượt **trần áp dụng cho nó** (512 văn xuôi; 2048 khi nhóm
  chứa bảng) ⇒ `oversize_reason` khác rỗng, gọi tên đường vượt — câu-không-có-ranh,
  bảng-giữ-nguyên, trần-cứng-ép-cắt. Trong trần ⇒ rỗng. Trần cứng 6000 và I20 không đổi.

**Blocked by:** 06 — cùng tầng chunk, làm nối tiếp; phiên bản đã nhích ở 05, ticket này **không**
nhích nữa.

**Status:** done

- [x] Có test: 300 cảnh báo giống hệt cả nguyên văn ⇒ một dòng `×300` — ca F34 nguyên bản
- [x] Có test: hai cảnh báo cùng loại khác nguyên văn ⇒ giữ đủ cả hai — lời hứa vòng 8 không đổ
- [x] Có test: cảnh báo hiếm lẫn giữa đống lặp ⇒ vẫn nhìn thấy
- [x] I25 có test ở seam thuần: chunk bảng 513 token mang lý do bảng-giữ-nguyên; chunk câu dài
      không ranh mang lý do của nó; chunk trong trần mang rỗng
- [x] Trên fixture slide: danh sách cảnh báo còn đọc được trong một màn hình, dòng `×7` xuất hiện;
      chunk bảng 513 token có `oversize_reason`
- [x] Số vàng: cột cảnh báo của slide và hai giáo trình co lại đúng phần trùng nguyên văn;
      số section/chunk/tham chiếu **mọi tài liệu đứng yên** — ticket này không được đổi nội dung
