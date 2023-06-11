# # Globals that tell the script the layout of the csv files
# from matplotlib import pyplot as plt
import internal.csv_utils as utils
import statistics


def export_number_revs(data, csv_name, no_compile_fail=False):
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

    set_to_analyze = ['OK', 'SomeTestFailed', 'TimedOut', 'compileError']
    if no_compile_fail:
        set_to_analyze.remove('compileError')

    # Transform the num_revs dict into a list of numbers
    status_numbers = ','.join(
        [str(num_revs[status]) for status in set_to_analyze])

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
    csv_row = f'{csv_name},{lang},"{eloc:,}",{test_lang},"{tloc:,}"'

    return csv_row


def export_delta_eloc_tloc(data, csv_name):
    cleaned_data = utils.clean_data(data)

    # Get eloc, tloc, and language
    eloc_data, tloc_data = utils.get_columns(cleaned_data, ['eloc', 'testsize'])

    # Get the last eloc and tloc
    eloc = eloc_data[-1]
    tloc = tloc_data[-1]

    # Get the first eloc and tloc
    first_eloc = eloc_data[0]
    first_tloc = tloc_data[0]

    # Calculate the delta eloc and tloc
    delta_eloc = eloc - first_eloc
    delta_tloc = tloc - first_tloc

    # Calculate the delta eloc and tloc as a percentage of the first eloc and tloc
    delta_eloc_percent = delta_eloc / first_eloc * 100
    delta_tloc_percent = delta_tloc / first_tloc * 100

    # Construct a CSV row with format csv_name, final eloc, delta eloc, final tloc, delta tloc
    # csv_row = f'{csv_name},"{eloc:,}","{delta_eloc:,}","{tloc:,}","{delta_tloc:,}"'

    # Construct a CSV row with format csv_name, delta eloc, delta eloc percent, delta tloc, delta tloc percent
    csv_row = f'{csv_name},"{delta_eloc:,}",+{delta_eloc_percent:.1f}%,"{delta_tloc:,}",+{delta_tloc_percent:.1f}%'

    return csv_row


def export_code_coverage(data, csv_name):
    # Export the final percentage code coverage

    cleaned_data = utils.clean_data(data)

    # Get the eloc and coverage
    eloc_data, coverage_data, covlines, notcovlines, patch_coverage = utils.get_columns(cleaned_data, ['eloc', 'coverage', 'covlines', 'notcovlines', 'patchcoverage'])

    # Calculate the percentage code coverage which is the last coverage divided by the last eloc multiplied by 100
    percent_coverage = coverage_data[-1] / eloc_data[-1] * 100

    # Get all indices where covlines + notcovlines is not 0
    nonzero_indices = [i for i in range(len(covlines)) if covlines[i] + notcovlines[i] != 0]
    patch_coverage = [patch_coverage[i] for i in nonzero_indices]

    # Calculate the average patch coverage
    avg_patch_coverage = sum(patch_coverage) / len(patch_coverage)

    # Construct a CSV row with format csv_name, percent coverage
    csv_row = f'{csv_name},{percent_coverage:.1f}%,{avg_patch_coverage:.1f}%'

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

    # Find indices of rows where either of cov_lines and not_cov_lines are nonzero
    # (can do covlines + notcovlines > 0 since they are always positive)
    nonzero_indices = [i for i in range(len(lines)) if cov_lines[i] + not_cov_lines[i] > 0]

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
    eloc_data, coveredlines, notcoveredlines = utils.get_columns(cleaned_data, ['eloc', 'covlines', 'notcovlines'])

    eloc_diffs = [coveredlines[i] + notcoveredlines[i] for i in range(len(coveredlines))]

    nonzero_indices = []
    for i in range(len(eloc_data)):
        if eloc_data[i] > 0:
            if coveredlines[i] + notcoveredlines[i] > 0:
                nonzero_indices.append(i)

    eloc_diffs = [eloc_diffs[i] for i in nonzero_indices]
    coveredlines = [coveredlines[i] for i in nonzero_indices]

    bins = [10, 100, 1000, float('inf')]

    bucketed_cov_perc_data = [0] * len(bins)
    total_covered = [0] * len(bins)
    total_total = [0] * len(bins)

    for i in range(len(eloc_diffs)):
        for j in range(len(bins)):
            if eloc_diffs[i] <= bins[j]:
                bucketed_cov_perc_data[j] += 1
                total_covered[j] += coveredlines[i]
                total_total[j] += eloc_diffs[i]
                break

    # Get the average coverage percentages
    bucketed_cov_perc_data_av = [total_covered[i] * 100 / total_total[i] if total_total[i] != 0 else 0 for i in range(len(total_covered))]

    # Also replace any 0s in bucketed_cov_perc_data with -
    csv_data = [csv_name] + [f'{data},{av:.1f}%' if av != 0 else f'{data},-' for data, av in
                             zip(bucketed_cov_perc_data, bucketed_cov_perc_data_av)]
    csv_row = ','.join(csv_data)

    return csv_row


