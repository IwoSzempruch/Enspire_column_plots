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
        select_btn = ttk.Button(self.root, text='Wybierz pliki wejściowe', command=self.choose_files)
        select_btn.pack(pady=5)
        self.table = ttk.Frame(self.root)
        self.table.pack(padx=10, pady=10)
        finish_btn = ttk.Button(self.root, text='Zatwierdź', command=self.finish)
        finish_btn.pack(pady=5)

    def choose_files(self):
        files = filedialog.askopenfilenames(initialdir=INPUT_DIR, filetypes=[('CSV','*.csv')])
        if not files:
            return
        for widget in self.table.winfo_children():
            widget.destroy()
        self.file_rows = []
        for i, f in enumerate(files):
            row_frame = ttk.Frame(self.table)
            row_frame.grid(row=i, column=0, pady=2)
            lbl = ttk.Label(row_frame, text=os.path.basename(f))
            lbl.grid(row=0, column=0)
            mapping_var = tk.StringVar()
            option = ttk.Combobox(row_frame, textvariable=mapping_var, values=self._mapping_files())
            option.grid(row=0, column=1)
            btn_edit = ttk.Button(row_frame, text='Edytuj', command=lambda path=f, var=mapping_var: self.edit_mapping(path, var))
            btn_edit.grid(row=0, column=2)
            self.file_rows.append({'file':f, 'var':mapping_var, 'widget':row_frame})
        logger.debug('Selected files: %s', files)

    def _mapping_files(self):
        files = [f for f in os.listdir(MAPPING_DIR) if f.endswith('.csv')]
        return files

    def edit_mapping(self, path, var):
        fname = filedialog.askopenfilename(initialdir=MAPPING_DIR, filetypes=[('CSV','*.csv')])
        if not fname:
            return
        var.set(os.path.basename(fname))
        logger.debug('Assigned mapping %s to %s', fname, path)
        # For editing we just open using sample_mapper_generator if needed
        messagebox.showinfo('Info', 'Aby edytować plik mappingu użyj modułu sample-mapper-generator')

    def finish(self):
        self.pairs = []
        for row in self.file_rows:
            mapping_name = row['var'].get()
            if not mapping_name:
                messagebox.showerror('Błąd', f'Brak mappingu dla {row["file"]}')
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
                writer.writerows(self.pairs)
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
