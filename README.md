# Enspire Column Plots

Ten projekt zawiera zestaw modułów upraszczających pracę z danymi z czytnika EnSpire. Każdy moduł to osobny plik Pythona.

## Moduły

- `sample_mapper_generator.py` – kreator nazw prób oraz narzędzie do tworzenia pliku mapowania prób na studzienki.
- `mappings_assigner.py` – przypisuje pliki mapowań do plików wejściowych.
- `data_generator.py` – generuje uporządkowane dane na podstawie plików wejściowych i mapowania.
- `data_analyser.py` – oblicza statystyki i (opcjonalnie) stosunki między pomiarami.
- `interactive_plot_selector.py` – prosty interaktywny wykres środków i odchyleń standardowych.
- `main.py` – menu łączące działanie wszystkich modułów.

Wszystkie komunikaty diagnostyczne są wyświetlane na konsoli oraz zapisywane w pliku `logs/program.log`.

## Używanie

Uruchom `python3 main.py` i postępuj zgodnie z instrukcjami w menu. Poszczególne katalogi (`input`, `mappings`, `data`, `configs`, `logs`) są tworzone automatycznie.

