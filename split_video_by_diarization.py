import pandas as pd
from moviepy.video.io.VideoFileClip import VideoFileClip
import os

# Parameters
mp4_file = 'Shake_It_Off.mp4'
diary_csv = 'diarization_111.csv'
output_dir = 'segments'

# Create output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

# Read diarization CSV
df = pd.read_csv(diary_csv)

# Load video
video = VideoFileClip(mp4_file)

# Iterate and cut segments
for idx, row in df.iterrows():
    start = float(row['start'])
    end = float(row['end'])
    speaker = str(row['speaker'])
    segment = video.subclip(start, end)
    out_name = f"segment_{start:.2f}_{end:.2f}_speaker_{speaker}.mp4"
    out_path = os.path.join(output_dir, out_name)
    segment.write_videofile(out_path, codec="libx264", audio_codec="aac", verbose=False, logger=None)

video.close()
print(f"Done splitting video. Segments saved in '{output_dir}' directory.") 