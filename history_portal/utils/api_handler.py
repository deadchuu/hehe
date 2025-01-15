"""
Moduł obsługi API dla portalu historycznego.

Ten moduł jest odpowiedzialny za:
- Pobieranie wydarzeń historycznych z zewnętrznego API
- Zarządzanie trybem online/offline
- Obsługę błędów połączenia
- Zapisywanie danych do pamięci podręcznej CSV

Wykorzystywane biblioteki:
- requests: Obsługa żądań HTTP
- socket: Sprawdzanie połączenia internetowego
"""

import requests
import socket
import random
from datetime import datetime, timedelta
from utils.csv_handler import CSVHandler

class APIHandler:
    """
    Klasa obsługująca interakcje z API wydarzeń historycznych.
    Zapewnia funkcjonalność online i offline poprzez pamięć podręczną CSV.
    """
    
    def __init__(self):
        """Inicjalizacja obsługi API z domyślnym trybem online."""
        self.online_mode = True
        self.csv_handler = CSVHandler()
        
    def check_internet(self, host="8.8.8.8", port=53, timeout=3):
        """
        Sprawdzenie połączenia internetowego.
        
        Args:
            host (str): Host do sprawdzenia (domyślnie Google DNS)
            port (int): Port do sprawdzenia
            timeout (int): Limit czasu w sekundach
            
        Returns:
            bool: True jeśli jest połączenie, False w przeciwnym razie
        """
        try:
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
            self.online_mode = True
            return True
        except socket.error:
            self.online_mode = False
            return False
            
    def get_events_by_date(self, month, day):
        """
        Pobieranie wydarzeń dla określonej daty.
        
        Args:
            month (str): Miesiąc (1-12)
            day (str): Dzień (1-31)
            
        Returns:
            list: Lista wydarzeń historycznych
        """
        if not self.online_mode:
            return self.csv_handler.get_events_by_date(month, day)
            
        # Sprawdzenie czy mamy wydarzenia w pamięci podręcznej
        if self.csv_handler.check_date_exists(month, day):
            return self.csv_handler.get_events_by_date(month, day)
            
        # Pobieranie z API
        url = f"https://history.muffinlabs.com/date/{month}/{day}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if "data" not in data or "Events" not in data["data"]:
                    print("Błąd API: Nieprawidłowy format odpowiedzi")
                    return []
                    
                api_events = data["data"]["Events"]
                events = []
                for event in api_events:
                    # Sprawdzenie czy wydarzenie ma wymagane pola
                    if "year" in event and "text" in event:
                        events.append({
                            "year": str(event["year"]),
                            "text": event["text"],
                            "day": int(day),
                            "month": int(month)
                        })
                # Zapisanie do CSV dla dostępu offline
                if events:
                    self.csv_handler.save_api_events(month, day, events)
                return events
            else:
                print(f"Błąd API: {response.status_code}")
                return []
        except Exception as e:
            print(f"Błąd API: {e}")
            return []
            
    def get_event(self, day, month):
        """
        Pobieranie pojedynczego wydarzenia dla danej daty.
        
        Args:
            day (int): Dzień (1-31)
            month (int): Miesiąc (1-12)
            
        Returns:
            dict: Wydarzenie historyczne lub None w przypadku błędu
        """
        events = self.get_events_by_date(str(month), str(day))
        return events[0] if events else None
        
    def get_prev_event(self, day, month):
        """
        Pobieranie wydarzenia z poprzedniego dnia.
        
        Args:
            day (int): Aktualny dzień
            month (int): Aktualny miesiąc
            
        Returns:
            dict: Poprzednie wydarzenie lub None
        """
        # Oblicz poprzednią datę
        date = datetime(2025, month, day)  # Rok nie ma znaczenia
        prev_date = date - timedelta(days=1)
        
        # Pobierz wydarzenia dla poprzedniej daty
        events = self.get_events_by_date(str(prev_date.month), str(prev_date.day))
        return events[0] if events else None
        
    def get_next_event(self, day, month):
        """
        Pobieranie wydarzenia z następnego dnia.
        
        Args:
            day (int): Aktualny dzień
            month (int): Aktualny miesiąc
            
        Returns:
            dict: Następne wydarzenie lub None
        """
        # Oblicz następną datę
        date = datetime(2025, month, day)  # Rok nie ma znaczenia
        next_date = date + timedelta(days=1)
        
        # Pobierz wydarzenia dla następnej daty
        events = self.get_events_by_date(str(next_date.month), str(next_date.day))
        return events[0] if events else None
        
    def get_random_event(self):
        """
        Pobieranie losowego wydarzenia.
        
        Returns:
            dict: Losowe wydarzenie historyczne lub None w przypadku błędu
        """
        # W trybie offline używamy tylko danych z CSV
        if not self.online_mode:
            return self.csv_handler.get_random_event()
            
        # Losowy miesiąc i dzień
        month = str(random.randint(1, 12))
        day = str(random.randint(1, 28))  # Używamy 28 aby uniknąć problemów z lutym
        
        # Pobieranie wydarzeń dla losowej daty
        events = self.get_events_by_date(month, day)
        return random.choice(events) if events else None
