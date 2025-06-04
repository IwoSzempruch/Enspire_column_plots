import csv
import os
from logger_setup import logger

DATA_DIR = 'data'
MAPPING_DIR = 'mappings'
ASSIGNMENT_FILE = os.path.join(MAPPING_DIR, 'assignment.csv')

os.makedirs(DATA_DIR, exist_ok=True)


def load_assignments(path: str = ASSIGNMENT_FILE):
    """Load input to mapping assignments from a file."""
    assignments = []
    if not os.path.exists(path):
        logger.error('Assignment file %s not found', path)
        return assignments
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=';')
        for row in reader:
            if len(row) >= 2:
                assignments.append((row[0], row[1]))
    logger.debug('Loaded assignments: %s', assignments)
    return assignments


def read_mapping(path):
    logger.debug('Reading mapping %s', path)
    mapping = {}
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        cols = next(reader)[1:]
        for row in reader:
            if not row:
                continue
            row_label = row[0]
            for c, sample in zip(cols, row[1:]):
                well = f'{row_label}{c}'
                mapping[well] = sample.strip()
    return mapping


def parse_input(path):
    logger.debug('Parsing input file %s', path)
    results = []
    with open(path, encoding='utf-8') as f:
        lines = [line.strip() for line in f]
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith('Results for'):
            meas = line.split('Results for')[1].split('-')[0].strip()
            logger.debug('Found measurement %s', meas)
            i += 2  # skip header
            for r in range(8):
                parts = lines[i].split(',')
                row_label = parts[0]
                values = parts[2:14]
                for c_idx, val in enumerate(values, start=1):
                    if val:
                        try:
                            value = float(val)
                        except ValueError:
                            logger.warning('Invalid value %s in %s', val, path)
                            continue
                        results.append((row_label, c_idx, meas, value))
                i += 1
            continue
        i += 1
    return results


def generate_data(input_file, mapping_file):
    logger.info('Generating data from %s with mapping %s', input_file, mapping_file)
    mapping = read_mapping(mapping_file)
    data = parse_input(input_file)
    plate_name = os.path.splitext(os.path.basename(input_file))[0]
    out_path = os.path.join(DATA_DIR, plate_name + '_data.csv')
    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Sample','Plate','Row','Column','Well','Measurement','Value'])
        for row_label, col_idx, meas, value in data:
            well = f'{row_label}{col_idx:02d}'
            sample = mapping.get(well, '')
            writer.writerow([sample, plate_name, row_label, col_idx, well, meas, value])
    logger.info('Saved data to %s', out_path)
    return out_path


def generate_all_from_assignment(path: str = ASSIGNMENT_FILE):
    """Generate data for all pairs from the assignment file."""
    outputs = []
    for input_file, mapping_file in load_assignments(path):
        try:
            out = generate_data(input_file, mapping_file)
            outputs.append(out)
        except Exception as e:
            logger.exception('Error generating data for %s: %s', input_file, e)
    return outputs

if __name__ == '__main__':
    print('Ten moduł powinien być użyty poprzez main.py')
