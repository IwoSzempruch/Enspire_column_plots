import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from itertools import product
import csv
import os
from logger_setup import logger

MAPPING_DIR = 'mappings'

class SampleMapperGenerator:
    def __init__(self):
        logger.info('Initializing SampleMapperGenerator')
        os.makedirs(MAPPING_DIR, exist_ok=True)
        self.root = tk.Tk()
        self.root.title('Sample Mapper Generator')
        self.positions = []
        self.position_frames = []
        self.names = []
        self._build_variant_editor()

    def _build_variant_editor(self):
        logger.debug('Building variant editor')
        editor_frame = ttk.Frame(self.root)
        editor_frame.pack(padx=10, pady=10)
        self.editor_frame = editor_frame
        self._add_position()
        gen_button = ttk.Button(self.root, text='Generuj nazwy', command=self.generate_names)
        gen_button.pack(pady=5)
        self.names_list = tk.Listbox(self.root, height=10, width=40)
        self.names_list.pack(pady=5)
        mapping_button = ttk.Button(self.root, text='Stwórz mapping', command=self.create_mapping)
        mapping_button.pack(pady=5)

    def _add_position(self):
        pos_index = len(self.positions)
        frame = ttk.Frame(self.editor_frame)
        frame.grid(row=0, column=pos_index, padx=5)
        entry = ttk.Entry(frame, width=6)
        entry.pack(pady=2)
        self.positions.append([entry])
        btn_add_variant = ttk.Button(frame, text='+ wariant', command=lambda f=frame: self._add_variant(f))
        btn_add_variant.pack(pady=2)
        btn_add_position = ttk.Button(frame, text='+ pozycja', command=self._add_position)
        btn_add_position.pack(pady=2)
        self.position_frames.append(frame)
        logger.debug('Added position %s', pos_index)

    def _add_variant(self, frame):
        entry = ttk.Entry(frame, width=6)
        entry.pack(pady=2)
        index = self.position_frames.index(frame)
        self.positions[index].append(entry)
        logger.debug('Added variant to position %s', index)

    def generate_names(self):
        logger.info('Generating names')
        variants = []
        for idx, variant_entries in enumerate(self.positions):
            variant_list = [e.get().strip() for e in variant_entries if e.get().strip()]
            if not variant_list:
                messagebox.showerror('Błąd', f'Pozycja {idx+1} nie ma wariantów')
                return
            variants.append(variant_list)
        self.names = [''.join(p) for p in product(*variants)]
        logger.debug('Generated names: %s', self.names)
        self.names_list.delete(0, tk.END)
        for name in self.names:
            self.names_list.insert(tk.END, name)

    def create_mapping(self):
        if not self.names:
            messagebox.showerror('Błąd', 'Najpierw wygeneruj nazwy')
            return
        MappingWindow(self.names)

    def run(self):
        logger.info('Running SampleMapperGenerator GUI')
        self.root.mainloop()

class MappingWindow:
    def __init__(self, samples):
        logger.info('Opening MappingWindow')
        self.samples = samples
        self.mapping = {}
        self.top = tk.Toplevel()
        self.top.title('Mapowanie prób')
        self.sample_list = tk.Listbox(self.top)
        for s in samples:
            self.sample_list.insert(tk.END, s)
        self.sample_list.grid(row=0, column=0, rowspan=9, padx=5, pady=5)
        grid_frame = ttk.Frame(self.top)
        grid_frame.grid(row=0, column=1, padx=5, pady=5)
        self.buttons = {}
        rows = 'ABCDEFGH'
        cols = [f'{i:02d}' for i in range(1,13)]
        for r_idx, r in enumerate(rows):
            for c_idx, c in enumerate(cols):
                well = f'{r}{c}'
                btn = ttk.Button(grid_frame, text=well, width=8,
                                 command=lambda w=well: self.assign_sample(w))
                btn.grid(row=r_idx, column=c_idx, padx=1, pady=1)
                self.buttons[well] = btn
        save_btn = ttk.Button(self.top, text='Zapisz mapping', command=self.save_mapping)
        save_btn.grid(row=1, column=0, pady=5)

    def assign_sample(self, well):
        selection = self.sample_list.curselection()
        if not selection:
            messagebox.showerror('Błąd', 'Nie wybrano próby')
            return
        sample = self.sample_list.get(selection)
        self.mapping[well] = sample
        self.buttons[well].config(text=sample)
        logger.debug('Assigned %s to %s', sample, well)

    def save_mapping(self):
        if len(self.mapping) != 96:
            if not messagebox.askyesno('Potwierdzenie', 'Nie wszystkie studzienki zmapowane. Czy kontynuować?'):
                return
        filename = filedialog.asksaveasfilename(defaultextension='.csv', initialdir=MAPPING_DIR,
                                                filetypes=[('CSV','*.csv')])
        if not filename:
            return
        logger.info('Saving mapping to %s', filename)
        rows = 'ABCDEFGH'
        cols = [f'{i:02d}' for i in range(1,13)]
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([''] + cols)
            for r in rows:
                row = [r]
                for c in cols:
                    well = f'{r}{c}'
                    row.append(self.mapping.get(well, ''))
                writer.writerow(row)
        messagebox.showinfo('Sukces', f'Zapisano mapping w {filename}')
        logger.info('Mapping saved')
        self.top.destroy()

if __name__ == '__main__':
    app = SampleMapperGenerator()
    app.run()
