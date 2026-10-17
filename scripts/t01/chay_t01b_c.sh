#!/bin/sh
# T-01b nhánh C (gộp + luật 05a, mã 8655791 có 05c) trên d01-t02. Dừng nếu lỗi, vượt trần chi, hoặc canonical không dùng bản nhãn mới.
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
run C-roles-t02 chunks d01-t02 0.05 gop05c label-roles --doc-id d01-t02 --allow-spend
NEW=$(last chunks d01-t02)
$P scripts/t01/chay_t01b.py gop05c a4 --doc-id d01-t02 --gold tests/fixtures/a4/gold-blind.json --no-gold-for-doc --language vi --dry-run > tmp/t01b/C-a4-dry.json 2> tmp/t01b/C-a4-dry.err
$P -c "import json,sys; n=json.load(open('tmp/t01b/C-a4-dry.json',encoding='utf-8'))['phases']['anchor']['note']; sys.exit(0 if 'anchor_chunks_version=$NEW' in n else 3)" \
  || { echo "DUNG: C canonical khong dung ban nhan moi v$NEW" >> $L; exit 3; }
echo "C-a4-dry dung-nhan=v$NEW" >> $L
run C-a4-t02 canonical d01-t02 0.3 gop05c a4 --doc-id d01-t02 --gold tests/fixtures/a4/gold-blind.json --no-gold-for-doc --language vi --allow-spend
run C-rm-t02 graph d01-t02 1.35 gop05c roadmap --doc-id d01-t02 --allow-spend
echo "XONG-C $(date -Iseconds)" >> $L
