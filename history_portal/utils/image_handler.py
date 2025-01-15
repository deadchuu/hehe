"""
Module for handling images in the history portal.

This module is responsible for:
- Fetching images from Google Search API
- Managing API query limits
- Saving images locally
"""

import requests
import json
import os
import csv
from datetime import datetime, timedelta
import time
import base64
import shutil
from urllib.parse import urlparse

class ImageHandler:
    """
    Class for handling image fetching from Google Search API.
    """
    
    def __init__(self):
        """Initialize image handling."""
        self.api_key = "AIzaSyCubrsaD3iWCn2DBmc5IUI9gY-dL2BsGAs"
        self.search_engine_id = "76870cfb35dbb443a"  # Google Custom Search Engine ID
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.cache_dir = os.path.join(self.project_root, "cache", "images")
        self.csv_cache = os.path.join(self.cache_dir, "image_cache.csv")
        self.images_dir = os.path.join(self.cache_dir, "downloaded")
        self.api_calls_today = 0
        self.max_api_calls = 45
        self.image_counter = 1
        
        # Create necessary directories
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(self.images_dir, exist_ok=True)
        
        # Clean up old images
        self._cleanup_old_images()
        self._init_csv_cache()
        
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
        
    def _download_png(self, url):
        """
        Download PNG image from URL.
        
        Args:
            url (str): Image URL
            
        Returns:
            str: Path to downloaded image or None if failed
        """
        try:
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                # Generate unique filename
                filename = f"image_{int(time.time())}_{self.image_counter}.png"
                filepath = os.path.join(self.images_dir, filename)
                
                # Save the image
                with open(filepath, 'wb') as f:
                    response.raw.decode_content = True
                    shutil.copyfileobj(response.raw, f)
                    
                self.image_counter += 1
                return filepath
            return None
        except Exception as e:
            print(f"Error downloading PNG: {e}")
            return None
            
    def get_image_url(self, query):
        """
        Get image URL from Google Custom Search API.
        
        Args:
            query (str): Search query
            
        Returns:
            tuple: (URL of the first PNG image, local path) or (None, None) if not found
        """
        if self.api_calls_today >= self.max_api_calls:
            print("API call limit reached for today")
            return None, None
            
        # Check cache first
        cached_result = self._get_cached_url(query)
        if cached_result:
            return cached_result
            
        # Construct the search URL
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
            response = requests.get(search_url, params=params)
            self.api_calls_today += 1
            
            if response.status_code == 200:
                data = response.json()
                if 'items' in data:
                    # Look for first PNG URL
                    for item in data['items']:
                        url = item['link']
                        if self._is_png_url(url):
                            # Download the PNG file
                            local_path = self._download_png(url)
                            if local_path:
                                self._cache_url(query, url, local_path)
                                return url, local_path
            return None, None
        except Exception as e:
            print(f"Error fetching image URL: {e}")
            return None, None
            
    def get_image_base64(self, query):
        """
        Get image as base64 string.
        
        Args:
            query (str): Search query
            
        Returns:
            str: Base64 encoded image or None if not found
        """
        image_url, local_path = self.get_image_url(query)
        if not local_path:
            return None
            
        try:
            with open(local_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
                return image_data
        except Exception as e:
            print(f"Error encoding image to base64: {e}")
            return None
            
    def _get_cached_url(self, query):
        """Get cached URL and local path for query if it exists and is not too old."""
        if not os.path.exists(self.csv_cache):
            return None
            
        with open(self.csv_cache, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['query'] == query:
                    timestamp = datetime.fromisoformat(row['timestamp'])
                    if datetime.now() - timestamp < timedelta(days=7):
                        if os.path.exists(row['local_path']):
                            return row['url'], row['local_path']
        return None
        
    def _cache_url(self, query, url, local_path):
        """Cache URL and local path for query."""
        with open(self.csv_cache, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([query, url, datetime.now().isoformat(), local_path])
            
    def get_api_calls_left(self):
        """Get number of API calls left for today."""
        return self.max_api_calls - self.api_calls_today
