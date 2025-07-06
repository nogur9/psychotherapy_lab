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

for speaker in df['speaker'].unique():
    os.makedirs(os.path.join(output_dir, str(speaker)), exist_ok=True)

os.makedirs(output_dir, exist_ok=True)
# Load video
video = VideoFileClip(mp4_file)

# Iterate and cut segments
for idx, row in df.iterrows():
    start = float(row['start'])
    end = float(row['end'])
    if end > video.end:
        break
    speaker = str(row['speaker'])
    segment = video.subclipped(start_time = start, end_time=end)
    out_name = f"segment_{start:.2f}_{end:.2f}.mp4"
    out_path = os.path.join(output_dir, speaker, out_name)
    segment.write_videofile(out_path, codec="libx264", audio_codec="aac")

video.close()
print(f"Done splitting video. Segments saved in '{output_dir}' directory.")

#
# if __name__ == "__main__":
#