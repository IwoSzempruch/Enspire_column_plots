import os
import csv
import statistics
from logger_setup import logger

DATA_DIR = 'data'
MERGED_FILENAME = 'data_merged.csv'
RATIOS_FILENAME = 'ratios.csv'
REQUIRED_COLUMNS = {'Sample', 'Plate', 'Row', 'Column', 'Well', 'Measurement', 'Value'}


def read_data(path):
    """Read a CSV file and return a list of row dicts."""
    try:
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = [dict(row) for row in reader]
        return rows
    except Exception as e:
        logger.error("Nie udało się wczytać %s: %s", path, e)
        return []


def write_data(path, rows, fieldnames):
    """Write a list of dict rows to a CSV file with specified fieldnames."""
    try:
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        logger.info("Zapisano dane do %s", path)
    except Exception as e:
        logger.error("Nie udało się zapisać %s: %s", path, e)


def find_raw_files():
    """
    Find all input CSV files in DATA_DIR ending with '_data.csv'.
    Skip any existing merged or ratios outputs.
    """
    raw_files = []
    for fname in os.listdir(DATA_DIR):
        if not fname.lower().endswith('_data.csv'):
            continue
        if fname in {MERGED_FILENAME, RATIOS_FILENAME} or fname.endswith('_analysed.csv'):
            continue
        raw_files.append(os.path.join(DATA_DIR, fname))
    return sorted(raw_files)


def merge_data(file_paths):
    """
    Merge rows from all valid CSVs into a single list of rows.
    Ensure each file has the required columns; skip otherwise.
    Returns (merged_rows, all_fieldnames) where merged_rows have '_float_value' for internal use.
    """
    merged_rows = []
    all_fieldnames = set()

    for path in file_paths:
        rows = read_data(path)
        if not rows:
            logger.warning("Pominięto pusty lub nieczytelny plik: %s", path)
            continue

        header_cols = set(rows[0].keys())
        if not REQUIRED_COLUMNS.issubset(header_cols):
            missing = REQUIRED_COLUMNS - header_cols
            logger.warning(
                "Plik %s nie zawiera kolumn: %s; pomijam.",
                path, missing
            )
            continue

        all_fieldnames.update(rows[0].keys())

        for r in rows:
            try:
                r['_float_value'] = float(r['Value'])
                merged_rows.append(r)
            except ValueError:
                logger.warning(
                    "Nieprawidłowa wartość w kolumnie 'Value' w %s (Sample=%s, Measurement=%s); pomijam wiersz.",
                    path, r.get('Sample', ''), r.get('Measurement', '')
                )

    if not merged_rows:
        logger.error("Brak poprawnych danych do scalenia.")
        return [], []

    return merged_rows, list(all_fieldnames)


def strip_auxiliary(rows):
    """
    Remove internal-use keys like '_float_value' from each row dict.
    """
    for r in rows:
        r.pop('_float_value', None)


def compute_single_measurement_stats(rows):
    """
    Dla przypadków z jednym typem pomiaru:
    oblicz średnią i odchylenie standardowe dla każdej próbki (Sample)
    i dodaj kolumny 'Mean' oraz 'Std'.
    """
    by_sample = {}
    for r in rows:
        sample = r['Sample']
        value = r['_float_value']
        by_sample.setdefault(sample, []).append(value)

    stats = {}
    for sample, vals in by_sample.items():
        mean = statistics.mean(vals)
        std = statistics.stdev(vals) if len(vals) > 1 else 0.0
        stats[sample] = (mean, std)

    for r in rows:
        mean, std = stats[r['Sample']]
        r['Mean'] = f"{mean:.4f}"
        r['Std'] = f"{std:.4f}"


def compute_multi_measurement_stats(rows):
    """
    Dla przypadków z dwoma typami pomiaru (bez ratio):
    oblicz średnią i odchylenie standardowe dla każdej pary (Sample, Measurement)
    i dodaj kolumny 'Mean' oraz 'Std'.
    """
    by_sample_meas = {}
    for r in rows:
        key = (r['Sample'], r['Measurement'])
        value = r['_float_value']
        by_sample_meas.setdefault(key, []).append(value)

    stats = {}
    for key, vals in by_sample_meas.items():
        mean = statistics.mean(vals)
        std = statistics.stdev(vals) if len(vals) > 1 else 0.0
        stats[key] = (mean, std)

    for r in rows:
        mean, std = stats[(r['Sample'], r['Measurement'])]
        r['Mean'] = f"{mean:.4f}"
        r['Std'] = f"{std:.4f}"


