# interactive_plot_selector.py
import os
import random
import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# Ścieżka do katalogu z danymi i mappingów
DATA_DIR = os.path.join(os.getcwd(), 'data')
MAPPING_DIR = os.path.join(os.getcwd(), 'mappings')
COLOR_MAPPING_FILE = os.path.join(MAPPING_DIR, 'color-mapping.csv')


class PlotSelector:
    def __init__(self):
        print("Inicjalizacja PlotSelector...")

        # Utworzenie katalogu mappings, jeśli nie istnieje
        os.makedirs(MAPPING_DIR, exist_ok=True)

        # Inicjalizacja głównego okna
        self.root = tk.Tk()
        self.root.title("Interaktywny selektor wykresów")

        # Lista podkatalogów w katalogu data
        self.subdirs = [
            d for d in os.listdir(DATA_DIR)
            if os.path.isdir(os.path.join(DATA_DIR, d))
        ]
        print(f"Znalezione podkatalogi w '{DATA_DIR}': {self.subdirs}")

        # Struktury do przechowywania DataFrame'ów
        self.data_dfs = {}   # {subdir: DataFrame z data_merged.csv}
        self.ratio_dfs = {}  # {subdir: DataFrame z ratios.csv}

        # Lista próbek (z pierwszego odpowiedniego pliku)
        self.sample_list = []

        # Zaznaczone próbki, osobno dla każdego podkatalogu
        self.selected_samples = {sub: set() for sub in self.subdirs}

        # Tryb 'data' lub 'ratio'
        self.mode = None
        self.available_modes = []

        # Dla trybu 'data': typy pomiarów i aktualny
        self.measurement_types = []
        self.current_measurement = None

        # Niestandardowe etykiety: {sample: label}
        self.custom_labels = {}

        # Kolory próbek: {sample: '#rrggbb'}
        self.sample_colors = {}
        # Hatch dla próbek: {sample: hatch_code}
        self.sample_hatches = {}
        # Kolor samego hatch: {sample: '#rrggbb'}
        self.sample_hatch_colors = {}

        # Domyślna paleta matplotlib
        self.default_colors = plt.rcParams['axes.prop_cycle'].by_key()['color']

        # Parametry wykresu
        self.bar_width = 0.8
        self.group_spacing = 1.0
        self.label_font_size = 10
        self.label_rotation = 45

        # Wczytanie danych i wyliczenie sample_list
        self._load_data_frames()

        # Wczytanie lub stworzenie color-mapping.csv (z kolorem i hatch)
        self._load_or_create_color_mapping()

        # Budowa GUI
        self._build_gui()

    def _load_data_frames(self):
        """
        Wczytuje data_merged.csv i ratios.csv z każdego podkatalogu.
        Ustala sample_list i dostępne tryby.
        """
        print("Wczytywanie plików CSV z podkatalogów...")
        for sub in self.subdirs:
            sub_path = os.path.join(DATA_DIR, sub)
            data_file = os.path.join(sub_path, 'data_merged.csv')
            ratio_file = os.path.join(sub_path, 'ratios.csv')

            if os.path.exists(data_file):
                try:
                    df = pd.read_csv(data_file)
                    self.data_dfs[sub] = df
                    print(f"Wczytano '{data_file}' dla '{sub}'")
                except Exception as e:
                    print(f"Błąd wczytywania '{data_file}': {e}")
            else:
                print(f"Brak '{data_file}' w '{sub}'")

            if os.path.exists(ratio_file):
                try:
                    rdf = pd.read_csv(ratio_file)
                    self.ratio_dfs[sub] = rdf
                    print(f"Wczytano '{ratio_file}' dla '{sub}'")
                except Exception as e:
                    print(f"Błąd wczytywania '{ratio_file}': {e}")
            else:
                print(f"Brak '{ratio_file}' w '{sub}'")

        if self.data_dfs:
            self.available_modes.append('data')
            print("Tryb 'Dane pomiarów' dostępny.")
        if self.ratio_dfs:
            self.available_modes.append('ratio')
            print("Tryb 'Stosunek' dostępny.")

        if 'data' in self.available_modes:
            self.mode = 'data'
        elif 'ratio' in self.available_modes:
            self.mode = 'ratio'
        else:
            messagebox.showerror(
                "Błąd",
                "Brak danych: nie znaleziono ani data_merged.csv, ani ratios.csv."
            )
            self.root.destroy()
            return

        print(f"Aktualny tryb: {self.mode}")

        if self.mode == 'data':
            first_sub = next(iter(self.data_dfs))
            df0 = self.data_dfs[first_sub]
            self.sample_list = sorted(df0['Sample'].unique().tolist())
            print(f"Próbki (z '{first_sub}'): {self.sample_list}")
            self.measurement_types = sorted(df0['Measurement'].unique().tolist())
            print(f"Typy Measurement: {self.measurement_types}")
            if self.measurement_types:
                self.current_measurement = self.measurement_types[0]
                print(f"Aktualny Measurement: {self.current_measurement}")
        else:
            first_sub = next(iter(self.ratio_dfs))
            rdf0 = self.ratio_dfs[first_sub]
            self.sample_list = sorted(rdf0['Sample'].unique().tolist())
            print(f"Próbki (z ratios, '{first_sub}'): {self.sample_list}")

        # Inicjalizuj etykiety, kolory i hatch dla każdej próbki
        for s in self.sample_list:
            self.custom_labels[s] = s
            self.sample_colors[s] = None
            self.sample_hatches[s] = ""
            self.sample_hatch_colors[s] = None

    def _load_or_create_color_mapping(self):
        """
        Wczytuje color-mapping.csv jeśli istnieje,
        uzupełnia losowo dla brakujących próbek,
        albo tworzy nowy plik, jeśli nie istnieje.
        Plik przechowuje: Sample,Color,Hatch,HatchColor
        """
        samples = list(self.sample_list)

        if os.path.exists(COLOR_MAPPING_FILE):
            df = pd.read_csv(COLOR_MAPPING_FILE)

            # Upewnijmy się, że brakujące wartości HatchColor są zamienione na pusty string
            if 'HatchColor' in df.columns:
                df['HatchColor'] = df['HatchColor'].fillna('')
            if 'Hatch' in df.columns:
                df['Hatch'] = df['Hatch'].fillna('')

            color_dict = dict(zip(df['Sample'], df['Color']))
            hatch_dict = {}
            hatch_color_dict = {}
            if 'Hatch' in df.columns:
                hatch_dict = dict(zip(df['Sample'], df['Hatch']))
            if 'HatchColor' in df.columns:
                hatch_color_dict = dict(zip(df['Sample'], df['HatchColor']))

            for s in samples:
                if s not in color_dict:
                    rand_col = "#{:06x}".format(random.randint(0, 0xFFFFFF))
                    color_dict[s] = rand_col
                if s not in hatch_dict:
                    hatch_dict[s] = ""
                if s not in hatch_color_dict:
                    hatch_color_dict[s] = ""

            for s in samples:
                self.sample_colors[s] = color_dict.get(s)
                self.sample_hatches[s] = hatch_dict.get(s, "")
                # hatch_color może być pustym stringiem, traktujemy to jako brak
                hc = hatch_color_dict.get(s, "")
                self.sample_hatch_colors[s] = hc if hc else None

            df_new = pd.DataFrame({
                'Sample': sorted(color_dict.keys()),
                'Color': [color_dict[k] for k in sorted(color_dict.keys())],
                'Hatch': [hatch_dict.get(k, "") for k in sorted(color_dict.keys())],
                'HatchColor': [
                    hatch_color_dict.get(k, "") for k in sorted(color_dict.keys())
                ]
            })
            df_new.to_csv(COLOR_MAPPING_FILE, index=False)
            print(f"Zaktualizowano {COLOR_MAPPING_FILE}")

        else:
            color_dict = {}
            hatch_dict = {}
            hatch_color_dict = {}
            for s in samples:
                rand_col = "#{:06x}".format(random.randint(0, 0xFFFFFF))
                color_dict[s] = rand_col
                hatch_dict[s] = ""
                hatch_color_dict[s] = ""
                self.sample_colors[s] = rand_col
                self.sample_hatches[s] = ""
                self.sample_hatch_colors[s] = None

            df_new = pd.DataFrame({
                'Sample': samples,
                'Color': [color_dict[s] for s in samples],
                'Hatch': [hatch_dict[s] for s in samples],
                'HatchColor': [hatch_color_dict[s] for s in samples]
            })
            df_new.to_csv(COLOR_MAPPING_FILE, index=False)
            print(f"Utworzono nowy {COLOR_MAPPING_FILE}")

    def _save_color_mapping_to_file(self):
        """
        Nadpisuje plik color-mapping.csv aktualnymi kolorami i wzorami.
        Kolumny: Sample,Color,Hatch,HatchColor
        """
        samples = sorted(self.sample_colors.keys())
        df = pd.DataFrame({
            'Sample': samples,
            'Color': [self.sample_colors[s] for s in samples],
            'Hatch': [self.sample_hatches.get(s, "") for s in samples],
            'HatchColor': [
                self.sample_hatch_colors.get(s, "") if self.sample_hatch_colors.get(s) else ""
                for s in samples
            ]
        })
        df.to_csv(COLOR_MAPPING_FILE, index=False)
        print(f"Zapisano color-mapping (z hatch) do {COLOR_MAPPING_FILE}")

    def _build_gui(self):
        print("Budowanie GUI...")
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=2)
        main_frame.grid_rowconfigure(0, weight=1)

        # LEWA KOLUMNA
        left_frame = tk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky="nswe", padx=5, pady=5)
        left_frame.grid_rowconfigure(1, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)

        mode_frame = tk.LabelFrame(left_frame, text="Tryb i pomiar")
        mode_frame.grid(row=0, column=0, sticky="we", pady=5)
        mode_frame.grid_columnconfigure(0, weight=1)

        self.mode_var = tk.StringVar(value=self.mode)
        col = 0
        if 'data' in self.available_modes:
            rb_data = tk.Radiobutton(
                mode_frame, text="Dane pomiarów",
                variable=self.mode_var, value='data',
                command=self._on_mode_change
            )
            rb_data.grid(row=0, column=col, padx=5, pady=2, sticky="w")
            col += 1
        if 'ratio' in self.available_modes:
            rb_ratio = tk.Radiobutton(
                mode_frame, text="Stosunek",
                variable=self.mode_var, value='ratio',
                command=self._on_mode_change
            )
            rb_ratio.grid(row=0, column=col, padx=5, pady=2, sticky="w")
            col += 1

        self.measurement_var = tk.StringVar(value=self.current_measurement or "")
        self.measurement_menu = None
        if self.mode == 'data':
            tk.Label(mode_frame, text="Measurement:").grid(
                row=1, column=0, padx=5, pady=2, sticky="w"
            )
            self.measurement_menu = ttk.Combobox(
                mode_frame, textvariable=self.measurement_var,
                values=self.measurement_types, state='readonly'
            )
            self.measurement_menu.grid(
                row=1, column=1, columnspan=max(col-1, 1),
                padx=5, pady=2, sticky="we"
            )
            self.measurement_menu.bind(
                "<<ComboboxSelected>>", self._on_measurement_change
            )

        list_frame = tk.LabelFrame(
            left_frame, text="Próbki (kliknij, aby zaznaczyć/odznaczyć)"
        )
        list_frame.grid(row=1, column=0, sticky="nswe", pady=5)
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        lists_container = tk.Frame(list_frame)
        lists_container.grid(row=0, column=0, sticky="nsew")
        lists_container.grid_columnconfigure(0, weight=1)

        self.listboxes = {}
        for idx, sub in enumerate(self.subdirs):
            print(f"Tworzenie listy dla podkatalogu '{sub}'")
            frame = tk.Frame(lists_container)
            frame.grid(row=idx, column=0, sticky="nsew", padx=5, pady=5)
            lists_container.grid_rowconfigure(idx, weight=1)

            lbl = tk.Label(frame, text=sub)
            lbl.pack(anchor="w")

            lb = tk.Listbox(
                frame, selectmode=tk.MULTIPLE,
                exportselection=False, height=10
            )
            lb.pack(side="left", fill="both", expand=True)

            scrollbar = tk.Scrollbar(
                frame, orient=tk.VERTICAL, command=lb.yview
            )
            scrollbar.pack(side="right", fill="y")
            lb.config(yscrollcommand=scrollbar.set)

            for s in self.sample_list:
                lb.insert(tk.END, s)

            lb.bind(
                '<ButtonRelease-1>',
                lambda event, subdir=sub: self._on_listbox_click(event, subdir)
            )
            self.listboxes[sub] = lb

        toggle_btn = tk.Button(
            left_frame, text="Ukryj/Pokaż listy",
            command=lambda: self._toggle_lists(list_frame)
        )
        toggle_btn.grid(row=2, column=0, pady=5)

        # PRAWA KOLUMNA
        right_frame = tk.Frame(main_frame)
        right_frame.grid(row=0, column=1, sticky="nswe", padx=5, pady=5)
        right_frame.grid_rowconfigure(0, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)

        plot_frame = tk.Frame(right_frame)
        plot_frame.grid(row=0, column=0, sticky="nswe")
        plot_frame.grid_rowconfigure(0, weight=1)
        plot_frame.grid_columnconfigure(0, weight=1)

        self.fig = Figure(figsize=(6, 5))
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title("Interaktywny wykres")

        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nswe")

        sliders_frame = tk.LabelFrame(right_frame, text="Ustawienia wykresu")
        sliders_frame.grid(row=1, column=0, sticky="we", pady=5)
        sliders_frame.grid_columnconfigure(1, weight=1)

        tk.Label(sliders_frame, text="Szerokość kolumn:").grid(
            row=0, column=0, sticky="w"
        )
        self.width_slider = tk.Scale(
            sliders_frame, from_=0.1, to=1.0, resolution=0.05,
            orient=tk.HORIZONTAL, command=self._on_width_change
        )
        self.width_slider.set(self.bar_width)
        self.width_slider.grid(
            row=0, column=1, sticky="we", padx=5, pady=2
        )

        tk.Label(sliders_frame, text="Odległość grup:").grid(
            row=1, column=0, sticky="w"
        )
        self.spacing_slider = tk.Scale(
            sliders_frame, from_=0.5, to=5.0, resolution=0.1,
            orient=tk.HORIZONTAL, command=self._on_spacing_change
        )
        self.spacing_slider.set(self.group_spacing)
        self.spacing_slider.grid(
            row=1, column=1, sticky="we", padx=5, pady=2
        )

        tk.Label(sliders_frame, text="Rozmiar czcionki etykiet:").grid(
            row=2, column=0, sticky="w"
        )
        self.font_slider = tk.Scale(
            sliders_frame, from_=6, to=20, resolution=1,
            orient=tk.HORIZONTAL, command=self._on_font_change
        )
        self.font_slider.set(self.label_font_size)
        self.font_slider.grid(
            row=2, column=1, sticky="we", padx=5, pady=2
        )

        tk.Label(sliders_frame, text="Kąt nachylenia etykiet:").grid(
            row=3, column=0, sticky="w"
        )
        self.rotation_slider = tk.Scale(
            sliders_frame, from_=0, to=90, resolution=5,
            orient=tk.HORIZONTAL, command=self._on_rotation_change
        )
        self.rotation_slider.set(self.label_rotation)
        self.rotation_slider.grid(
            row=3, column=1, sticky="we", padx=5, pady=2
        )

        label_btn = tk.Button(
            right_frame, text="Edytuj etykiety",
            command=self._edit_labels_popup
        )
        label_btn.grid(row=2, column=0, pady=5)

        color_btn = tk.Button(
            right_frame, text="Zmień kolor",
            command=self._change_color_popup
        )
        color_btn.grid(row=3, column=0, pady=5)

        hatch_btn = tk.Button(
            right_frame, text="Zmień wypełnienie",
            command=self._change_hatch_popup
        )
        hatch_btn.grid(row=4, column=0, pady=5)

        # Pierwszy wykres
        self._update_plot()

    def _toggle_lists(self, list_frame):
        if list_frame.winfo_viewable():
            print("Ukrywam listy próbek")
            list_frame.grid_remove()
        else:
            print("Pokazuję listy próbek")
            list_frame.grid()
        self.root.update()

    def _on_mode_change(self):
        new_mode = self.mode_var.get()
        print(f"Zmieniono tryb na: {new_mode}")
        if new_mode == self.mode:
            return
        self.mode = new_mode

        for sub in self.subdirs:
            self.selected_samples[sub].clear()

        for s in self.sample_list:
            self.custom_labels[s] = s

        if self.mode == 'data':
            first_sub = next(iter(self.data_dfs))
            df0 = self.data_dfs[first_sub]
            self.sample_list = sorted(df0['Sample'].unique().tolist())
            print(f"[Mode change] Próbki w 'data': {self.sample_list}")
            self.measurement_types = sorted(df0['Measurement'].unique().tolist())
            self.current_measurement = (
                self.measurement_types[0] if self.measurement_types else None
            )
            if self.measurement_menu is None:
                mode_frame = self.root.children['!frame'].children['!labelframe']
                tk.Label(
                    mode_frame, text="Measurement:"
                ).grid(row=1, column=0, padx=5, pady=2, sticky="w")
                self.measurement_menu = ttk.Combobox(
                    mode_frame, textvariable=self.measurement_var,
                    values=self.measurement_types, state='readonly'
                )
                self.measurement_menu.grid(
                    row=1, column=1, columnspan=1,
                    padx=5, pady=2, sticky="we"
                )
                self.measurement_menu.bind(
                    "<<ComboboxSelected>>", self._on_measurement_change
                )
            else:
                self.measurement_menu.config(
                    values=self.measurement_types, state='readonly'
                )
                self.measurement_menu.set(self.current_measurement)
        else:
            first_sub = next(iter(self.ratio_dfs))
            rdf0 = self.ratio_dfs[first_sub]
            self.sample_list = sorted(rdf0['Sample'].unique().tolist())
            print(f"[Mode change] Próbki w 'ratio': {self.sample_list}")
            if self.measurement_menu:
                self.measurement_menu.destroy()
                self.measurement_menu = None

        for sub, lb in self.listboxes.items():
            print(f"[Mode change] Aktualizuję listę '{sub}'")
            lb.delete(0, tk.END)
            for s in self.sample_list:
                lb.insert(tk.END, s)
        for lb in self.listboxes.values():
            lb.selection_clear(0, tk.END)

        for s in self.sample_list:
            if s not in self.sample_colors:
                self.sample_colors[s] = None
            if s not in self.sample_hatches:
                self.sample_hatches[s] = ""
            if s not in self.sample_hatch_colors:
                self.sample_hatch_colors[s] = None

        self._update_plot()

    def _on_measurement_change(self, event):
        new_measurement = self.measurement_var.get()
        print(f"Zmieniono Measurement na: {new_measurement}")
        if new_measurement == self.current_measurement:
            return
        self.current_measurement = new_measurement
        self._update_plot()

    def _on_listbox_click(self, event, subdir):
        lb = self.listboxes[subdir]
        idx = lb.nearest(event.y)
        if idx < 0 or idx >= len(self.sample_list):
            return
        sample = self.sample_list[idx]

        if sample in self.selected_samples[subdir]:
            print(f"[{subdir}] Odznaczam próbkę: {sample}")
            self.selected_samples[subdir].remove(sample)
            lb.selection_clear(idx)
        else:
            print(f"[{subdir}] Zaznaczam próbkę: {sample}")
            self.selected_samples[subdir].add(sample)
            lb.selection_set(idx)

        self._update_plot()

    def _change_color_popup(self):
        wszystkie_zaznaczone = set().union(*self.selected_samples.values())
        if not wszystkie_zaznaczone:
            messagebox.showinfo("Brak próbek", "Nie zaznaczono żadnych próbek do zmiany koloru.")
            return

        color = colorchooser.askcolor(title="Wybierz kolor dla zaznaczonych próbek")
        if not color or not color[1]:
            return
        rgb_hex = color[1]
        for sample in wszystkie_zaznaczone:
            print(f"Przypisuję kolor {rgb_hex} dla próbki: {sample}")
            self.sample_colors[sample] = rgb_hex

        self._save_color_mapping_to_file()
        self._update_plot()

    def _change_hatch_popup(self):
        wszystkie_zaznaczone = set().union(*self.selected_samples.values())
        if not wszystkie_zaznaczone:
            messagebox.showinfo("Brak próbek", "Nie zaznaczono próbek do wypełnienia.")
            return

        popup = tk.Toplevel(self.root)
        popup.title("Wybierz wzór i kolor wypełnienia")

        tk.Label(popup, text="Wzór:").pack(padx=5, pady=(5, 0))
        hatch_var = tk.StringVar(value="")

        hatch_options = {
            "Brak": "",
            "Kropki": ".",
            "Małe kółka": "o",
            "Duże kółka": "O",
            "Kwadraty": "s",
            "Krzyżyk": "x",
            "Poziome kreski": "-",
            "Pionowe kreski": "|",
            "Plus (krata)": "+",
            "Gwiazdy": "*",
            "Przekątne '/'": "/",
            "Przekątne '\\'": "\\",
            "Kratka z trójkątów": "x"
        }
        comb = ttk.Combobox(
            popup,
            textvariable=hatch_var,
            values=list(hatch_options.keys()),
            state='readonly'
        )
        comb.pack(fill="x", padx=5, pady=(0, 5))
        comb.current(0)

        tk.Label(popup, text="Kolor wypełnienia:").pack(padx=5, pady=(5, 0))
        color_frame = tk.Frame(popup)
        color_frame.pack(fill="x", padx=5, pady=5)

        hatch_color_var = tk.StringVar(value="#000000")
        color_display = tk.Label(
            color_frame, background=hatch_color_var.get(), width=3
        )
        color_display.pack(side="left", padx=(0, 5))

        def pick_hatch_color():
            color = colorchooser.askcolor(title="Wybierz kolor hatch")
            if color and color[1]:
                hatch_color_var.set(color[1])
                color_display.configure(background=color[1])

        pick_btn = tk.Button(color_frame, text="Wybierz kolor", command=pick_hatch_color)
        pick_btn.pack(side="left")

        def apply_hatch():
            selected_hatch_name = hatch_var.get()
            hatch_code = hatch_options[selected_hatch_name]
            hatch_color = hatch_color_var.get()

            for sample in wszystkie_zaznaczone:
                self.sample_hatches[sample] = hatch_code
                self.sample_hatch_colors[sample] = hatch_color

            self._save_color_mapping_to_file()
            self._update_plot()
            popup.destroy()

        save_btn = tk.Button(popup, text="Zastosuj", command=apply_hatch)
        save_btn.pack(pady=(5, 10))

    def _on_width_change(self, val):
        self.bar_width = float(val)
        print(f"Szerokość kolumn ustawiona na: {self.bar_width}")
        self._update_plot()

    def _on_spacing_change(self, val):
        self.group_spacing = float(val)
        print(f"Odległość grup ustawiona na: {self.group_spacing}")
        self._update_plot()

    def _on_font_change(self, val):
        self.label_font_size = int(val)
        print(f"Rozmiar czcionki etykiet ustawiony na: {self.label_font_size}")
        self._update_plot()

    def _on_rotation_change(self, val):
        self.label_rotation = int(val)
        print(f"Kąt nachylenia etykiet ustawiony na: {self.label_rotation}")
        self._update_plot()

    def _edit_labels_popup(self):
        wszystkie_zaznaczone = set().union(*self.selected_samples.values())
        if not wszystkie_zaznaczone:
            messagebox.showinfo("Brak próbek", "Nie zaznaczono żadnych próbek do edycji etykiet.")
            return

        print("Otwieram okno edycji etykiet...")
        popup = tk.Toplevel(self.root)
        popup.title("Edytuj etykiety próbek")

        lbl = tk.Label(popup, text="Zaznaczone próbki:")
        lbl.pack(pady=2)
        sel_list = tk.Listbox(popup, height=10)
        sel_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)
        for sample in sorted(wszystkie_zaznaczone):
            sel_list.insert(tk.END, sample)

        entry_lbl = tk.Label(popup, text="Nowa etykieta dla wybranej próbki:")
        entry_lbl.pack(pady=2)
        entry = tk.Entry(popup, width=30)
        entry.pack(pady=2)

        def on_sample_select(event):
            idx = sel_list.curselection()
            if not idx:
                return
            sample = sel_list.get(idx)
            entry.delete(0, tk.END)
            entry.insert(0, self.custom_labels.get(sample, sample))

        sel_list.bind('<<ListboxSelect>>', on_sample_select)

        def save_label():
            idx = sel_list.curselection()
            if not idx:
                return
            sample = sel_list.get(idx)
            new_label = entry.get().strip()
            if not new_label:
                messagebox.showwarning("Pusta etykieta", "Etykieta nie może być pusta.")
                return
            print(f"Ustawiam nową etykietę dla '{sample}': '{new_label}'")
            self.custom_labels[sample] = new_label
            self._update_plot()

        save_btn = tk.Button(popup, text="Zapisz etykietę", command=save_label)
        save_btn.pack(pady=5)
        close_btn = tk.Button(popup, text="Zamknij", command=popup.destroy)
        close_btn.pack(pady=5)

    def _update_plot(self):
        print("Aktualizacja wykresu (per subdir z intra_gap, kolorem i wypełnieniem)...")
        self.ax.clear()

        bar_w = self.bar_width
        spacing = self.group_spacing
        intra_gap = 0.2 * bar_w
        cumulative_x_pos = 0

        x_ticks = []
        x_labels = []
        any_plotted = False

        default_color_idx = 0

        for sub in self.subdirs:
            selected_in_sub = sorted(self.selected_samples[sub])
            if not selected_in_sub:
                continue

            any_plotted = True
            print(f"[{sub}] Zaznaczone próbki: {selected_in_sub}")

            n = len(selected_in_sub)
            means = []
            stds = []
            for s in selected_in_sub:
                if self.mode == 'data':
                    df = self.data_dfs.get(sub)
                    df_s = df[
                        (df['Sample'] == s) &
                        (df['Measurement'] == self.current_measurement)
                    ]
                    if not df_s.empty:
                        means.append(df_s['Mean'].values[0])
                        stds.append(df_s['Std'].values[0])
                    else:
                        means.append(0)
                        stds.append(0)
                else:
                    rdf = self.ratio_dfs.get(sub)
                    df_s = rdf[rdf['Sample'] == s]
                    if not df_s.empty:
                        means.append(df_s['Ratio_Mean'].values[0])
                        stds.append(df_s['Ratio_Std'].values[0])
                    else:
                        means.append(0)
                        stds.append(0)

            group_width = n * bar_w + (n - 1) * intra_gap
            base = cumulative_x_pos
            xs = [base + i * (bar_w + intra_gap) for i in range(n)]
            print(f"[{sub}] xs={xs}, means={means}, stds={stds}")

            bar_colors = []
            bar_hatches = []
            bar_hatch_colors = []
            for s in selected_in_sub:
                col = self.sample_colors.get(s)
                if col:
                    bar_colors.append(col)
                else:
                    color = self.default_colors[default_color_idx % len(self.default_colors)]
                    bar_colors.append(color)
                    default_color_idx += 1

                hatch_code = self.sample_hatches.get(s, "")
                bar_hatches.append(hatch_code)

                hatch_col = self.sample_hatch_colors.get(s)
                bar_hatch_colors.append(hatch_col if hatch_col else 'black')

            self.ax.bar(
                xs, means, yerr=stds,
                width=bar_w, label=sub, capsize=5,
                color=bar_colors, hatch=bar_hatches,
                edgecolor=bar_hatch_colors,
            )

            for i, s in enumerate(selected_in_sub):
                x_ticks.append(xs[i])
                x_labels.append(self.custom_labels.get(s, s))

            cumulative_x_pos += group_width + spacing

        if not any_plotted:
            self.ax.set_title("Brak zaznaczonych próbek")
            self.canvas.draw()
            return

        print(f"Etykiety osi X: {x_labels}")
        self.ax.set_xticks(x_ticks)
        self.ax.set_xticklabels(
            x_labels, rotation=self.label_rotation,
            fontsize=self.label_font_size, ha='right'
        )

        self.ax.legend(title="Podkatalogi", fontsize=8)
        self.ax.set_ylabel("Wartość")
        self.ax.set_xlabel("Próbka")
        self.ax.set_title("Wykres próbek (oddzielnie per lista)")

        self.canvas.draw()

    def run(self):
        print("Uruchamiam pętlę główną tkinter...")
        self.root.mainloop()


if __name__ == '__main__':
    app = PlotSelector()
    app.run()
