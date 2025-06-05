import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import csv
from logger_setup import logger

MAPPING_DIR = 'mappings'
INPUT_DIR = 'input'

class MappingAssigner:
    def __init__(self):
        logger.info('Initializing MappingAssigner')
        os.makedirs(MAPPING_DIR, exist_ok=True)
        os.makedirs(INPUT_DIR, exist_ok=True)
        self.root = tk.Tk()
        self.root.title('Mappings Assigner')
        self.file_rows = []
        self._build_gui()

    def _build_gui(self):
        # Przycisk do wyboru katalogów wejściowych
        select_btn = ttk.Button(self.root, text='Wybierz katalogi wejściowe', command=self.choose_dirs)
        select_btn.pack(pady=5)

        # Kontener na tabelę plików i ich przypisań
        self.table_frame = ttk.Frame(self.root)
        self.table_frame.pack(padx=10, pady=10)

        # Przycisk do przypisania jednego mappingu do wszystkich plików
        self.assign_all_btn = ttk.Button(self.root, text='Przypisz mapping do wszystkich', command=self.assign_all)
        self.assign_all_btn.pack(pady=5)
        self.assign_all_btn['state'] = 'disabled'  # Domyślnie wyłączony, włącza się po załadowaniu plików

        # Przycisk zatwierdzenia i zapisania assignment.csv
        finish_btn = ttk.Button(self.root, text='Zatwierdź', command=self.finish)
        finish_btn.pack(pady=5)

    def choose_dirs(self):
        """
        Otwarcie okna dialogowego z listą podkatalogów w INPUT_DIR, 
        pozwalającego wybrać wiele katalogów wejściowych.
        """
        # Sprawdzenie istnienia podkatalogów
        subdirs = [d for d in os.listdir(INPUT_DIR) if os.path.isdir(os.path.join(INPUT_DIR, d))]
        if not subdirs:
            messagebox.showerror('Błąd', f'Brak podkatalogów w {INPUT_DIR}')
            return

        # Nowe okno do wyboru katalogów
        dlg = tk.Toplevel(self.root)
        dlg.title('Wybierz katalogi')
        dlg.grab_set()

        lbl = ttk.Label(dlg, text='Zaznacz katalogi wejściowe:')
        lbl.pack(pady=5)

        listbox = tk.Listbox(dlg, selectmode='extended', height=10)
        for d in subdirs:
            listbox.insert(tk.END, d)
        listbox.pack(padx=10, pady=5)

        btn_frame = ttk.Frame(dlg)
        btn_frame.pack(pady=5)

        def confirm():
            selections = listbox.curselection()
            if not selections:
                messagebox.showerror('Błąd', 'Nie wybrano żadnego katalogu.')
                return
            chosen_dirs = [os.path.join(INPUT_DIR, subdirs[i]) for i in selections]
            dlg.destroy()
            self.load_files_from_dirs(chosen_dirs)

        def cancel():
            dlg.destroy()

        confirm_btn = ttk.Button(btn_frame, text='OK', command=confirm)
        confirm_btn.grid(row=0, column=0, padx=5)
        cancel_btn = ttk.Button(btn_frame, text='Anuluj', command=cancel)
        cancel_btn.grid(row=0, column=1, padx=5)

    def load_files_from_dirs(self, dirs):
        """
        Wczytuje pliki z wybranych katalogów i tworzy wiersze w GUI.
        """
        # Wyczyść poprzednie wiersze w tabeli
        for widget in self.table_frame.winfo_children():
            widget.destroy()
        self.file_rows = []

        all_files = []
        for d in dirs:
            for fname in os.listdir(d):
                fpath = os.path.join(d, fname)
                if os.path.isfile(fpath):
                    all_files.append(fpath)

        if not all_files:
            messagebox.showerror('Błąd', 'Wybrane katalogi są puste.')
            return

        # Nagłówki kolumn
        header_frame = ttk.Frame(self.table_frame)
        header_frame.grid(row=0, column=0, pady=2, sticky='w')
        lbl_file = ttk.Label(header_frame, text='Plik wejściowy', width=40, anchor='w')
        lbl_file.grid(row=0, column=0, padx=5)
        lbl_mapping = ttk.Label(header_frame, text='Mapping', width=30, anchor='w')
        lbl_mapping.grid(row=0, column=1, padx=5)

        # Utworzenie wierszy dla każdego pliku
        for i, f in enumerate(all_files, start=1):
            row_frame = ttk.Frame(self.table_frame)
            row_frame.grid(row=i, column=0, pady=2, sticky='w')

            lbl = ttk.Label(row_frame, text=os.path.relpath(f, INPUT_DIR), width=40, anchor='w')
            lbl.grid(row=0, column=0, padx=5)

            mapping_var = tk.StringVar()
            option = ttk.Combobox(row_frame, textvariable=mapping_var, values=self._mapping_files(), width=28)
            option.grid(row=0, column=1, padx=5)

            btn_edit = ttk.Button(
                row_frame, 
                text='Edytuj', 
                command=lambda path=f, var=mapping_var: self.edit_mapping(path, var)
            )
            btn_edit.grid(row=0, column=2, padx=5)

            self.file_rows.append({'file': f, 'var': mapping_var, 'widget': row_frame})

        # Po załadowaniu plików włącz przycisk przypisz do wszystkich
        self.assign_all_btn['state'] = 'normal'
        logger.debug('Loaded files from dirs: %s', all_files)

    def _mapping_files(self):
        files = [f for f in os.listdir(MAPPING_DIR) if f.endswith('.csv')]
        return files

    def edit_mapping(self, path, var):
        """
        Pozwala wybrać plik mappingu i przypisać jego nazwę do zmiennej powiązanej z danym plikiem wejściowym.
        """
        fname = filedialog.askopenfilename(initialdir=MAPPING_DIR, filetypes=[('CSV','*.csv')])
        if not fname:
            return
        var.set(os.path.basename(fname))
        logger.debug('Assigned mapping %s to %s', fname, path)
        # Informacja, że edycję mappingu trzeba wykonać w innym module
        messagebox.showinfo('Info', 'Aby edytować plik mappingu użyj modułu sample-mapper-generator')

    def assign_all(self):
        """
        Umożliwia wybranie jednego pliku mappingu, który zostanie przypisany do wszystkich wierszy.
        """
        fname = filedialog.askopenfilename(initialdir=MAPPING_DIR, filetypes=[('CSV','*.csv')])
        if not fname:
            return
        base = os.path.basename(fname)
        for row in self.file_rows:
            row['var'].set(base)
        logger.debug('Assigned mapping %s to all files', base)

    def finish(self):
        """
        Waliduje przypisania i zapisuje je do mappings/assignment.csv.
        """
        self.pairs = []
        for row in self.file_rows:
            mapping_name = row['var'].get()
            if not mapping_name:
                rel = os.path.relpath(row['file'], INPUT_DIR)
                messagebox.showerror('Błąd', f'Brak mappingu dla {rel}')
                return
            mapping_path = os.path.join(MAPPING_DIR, mapping_name)
            if not os.path.exists(mapping_path):
                messagebox.showerror('Błąd', f'Mapping {mapping_path} nie istnieje')
                return
            self.pairs.append((row['file'], mapping_path))

        if not self.pairs:
            messagebox.showerror('Błąd', 'Brak plików do przypisania')
            return

        logger.info('Mappings assigned: %s', self.pairs)
        assignment_path = os.path.join(MAPPING_DIR, 'assignment.csv')
        try:
            with open(assignment_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(['input_file', 'mapping_file'])
                for inp, mp in self.pairs:
                    writer.writerow([inp, mp])
            logger.info('Saved assignment file to %s', assignment_path)
        except OSError as e:
            logger.exception('Failed to write assignment file: %s', e)
            messagebox.showerror('Błąd', f'Nie można zapisać pliku {assignment_path}')
            return

        self.root.quit()

    def run(self):
        logger.info('Running MappingAssigner GUI')
        self.root.mainloop()
        return getattr(self, 'pairs', [])


if __name__ == '__main__':
    assigner = MappingAssigner()
    pairs = assigner.run()
    print('Pairs:', pairs)
