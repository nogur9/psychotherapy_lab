import pandas as pd
from moviepy.video.io.VideoFileClip import VideoFileClip
import os
import tempfile
import zipfile
from typing import Optional, Tuple, Dict, Any
import streamlit as st


class VideoProcessor:
    """Handles video processing and segmentation based on diarization data."""
    
    def __init__(self):
        self.video: Optional[VideoFileClip] = None
        self.diarization_data: Optional[pd.DataFrame] = None
        self.temp_dir: Optional[str] = None
        
    def validate_diarization_data(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """Validate that the diarization CSV has required columns."""
        required_columns = ['start', 'end', 'speaker']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return False, f"Missing required columns: {', '.join(missing_columns)}"
        
        # Check for valid numeric values
        try:
            df['start'] = pd.to_numeric(df['start'])
            df['end'] = pd.to_numeric(df['end'])
        except ValueError:
            return False, "Start and end times must be numeric values"
        
        # Check for logical consistency
        if (df['end'] <= df['start']).any():
            return False, "End time must be greater than start time"
            
        return True, "Data validation successful"
    
    def load_video(self, video_path: str) -> bool:
        """Load video file into memory."""
        try:
            self.video = VideoFileClip(video_path)
            return True
        except Exception as e:
            st.error(f"Error loading video: {str(e)}")
            return False
    
    def load_diarization_data(self, csv_path: str) -> bool:
        """Load and validate diarization data."""
        try:
            self.diarization_data = pd.read_csv(csv_path)
            is_valid, message = self.validate_diarization_data(self.diarization_data)
            
            if not is_valid:
                st.error(f"Invalid diarization data: {message}")
                return False
                
            return True
        except Exception as e:
            st.error(f"Error loading diarization data: {str(e)}")
            return False
    
    def create_output_structure(self, output_dir: str) -> None:
        """Create directory structure for output segments."""
        os.makedirs(output_dir, exist_ok=True)
        
        # Create speaker directories
        for speaker in self.diarization_data['speaker'].unique():
            speaker_dir = os.path.join(output_dir, str(speaker))
            os.makedirs(speaker_dir, exist_ok=True)
    
    def process_segment(self, row: pd.Series, output_dir: str) -> bool:
        """Process a single video segment."""
        try:
            start = float(row['start'])
            end = float(row['end'])
            
            # Skip if segment extends beyond video
            if end > self.video.duration:
                return False
            
            speaker = str(row['speaker'])
            segment = self.video.subclipped(start_time=start, end_time=end)
            
            # Create output filename
            out_name = f"segment_{start:.2f}_{end:.2f}.mp4"
            out_path = os.path.join(output_dir, speaker, out_name)
            
            # Write segment
            segment.write_videofile(
                out_path,
                codec="libx264",
                audio_codec="aac",
                logger=None
            )
            
            return True
            
        except Exception as e:
            st.error(f"Error processing segment {start:.2f}-{end:.2f}: {str(e)}")
            return False
    
    def create_zip_archive(self, output_dir: str, zip_path: str) -> bool:
        """Create ZIP archive of processed segments."""
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(output_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, output_dir)
                        zipf.write(file_path, arcname)
            return True
        except Exception as e:
            st.error(f"Error creating ZIP archive: {str(e)}")
            return False
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get statistics about the processing results."""
        if self.diarization_data is None:
            return {}
        
        speaker_counts = self.diarization_data['speaker'].value_counts()
        
        return {
            'total_segments': len(self.diarization_data),
            'unique_speakers': int(self.diarization_data['speaker'].nunique()),
            'total_duration': float(self.diarization_data['end'].max()),
            'speaker_breakdown': speaker_counts.to_dict()
        }
    
    def cleanup(self) -> None:
        """Clean up resources."""
        if self.video:
            self.video.close()
            self.video = None
    
    def process_video_file(self, video_file, diarization_file, progress_callback=None):
        """Main method to process video with diarization data."""
        
        try:
            # Create temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                self.temp_dir = temp_dir
                
                if progress_callback:
                    progress_callback(10, "📁 Setting up temporary directory...")
                
                # Save uploaded files
                video_path = os.path.join(temp_dir, video_file.name)
                with open(video_path, 'wb') as f:
                    f.write(video_file.getbuffer())
                
                csv_path = os.path.join(temp_dir, "diarization.csv")
                with open(csv_path, 'wb') as f:
                    f.write(diarization_file.getbuffer())
                
                # Load files
                if progress_callback:
                    progress_callback(20, "🎬 Loading video file...")
                
                if not self.load_video(video_path):
                    return False, None
                
                if not self.load_diarization_data(csv_path):
                    return False, None
                
                # Process segments
                total_segments = len(self.diarization_data)
                if progress_callback:
                    progress_callback(30, f"✂️ Processing {total_segments} segments...")
                
                output_dir = os.path.join(temp_dir, "segments")
                self.create_output_structure(output_dir)
                
                processed_segments = 0
                for idx, row in self.diarization_data.iterrows():
                    if self.process_segment(row, output_dir):
                        processed_segments += 1
                    
                    # Update progress
                    if progress_callback:
                        progress = 30 + (processed_segments / total_segments) * 50
                        speaker = str(row['speaker'])
                        progress_callback(int(progress), f"✂️ Processing segment {processed_segments}/{total_segments} ({speaker})")
                
                # Create ZIP archive
                if progress_callback:
                    progress_callback(80, "📦 Creating download package...")
                
                zip_path = os.path.join(temp_dir, "segments.zip")
                if not self.create_zip_archive(output_dir, zip_path):
                    return False, None
                
                if progress_callback:
                    progress_callback(100, "✅ Processing complete!")
                
                # Read ZIP data
                with open(zip_path, 'rb') as f:
                    zip_data = f.read()
                
                return True, zip_data
                
        except Exception as e:
            st.error(f"Unexpected error during processing: {str(e)}")
            return False, None
        
        finally:
            self.cleanup()


class ProcessingStats:
    """Helper class to display processing statistics."""
    
    @staticmethod
    def display_summary(stats: Dict[str, Any]) -> None:
        """Display processing summary metrics."""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Processed Segments", stats.get('total_segments', 0))
        with col2:
            st.metric("Speakers", stats.get('unique_speakers', 0))
        with col3:
            st.metric("Total Duration", f"{stats.get('total_duration', 0):.1f}s")
    
    @staticmethod
    def display_speaker_breakdown(stats: Dict[str, Any]) -> None:
        """Display speaker breakdown."""
        speaker_breakdown = stats.get('speaker_breakdown', {})
        
        st.subheader("👥 Speaker Breakdown")
        for speaker, count in speaker_breakdown.items():
            st.write(f"**{speaker}**: {count} segments") 