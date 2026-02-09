#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import math
import argparse
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

pd.options.mode.chained_assignment = None

RENAME_MAP = {
    "frame.number": "Frame_number",
    "frame.time_epoch": "Frame_time_epoch",
    "wlan.fixed.timestamp": "Fixed_timestamp",
    "wlan_radio.signal_dbm": "RSSI_dBm",
    "wlan_radio.channel": "Channel",
    "wlan.fc.type": "Frame_type",
    "wlan.fc.type_subtype": "Frame_subtype",
    "wlan.fc.retry": "Retransmission",
    "wlan.fcs": "Checksum",
    "wlan.sa": "Source_MAC_address",
    "wlan.seq": "Sequence_number",
    "wlan.frag": "Fragment_number",
}

FILL_ZERO_COLS = [
    "Source_MAC_address",
    "Sequence_number",
    "Checksum",
    "Fragment_number",
    "Fixed_timestamp",
]

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)
    os.chmod(path, 0o777)

class PyPal:

    def _load_trace(self, path):
        df = pd.read_csv(path, delimiter="\t")
        df = df.rename(columns=RENAME_MAP)
        for c in FILL_ZERO_COLS:
            df[c] = df[c].fillna(0)
        return df

    def _extract_unique_frames(self, df):
        return df.loc[(df["Frame_subtype"].isin([5, 8])) & (df["Retransmission"] == 0)].copy()

    def UniqueFrames(self, trace1, trace2):
        """
        Method to extract the unique frames

        :param trace1: trace file to be synchronised
        :param trace2: reference trace file
        """
        ensure_dir("TXTTraces")

        self.TRACE1 = self._load_trace(trace1)
        self.TRACE2 = self._load_trace(trace2)

        UniqueFrames1 = self._extract_unique_frames(self.TRACE1)
        UniqueFrames2 = self._extract_unique_frames(self.TRACE2)

        self.TRACE1.to_csv(f"TXTTraces/{self.trace1_name}", index=False, sep="\t")
        self.TRACE2.to_csv(f"TXTTraces/{self.trace2_name}", index=False, sep="\t")

        if self.U:
            ensure_dir("UniqueFrames")
            directory = "UniqueFrames"
            UniqueFrames1.to_csv(f"UniqueFrames/UniqueFrames_{self.trace1_name}", index=False, sep="\t")
            UniqueFrames2.to_csv(f"UniqueFrames/UniqueFrames_{self.trace2_name}", index=False, sep="\t")
            print("="*92)
            print(f"✅ \033[1mUnique frames\033[0m have been \033[1mextracted\033[0m to txt files and saved in \033[1m{directory}\033[0m directory.")
            print("="*92)
            return

        self.ExtractReferenceFrames(UniqueFrames1, UniqueFrames2)

    def ExtractReferenceFrames(self, UF1, UF2):
        """
        Method to extract reference frames from unique frames
        
        :param UF1: dataframe of unique frames of trace1
        :param UF2: dataframe of unique frames of trace2
        """
        UF1 = UF1.copy()
        UF2 = UF2.copy()

        # using a combination of source MAC address, sequence number, frame subtype, checksum,
        # fragment number, and fixed timestamp as key of the dictionary. This helps in finding
        # unique frames those are present in both the traces i.e. reference frames

        UF1["key"] = (
            UF1["Source_MAC_address"].astype(str)
            + UF1["Sequence_number"].astype(str)
            + UF1["Frame_subtype"].astype(str)
            + UF1["Checksum"].astype(str)
            + UF1["Fragment_number"].astype(str)
            + UF1["Fixed_timestamp"].astype(str)
        )
        UF2["key"] = (
            UF2["Source_MAC_address"].astype(str)
            + UF2["Sequence_number"].astype(str)
            + UF2["Frame_subtype"].astype(str)
            + UF2["Checksum"].astype(str)
            + UF2["Fragment_number"].astype(str)
            + UF2["Fixed_timestamp"].astype(str)
        )

        merged = UF1.merge(UF2, on="key", suffixes=("_1","_2"), how="inner")

        REFERENCE_FRAMES = merged[["Frame_number_1","Frame_number_2"]].values.tolist()
        REF_T1 = merged["Frame_time_epoch_1"].tolist()
        REF_T2 = merged["Frame_time_epoch_2"].tolist()

        if self.R:
            ensure_dir("ReferenceFrames")
            directory = "ReferenceFrames"
            if os.path.exists("ReferenceFrames/REFERENCE_FRAMES.txt"):
                print("WARNING: ReferenceFrames/REFERENCE_FRAMES.txt exists and will be overwritten")
            with open("ReferenceFrames/REFERENCE_FRAMES.txt","w") as f:
                for a,b in REFERENCE_FRAMES:
                    f.write(f"{a}\t{b}\n")
            print("="*102)
            print(f"✅ Unique \033[1mreference frames\033[0m have been extracted to txt files and saved in \033[1m{directory}\033[0m directory.")
            print("="*102)
            return

        self.SynchroniseReferenceFrames(REFERENCE_FRAMES, REF_T1, REF_T2)

    def SynchroniseReferenceFrames(self, REF_FRAMES, REF_T1, REF_T2):
        """
        Method to synchronise reference frames
        
        :param REF_FRAMES: list of epoch timestamps for reference frames of both traces
        :param REF_T1: list of epoch timestamps for reference frames of trace1
        :param REF_T2: list of epoch timestamps for reference frames of trace2
        """
        ensure_dir("SynchronisedReferenceFrames")
        directory = "SynchronisedReferenceFrames"

        model = LinearRegression()
        window = 3
        q = {}
        a0, b0 = [], []

        with open("SynchronisedReferenceFrames/Synchronised_Reference_Frames.txt","w") as f:
            f.write("a\tb\tframe1\tframe2\ttime1\ttime2\terror\n")
            for i in range(len(REF_T1)):
                if i == 0:
                    x = REF_T1[:window]
                    y = REF_T2[:window]
                elif i==len(REF_T1)-1:
                    x = REF_T1[-window:]
                    y = REF_T2[-window:]
                else:
                    x = REF_T1[i-1:i+2]
                    y = REF_T2[i-1:i+2]

                t1 = REF_T1[i] # timestamp of 1st trace which has to be synchronised
                s = REF_T2[i]  # timestamp of 2nd trace for finding error between timestamps after synchronisation

                model.fit(np.array(x).reshape(-1,1),y)
                a = model.coef_[0]
                b = model.intercept_

                t2 = a * t1 + b
                err = t2 - s

                if abs(err) <= 106/1_000_000:
                    a0.append(a)
                    b0.append(b)
                    q[REF_FRAMES[i][0]] = t2
                    f.write(f"{a}\t{b}\t{REF_FRAMES[i][0]}\t{REF_FRAMES[i][1]}\t{t2}\t{s}\t{err}\n")

        if self.SR:
            print("="*129)
            print(f"✅ \033[1mUnique reference frames\033[0m have been \033[1msynchronised\033[0m and saved in \033[1m{directory}\033[0m directory.")
            print("="*129)
            return

        df = pd.read_csv("SynchronisedReferenceFrames/Synchronised_Reference_Frames.txt", sep="\t").sort_values(["frame1","frame2"])
        df.to_csv("SynchronisedReferenceFrames/Synchronised_Reference_Frames.txt", index=False, sep="\t")
        self.SynchroniseTrace(df["a"].tolist(), df["b"].tolist(), q)

    def SynchroniseTrace(self, a0, b0, q):
        """
        Method to extend synchronisation of reference frames
        to synchronise trace1 with respect to reference trace2
        
        Following two parameters (a and b) are from the linear regression equation y = a + bx
        :param a0: list of intercept values of the regression line for synchronised reference frames
        :param b0: list of slope of the regression line for synchronised reference frames
        :param q: dictionary of linear regression values for synchronised reference frames
        """
        ensure_dir("SynchronisedTraces")
        directory = "SynchronisedTraces"

        fn_array = self.TRACE1["Frame_number"].to_numpy()
        ts_array = self.TRACE1["Frame_time_epoch"].to_numpy()
        new_ts = np.empty_like(ts_array,dtype=float)

        k = 0
        a, b = a0[k], b0[k]
        first = list(q.keys())[0]

        for i in range(len(fn_array)):
            fn = fn_array[i]
            if fn in q:
                new_ts[i] = q[fn]
                if k < len(a0)-1 and fn > first:
                    k += 1
                    a, b = a0[k], b0[k]
            else:
                new_ts[i] = a*ts_array[i] + b

        self.TRACE1["Frame_time_epoch"] = new_ts

        self.TRACE1.to_csv(f"SynchronisedTraces/Synchronised_Trace_{self.trace1_name}", index=False, sep="\t")
        self.TRACE2.to_csv(f"SynchronisedTraces/Synchronised_Trace_{self.trace2_name}", index=False, sep="\t")

        if self.S:
            print("="*106)
            print(f"✅ Traces have been \033[1msynchronised\033[0m and saved in \033[1m{directory}\033[0m directory.")
            print("="*106)
            return

        self.MergeTraces()

    def MergeTraces(self):
        """
        Method to:
            - either concatenate traces and keep all the duplicate packets
              and generate per MAC address traces (or per user traces if one is able to solve MAC address randimisation)
            - or merge traces to measure trace completeness by removing the duplicate packets
        """
        
        # Add trace name to each frame
        add_trace_name = str(self.trace1_name)
        self.TRACE1['Trace_name'] = add_trace_name
        add_trace_name = str(self.trace2_name)
        self.TRACE2['Trace_name'] = add_trace_name

        if self.C:
            ensure_dir("ConcatenatedTrace")
            directory = "ConcatenatedTrace"

            traces = [self.TRACE1, self.TRACE2]

            concatenated = pd.concat(traces)
            concatenated = concatenated.sort_values(by=['Frame_time_epoch'])
            new_frame_no = list(range(1, len(concatenated)+1))
            concatenated['Frame_number'] = new_frame_no
            f = f"{directory}/ConcatenatedTrace.txt"
            concatenated.to_csv(f, index=False, header=True, sep='\t')

            print("="*110)
            print(f"✅ \033[1mConcatenation\033[0m (with duplicates) completed, trace has been saved in \033[1m{directory}\033[0m directory.")

            # Extract per-user traces
            per_user_dir = f"{directory}/PerUserTraces"
            ensure_dir(per_user_dir)
            trace1_dir = f"{per_user_dir}/Trace1"
            trace2_dir = f"{per_user_dir}/Trace2"
            ensure_dir(trace1_dir)
            ensure_dir(trace2_dir)

            # TRACE1 per-user
            for i, mac in enumerate(self.TRACE1["Source_MAC_address"].unique()):
                self.TRACE1[self.TRACE1.Source_MAC_address == mac].to_csv(f"{trace1_dir}/User_{i+1}.txt", index=False, sep="\t")

            # TRACE2 per-user
            for i, mac in enumerate(self.TRACE2["Source_MAC_address"].unique()):
                self.TRACE2[self.TRACE2.Source_MAC_address == mac].to_csv(f"{trace2_dir}/User_{i+1}.txt", index=False, sep="\t")
            
            print("")
            print(f"✅ \033[1mPer-user traces\033[0m have been saved in \033[1m{directory}/PerUserTraces/\033[0m directory.")
            print("="*110)

            return

        ensure_dir("MergedTrace")
        directory = "MergedTrace"

        # Create unique keys using source mac address, sequence number, frame subtype,
        # checksum, fragment number, and fixed timestamp for the ease of detecting duplicate frames
        # this key ensures that unique packets are not otherwise considered duplicate
        # for example sequence numbers are repeated, capturing device might drop
        # the framecheck sequence values, and so on
        def create_key(df):
            return (
                df["Source_MAC_address"].astype(str)
                + df["Sequence_number"].astype(str)
                + df["Frame_subtype"].astype(str)
                + df["Checksum"].astype(str)
                + df["Fragment_number"].astype(str)
                + df["Fixed_timestamp"].astype(str)
            )

        self.TRACE1["Unique_key"]=create_key(self.TRACE1)
        self.TRACE2["Unique_key"]=create_key(self.TRACE2)

        # Use the pandas dataframe merge option (which is a sort of a concatenation)
        # Sort values by timestamp and unique key to make sure duplicate frames are well placed to be detected
        merged = pd.merge(
            self.TRACE1,
            self.TRACE2,
            on=["Frame_number","Frame_time_epoch","Fixed_timestamp","RSSI_dBm","Channel","Frame_type",
                "Frame_subtype","Retransmission","Checksum","Source_MAC_address","Sequence_number",
                "Fragment_number","Unique_key", "Trace_name"], how="outer"
        ).sort_values(["Frame_time_epoch","Unique_key"])

        # Identify duplicates
        # Shifting timestamp, unique key and rssi values to facilitate
        # the comparisons and eventually identify the duplicate frames
        merged['next_ts'] = merged['Frame_time_epoch'].shift(-1)
        merged['next_key'] = merged['Unique_key'].shift(-1)
        merged['next_rssi'] = merged['RSSI_dBm'].shift(-1)

        diff = []
        dup = 0
        for row in merged.itertuples():
            if dup == 1:
                diff.append('Unique')
                dup = 0
            elif dup == 2:
                diff.append('Duplicate')
                dup = 0
            elif row.next_key == row.Unique_key:
                k = row.next_ts - row.Frame_time_epoch
                if abs(k) < 106/1_000_000:
                    if row.next_rssi > row.RSSI_dBm:
                        diff.append('Duplicate')
                        dup = 1
                    else:
                        diff.append('Unique')
                        dup = 2
                else:
                    diff.append('Unique')
            else:
                diff.append('Unique')
            
            """
            # to keep the first unique packet and all other duplicate packets irrespective of the RSSI values
            if dup == 1:
                diff.append('Duplicate')
                dup = 0
            elif row.next_key == row.Unique_key:
                k = row.next_ts - row.Frame_time_epoch
                if abs(k) < 106/1000000:
                    diff.append('Unique')
                    dup = 1
                    #diff.append('Duplicate')
                    trace_name = str(row.Trace_name) + "-" + str(row.next_trace_name)
                    trace_name = trace_name.split('-')
                    trace_name = sorted(trace_name)
                    trace_name = '-'.join(trace_name)
                    self.TRACE1.loc[row.Index, 'Trace_name'] = trace_name
                else:
                    diff.append('Unique')
            else:
                diff.append('Unique')"""

        if len(diff) < len(merged): diff.append('Unique')
        merged['Unique_or_Duplicate'] = diff

        merged.drop(columns = ['next_key','next_ts','next_rssi'], inplace=True)

        # Save the trace with containing unique and duplicate labels for frames
        merged.to_csv(f"{directory}/Merged_Trace_with_Unique-Duplicate_Label.txt", index=False, sep="\t")

        # Remove duplicate frames
        merged = merged[merged.Unique_or_Duplicate!="Duplicate"].sort_values("Frame_time_epoch")
        merged.drop(columns = ['Unique_or_Duplicate'], inplace=True)
        merged["Frame_number"] = range(1, len(merged)+1)

        # Save the final (duplicate frame free) merged trace
        merged.to_csv(f"{directory}/Merged_Trace.txt", index=False, sep="\t")
        print("="*110)
        print(f"✅ \033[1mMerging without duplicates\033[0m completed, trace has been saved in \033[1m{directory}\033[0m directory.")
        print("="*110)


