#!/bin/bash
# E6 trên máy GPU: chạy tuần tự các lượt trong `~/e6/hang-doi.txt`, mỗi dòng "<tên lượt> <tham số cho e6_cross_encoder.py>".
# Chạy dưới systemd-inhibit --what=idle (qua SSH chỉ được chặn idle; chặn ngủ và chặn gập máy cần xác thực tương tác): máy phải cắm sạc và
# không gập. TMPDIR trỏ sang ổ chính vì /tmp là tmpfs có hạn mức theo người dùng. Nếp đã xong thì e6_cross_encoder.py tự bỏ qua, nên chạy lại
# hàng đợi sau khi đứt là chạy tiếp.
#   cd ~/e6 && (setsid nohup bash e6_chay_hang_doi.sh > nhat-ky/chay.out 2>&1 < /dev/null &)
export TMPDIR=$HOME/e6/tmp
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
cd "$HOME/e6" || exit 1
mkdir -p nhat-ky tmp
while read -r name args; do
  [ -z "$name" ] && continue
  case "$name" in \#*) continue ;; esac
  echo "$(date '+%F %T') bat dau $name" >> nhat-ky/hang-doi.log
  systemd-inhibit --what=idle --who=e6 --why="E6 cross-encoder" --mode=block \
    venv/bin/python ma/e6_cross_encoder.py --luot="$name" $args >> "nhat-ky/$name.log" 2>&1 < /dev/null
  echo "$(date '+%F %T') xong $name (ma thoat $?)" >> nhat-ky/hang-doi.log
done < hang-doi.txt
echo "$(date '+%F %T') HET HANG DOI" >> nhat-ky/hang-doi.log
