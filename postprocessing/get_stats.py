# # Globals that tell the script the layout of the csv files
# from matplotlib import pyplot as plt
import internal.csv_utils as utils
import statistics


def export_number_revs(data, csv_name):
    # Export the number of revisions to a file

    # Clean the data
    cleaned_data = utils.clean_data(data, omit=['EmptyCommit', 'NoCoverage'])

    # Get the dates
    exit_statuses, dates = utils.get_columns(cleaned_data, ['exit', 'time'])

    # Count the number of revisions for each of the exit statuses
    num_revs = {'OK': 0, 'SomeTestFailed': 0, 'TimedOut': 0, 'compileError': 0, }
    for exit_status in exit_statuses:
        if exit_status not in num_revs:
            num_revs[exit_status] = 0
        num_revs[exit_status] += 1

    # Get the first and last dates
    first_date = dates[0]
    last_date = dates[-1]

    # Get the number of months between the first and last dates
    num_months = (last_date.year - first_date.year) * 12 + (last_date.month - first_date.month)

    # Append num_months with mo
    num_months = f'{num_months}mo'

    # Print the number of revisions and the number of days
    print(f'Number of revisions for {csv_name}: {num_revs}')
    print(f'Number of months for {csv_name}: {num_months}')

    # Transform the num_revs dict into a list of numbers
    status_numbers = ','.join(
        [str(num_revs[status]) for status in ['OK', 'SomeTestFailed', 'TimedOut', 'compileError']])

    # Append the sum of the numbers to the end of the list apart from compileError
    status_numbers += f',{sum([num_revs[status] for status in ["OK", "SomeTestFailed", "TimedOut"]])}'

    # Construct a CSV row with format csv_name, status numbers, num_months
    csv_row = f'{csv_name},{status_numbers},{num_months}'

    return csv_row


def export_eloc_tloc(data, csv_name):
    # Export stats like ELOC and TLOC and language

    cleaned_data = utils.clean_data(data)

    # Get eloc, tloc, and language
    eloc_data, tloc_data = utils.get_columns(cleaned_data, ['eloc', 'testsize'])

    lang_map = {
        'Binutils': ('C', 'DejaGNU'),
        'Git': ('C', 'C/Perl'),
        'Lighttpd2': ('C', 'Python'),
        'Memcached': ('C', 'C/Perl'),
        'Redis': ('C', 'Tcl'),
        'ZeroMQ': ('C++', 'C++'),
        'Apr': ('C', 'C'),
        'Curl': ('C', 'Perl/Python'),
        'Vim': ('C', 'Vim Script'),
    }

    # Convert all the map keys to lowercase
    lang_map = {k.lower(): v for k, v in lang_map.items()}

    # Get the language (first is code language, second is test language) finding if csv_name contains part of the key in lang_map
    try:
        lang = [lang_map[key][0] for key in lang_map if key in csv_name.lower()][0]
        test_lang = [lang_map[key][1] for key in lang_map if key in csv_name.lower()][0]
    except IndexError:
        print(f'Could not find language for {csv_name}')
        return None

    # Get the eloc and tloc - from the last row
    eloc = eloc_data[-1]
    tloc = tloc_data[-1]

    # Construct a CSV row with format csv_name, lang, eloc, test_lang, tloc
    csv_row = f'{csv_name},{lang},{eloc},{test_lang},{tloc}'

    return csv_row


