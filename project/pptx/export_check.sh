#!/bin/zsh
# Opens ../presentation.pptx in Microsoft PowerPoint, exports PDF (PowerPoint's own renderer), rasterises pages to PNG.
PPTX="$(cd .. && pwd)/presentation.pptx"
CONT=~/Library/Containers/com.microsoft.Powerpoint/Data/Documents
rm -f $CONT/check.pdf
osascript <<OSA
tell application "Microsoft PowerPoint"
  close every presentation saving no
  open POSIX file "$PPTX"
  delay 3
  save active presentation in ((path to documents folder as text) & "check.pdf") as save as PDF
end tell
OSA
cp $CONT/check.pdf ../presentation.pdf
OUT=${1:-/private/tmp/claude-501/pcimg}; mkdir -p $OUT
uv run --with pymupdf python -W ignore -c "
import fitz
d=fitz.open('../presentation.pdf'); print(len(d),'pages')
for i,p in enumerate(d): p.get_pixmap(dpi=110).save('$OUT/p%d.png'%(i+1))
" 2>/dev/null
