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

        # Struktura na pozycje wariantów
        self.positions = []
        # Iloczyn kartezjański i wynikowe nazwy
        self.variants_tuples = []
        self.names = []

        self._build_variant_editor()

    def _build_variant_editor(self):
        logger.debug('Building variant editor')
        self.editor_frame = ttk.Frame(self.root)
        self.editor_frame.pack(padx=10, pady=10)

        # Pierwsza pozycja
        self._add_position()

        # Przycisk "Generuj nazwy"
        gen_button = ttk.Button(self.root, text='Generuj nazwy', command=self.generate_names)
        gen_button.pack(pady=(5, 5))

        # -----------------------
        # Sekcja dodawania ręcznego
        # -----------------------
        manual_frame = ttk.Frame(self.root)
        manual_frame.pack(pady=(0, 5))

        self.manual_entry = ttk.Entry(manual_frame, width=50)
        self.manual_entry.pack(side='left', padx=(0, 5))
        add_manual_btn = ttk.Button(manual_frame, text='Dodaj nazwę', command=self.add_manual_names)
        add_manual_btn.pack(side='left')

        # -----------------------
        # Pole tekstowe dla wszystkich nazw (comma-separated)
        # -----------------------
        self.names_var = tk.StringVar()
        self.names_entry = ttk.Entry(self.root, textvariable=self.names_var, width=60, state='readonly')
        self.names_entry.pack(pady=(0, 5))

        # -----------------------
        # Sortowanie nazw
        # -----------------------
        sort_frame = ttk.Frame(self.root)
        sort_frame.pack(pady=(0, 5))

        ttk.Label(sort_frame, text="Sortuj wg:").pack(side='left', padx=(0, 5))
        self.sort_var = tk.StringVar()
        self.sort_combo = ttk.Combobox(sort_frame, textvariable=self.sort_var, state='readonly')
        self.sort_combo['values'] = []
        self.sort_combo.pack(side='left')
        self.sort_button = ttk.Button(sort_frame, text='Sortuj', command=self.sort_names, state='disabled')
        self.sort_button.pack(side='left', padx=(5, 0))

        # Przycisk do otwarcia okna mapowania
        mapping_button = ttk.Button(self.root, text='Stwórz mapping', command=self.create_mapping)
        mapping_button.pack(pady=(0, 10))

    def _add_variant_to_frame(self, container_frame, variants_list):
        """
        Dodaje wiersz z Entry + przyciskiem '✖'. Ustawia fokus na nowe Entry.
        """
        row_frame = ttk.Frame(container_frame)
        row_frame.pack(fill='x', pady=(2, 2))

        entry = ttk.Entry(row_frame, width=8)
        entry.pack(side='left', padx=(0, 2))
        entry.focus_set()

        delete_btn = ttk.Button(
            row_frame,
            text='✖',
            width=2,
            command=lambda rf=row_frame: self._delete_variant(rf, variants_list)
        )
        delete_btn.pack(side='left')

        variants_list.append((entry, delete_btn))
        logger.debug('Added variant field; total now: %s', len(variants_list))

    def _delete_variant(self, row_frame, variants_list):
        """
        Usuwa entry + delete_btn z GUI i z listy variants_list.
        """
        for w in row_frame.pack_slaves():
            w.destroy()
        row_frame.destroy()

        for i, (e, btn) in enumerate(list(variants_list)):
            if btn.master == row_frame:
                variants_list.pop(i)
                break

        logger.debug('Deleted a variant field; remaining: %s', len(variants_list))

    def _add_position(self):
        """
        Dodaje nową ramkę pozycji z:
        - kontenerem na warianty (Entry + '✖'),
        - checkboxem 'Pozwól pustą wartość',
        - przyciskiem '+ wariant',
        - przyciskiem '+ pozycję' (tylko w tej ramce).
        """
        pos_index = len(self.positions)
        logger.debug('Adding new position at index %s', pos_index)

        # Ukryj '+ pozycję' z poprzedniej ramki
        if self.positions:
            prev = self.positions[-1]
            prev['btn_add_position'].pack_forget()

        frame = ttk.Frame(self.editor_frame, relief='ridge', borderwidth=1)
        frame.grid(row=0, column=pos_index, padx=5, pady=5, sticky='n')

        variants = []
        allow_empty_var = tk.BooleanVar(value=False)

        variants_container = ttk.Frame(frame)
        variants_container.pack(pady=(5, 5))

        # Pierwsze pole wariantu
        self._add_variant_to_frame(variants_container, variants)

        chk_empty = ttk.Checkbutton(
            frame,
            text='Pozwól pustą wartość',
            variable=allow_empty_var
        )
        chk_empty.pack(anchor='w', padx=5, pady=(0, 5))

        btn_add_variant = ttk.Button(
            frame,
            text='+ wariant',
            command=lambda vc=variants_container, v=variants: self._add_variant(vc, v)
        )
        btn_add_variant.pack(pady=(0, 5))

        btn_add_position = ttk.Button(
            frame,
            text='+ pozycję',
            command=self._add_position
        )
        btn_add_position.pack(pady=(0, 5))
        btn_add_position.bind('<Button-1>', lambda e: self._focus_new_position(pos_index + 1))

        self.positions.append({
            'frame': frame,
            'variants': variants,
            'variants_container': variants_container,
            'allow_empty_var': allow_empty_var,
            'btn_add_position': btn_add_position
        })

    def _focus_new_position(self, new_index):
        """
        Ustawia fokus na pierwszym Entry w nowo utworzonej ramce.
        """
        if new_index <= len(self.positions):
            new_pos = self.positions[new_index - 1]
            variants = new_pos['variants']
            if variants:
                first_entry = variants[0][0]
                first_entry.focus_set()

    def _add_variant(self, container_frame, variants_list):
        """
        Dodaje nowe pole Entry + '✖' i ustawia fokus.
        """
        self._add_variant_to_frame(container_frame, variants_list)
        logger.debug('Added a variant to position; now %s variants.', len(variants_list))

    def add_manual_names(self):
        """
        Dodaje ręcznie wpisane nazwy (oddzielone przecinkami) do listy.
        """
        text = self.manual_entry.get().strip()
        if not text:
            messagebox.showerror('Błąd', 'Wpisz przynajmniej jedną nazwę przed dodaniem')
            return

        parts = [p.strip() for p in text.split(',') if p.strip()]
        if not parts:
            messagebox.showerror('Błąd', 'Nie znaleziono żadnej nazwy do dodania')
            return

        for name in parts:
            if name in self.names:
                continue
            self.names.append(name)
            self.variants_tuples.append((name,))
        self._refresh_names_entry()
        self.manual_entry.delete(0, tk.END)
        logger.debug('Manually added names: %s', parts)

        if not self.sort_combo['values']:
            if len(self.positions) == 1:
                self.sort_combo['values'] = ['Pozycja 1']
            else:
                opts = [f"Pozycja {i+1}" for i in range(len(self.positions))]
                self.sort_combo['values'] = opts
            self.sort_combo.current(0)
            self.sort_button.config(state='normal')

    def generate_names(self):
        """
        Tworzy iloczyn kartezjański wariantów z każdej pozycji.
        """
        logger.info('Generating names')
        all_variants = []

        for idx, pos in enumerate(self.positions):
            widgets = pos['variants']
            allow_empty = pos['allow_empty_var'].get()

            vals = [e.get().strip() for e, _ in widgets if e.get().strip()]
            if allow_empty:
                vals.append('')
            if not vals:
                messagebox.showerror(
                    'Błąd',
                    f'Pozycja {idx+1} nie ma żadnych wartości (ani pustego).'
                )
                return

            logger.debug('Position %s variants (including empty=%s): %s', idx+1, allow_empty, vals)
            all_variants.append(vals)

        self.variants_tuples = list(product(*all_variants))
        self.names = [''.join(combo) for combo in self.variants_tuples]
        logger.debug('Generated names: %s', self.names)

        self._refresh_names_entry()

        opts = [f"Pozycja {i+1}" for i in range(len(self.positions))]
        self.sort_combo['values'] = opts
        self.sort_combo.current(0)
        self.sort_button.config(state='normal')

    def _refresh_names_entry(self):
        """
        Uaktualnia pole tekstowe tak, aby wyświetlało wszystkie nazwy oddzielone przecinkami.
        """
        display = ', '.join(self.names)
        self.names_entry.config(state='normal')
        self.names_var.set(display)
        self.names_entry.config(state='readonly')

    def sort_names(self):
        """
        Sortuje listę nazw wg wybranej pozycji.
        """
        sel = self.sort_combo.current()
        if sel < 0:
            return
        idx = sel

        logger.debug('Sorting names by position %s', idx+1)

        def key_fn(tpl):
            return tpl[idx] if idx < len(tpl) else ''

        self.variants_tuples.sort(key=key_fn)
        self.names = [''.join(combo) for combo in self.variants_tuples]
        self._refresh_names_entry()

    def create_mapping(self):
        """
        Otwiera okno mapowania próbek, przekazując nazwy i krotki wariantów.
        """
        if not self.names:
            messagebox.showerror('Błąd', 'Brak nazw do mapowania. Wygeneruj lub dodaj ręcznie.')
            return
        MappingWindow(self.names, self.variants_tuples)

    def run(self):
        logger.info('Running SampleMapperGenerator GUI')
        self.root.mainloop()


