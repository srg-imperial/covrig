# Globals that tell the script the layout of the csv files

# Replace as necessary
file_header_raw = "rev,#eloc,coverage,testsize,author,#addedlines,#covlines,#notcovlines,patchcoverage,#covlinesprevpatches*,#covlinesprevpatches*,#covlinesprevpatches*,#covlinesprevpatches*,#covlinesprevpatches*,#covlinesprevpatches*,#covlinesprevpatches*,#covlinesprevpatches*,#covlinesprevpatches*,#covlinesprevpatches*,time,exit,hunks,ehunks,changed_files,echanged_files,changed_test_files,hunks3,ehunks3,merge,#br,#brcov"

# Remove any # or *s from the file_header after splitting by string
file_header_list = [x.replace('#', '').replace('*', '') for x in file_header_raw.split(',')]

# Create a map to hold the type of each column
file_header_type = {
    'rev': int,
    'eloc': int,
    'coverage': float,
    'testsize': int,
    'author': str,
    'addedlines': int,
    'covlines': int,
    'notcovlines': int,
    'patchcoverage': float,
    'covlinesprevpatches': int,
    'time': int,
    'exit': str,
    'hunks': int,
    'ehunks': int,
    'changed_files': int,
    'echanged_files': int,
    'changed_test_files': int,
    'hunks3': int,
    'ehunks3': int,
    'merge': int,
    'br': int,
    'brcov': int
}


def plot_eloc(data, csv_name, save=True, date=False):
    # Clean the data to ignore rows with exits "EmptyCommit", "NoCoverage" or "compileError"
    cleaned_data = clean_data(data)

    # Use get_columns to get the eloc and time data from data
    eloc_data, dates = get_columns(cleaned_data, ['eloc', 'time'])

    # Plot the eloc data against the dates as small dots
    if date:
        plt.plot(dates, eloc_data, '+', markersize=5)
        plt.xticks(rotation=45)
    else:
        plt.plot(eloc_data, '+', markersize=5)
        plt.xlabel('Revision')
    # Label the axes, do not show xticks
    plt.ylabel('ELOC')
    # Title the plot
    plt.title(f'ELOC over time for {csv_name}')

    # Use locator_params to make the y axis have 10 ticks
    plt.locator_params(axis='y', nbins=10)

    # Save the plot
    if save:
        plt.savefig(f'postprocessing/graphs/{csv_name}/{csv_name}-eloc{"-date" if date else ""}.png',
                    bbox_inches='tight')

    # Clear the plot so that the next plot can be made
    plt.clf()


def plot_tloc(data, csv_name, save=True, date=False):
    # Clean the data to ignore rows with exits "EmptyCommit", "NoCoverage" or "compileError"
    cleaned_data = clean_data(data)

    # Get the tloc and time data from data
    tloc_data, dates = get_columns(cleaned_data, ['testsize', 'time'])

    # Plot the eloc data against the dates as small dots
    if date:
        plt.plot(dates, tloc_data, '+', markersize=5, color='red')
        plt.xticks(rotation=45)
    else:
        plt.plot(tloc_data, '+', markersize=5, color='red')
        plt.xlabel('Revision')
    # Label the axes, do not show xticks
    plt.ylabel('TLOC')
    # Title the plot
    plt.title(f'Test LOC over time for {csv_name}')

    # Use locator_params to make the y axis have 10 ticks
    plt.locator_params(axis='y', nbins=10)

    # Save the plot
    if save:
        plt.savefig(f'postprocessing/graphs/{csv_name}/{csv_name}-tloc{"-date" if date else ""}.png',
                    bbox_inches='tight')

    # Clear the plot so that the next plot can be made
    plt.clf()


