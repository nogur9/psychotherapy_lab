"""
Data models for the Audio Diarization Splitter application.
Contains clean, simple data structures that represent the domain concepts.
"""

from dataclasses import dataclass
from typing import List, Dict, Any
import pandas as pd


@dataclass
class AudioSegment:
    """Represents a single audio segment with timing and speaker information."""
    start_time: float
    end_time: float
    speaker: str
    segment_id: str = None
    
    def __post_init__(self):
        """Generate segment ID if not provided."""
        if self.segment_id is None:
            self.segment_id = f"{self.start_time:.2f}_{self.end_time:.2f}"
    
    @property
    def duration(self) -> float:
        """Calculate the duration of this segment."""
        return self.end_time - self.start_time


@dataclass
class ProcessingResult:
    """Represents the result of audio processing."""
    total_segments: int
    processed_segments: int
    speakers: List[str]
    output_directory: str
    zip_data: bytes = None
    
    @property
    def success_rate(self) -> float:
        """Calculate the success rate of processing."""
        if self.total_segments == 0:
            return 0.0
        return self.processed_segments / self.total_segments


@dataclass
class AudioFile:
    """Represents an uploaded audio file."""
    name: str
    content: bytes
    file_path: str = None
    
    @property
    def size_bytes(self) -> int:
        """Get the size of the audio file in bytes."""
        return len(self.content)


@dataclass
class DiarizationData:
    """Represents diarization data from CSV file."""
    dataframe: pd.DataFrame
    file_name: str
    
    @property
    def total_segments(self) -> int:
        """Get the total number of segments."""
        return len(self.dataframe)
    
    @property
    def unique_speakers(self) -> List[str]:
        """Get list of unique speakers."""
        return self.dataframe['speaker'].unique().tolist()
    
    @property
    def total_duration(self) -> float:
        """Get the total duration of all segments."""
        return self.dataframe['end'].max()
    
    def get_segments_for_speaker(self, speaker: str) -> List[AudioSegment]:
        """Get all segments for a specific speaker."""
        speaker_data = self.dataframe[self.dataframe['speaker'] == speaker]
        return [
            AudioSegment(
                start_time=row['start'],
                end_time=row['end'],
                speaker=row['speaker']
            )
            for _, row in speaker_data.iterrows()
        ]
    
    def validate(self) -> List[str]:
        """Validate the diarization data and return list of errors."""
        errors = []
        
        # Check required columns
        required_columns = ['start', 'end', 'speaker']
        missing_columns = [col for col in required_columns if col not in self.dataframe.columns]
        if missing_columns:
            errors.append(f"Missing required columns: {', '.join(missing_columns)}")
        
        # Check for empty dataframe
        if self.dataframe.empty:
            errors.append("CSV file is empty")
            return errors
        
        # Check for negative times
        if (self.dataframe['start'] < 0).any() or (self.dataframe['end'] < 0).any():
            errors.append("Found negative time values")
        
        # Check for invalid time ranges
        if (self.dataframe['end'] <= self.dataframe['start']).any():
            errors.append("Found segments where end time <= start time")
        
        return errors 