class MappingWindow:
    def __init__(self, samples, variants_tuples):
        logger.info('Opening MappingWindow')
        # Przechowujemy oryginalne kolejności
        self.original_samples = samples[:]
        self.original_tuples = variants_tuples[:]
        # Listy bieżące (do sortowania)
        self.samples = samples[:]
        self.variants_tuples = variants_tuples[:]

        self.mapping = {}  # { well: sample }
        self.top = tk.Toplevel()
        self.top.title('Mapowanie prób')

        # Pobranie domyślnego tła przycisku
        tmp = tk.Button(self.top)
        self.default_bg = tmp.cget('bg')
        tmp.destroy()

        # Inicjalizacja słownika przycisków przed budową widoku
        self.buttons = {}

        # -----------------------
        # Sekcja sortowania próbek
        # -----------------------
        sort_frame = ttk.Frame(self.top)
        sort_frame.grid(row=0, column=0, columnspan=2, pady=(10, 5), padx=10, sticky='w')

        ttk.Label(sort_frame, text="Sortuj próbki:").pack(side='left', padx=(0, 5))
        self.sort_samples_var = tk.StringVar()
        # Obliczamy liczbę dostępnych pozycji z krotki (wersje wildcard)
        num_positions = len(self.variants_tuples[0]) if self.variants_tuples else 1
        sort_values = ['Oryginalne', 'Alfabetycznie'] + [f"Pozycja {i+1}" for i in range(num_positions)]
        self.sort_samples_combo = ttk.Combobox(
            sort_frame,
            textvariable=self.sort_samples_var,
            state='readonly',
            values=sort_values
        )
        self.sort_samples_combo.current(0)
        self.sort_samples_combo.pack(side='left')
        self.sort_samples_combo.bind('<<ComboboxSelected>>', lambda e: self.sort_samples())

        # -----------------------
        # Tabela próbek (grid)
        # -----------------------
        table_frame = ttk.Frame(self.top)
        table_frame.grid(row=1, column=0, padx=10, pady=(0,10), sticky='nw')
        self.table_frame = table_frame
        self.sample_labels = {}
        self._build_sample_table()

        # -----------------------
        # Tabela studzienek 8×12
        # -----------------------
        grid_frame = ttk.Frame(self.top)
        grid_frame.grid(row=1, column=1, padx=5, pady=(0,10), sticky='ne')

        wells_rows = 'ABCDEFGH'
        wells_cols = [f'{i:02d}' for i in range(1, 13)]
        for r_idx, r in enumerate(wells_rows):
            for c_idx, c in enumerate(wells_cols):
                well = f'{r}{c}'
                btn = tk.Button(
                    grid_frame,
                    text=well,
                    width=8,
                    bg=self.default_bg,
                    command=lambda w=well: self.assign_sample(w)
                )
                btn.grid(row=r_idx, column=c_idx, padx=1, pady=1)
                # Prawy przycisk usuwa przypisanie
                btn.bind('<Button-3>', lambda e, w=well: self.unassign_sample(w))
                self.buttons[well] = btn

        # -----------------------
        # Przycisk Zapisz mapping
        # -----------------------
        save_btn = ttk.Button(self.top, text='Zapisz mapping', command=self.save_mapping)
        save_btn.grid(row=2, column=0, columnspan=2, pady=(0, 10))

    def _build_sample_table(self):
        """
        Tworzy siatkę Labeli reprezentujących próbki w kilku kolumnach.
        """
        for lbl in self.sample_labels.values():
            lbl.destroy()
        self.sample_labels.clear()

        columns = 4
        rows = (len(self.samples) + columns - 1) // columns
        idx = 0
        for r in range(rows):
            for c in range(columns):
                if idx >= len(self.samples):
                    break
                sample = self.samples[idx]
                lbl = tk.Label(
                    self.table_frame,
                    text=sample,
                    width=15,
                    anchor='w',
                    relief='ridge',
                    bg=self.default_bg
                )
                lbl.grid(row=r, column=c, padx=2, pady=2, sticky='w')
                lbl.bind('<Button-1>', lambda e, s=sample: self.on_sample_click(s))
                self.sample_labels[sample] = lbl
                idx += 1

        self.clear_highlights()

    def sort_samples(self):
        """
        Sortuje tabelę próbek wg wybranej opcji:
        - Oryginalne = przywraca listę do stanu wyjściowego
        - Alfabetycznie = sortuje wg nazwy
        - Pozycja i = sortuje wg i-tego elementu w krotce variants_tuples
        """
        choice = self.sort_samples_var.get()
        if choice == 'Oryginalne':
            self.samples = self.original_samples[:]
            self.variants_tuples = self.original_tuples[:]
        elif choice == 'Alfabetycznie':
            combined = list(zip(self.samples, self.variants_tuples))
            combined.sort(key=lambda x: x[0].lower())
            self.samples, self.variants_tuples = zip(*combined)
            self.samples = list(self.samples)
            self.variants_tuples = list(self.variants_tuples)
        else:
            pos_idx = int(choice.split()[1]) - 1
            combined = list(zip(self.samples, self.variants_tuples))
            combined.sort(key=lambda x: x[1][pos_idx] if pos_idx < len(x[1]) else '')
            self.samples, self.variants_tuples = zip(*combined)
            self.samples = list(self.samples)
            self.variants_tuples = list(self.variants_tuples)

        self._build_sample_table()

    def assign_sample(self, well):
        """
        Lewy klik na przycisku studzienki przypisuje last_selected_sample.
        """
        if not hasattr(self, 'last_selected_sample'):
            messagebox.showerror('Błąd', 'Kliknij próbkę w tabeli, by ją wybrać.')
            return

        new_sample = self.last_selected_sample
        old_sample = self.mapping.get(well)

        self.mapping[well] = new_sample
        self.buttons[well].config(text=new_sample, bg='lightblue')

        if old_sample:
            logger.debug("Overwritten sample in well %s: '%s' → '%s'", well, old_sample, new_sample)
        else:
            logger.debug("Assigned sample '%s' to well %s", new_sample, well)

        self.clear_highlights()
        self.on_sample_click(new_sample)

    def unassign_sample(self, well):
        """
        Prawy klik usuwa przypisanie z danej studzienki.
        """
        if well in self.mapping:
            del self.mapping[well]
            self.buttons[well].config(text=well, bg=self.default_bg)
            logger.debug("Unassigned sample from well %s", well)
            self.clear_highlights()

    def on_sample_click(self, sample):
        """
        Po kliknięciu próbki:
        - zapamiętaj last_selected_sample
        - podświetl ją na żółto i podświetl powiązane studzienki
        """
        self.last_selected_sample = sample

        for s, lbl in self.sample_labels.items():
            if s in self.mapping.values():
                lbl.config(bg='lightblue')
            else:
                lbl.config(bg=self.default_bg)

        self.sample_labels[sample].config(bg='yellow')

        for well, btn in self.buttons.items():
            if well in self.mapping:
                btn.config(bg='lightblue', text=self.mapping[well])
            else:
                btn.config(bg=self.default_bg, text=well)

        for well, samp in self.mapping.items():
            if samp == sample:
                self.buttons[well].config(bg='yellow', text=sample)

    def clear_highlights(self):
        """
        Przywraca kolory próbek i przycisków do poprawnych stanów:
        - przypisane→lightblue, nieprzypisane→domyślne
        """
        for sample, lbl in self.sample_labels.items():
            if sample in self.mapping.values():
                lbl.config(bg='lightblue')
            else:
                lbl.config(bg=self.default_bg)

        for well, btn in self.buttons.items():
            if well in self.mapping:
                btn.config(bg='lightblue', text=self.mapping[well])
            else:
                btn.config(bg=self.default_bg, text=well)

    def save_mapping(self):
        """
        Zapisuje mapping do CSV:
        Nagłówek: puste + kolumny 01–12
        Wiersze A–H z wartościami lub pustym stringiem.
        """
        if len(self.mapping) != 96:
            if not messagebox.askyesno(
                'Potwierdzenie',
                'Nie wszystkie studzienki zmapowane. Czy kontynuować?'
            ):
                return

        filename = filedialog.asksaveasfilename(
            defaultextension='.csv',
            initialdir=MAPPING_DIR,
            filetypes=[('CSV', '*.csv')]
        )
        if not filename:
            return

        logger.info('Saving mapping to %s', filename)
        rows = 'ABCDEFGH'
        cols = [f'{i:02d}' for i in range(1, 13)]

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
