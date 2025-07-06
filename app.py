import streamlit as st
import pandas as pd
from video_processor import VideoProcessor, ProcessingStats


class VideoDiarizationApp:
    """Main Streamlit application for video diarization processing."""
    
    def __init__(self):
        self.video_processor = VideoProcessor()
        self.setup_page_config()
    
    def setup_page_config(self):
        """Configure Streamlit page settings."""
        st.set_page_config(
            page_title="Video Diarization Splitter",
            page_icon="🎬",
            layout="wide"
        )
    
    def render_header(self):
        """Render the main header and description."""
        st.title("🎬 Video Diarization Splitter")
        st.markdown("""
        Upload your video file and diarization CSV to automatically split the video into segments by speaker.
        The app will create separate folders for each speaker and save the video segments there.
        """)
    
    def render_sidebar(self):
        """Render the sidebar with file upload controls."""
        with st.sidebar:
            st.header("📁 Upload Files")
            
            # File uploaders
            video_file = st.file_uploader(
                "Upload Video File (MP4)",
                type=['mp4'],
                help="Upload your MP4 video file"
            )
            
            diarization_file = st.file_uploader(
                "Upload Diarization CSV",
                type=['csv'],
                help="Upload your diarization CSV file with 'start', 'end', and 'speaker' columns"
            )
        
        return video_file, diarization_file
    
    def render_file_info(self, video_file, diarization_file):
        """Display information about uploaded files."""
        st.success("✅ Both files uploaded successfully!")
        
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**Video:** {video_file.name}")
        with col2:
            st.info(f"**Diarization:** {diarization_file.name}")
    
    def validate_and_preview_data(self, diarization_file):
        """Validate and preview the diarization data."""
        try:
            df = pd.read_csv(diarization_file)
            st.subheader("📊 Diarization Data Preview")
            
            # Check required columns
            required_columns = ['start', 'end', 'speaker']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                st.error(f"❌ Missing required columns: {', '.join(missing_columns)}")
                st.info("Your CSV should have columns: 'start', 'end', and 'speaker'")
                return False, None
            
            st.success("✅ CSV format looks good!")
            
            # Show preview
            st.dataframe(df.head(10), use_container_width=True)
            
            # Show statistics
            self.render_data_statistics(df)
            
            return True, df
            
        except Exception as e:
            st.error(f"❌ Error reading CSV file: {str(e)}")
            return False, None
    
    def render_data_statistics(self, df):
        """Render statistics about the diarization data."""
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Segments", len(df))
        with col2:
            st.metric("Unique Speakers", int(df['speaker'].nunique()))
        with col3:
            st.metric("Duration (seconds)", f"{df['end'].max():.1f}")
    
    def progress_callback(self, progress, message):
        """Callback function for progress updates."""
        self.progress_bar.progress(progress)
        self.status_text.text(message)
    
    def process_video_files(self, video_file, diarization_file):
        """Process the uploaded video and diarization files."""
        # Create progress bar
        self.progress_bar = st.progress(0)
        self.status_text = st.empty()
        
        # Process video
        success, zip_data = self.video_processor.process_video_file(
            video_file, 
            diarization_file, 
            self.progress_callback
        )
        
        if success and zip_data:
            self.render_success_results(zip_data)
        else:
            st.error("❌ Processing failed. Please check your files and try again.")
    
    def render_success_results(self, zip_data):
        """Render the success results and download options."""
        st.success("🎉 Video processing completed successfully!")
        
        # Download button
        st.download_button(
            label="📥 Download Segments (ZIP)",
            data=zip_data,
            file_name="video_segments.zip",
            mime="application/zip",
            use_container_width=True
        )
        
        # Show summary
        stats = self.video_processor.get_processing_stats()
        ProcessingStats.display_summary(stats)
        ProcessingStats.display_speaker_breakdown(stats)
    
    def render_instructions(self):
        """Render instructions when no files are uploaded."""
        st.info("👆 Please upload your files using the sidebar to get started.")
        
        # Example CSV format
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
            <p>Video Diarization Splitter | Built with Streamlit</p>
        </div>
        """, unsafe_allow_html=True)
    
    def run(self):
        """Main application loop."""
        self.render_header()
        
        # Get uploaded files
        video_file, diarization_file = self.render_sidebar()
        
        # Main content area
        if video_file and diarization_file:
            self.render_file_info(video_file, diarization_file)
            
            # Validate and preview data
            is_valid, df = self.validate_and_preview_data(diarization_file)
            
            if is_valid:
                # Process button
                if st.button("🚀 Start Processing", type="primary", use_container_width=True):
                    self.process_video_files(video_file, diarization_file)
        
        elif video_file or diarization_file:
            st.warning("⚠️ Please upload both video and diarization files to continue.")
        
        else:
            self.render_instructions()
        
        self.render_footer()


def main():
    """Main entry point for the application."""
    app = VideoDiarizationApp()
    app.run()


if __name__ == "__main__":
    main() 