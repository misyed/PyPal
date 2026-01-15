# PyPal: Wi-Fi Trace Synchronisation and Merging Tool

This is a **one-off extended version** of the Wi-Fi trace synchronisation and merging tool [**PyPal**](https://gitlab.lip6.fr/syed/pypal), developed during the author’s Ph.D. research. This version introduces performance efficiency and a graphical user interface (GUI) to simplify execution.

---

## Disclaimer

This project is **not actively maintained** and is released for research and academic use under the licence [GNU General Public License v3.0](https://spdx.org/licenses/GPL-3.0-or-later.html) or later. Use of this code is at your own discretion, and we encourage you to exercise caution and discretion in its adaptation.

---

## Background

The original PyPal tool was developed within the ANR MITIK project and is partially related to Mohammad Imran Syed's Ph.D. thesis titled ["Wireless passive measurements: tool, redundancy, measurements, and analyses"](https://theses.hal.science/tel-04258062).

Original repository:  
https://gitlab.lip6.fr/syed/pypal  

Technical report (contains the algorithmic details):  
https://hal.science/hal-03618014

---

## Dependencies

The tool requires **Python 3** and the following Python libraries:

- `numpy`
- `pandas`
- `scikit-learn`
- `PySide6` (required only for the GUI version)

These dependencies must be installed manually before running the tool.

---

## Trace file format

You would need to have the following fields in the traces:

- frame.number: Frame_number
- frame.time_epoch: Frame_time_epoch
- wlan.fixed.timestamp: Fixed_timestamp
- wlan_radio.signal_dbm: RSSI_dBm
- wlan_radio.channel: Channel
- wlan.fc.type: Frame_type
- wlan.fc.type_subtype: Frame_subtype
- wlan.fc.retry: Retransmission
- wlan.fcs: Checksum
- wlan.sa: Source_MAC_address
- wlan.seq: Sequence_number
- wlan.frag: Fragment_number

You can use the following tshark command to extract the above mentioned fields from a pcap file (make sure you use the channel number corresponding to your traces).

tshark -r pcap_input_file -Y '!_ws.malformed and wlan_radio.channel==1' -T fields -E header=y -E separator=/t -e frame.number -e frame.time_epoch -e wlan.fixed.timestamp -e wlan_radio.signal_dbm -e wlan_radio.channel -e wlan.fc.type -e wlan.fc.type_subtype -e wlan.fc.retry -e wlan.fcs -e wlan.sa -e wlan.seq -e wlan.frag > csv_or_txt_output_file

It is recommended to use tshark version 3.2.3 or lower. Version 4.2.5, for example, processes the pcap files differently and creates hex and Boolean values for frame subtype and retransmission bit respectively. Whereas, the tool expects these values to be integers.

**It is, however, essential to clearly define which data one can sniff depending on the location of the measurement campaign to preserve the privacy of the users. It is also necessary to carry out hashing of MAC addresses to preserve the privacy.**

---

## Installation

Python 3 is required.

```bash
git clone https://github.com/misyed/PyPal
cd PyPal
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

## Citation

If you use this tool in your research, please cite:

@techreport{syed:hal-03618014,
  TITLE = {{PyPal: Wi-Fi Trace Synchronization and Merging Python Tool}},
  AUTHOR = {Syed, Mohammad Imran and Fladenmuller, Anne and Dias de Amorim, Marcelo},
  URL = {https://hal.science/hal-03618014},
  TYPE = {Technical Report},
  INSTITUTION = {{LIP6 UMR 7606, Sorbonne Universit{\'e}, France}},
  YEAR = {2022},
  MONTH = Mar,
  HAL_ID = {hal-03618014},
}

M. I. Syed, A. Flandenmuller, M. Dias de Amorim. PyPal: Wi-Fi Trace Synchronization and Merging Python Tool. [Technical Report] LIP6 UMR 7606, UPMC Sorbonne Université, France. 2022. [hal-03618014](https://hal.science/hal-03618014)
