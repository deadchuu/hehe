"""
Module for handling images in the history portal.

This module is responsible for:
- Fetching images from Google Search API
- Managing API query limits
- Saving images locally
"""

import os
import shutil
import requests
import base64
from io import BytesIO
import json
import csv
from datetime import datetime, timedelta
import time
from urllib.parse import urlparse
from dotenv import load_dotenv
from PIL import Image

class ImageHandler:
    """
    Class for handling image fetching from Google Search API.
    """
    
    def __init__(self):
        """Initialize image handling."""
        # Load environment variables
        load_dotenv()
        self.api_key = os.getenv('GOOGLE_API_KEY')
        self.search_engine_id = os.getenv('SEARCH_ENGINE_ID')
        
        if not self.api_key or not self.search_engine_id:
            raise ValueError("API credentials not found in environment variables")
            
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.cache_dir = os.path.join(self.project_root, "cache", "images")
        self.csv_cache = os.path.join(self.cache_dir, "image_cache.csv")
        self.images_dir = os.path.join(self.cache_dir, "downloaded")
        
        # Initialize API counter
        self.api_calls_file = os.path.join(self.project_root, 'cache', 'api_counter.json')
        self.load_api_counter()
        
        # Create necessary directories
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(self.images_dir, exist_ok=True)
        
        # Clean up old images
        self.cleanup_images()
        self._init_csv_cache()
        
    def load_api_counter(self):
        """Load API counter from file or initialize if not exists."""
        try:
            if os.path.exists(self.api_calls_file):
                with open(self.api_calls_file, 'r') as f:
                    data = json.load(f)
                    last_reset = datetime.fromisoformat(data['last_reset'])
                    # Reset counter if it's a new day
                    if last_reset.date() < datetime.now().date():
                        self.api_calls_left = 95
                        self.save_api_counter()
                    else:
                        self.api_calls_left = data['calls_left']
            else:
                self.api_calls_left = 95
                self.save_api_counter()
        except Exception as e:
            print(f"Error loading API counter: {e}")
            self.api_calls_left = 95
            self.save_api_counter()
            
    def save_api_counter(self):
        """Save API counter to file."""
        try:
            os.makedirs(os.path.dirname(self.api_calls_file), exist_ok=True)
            with open(self.api_calls_file, 'w') as f:
                json.dump({
                    'last_reset': datetime.now().isoformat(),
                    'calls_left': self.api_calls_left
                }, f)
        except Exception as e:
            print(f"Error saving API counter: {e}")
            
    def get_api_calls_left(self):
        """Get number of API calls left."""
        return self.api_calls_left
        
    def decrease_api_counter(self):
        """Decrease API counter and save."""
        if self.api_calls_left > 0:
            self.api_calls_left -= 1
            self.save_api_counter()
        
    def cleanup_images(self):
        """Delete all images from previous session."""
        if os.path.exists(self.images_dir):
            shutil.rmtree(self.images_dir)
        os.makedirs(self.images_dir, exist_ok=True)
        
    def _init_csv_cache(self):
        """Initialize CSV cache file if it doesn't exist."""
        if not os.path.exists(self.csv_cache):
            with open(self.csv_cache, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['query', 'url', 'timestamp', 'local_path'])
                
    def _cleanup_old_images(self):
        """Clean up images older than 7 days."""
        now = datetime.now()
        for filename in os.listdir(self.images_dir):
            file_path = os.path.join(self.images_dir, filename)
            if os.path.isfile(file_path):
                file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                if now - file_time > timedelta(days=7):
                    os.remove(file_path)
                    
    def _is_png_url(self, url):
        """Check if URL points to a PNG file."""
        parsed = urlparse(url)
        path = parsed.path.lower()
        return path.endswith('.png')
        
    def _download_image(self, url):
        """
        Download image from URL.
        
        Args:
            url (str): Image URL
            
        Returns:
            str: Path to downloaded image or None if failed
        """
        try:
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                # Generate unique filename
                filename = f"image_{int(time.time())}_{self.api_calls_left}.png"
                filepath = os.path.join(self.images_dir, filename)
                
                # Save the image
                with open(filepath, 'wb') as f:
                    response.raw.decode_content = True
                    shutil.copyfileobj(response.raw, f)
                    
                return filepath
            return None
        except Exception as e:
            print(f"Error downloading image: {e}")
            return None
            
    def get_image_url(self, query):
        """
        Get image URL from Google Custom Search API.
        
        Args:
            query (str): Search query
            
        Returns:
            tuple: (URL of the first PNG image, local path) or (None, None) if not found
        """
        # Check API limit
        if self.api_calls_left <= 0:
            print("API limit reached for today")
            return None, None
            
        # Check cache first
        cached_url = self._get_cached_url(query)
        if cached_url:
            return cached_url
            
        # Prepare search query
        search_url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': self.api_key,
            'cx': self.search_engine_id,
            'q': query,
            'searchType': 'image',
            'fileType': 'png',  # Request only PNG images
            'num': 10  # Get more results to find PNG
        }
        
        try:
            # Make API request
            response = requests.get(search_url, params=params)
            
            if response.status_code == 200:
                # Decrease API counter only after successful request
                self.decrease_api_counter()
                
                data = response.json()
                if 'items' in data:
                    # Look for first PNG URL
                    for item in data['items']:
                        url = item['link']
                        if url.lower().endswith('.png'):
                            # Download and save image
                            local_path = self._download_image(url)
                            if local_path:
                                # Cache the result
                                self._cache_url(query, url, local_path)
                                return url, local_path
                return None, None
        except Exception as e:
            print(f"Error in get_image_url: {e}")
            return None, None
            
    def get_image_base64(self, query):
        """Get base64-encoded image for the query."""
        try:
            # Try to get image URL from Google Custom Search API
            image_url, local_path = self.get_image_url(query)
            if not image_url:
                return None
                
            # Download image
            response = requests.get(image_url)
            if response.status_code != 200:
                return None
                
            # Return raw PNG data
            return base64.b64encode(response.content).decode('utf-8')
                
        except Exception as e:
            print(f"Error getting image: {e}")
            return None
            
    def _get_cached_url(self, query):
        """Get cached URL for query if exists and not expired."""
        if not os.path.exists(self.csv_cache):
            return None
        
        with open(self.csv_cache, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 4 and row[0] == query:
                    # Don't decrease counter for cached results
                    return row[1], row[3]
        return None
        
    def _cache_url(self, query, url, local_path):
        """Cache URL and local path for query."""
        with open(self.csv_cache, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([query, url, datetime.now().isoformat(), local_path])