def plot_evolution_of_eloc_and_tloc(data, csv_name, save=True, graph_mode="zeroone"):
    # Clean the data to ignore rows with exits "EmptyCommit", "NoCoverage" or "compileError"
    cleaned_data = clean_data(data)

    # Get the eloc_data, tloc_data and time data from data
    eloc_data, tloc_data, dates = get_columns(cleaned_data, ['eloc', 'testsize', 'time'])

    eloc_counter = 0
    tloc_counter = 0
    eloc_counter_list = []
    tloc_counter_list = []
    if graph_mode == "standard":
        for i in range(len(eloc_data)):
            if eloc_data[i] > 0:
                eloc_counter_list.append(eloc_data[i])
                tloc_counter_list.append(tloc_data[i])
    elif graph_mode == "zeroone":  # zero-one technique, displayed in covrig paper
        # effectively: for each revision, increment a counter if the eloc is different from the previous revision
        # for each revision increment another counter if the tloc is different from the previous revision
        covlines_data, notcovlines_data, changed_test_files_data = get_columns(cleaned_data, ['covlines', 'notcovlines',
                                                                                              'changed_test_files'])
        # Establish vars for the previous eloc and tloc
        peloc, ptloc = 0, 0
        for i in range(len(eloc_data)):
            if eloc_data[i] > 0:
                if eloc_data[i] != peloc or covlines_data[i] > 0 or notcovlines_data[i] > 0:
                    eloc_counter += 1
                if tloc_data[i] != ptloc or changed_test_files_data[i] > 0:
                    tloc_counter += 1
                eloc_counter_list.append(eloc_counter)
                tloc_counter_list.append(tloc_counter)
                peloc = eloc_data[i]
                ptloc = tloc_data[i]
    else:
        print("Invalid graph mode for eloc/tloc evolution graph")

    # Plot the eloc data against the dates as a line
    plt.plot(eloc_counter_list)
    # Plot the tloc data against the dates as a line (red dashed)
    plt.plot(tloc_counter_list, color='red', linestyle='dashed')

    # Give the plot a title
    plt.title(f'Co-evolution of executable and test code for {csv_name}')

    # Label the y axis as Revisions (i.e. the number of changes to the code (not the number of commits))
    plt.ylabel('Revisions')
    # Make the upper y axis limit as the maximum number of revisions rounded up to the nearest 50
    plt.ylim(bottom=0, top=math.ceil(max(eloc_counter_list + tloc_counter_list) / 50) * 50)
    # Draw a grid
    plt.grid()

    # Label the x axis as Commits (i.e. the number of commits)
    plt.xlabel('Commits')
    plt.xlim(left=0, right=len(dates))

    # Save the plot
    if save:
        plt.savefig(f'postprocessing/graphs/{csv_name}/{csv_name}-evolution.png', bbox_inches='tight')

    # Clear the plot so that the next plot can be made
    plt.clf()


def plot_coverage(data, csv_name, save=True, date=False):
    # Clean the data to ignore rows with exits "EmptyCommit", "NoCoverage" or "compileError"
    cleaned_data = clean_data(data)

    # Get the coverage data using eloc_data, coverage_data, branch_data, branch_coverage_data and dates
    eloc_data, coverage_data, branch_data, branch_coverage_data, dates = get_columns(cleaned_data,
                                                                                     ['eloc', 'coverage', 'br', 'brcov',
                                                                                      'time'])

    line_coverage = []
    br_coverage = []
    for i in range(len(coverage_data)):
        if eloc_data[i] > 0:
            if branch_data[i] > 0:
                line_coverage.append(coverage_data[i] * 100 / eloc_data[i])
                br_coverage.append(branch_coverage_data[i] * 100 / branch_data[i])
            else:
                line_coverage.append(coverage_data[i] * 100 / eloc_data[i])
                br_coverage.append(0)

    # Plot the eloc data against the dates as small dots
    if date:
        plt.plot(dates, line_coverage, '+', markersize=5)
        plt.plot(dates, br_coverage, 'x', markersize=5, color='red')
        plt.xticks(rotation=45)
    else:
        plt.plot(line_coverage, '+', markersize=5)
        plt.plot(br_coverage, 'x', markersize=5, color='red')
        plt.xlabel('Revision')

    # Set the y axis from 0 to 100
    plt.ylim(bottom=0, top=100)

    # Label the y axis as Coverage
    plt.ylabel('Coverage (%)')

    # Give the plot a title
    plt.title(f'Coverage for {csv_name}')

    # Print the legend
    plt.legend(['Line Coverage', 'Branch Coverage'])

    # Save the plot
    if save:
        plt.savefig(f'postprocessing/graphs/{csv_name}/{csv_name}-coverage{"-date" if date else ""}.png',
                    bbox_inches='tight')

    # Clear the plot so that the next plot can be made
    plt.clf()


