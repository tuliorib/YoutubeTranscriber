from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
import requests
from bs4 import BeautifulSoup
import sys
import re

def extract_video_id(url):
    """
    Extract the video ID from a YouTube URL.
    Handles different YouTube URL formats.
    """
    parsed_url = urlparse(url)
    
    if parsed_url.netloc == 'youtu.be':
        return parsed_url.path[1:]
    
    if parsed_url.netloc in ('youtube.com', 'www.youtube.com'):
        if parsed_url.path == '/watch':
            return parse_qs(parsed_url.query)['v'][0]
        elif parsed_url.path.startswith('/embed/'):
            return parsed_url.path.split('/')[2]
    
    raise ValueError("Invalid YouTube URL")

def get_video_title(url):
    """
    Fetch the title of the YouTube video using requests and BeautifulSoup.
    Returns the video title or None if not found.
    """
    try:
        response = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try different meta tags that might contain the title
        meta_title = soup.find('meta', property='og:title')
        if meta_title:
            return meta_title['content']
            
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.text.replace(' - YouTube', '')
            return title.strip()
            
        return None
    except Exception as e:
        print(f"Warning: Could not fetch video title: {str(e)}")
        return None

def sanitize_filename(title):
    """
    Convert a video title into a clean filename.
    Removes special characters, converts to lowercase, replaces spaces with underscores.
    """
    if not title:
        return "transcript"
    
    # Convert to lowercase
    clean_name = title.lower()
    
    # Replace special characters and spaces
    clean_name = re.sub(r'[^\w\s-]', '', clean_name)  # Remove special characters
    clean_name = re.sub(r'\s+', '_', clean_name)      # Replace spaces with underscore
    clean_name = re.sub(r'_+', '_', clean_name)       # Remove multiple consecutive underscores
    clean_name = clean_name.strip('_')                 # Remove leading/trailing underscores
    
    # Ensure the filename isn't too long (max 50 chars)
    clean_name = clean_name[:50]
    
    return f"{clean_name}_transcript.txt"

def get_transcript_and_title(url):
    """
    Fetch the transcript and title for a YouTube video.
    Returns tuple of (transcript_text, video_title).
    """
    try:
        video_id = extract_video_id(url)
        
        # Get video title first
        title = get_video_title(url)
        
        # Get available transcripts
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # Try to get the English transcript first, fall back to any available transcript
        try:
            transcript = transcript_list.find_transcript(['en'])
        except:
            transcript = transcript_list.find_transcript([])
            
        # Fetch the transcript
        transcript_data = transcript.fetch()
        
        # Combine all text segments into a single string
        full_text = ' '.join(segment['text'] for segment in transcript_data)
        
        return full_text, title
        
    except Exception as e:
        return f"Error fetching transcript: {str(e)}", None

def save_transcript(transcript, output_file):
    """
    Save the transcript to a text file.
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(transcript)

def main():
    if len(sys.argv) < 2:
        print("Usage: python script.py <youtube_url>")
        sys.exit(1)
    
    url = sys.argv[1]
    transcript, title = get_transcript_and_title(url)
    
    if transcript.startswith("Error"):
        print(transcript)
    else:
        output_file = sanitize_filename(title)
        save_transcript(transcript, output_file)
        print(f"Transcript saved to {output_file}")

if __name__ == "__main__":
    main()
