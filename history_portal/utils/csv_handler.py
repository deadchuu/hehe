"""
Moduł obsługi plików CSV dla portalu historycznego.

Ten moduł jest odpowiedzialny za:
- Zapisywanie wydarzeń historycznych do pliku CSV
- Odczytywanie wydarzeń z pliku CSV
- Zarządzanie pamięcią podręczną wydarzeń

Wykorzystywane biblioteki:
- csv: Obsługa plików CSV
- os: Operacje na systemie plików
- random: Wybór losowych wydarzeń
- datetime: Operacje na datach
"""

import csv
import os
import random
from datetime import datetime

class CSVHandler:
    """
    Klasa obsługująca operacje na plikach CSV.
    Zapewnia funkcjonalność pamięci podręcznej dla wydarzeń historycznych.
    """
    
    def __init__(self, filename="database/events.csv"):
        """
        Inicjalizacja obsługi CSV.
        Tworzy plik CSV jeśli nie istnieje.
        """
        self.filename = filename
        self.init_csv()

    def init_csv(self):
        """
        Inicjalizacja pliku CSV.
        Tworzy plik CSV jeśli nie istnieje.
        """
        os.makedirs(os.path.dirname(self.filename), exist_ok=True)
        if not os.path.exists(self.filename):
            with open(self.filename, "w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(["Date", "Year", "Title", "Description"])

    def get_events_by_date(self, month, day):
        """
        Pobieranie wydarzeń dla określonej daty.
        
        Args:
            month (int): Miesiąc (1-12)
            day (int): Dzień (1-31)
            
        Returns:
            list: Lista wydarzeń dla danej daty
        """
        events = []
        if os.path.exists(self.filename):
            with open(self.filename, "r", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                date_pattern = f"-{int(month):02d}-{int(day):02d}"
                for row in reader:
                    if row["Date"].endswith(date_pattern):
                        events.append({
                            "year": row["Year"],
                            "text": row["Description"]
                        })
        return events

    def get_random_event(self):
        """
        Pobieranie losowego wydarzenia z pliku CSV.
        
        Returns:
            dict: Losowe wydarzenie lub None w przypadku błędu
        """
        if not os.path.exists(self.filename):
            return None
            
        try:
            with open(self.filename, "r", encoding="utf-8") as file:
                reader = list(csv.DictReader(file))
                if not reader:
                    return None
                    
                event = random.choice(reader)
                return {
                    "year": event["Year"],
                    "text": event["Description"]
                }
        except Exception as e:
            print(f"Błąd podczas pobierania losowego wydarzenia: {e}")
            return None

    def save_api_events(self, month, day, events):
        """
        Zapisanie wydarzeń z API do pliku CSV.
        
        Args:
            month (str): Miesiąc (1-12)
            day (str): Dzień (1-31)
            events (list): Lista wydarzeń z API
        """
        date = f"{datetime.now().year}-{int(month):02d}-{int(day):02d}"
        for event in events:
            self.add_event(
                date=date,
                year=event["year"],
                title=f"Event from {event['year']}",
                description=event["text"]
            )

    def add_event(self, date, year, title, description):
        """
        Dodanie nowego wydarzenia do pliku CSV.
        
        Args:
            date (str): Data wydarzenia (format: RRRR-MM-DD)
            year (str): Rok wydarzenia
            title (str): Tytuł wydarzenia
            description (str): Opis wydarzenia
        """
        with open(self.filename, "a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([date, year, title, description])

    def check_date_exists(self, month, day):
        """
        Sprawdzenie czy wydarzenia dla danej daty istnieją w CSV.
        
        Args:
            month (int): Miesiąc (1-12)
            day (int): Dzień (1-31)
            
        Returns:
            bool: True jeśli wydarzenia istnieją, False w przeciwnym razie
        """
        if os.path.exists(self.filename):
            with open(self.filename, "r", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                date_pattern = f"-{int(month):02d}-{int(day):02d}"
                for row in reader:
                    if row["Date"].endswith(date_pattern):
                        return True
        return False
