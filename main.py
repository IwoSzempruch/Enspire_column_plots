import os
import shutil
from logger_setup import logger
import sample_mapper_generator
import mappings_assigner
import data_generator
import data_analyser
import interactive_plot_selector

ROOT_DIR = os.getcwd()
INPUT_DIR = 'input'
MAPPING_DIR = 'mappings'
DATA_DIR = 'data'
CONFIG_DIR = 'configs'

for d in [INPUT_DIR, MAPPING_DIR, DATA_DIR, CONFIG_DIR]:
    os.makedirs(d, exist_ok=True)


def copy_input_files(paths):
    for p in paths:
        dst = os.path.join(INPUT_DIR, os.path.basename(p))
        if not os.path.exists(dst):
            shutil.copy(p, dst)
            logger.info('Copied %s to %s', p, dst)


def main_menu():
    while True:
        print('\nWybierz opcję:')
        print('1 - Generator mappingu')
        print('2 - Przypisz mappingi do plików')
        print('3 - Generuj dane')
        print('4 - Analiza danych')
        print('5 - Interaktywny wykres')
        print('0 - Zakończ')
        choice = input('> ')
        if choice == '1':
            app = sample_mapper_generator.SampleMapperGenerator()
            app.run()
        elif choice == '2':
            assigner = mappings_assigner.MappingAssigner()
            pairs = assigner.run()
            if pairs:
                copy_input_files([p[0] for p in pairs])
                with open('mapping_pairs.txt', 'w', encoding='utf-8') as f:
                    for p in pairs:
                        f.write(f'{p[0]};{p[1]}\n')
        elif choice == '3':
            if not os.path.exists('mapping_pairs.txt'):
                print('Brak przypisanych plików. Najpierw użyj opcji 2.')
                continue
            with open('mapping_pairs.txt', encoding='utf-8') as f:
                pairs = [line.strip().split(';') for line in f if line.strip()]
            for input_file, mapping_file in pairs:
                try:
                    data_generator.generate_data(input_file, mapping_file)
                except Exception as e:
                    logger.exception('Błąd podczas generowania danych: %s', e)
            print('Generowanie danych zakończone')
        elif choice == '4':
            data_analyser.analyze_all()
            print('Analiza zakończona')
        elif choice == '5':
            app = interactive_plot_selector.PlotSelector()
            app.run()
        elif choice == '0':
            break
        else:
            print('Nieznana opcja')

if __name__ == '__main__':
    main_menu()
