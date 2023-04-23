# Replace as necessary
file_header_raw = "rev,#eloc,coverage,testsize,author,#addedlines,#covlines,#notcovlines,patchcoverage,#covlinesprevpatches*,#covlinesprevpatches*,#covlinesprevpatches*,#covlinesprevpatches*,#covlinesprevpatches*,#covlinesprevpatches*,#covlinesprevpatches*,#covlinesprevpatches*,#covlinesprevpatches*,#covlinesprevpatches*,time,exit,hunks,ehunks,changed_files,echanged_files,changed_test_files,hunks3,ehunks3,merge,#br,#brcov"

# Remove any # or *s from the file_header after splitting by string
file_header_list = [x.replace('#', '').replace('*', '') for x in file_header_raw.split(',')]


def plot_eloc(data, csv_name, save=True, date=False):
    # Clean the data to ignore rows with exits "EmptyCommit", "NoCoverage" or "compileError"
    data = [x for x in data if x[file_header_list.index('exit')] not in ['EmptyCommit', 'NoCoverage', 'compileError']]

    # Get the eloc data from data
    eloc_data = [int(x[file_header_list.index('eloc')]) for x in data]
    dates = [x[file_header_list.index('time')] for x in data]

    # Convert the unix timestamps to datetime objects
    dates = [datetime.datetime.fromtimestamp(int(x)) for x in dates]

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
        plt.savefig(f'postprocessing/graphs/{csv_name}/{csv_name}-eloc{"-date" if date else ""}.png', bbox_inches='tight')

    # Clear the plot so that the next plot can be made
    plt.clf()


def plot_tloc(data, csv_name, save=True, date=False):
    # Clean the data to ignore rows with exits "EmptyCommit", "NoCoverage" or "compileError"
    data = [x for x in data if x[file_header_list.index('exit')] not in ['EmptyCommit', 'NoCoverage', 'compileError']]

    # Get the eloc data from data
    tloc_data = [int(x[file_header_list.index('testsize')]) for x in data]
    dates = [x[file_header_list.index('time')] for x in data]

    # Convert the unix timestamps to datetime objects
    dates = [datetime.datetime.fromtimestamp(int(x)) for x in dates]

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
        plt.savefig(f'postprocessing/graphs/{csv_name}/{csv_name}-tloc{"-date" if date else ""}.png', bbox_inches='tight')

    # Clear the plot so that the next plot can be made
    plt.clf()


def plot_evolution_of_eloc_and_tloc(data, csv_name, save=True, graph_mode="zeroone"):
    # Clean the data to ignore rows with exits "EmptyCommit", "NoCoverage" or "compileError"
    data = [x for x in data if x[file_header_list.index('exit')] not in ['EmptyCommit', 'NoCoverage', 'compileError']]

    # Get the eloc data from data
    eloc_data = [int(x[file_header_list.index('eloc')]) for x in data]
    tloc_data = [int(x[file_header_list.index('testsize')]) for x in data]
    dates = [x[file_header_list.index('time')] for x in data]

    # Convert the unix timestamps to datetime objects
    dates = [datetime.datetime.fromtimestamp(int(x)) for x in dates]

    eloc_counter = 0
    tloc_counter = 0
    eloc_counter_list = []
    tloc_counter_list = []
    if graph_mode == "standard":
        for i in range(len(eloc_data)):
            if eloc_data[i] > 0:
                eloc_counter_list.append(eloc_data[i])
                tloc_counter_list.append(tloc_data[i])
    elif graph_mode == "zeroone": #zero-one technique, displayed in covrig paper
        # effectively: for each revision, increment a counter if the eloc is different from the previous revision
        # for each revision increment another counter if the tloc is different from the previous revision
        covlines_data = [int(x[file_header_list.index('covlines')]) for x in data]
        notcovlines_data = [int(x[file_header_list.index('notcovlines')]) for x in data]
        changed_test_files_data = [int(x[file_header_list.index('changed_test_files')]) for x in data]
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
    data = [x for x in data if x[file_header_list.index('exit')] not in ['EmptyCommit', 'NoCoverage', 'compileError']]

    # Get the coverage data from data
    eloc_data = [int(x[file_header_list.index('eloc')]) for x in data]
    coverage_data = [int(x[file_header_list.index('coverage')]) for x in data]
    branch_data = [int(x[file_header_list.index('br')]) for x in data]
    branch_coverage_data = [int(x[file_header_list.index('brcov')]) for x in data]
    dates = [x[file_header_list.index('time')] for x in data]

    # Convert the unix timestamps to datetime objects
    dates = [datetime.datetime.fromtimestamp(int(x)) for x in dates]

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
    data = [x for x in data if x[file_header_list.index('exit')] not in ['EmptyCommit', 'NoCoverage', 'compileError']]

    # Get the eloc data from data
    eloc_data = [int(x[file_header_list.index('eloc')]) for x in data]
    dates = [x[file_header_list.index('time')] for x in data]

    # Convert the unix timestamps to datetime objects
    dates = [datetime.datetime.fromtimestamp(int(x)) for x in dates]

    # Get covered_lines and not_covered_lines data from data
    covered_lines_data = [int(x[file_header_list.index('covlines')]) for x in data]
    not_covered_lines_data = [int(x[file_header_list.index('notcovlines')]) for x in data]

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

    print("=====================================================")
    print(f'Finished plotting {csv_name}. You can find the plots in postprocessing/graphs/{csv_name}')
