#!/bin/bash

# script/capture_screenshots.sh <video_path>

VIDEO_PATH=$1
OUTPUT_DIR="data/screenshots"

if [ -z "$VIDEO_PATH" ]; then
    echo "Usage: $0 <video_path>"
    exit 1
fi

if [ ! -f "$VIDEO_PATH" ]; then
    echo "Error: File $VIDEO_PATH not found."
    exit 1
fi

# Create and clear output directory
mkdir -p "$OUTPUT_DIR"
rm -f "$OUTPUT_DIR"/*.jpg

# Get duration in seconds
DURATION=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$VIDEO_PATH")

if [ -z "$DURATION" ]; then
    echo "Error: Could not determine video duration."
    exit 1
fi

echo "Video duration: $DURATION seconds"

# Intervals: 10%, 30%, 50%, 70%, 90%
PERCENTAGES=(10 30 50 70 90)

for P in "${PERCENTAGES[@]}"; do
    # Use awk for floating point math
    TIMESTAMP=$(awk "BEGIN {print $DURATION * $P / 100}")
    OUTPUT_FILE="$OUTPUT_DIR/screenshot_${P}pct.jpg"
    
    echo "Capturing screenshot at $P% ($TIMESTAMP seconds)..."
    
    # -ss before -i for faster seeking
    ffmpeg -ss "$TIMESTAMP" -i "$VIDEO_PATH" -frames:v 1 -q:v 2 "$OUTPUT_FILE" -y -loglevel error
done

echo "Done! Screenshots saved to $OUTPUT_DIR"
ls -lh "$OUTPUT_DIR"