def export_lines_hunks_files(data, csv_name):
    # Export stats like lines, hunks, and files

    cleaned_data = utils.clean_data(data)

    # Get the lines, hunks, and files
    cov_lines, not_cov_lines, hunks, files = utils.get_columns(cleaned_data,
                                                               ['covlines', 'notcovlines', 'ehunks3', 'echanged_files'])

    # # Get the differences between consecutive elocs
    # eloc_diffs = [abs(eloc[i] - eloc[i - 1]) for i in range(1, len(eloc))]
    #
    # # Set the first eloc_diff to 0
    # eloc_diffs = [0] + eloc_diffs

    # sum the covlines and notcovlines to get the total lines of code
    lines = [cov_lines[i] + not_cov_lines[i] for i in range(len(cov_lines))]

    # # Limit to the first 250 revisions
    # lines = lines[:250]
    # hunks = hunks[:250]
    # files = files[:250]

    # Find indices of rows where echanged_files is not 0
    nonzero_indices = [i for i in range(len(files)) if files[i] != 0]

    # Filter lines and hunks to only include nonzero indices
    lines = [lines[i] for i in nonzero_indices]
    hunks = [hunks[i] for i in nonzero_indices]
    files = [files[i] for i in nonzero_indices]

    # Get the median of the lines, hunks, and files
    lines = int(statistics.median(lines))
    hunks = int(statistics.median(hunks))
    files = int(statistics.median(files))

    # # Get the mean of the lines, hunks, and files
    # lines = int(statistics.mean(lines))
    # hunks = int(statistics.mean(hunks))
    # files = int(statistics.mean(files))

    # Construct a CSV row with format csv_name, lines, hunks, files
    csv_row = f'{csv_name},{lines},{hunks},{files}'

    return csv_row


def export_bucketed_patch_coverage(data, csv_name):
    # Clean the data
    cleaned_data = utils.clean_data(data)

    # Get the coverage data, eloc and echanged_files
    eloc_data, patch_coverage, coveredlines, notcoveredlines = utils.get_columns(cleaned_data, ['eloc', 'patchcoverage', 'covlines', 'notcovlines'])

    eloc_diffs = [coveredlines[i] + notcoveredlines[i] for i in range(len(coveredlines))]

    peloc = 0
    nonzero_indices = []
    for i in range(len(eloc_data)):
        if eloc_data[i] > 0:
            if eloc_data[i] != peloc or coveredlines[i] > 0 or notcoveredlines[i] > 0:
                nonzero_indices.append(i)
            peloc = eloc_data[i]

    eloc_diffs = [eloc_diffs[i] for i in nonzero_indices]
    patch_coverage = [patch_coverage[i] for i in nonzero_indices]

    # bucket the coverage percentages into 3 buckets (<= 10, 11-100, > 100) in terms of eloc
    bucketed_cov_perc_data = [0, 0, 0]
    totals = [0, 0, 0]
    for i in range(len(eloc_diffs)):
        if eloc_diffs[i] <= 10:
            bucketed_cov_perc_data[0] += 1
            totals[0] += patch_coverage[i]
        elif eloc_diffs[i] <= 100:
            bucketed_cov_perc_data[1] += 1
            totals[1] += patch_coverage[i]
        else:
            bucketed_cov_perc_data[2] += 1
            totals[2] += patch_coverage[i]

    # Get the average coverage percentages
    bucketed_cov_perc_data_av = [totals[i] / bucketed_cov_perc_data[i] for i in range(len(bucketed_cov_perc_data))]

    # format bucketed_cov_perc_data_av to 1dp
    bucketed_cov_perc_data_av = [round(bucketed_cov_perc_data_av[i], 1) for i in range(len(bucketed_cov_perc_data_av))]

    # End all bucketed_cov_perc_data_av with a %
    bucketed_cov_perc_data_av = [str(bucketed_cov_perc_data_av[i]) + '%' for i in range(len(bucketed_cov_perc_data_av))]

    # Construct a CSV row with format csv_name, <= 10, <=10 av, 11-100, 11-100 av, > 100, > 100 av
    csv_row = f'{csv_name},{bucketed_cov_perc_data[0]},{bucketed_cov_perc_data_av[0]},{bucketed_cov_perc_data[1]},{bucketed_cov_perc_data_av[1]},{bucketed_cov_perc_data[2]},{bucketed_cov_perc_data_av[2]}'

    return csv_row


def write_stats(paths, csv_names):
    write_multiple_csv(export_number_revs, paths, csv_names, ['App', 'OK', 'TF', 'TO', 'CF', 'TotalWorking', 'Time'],
                       'num_revs')
    write_multiple_csv(export_eloc_tloc, paths, csv_names, ['App', 'Lang', 'ELOC', 'Lang', 'TLOC'], 'eloc_tloc')
    write_multiple_csv(export_lines_hunks_files, paths, csv_names, ['App', 'Lines', 'Hunks', 'Files'],
                       'lines_hunks_files')
    write_multiple_csv(export_bucketed_patch_coverage, paths, csv_names,
                       ['App', '<= 10 NP', '<= 10 C', '11-100 NP', '11-100 C', '> 100 NP', '> 100 C'],
                       'bucketed_patch_coverage')


