# Tiny script to sum csvs element-wise (needed for Binutils & Binutils-GDB)

import csv
import argparse


def main():
    # Argparse code - one ouput and one or more input files
    parser = argparse.ArgumentParser(description='Sum csvs element-wise')
    parser.add_argument('output_file', type=str, help='Output file')
    parser.add_argument('input_files', type=str, nargs='+', help='Input files')
    args = parser.parse_args()

    # Read in input files
    input_files = [open(file, 'r') for file in args.input_files]
    readers = [csv.reader(file) for file in input_files]

    # Write to output file
    skipped_header = False
    with open(args.output_file, 'w') as f:
        writer = csv.writer(f)
        for rows in zip(*readers):
            # Skip the header
            if not skipped_header:
                skipped_header = True
                # Write the header
                writer.writerow(rows[0])
                continue
            # Add each element together between the rows (like a zip)
            writer.writerow([sum(int(row[i]) for row in rows) for i in range(len(rows[0]))])

    # Close input files
    for file in input_files:
        file.close()

    # Print success message
    print(f"Successfully summed {len(args.input_files)} files and wrote to {args.output_file}")


if __name__ == '__main__':
    main()
