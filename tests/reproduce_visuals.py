
import asyncio
from pathlib import Path
from src.subtitles.ass_generator import ASSGenerator
from src.subtitles.renderer import KaraokeRenderer
from src.subtitles.models import SubtitleEvent, WordBoundary, SubtitleStyle, RendererConfig

def create_sample_events():
    # "Hello World Test"
    # Total 1.5 seconds
    words = [
        WordBoundary(text="Hello", audio_offset_ms=100, duration_ms=400),
        WordBoundary(text="World", audio_offset_ms=600, duration_ms=400),
        WordBoundary(text="Test", audio_offset_ms=1100, duration_ms=300),
    ]
    event = SubtitleEvent(start_time_ms=0, end_time_ms=1500, words=words)
    return [event]

def main():
    base_dir = Path("tests")
    output_ass = base_dir / "test.ass"
    bg_video = base_dir / "dummy_bg.mp4"
    output_video = base_dir / "test_output.mp4"
    
    # 1. Generate ASS
    print("Generating ASS...")
    style = SubtitleStyle()
    # Ensure rounded box settings are active
    style.use_box_highlight = True
    style.box_radius = 20.0
    style.box_blur = 8.0
    
    generator = ASSGenerator(style)
    events = create_sample_events()
    generator.generate(events, output_ass)
    print(f"ASS generated at {output_ass}")
    
    # 2. Render Video
    print("Rendering Video...")
    renderer_config = RendererConfig()
    renderer = KaraokeRenderer(renderer_config)
    
    # We need a dummy audio file too, or silence
    # Renderer expects audio path. Let's create a silent mp3 or just use the video as audio source (it has no audio)
    # The renderer might fail if audio is missing. Let's check renderer.py
    # But for now let's try generating a silent audio
    
    # Actually, let's just create a silent mp3
    # ffmpeg -f lavfi -i anullsrc=r=44100:cl=mono -t 2 -q:a 9 -acodec libmp3lame tests/silence.mp3
    
    # Assuming silence.mp3 exists (I will run the command separately)
    audio_path = base_dir / "silence.mp3"
    
    renderer.render_video(
        background_video=bg_video,
        audio=audio_path,
        subtitles=output_ass,
        output=output_video,
        target_duration_ms=2000
    )
    print(f"Video rendered at {output_video}")

if __name__ == "__main__":
    main()