def write_multiple_csv(func, paths, csv_names, header, name):
    # Run a function on multiple CSV files
    rows = []
    for i in range(len(csv_names)):
        csv_data = utils.extract_data(f'{paths[i]}', csv_names[i])
        if csv_data is None:
            continue
        res = func(csv_data, csv_names[i])
        if res is not None:
            rows.append(res)

    # Convert header to a CSV row
    header = ','.join(header)

    write_csv(f'stats/{name}.csv', header, rows)

    # Print wrote to file
    print(f'Wrote to stats/{name}.csv')


def write_csv(csv_name, header, rows):
    # Write the rows to the csv
    with open(csv_name, 'w') as f:
        # Write the header
        f.write(header + '\n')

        # Write the rows
        for row in rows:
            f.write(row + '\n')

    return


if __name__ == '__main__':
    import os
    import argparse
    import glob

    # argparse the location of the input file (e.g. remotedata/apr/Apr.csv)
    parser = argparse.ArgumentParser()
    # argparse for either an input file or a directory
    parser.add_argument('input', help='The input file or directory to process')
    # add a directory option so if --dir is present, the input is a directory, otherwise it is a file
    parser.add_argument('--dir', action='store_true',
                        help='The input is a directory (dir/repo1/*.csv, dir/repo2/*.csv)')

    args = parser.parse_args()

    # Make a stats directory if it doesn't exist
    if not os.path.isdir('stats'):
        os.mkdir('stats')

    if args.dir:
        # Make sure the input is a directory
        if not os.path.isdir(args.input):
            raise NotADirectoryError(f'{args.input} is not a directory')

        # Get the names of the CSV files (basenames)
        paths = glob.glob(f'{args.input}/*/*.csv')

        # Add to paths a level up
        if len(paths) == 0:
            paths += glob.glob(f'{args.input}/*.csv')

        # TODO: remove when data fixed
        # Remove the following CSV files from the list since they are either not complete or lack fields
        excluded_paths = ['remotedata/binutils-gdb/BinutilsGdb_gaps.csv', 'remotedata/binutils-gdb/BinutilsGdb_all.csv',
                          'remotedata/binutils/Binutils.csv']

        # Make sure we have at least one CSV file
        if len(paths) == 0:
            raise FileNotFoundError(f'No CSV files found in {args.input}')

        paths = [x for x in paths if x not in excluded_paths]

        # Make sure we have at least one valid CSV file
        if len(paths) == 0:
            raise FileNotFoundError(f'No non-excepted CSV files found in {args.input}')

        csv_names = [os.path.basename(x) for x in paths]

        # Remove the .csv extension
        csv_names = [x[:-4] for x in csv_names]

        csv_paths = sorted(zip(csv_names, paths))
        csv_names, paths = zip(*csv_paths)
        csv_names = list(csv_names)
        paths = list(paths)

        print(f'Paths: {paths}')
        # Print the names of the CSV files
        print(f'CSV names: {csv_names}')
        print("=====================================================")

        # Stats for number of revs
        write_stats(paths, csv_names)

    else:
        # Make sure we have a file not a directory and that it is a CSV, throw a nice error otherwise
        if os.path.isdir(args.input):
            raise IsADirectoryError(
                f'Input {args.input} is a directory (single input should be a file, try using --dir)')
        if not os.path.isfile(args.input):
            raise FileNotFoundError(f'Input {args.input} is not a file')
        if not args.input.endswith('.csv'):
            raise TypeError(f'File {args.input} is not a CSV file')

        # Get the name of the CSV file (basename)
        csv_name = os.path.basename(args.input)

        # Remove the .csv extension
        csv_name = csv_name[:-4]

        # Stats for number of revs
        write_multiple_csv(export_number_revs, [args.input], [csv_name], ['csv_name', 'num_revs', 'num_days'],
                           'num_revs')

    print("All done!")
