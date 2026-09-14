# 06 — Lọc khối phi ngôn ngữ và khối mục lục (F39)

**What to build:** Bốn chunk rác của báo cáo DOCX biến mất — hai chunk 99% dấu chấm (3.535 + 407
ký tự, dòng kẻ cho giảng viên viết tay) và hai chunk mục lục lặp toàn bộ tiêu đề kèm số trang —
mỗi khối bị loại để lại **một cảnh báo kèm đoạn đầu nguyên văn** để người vận hành kiểm được bộ lọc
không nuốt nhầm nội dung thật.

## Hai luật, chạy ở tầng dựng cấu trúc (sau chuẩn hoá, trước gộp)

- **Phi ngôn ngữ:** khối văn bản dài từ một ngưỡng ký tự trở lên mà tỉ lệ chữ-cái (Unicode letter)
  dưới ngưỡng ⇒ loại, cảnh báo `non_linguistic_block` kèm đoạn đầu. Ngưỡng độ dài tối thiểu bảo vệ
  dòng kỹ thuật ngắn (`x = 5` phải sống); dòng chấm dài phải chết.
- **Mục lục:** khối mà đa số dòng trùng nguyên văn một tiêu đề đã biết của **chính tài liệu đó**
  (bỏ qua số trang cuối dòng) ⇒ loại, cảnh báo `toc_block`. Dùng bằng chứng trong tài liệu — cùng
  triết lý luật tiêu-đề-lặp — **không** dùng danh sách tên mục lục của bất kỳ ngôn ngữ nào.

Node bị loại **vẫn nằm trong cây parse đóng băng** — chỉ tầng chunk bỏ. I23 không bị chạm: đây là
loại có cảnh báo, không phải bỏ im lặng.

**Blocked by:** 05 — cùng vùng dựng cấu trúc, làm nối tiếp; phiên bản tầng chunk đã nhích ở 05,
ticket này **không** nhích nữa.

**Status:** done

- [x] Có test: khối chấm dài bị loại kèm cảnh báo mang đoạn đầu; `x = 5` ngắn sống
- [x] Có test: khối lặp tiêu đề + số trang bị loại như mục lục; đoạn văn thường nhắc **một** tiêu đề
      giữa các câu **sống** (đa-số-dòng là ngưỡng, không phải chứa-là-chết)
- [x] Có test: tài liệu không có khối rác nào ⇒ không cảnh báo thừa
- [x] Trên fixture DOCX: đúng 4 chunk rác biến mất, số chunk 30 → 26 (± phần ticket 04 đã dồn),
      section MỤC LỤC và NHẬN XÉT vẫn tồn tại trong cây — chỉ nội dung rác của chúng bị loại
- [x] Không một câu văn bản thật nào biến mất: tổng ký tự chữ-cái của các chunk trước/sau chỉ được
      lệch đúng phần rác đã loại
- [x] Số vàng: DOCX đổi đúng cột chunk và cảnh báo; **ba tài liệu kia đứng yên** (hai giáo trình và
      slide không có khối nào rơi vào hai luật — nếu có, dừng và tìm ra vì sao)
