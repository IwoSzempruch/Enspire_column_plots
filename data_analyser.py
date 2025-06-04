import csv
import os
import statistics
from logger_setup import logger

DATA_DIR = 'data'


def read_data(path):
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = [dict(row) for row in reader]
    return rows


def write_data(path, rows, fieldnames):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def analyze_file(path):
    logger.info('Analyzing %s', path)
    rows = read_data(path)
    if not rows:
        logger.warning('No data in %s', path)
        return
    meas_types = sorted(set(r['Measurement'] for r in rows))
    logger.debug('Measurement types: %s', meas_types)
    if len(meas_types) == 1:
        m = meas_types[0]
        by_sample = {}
        for r in rows:
            sample = r['Sample']
            value = float(r['Value'])
            by_sample.setdefault(sample, []).append(value)
        stats = {s:(statistics.mean(v), statistics.stdev(v) if len(v)>1 else 0.0) for s,v in by_sample.items()}
        for r in rows:
            mean, std = stats[r['Sample']]
            r['Mean'] = f'{mean:.4f}'
            r['Std'] = f'{std:.4f}'
        out_path = path.replace('.csv','_analysed.csv')
        fieldnames = list(rows[0].keys())
        write_data(out_path, rows, fieldnames)
        logger.info('Saved analysed data to %s', out_path)
    elif len(meas_types) == 2:
        num = input(f'Podaj licznik {meas_types}: ')
        den = input(f'Podaj mianownik {meas_types}: ')
        if num not in meas_types or den not in meas_types:
            logger.error('Niepoprawne nazwy pomiarów')
            return
        # create mapping for denominator values
        denom_map = {}
        for r in rows:
            if r['Measurement'] == den:
                key = (r['Sample'], r['Plate'], r['Row'], r['Column'])
                denom_map[key] = float(r['Value'])
        ratio_values = {}
        for r in rows:
            if r['Measurement'] == num:
                key = (r['Sample'], r['Plate'], r['Row'], r['Column'])
                denom = denom_map.get(key)
                if denom is not None and float(denom) != 0:
                    ratio = float(r['Value']) / denom
                    r['Denominator_Sample'] = r['Sample']
                    r['Denominator_Plate'] = r['Plate']
                    r['Denominator_Row'] = r['Row']
                    r['Denominator_Column'] = r['Column']
                    r['Denominator_Well'] = r['Well']
                    r['Denominator_Measurement'] = den
                    r['Denominator_Value'] = denom
                    r['Ratio'] = ratio
                    ratio_values.setdefault(r['Sample'], []).append(ratio)
                else:
                    r['Ratio'] = ''
        ratio_stats = {s:(statistics.mean(v), statistics.stdev(v) if len(v)>1 else 0.0) for s,v in ratio_values.items()}
        for r in rows:
            if r['Measurement'] == num and r['Ratio'] != '':
                mean, std = ratio_stats[r['Sample']]
                r['Ratio_Mean'] = f'{mean:.4f}'
                r['Ratio_Std'] = f'{std:.4f}'
        out_path = path.replace('.csv','_analysed.csv')
        fieldnames = list(rows[0].keys())
        if 'Ratio_Mean' in rows[0]:
            fieldnames.extend(['Ratio_Mean','Ratio_Std'])
        write_data(out_path, rows, fieldnames)
        logger.info('Saved analysed data to %s', out_path)
    else:
        logger.error('Nieobługiwane liczba typów pomiarów: %s', meas_types)


def analyze_all():
    files = [f for f in os.listdir(DATA_DIR) if f.endswith('_data.csv')]
    for f in files:
        analyze_file(os.path.join(DATA_DIR, f))

if __name__ == '__main__':
    analyze_all()
