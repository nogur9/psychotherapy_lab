import streamlit as st
import pandas as pd
from moviepy.video.io.VideoFileClip import VideoFileClip
import os
import tempfile
import zipfile
from pathlib import Path
import time


def process_video(video_file, diarization_file):
    """Process the video and create segments"""

    # Read diarization CSV
    df_diari = pd.read_csv(diarization_file).copy()

    # Create progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        # Create temporary directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            status_text.text("📁 Setting up temporary directory...")
            progress_bar.progress(10)

            # Save uploaded files to temp directory
            video_path = os.path.join(temp_dir, video_file.name)
            with open(video_path, 'wb') as f:
                f.write(video_file.getbuffer())

            status_text.text("🎬 Loading video file...")
            progress_bar.progress(20)

            # Load video
            video = VideoFileClip(video_path)
            total_segments = len(df_diari)

            status_text.text(f"✂️ Processing {total_segments} segments...")

            # Create output directory
            output_dir = os.path.join(temp_dir, "segments")
            os.makedirs(output_dir, exist_ok=True)

            # Create speaker directories
            for speaker in df_diari['speaker'].unique():
                os.makedirs(os.path.join(output_dir, str(speaker)), exist_ok=True)

            # Process each segment
            processed_segments = 0
            for idx, row in df_diari.iterrows():
                start = float(row['start'])
                end = float(row['end'])

                # Skip if segment extends beyond video
                if end > video.duration:
                    break

                speaker = str(row['speaker'])
                segment = video.subclipped(start_time=start, end_time=end)

                # Create output filename
                out_name = f"segment_{start:.2f}_{end:.2f}.mp4"
                out_path = os.path.join(output_dir, speaker, out_name)

                # Write segment
                segment.write_videofile(
                    out_path,
                    codec="libx264",
                    audio_codec="aac",
                    verbose=False,
                    logger=None
                )

                processed_segments += 1
                progress = 20 + (processed_segments / total_segments) * 70
                progress_bar.progress(int(progress))

                # Update status
                status_text.text(f"✂️ Processing segment {processed_segments}/{total_segments} ({speaker})")

            video.close()

            status_text.text("📦 Creating download package...")
            progress_bar.progress(90)

            # Create ZIP file for download
            zip_path = os.path.join(temp_dir, "segments.zip")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(output_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, output_dir)
                        zipf.write(file_path, arcname)

            progress_bar.progress(100)
            status_text.text("✅ Processing complete!")

            # Provide download link
            with open(zip_path, 'rb') as f:
                zip_data = f.read()

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
            st.subheader("📋 Processing Summary")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Processed Segments", processed_segments)
            with col2:
                st.metric("Speakers", df_diari['speaker'].nunique())
            with col3:
                st.metric("Total Duration", f"{df_diari['end'].max():.1f}s")

            # Show speaker breakdown
            speaker_counts = df_diari['speaker'].value_counts()
            st.subheader("👥 Speaker Breakdown")
            for speaker, count in speaker_counts.items():
                st.write(f"**{speaker}**: {count} segments")

    except Exception as e:
        st.error(f"❌ Error during processing: {str(e)}")
        st.error("Please check your files and try again.")


# Page configuration
st.set_page_config(
    page_title="Video Diarization Splitter",
    page_icon="🎬",
    layout="wide"
)

# Title and description
st.title("🎬 Video Diarization Splitter")
st.markdown("""
Upload your video file and diarization CSV to automatically split the video into segments by speaker.
The app will create separate folders for each speaker and save the video segments there.
""")

# Sidebar for file uploads
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

# Main content area
if video_file and diarization_file:
    st.success("✅ Both files uploaded successfully!")
    
    # Display file info
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**Video:** {video_file.name}")
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
                st.metric("Unique Speakers", df['speaker'].nunique())
            with col3:
                st.metric("Duration (seconds)", f"{df['end'].max():.1f}")
            
            # Process button
            if st.button("🚀 Start Processing", type="primary", use_container_width=True):
                process_video(video_file, diarization_file, df)
    
    except Exception as e:
        st.error(f"❌ Error reading CSV file: {str(e)}")

elif video_file or diarization_file:
    st.warning("⚠️ Please upload both video and diarization files to continue.")

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
    <p>Video Diarization Splitter | Built with Streamlit</p>
</div>
""", unsafe_allow_html=True) 