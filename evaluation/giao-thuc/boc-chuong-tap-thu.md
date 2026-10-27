# Giao thức bốc chương tập thử

**Phiên bản:** boc-1 · **Chốt:** 2026-10-27, trước khi lập danh sách chương của bất kỳ cuốn thử nào · **Người giữ:** Claude

Tệp này được commit **trước** khi người giữ mở mục lục các cuốn thử. Hash commit là bằng chứng luật, N và seed có trước danh sách chương, nên không thể chọn
seed hay N theo kết quả bốc. Spec mục 4; kế hoạch mục 5; Q36, Q37.

## Tham số

| Tham số | Giá trị |
|---|---|
| seed | `20261027`, dùng chung cho mọi cuốn thử |
| N (số trang tối thiểu của chương hợp lệ) | 5 trang PDF |
| số chương bốc mỗi cuốn | 3: một ở phần đầu, một ở phần giữa, một ở phần cuối |
| lệnh | `python -m danhgia.bo_sach boc <manifest> --seed 20261027 --n-trang 5` |

## Đơn vị "chương"

- Chương là mục cấp cao nhất có đánh số trong mục lục in, ví dụ "Chương 3", "Bài 3", "Chủ đề 3". Sách có cấp "Phần" bọc ngoài chương thì đơn vị vẫn là chương.
- Trang đầu của chương là trang PDF chứa tiêu đề chương. Trang cuối là trang ngay trước tiêu đề của chương kế tiếp, hoặc của mục cuối sách kế tiếp.
- Số trang là trang của tệp PDF, đánh từ 1, không phải số in trên sách.
- **Dự phòng:** cuốn nào có dưới 3 chương hợp lệ thì đơn vị đổi xuống mục cấp hai có đánh số (ví dụ 2.1, 2.2), N = 3, cùng seed. Cách đổi này ghi trong
  manifest của cuốn đó.

## Phân loại chương, chỉ theo tên trong mục lục

Luật lọc không đọc nội dung chương và không nhìn đầu ra máy. Loại được xác định từ tên chương, sau khi bỏ tiền tố "Chương N:":

| Loại | Tên chương |
|---|---|
| `mo_dau` | phần trước chương thứ nhất (bìa, mục lục, lời nói đầu); chương có tên đúng là "Mở đầu", "Lời mở đầu", "Lời nói đầu", "Giới thiệu", "Giới thiệu chung" hay "Nhập đề" |
| `bai_tap` | tên bắt đầu bằng "Bài tập", "Câu hỏi", "Đáp án", "Ôn tập" hay "Hướng dẫn giải" |
| `phu_luc` | tên bắt đầu bằng "Phụ lục", "Tài liệu tham khảo", "Chỉ mục", "Bảng tra" hay "Thuật ngữ" |
| `noi_dung` | mọi chương còn lại |

Chương hợp lệ là chương `noi_dung` dài từ N trang trở lên. Các chương hợp lệ, theo thứ tự sách, được chia thành ba phần liền nhau gần bằng nhau. Mỗi phần bốc một
chương bằng LCG tất định theo seed (mã ở `evaluation/danhgia/bo_sach.py`).

## Lưu giữ

- Manifest tập thử nằm ở sổ người giữ ngoài repo, cùng PDF. Repo chỉ giữ SHA-256 của manifest và PDF.
- Agent và sinh viên không được biết đường dẫn của sổ.
- Cuốn nào bị thay (vi phạm điều kiện chọn sách) thì cuốn thay dùng đúng giao thức này, không đổi seed hay N.
