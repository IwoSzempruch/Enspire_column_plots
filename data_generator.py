#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import os
import sys
import logging

# ------------------------- USTAWIENIA LOGOWANIA -------------------------

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stream=sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)

# ------------------------- STAŁE -------------------------

DATA_DIR = 'data'
MAPPING_DIR = 'mappings'
ASSIGNMENT_FILE = os.path.join(MAPPING_DIR, 'assignment.csv')

# ------------------------- FUNKCJE POMOCNICZE -------------------------

def load_assignments(path: str = ASSIGNMENT_FILE):
    """
    Wczytuje z pliku assignment.csv pary (ścieżka_do_pliku_wejściowego, ścieżka_do_pliku_mapującego).
    Plik powinien być kodowany UTF-8, a pola rozdzielone średnikami.
    Normalizuje ścieżki, aby działało zarówno na Windows, jak i na Linuxie.
    """
    assignments = []
    if not os.path.exists(path):
        logger.error('Plik assignment nie znaleziony: %s', path)
        return assignments

    with open(path, newline='', encoding='utf-8', errors='replace') as f:
        reader = csv.reader(f, delimiter=';')
        for idx, row in enumerate(reader, start=1):
            if len(row) < 2:
                logger.warning('Pominięto wiersz %d w %s – brak co najmniej 2 kolumn', idx, path)
                continue
            infile = row[0].strip()
            mapfile = row[1].strip()
            if infile and mapfile:
                infile_norm = os.path.normpath(infile)
                mapfile_norm = os.path.normpath(mapfile)
                assignments.append((infile_norm, mapfile_norm))
            else:
                logger.warning('Pominięto wiersz %d w %s – puste ścieżki', idx, path)

    logger.info('Załadowano %d przypisań', len(assignments))
    return assignments


def read_mapping(path: str) -> dict:
    """
    Wczytuje mapowanie z pliku CSV. Zakłada, że:
    - Pierwszy wiersz: pusta komórka w pierwszej kolumnie, a w kolejnych nagłówki "01","02",...,"12"
    - Kolejne wiersze: litera_wiersza, nazwa_próbki_kolumna_01, nazwa_próbki_kolumna_02, ..., nazwa_próbki_kolumna_12
    Zwraca słownik tylko dla niepustych próbek: {'A01': '1M_CAA', 'A02': '2M_CAA', ...}
    """
    if not os.path.exists(path):
        logger.error('Plik mapowania nie istnieje: %s', path)
        return {}

    mapping = {}
    try:
        with open(path, newline='', encoding='utf-8', errors='replace') as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if not header or len(header) < 2:
                logger.error('Nieprawidłowy format nagłówka w pliku mapującym: %s', path)
                return {}

            cols = header[1:]  # np. ["01","02",..., "12"]
            for row_idx, row in enumerate(reader, start=2):
                if not row or len(row) < 2:
                    continue
                row_label = row[0].strip()
                if not row_label:
                    continue
                for col_idx, sample in enumerate(row[1:], start=0):
                    if col_idx >= len(cols):
                        break
                    col_name = cols[col_idx].strip()
                    sample_name = sample.strip()
                    # Dodajemy tylko, gdy sample_name nie jest pusty
                    if row_label and col_name and sample_name:
                        well = f'{row_label}{col_name}'
                        mapping[well] = sample_name
    except Exception as e:
        logger.error('Błąd podczas czytania mapowania %s: %s', path, e)
        return {}

    logger.debug('Wczytano %d wpisów mapujących z %s', len(mapping), path)
    return mapping


def parse_input(path: str) -> list:
    """
    Parsuje plik wejściowy EnSpire i wyciąga wszystkie rekordy:
    [(row_label, column_index, measurement_name, value), ...]
    Szuka bloków zaczynających się od linii "Results for Meas X - ...", następnie
    czyta kolejne 8 wierszy (A–H) z wartościami w kolumnach 01–12.
    """
    results = []
    if not os.path.exists(path):
        logger.error('Plik wejściowy nie istnieje: %s', path)
        return results

    encoding_used = 'cp1250'
    try:
        with open(path, encoding=encoding_used, errors='replace') as f:
            lines = [line.rstrip('\n') for line in f]
    except Exception as e:
        logger.error("Nie udało się wczytać '%s' z kodowaniem %s: %s", path, encoding_used, e)
        return results

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('Results for'):
            try:
                meas = line.split('Results for')[1].split('-')[0].strip()
            except Exception:
                meas = line
            logger.debug('Znaleziono pomiar: %s w pliku %s (linia %d)', meas, path, i+1)

            i += 1
            if i >= len(lines):
                break
            if not lines[i].startswith(','):
                continue

            for row_offset in range(1, 9):
                if i + row_offset >= len(lines):
                    break
                data_line = lines[i + row_offset]
                parts = data_line.split(',')
                if len(parts) < 2:
                    continue
                row_label = parts[0].strip()
                values = parts[1:13]  # kolumny 01–12
                for c_idx, val in enumerate(values, start=1):
                    if val and val.strip():
                        try:
                            numeric_value = float(val.replace(',', '.'))
                        except ValueError:
                            logger.warning('Nieprawidłowa wartość "%s" w %s (wiersz %s, kolumna %02d)', val, path, row_label, c_idx)
                            continue
                        results.append((row_label, c_idx, meas, numeric_value))

            i += 9
            continue

        i += 1

    logger.debug('Wyników pomiaru w pliku %s: %d rekordów', path, len(results))
    return results


