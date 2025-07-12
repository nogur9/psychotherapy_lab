import pandas as pd
from moviepy.video.io.VideoFileClip import VideoFileClip
import os
import tempfile
import zipfile


def process_audio(_audio_file, _diarization_file):
    """Process the audio file and create segments by speaker"""
    
    diarization_data = _load_diarization_data(_diarization_file)
    _validate_diarization_data(diarization_data)

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            audio_path = _save_uploaded_file(_audio_file, temp_dir)
            audio_clip = _load_audio_file(audio_path)

            output_dir = _create_output_directory(temp_dir, diarization_data)
            processed_segments = _process_audio_segments(
                audio_clip, diarization_data, output_dir)
            
            audio_clip.close()
            
            zip_data = _create_download_package(output_dir)

    except Exception as e:
        _handle_processing_error(e)


def _load_diarization_data(diarization_file):
    """Load and return diarization data from CSV file"""
    return pd.read_csv(diarization_file).copy()


def _validate_diarization_data(diarization_data):
    """Validate that diarization data has required columns"""
    required_columns = ['start', 'end', 'speaker']
    missing_columns = [col for col in required_columns if col not in diarization_data.columns]
    
    if missing_columns:
        raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")


def _save_uploaded_file(uploaded_file, temp_dir):
    """Save uploaded file to temporary directory and return path"""
    file_path = os.path.join(temp_dir, uploaded_file.name)
    with open(file_path, 'wb') as f:
        f.write(uploaded_file.getbuffer())
    return file_path


def _load_audio_file(audio_path):
    """Load audio file using MoviePy"""
    return VideoFileClip(audio_path)


def _create_output_directory(temp_dir, diarization_data):
    """Create output directory structure for speakers"""
    output_dir = os.path.join(temp_dir, "segments")
    os.makedirs(output_dir, exist_ok=True)
    
    for speaker in diarization_data['speaker'].unique():
        speaker_dir = os.path.join(output_dir, str(speaker))
        os.makedirs(speaker_dir, exist_ok=True)
    
    return output_dir


def _process_audio_segments(audio_clip, diarization_data, output_dir):
    """Process audio segments and return count of processed segments"""
    total_segments = len(diarization_data)
    processed_segments = 0
    
    for idx, row in diarization_data.iterrows():
        start_time = float(row['start'])
        end_time = float(row['end'])
        
        if end_time > audio_clip.duration:
            break
        
        speaker = str(row['speaker'])
        segment = audio_clip.subclipped(start_time=start_time, end_time=end_time)
        
        output_filename = f"segment_{start_time:.2f}_{end_time:.2f}.mp3"
        output_path = os.path.join(output_dir, speaker, output_filename)
        
        segment.write_audiofile(
            output_path,
            verbose=False,
            logger=None
        )
        
        processed_segments += 1

    return processed_segments


def _create_download_package(output_dir):
    """Create ZIP file for download and return its data"""

    zip_path = os.path.join(output_dir, "..", "segments.zip")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, output_dir)
                zipf.write(file_path, arcname)

    
    with open(zip_path, 'rb') as f:
        return f.read()

def _handle_processing_error(error):
    """Handle and display processing errors"""
    raise ValueError(f"❌ Error during processing: {str(error)}")




def main (audio_file, diarization_file):

    # Preview diarization data
    df = pd.read_csv(diarization_file)

    # Check required columns
    required_columns = ['start', 'end', 'speaker']
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        raise ValueError(f"❌ Missing required columns: {', '.join(missing_columns)}")

    else:
        process_audio(audio_file, diarization_file)


if __name__ == "__main__":
    audio_file = "Taylor Swift - Shake It Off.mp3"
    diarization_file = "diarization_111.csv"
    main(audio_file, diarization_file)