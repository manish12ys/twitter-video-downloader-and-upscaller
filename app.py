import streamlit as st
import yt_dlp
import re
import shutil
import os
import subprocess

# Check if ffmpeg is installed
ffmpeg_installed = shutil.which("ffmpeg") is not None

# Function to fetch available video formats
def get_available_formats(tweet_url):
    ydl_opts = {
        "quiet": True,
        "noplaylist": True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(tweet_url, download=False)  # Fetch info without downloading
            formats = [
                (f"{f['format']} - {f['height']}p", f['format_id'])
                for f in info.get("formats", [])
                if f.get("height") and f.get("ext") == "mp4"  # Only MP4 videos with height info
            ]
            return sorted(set(formats), key=lambda x: int(x[0].split('-')[1].replace('p', '')), reverse=True)
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return []

# Function to download Twitter video in selected quality
def download_twitter_video(tweet_url, format_id):
    ydl_opts = {
        "format": format_id,  # Download user-selected format
        "quiet": True,
        "outtmpl": "twitter_video.%(ext)s",
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(tweet_url, download=True)
            video_file = "twitter_video.mp4"
            return video_file if os.path.exists(video_file) else None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

# Function to upscale video to 1080p HD using FFmpeg
def upscale_to_hd(input_file):
    output_file = "twitter_video_hd.mp4"
    command = [
        "ffmpeg",
        "-i", input_file,
        "-vf", "scale=1920:1080:flags=lanczos",  # High-quality upscaling using Lanczos filter
        "-c:v", "libx264",
        "-preset", "slow",
        "-crf", "18",  # High-quality output
        "-c:a", "aac",
        "-b:a", "192k",
        output_file
    ]

    try:
        subprocess.run(command, check=True)
        return output_file if os.path.exists(output_file) else None
    except Exception as e:
        st.error(f"Upscaling error: {str(e)}")
        return None

st.title("📹 Twitter HD Video Downloader & Upscaler")
st.write("Paste a Twitter video link below, click 'Enter', choose a resolution, and upscale it to HD if needed.")

tweet_url = st.text_input("Enter Twitter video URL:")
enter_pressed = st.button("Enter")  # Add enter button

def is_valid_twitter_url(url):
    return re.match(r"https?://(www\.)?(twitter|x)\.com/.+/status/\d+", url)

if enter_pressed and tweet_url and is_valid_twitter_url(tweet_url):
    formats = get_available_formats(tweet_url)

    if formats:
        format_options = [f[0] for f in formats]
        selected_quality = st.selectbox("Select video quality:", format_options)
        format_id = dict(formats)[selected_quality]  # Get format ID from selection

        upscale_option = st.checkbox("Enhance to HD (1080p)")

        if st.button("Download Video"):
            if not ffmpeg_installed:
                st.error("FFmpeg is not installed! Please install it and restart the app.")
            else:
                video_file = download_twitter_video(tweet_url, format_id)
                if video_file:
                    if upscale_option:
                        st.info("Enhancing video to 1080p HD, please wait...")
                        video_file = upscale_to_hd(video_file)  # Upscale video if selected

                    if video_file:
                        st.success("Download complete! Click below to get your HD video:")
                        st.download_button("⬇ Download Video", open(video_file, "rb"), "twitter_video_hd.mp4")
                    else:
                        st.error("Failed to upscale the video.")
                else:
                    st.error("Failed to download video. Please check the URL.")
    else:
        st.warning("No valid MP4 formats found. The video might not be downloadable.")

st.markdown("<br><p style='text-align: center; color: gray;'>Made with ❤️ using Streamlit</p>", unsafe_allow_html=True)
