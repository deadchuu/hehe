# History Portal - Portal Historyczny

## Opis
History Portal to aplikacja desktopowa, która pozwala użytkownikom odkrywać wydarzenia historyczne z różnych dat. Program prezentuje wydarzenia wraz z powiązanymi obrazami, umożliwiając interaktywne poznawanie historii.

## Funkcje
- **Wyszukiwanie wydarzeń historycznych** - wybierz dowolną datę, aby zobaczyć co się wydarzyło tego dnia w historii
- **Wyświetlanie obrazów** - dla każdego wydarzenia wyświetlany jest powiązany obraz
- **Tryb online/offline** - możliwość pracy w trybie online (z pobieraniem nowych obrazów) lub offline (tylko z pamięci podręcznej)
- **Limit API** - program śledzi liczbę zapytań API (95 dziennie) i wyświetla odpowiednie ostrzeżenia
- **Przycisk "Read More"** - szybki dostęp do szczegółowych informacji o wydarzeniu poprzez wyszukiwarkę Google

## Obsługa programu

### Podstawowe funkcje:
1. **Wybór daty**:
   - Użyj kalendarza lub wpisz datę ręcznie
   - Kliknij "Find Events" aby wyświetlić wydarzenia

2. **Przeglądanie wydarzeń**:
   - Wydarzenia są wyświetlane w głównym oknie
   - Użyj przycisków "Next" aby przejść do kolejnego wydarzenia
   - Kliknij "Read More" aby otworzyć szczegółowe informacje w przeglądarce

3. **Tryb online/offline**:
   - Przełącznik w górnej części okna
   - Online: pobiera nowe obrazy z internetu
   - Offline: używa tylko zapisanych obrazów

### Limity i ostrzeżenia:
- Program ma limit 95 zapytań API dziennie
- Licznik pozostałych zapytań jest wyświetlany
- Przy 10 pozostałych zapytaniach pojawia się ostrzeżenie
- Po wyczerpaniu limitu program automatycznie przechodzi w tryb offline

## Wymagania techniczne
- Python 3.x
- Dostęp do internetu (dla trybu online)
- Klucz API Google Custom Search
- Identyfikator wyszukiwarki niestandardowej Google

## Uwagi
- Obrazy są zapisywane w pamięci podręcznej dla szybszego dostępu
- Program obsługuje tylko obrazy w formacie PNG
- Limit API odnawia się codziennie
- W trybie offline dostępne są tylko wcześniej pobrane obrazy
