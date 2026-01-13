# PyPal: Wi-Fi Trace Synchronisation and Merging Tool

This is a **one-off extended version** of the Wi-Fi trace synchronisation and merging tool [**PyPal**](https://gitlab.lip6.fr/syed/pypal), developed during the author’s Ph.D. research.  
This version introduces performance improvement and a graphical user interface (GUI) to simplify execution.

This project is **not actively maintained** and is released for research and academic use.

---

## Background

The original PyPal tool was developed within the ANR MITIK project and is partially related to Mohammad Imran Syed's Ph.D. thesis titled ["Wireless passive measurements: tool, redundancy, measurements, and analyses"](https://theses.hal.science/tel-04258062)

Original repository:  
https://gitlab.lip6.fr/syed/pypal  

Technical report (contains the algorithmic details):  
https://hal.science/hal-03618014v5

---

## Dependencies

The tool requires **Python 3** and the following Python libraries:

- `numpy`
- `pandas`
- `scikit-learn`
- `PySide6` (required only for the GUI version)

These dependencies must be installed manually before running the tool.

---

## Installation

Python 3 is required.

```bash
git clone https://github.com/misyed/pypal
cd pypal-gui
pip install -r requirements.txt
```

---

## Usage (Command-Line Interface)

Display help and available options:

```bash
python3 pypal.py -h
```

### Positional Arguments

- trace1 — trace to be synchronised
- trace2 — reference trace

### Optional Arguments

(Only one option can be used at a time.)

- -U Extract unique frames
- -R Extract unique reference frames
- -SR Synchronise unique reference frames
- -S Synchronise traces
- -C Concatenate traces and keep duplicate frames
- -M Merge traces and remove duplicate frames within a 106 µs time window

Example

Synchronise two traces:
```bash
python3 pypal.py trace1.csv trace2.csv -S
```

---

## GUI Version

The GUI version allows users to:

- Browse and select trace files
- Select one of the available processing modes
- Execute the process while showing the progress

---

## License

This project is licensed under the GNU General Public License v3.0 or later, consistent with the original PyPal tool.

---

## Disclaimer

This tool is intended for research and experimental use. Use of this code is at your own discretion, and we encourage you to exercise caution and discretion in its adaptation.
