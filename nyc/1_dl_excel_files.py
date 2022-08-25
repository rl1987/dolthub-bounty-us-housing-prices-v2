#!/usr/bin/python3

import csv
import os
import sys
import subprocess

def main():
    if len(sys.argv) != 3:
        print("Usage:")
        print("{} <url_list> <output_dir>".format(sys.argv[0]))
        return

    url_list = sys.argv[1]
    output_dir = sys.argv[2]

    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)

    in_f = open(url_list, "r")

    csv_reader = csv.DictReader(in_f)

    for in_row in csv_reader:
        output_path = os.path.join(output_dir, in_row.get("filename"))
        url = in_row.get("url")
        
        if os.path.isfile(output_path):
            continue

        subprocess.run(["wget", url, "-O", output_path], capture_output=False)

    in_f.close()

if __name__ == "__main__":
    main()

