"""
Graphical user interface module for the history portal.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import base64
from io import BytesIO
from utils.api_handler import APIHandler
from utils.image_handler import ImageHandler
import socket
import webbrowser
import threading
import time

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
        # Image label
        self.image_label = tk.Label(self.left_frame, bg="#2b2b2b", fg="white")
        self.image_label.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Loading animation below image
        self.loading_animation = LoadingAnimation(
            self.left_frame,
            width=int(self.window.winfo_screenwidth() * 0.4),
            height=4
        )
        self.loading_animation.pack(fill="x", padx=10, pady=(0, 10))
        
    def create_right_panel(self):
        """Create the right panel with controls and text display."""
        # Input fields frame
        input_frame = ctk.CTkFrame(self.right_frame)
        input_frame.pack(fill="x", padx=10, pady=10)
        
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
        
        # Buttons frame
        button_frame = ctk.CTkFrame(self.right_frame)
        button_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # Control buttons
        self.find_button = ctk.CTkButton(
            button_frame,
            text="Find Event",
            command=self.find_events
        )
        self.find_button.pack(fill="x", padx=5, pady=2)
        
        self.random_button = ctk.CTkButton(
            button_frame,
            text="Random Event",
            command=self.random_date
        )
        self.random_button.pack(fill="x", padx=5, pady=2)
        
        self.next_button = ctk.CTkButton(
            button_frame,
            text="Next Event",
            command=self.next_event
        )
        self.next_button.pack(fill="x", padx=5, pady=2)
        
        # Online mode frame
        mode_frame = ctk.CTkFrame(self.right_frame)
        mode_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # Online mode switch
        self.online_switch = ctk.CTkSwitch(
            mode_frame,
            text="Online Mode",
            command=self.toggle_online_mode,
            onvalue=True,
            offvalue=False
        )
        self.online_switch.pack(pady=5)
        self.online_switch.select()
        
        # API calls counter
        self.api_calls_label = ctk.CTkLabel(
            mode_frame,
            text=f"API Calls Left Today: {self.api_calls_left}"
        )
        self.api_calls_label.pack(pady=5)
        
        # Event text display
        self.event_text = ctk.CTkTextbox(
            self.right_frame,
            height=400,
            wrap="word"
        )
        self.event_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Read more button at the bottom
        self.read_more_button = ctk.CTkButton(
            self.right_frame,
            text="Read More",
            command=self.open_wiki
        )
        self.read_more_button.pack(fill="x", padx=10, pady=(0, 10))
        
    def toggle_online_mode(self):
        """Toggle between online and offline modes."""
        self.is_online = self.online_switch.get()
        
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
        """Display the event and its related image."""
        if not event:
            return
            
        # Display event text
        self.event_text.delete("1.0", tk.END)
        self.event_text.insert("1.0", f"Year: {event['year']}\n\n{event['text']}")
        
        # Display related image
        if self.is_online:
            # Create search query from event
            query = f"{event['text']} {event['year']} historical event"
            self.display_image(query)
            
            # Update API calls counter
            self.api_calls_left = self.image_handler.get_api_calls_left()
            self.api_calls_label.configure(
                text=f"API Calls Left Today: {self.api_calls_left}"
            )
            
    def display_image(self, query):
        """Display image for the given query."""
        try:
            if not self.is_online:
                self.image_label.configure(text="Images not available in offline mode")
                return
                
            self.start_loading_animation()
            
            def load_image():
                try:
                    image_data = self.image_handler.get_image_base64(query)
                    if not image_data:
                        self.window.after(0, lambda: self.image_label.configure(text="No image found"))
                        return
                        
                    image = tk.PhotoImage(data=image_data)
                    self.window.after(0, lambda: self.update_image_label(image))
                    
                except Exception as e:
                    print(f"Error displaying image: {e}")
                    self.window.after(0, lambda: self.image_label.configure(text="Error displaying image"))
                finally:
                    self.window.after(0, self.stop_loading_animation)
                    
            threading.Thread(target=load_image, daemon=True).start()
            
        except Exception as e:
            print(f"Error in display_image: {e}")
            self.stop_loading_animation()
            self.image_label.configure(text="Error displaying image")
            
    def update_image_label(self, photo):
        """Update image label with new photo."""
        self.current_image = photo
        self.image_label.configure(image=photo)
        
    def start_loading_animation(self):
        """Start loading animation and disable buttons."""
        self.find_button.configure(state="disabled")
        self.random_button.configure(state="disabled")
        self.next_button.configure(state="disabled")
        self.loading_animation.start()
        
    def stop_loading_animation(self):
        """Stop loading animation and enable buttons."""
        self.find_button.configure(state="normal")
        self.random_button.configure(state="normal")
        self.next_button.configure(state="normal")
        self.loading_animation.stop()
        
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
            
    def open_wiki(self):
        """Open Wikipedia article for the current event."""
        if self.current_event and 'link' in self.current_event:
            webbrowser.open(self.current_event['link'])
            
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