def compute_and_write_ratios(rows, measurements):
    """
    Zapytaj użytkownika, które pomiary mają być licznikiem, a które mianownikiem,
    oblicz ratio dla każdej pary (Sample, Plate, Row, Column, Well),
    oblicz Mean i Std dla Ratio na poziomie Sample,
    i zapisz wynik do pliku 'ratios.csv'.
    """
    num = input(f"Podaj nazwę pomiaru, który ma być licznikiem spośród {measurements}: ").strip()
    den = input(f"Podaj nazwę pomiaru, który ma być mianownikiem spośród {measurements}: ").strip()

    if num not in measurements or den not in measurements:
        logger.error("Niepoprawne nazwy pomiarów: %s, %s", num, den)
        return

    denom_map = {}
    for r in rows:
        if r['Measurement'] == den:
            key = (r['Sample'], r['Plate'], r['Row'], r['Column'], r['Well'])
            denom_map[key] = r['_float_value']

    ratio_rows = []
    ratio_by_sample = {}

    for r in rows:
        if r['Measurement'] != num:
            continue
        key = (r['Sample'], r['Plate'], r['Row'], r['Column'], r['Well'])
        denom_value = denom_map.get(key)
        if denom_value is None:
            logger.warning(
                "Brak dopasowania mianownika dla Sample=%s, Plate=%s, Well=%s; pomijam ratio.",
                r['Sample'], r['Plate'], r['Well']
            )
            continue
        if denom_value == 0:
            logger.warning(
                "Mianownik równy zero dla Sample=%s, Plate=%s, Well=%s; pomijam ratio.",
                r['Sample'], r['Plate'], r['Well']
            )
            continue

        nom_value = r['_float_value']
        ratio = nom_value / denom_value

        ratio_row = {
            'Sample': r['Sample'],
            'Nominator_Plate': r['Plate'],
            'Nominator_Well': r['Well'],
            'Nominator_Measurement': num,
            'Nominator_Value': f"{nom_value:.4f}",
            'Denominator_Plate': r['Plate'],
            'Denominator_Well': r['Well'],
            'Denominator_Measurement': den,
            'Denominator_Value': f"{denom_value:.4f}",
            'Ratio': f"{ratio:.4f}"
        }
        ratio_rows.append(ratio_row)
        ratio_by_sample.setdefault(r['Sample'], []).append(ratio)

    if not ratio_rows:
        logger.error("Brak poprawnych par (licznik/mianownik) do obliczenia stosunków.")
        return

    ratio_stats = {}
    for sample, vals in ratio_by_sample.items():
        mean = statistics.mean(vals)
        std = statistics.stdev(vals) if len(vals) > 1 else 0.0
        ratio_stats[sample] = (mean, std)

    for r in ratio_rows:
        mean, std = ratio_stats[r['Sample']]
        r['Ratio_Mean'] = f"{mean:.4f}"
        r['Ratio_Std'] = f"{std:.4f}"

    fieldnames = [
        'Sample',
        'Nominator_Plate', 'Nominator_Well', 'Nominator_Measurement', 'Nominator_Value',
        'Denominator_Plate', 'Denominator_Well', 'Denominator_Measurement', 'Denominator_Value',
        'Ratio', 'Ratio_Mean', 'Ratio_Std'
    ]

    out_path = os.path.join(DATA_DIR, RATIOS_FILENAME)
    if os.path.exists(out_path):
        logger.info("Plik %s już istnieje i zostanie nadpisany.", RATIOS_FILENAME)
    write_data(out_path, ratio_rows, fieldnames)


def analyze_all():
    """
    Główna funkcja:
    1. Znajduje wszystkie pliki kończące się na '_data.csv'.
    2. Scala je w jeden data_merged.csv.
    3. Jeśli jest jeden typ pomiaru: oblicza Mean/Std per Sample.
       Jeśli są dwa typy pomiaru: oblicza Mean/Std per (Sample, Measurement), zapisuje merged,
       a następnie pyta, czy wygenerować ratios.csv.
    """
    raw_files = find_raw_files()
    if not raw_files:
        logger.error("Brak plików źródłowych do analizy w katalogu '%s'.", DATA_DIR)
        return

    merged_path = os.path.join(DATA_DIR, MERGED_FILENAME)
    if os.path.exists(merged_path):
        logger.info("Plik %s już istnieje i zostanie nadpisany.", MERGED_FILENAME)

    # Scal wszystkie dane
    merged_rows, base_fieldnames = merge_data(raw_files)
    if not merged_rows:
        return

    # Zbierz unikalne typy pomiarów
    measurement_types = sorted({r['Measurement'] for r in merged_rows})
    logger.info("Znalezione typy pomiarów: %s", measurement_types)

    # Utwórz kopię danych przed usunięciem '_float_value' do obliczenia ratio
    ratio_source_rows = [r.copy() for r in merged_rows]

    # Przygotuj początkowy zestaw kolumn do zapisania (bez '_float_value')
    initial_fieldnames = [fn for fn in base_fieldnames if fn != '_float_value']

    if len(measurement_types) == 1:
        compute_single_measurement_stats(merged_rows)
        strip_auxiliary(merged_rows)

        final_fieldnames = initial_fieldnames[:]
        if 'Mean' not in final_fieldnames:
            final_fieldnames.extend(['Mean', 'Std'])
        write_data(merged_path, merged_rows, final_fieldnames)

    elif len(measurement_types) == 2:
        compute_multi_measurement_stats(merged_rows)
        strip_auxiliary(merged_rows)

        final_fieldnames = initial_fieldnames[:]
        if 'Mean' not in final_fieldnames:
            final_fieldnames.extend(['Mean', 'Std'])
        write_data(merged_path, merged_rows, final_fieldnames)

        choice = input("Znaleziono dwa typy pomiarów. Czy chcesz obliczyć stosunki? (t/n): ").strip().lower()
        if choice == 't':
            compute_and_write_ratios(ratio_source_rows, measurement_types)
        else:
            logger.info("Pominięto generowanie pliku ratios.csv.")

    else:
        logger.error("Nieobsługiwana liczba typów pomiarów: %d. Oczekiwano 1 lub 2.", len(measurement_types))


if __name__ == '__main__':
    analyze_all()