def main():
    start=time.time()

    parser=argparse.ArgumentParser(description="PyPal 1.0 Trace Merging Tool")
    parser.add_argument("trace1", type = str, help="First trace file: Trace to be sychronised.")
    parser.add_argument("trace2", type = str, help="Second trace file: Reference trace.")
    parser.add_argument('-U', help='Extract unique frames', required = False, nargs='?', const='True')
    parser.add_argument('-R', help='Extract unique reference frames', required = False, nargs='?', const='True')
    parser.add_argument('-SR', help='Synchronise unique reference frames', required = False, nargs='?', const='True')
    parser.add_argument('-S', help='Synchronise traces', required = False, nargs='?', const='True')
    parser.add_argument('-C', help='Concatenate traces (and keep the duplicate frames)', required = False, nargs='?', const='True')
    parser.add_argument('-M', help='Merge traces and remove the duplicate frames within a time difference of 106us', required = False, nargs='?', const='True')

    args=parser.parse_args()

    if not any([args.U, args.R, args.SR, args.S, args.C, args.M]):
        parser.error("❌ No action requested")

    pypal=PyPal()
    pypal.trace1_name = f"{args.trace1[:-4]}.txt"
    pypal.trace2_name = f"{args.trace2[:-4]}.txt"

    pypal.U = args.U
    pypal.R = args.R
    pypal.SR = args.SR
    pypal.S = args.S
    pypal.C = args.C
    pypal.M = args.M

    pypal.UniqueFrames(args.trace1, args.trace2)
    
    print("*"*50)
    print(f"⏱  \033[1;32mTime Taken: {time.time()-start:.3f} seconds\033[0m")
    print("*"*50)

if __name__=="__main__":
    main()
