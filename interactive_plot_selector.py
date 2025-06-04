import tkinter as tk
from tkinter import ttk, colorchooser
import os
import csv
import matplotlib.pyplot as plt
from logger_setup import logger

DATA_DIR = 'data'
CONFIG_DIR = 'configs'

os.makedirs(CONFIG_DIR, exist_ok=True)

class PlotSelector:
    def __init__(self):
        logger.info('Initializing PlotSelector')
        self.data = self._load_data()
        self.root = tk.Tk()
        self.root.title('Interactive Plot Selector')
        self.selected = []
        self._build_gui()

    def _load_data(self):
        logger.debug('Loading analysed data')
        data = {}
        for fname in os.listdir(DATA_DIR):
            if fname.endswith('_analysed.csv'):
                with open(os.path.join(DATA_DIR, fname), newline='', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        sample = row['Sample']
                        mean = row.get('Ratio_Mean') or row.get('Mean')
                        std = row.get('Ratio_Std') or row.get('Std')
                        if mean is None:
                            continue
                        data.setdefault(sample, {'mean':float(mean), 'std':float(std) if std else 0.0})
        logger.debug('Loaded samples: %s', list(data.keys()))
        return data

    def _build_gui(self):
        listbox = tk.Listbox(self.root, selectmode=tk.MULTIPLE)
        for s in sorted(self.data.keys()):
            listbox.insert(tk.END, s)
        listbox.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        self.listbox = listbox
        btn_plot = ttk.Button(self.root, text='Rysuj', command=self.draw_plot)
        btn_plot.pack(side=tk.LEFT, padx=5)

    def draw_plot(self):
        selections = [self.listbox.get(i) for i in self.listbox.curselection()]
        if not selections:
            return
        means = [self.data[s]['mean'] for s in selections]
        stds = [self.data[s]['std'] for s in selections]
        colors = []
        for s in selections:
            color = colorchooser.askcolor(title=f'Kolor dla {s}')[1]
            if not color:
                color = 'blue'
            colors.append(color)
        plt.figure(figsize=(10,6))
        plt.bar(range(len(selections)), means, yerr=stds, color=colors, tick_label=selections)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

    def run(self):
        logger.info('Running PlotSelector GUI')
        self.root.mainloop()

if __name__ == '__main__':
    app = PlotSelector()
    app.run()
