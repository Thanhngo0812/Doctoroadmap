"""Điều phối lượt chạy (vé DG-08, spec mục 13), thuộc seam xuất.

Một lệnh `python -m danhgia luot` chạy một biến thể trên một cuốn trong một **thư mục lượt**:

    DIR/ban-ghi-luot.json   bản ghi lượt (commit, hash cấu hình, mô hình, transport, seed, ngày, các bước đã xong)
    DIR/kho/                kho artifact riêng của lượt (DOC2ROADMAP_ARTIFACT_DIR); không bao giờ là `artifacts/` chung
    DIR/kho-pha-b.json      kho Pha B riêng (bản chép của kho/phase_b/live.json của chính lượt này)
    DIR/dry-run.json        dự toán trước khi chi
    DIR/so-chi.json         sổ chi thật, dựng từ usage ghi trong manifest các artifact của kho lượt
    DIR/hop-dong.json       hợp đồng `danh-gia-xuat-1` (kèm giây chạy, giây chờ embedding nếu có)
    DIR/bang-diem.json      bảng điểm (khi có vàng)

Chỉ `chay_cli.py`, `so_chi.py` và `uoc_chi.py` nhập mã pipeline; phần còn lại là điều phối thuần.
"""
