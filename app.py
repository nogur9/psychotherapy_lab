"""
Streamlit UI for the Audio Diarization Splitter application.
Clean, focused interface that delegates all processing to dedicated modules.
"""

import streamlit as st
import pandas as pd
from audio_processor import AudioProcessingService
from models import DiarizationData


class StreamlitUI:
    """Handles all Streamlit UI components and user interactions."""
    
    def __init__(self):
        """Initialize the UI with audio processing service."""
        self.audio_service = AudioProcessingService()
        self._setup_page_config()
    
    def _setup_page_config(self):
        """Configure Streamlit page settings."""
        st.set_page_config(
            page_title="Audio Diarization Splitter",
            page_icon="🎵",
            layout="wide"
        )
    
    def render_header(self):
        """Render the main header and description."""
        st.title("🎵 Audio Diarization Splitter")
        st.markdown("""
        Upload your audio file and diarization CSV to automatically split the audio into segments by speaker.
        The app will create separate folders for each speaker and save the audio segments there.
        """)
    
    def render_sidebar(self):
        """Render the sidebar with file uploaders."""
        with st.sidebar:
            st.header("📁 Upload Files")
            
            # Add privacy notice
            st.info("🔒 **Privacy Notice**: Files are processed temporarily and automatically deleted after processing.")
            
            audio_file = st.file_uploader(
                "Upload Audio File (MP3 or WAV)",
                type=['mp3', 'wav'],
                help="Upload your MP3 or WAV audio file (max 200MB)"
            )
            
            diarization_file = st.file_uploader(
                "Upload Diarization CSV",
                type=['csv'],
                help="Upload your diarization CSV file with 'start', 'end', and 'speaker' columns"
            )
        
        return audio_file, diarization_file
    
    def render_file_info(self, audio_file, diarization_file):
        """Display information about uploaded files."""
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**Audio:** {audio_file.name}")
        with col2:
            st.info(f"**Diarization:** {diarization_file.name}")
    
    def render_diarization_preview(self, diarization_file):
        """Render diarization data preview and validation."""
        try:
            # Reset file pointer and load data
            diarization_file.seek(0)
            df = pd.read_csv(diarization_file)
            
            st.subheader("📊 Diarization Data Preview")
            
            if df.empty:
                st.error("❌ CSV file is empty. Please upload a valid diarization file.")
                return False, None
            
            # Validate data
            diarization_data = DiarizationData(dataframe=df, file_name=diarization_file.name)
            validation_errors = diarization_data.validate()
            
            if validation_errors:
                for error in validation_errors:
                    st.error(f"❌ {error}")
                return False, None
            
            st.success("✅ CSV format looks good!")
            
            # Show preview
            st.dataframe(df.head(10), use_container_width=True)
            
            # Show statistics
            self._render_statistics(diarization_data)
            
            return True, diarization_data
            
        except Exception as e:
            st.error(f"❌ Error reading CSV file: {str(e)}")
            st.info("Please check that your CSV file is not empty and has the correct format.")
            return False, None
    
    def _render_statistics(self, diarization_data: DiarizationData):
        """Render statistics about the diarization data."""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Segments", diarization_data.total_segments)
        with col2:
            st.metric("Unique Speakers", len(diarization_data.unique_speakers))
        with col3:
            st.metric("Duration (seconds)", f"{diarization_data.total_duration:.1f}")
    
    def render_processing_button(self, audio_file, diarization_file):
        """Render the processing button and handle processing."""
        if st.button("🚀 Start Processing", type="primary", use_container_width=True):
            self._process_audio(audio_file, diarization_file)
    
    def _process_audio(self, audio_file, diarization_file):
        """Handle audio processing with progress tracking."""
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def progress_callback(processed, total, speaker):
            """Callback function to update progress."""
            progress = 20 + (processed / total) * 70
            progress_bar.progress(int(progress))
            status_text.text(f"✂️ Processing segment {processed}/{total} ({speaker})")
        
        try:
            # Process audio
            result = self.audio_service.process_audio_with_diarization(
                audio_file, 
                diarization_file, 
                progress_callback
            )
            
            # Update progress to completion
            progress_bar.progress(100)
            status_text.text("✅ Processing complete!")
            
            # Display results
            self._display_results(result)
            
        except Exception as e:
            st.error(f"❌ Error during processing: {str(e)}")
            st.info("Please check your files and try again.")
        finally:
            # Clean up
            self.audio_service.cleanup()
    
    def _display_results(self, result):
        """Display processing results and download button."""
        st.success("🎉 Audio processing completed successfully!")
        
        # Download button
        st.download_button(
            label="📥 Download Segments (ZIP)",
            data=result.zip_data,
            file_name="audio_segments.zip",
            mime="application/zip",
            use_container_width=True
        )
        
        # Summary
        self._display_summary(result)
        self._display_speaker_breakdown(result)
    
    def _display_summary(self, result):
        """Display processing summary."""
        st.subheader("📋 Processing Summary")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Processed Segments", result.processed_segments)
        with col2:
            st.metric("Speakers", len(result.speakers))
    
    def _display_speaker_breakdown(self, result):
        """Display breakdown by speaker."""
        st.subheader("👥 Speaker Breakdown")
        
        # Get speaker counts from the original data
        # This would need to be passed through the result or calculated differently
        st.info("Speaker breakdown information available in the downloaded ZIP file.")
    
    def render_instructions(self):
        """Render instructions when no files are uploaded."""
        st.info("👆 Please upload your files using the sidebar to get started.")
        
        st.subheader("📋 Expected CSV Format")
        st.markdown("""
        Your diarization CSV should have the following columns:
        - `start`: Start time in seconds
        - `end`: End time in seconds  
        - `speaker`: Speaker identifier (e.g., 'therapist', 'patient')
        """)
        
        # Example data
        example_data = {
            'start': [0.03, 2.28, 4.09, 5.50],
            'end': [2.28, 4.09, 5.50, 7.75],
            'speaker': ['therapist', 'patient', 'therapist', 'patient']
        }
        st.dataframe(pd.DataFrame(example_data), use_container_width=True)
    
    def render_footer(self):
        """Render the footer."""
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; color: #666;'>
            <p>Audio Diarization Splitter | Built with Streamlit</p>
        </div>
        """, unsafe_allow_html=True)
    
    def run(self):
        """Main method to run the Streamlit application."""
        self.render_header()
        
        # Get uploaded files
        audio_file, diarization_file = self.render_sidebar()
        
        # Main content area
        if audio_file and diarization_file:
            st.success("✅ Both files uploaded successfully!")
            self.render_file_info(audio_file, diarization_file)
            
            # Preview and validate diarization data
            is_valid, diarization_data = self.render_diarization_preview(diarization_file)
            
            if is_valid:
                self.render_processing_button(audio_file, diarization_file)
        
        elif audio_file or diarization_file:
            st.warning("⚠️ Please upload both audio and diarization files to continue.")
        
        else:
            self.render_instructions()
        
        self.render_footer()


# Main application entry point
if __name__ == "__main__":
    ui = StreamlitUI()
    ui.run() 