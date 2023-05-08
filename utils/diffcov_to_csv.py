# Script to take genhtml data and convert to a csv file
import csv
import re


### i.e. this data:
# Overall coverage rate:
#   lines......: 71.9% (4990 of 6939 lines)
#        UNC...: 1556
#        LBC...: 10
#        UIC...: 32
#        UBC...: 351
#        GBC...: 242
#        GIC...: 21
#        GNC...: 3114
#        CBC...: 1613
#        ECB...: 12
#        DUB...: 513
#        DCB...: 671
#   functions......: 82.3% (767 of 932 functions)
#        UNC...: 103
#        LBC...: 1
#        UIC...: 15
#        UBC...: 46
#        GBC...: 25
#        GIC...: 19
#        GNC...: 365
#        CBC...: 358
#        EUB...: 2
#        ECB...: 8
#        DUB...: 30
#        DCB...: 81
#   branches......: 41.6% (3446 of 8281 branches)
#        UNC...: 3993
#        LBC...: 10
#        UIC...: 104
#        UBC...: 728
#        GBC...: 159
#        GIC...: 63
#        GNC...: 2479
#        CBC...: 745
#        EUB...: 51
#        ECB...: 39
#        DUB...: 895
#        DCB...: 522

# to a csv with the following format:
# UNC, LBC, UIC, UBC, GBC, GIC, GNC, CBC, EUB, ECB, DUB, DCB

def convert_to_csv(input_file: str, output_file: str):
    # Read in input file
    with input_file as f:
        lines = f.readlines()

    # Keep all beyond the line that says "Overall coverage rate:"
    lines = lines[lines.index('Overall coverage rate:\n') + 1:]

    # Strip the new line characters and any leading or trailing white space
    lines = [line.strip() for line in lines]

    idxs = []
    # Find the index of the line that says "lines......:", "functions......:", and "branches......:"
    for i in range(len(lines)):
        if lines[i].startswith('lines......:'):
            idxs.append(i)
        elif lines[i].startswith('functions......:'):
            idxs.append(i)
        elif lines[i].startswith('branches......:'):
            idxs.append(i)

    # Split lines into sets based on the idxs
    coverage_types = {'lines': lines[idxs[0]:idxs[1]],
                      'functions': lines[idxs[1]:idxs[2]],
                      'branches': lines[idxs[2]:]}

    bins = ['UNC', 'LBC', 'UIC', 'UBC', 'GBC', 'GIC', 'GNC', 'CBC', 'EUB', 'ECB', 'DUB', 'DCB']

    # For each of the coverage types, extract the data according to the bins
    coverage_data = {}
    for cov_type in coverage_types:
        coverage_data[cov_type] = {}
        for bin in bins:
            coverage_data[cov_type][bin] = 0
        for line in coverage_types[cov_type]:
            for bin in bins:
                if bin in line:
                    coverage_data[cov_type][bin] = int(re.findall('\d+', line)[0])

    # Extract the data into a csv file
    with output_file as f:
        writer = csv.writer(f)
        writer.writerow(bins)
        for cov_type in coverage_data:
            writer.writerow([coverage_data[cov_type][bin] for bin in bins])


def main():
    # Argparse code
    import argparse
    parser = argparse.ArgumentParser(description='Convert genhtml data to csv')
    parser.add_argument('input', type=argparse.FileType('r', errors='replace'),
                        help='Input file')
    parser.add_argument('output', type=argparse.FileType('w', errors='replace'),
                        help='Output file')
    args = parser.parse_args()
    convert_to_csv(args.input, args.output)


if __name__ == '__main__':
    main()