def plot_churn(data, csv_name, save=True, date=False):
    # Clean the data to ignore rows with exits "EmptyCommit", "NoCoverage" or "compileError"
    cleaned_data = clean_data(data)

    # use the get_column function to get the data for eloc, covlines, notcovlines, time
    eloc_data, covered_lines_data, not_covered_lines_data, dates = get_columns(cleaned_data,
                                                                               ['eloc', 'covlines', 'notcovlines',
                                                                                'time'])

    # Calculate the churn for each revision
    churn_list = []
    peloc = 0
    for i in range(len(eloc_data)):
        if (covered_lines_data[i] > 0 or not_covered_lines_data[i] > 0) and peloc > 0:
            churn_list.append(2 * (covered_lines_data[i] + not_covered_lines_data[i]) - (eloc_data[i] - peloc))
        peloc = eloc_data[i]

    if date:
        plt.plot(dates, churn_list, '+', markersize=5)
        plt.xticks(rotation=45)
    else:
        plt.plot(churn_list, '+', markersize=5)
        plt.xlabel('Revision')

    # Label the y axis as Churn
    plt.ylabel('Churn')

    # Give the plot a title
    plt.title(f'Churn for {csv_name}')

    # Save the plot
    if save:
        plt.savefig(f'postprocessing/graphs/{csv_name}/{csv_name}-churn{"-date" if date else ""}.png',
                    bbox_inches='tight')

    # Clear the plot so that the next plot can be made
    plt.clf()


def plot_patch_coverage(data, csv_name, save=True, bucket_no=6):
    # Clean the data to ignore rows with exits "EmptyCommit", "NoCoverage" or "compileError"
    cleaned_data = clean_data(data)

    # Get the coverage data using eloc_data, coverage_data, branch_data, branch_coverage_data and dates
    covered_lines_data, not_covered_lines_data = get_columns(cleaned_data, ['covlines', 'notcovlines'])

    # Count the number of revisions that introduce executable lines
    total_revs_exec = 0
    for i in range(len(covered_lines_data)):
        if covered_lines_data[i] + not_covered_lines_data[i] > 0:
            total_revs_exec += 1

    # Establish buckets for the patch coverage between -1 and 1 and their names
    bucket_membership = []
    buckets = [0, 0.25, 0.5, 0.75, 1]

    # Bucket styles
    covrig_buckets = 4  # [0, 0.25], (0.25, 0.5], (0.5, 0.75], (0.75, 1]
    large_scale_buckets = 6  # 0, (0, 0.25], (0.25, 0.5], (0.5, 0.75], (0.75, 1), 1 (large scale study)

    bucket_names = ["0%", "(0%, 25%]", "(25%, 50%]", "(50%, 75%]", "(75%, 100%)", "100%"]
    if bucket_no == covrig_buckets:
        bucket_names = ["N/A", "[0%, 25%]", "(25%, 50%]", "(50%, 75%]", "(75%, 100%]", "N/A"]

    for i in range(len(covered_lines_data)):
        # Calculate the patch coverage
        patch_coverage = covered_lines_data[i] / (covered_lines_data[i] + not_covered_lines_data[i]) if \
        covered_lines_data[i] + not_covered_lines_data[i] > 0 else -1
        # Find the bucket that the patch coverage falls into
        bucket = 0
        if patch_coverage == -1:
            # i.e. no executable lines and therefore no patch coverage
            bucket = -1
        else:
            if bucket_no == covrig_buckets:
                # The standard quartile buckets (covrig)
                while patch_coverage > buckets[bucket]:
                    bucket += 1
                if bucket == 0:
                    # Merge any 0s into the first bucket
                    bucket = 1
            elif bucket_no == large_scale_buckets:
                # Introduce extra buckets for 0 and 1 patch coverage
                if patch_coverage == 0:
                    bucket = 0
                elif patch_coverage == 1:
                    bucket = 5
                else:
                    # Step through the buckets until the patch coverage is less than the bucket
                    while patch_coverage > buckets[bucket]:
                        bucket += 1
            else:
                print('Invalid bucket number for patch coverage')
                return
        bucket_membership.append(bucket)

    # Assert if we are in covrig mode we should not have any 0s or 5s in our bucket membership
    assert bucket_no != covrig_buckets or (0 not in bucket_membership and 5 not in bucket_membership)

    # Calculate the number of revisions in each bucket
    bucket_counts = [0] * large_scale_buckets
    for bucket in bucket_membership:
        if bucket != -1:
            bucket_counts[bucket] += 1

    # Calculate the percentage of revisions in each bucket using total_revs_exec
    bucket_percentages = [x * 100 / total_revs_exec for x in bucket_counts]

    # Assert we sum to roughly 100
    assert 99.9 < sum(bucket_percentages) < 100.1

    # Print out the bucket percentages to 5 decimal places
    # print(f"Patch coverage percentages for {csv_name}: {[round(x, 5) for x in bucket_percentages]}")

    fig = plt.figure(figsize=(11, 11))
    ax = fig.add_subplot(1, 1, 1)
    colours = ["#ad302e", "#de5434", "#e9923e", "#f8cc47", "#8bb954", "#428f4d"]
    if bucket_no == covrig_buckets:
        colours = ["#ffffff", "#bd2121", "#ffba0f", "#c9ff70", "#4d9b00", "#ffffff"]

    # Plot the data as a stacked vertical bar chart
    cumulative_total = 0
    idx = 0
    for bucket_p in bucket_percentages:
        ax.bar(0, bucket_p, bottom=cumulative_total, label=bucket_names[idx], width=0.5, color=colours[idx],
               edgecolor='black', zorder=3)
        cumulative_total += bucket_p
        idx += 1

    # Turn off ticks for the x axis
    plt.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)
    plt.xlim(-1, 1)

    # Label the y axis as Patch Coverage
    plt.ylabel('Frequency of Patch Coverage (binned)')
    plt.ylim(0, 100.0001)

    # Give the plot a title
    plt.title(f'Patch Coverage for {csv_name}')

    # Print the legend with the bucket names [0%, 25%], (25%, 50%], (50%, 75%], (75%, 100%]
    # or if we are in large scale mode (0%, 25%], (25%, 50%], (50%, 75%], (75%, 100%], 0%, 100%

    # Do plt.legend(bucket_names) but in reverse order
    handles, labels = ax.get_legend_handles_labels()
    plt.legend(handles[::-1], labels[::-1])

    # if we are in covrig mode, do not plot the 0% and 100% buckets
    if bucket_no == covrig_buckets:
        plt.legend(handles[::-1][1:5], labels[::-1][1:5])

    # Make it a dotted grid
    ax.grid(linestyle='dotted', zorder=0, axis='y')

    # Save the plot
    if save:
        plt.savefig(f'postprocessing/graphs/{csv_name}/{csv_name}-patch-coverage-{bucket_no}-buckets.png',
                    bbox_inches='tight')

    # Clear the plot so that the next plot can be made
    plt.clf()


