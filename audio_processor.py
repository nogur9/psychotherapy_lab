"""
Audio processing logic for the Audio Diarization Splitter.
Handles audio loading, segmentation, and export with clean separation of concerns.
"""

import os
import librosa
import soundfile as sf
import numpy as np
from typing import List, Tuple, Optional
from models import AudioSegment, ProcessingResult, AudioFile, DiarizationData
from file_handler import FileHandler


class AudioProcessor:
    """Handles all audio processing operations."""
    
    def __init__(self, file_handler: FileHandler):
        """Initialize audio processor with file handler."""
        self.file_handler = file_handler
        self.audio_data = None
        self.sample_rate = None
    
    def load_audio(self, audio_file: AudioFile) -> None:
        """Load audio file into memory."""
        if not os.path.exists(audio_file.file_path):
            raise FileNotFoundError(f"Audio file not found: {audio_file.file_path}")
        
        self.audio_data, self.sample_rate = librosa.load(
            audio_file.file_path, 
            sr=None
        )
    
    def get_audio_duration(self) -> float:
        """Get the duration of the loaded audio in seconds."""
        if self.audio_data is None:
            raise ValueError("No audio loaded. Call load_audio() first.")
        return len(self.audio_data) / self.sample_rate
    
    def extract_segment(self, segment: AudioSegment) -> np.ndarray:
        """Extract a specific segment from the audio."""
        if self.audio_data is None:
            raise ValueError("No audio loaded. Call load_audio() first.")
        
        start_sample = int(segment.start_time * self.sample_rate)
        end_sample = int(segment.end_time * self.sample_rate)
        
        # Ensure we don't go beyond audio length
        end_sample = min(end_sample, len(self.audio_data))
        
        return self.audio_data[start_sample:end_sample]
    
    def save_segment(self, segment_data: np.ndarray, output_path: str) -> None:
        """Save audio segment to WAV file."""
        sf.write(output_path, segment_data, self.sample_rate)
    
    def process_all_segments(
        self, 
        diarization_data: DiarizationData,
        output_directory: str,
        progress_callback=None
    ) -> ProcessingResult:
        """Process all segments and return processing result."""
        if self.audio_data is None:
            raise ValueError("No audio loaded. Call load_audio() first.")
        
        # Create speaker directories
        self.file_handler.create_speaker_directories(
            output_directory, 
            diarization_data.unique_speakers
        )
        
        total_segments = diarization_data.total_segments
        processed_segments = 0
        audio_duration = self.get_audio_duration()
        
        for idx, row in diarization_data.dataframe.iterrows():
            # Create segment object
            segment = AudioSegment(
                start_time=float(row['start']),
                end_time=float(row['end']),
                speaker=str(row['speaker'])
            )
            
            # Skip if segment extends beyond audio
            if segment.end_time > audio_duration:
                break
            
            # Extract and save segment
            segment_data = self.extract_segment(segment)
            output_filename = f"segment_{segment.segment_id}.wav"
            output_path = os.path.join(output_directory, segment.speaker, output_filename)
            
            self.save_segment(segment_data, output_path)
            
            processed_segments += 1
            
            # Update progress if callback provided
            if progress_callback:
                progress_callback(processed_segments, total_segments, segment.speaker)
        
        return ProcessingResult(
            total_segments=total_segments,
            processed_segments=processed_segments,
            speakers=diarization_data.unique_speakers,
            output_directory=output_directory
        )


class AudioProcessingService:
    """High-level service that orchestrates audio processing."""
    
    def __init__(self):
        """Initialize the audio processing service."""
        self.file_handler = FileHandler()
        self.audio_processor = AudioProcessor(self.file_handler)
    
    def process_audio_with_diarization(
        self,
        audio_file,
        diarization_file,
        progress_callback=None
    ) -> ProcessingResult:
        """Main method to process audio with diarization data."""
        try:
            # Load and validate files
            audio_file_obj = self.file_handler.save_uploaded_audio(audio_file)
            diarization_data = self.file_handler.load_diarization_csv(diarization_file)
            
            # Validate diarization data
            validation_errors = diarization_data.validate()
            if validation_errors:
                raise ValueError(f"Invalid diarization data: {'; '.join(validation_errors)}")
            
            # Load audio
            self.audio_processor.load_audio(audio_file_obj)
            
            # Create output directory
            output_dir = os.path.join(self.file_handler.temp_directory, "segments")
            os.makedirs(output_dir, exist_ok=True)
            
            # Process segments
            result = self.audio_processor.process_all_segments(
                diarization_data,
                output_dir,
                progress_callback
            )
            
            # Create ZIP package
            result.zip_data = self.file_handler.create_zip_package(output_dir)
            
            return result
            
        except Exception as e:
            # Clean up on error
            self.file_handler.cleanup()
            raise
    
    def cleanup(self):
        """Clean up temporary files."""
        self.file_handler.cleanup() 