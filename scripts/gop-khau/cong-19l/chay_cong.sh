#!/bin/sh
# Cổng 19l: A4 chuỗi gộp cho 5 tài liệu còn lại, rồi chuỗi đồ thị cho 3 tài liệu có vàng; mã từ worktree sạch của commit đã ghim.
export PYTHONIOENCODING=utf-8
L=tmp/v4-19l/chay.log
R="cổng 19l: cùng chunk đã chấm ở chuỗi v3; dòng VNI trang 3 là lỗi đã biết"
run() { tag=$1; shift; s=$(date +%s); echo "$tag bat-dau=$(date -Iseconds)" >> $L
  .venv/Scripts/python.exe scripts/gop-khau/cong-19l/chay_tu_commit.py "$@" > tmp/v4-19l/$tag.json 2> tmp/v4-19l/$tag.err; rc=$?
  echo "$tag exit=$rc giay=$(( $(date +%s) - s ))" | tee -a $L; [ $rc -ne 0 ] && tail -c 600 tmp/v4-19l/$tag.err; return $rc; }
for d in nhap-mon-ml naive-bayes doc-6 xstk-ch3-1 doc-4; do
  case $d in doc-6|doc-4) extra="--no-gold-for-doc --language vi";; *) extra="";; esac
  run a4-$d a4 --doc-id $d --gold artifacts/a4-gold.json $extra --upstream-chain gop --allow-spend
done
run rm-doc-1 roadmap --doc-id doc-1 --upstream-chain gop --allow-spend
run rm-xstk-ch3-1 roadmap --doc-id xstk-ch3-1 --upstream-chain gop --allow-spend --allow-text-quality-reason "$R"
run rm-doc-4 roadmap --doc-id doc-4 --upstream-chain gop --allow-spend
echo "XONG $(date -Iseconds)" >> $L