def plot_patch_type(data, csv_name, save=True):
    # Clean the data
    cleaned_data = clean_data(data)

    # Get the columns we want - covered_lines, not_covered_lines, and changed_test_files
    covered_lines_data, not_covered_lines_data, changed_test_files_data = get_columns(cleaned_data,
                                                                                      ['covlines',
                                                                                       'notcovlines',
                                                                                       'changed_test_files'])

    patch_types = {
        'Code only': 0,
        'Code+Test': 0,
        'Test only': 0,
        'Other': 0,
    }

    revs = 0
    for i in range(len(changed_test_files_data)):
        # Calculate the patch type
        if (covered_lines_data[i] > 0 or not_covered_lines_data[i] > 0) and changed_test_files_data[i] == 0:
            patch_types['Code only'] += 1
        if covered_lines_data[i] == 0 and not_covered_lines_data[i] == 0 and changed_test_files_data[i] > 0:
            patch_types['Test only'] += 1
        if (covered_lines_data[i] > 0 or not_covered_lines_data[i] > 0) and changed_test_files_data[i] > 0:
            patch_types['Code+Test'] += 1
        revs += 1

    # "Other" patches are revs - #onlyExecutable - #onlyTest - #testAndExecutable
    patch_types['Other'] = revs - sum(patch_types.values())

    # Plot our data
    fig = plt.figure(figsize=(11, 11))
    ax = fig.add_subplot(1, 1, 1)
    patch_type_colours = ["#bd2121", "#bf3dff", "#6394ed", "#ededed"]

    # Plot the data as a stacked vertical bar chart
    cumulative_total = 0
    idx = 0
    for patch_type in patch_types:
        ax.bar(0, patch_types[patch_type], bottom=cumulative_total, label=patch_type, width=0.5,
               color=patch_type_colours[idx], edgecolor='black', zorder=3)
        cumulative_total += patch_types[patch_type]
        idx += 1

    # Turn off ticks for the x axis
    plt.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)
    plt.xlim(-1, 1)

    # Label the y axis as Number of Patches
    plt.ylabel('Number of Patches')

    # Give the plot a title
    plt.title(f'Patch Types for {csv_name}')

    # Print the legend with the patch type names
    handles, labels = ax.get_legend_handles_labels()
    plt.legend(handles[::-1], labels[::-1])

    # Make it a dotted grid
    ax.grid(linestyle='dotted', zorder=0, axis='y')

    # Save the plot
    if save:
        plt.savefig(f'postprocessing/graphs/{csv_name}/{csv_name}-patch-types.png', bbox_inches='tight')

    # Clear the plot so that the next plot can be made
    plt.clf()


