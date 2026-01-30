#!/bin/zsh

# Use ffmpeg-full which includes libass for subtitle burning
export PATH="/usr/local/opt/ffmpeg-full/bin:$PATH"

python -m src.subtitles \
  --script data/karaoke/script1_es.txt \
  --bg  data/temp/final_fixed.mp4\
  --output data/temp/final.mp4 \
  --lang es-ES