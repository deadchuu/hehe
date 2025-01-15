"""
Graphical user interface module for the history portal.
"""

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import base64
from io import BytesIO
import os
from PIL import Image, ImageTk
import threading
import webbrowser
import time
import urllib.parse

from utils.api_handler import APIHandler
from utils.image_handler import ImageHandler
import socket
import customtkinter as ctk

class LoadingAnimation(tk.Canvas):
    def __init__(self, parent, width, height, *args, **kwargs):
        super().__init__(parent, width=width, height=height, *args, **kwargs)
        self.width = width
        self.height = height
        self.progress = 0
        self.is_running = False
        self.configure(bg="#2b2b2b", highlightthickness=0)
        
    def start(self):
        self.is_running = True
        self.progress = 0
        self.animate()
        
    def stop(self):
        self.is_running = False
        self.delete("progress")
        
    def animate(self):
        if not self.is_running:
            return
            
        self.delete("progress")
        progress_width = (self.width * self.progress) / 100
        
        self.create_rectangle(
            0, 0, progress_width, self.height,
            fill="#4a9eff", outline="",
            tags="progress"
        )
        
        if self.progress < 100:
            self.progress += 2
            self.after(50, self.animate)
        else:
            self.stop()

class HistoryPortalGUI:
    def __init__(self):
        """Initialize the graphical interface."""
        self.window = ctk.CTk()
        self.window.title("History Portal")
        self.window.geometry("1200x800")
        
        # Set dark theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        
        # Initialize state variables
        self.current_event = None
        self.current_image = None
        self.is_online = True
        self.api_calls_left = 45  # Current API calls left
        
        # Initialize handlers
        self.api_handler = APIHandler()
        self.image_handler = ImageHandler()
        
        # Split window into two frames
        self.create_main_frames()
        
        # Create UI elements
        self.create_right_panel()
        self.create_left_panel()
        
        # Check internet connection
        self.check_internet_connection()
        
        # Add Google Custom Search
        self.add_google_search()
        
    def create_main_frames(self):
        """Create main left and right frames."""
        # Configure grid weights for the main window
        self.window.grid_columnconfigure(0, weight=1)  # Left frame
        self.window.grid_columnconfigure(1, weight=1)  # Right frame
        self.window.grid_rowconfigure(0, weight=1)
        
        # Left frame for image
        self.left_frame = ctk.CTkFrame(self.window)
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Right frame for controls and text
        self.right_frame = ctk.CTkFrame(self.window)
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
    def create_left_panel(self):
        """Create the left panel with image display."""
        # Use specific color that matches CustomTkinter dark theme
        bg_color = "#2B2B2B"
        
        # Create canvas with matching background
        self.image_canvas = tk.Canvas(
            self.left_frame,
            bg=bg_color,
            highlightthickness=0
        )
        self.image_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Loading label with matching colors
        self.loading_label = tk.Label(
            self.image_canvas,
            text="Loading...",
            fg="#DCE4EE",  # Light text color
            bg=bg_color
        )
        
    def create_right_panel(self):
        """Create the right panel with controls and text display."""
        # Input fields frame
        input_frame = ctk.CTkFrame(self.right_frame)
        input_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Day input
        self.day_label = ctk.CTkLabel(input_frame, text="Day:")
        self.day_label.grid(row=0, column=0, padx=5, pady=5)
        self.day_entry = ctk.CTkEntry(input_frame, width=60)
        self.day_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Month input
        self.month_label = ctk.CTkLabel(input_frame, text="Month:")
        self.month_label.grid(row=0, column=2, padx=5, pady=5)
        self.month_entry = ctk.CTkEntry(input_frame, width=60)
        self.month_entry.grid(row=0, column=3, padx=5, pady=5)
        
        # Create frame for buttons
        self.button_frame = ctk.CTkFrame(self.right_frame)
        self.button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Control buttons
        self.find_button = ctk.CTkButton(
            self.button_frame,
            text="Find Event",
            command=self.find_events
        )
        self.find_button.pack(side=tk.LEFT, padx=5)
        
        self.next_button = ctk.CTkButton(
            self.button_frame,
            text="Next",
            command=self.next_event
        )
        self.next_button.pack(side=tk.LEFT, padx=5)
        
        self.random_button = ctk.CTkButton(
            self.button_frame,
            text="Random",
            command=self.random_date
        )
        self.random_button.pack(side=tk.LEFT, padx=5)
        
        # Online mode frame
        mode_frame = ctk.CTkFrame(self.right_frame)
        mode_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Online mode switch
        self.online_switch = ctk.CTkSwitch(
            mode_frame,
            text="Online Mode",
            command=self.toggle_online_mode
        )
        self.online_switch.pack(side=tk.LEFT, padx=5)
        self.online_switch.select()  # Enable by default
        
        # API counter label
        self.api_counter_label = ctk.CTkLabel(
            mode_frame,
            text="API Calls: 95/95",
            font=("Arial", 12)
        )
        self.api_counter_label.pack(side=tk.RIGHT, padx=5)
        
        # Create text widget for event display
        self.event_text = ctk.CTkTextbox(
            self.right_frame,
            height=200,
            font=("Arial", 12)
        )
        self.event_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Read more button at the bottom
        self.read_more_button = ctk.CTkButton(
            self.right_frame,
            text="Read More",
            command=self.open_in_google
        )
        self.read_more_button.pack(fill=tk.X, padx=5, pady=5)
        
    def toggle_online_mode(self):
        """Toggle between online and offline modes."""
        self.is_online = self.online_switch.get()
        
        # Clear canvas when switching modes
        self.image_canvas.delete("all")
        
        # Update current event display if exists
        if hasattr(self, 'current_event'):
            self.display_event(self.current_event)
        
        # Update API counter display
        if self.is_online:
            api_calls_left = self.image_handler.get_api_calls_left()
            self.api_counter_label.configure(text=f"API Calls: {api_calls_left}/95")
            if api_calls_left <= 10:
                self.api_counter_label.configure(
                    text=f"Warning: only {api_calls_left} API calls left!",
                    text_color="red"
                )
        else:
            self.api_counter_label.configure(text="Offline Mode", text_color="white")
            
    def find_events(self):
        """Find historical events for the given date."""
        try:
            day = int(self.day_entry.get())
            month = int(self.month_entry.get())
            
            events = self.api_handler.get_events_by_date(month, day)
            if not events:
                self.event_text.delete("1.0", tk.END)
                self.event_text.insert("1.0", "No events found for this date")
                return
                
            self.current_event = events[0]
            self.display_event(self.current_event)
            
        except ValueError:
            messagebox.showerror("Error", "Please enter valid day and month")
            
    def display_event(self, event):
        """Display the event in the text widget."""
        if not event:
            return
        
        self.current_event = event
        
        # Enable text widget for editing
        self.event_text.configure(state="normal")
        
        # Clear previous content
        self.event_text.delete("1.0", tk.END)
        
        # Add event text
        year_text = f"{event['year']} - "
        description = event['text']
        
        self.event_text.insert(tk.END, year_text, "year")
        self.event_text.insert(tk.END, description)
        
        # Disable text widget
        self.event_text.configure(state="disabled")
        
        # Display related image
        if self.is_online:
            self.loading_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
            self.window.update()
            
            # Create search query from event
            query = f"{event['year']} {event['text']}"
            
            # Get and display image
            image_data = self.image_handler.get_image_base64(query)
            self.display_image(image_data)
            
    def _load_image_async(self, query):
        """Load and display image asynchronously."""
        try:
            image_data = self.image_handler.get_image_base64(query)
            
            # Schedule image display on main thread
            self.window.after(0, lambda: self._display_image_main_thread(image_data))
        except Exception as e:
            print(f"Error loading image: {e}")
            self.window.after(0, self.enable_buttons)

    def _display_image_main_thread(self, image_data):
        """Display image on main thread and update UI state."""
        try:
            self.display_image(image_data)
        finally:
            self.enable_buttons()
            # Update API calls counter
            self.api_calls_left = self.image_handler.get_api_calls_left()
            self.api_counter_label.configure(
                text=f"API Calls: {self.api_calls_left}/95"
            )

    def disable_buttons(self):
        """Disable all interactive buttons."""
        self.find_button.configure(state="disabled")
        self.random_button.configure(state="disabled")
        
    def enable_buttons(self):
        """Enable all interactive buttons."""
        self.find_button.configure(state="normal")
        self.random_button.configure(state="normal")

    def display_image(self, image_data):
        """Display image for the given query."""
        if not image_data:
            # Clear previous image
            self.image_canvas.delete("all")
            
            # If no API calls left, show message
            if self.image_handler.get_api_calls_left() <= 0:
                self.image_canvas.create_text(
                    self.image_canvas.winfo_width() // 2,
                    self.image_canvas.winfo_height() // 2,
                    text="API limit reached for today\nPlease try again tomorrow",
                    fill="#DCE4EE",
                    font=("Arial", 14),
                    justify=tk.CENTER
                )
                return
            
            self.loading_label.configure(text="No image found")
            return
        
        try:
            # Clear previous image
            self.image_canvas.delete("all")
            
            # Create PhotoImage directly from base64 data
            photo = tk.PhotoImage(data=image_data)
            
            # Create image on canvas and center it
            self.image_canvas.create_image(
                self.image_canvas.winfo_width() // 2,
                self.image_canvas.winfo_height() // 2,
                image=photo,
                anchor=tk.CENTER
            )
            
            # Keep reference to prevent garbage collection
            self.image_canvas.image = photo
            
            # Show warning if less than 10 API calls left
            if self.image_handler.get_api_calls_left() <= 10:
                self.api_counter_label.configure(
                    text=f"Warning: only {self.image_handler.get_api_calls_left()} API calls left!",
                    text_color="red"
                )
        
        except Exception as e:
            print(f"Error displaying image: {e}")
            import traceback
            traceback.print_exc()  # Print full error trace
            self.loading_label.configure(text=f"Error displaying image: {str(e)}")
        finally:
            self.loading_label.place_forget()
            
    def random_date(self):
        """Get events for a random date."""
        event = self.api_handler.get_random_event()
        if event:
            self.current_event = event
            self.display_event(self.current_event)
            
    def next_event(self):
        """Display the next event."""
        if not self.current_event:
            return
            
        events = self.api_handler.get_events_by_date(
            self.current_event['month'],
            self.current_event['day']
        )
        
        if not events:
            return
            
        current_index = events.index(self.current_event)
        if current_index < len(events) - 1:
            self.current_event = events[current_index + 1]
            self.display_event(self.current_event)
            
    def prev_event(self):
        """Display the previous event."""
        if not self.current_event:
            return
            
        events = self.api_handler.get_events_by_date(
            self.current_event['month'],
            self.current_event['day']
        )
        
        if not events:
            return
            
        current_index = events.index(self.current_event)
        if current_index > 0:
            self.current_event = events[current_index - 1]
            self.display_event(self.current_event)
            
    def open_in_google(self):
        """Open current event in Google search."""
        if hasattr(self, 'current_event'):
            # Get year and description
            year = self.current_event['year']
            description = self.current_event['text']
            
            # Create search query
            query = f"{year} {description}"
            
            # URL encode the query
            encoded_query = urllib.parse.quote(query)
            
            # Create Google search URL
            url = f"https://www.google.com/search?q={encoded_query}"
            
            # Open in default browser
            webbrowser.open(url)
            
    def check_internet_connection(self):
        """Check if internet connection is available."""
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            self.is_online = True
            self.online_switch.select()
        except OSError:
            self.is_online = False
            self.online_switch.deselect()
            
    def add_google_search(self):
        """Add Google Custom Search element."""
        search_html = """
        <script async src="https://cse.google.com/cse.js?cx=76870cfb35dbb443a"></script>
        <div class="gcse-search"></div>
        """
        with open("google_search.html", "w", encoding="utf-8") as f:
            f.write(search_html)
            
    def run(self):
        """Start the GUI application."""
        self.window.mainloop()
