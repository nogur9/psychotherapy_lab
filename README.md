# 🎵 Audio Diarization Splitter

A Streamlit web application that automatically splits audio files into segments based on speaker diarization data.

## Features

- 📁 **Easy File Upload**: Upload MP3 audio files and CSV diarization files
- 👥 **Speaker Separation**: Automatically organizes segments by speaker
- 📊 **Data Preview**: Preview your diarization data before processing
- ⏱️ **Progress Tracking**: Real-time progress updates during processing
- 📦 **ZIP Download**: Download all segments as a compressed file
- 📱 **Responsive Design**: Works on desktop and mobile devices

## Requirements

Your diarization CSV file should have the following columns:
- `start`: Start time in seconds
- `end`: End time in seconds
- `speaker`: Speaker identifier (e.g., 'therapist', 'patient')

## Installation

### Local Development

1. **Clone or download this repository**

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the app**:
   ```bash
   streamlit run app.py
   ```

4. **Open your browser** and go to `http://localhost:8501`

### Deployment Options

#### Streamlit Cloud (Recommended)
1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repository
4. Deploy with one click

#### Other Platforms
- **Heroku**: Add `setup.sh` and `Procfile`
- **Railway**: Direct deployment from GitHub
- **Google Cloud Run**: Container-based deployment

## Usage

1. **Upload Files**: Use the sidebar to upload your MP3 audio file and CSV diarization file
2. **Preview Data**: Check the diarization data preview to ensure correct format
3. **Start Processing**: Click the "Start Processing" button
4. **Download Results**: Download the ZIP file containing all segments organized by speaker

## Example CSV Format

```csv
start,end,speaker
0.03,2.28,therapist
2.28,4.09,patient
4.09,5.50,therapist
5.50,7.75,patient
```

## Output Structure

The app creates a ZIP file with the following structure:
```
segments/
├── therapist/
│   ├── segment_0.03_2.28.wav
│   ├── segment_4.09_5.50.wav
│   └── ...
└── patient/
    ├── segment_2.28_4.09.wav
    ├── segment_5.50_7.75.wav
    └── ...
```

## Technical Details

- **Audio Processing**: Uses librosa and soundfile for audio manipulation
- **File Handling**: Temporary file processing with automatic cleanup
- **Progress Tracking**: Real-time updates during processing
- **Error Handling**: Comprehensive error messages and validation

## Limitations

- Maximum file size depends on your deployment platform
- Processing time scales with audio length and number of segments
- Input supports MP3 format, output is WAV format for better compatibility

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is open source and available under the MIT License. 