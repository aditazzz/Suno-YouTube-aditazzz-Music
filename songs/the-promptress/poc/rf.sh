#!/bin/bash
# one render pass (<=166 s): split the missing frames of the film into 3 equal contiguous chunks and render them in parallel
cd "$(dirname "$0")/.."; export TMPDIR=$PWD/build/_tmp; O=${1:-build/film/frames}; mkdir -p $O
for f in $O/*.tmp.jpg; do [ -e "$f" ] && mv "$f" build/_bad1/ 2>/dev/null; done
R=$(python3 -c "
import os; NF=int(os.environ.get('NFMAX','8052')); m=[f for f in range(NF) if not os.path.exists('$O/%05d.jpg'%f)]
if not m: print('DONE')
else:
  k=max(1,len(m)//3); cuts=[m[0], m[min(k,len(m)-1)], m[min(2*k,len(m)-1)], NF]
  print(' '.join(f'{cuts[i]}:{cuts[i+1]}' for i in range(3)))")
[ "$R" = "DONE" ] && { echo DONE; exit 0; }
for r in $R; do timeout 155 python3 poc/film.py $O ${r%%:*} ${r##*:} > /dev/null 2>>build/film/render_err.log & done; wait
echo "$(ls $O | grep -v tmp | wc -l) / 8052"