def export_non_det_revisions(data, csv_name):
    # Clean the data (not removing all OK rows since some repos return OK but have different return values under the
    # hood which make for some interesting results)
    cleaned_data = utils.clean_data(data, omit=['EmptyCommit', 'NoCoverage', 'compileError', 'TimedOut'])

    # Get the commit hash, repeats, and non_det columns
    commit_hash, repeats, non_det = utils.get_columns(cleaned_data, ['rev', 'repeats', 'non_det'])

    # Get the indices of the non_det revisions
    non_det_indices = [i for i in range(len(non_det)) if non_det[i] == 'True']

    # Get the commit hashes of the non_det revisions
    non_det_commit_hashes = [commit_hash[i] for i in non_det_indices]

    # Get the number of repeats of the non_det revisions
    non_det_repeats = [repeats[i] for i in non_det_indices][0]

    # Get the number of non_det revisions
    num_non_det_revs = len(non_det_commit_hashes)

    # Get the number of non_det revisions as a percentage of the total number of revisions
    num_non_det_revs_perc = num_non_det_revs / len(commit_hash) * 100

    # Construct a csv row with the format csv_name, num_non_det_revs, num_not_det_revs_perc, non_det_repeats, non_det_commit_hashes*
    csv_row = f'{csv_name},{num_non_det_revs},{num_non_det_revs_perc:.1f},{non_det_repeats},\"[{",".join(non_det_commit_hashes)}]\"'

    return csv_row


def export_coverage_delta(data, csv_name):
    # Clean the data of all apart from OK
    cleaned_data = utils.clean_data(data,
                                    omit=['EmptyCommit', 'NoCoverage', 'compileError', 'TimedOut', 'SomeTestFailed'])

    # Get the coverage data and eloc
    eloc_data, coverage = utils.get_columns(cleaned_data, ['eloc', 'coverage'])

    # Calculate the coverage at the start and end of the project
    start_coverage = coverage[0] / eloc_data[0] * 100
    end_coverage = coverage[-1] / eloc_data[-1] * 100

    # Calculate the delta in coverage
    delta_coverage = end_coverage - start_coverage

    # Calculate the percentage delta in coverage
    delta_coverage_perc = delta_coverage / start_coverage * 100

    # If delta_coverage and delta_coverage_perc are positive, add a + to the start of the string

    # Construct a csv row with the format csv_name, start_coverage, end_coverage, delta_coverage, delta_coverage_perc
    csv_row = f'{csv_name},{start_coverage:.1f},{end_coverage:.1f},{delta_coverage_perc:+.1f}%'

    return csv_row


