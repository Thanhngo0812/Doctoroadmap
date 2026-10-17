#!/bin/sh
# T-01b: nhánh A (v3, 2c93c5a) rồi nhánh B (gộp, 36b81ff) trên d01-t01, d01-t02. Dừng nếu lỗi hoặc một bước vượt ngưỡng chi.
export PYTHONIOENCODING=utf-8
L=tmp/t01b/chay.log
P=.venv/Scripts/python.exe
last() { ls artifacts/$1/$2 2>/dev/null | sed 's/^v//' | sort -n | tail -1; }
run() { tag=$1; kind=$2; doc=$3; cap=$4; shift 4
  before=$(last $kind $doc); before=${before:-0}; s=$(date +%s); echo "$tag bat-dau=$(date -Iseconds) truoc=v$before" >> $L
  $P scripts/t01/chay_t01b.py "$@" > tmp/t01b/$tag.json 2> tmp/t01b/$tag.err; rc=$?
  usd=$($P scripts/t01/chi_buoc.py $kind $doc $before)
  echo "$tag exit=$rc giay=$(( $(date +%s) - s )) usd=$usd tran=$cap sau=v$(last $kind $doc)" >> $L
  [ $rc -ne 0 ] && { echo "DUNG: $tag loi" >> $L; exit 1; }
  awk -v u=$usd -v c=$cap 'BEGIN{exit !(u>c)}' && { echo "DUNG: $tag vuot tran" >> $L; exit 2; }
  return 0; }
run A-rm-t01 graph d01-t01 1.9 v3 roadmap --doc-id d01-t01 --allow-spend
run A-rm-t02 graph d01-t02 2.1 v3 roadmap --doc-id d01-t02 --allow-spend
run B-a4-t01 canonical d01-t01 0.75 gop a4 --doc-id d01-t01 --gold tests/fixtures/a4/gold-blind.json --no-gold-for-doc --language vi --allow-spend
run B-rm-t01 graph d01-t01 1.2 gop roadmap --doc-id d01-t01 --allow-spend
run B-a4-t02 canonical d01-t02 0.8 gop a4 --doc-id d01-t02 --gold tests/fixtures/a4/gold-blind.json --no-gold-for-doc --language vi --allow-spend
run B-rm-t02 graph d01-t02 1.35 gop roadmap --doc-id d01-t02 --allow-spend
echo "XONG $(date -Iseconds)" >> $L
