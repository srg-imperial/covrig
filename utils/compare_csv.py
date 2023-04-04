import csv

def compare_csv(args):
    # read the csv files
    reader1 = csv.reader(args.file1)
    reader2 = csv.reader(args.file2)

    # get the header row
    header1 = next(reader1)
    header2 = next(reader2)

    # compare the headers
    if header1 != header2:
        print('WARNING: Headers are different')

    print(len(header1))

    # for each column in the csv file, get the maximum absolute difference between the two files
    for i in range(len(header1)):
        max_diff = 0
        idx = 0
        count = 0
        for row1, row2 in zip(reader1, reader2):
            # ignore rows where either has a compileError or EmptyCommit in any of the columns
            if any([row1[j] == 'compileError' for j in range(len(row1))]) or \
                    any([row2[j] == 'compileError' for j in range(len(row2))]):
                count += 1
                # print('Skipping row {} due to compileError'.format(count))
                continue
            if any([row1[j] == 'EmptyCommit' for j in range(len(row1))]) or \
                    any([row2[j] == 'EmptyCommit' for j in range(len(row2))]):
                count += 1
                continue

            try:
                diff = abs(float(row1[i]) - float(row2[i]))
            except ValueError:
                diff = 0
            if diff > max_diff:
                max_diff = diff
                idx = count
            count += 1
        # Reset the file pointers
        args.file1.seek(0)
        args.file2.seek(0)
        print('Max difference for column {}: {} at line {}'.format(header1[i], max_diff, idx))

# compare csv files as above but calculate the average difference
def compare_csv_avg(args):
    # read the csv files
    reader1 = csv.reader(args.file1)
    reader2 = csv.reader(args.file2)

    # get the header row
    header1 = next(reader1)
    header2 = next(reader2)

    # compare the headers
    if header1 != header2:
        print('WARNING: Headers are different')

    print(len(header1))

    # for each column in the csv file, get the average absolute difference between the two files
    for i in range(len(header1)):
        total_diff = 0
        count = 0
        # deviated_count = 0
        for row1, row2 in zip(reader1, reader2):
            # ignore rows where either has a compileError or EmptyCommit in any of the columns
            if any([row1[j] == 'compileError' for j in range(len(row1))]) or \
                    any([row2[j] == 'compileError' for j in range(len(row2))]):
                count += 1
                # print('Skipping row {} due to compileError'.format(count))
                continue
            if any([row1[j] == 'EmptyCommit' for j in range(len(row1))]) or \
                    any([row2[j] == 'EmptyCommit' for j in range(len(row2))]):
                count += 1
                continue

            try:
                diff = abs(float(row1[i]) - float(row2[i]))
                # if diff != 0:
                #     deviated_count += 1
            except ValueError:
                diff = 0
            total_diff += diff
            count += 1
        # Reset the file pointers
        args.file1.seek(0)
        args.file2.seek(0)
        # stat = total_diff/deviated_count if deviated_count != 0 else 0
        stat = total_diff/count if count != 0 else 0
        print('Average difference for column {}: {}'.format(header1[i], stat))

if __name__ == '__main__':
    import argparse
    import os

    # use argparse to get the two csv files
    parser = argparse.ArgumentParser(description='Compare two csv files.')
    parser.add_argument('file1', type=argparse.FileType('r'),
                        help='First file to compare')
    parser.add_argument('file2', type=argparse.FileType('r'),
                        help='Second file to compare')
    args = parser.parse_args()
    compare_csv(args)
    compare_csv_avg(args)
