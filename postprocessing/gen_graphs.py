# Replace as necessary
file_header_raw = "rev,#eloc,coverage,testsize,author,#addedlines,#covlines,#notcovlines,patchcoverage,#covlinesprevpatches*,#covlinesprevpatches*,#covlinesprevpatches*,#covlinesprevpatches*,#covlinesprevpatches*,#covlinesprevpatches*,#covlinesprevpatches*,#covlinesprevpatches*,#covlinesprevpatches*,#covlinesprevpatches*,time,exit,hunks,ehunks,changed_files,echanged_files,changed_test_files,hunks3,ehunks3,merge,#br,#brcov"

# Remove any # or *s from the file_header after splitting by string
file_header_list = [x.replace('#', '').replace('*', '') for x in file_header_raw.split(',')]


def plot_eloc(data, csv_name, save=True, date=False):
    # Clean the data to ignore rows with exits "EmptyCommit", "NoCoverage" or "compileError"
    data = [x for x in data if x[file_header_list.index('exit')] not in ['EmptyCommit', 'NoCoverage', 'compileError']]

    # Get the eloc data from data
    eloc_data = [x[file_header_list.index('eloc')] for x in data]
    dates = [x[file_header_list.index('time')] for x in data]

    # Make sure eloc_data is a list of ints
    eloc_data = [int(x) for x in eloc_data]

    # Convert the unix timestamps to datetime objects
    dates = [datetime.datetime.fromtimestamp(int(x)) for x in dates]

    # Plot the eloc data against the dates as small dots
    if date:
        plt.plot(dates, eloc_data, '+', markersize=5)
    else:
        plt.plot(eloc_data, '+', markersize=5)
        plt.xlabel('Revision')
    # Label the axes, do not show xticks
    plt.ylabel('ELOC')
    # Title the plot
    plt.title(f'ELOC over time for {csv_name}')

    # Use locator_params to make the y axis have 10 ticks
    plt.locator_params(axis='y', nbins=10)
    plt.xticks(rotation=45)

    # Save the plot
    if save:
        plt.savefig(f'postprocessing/graphs/{csv_name}-eloc.png', bbox_inches='tight')

    # Clear the plot so that the next plot can be made
    plt.clf()


def plot_tloc(data, csv_name, save=True, date=False):
    # Clean the data to ignore rows with exits "EmptyCommit", "NoCoverage" or "compileError"
    data = [x for x in data if x[file_header_list.index('exit')] not in ['EmptyCommit', 'NoCoverage', 'compileError']]

    # Get the eloc data from data
    tloc_data = [x[file_header_list.index('testsize')] for x in data]
    dates = [x[file_header_list.index('time')] for x in data]

    # Make sure eloc_data is a list of ints
    tloc_data = [int(x) for x in tloc_data]

    # Convert the unix timestamps to datetime objects
    dates = [datetime.datetime.fromtimestamp(int(x)) for x in dates]

    # Plot the eloc data against the dates as small dots
    if date:
        plt.plot(dates, tloc_data, '+', markersize=5, color='red')
    else:
        plt.plot(tloc_data, '+', markersize=5, color='red')
        plt.xlabel('Revision')
    # Label the axes, do not show xticks
    plt.ylabel('TLOC')
    # Title the plot
    plt.title(f'Test LOC over time for {csv_name}')

    # Use locator_params to make the y axis have 10 ticks
    plt.locator_params(axis='y', nbins=10)
    plt.xticks(rotation=45)

    # Save the plot
    if save:
        plt.savefig(f'postprocessing/graphs/{csv_name}-tloc.png', bbox_inches='tight')

    # Clear the plot so that the next plot can be made
    plt.clf()


def plot_evolution_of_eloc_and_tloc(data, csv_name, save=True):
    # Clean the data to ignore rows with exits "EmptyCommit", "NoCoverage" or "compileError"
    data = [x for x in data if x[file_header_list.index('exit')] not in ['EmptyCommit', 'NoCoverage', 'compileError']]

    # Get the eloc data from data
    eloc_data = [x[file_header_list.index('eloc')] for x in data]
    tloc_data = [x[file_header_list.index('testsize')] for x in data]
    dates = [x[file_header_list.index('time')] for x in data]

    # Make sure eloc_data is a list of ints
    eloc_data = [int(x) for x in eloc_data]
    tloc_data = [int(x) for x in tloc_data]

    # Convert the unix timestamps to datetime objects
    dates = [datetime.datetime.fromtimestamp(int(x)) for x in dates]

    # for each revision, increment a counter if the eloc is different from the previous revision
    # for each revision increment another counter if the tloc is different from the previous revision
    # plot the two counters against the dates
    eloc_counter = 0
    tloc_counter = 0
    eloc_counter_list = []
    tloc_counter_list = []
    for i in range(len(eloc_data)):
        if eloc_data[i] != eloc_data[i - 1]:
            eloc_counter += 1
        if tloc_data[i] != tloc_data[i - 1]:
            tloc_counter += 1
        eloc_counter_list.append(eloc_counter)
        tloc_counter_list.append(tloc_counter)

    # Plot the eloc data against the dates as a line
    plt.plot(eloc_counter_list, color='blue')
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
        plt.savefig(f'postprocessing/graphs/{csv_name}-evolution.png', bbox_inches='tight')

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

        # Split the lines by comma
        lines = [line.split(',') for line in lines]

    # Perform a sanity check on the data, that the timestamps are in order (low to high)
    dates = [line[file_header_list.index('time')] for line in lines]

    # Make sure the dates are in order
    assert dates == sorted(dates)

    return lines


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

    data = extract_data(args.input_file)

    plot_eloc(data, csv_name, date=args.date)
    plot_tloc(data, csv_name, date=args.date)
    plot_evolution_of_eloc_and_tloc(data, csv_name)
