import streamlit as st
import pandas as pd
from moviepy.video.io.VideoFileClip import VideoFileClip
import os
import tempfile
import zipfile


def process_audio(_audio_file, _diarization_file):
    """Process the audio file and create segments by speaker"""
    
    diarization_data = _load_diarization_data(_diarization_file)
    _validate_diarization_data(diarization_data)
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            audio_path = _save_uploaded_file(_audio_file, temp_dir)
            audio_clip = _load_audio_file(audio_path)
            
            status_text.text(f"✂️ Processing {len(diarization_data)} segments...")
            progress_bar.progress(20)
            
            output_dir = _create_output_directory(temp_dir, diarization_data)
            processed_segments = _process_audio_segments(
                audio_clip, diarization_data, output_dir, progress_bar, status_text
            )
            
            audio_clip.close()
            
            zip_data = _create_download_package(output_dir, progress_bar, status_text)
            _display_results(processed_segments, diarization_data, zip_data)
            
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


def _process_audio_segments(audio_clip, diarization_data, output_dir, progress_bar, status_text):
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
        progress = 20 + (processed_segments / total_segments) * 70
        progress_bar.progress(int(progress))
        
        status_text.text(f"✂️ Processing segment {processed_segments}/{total_segments} ({speaker})")
    
    return processed_segments


def _create_download_package(output_dir, progress_bar, status_text):
    """Create ZIP file for download and return its data"""
    status_text.text("📦 Creating download package...")
    progress_bar.progress(90)
    
    zip_path = os.path.join(output_dir, "..", "segments.zip")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, output_dir)
                zipf.write(file_path, arcname)
    
    progress_bar.progress(100)
    status_text.text("✅ Processing complete!")
    
    with open(zip_path, 'rb') as f:
        return f.read()


def _display_results(processed_segments, diarization_data, zip_data):
    """Display processing results and download button"""
    st.success("🎉 Audio processing completed successfully!")
    
    st.download_button(
        label="📥 Download Segments (ZIP)",
        data=zip_data,
        file_name="audio_segments.zip",
        mime="application/zip",
        use_container_width=True
    )
    
    _display_summary(processed_segments, diarization_data)
    _display_speaker_breakdown(diarization_data)


def _display_summary(processed_segments, diarization_data):
    """Display processing summary metrics"""
    st.subheader("📋 Processing Summary")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Processed Segments", processed_segments)
    with col2:
        st.metric("Speakers", int(diarization_data['speaker'].nunique()))
    with col3:
        st.metric("Total Duration", f"{float(diarization_data['end'].max()):.1f}s")


def _display_speaker_breakdown(diarization_data):
    """Display breakdown of segments by speaker"""
    st.subheader("👥 Speaker Breakdown")
    speaker_counts = diarization_data['speaker'].value_counts()
    
    for speaker, count in speaker_counts.items():
        st.write(f"**{speaker}**: {count} segments")


def _handle_processing_error(error):
    """Handle and display processing errors"""
    st.error(f"❌ Error during processing: {str(error)}")
    st.error("Please check your files and try again.")


# Page configuration
st.set_page_config(
    page_title="Audio Diarization Splitter",
    page_icon="🎵",
    layout="wide"
)

# Title and description
st.title("🎵 Audio Diarization Splitter")
st.markdown("""
Upload your audio file and diarization CSV to automatically split the audio into segments by speaker.
The app will create separate folders for each speaker and save the audio segments there.
""")

# Sidebar for file uploads
with st.sidebar:
    st.header("📁 Upload Files")
    
    # File uploaders
    audio_file = st.file_uploader(
        "Upload Audio File (MP3)",
        type=['mp3'],
        help="Upload your MP3 audio file"
    )
    
    diarization_file = st.file_uploader(
        "Upload Diarization CSV",
        type=['csv'],
        help="Upload your diarization CSV file with 'start', 'end', and 'speaker' columns"
    )

# Main content area
if audio_file and diarization_file:
    st.success("✅ Both files uploaded successfully!")
    
    # Display file info
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**Audio:** {audio_file.name}")
    with col2:
        st.info(f"**Diarization:** {diarization_file.name}")
    
    # Preview diarization data
    try:
        df = pd.read_csv(diarization_file)
        st.subheader("📊 Diarization Data Preview")
        
        # Check required columns
        required_columns = ['start', 'end', 'speaker']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            st.error(f"❌ Missing required columns: {', '.join(missing_columns)}")
            st.info("Your CSV should have columns: 'start', 'end', and 'speaker'")
        else:
            st.success("✅ CSV format looks good!")
            
            # Show preview
            st.dataframe(df.head(10), use_container_width=True)

            # Show statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Segments", len(df))
            with col2:
                st.metric("Unique Speakers", int(df['speaker'].nunique()))
            with col3:
                st.metric("Duration (seconds)", f"{float(df['end'].max()):.1f}")

    except Exception as e:
            st.error(f"❌ Error reading CSV file: {str(e)}")


    try:
            # Process button
            if st.button("🚀 Start Processing", type="primary", use_container_width=True):
                process_audio(audio_file, diarization_file)
    
    except Exception as e:
        st.error(f"❌ Error processing audio: {str(e)}")

elif audio_file or diarization_file:
    st.warning("⚠️ Please upload both audio and diarization files to continue.")

else:
    # Instructions when no files are uploaded
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
# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>Audio Diarization Splitter | Built with Streamlit</p>
</div>
""", unsafe_allow_html=True) 