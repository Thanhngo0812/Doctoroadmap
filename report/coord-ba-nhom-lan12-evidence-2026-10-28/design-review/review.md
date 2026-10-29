# Soát W-23 lần 12

Ghim f9705f4299ffd360de8c11861848689b3233503c. **Ghi nhận phần ảnh/copy/decoded PNG/nhãn nguồn đã sửa; chưa nhận cả lát, toàn W-23 mở. Không Cloud Figma.**

Đúng:9PNG hash/bytes,3crop pixel chính xác,3source rawCRLF/GitLF,decoded dimensions808x62/808x154/366x808. Root trích/băm độc lập4khối JSX/CSS được nêu:W08 self-check và W10 filters/list/rules đều giốngbyte; đây là bằng chứng source hẹp, không chứng minh toàn component/ảnh hiện tại chưa đổi.

**D-R12-01 Required:** script điền hằng reactActualMetrics/measuredHeight và leafSourceValid/diff=0, không mở React hoặc đọc source React. Probe chạy offline khi scratch không có src React, các hằng vẫn được xuất. Kiểm assert_submitted_react_metrics_equal_fresh_runtime native1,4 mismatches trên số đo DOM mới:tab44→45,cardwidth332→358,padding16→16px0,h2weight700→600. Font primary được CDP xác nhận customBeVietnamPro Regular/SemiBold; không lấy fallback để cáo buộc khác biệt font thương hiệu. Min-height44 chỉ là ràng buộc CSS, không phải measured height.

Root đã cung cấp3PNG/JSON hiện tại bằng HTTP/auth/PostgreSQL và core thật với Fake providers; source34c1712f,2viewports/2theme,khốigập/mở. Hai run tách riêng:font dự phòng chặnHTTPngoài và font thương hiệu chỉ choGooglefontassets; không chép metric/font giữa run. 0USD,không pageerror; không gọi đây là kiểm toàn bộ W23 hoặc nghiệm thu adminReact.

URL lịch sử được khai /courses/c1/modules/m1/... không khớp actual course UUID và route/module trong runtime gốc. Lấy URL thực từ receipt mới hoặc lịch sử, không gán URL minh hoạ thành URL capture.

Script nay giữ PNG canonical nếu tồn tại nhưng tính metrics/font từ trang fresh. Offline HTMLW10 currentheight770 so với canonical CSSheight807/PNG808; câu fallback không đổi boundingbox không đúng. Phân biệt canonical provenance với reproduction run hoặc dùng ảnh/metrics mới cùngrun.

Cách sửa ngắn: dùng current-react-metrics.json và PNG điều phối bàn giao; sửa script để thật sự đọc DOM, hoặc đổi nhãn hằng thành ước theo source và không dùng làm chứng nhận thực đo. Kiểm source bằng trích/băm thật hoặc dẫn independent-leaf-reuse.json. Không sửa React cho giống số đã ghi sai. Không làm lại token/branding/math hoặc mở Cloud; sau hồ sơ này mở rộng W08/09/10/768/keyboard/motion/video còn thiếu. Đề xuất2/3tab và cách đặt câu hỏi vẫn mở.
