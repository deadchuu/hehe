"""
Portal historyczny - główny plik aplikacji
Ten moduł służy jako punkt wejścia do aplikacji portalu historycznego.
Inicjalizuje i uruchamia interfejs graficzny.

Wykorzystywane biblioteki:
- os: Operacje na ścieżkach systemowych
- sys: Modyfikacja ścieżki Pythona
- ui.gui: Własny moduł interfejsu graficznego
"""

import sys
import os

# Dodaj katalog główny projektu do ścieżki Pythona
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.gui import HistoryPortalGUI

def main():
    """Main function to run the application."""
    app = HistoryPortalGUI()
    app.run()

if __name__ == "__main__":
    main()