def write_stats(paths, csv_names, limit=None):
    write_multiple_csv(export_number_revs, paths, csv_names, ['App', 'OK', 'TF', 'TO', 'CF', 'Total Working', 'Time'],
                       'num_revs_all', limit=limit, no_filter=True)
    write_multiple_csv(export_number_revs, paths, csv_names, ['App', 'OK', 'TF', 'TO', 'MCT', 'Time'],
                       'num_revs_mct', limit=limit, no_compile_fail=True)
    write_multiple_csv(export_eloc_tloc, paths, csv_names, ['App', 'Lang.', 'ELOC', 'Lang.', 'TLOC'], 'eloc_tloc',
                       limit=limit)
    write_multiple_csv(export_delta_eloc_tloc, paths, csv_names, ['App', 'ΔELOC', 'ΔELOC%', 'ΔTLOC', 'ΔTLOC%'],
                       'delta_eloc_tloc', limit=limit)
    write_multiple_csv(export_lines_hunks_files, paths, csv_names, ['App', 'Lines', 'Hunks', 'Files'],
                       'lines_hunks_files', limit=limit)
    write_multiple_csv(export_bucketed_patch_coverage, paths, csv_names,
                       ['App', '<= 10 NP', '<= 10 C', '11-100 NP', '11-100 C', '101-1000 NP', '101-1000 C', '> 1000 NP', '> 1000 C'],
                       'bucketed_patch_coverage', limit=limit)
    write_multiple_csv(export_code_coverage, paths, csv_names, ['App', 'Final Cov. %', 'Avg. Patch Cov. %'], 'code_coverage', limit=limit)
    write_multiple_csv(export_coverage_delta, paths, csv_names, ['App', 'Start Cov. %', 'End Cov. %', 'Cov. % Δ'],
                       'coverage_delta', limit=limit)

    paths, csv_names = utils.filter_to_non_det_supported(paths, csv_names)

    write_multiple_csv(export_non_det_revisions, paths, csv_names,
                       ['App', 'Nondet. Result', '% Total Working Flaky', 'Repeats', 'Nondet. Commits'], 'non_det_revs')


def write_multiple_csv(func, paths, csv_names, header, name, limit=None, no_filter=False, **kwargs):
    # Run a function on multiple CSV files
    rows = []
    for i in range(len(csv_names)):
        csv_data = utils.extract_data(f'{paths[i]}', csv_names[i])
        if csv_data is None:
            continue
        if not no_filter:
            # Filter the data to only include revisions that modify executable code or test files
            csv_data, _ = utils.filter_data_by_exec_test(csv_data)
        if limit is not None:
            csv_data = csv_data[-limit:]
        res = func(csv_data, csv_names[i], **kwargs)
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
    # add a limit option to limit the number of revisions to process
    parser.add_argument('--limit', type=int, help='The number of revisions to process')

    args = parser.parse_args()

    print(args.limit)

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

        included_paths = ['remotedata/apr/Apr_repeats.csv',
                          'remotedata/binutils-gdb/BinutilsGdb_repeats.csv',
                          'remotedata/curl/Curl_repeats.csv',
                          'remotedata/git/Git_repeats.csv',
                          'remotedata/lighttpd2/Lighttpd2_repeats.csv',
                          'remotedata/memcached/Memcached_repeats.csv',
                          'remotedata/redis/Redis_repeats.csv',
                          'remotedata/vim/Vim_repeats.csv',
                          'remotedata/zeromq/Zeromq_repeats.csv']

        # Get indices of all paths that contain the word 'diffcov'
        diffcov_indices = [i for i in range(len(paths)) if 'diffcov' in paths[i]]
        # Remove all paths that contain the word 'diffcov'
        paths = [paths[i] for i in range(len(paths)) if i not in diffcov_indices]

        # Make sure we have at least one CSV file
        if len(paths) == 0:
            raise FileNotFoundError(f'No CSV files found in {args.input}')

        paths = [x for x in paths if x in included_paths]

        # Make sure we have at least one valid CSV file
        if len(paths) == 0:
            raise FileNotFoundError(f'No non-excepted CSV files found in {args.input}')

        csv_names = [os.path.basename(x) for x in paths]

        # Remove the .csv extension
        csv_names = [x[:-4] for x in csv_names]

        # Trim CSV names
        csv_names = utils.reformat_csv_names(csv_names)

        csv_paths = sorted(zip(csv_names, paths))
        csv_names, paths = zip(*csv_paths)
        csv_names = list(csv_names)
        paths = list(paths)

        print(f'Paths: {paths}')
        # Print the names of the CSV files
        print(f'CSV names: {csv_names}')
        print("=====================================================")

        # Stats for number of revs
        write_stats(paths, csv_names, limit=args.limit)

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
        write_stats([args.input], [csv_name], limit=args.limit)

    print("All done!")
