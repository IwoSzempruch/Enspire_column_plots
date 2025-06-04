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

        # Każda pozycja to słownik z następującymi polami:
        #   frame: ramka (tk.Frame)
        #   variants: lista par (entry_widget, delete_btn_widget)
        #   variants_container: container (tk.Frame) dla wariantów
        #   allow_empty_var: tk.BooleanVar (checkbox „Pozwól pustą wartość”)
        #   btn_add_position: przycisk „+ pozycję” (tylko w ostatniej ramce)
        self.positions = []

        # Przechowuje iloczyn kartezjański jako listę krotek przed łączeniem w stringi
        self.variants_tuples = []
        self.names = []  # wynikowe wygenerowane nazwy (stringi)

        self._build_variant_editor()

    def _build_variant_editor(self):
        logger.debug('Building variant editor')
        self.editor_frame = ttk.Frame(self.root)
        self.editor_frame.pack(padx=10, pady=10)

        # Dodaj pierwszą pozycję
        self._add_position()

        # Przycisk generowania nazw
        gen_button = ttk.Button(self.root, text='Generuj nazwy', command=self.generate_names)
        gen_button.pack(pady=(5, 5))

        # Listbox do wyświetlenia wygenerowanych nazw
        self.names_list = tk.Listbox(self.root, height=10, width=40)
        self.names_list.pack(pady=(0, 5))

        # Ramka na opcje sortowania
        sort_frame = ttk.Frame(self.root)
        sort_frame.pack(pady=(0, 5))

        ttk.Label(sort_frame, text="Sortuj wg:").pack(side='left', padx=(0, 5))
        self.sort_var = tk.StringVar()
        self.sort_combo = ttk.Combobox(sort_frame, textvariable=self.sort_var, state='readonly')
        self.sort_combo.pack(side='left')
        self.sort_button = ttk.Button(sort_frame, text='Sortuj', command=self.sort_names, state='disabled')
        self.sort_button.pack(side='left', padx=(5, 0))

        # Przycisk przejścia do tworzenia mappingu
        mapping_button = ttk.Button(self.root, text='Stwórz mapping', command=self.create_mapping)
        mapping_button.pack(pady=(0, 10))

    def _add_variant_to_frame(self, container_frame, variants_list):
        """
        Pomocnicza metoda: tworzy jedno pole Entry z przyciskiem '✖' (usuń) w ramach container_frame.
        Dodaje także obie referencje (entry_widget, delete_btn_widget) do variants_list.
        """
        row_frame = ttk.Frame(container_frame)
        row_frame.pack(fill='x', pady=(2, 2))

        entry = ttk.Entry(row_frame, width=8)
        entry.pack(side='left', padx=(0, 2))

        delete_btn = ttk.Button(
            row_frame, text='✖', width=2,
            command=lambda rf=row_frame: self._delete_variant(rf, variants_list)
        )
        delete_btn.pack(side='left')

        variants_list.append((entry, delete_btn))
        logger.debug('Added variant field; total now: %s', len(variants_list))

    def _delete_variant(self, row_frame, variants_list):
        """
        Usuwa dany wiersz w container_frame (entry + delete_btn) z GUI i z variants_list.
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
        Tworzy nową ramkę („pozycję”) z:
        - containerem na warianty (Entry + '✖')
        - checkboxem „Pozwól pustą wartość”
        - przyciskiem "+ wariant"
        - przyciskiem "+ pozycję" (tylko widoczny w tej, ostatniej ramce)
        """
        pos_index = len(self.positions)
        logger.debug('Adding new position at index %s', pos_index)

        if self.positions:
            prev = self.positions[-1]
            prev['btn_add_position'].pack_forget()

        frame = ttk.Frame(self.editor_frame, relief='ridge', borderwidth=1)
        frame.grid(row=0, column=pos_index, padx=5, pady=5, sticky='n')

        variants = []
        allow_empty_var = tk.BooleanVar(value=False)

        variants_container = ttk.Frame(frame)
        variants_container.pack(pady=(5, 5))

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

        self.positions.append({
            'frame': frame,
            'variants': variants,
            'variants_container': variants_container,
            'allow_empty_var': allow_empty_var,
            'btn_add_position': btn_add_position
        })

    def _add_variant(self, container_frame, variants_list):
        """
        Dodaje nowe pole Entry + przycisk '✖' do container_frame.
        """
        self._add_variant_to_frame(container_frame, variants_list)
        logger.debug('Added a variant to position; now %s variants.', len(variants_list))

    def generate_names(self):
        """
        Zbiera wszystkie warianty ze wszystkich pozycji i tworzy iloczyn kartezjański.
        Jeśli checkbox 'Pozwól pustą wartość' jest zaznaczony, dopuszcza opcję "" (pusty).
        """
        logger.info('Generating names')
        all_variants = []

        for idx, pos in enumerate(self.positions):
            variants_widgets = pos['variants']
            allow_empty = pos['allow_empty_var'].get()

            values = [e.get().strip() for e, _ in variants_widgets if e.get().strip()]
            if allow_empty:
                values.append('')
            if not values:
                messagebox.showerror(
                    'Błąd',
                    f'Pozycja {idx + 1} nie ma żadnych wartości (ani pustego).'
                )
                return

            logger.debug('Position %s variants (including empty=%s): %s', idx + 1, allow_empty, values)
            all_variants.append(values)

        # Zapisujemy krotki przed połączeniem w stringi
        self.variants_tuples = list(product(*all_variants))
        self.names = [''.join(combo) for combo in self.variants_tuples]
        logger.debug('Generated names: %s', self.names)

        self._refresh_names_listbox()

        # Wypełnij Combobox sortowania: "Pozycja 1", "Pozycja 2", ...
        options = [f"Pozycja {i+1}" for i in range(len(self.positions))]
        self.sort_combo['values'] = options
        self.sort_combo.current(0)
        self.sort_button.config(state='normal')

    def _refresh_names_listbox(self):
        """
        Aktualizuje Listbox (names_list) na podstawie self.names.
        """
        self.names_list.delete(0, tk.END)
        for name in self.names:
            self.names_list.insert(tk.END, name)

    def sort_names(self):
        """
        Sortuje self.variants_tuples i self.names wg wybranej pozycji.
        Kombinacje posortowane są rosnąco wg wartości podanej pozycji.
        """
        sel = self.sort_combo.current()
        if sel < 0:
            return

        idx = sel  # indeks pozycji do sortowania (0-based)
        logger.debug('Sorting names by position %s', idx + 1)

        # Sortuj krotki wg elementu na pozycji idx
        self.variants_tuples.sort(key=lambda tpl: tpl[idx])
        self.names = [''.join(combo) for combo in self.variants_tuples]
        self._refresh_names_listbox()

    def create_mapping(self):
        """
        Uruchamia okno mapowania, jeśli są wygenerowane nazwy.
        """
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

        # Lista próbek po lewej
        self.sample_list = tk.Listbox(self.top, height=12, width=20)
        for s in samples:
            self.sample_list.insert(tk.END, s)
        self.sample_list.grid(row=0, column=0, rowspan=9, padx=(10, 5), pady=10)

        # Ramka z przyciskami 8×12
        grid_frame = ttk.Frame(self.top)
        grid_frame.grid(row=0, column=1, padx=5, pady=10)

        self.buttons = {}
        rows = 'ABCDEFGH'
        cols = [f'{i:02d}' for i in range(1, 13)]
        for r_idx, r in enumerate(rows):
            for c_idx, c in enumerate(cols):
                well = f'{r}{c}'
                btn = ttk.Button(
                    grid_frame,
                    text=well,
                    width=8,
                    command=lambda w=well: self.assign_sample(w)
                )
                btn.grid(row=r_idx, column=c_idx, padx=1, pady=1)
                self.buttons[well] = btn

        # Przycisk "Zapisz mapping"
        save_btn = ttk.Button(self.top, text='Zapisz mapping', command=self.save_mapping)
        save_btn.grid(row=1, column=0, padx=10, pady=(0, 10), sticky='w')

    def assign_sample(self, well):
        """
        Przypisuje lub nadpisuje zaznaczoną próbkę dla komórki `well`.
        Jeśli w tej komórce była już jakaś nazwa, zostanie zastąpiona.
        """
        selection = self.sample_list.curselection()
        if not selection:
            messagebox.showerror('Błąd', 'Nie wybrano próby')
            return

        new_sample = self.sample_list.get(selection[0])
        old_sample = self.mapping.get(well)

        # Nadpisujemy niezależnie od tego, czy była już jakaś wartość
        self.mapping[well] = new_sample
        self.buttons[well].config(text=new_sample)

        if old_sample:
            logger.debug("Overwritten sample in well %s: '%s' → '%s'", well, old_sample, new_sample)
        else:
            logger.debug("Assigned sample '%s' to well %s", new_sample, well)

    def save_mapping(self):
        """
        Zapisuje mapping do pliku CSV. Struktura:
        - Nagłówek: puste pole + kolumny 01–12
        - Kolejne wiersze: A,<wartość dla A01>,<wartość dla A02>,...,A12
          itd. dla wierszy A–H.
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
