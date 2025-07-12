"""
File handling operations for the Audio Diarization Splitter.
Handles file uploads, saves, and ZIP creation with clean separation of concerns.
"""

import os
import tempfile
import zipfile
from typing import Tuple
import pandas as pd
from models import AudioFile, DiarizationData


class FileHandler:
    """Handles all file operations for the application."""
    
    def __init__(self, temp_directory: str = None):
        """Initialize file handler with optional temp directory."""
        self.temp_directory = temp_directory or tempfile.mkdtemp()
    
    def save_uploaded_audio(self, uploaded_file) -> AudioFile:
        """Save uploaded audio file and return AudioFile object."""
        file_path = os.path.join(self.temp_directory, uploaded_file.name)
        
        with open(file_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        
        return AudioFile(
            name=uploaded_file.name,
            content=uploaded_file.getbuffer(),
            file_path=file_path
        )
    
    def load_diarization_csv(self, uploaded_file) -> DiarizationData:
        """Load diarization data from uploaded CSV file."""
        # Reset file pointer to beginning
        uploaded_file.seek(0)
        
        try:
            dataframe = pd.read_csv(uploaded_file)
            return DiarizationData(
                dataframe=dataframe,
                file_name=uploaded_file.name
            )
        except Exception as e:
            raise ValueError(f"Failed to read CSV file: {str(e)}")
    
    def create_speaker_directories(self, output_dir: str, speakers: list) -> None:
        """Create directories for each speaker."""
        for speaker in speakers:
            speaker_dir = os.path.join(output_dir, str(speaker))
            os.makedirs(speaker_dir, exist_ok=True)
    
    def save_audio_segment(self, audio_data: bytes, output_path: str) -> None:
        """Save audio segment to file."""
        with open(output_path, 'wb') as f:
            f.write(audio_data)
    
    def create_zip_package(self, source_directory: str) -> bytes:
        """Create ZIP file from directory and return as bytes."""
        zip_path = os.path.join(self.temp_directory, "segments.zip")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(source_directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, source_directory)
                    zipf.write(file_path, arcname)
        
        with open(zip_path, 'rb') as f:
            return f.read()
    
    def cleanup(self) -> None:
        """Clean up temporary files."""
        if os.path.exists(self.temp_directory):
            import shutil
            shutil.rmtree(self.temp_directory)
    
    def get_file_size_mb(self, file_path: str) -> float:
        """Get file size in megabytes."""
        return os.path.getsize(file_path) / (1024 * 1024)
    
    def is_valid_audio_file(self, file_name: str) -> bool:
        """Check if file is a valid audio file."""
        valid_extensions = ['.mp3', '.wav', '.m4a', '.flac']
        return any(file_name.lower().endswith(ext) for ext in valid_extensions)
    
    def is_valid_csv_file(self, file_name: str) -> bool:
        """Check if file is a valid CSV file."""
        return file_name.lower().endswith('.csv') 