def clean_data(data):
    return [x for x in data if x[file_header_list.index('exit')] not in ['EmptyCommit', 'NoCoverage', 'compileError']]


def get_columns(data, columns):
    # Get the data from the columns specified and convert to the correct type using file_header_type
    data_list = []
    for column in columns:
        # Get the data from the column
        column_data = [x[file_header_list.index(column)] for x in data]
        # Convert the data to the correct type (int, str, float)
        column_data = [file_header_type[column](x) for x in column_data]
        if column == 'time':
            column_data = [datetime.datetime.fromtimestamp(int(x)) for x in column_data]
        # Add the data to the list
        data_list.append(column_data)
    return data_list


def extract_data(input_file):
    # Take the input file CSV and extract to an internal representation of the data

    # Open the file
    with open(input_file, 'r') as f:
        # Read the file
        lines = f.readlines()

        # Remove the header
        lines = lines[1:]

        # Ignore any lines that begin with a # (i.e. comments)
        lines = [line for line in lines if not line.startswith('#')]

        # Split the lines by comma
        lines = [line.split(',') for line in lines]

    # Perform a sanity check on the data, that the timestamps are in order (low to high)
    dates = [line[file_header_list.index('time')] for line in lines]

    # Make sure the dates are in order
    dates_ok = date_check(dates)

    return lines


def date_check(dates):
    for i in range(len(dates) - 1):
        if dates[i] > dates[i + 1]:
            print(f'Warning: The dates are not in order, {dates[i]} is after {dates[i + 1]}')
            print(
                f'Maybe double check the git history using something like "git rev-list --reverse -n 3" on the offending commit to check this is intended.')
            return False
    return True


if __name__ == '__main__':
    # TODO: Add an option to specify whether our X axis is time or revision number
    import os
    import argparse
    import math
    import numpy as np
    import datetime
    import matplotlib.pyplot as plt

    # argparse the location of the input file (e.g. remotedata/apr/Apr.csv)
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file', type=str, help='Input file')
    # add a byDate option so if --date is present, the X axis is time, otherwise it is revision number
    parser.add_argument('--date', action='store_true', help='Plot by date')
    args = parser.parse_args()

    # Get the name of the CSV file (basename)
    csv_name = os.path.basename(args.input_file)
    # Remove the .csv extension
    csv_name = csv_name[:-4]

    # Make the directory /graphs if it doesn't exist
    if not os.path.exists('postprocessing/graphs'):
        os.makedirs('postprocessing/graphs')

    # Make the directory for the graphs if it doesn't exist
    if not os.path.exists(f'postprocessing/graphs/{csv_name}'):
        os.makedirs(f'postprocessing/graphs/{csv_name}')

    data = extract_data(args.input_file)

    plot_eloc(data, csv_name, date=args.date)
    plot_tloc(data, csv_name, date=args.date)
    plot_evolution_of_eloc_and_tloc(data, csv_name, graph_mode="zeroone")

    plot_coverage(data, csv_name, date=args.date)
    plot_churn(data, csv_name, date=args.date)

    plot_patch_coverage(data, csv_name, bucket_no=4)
    plot_patch_type(data, csv_name)

    print("=====================================================")
    print(f'Finished plotting {csv_name}. You can find the plots in postprocessing/graphs/{csv_name}')