def generate_data(input_file: str, mapping_file: str) -> str:
    """
    Generuje plik CSV z połączonych danych z pliku wejściowego i mapowania.
    Plik wyjściowy zapisywany jest w strukturze data/[ścieżka_z_input_po_input/...].
    Zwraca ścieżkę do wygenerowanego pliku lub pusty string w razie błędu.
    """
    if not os.path.exists(input_file):
        logger.error('Plik wejściowy nie znaleziony: %s', input_file)
        return ''

    if not os.path.exists(mapping_file):
        logger.error('Plik mapujący nie znaleziony: %s', mapping_file)
        return ''

    logger.info('Przetwarzanie:\n  Wejście:  %s\n  Mapowanie: %s', input_file, mapping_file)
    mapping = read_mapping(mapping_file)
    if not mapping:
        logger.warning('Mapowanie jest puste – nie zapiszę pliku wyjściowego dla %s', input_file)
        return ''

    data = parse_input(input_file)
    if not data:
        logger.warning('Brak danych do zapisania z pliku %s', input_file)
        return ''

    plate_name = os.path.splitext(os.path.basename(input_file))[0]
    out_filename = f'{plate_name}_data.csv'

    input_dir = os.path.dirname(input_file)
    normalized_input_dir = os.path.normpath(input_dir)
    out_dir = DATA_DIR

    rel_dir = None
    try:
        base_input = os.path.normpath('input')
        if normalized_input_dir.startswith(base_input + os.sep) or normalized_input_dir == base_input:
            rel_dir = os.path.relpath(normalized_input_dir, base_input)
        else:
            rel_dir = os.path.basename(normalized_input_dir)
    except Exception:
        rel_dir = os.path.basename(normalized_input_dir)

    if rel_dir and rel_dir != os.curdir:
        out_dir = os.path.join(DATA_DIR, rel_dir)

    try:
        os.makedirs(out_dir, exist_ok=True)
    except Exception as e:
        logger.error('Nie udało się utworzyć katalogu %s: %s', out_dir, e)
        return ''

    out_path = os.path.join(out_dir, out_filename)

    try:
        with open(out_path, 'w', newline='', encoding='utf-8') as fout:
            writer = csv.writer(fout)
            writer.writerow(['Sample', 'Plate', 'Row', 'Column', 'Well', 'Measurement', 'Value'])
            for row_label, col_idx, meas, value in data:
                well = f'{row_label}{col_idx:02d}'
                sample = mapping.get(well, '')
                writer.writerow([sample, plate_name, row_label, col_idx, well, meas, value])
    except Exception as e:
        logger.error('Błąd podczas zapisywania pliku %s: %s', out_path, e)
        return ''

    logger.info('Zapisano dane do: %s', out_path)
    print(f'✅ Wygenerowano dane z {os.path.basename(input_file)} → {out_path}')
    return out_path


def generate_all_from_assignment(path: str = ASSIGNMENT_FILE) -> list:
    """
    Dla każdej pary (plik_wejściowy, plik_mapujący) wywołuje generate_data.
    Zwraca listę ścieżek do wygenerowanych plików.
    """
    outputs = []
    assignments = load_assignments(path)
    if not assignments:
        logger.error('Brak przypisań do przetworzenia.')
        return outputs

    for infile, mapfile in assignments:
        try:
            out = generate_data(infile, mapfile)
            if out:
                outputs.append(out)
        except Exception as e:
            logger.exception('Błąd podczas generowania danych dla %s: %s', infile, e)

    logger.info('Łącznie wygenerowano %d plików', len(outputs))
    return outputs


# ------------------------- URUCHAMIANIE JAKO SKRYPT -------------------------

if __name__ == '__main__':
    """
    Skrypt uruchamiamy w ten sposób:
        python data-generator.py
    lub
        python3 data-generator.py
    """
    generate_all_from_assignment()
