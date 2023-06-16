# Globals that tell the script the layout of the csv files
import datetime
import numpy as np
import statistics
import datetime as dt
from matplotlib import pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import matplotlib.dates as mdates
from copy import deepcopy
from textwrap import wrap

from matplotlib.ticker import MaxNLocator

# Config for the csv files' layout (edit as necessary)
import internal.csv_config as config
import internal.csv_utils as utils

# Remove any # or *s from the file_header after splitting by string
file_header_list = config.file_header_list

# Create a map to hold the type of each column
file_header_type = config.file_header_type

# Other globals
markersize = 3
output_location = 'postprocessing/graphs/'
SMALL_FIGSIZE = (5, 5)
MED_FIGSIZE = (8, 8)
DEFAULT_FIGSIZE = (11, 11)
EXPANDED_FIGSIZE = (15, 15)
date_warning_thrown = []

LEGACY_NUM_REVS = 250
# timestamps of first commits in jun2015 files (not necessarily first of 250 data), and last commits (which will be the last of 250 data)
commits_prev_compiling_range = {
    'Apr': (-1, -1),
    'Binutils': (1266228576, 1381776346),
    'Curl': (-1, -1),
    'Git': (1370985909, 1386887079),
    'Lighttpd': (1284310497, 1378821913),
    'Lighttpd2': (1284310497, 1378821913),
    'Memcached': (1234570260, 1358117990),
    'Redis': (1359375286, 1380183166),
    'Vim': (-1, -1),
    'Zeromq': (1324305818, 1381730754),
}

# Extracted from {csv_names[i]} starts at: <> portion of code in plot_metric_combined
commits_prev_operating_range = {
    'Apr': (-1, -1),
    'Binutils': (1289860245, 1381776346),
    'Curl': (-1, -1),
    'Git': (1372106937, 1386887079),
    'Lighttpd': (1284933555, 1378821913),
    'Lighttpd2': (1284933555, 1378821913),
    'Memcached': (1236258497, 1358117990),
    'Redis': (1362569886, 1380183166),
    'Vim': (-1, -1),
    'Zeromq': (1335763996, 1381730754),
}


def plot_eloc(data, csv_name, save=True, date=False, plot=None, savedir=None):
    if plot is None:
        plot = plt.subplots(figsize=SMALL_FIGSIZE)
    (fig, ax) = plot
    # Clean the data to ignore rows with exits "EmptyCommit", "NoCoverage" or "compileError"
    cleaned_data = utils.clean_data(data)

    # Use utils.get_columns to get the eloc and time data from data
    eloc_data, dates = utils.get_columns(cleaned_data, ['eloc', 'time'])

    # Plot the eloc data against the dates as small dots
    if date:
        ax.plot(dates, eloc_data, '+', markersize=markersize)
        ax.tick_params(axis='x', rotation=45)
        ax.set_xlim(dates[0], dates[-1])
        adjust_dates_on_xaxis(ax, dates)
    else:
        ax.plot(eloc_data, '+', markersize=markersize)
        ax.set_xlabel('Revision')
        ax.set_xlim(0, len(eloc_data))
    # Label the axes, do not show xticks
    ax.set_ylabel('ELOC')
    # ax.set_ylim(math.floor(min(eloc_data) / 500) * 500, math.ceil(max(eloc_data) / 500) * 500)
    # Title the plot
    ax.set_title(f'{csv_name}')

    # Use locator_params to make the y axis have 10 ticks
    ax.locator_params(axis='y', nbins=10)

    # If we can find the legacy date, let's plot it as a vertical line
    plot_vert_at_timestamp(ax, csv_name, date)

    # Save the plot
    if save:
        ax.set_title(f'ELOC over time for {csv_name}')
        fig.savefig(f'postprocessing/graphs/{savedir}/{csv_name}/{csv_name}-eloc{"-date" if date else ""}.png',
                    bbox_inches='tight')
        # Close the figure to save memory (if we're saving, we do not need to keep the figure in memory)
        plt.close(fig)


def plot_tloc(data, csv_name, save=True, date=False, plot=None, savedir=None):
    if plot is None:
        plot = plt.subplots(figsize=SMALL_FIGSIZE)
    (fig, ax) = plot
    # Clean the data to ignore rows with exits "EmptyCommit", "NoCoverage" or "compileError"
    cleaned_data = utils.clean_data(data)

    # Get the tloc and time data from data
    tloc_data, dates = utils.get_columns(cleaned_data, ['testsize', 'time'])

    # Plot the eloc data against the dates as small dots
    if date:
        ax.plot(dates, tloc_data, '+', markersize=markersize, color='red')
        ax.tick_params(axis='x', rotation=45)
        ax.set_xlim(left=dates[0], right=dates[-1])
        adjust_dates_on_xaxis(ax, dates)
    else:
        ax.plot(tloc_data, '+', markersize=markersize, color='red')
        ax.set_xlabel('Revision')
        ax.set_xlim(left=0, right=len(tloc_data))
    # Label the axes, do not show xticks
    ax.set_ylabel('TLOC')
    # ax.set_ylim(bottom=0, top=math.ceil(max(tloc_data) / 100) * 100)
    # Title the plot
    ax.set_title(f'{csv_name}')

    # Use locator_params to make the y axis have 10 ticks
    ax.locator_params(axis='y', nbins=10)

    # If we can find the legacy date, let's plot it as a vertical line
    plot_vert_at_timestamp(ax, csv_name, date)

    # Save the plot
    if save:
        ax.set_title(f'Test LOC over time for {csv_name}')
        fig.savefig(f'postprocessing/graphs/{savedir}/{csv_name}/{csv_name}-tloc{"-date" if date else ""}.png',
                    bbox_inches='tight')
        plt.close(fig)


def plot_evolution_of_eloc_and_tloc(data, csv_name, save=True, graph_mode="zeroone", date=False,
                                    plot=None, savedir=None):
    if plot is None:
        plot = plt.subplots(figsize=SMALL_FIGSIZE)
    (fig, ax) = plot
    # Clean the data to ignore rows with exits "EmptyCommit", "NoCoverage" or "compileError"
    cleaned_data = utils.clean_data(data)

    # Get the eloc_data, tloc_data and time data from data
    eloc_data, tloc_data, dates = utils.get_columns(cleaned_data, ['eloc', 'testsize', 'time'])

    eloc_counter = 0
    tloc_counter = 0
    eloc_counter_list = []
    tloc_counter_list = []
    idxs = []
    if graph_mode == "standard":
        for i in range(len(eloc_data)):
            if eloc_data[i] > 0:
                eloc_counter_list.append(eloc_data[i])
                tloc_counter_list.append(tloc_data[i])
                idxs.append(i)
    elif graph_mode == "zeroone":  # zero-one technique, displayed in covrig paper
        # effectively: for each revision, increment a counter if the eloc is different from the previous revision
        # for each revision increment another counter if the tloc is different from the previous revision
        covlines_data, notcovlines_data, changed_test_files_data = utils.get_columns(cleaned_data,
                                                                                     ['covlines', 'notcovlines',
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
                idxs.append(i)
    else:
        print("Invalid graph mode for eloc/tloc evolution graph")

    if date:
        corresponding_dates = [dates[i] for i in idxs]
        # Plot the eloc data against the dates as a line
        ax.plot(corresponding_dates, eloc_counter_list)
        # Plot the tloc data against the dates as a line (red dashed)
        ax.plot(corresponding_dates, tloc_counter_list, color='red', linestyle='dashed')
        ax.tick_params(axis='x', rotation=45)
        ax.set_xlim(left=dates[0], right=dates[-1])
        adjust_dates_on_xaxis(ax, corresponding_dates)
    else:
        # Plot the eloc data against the dates as a line
        ax.plot(eloc_counter_list)
        # Plot the tloc data against the dates as a line (red dashed)
        ax.plot(tloc_counter_list, color='red', linestyle='dashed')
        ax.set_xlim(left=0, right=len(dates))

    # Give the plot a title
    ax.set_title(f'{csv_name}')

    # Label the y axis as Revisions (i.e. the number of changes to the code (not the number of commits))
    ax.set_ylabel('Revisions')
    # Make the upper y axis limit as the maximum number of revisions rounded up to the nearest 50
    ax.set_ylim(bottom=0, top=math.ceil(max(eloc_counter_list + tloc_counter_list) / 50) * 50)

    # Label the x axis as Commits (i.e. the number of commits)
    ax.set_xlabel('Commits')

    ax.legend(['Code', 'Test'], loc='upper left')

    # If we can find the legacy date, let's plot it as a vertical line
    plot_vert_at_timestamp(ax, csv_name, date)

    # Save the plot
    if save:
        ax.set_title(f'Co-evolution of executable and test code for {csv_name}')
        fig.savefig(f'postprocessing/graphs/{savedir}/{csv_name}/{csv_name}-evolution{"-date" if date else ""}.png',
                    bbox_inches='tight')
        plt.close(fig)


def plot_coverage(data, csv_name, save=True, date=False, plot=None, savedir=None):
    local_multiple = True
    if plot is None:
        plot = plt.subplots(figsize=SMALL_FIGSIZE)
        local_multiple = False
    (fig, ax) = plot
    # Clean the data to ignore rows with exits "EmptyCommit", "NoCoverage" or "compileError"
    cleaned_data = utils.clean_data(data)

    # Get the coverage data using eloc_data, coverage_data, branch_data, branch_coverage_data and dates
    eloc_data, coverage_data, branch_data, branch_coverage_data, dates = utils.get_columns(cleaned_data,
                                                                                           ['eloc', 'coverage', 'br',
                                                                                            'brcov',
                                                                                            'time'])

    line_coverage = []
    br_coverage = []
    idxs = []
    for i in range(len(coverage_data)):
        if eloc_data[i] > 0:
            if branch_data[i] > 0:
                line_coverage.append(coverage_data[i] * 100 / eloc_data[i])
                br_coverage.append(branch_coverage_data[i] * 100 / branch_data[i])
            else:
                line_coverage.append(coverage_data[i] * 100 / eloc_data[i])
                br_coverage.append(0)
            idxs.append(i)

    # Plot the eloc data against the dates as small dots
    if date:
        corresponding_dates = [dates[i] for i in idxs]
        ax.plot(corresponding_dates, line_coverage, '+', markersize=markersize)
        ax.plot(corresponding_dates, br_coverage, 'x', markersize=markersize, color='red')
        ax.tick_params(axis='x', rotation=45)
        ax.set_xlim(left=dates[0], right=dates[-1])
        adjust_dates_on_xaxis(ax, corresponding_dates)
    else:
        ax.plot(line_coverage, '+', markersize=markersize)
        ax.plot(br_coverage, 'x', markersize=markersize, color='red')
        ax.set_xlabel('Revision')
        ax.set_xlim(left=0, right=len(dates))

    # Set the y axis from 0 to 100
    ax.set_ylim(bottom=0, top=100)

    # Label the y axis as Coverage
    ax.set_ylabel('Coverage (%)')

    # Give the plot a title
    ax.set_title(f'{csv_name}')

    # Print the legend
    if local_multiple:
        ax.legend(['Line Coverage', 'Branch Coverage'], prop={'size': 6}, loc='upper right')
    else:
        ax.legend(['Line Coverage', 'Branch Coverage'], prop={'size': 9}, loc='upper right')

    # If we can find the legacy date, let's plot it as a vertical line
    plot_vert_at_timestamp(ax, csv_name, date)

    # Save the plot
    if save:
        ax.set_title(f'Coverage for {csv_name}')
        fig.savefig(f'postprocessing/graphs/{savedir}/{csv_name}/{csv_name}-coverage{"-date" if date else ""}.png',
                    bbox_inches='tight')
        plt.close(fig)


def plot_churn(data, csv_name, save=True, date=False, plot=None, savedir=None):
    if plot is None:
        plot = plt.subplots(figsize=DEFAULT_FIGSIZE)
    (fig, ax) = plot
    # Clean the data to ignore rows with exits "EmptyCommit", "NoCoverage" or "compileError"
    cleaned_data = utils.clean_data(data)

    # use the get_column function to get the data for eloc, covlines, notcovlines, time
    eloc_data, covered_lines_data, not_covered_lines_data, dates = utils.get_columns(cleaned_data,
                                                                                     ['eloc', 'covlines', 'notcovlines',
                                                                                      'time'])

    # Calculate the churn for each revision
    churn_list = []
    idxs = []
    peloc = 0
    for i in range(len(eloc_data)):
        if (covered_lines_data[i] > 0 or not_covered_lines_data[i] > 0) and peloc > 0:
            churn_list.append(2 * (covered_lines_data[i] + not_covered_lines_data[i]) - (eloc_data[i] - peloc))
            idxs.append(i)
        peloc = eloc_data[i]

    if date:
        corresponding_dates = [dates[i] for i in idxs]
        ax.plot(corresponding_dates, churn_list, '+', markersize=markersize)
        ax.tick_params(axis='x', rotation=45)
        adjust_dates_on_xaxis(ax, corresponding_dates)
    else:
        ax.plot(churn_list, '+', markersize=markersize)
        ax.set_xlabel('Revision')

    # Label the y axis as Churn
    ax.set_ylabel('Churn')

    # Give the plot a title
    ax.set_title(f'{csv_name}')

    # If we can find the legacy date, let's plot it as a vertical line
    plot_vert_at_timestamp(ax, csv_name, date)

    # Save the plot
    if save:
        ax.set_title(f'Churn for {csv_name}')
        fig.savefig(f'postprocessing/graphs/{savedir}/{csv_name}/{csv_name}-churn{"-date" if date else ""}.png',
                    bbox_inches='tight')
        plt.close(fig)


def plot_patch_coverage(data, csv_name, save=True, bucket_no=6, plot=None, pos=0, multiple=False, savedir=None,
                        weighted=False):
    if plot is None:
        plot = plt.subplots(figsize=SMALL_FIGSIZE)
    (fig, ax) = plot
    # Clean the data to ignore rows with exits "EmptyCommit", "NoCoverage" or "compileError"
    cleaned_data = utils.clean_data(data)

    # Get the coverage data using eloc_data, coverage_data, branch_data, branch_coverage_data and dates
    eloc_data, cov_data, covered_lines_data, not_covered_lines_data, patchcoverage_data = utils.get_columns(
        cleaned_data, ['eloc', 'coverage', 'covlines', 'notcovlines', 'patchcoverage'])

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

    lines_bucket_membership = []

    for i in range(len(covered_lines_data)):
        # Calculate the patch coverage (this calc is equal to the patchcoverage column in the csv)
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
        num_lines_added_modified = covered_lines_data[i] + not_covered_lines_data[i] if \
            covered_lines_data[i] + not_covered_lines_data[i] > 0 else -1
        lines_bucket_membership.append(num_lines_added_modified)

    # Assert if we are in covrig mode we should not have any 0s or 5s in our bucket membership
    assert bucket_no != covrig_buckets or (0 not in bucket_membership and 5 not in bucket_membership)

    # Calculate the number of revisions in each bucket
    bucket_counts = [0] * large_scale_buckets
    line_counts = [0] * large_scale_buckets
    total_lines_contributed = 0
    for bucket_idx in range(len(bucket_membership)):
        if bucket_membership[bucket_idx] != -1:
            bucket = bucket_membership[bucket_idx]
            bucket_counts[bucket] += 1
            line_counts[bucket] += lines_bucket_membership[bucket_idx]
            total_lines_contributed += lines_bucket_membership[bucket_idx]

    # Calculate the percentage of revisions in each bucket using total_revs_exec
    bucket_percentages = []
    for bucket in range(len(bucket_counts)):
        percentage_in_bucket = bucket_counts[bucket] * 100 / total_revs_exec
        # Use the line counts to calculate the weighted percentage
        if weighted:
            line_percentage_in_bucket = line_counts[bucket] * 100 / total_lines_contributed
            # Multiply the percentage by the percentage of lines contributed by that bucket
            percentage_in_bucket *= line_percentage_in_bucket
        bucket_percentages.append(percentage_in_bucket)

    # If weighted, normalise the percentages so they sum to 100
    if weighted:
        bucket_percentages = [x * 100 / sum(bucket_percentages) for x in bucket_percentages]

    # Assert we sum to roughly 100
    assert 99.9 < sum(bucket_percentages) < 100.1

    # Print out the bucket percentages to 5 decimal places
    # print(f"Patch coverage percentages for {csv_name}: {[round(x, 5) for x in bucket_percentages]}")

    colours = ["#ad302e", "#de5434", "#e9923e", "#f8cc47", "#8bb954", "#428f4d"]
    if bucket_no == covrig_buckets:
        colours = ["#ffffff", "#bd2121", "#ffba0f", "#c9ff70", "#4d9b00", "#ffffff"]

    # Plot the data as a stacked vertical bar chart
    cumulative_total = 0
    idx = 0
    for bucket_p in bucket_percentages:
        ax.bar(csv_name if multiple else 0, bucket_p, bottom=cumulative_total, label=bucket_names[idx], width=0.7,
               color=colours[idx],
               edgecolor='black', zorder=3)
        cumulative_total += bucket_p
        idx += 1

    # Get the average patch coverage
    # Filter patchcoverage data to only include revisions that introduce executable lines
    # patchcoverage_data = [x for i, x in enumerate(patchcoverage_data) if
    #                       covered_lines_data[i] + not_covered_lines_data[i] > 0]
    # avg_patch_coverage = sum(patchcoverage_data) / len(patchcoverage_data)

    # Calculate the coverage for each revision using eloc and coverage
    coverage_perc = [x * 100 / y if y > 0 else -1 for x, y in zip(cov_data, eloc_data)]
    # Filter coverage_perc to only include revisions that work (no -1s)
    coverage_perc = [x for x in coverage_perc if x != -1]
    # Calculate the average coverage
    avg_coverage = sum(coverage_perc) / len(coverage_perc)

    # ax.bar(csv_name if multiple else 0, 0.5, bottom=avg_coverage, label="Average %", width=0.5, color='black',
    #        zorder=4)

    # Turn off ticks for the x axis
    if not multiple:
        ax.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)
        ax.set_xlim(-1, 1)

    # Label the y axis as Patch Coverage
    ax.set_ylabel('Frequency of Patch Coverage (binned)')
    ax.set_ylim(0, 100.0001)

    # Give the plot a title
    if not multiple:
        ax.set_title(f'{csv_name}')
    else:
        ax.set_title(f'Patch Coverage across projects (revs that introduce executable lines)')

    # Print the legend with the bucket names [0%, 25%], (25%, 50%], (50%, 75%], (75%, 100%]
    # or if we are in large scale mode (0%, 25%], (25%, 50%], (50%, 75%], (75%, 100%], 0%, 100%

    # Do plt.legend(bucket_names) but in reverse order
    handles, labels = ax.get_legend_handles_labels()

    # if we are in covrig mode, do not plot the 0% and 100% buckets. Only print the legend once
    if pos == 0:
        if bucket_no == covrig_buckets:
            # Move the legend to the side
            # Remove any N/A strings from handles and labels
            handles = handles[1:5] + handles[6:]
            labels = labels[1:5] + labels[6:]
            ax.legend(handles[::-1], labels[::-1], bbox_to_anchor=(1.05, 1), loc='upper left')
        else:
            # Move the legend to the side
            ax.legend(handles[::-1], labels[::-1], bbox_to_anchor=(1.05, 1), loc='upper left')

    # Make it a dotted grid
    ax.grid(linestyle='dotted', zorder=0, axis='y')

    # Save the plot
    if save:
        ax.set_title(f'Patch Coverage for {csv_name}')
        fig.savefig(f'postprocessing/graphs/{savedir}/{csv_name}/{csv_name}-patch-coverage-{bucket_no}-buckets.png',
                    bbox_inches='tight')
        plt.close(fig)

def plot_bucketed_patch_coverage(data, csv_name, save=True, plot=None, pos=0, multiple=False, savedir=None,
                        weighted=False):
    if plot is None:
        plot = plt.subplots(figsize=DEFAULT_FIGSIZE)
    (fig, ax) = plot
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
    bucketed_cov_perc_data_av = [total_covered[i] * 100 / total_total[i] if total_total[i] != 0 else 0 for i in
                                 range(len(total_covered))]

    # Calculate the proportions
    proportions = [bucketed_cov_perc_data[i] / sum(bucketed_cov_perc_data) for i in range(len(bucketed_cov_perc_data))]

    if weighted:
        proportions = [total_total[i] / sum(total_total) for i in range(len(total_total))]

    # Define the bin labels
    bin_labels = ['≤ 10', '11-100', '101-1000', '> 1000']

    # Define colours
    colours = ['#5299D3', '#EE6C4D', '#FFE0B5', '#663F46']

    # # Obtain the corresponding color from the Viridis colormap
    # colours = [cm.viridis(p / 100) for p in bucketed_cov_perc_data_av]

    # Create the horizontal bar chart
    cumulative_proportions = list(np.cumsum(proportions))
    # Add the 0 to the beginning of the list and remove the last element
    cumulative_proportions = [0] + cumulative_proportions[:-1]

    # Create stacked sections of the bar
    for i in range(len(bin_labels)):
        ax.barh(csv_name if multiple else 0, width=proportions[i], left=cumulative_proportions[i], align='center', label=bin_labels[i], color=colours[i], edgecolor='black')

    # Use ax annotate to add the percentages to the bars (bucketed_cov_perc_data_av)
    annotation_fontsize = 10
    for i in range(len(bin_labels)):
        text_colour = 'black'
        if i == len(bin_labels) - 1:
            text_colour = 'white'
        if proportions[i] > 0.04:
            ax.annotate(f'{bucketed_cov_perc_data_av[i]:.1f}%', xy=(cumulative_proportions[i] + proportions[i] / 2, csv_name if multiple else 0), ha='center', va='center', fontsize=annotation_fontsize, color=text_colour)
        elif proportions[i] != 0:
            # Annotate with an arrow to the side of the bar
            va = 'center'
            ha = 'left'
            xoffset = 0.05
            yoffset = 0
            if i == len(bin_labels) - 1:
                va = 'top'
                xoffset = 0.03
                yoffset = -0.07
            elif i == len(bin_labels) - 2:
                va = 'bottom'
                xoffset = 0.03
                yoffset = 0.07
            ax.annotate(f'{bucketed_cov_perc_data_av[i]:.1f}%', xy=(cumulative_proportions[i] + proportions[i] / 2 , pos + yoffset), xytext=(cumulative_proportions[i] + proportions[i] / 2 + xoffset, pos + yoffset), ha=ha, va=va, fontsize=annotation_fontsize, color='black', arrowprops=dict(arrowstyle='->', color='black'))

    # Set the x-axis label
    if weighted:
        ax.set_xlabel('Proportion of total ELOC contributed by patches')
    else:
        ax.set_xlabel('Proportion of patches')

    if not multiple:
        # Turn off ticks for the y-axis
        ax.tick_params(axis='y', which='both', left=False, right=False, labelleft=False)

    if pos == 0:
        # Set the legend in reverse
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, -0.10), ncol=len(labels), fontsize=8, title='Bins for Patch Sizes (ELOC)')

    ax.set_title('Patches bucketed by the size of the patch in ELOC with average patch coverages for each bin listed')

    # Save the plot
    if save:
        ax.set_title(f'Patch Types for {csv_name}')
        fig.savefig(f'postprocessing/graphs/{savedir}/{csv_name}/{csv_name}-patch-coverage-dist{"-weighted" if weighted else ""}.png', bbox_inches='tight')
        plt.close(fig)

def plot_patch_type(data, csv_name, save=True, plot=None, pos=0, multiple=False, savedir=None, proportional=False):
    if plot is None:
        plot = plt.subplots(figsize=DEFAULT_FIGSIZE)
    (fig, ax) = plot
    # Clean the data
    cleaned_data = utils.clean_data(data)

    # Get the columns we want - covered_lines, not_covered_lines, and changed_test_files
    covered_lines_data, not_covered_lines_data, changed_test_files_data = utils.get_columns(cleaned_data,
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
    patch_type_colours = ["#bd2121", "#bf3dff", "#6394ed", "#ededed"]

    if proportional:
        total = sum(patch_types.values())
        for patch_type in patch_types:
            patch_types[patch_type] = patch_types[patch_type] * 100 / total
        ax.set_ylabel('Percentage of Patches')
    else:
        # Label the y axis as Number of Patches
        ax.set_ylabel('Number of Patches')

    # Plot the data as a stacked vertical bar chart
    cumulative_total = 0
    idx = 0
    for patch_type in patch_types:
        ax.bar(csv_name if multiple else 0, patch_types[patch_type], bottom=cumulative_total, label=patch_type,
               width=0.7,
               color=patch_type_colours[idx], edgecolor='black', zorder=3)
        cumulative_total += patch_types[patch_type]
        idx += 1

    # Turn off ticks for the x axis
    if not multiple:
        ax.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)
        ax.set_xlim(-1, 1)

    # Give the plot a title
    if not multiple:
        ax.set_title(f'{csv_name}')
    else:
        ax.set_title(f'Patch Types across projects')

    # Print the legend with the patch type names
    if pos == 0:
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles[::-1], labels[::-1], bbox_to_anchor=(1.05, 1), loc='upper left')

    if proportional:
        # So we get a sliver of space at the top of the graph
        ax.set_ylim(0, 100.0001)
    else:
        # Use locator params to have 9 ticks on the y axis
        ax.yaxis.set_major_locator(plt.MaxNLocator(9))

    # Make it a dotted grid
    ax.grid(linestyle='dotted', zorder=0, axis='y')

    # Save the plot
    if save:
        ax.set_title(f'Patch Types for {csv_name}')
        fig.savefig(f'postprocessing/graphs/{savedir}/{csv_name}/{csv_name}-patch-types.png', bbox_inches='tight')
        plt.close(fig)


def plot_author_dist(data, csv_name, save=True, date=False, plot=None, limit_authors=5, savedir=None):
    if plot is None:
        plot = plt.subplots(figsize=DEFAULT_FIGSIZE)
    (fig, ax) = plot
    # Clean the data to ignore rows with exits "EmptyCommit", "NoCoverage" or "compileError"
    cleaned_data = utils.clean_data(data)

    author, added_lines, dates = utils.get_columns(cleaned_data, ['author', 'addedlines', 'time'])

    author = replace_names(author)

    # Get the unique authors
    author_dict = anonymize_names(author)

    unique_authors = list(author_dict.values())

    # Get the number of authors
    num_authors = len(unique_authors)

    # Get the number of commits
    num_commits = len(author)

    # Get the number of commits per author
    commits_per_author = {}
    lines_added_per_author = {}
    for i in range(num_authors):
        commits_per_author[unique_authors[i]] = 0
        lines_added_per_author[unique_authors[i]] = 0
    for i in range(num_commits):
        # use author_dict to get the anonymized author
        anon_author = author_dict[author[i]]
        commits_per_author[anon_author] += 1
        lines_added_per_author[anon_author] += added_lines[i]

    # look at dictionary and remove authors with less than <limit> commits
    for key in list(commits_per_author.keys()):
        if commits_per_author[key] < limit_authors:
            del commits_per_author[key]
            del lines_added_per_author[key]

    # # order the authors by number of commits
    # commits_per_author = dict(sorted(commits_per_author.items(), key=lambda item: item[1], reverse=True))
    #
    # # plot the histogram of author on the x axis and number of commits on the y axis
    # ax.bar(commits_per_author.keys(), commits_per_author.values(), edgecolor='black', zorder=3)

    # calculate the average number of lines per commit for each author
    for key in lines_added_per_author.keys():
        lines_added_per_author[key] = lines_added_per_author[key] / commits_per_author[key]

    # order the authors by number of commits
    lines_added_per_author = dict(sorted(lines_added_per_author.items(), key=lambda item: item[1], reverse=True))

    # plot the histogram of author on the x axis and number of commits on the y axis
    ax.bar(lines_added_per_author.keys(), lines_added_per_author.values(), edgecolor='black', zorder=3)

    # Label the x axis as Author
    ax.set_xlabel('Author')

    # Rotate the x axis labels
    plt.xticks(rotation=90)

    # # Label the y axis as Number of Commits
    # ax.set_ylabel('Number of Commits')

    # Label the y axis
    ax.set_ylabel('Number of Lines Added')

    # # Give the plot a title
    # ax.set_title(f'Number of Commits per Author for {csv_name}')

    # Give the plot a title
    ax.set_title(f'Number of Lines Added per Author for {csv_name}')

    # Save the plot
    if save:
        fig.savefig(f'postprocessing/graphs/{savedir}/{csv_name}/{csv_name}-author-dist.png', bbox_inches='tight')
        plt.close(fig)


def plot_exit_status_rates(data, csv_name, save=True, plot=None, pos=0, multiple=False, savedir=None):
    if plot is None:
        plot = plt.subplots(figsize=DEFAULT_FIGSIZE)
    (fig, ax) = plot
    # This time, don't clean the data of compileErrors
    cleaned_data = utils.clean_data(data, omit=['EmptyCommit', 'NoCoverage'])

    # Get the columns we want - covered_lines, not_covered_lines, and changed_test_files
    exit_status_data, dates = utils.get_columns(cleaned_data, ['exit', 'time'])

    # Get the unique exit statuses
    unique_exit_statuses = ["OK", "SomeTestFailed", "TimedOut", "compileError"]

    # Get the number of exit statuses
    num_exit_statuses = len(unique_exit_statuses)

    # Get the number of commits
    num_commits = len(exit_status_data)

    # Get the number of commits per exit status
    commits_per_exit_status = {}
    for i in range(num_exit_statuses):
        commits_per_exit_status[unique_exit_statuses[i]] = 0
    for i in range(num_commits):
        commits_per_exit_status[exit_status_data[i]] += 1

    # Plot our data
    exit_status_colours = ["#428f4d", "#de5434", "#cccccc", "#ad302e"]

    # Calculate the percentage of commits for each exit status
    total_commits = sum(commits_per_exit_status.values())
    for exit_status in commits_per_exit_status.keys():
        commits_per_exit_status[exit_status] = commits_per_exit_status[exit_status] / total_commits * 100

    # Plot the data as a stacked vertical bar chart
    cumulative_total = 0
    idx = 0
    for exit_status in commits_per_exit_status.keys():
        ax.bar(csv_name if multiple else 0, commits_per_exit_status[exit_status], bottom=cumulative_total, width=0.7,
               label=exit_status, color=exit_status_colours[idx], edgecolor='black', zorder=3)
        cumulative_total += commits_per_exit_status[exit_status]
        idx += 1

    # Turn off ticks for the x axis
    if not multiple:
        ax.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)
        ax.set_xlim(-1, 1)

    # Label the y axis as Number of Commits
    ax.set_ylabel('Number of Commits')

    # Give the plot a title
    if not multiple:
        ax.set_title(f'Percentage of Commits per Exit Status for {csv_name}')
    else:
        ax.set_title(f'Percentage of Commits per Exit Status')

    if pos == 0:
        # Add a legend
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles[::-1], labels[::-1], loc='upper left', bbox_to_anchor=(1, 1), title='Exit Statuses')

    # Make it a dotted grid
    ax.grid(linestyle='dotted', zorder=0, axis='y')

    # Save the plot
    if save:
        fig.savefig(f'postprocessing/graphs/{savedir}/{csv_name}/{csv_name}-exit-status-rates.png',
                    bbox_inches='tight')
        plt.close(fig)


def plot_coverage_line_per_author(data, csv_name, save=True, date=False, plot=None, limit_authors=5, savedir=None):
    if plot is None:
        plot = plt.subplots(figsize=DEFAULT_FIGSIZE)
    (fig, ax) = plot
    # Clean the data
    cleaned_data = utils.clean_data(data)

    # Get the columns we want - patch coverage
    patch_coverage_data, authors, dates, covlines, notcovlines = utils.get_columns(cleaned_data,
                                                                                   ['patchcoverage', 'author', 'time',
                                                                                    'covlines', 'notcovlines'])

    # Filter out commits that don't change any executable lines
    idxs = [i for i in range(len(patch_coverage_data)) if covlines[i] + notcovlines[i] > 0]
    patch_coverage_data = [patch_coverage_data[i] for i in idxs]
    authors = [authors[i] for i in idxs]
    dates = [dates[i] for i in idxs]

    # Get the unique authors
    unique_authors = list(set(authors))

    # Get the number of authors
    num_authors = len(unique_authors)

    # Get the number of commits per author
    commits_per_author = {}
    for i in range(num_authors):
        commits_per_author[unique_authors[i]] = 0
    for i in range(len(authors)):
        commits_per_author[authors[i]] += 1

    # Filter out authors with less than <limit> commits
    filtered_authors = []
    for author in commits_per_author.keys():
        if commits_per_author[author] >= limit_authors:
            filtered_authors.append(author)
    filtered_authors = set(filtered_authors)

    # Create a list of patch coverages for each author
    author_patch_coverages = {}
    dates_for_authors = {}
    for author in filtered_authors:
        author_patch_coverages[author] = []
        dates_for_authors[author] = []
    for i in range(len(authors)):
        if authors[i] in filtered_authors:
            author_patch_coverages[authors[i]].append(patch_coverage_data[i])
            dates_for_authors[authors[i]].append(dates[i])

    # Calculate a moving average for each author with a window size of 5
    moving_average_author_patch_coverages = {}
    for author in filtered_authors:
        moving_average_author_patch_coverages[author] = moving_average(author_patch_coverages[author], 5)

    # Plot a line graph of coverage over time for each author
    if date:
        for author in filtered_authors:
            # print(len(dates_for_authors[author]), len(moving_average_author_patch_coverages[author]))
            ax.plot(dates_for_authors[author], moving_average_author_patch_coverages[author], label=author)
    else:
        # NOTE: not a great visualization since each author has a different number of commits
        for author in filtered_authors:
            ax.plot(moving_average_author_patch_coverages[author], label=author)

    # Label the x axis as Date
    if date:
        ax.set_xlabel('Date')
    else:
        ax.set_xlabel('Commit Number')

    # Label the y axis as Patch Coverage
    ax.set_ylabel('Patch Coverage')

    # Give the plot a title
    ax.set_title(
        f'Patch Coverage over Time for {csv_name} per Author (only revisions that add/modify executable lines)')

    # Add a legend
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles[::-1], labels[::-1], loc='upper left', bbox_to_anchor=(1, 1), title='Authors')

    # Save the plot
    if save:
        fig.savefig(
            f'postprocessing/graphs/{savedir}/{csv_name}/{csv_name}-patch-coverage-line-author{"-date" if date else ""}.png',
            bbox_inches='tight')
        plt.close(fig)


def plot_coverage_box_per_author(data, csv_name, save=True, date=False, plot=None, limit_authors=5, savedir=None):
    if plot is None:
        plot = plt.subplots(figsize=DEFAULT_FIGSIZE)
    (fig, ax) = plot
    # Clean the data
    cleaned_data = utils.clean_data(data)

    # Get the columns we want - patch coverage
    patch_coverage_data, authors, dates, covlines, notcovlines = utils.get_columns(cleaned_data,
                                                                                   ['patchcoverage', 'author', 'time',
                                                                                    'covlines', 'notcovlines'])

    # Filter out commits that don't change any executable lines
    idxs = [i for i in range(len(patch_coverage_data)) if covlines[i] + notcovlines[i] > 0]
    patch_coverage_data = [patch_coverage_data[i] for i in idxs]
    authors = [authors[i] for i in idxs]
    dates = [dates[i] for i in idxs]

    # Get the unique authors
    unique_authors = list(set(authors))

    # Get the number of authors
    num_authors = len(unique_authors)
    limit = min(limit_authors, num_authors)  # Make sure we don't try to plot more authors than we have

    # Get the number of commits per author
    commits_per_author = {}
    for i in range(num_authors):
        commits_per_author[unique_authors[i]] = 0
    for i in range(len(authors)):
        commits_per_author[authors[i]] += 1

    # # Filter out authors with less than <limit> commits
    # filtered_authors = []
    # for author in commits_per_author.keys():
    #     if commits_per_author[author] >= limit:
    #         filtered_authors.append(author)
    # filtered_authors = set(filtered_authors)

    # Filter only the top <limit> authors
    sorted_authors = sorted(commits_per_author.items(), key=lambda x: x[1], reverse=True)
    filtered_authors = []
    for i in range(limit):
        filtered_authors.append(sorted_authors[i][0])

    # Create a list of patch coverages for each author
    author_patch_coverages = {}
    for author in filtered_authors:
        author_patch_coverages[author] = []
    for i in range(len(authors)):
        if authors[i] in filtered_authors:
            author_patch_coverages[authors[i]].append(patch_coverage_data[i])

    # Plot a box plot of patch coverage for each author
    # transform the data into a list of lists
    data_to_plot = []
    for author in filtered_authors:
        data_to_plot.append(author_patch_coverages[author])

    # # Print the data
    # for i in range(len(data_to_plot)):
    #     # sort the data
    #     data_to_plot[i].sort()
    #     print(f'{filtered_authors[i]}: {data_to_plot[i]}')

    # Create the boxplot
    # ax.boxplot(data_to_plot, labels=filtered_authors, autorange=True)

    # Do a violin plot instead
    ax.violinplot(data_to_plot, showmedians=True, showextrema=True)

    # Write the author names instead of numbers
    ax.set_xticks(range(1, len(filtered_authors) + 1))
    ax.set_xticklabels(filtered_authors)
    #
    # # Label the x axis as author
    # ax.set_xlabel('Author')

    # Make the x label vertical
    ax.tick_params(axis='x', labelrotation=90)

    # Label the y axis as Patch Coverage

    ax.set_ylabel('Patch Coverage')

    # Give the plot a title
    ax.set_title(f'Patch Coverage for {csv_name} (revisions that add/modify executable lines)')

    # Save the plot
    if save:
        fig.savefig(f'postprocessing/graphs/{savedir}/{csv_name}/{csv_name}-patch-coverage-box.png',
                    bbox_inches='tight')
        plt.close(fig)


def plot_patch_coverage_over_time(data, csv_name, save=True, date=False, plot=None, window_size=50, savedir=None):
    if plot is None:
        plot = plt.subplots(figsize=DEFAULT_FIGSIZE)
    (fig, ax) = plot
    # Clean the data
    cleaned_data = utils.clean_data(data)

    # Get the columns we want - patch coverage, dates
    patch_coverage_data, dates, covlines, notcovlines = utils.get_columns(cleaned_data,
                                                                          ['patchcoverage', 'time', 'covlines',
                                                                           'notcovlines'])

    # Filter out commits that don't change any executable lines
    idxs = [i for i in range(len(patch_coverage_data)) if covlines[i] + notcovlines[i] > 0]
    patch_coverage_data = [patch_coverage_data[i] for i in idxs]
    dates = [dates[i] for i in idxs]

    # Get the moving average of the patch coverage
    moving_average_patch_coverage = moving_average(patch_coverage_data, window_size)

    # Plot a line graph of coverage over time
    if date:
        ax.plot(dates, moving_average_patch_coverage)
        ax.plot(dates, patch_coverage_data, 'o')
    else:
        ax.plot(moving_average_patch_coverage)
        ax.plot(patch_coverage_data, 'o')

    # Label the x axis as Date
    if date:
        ax.set_xlabel('Date')
    else:
        ax.set_xlabel('Commit Number')

    # Label the y axis as Patch Coverage
    ax.set_ylabel('Patch Coverage')

    # Give the plot a title
    ax.set_title(
        f'Patch Coverage over Time for {csv_name} (window size = {window_size}, only commits that add/modify executable lines)')

    # Save the plot
    if save:
        fig.savefig(
            f'postprocessing/graphs/{savedir}/{csv_name}/{csv_name}-patch-coverage-line-overall{"-date" if date else ""}.png',
            bbox_inches='tight')
        plt.close(fig)


def plot_average_patch_coverage_per_author(data, csv_name, save=True, plot=None, limit_authors=5, savedir=None):
    if plot is None:
        plot = plt.subplots(figsize=DEFAULT_FIGSIZE)
    (fig, ax) = plot
    # Clean the data
    cleaned_data = utils.clean_data(data)

    # Get the columns we want - patch coverage and author
    patch_coverage_data, authors, covlines, notcovlines = utils.get_columns(cleaned_data,
                                                                            ['patchcoverage', 'author', 'covlines',
                                                                             'notcovlines'])

    # Filter out commits that don't change any executable lines
    idxs = [i for i in range(len(patch_coverage_data)) if covlines[i] + notcovlines[i] > 0]
    patch_coverage_data = [patch_coverage_data[i] for i in idxs]
    authors = [authors[i] for i in idxs]

    authors = replace_names(authors)

    author_to_anon = anonymize_names(authors)

    # Take all authors and make them anonymous
    authors = [author_to_anon[author] for author in authors]

    # Get the average patch coverage overall
    average_patch_coverage_overall = sum(patch_coverage_data) / len(patch_coverage_data)

    # Get the median patch coverage overall
    # median_patch_coverage_overall = statistics.median(patch_coverage_data)

    # Group the data by author
    author_patch_coverage = {}
    for i in range(len(authors)):
        if authors[i] not in author_patch_coverage.keys():
            author_patch_coverage[authors[i]] = []
        author_patch_coverage[authors[i]].append(patch_coverage_data[i])

    # Filter to only the authors with <limit> or more commits
    filtered_authors = []
    for author in author_patch_coverage.keys():
        if len(author_patch_coverage[author]) >= limit_authors:
            filtered_authors.append(author)
    filtered_authors = set(filtered_authors)

    # Calculate the average patch coverage for each author
    average_patch_coverage = {}
    for author in filtered_authors:
        average_patch_coverage[author] = sum(author_patch_coverage[author]) / len(author_patch_coverage[author])

    # Sort the authors by average patch coverage and take the top n
    n = 10

    sorted_average_patch_coverage = sorted(average_patch_coverage.items(), key=lambda x: x[1], reverse=True)
    sorted_average_patch_coverage = sorted_average_patch_coverage[:n]

    bar_container = ax.bar([x[0] for x in sorted_average_patch_coverage], [x[1] for x in sorted_average_patch_coverage],
                           edgecolor='black')

    # Add a horizontal line for the average patch coverage overall
    ax.axhline(y=average_patch_coverage_overall, color='red', linestyle='--')
    # ax.axhline(y=median_patch_coverage_overall, color='orange', linestyle='--')

    # for sorted_average_patch_coverage, get the number of commits for each author
    number_of_commits = []
    for author in sorted_average_patch_coverage:
        number_of_commits.append(len(author_patch_coverage[author[0]]))

    # use ax.bar_label to add text labels to the top of the bars to show the number of commits
    ax.bar_label(bar_container, labels=number_of_commits, label_type='edge', padding=3)

    # Label the y axis as Average Patch Coverage
    ax.set_ylabel('Average Patch Coverage')

    # Make the x label vertical
    ax.tick_params(axis='x', labelrotation=90)
    ax.set_ylim(0, 100)

    # TODO: Move this to get_stats
    # Print out the top n authors and their average patch coverage
    # print(f'Top {n} authors by average patch coverage:')
    # for author in sorted_average_patch_coverage:
    #     print(f'{author[0]}: {author[1]:.2f}%')

    # Give the plot a title
    ax.set_title(f'{csv_name}')
    fig.suptitle(
        f'Average Patch Coverage per Author (across commits that add/modify executable lines) (minimum of {limit_authors} commits)',
        fontsize=16,
        y=0.98)
    # Add a subtitle
    fig.text(0.5, 0.945, f'(Numbers on bars represent number of commits attributed to author)', ha='center',
             fontsize=14,
             fontweight='normal')

    # Label the vertical line as the average patch coverage overall in the legend and specify the value
    # ax.legend([f'Avg. Patch Cov = {average_patch_coverage_overall:.2f}%',
    #            f'Median Patch Cov = {median_patch_coverage_overall:.2f}%'])
    ax.legend([f'Avg. Patch Cov = {average_patch_coverage_overall:.2f}%'])

    # Save the plot
    if save:
        fig.savefig(f'postprocessing/graphs/{savedir}/{csv_name}/{csv_name}-average-patch-coverage-per-author.png',
                    bbox_inches='tight')
        plt.close(fig)


def plot_patch_coverage_bins(data, csv_name, save=True, plot=None, savedir=None):
    if plot is None:
        plot = plt.subplots(figsize=DEFAULT_FIGSIZE)
    (fig, ax) = plot

    # Clean the data
    cleaned_data = utils.clean_data(data)

    # Get the columns we want - patch coverage
    patch_coverage_data, covlines, notcovlines = utils.get_columns(cleaned_data,
                                                                   ['patchcoverage', 'covlines', 'notcovlines'])

    # Filter patch coverage data to only include commits covlines + notcovlines > 0
    idxs = [i for i in range(len(patch_coverage_data)) if covlines[i] + notcovlines[i] > 0]
    patch_coverage_data = [patch_coverage_data[i] for i in idxs]

    bins = 100
    ax.hist(patch_coverage_data, bins=bins)

    # Label the x axis as Patch Coverage
    ax.set_xlabel('Patch Coverage')

    # Label the y axis as Number of Commits
    ax.set_ylabel('Number of Commits')

    # Give the plot a title
    ax.set_title(f'{csv_name}')
    fig.suptitle(f'Patch Coverage Distributions for Revisions that Add or Modify Executable Code', fontsize=16)

    # Save the plot
    if save:
        fig.savefig(f'postprocessing/graphs/{savedir}/{csv_name}/{csv_name}-patch-coverage-bins.png',
                    bbox_inches='tight')
        plt.close(fig)


def plot_commit_frequency(data, csv_name, save=True, plot=None, limit=5, savedir=None):
    if plot is None:
        plot = plt.subplots(figsize=DEFAULT_FIGSIZE)
    (fig, ax) = plot

    # Clean the data
    cleaned_data = utils.clean_data(data)

    # Get the columns we want - author, date
    author_data, date_data = utils.get_columns(cleaned_data, ['author', 'time'])

    author_data = replace_names(author_data)

    anonymized_author_to_author = anonymize_names(author_data)

    # Replace the author data with the anonymized author data
    author_data = [anonymized_author_to_author[author] for author in author_data]

    # Filter to the top <limit> authors
    author_commit_frequency = {}
    for author in author_data:
        if author not in author_commit_frequency:
            author_commit_frequency[author] = 1
        else:
            author_commit_frequency[author] += 1

    sorted_author_commit_frequency = sorted(author_commit_frequency.items(), key=lambda x: x[1], reverse=True)
    top_authors = [author for author, _ in sorted_author_commit_frequency[:limit]]

    # Filter the data to only include commits by the filtered authors
    filtered_data = []
    for i in range(len(author_data)):
        if author_data[i] in top_authors:
            filtered_data.append((author_data[i], date_data[i]))

    author_data, date_data = zip(*filtered_data)

    # Convert author_data to a list and date_data to a list
    author_data = list(author_data)
    date_data = list(date_data)

    # Set months to be a list of all months in the data
    time_bins = {}
    # Populate time_bins with (month, year) tuples from the earliest commit to the latest commit
    # make a copy of the date_data list so we don't modify the original
    date_data_copy = deepcopy(date_data)
    # sort the date_data_copy list
    date_data_copy.sort()
    # get the earliest commit date
    earliest_commit_date, latest_commit_date = date_data_copy[0], date_data_copy[-1]
    # Initialize the time_bins dictionary with the earliest commit date up to the latest commit date in 1 month increments
    current_date = earliest_commit_date
    current_date = current_date.replace(day=1).replace(hour=0).replace(minute=0).replace(second=0).replace(
        microsecond=0)

    while current_date <= latest_commit_date:
        time_bins[(current_date.month, current_date.year)] = 0
        current_date = (current_date.replace(day=1) + datetime.timedelta(days=32)).replace(day=1)

    # Populate time_bins with the number of commits per month for each author (dict of dicts)
    author_commit_frequency_per_month = {}
    for author in top_authors:
        author_commit_frequency_per_month[author] = deepcopy(time_bins)
    for i in range(len(author_data)):
        author = author_data[i]
        date = date_data[i]
        author_commit_frequency_per_month[author][(date.month, date.year)] += 1

    # Create a map from (month, year) tuples to dict objects containing the number of commits for each author
    time_bins_dict = {}
    for (month, year) in time_bins:
        time_bins_dict[(month, year)] = {}
        for author in top_authors:
            time_bins_dict[(month, year)][author] = author_commit_frequency_per_month[author][(month, year)]

    # Generate <limit> colours in the matplotlib default colour cycle
    colours = [colour for _, colour in zip(range(limit), ax._get_lines.prop_cycler)]
    # Map each author to a colour
    author_colour_map = {}
    for i in range(len(top_authors)):
        author_colour_map[top_authors[i]] = colours[i]

    # Plot the data for each month, year tuple
    datecounter = 0
    for (month, year) in time_bins_dict:
        # Plot as a histogram
        # order the authors by number of commits
        sorted_authors = sorted(time_bins_dict[(month, year)].items(), key=lambda x: x[1], reverse=True)

        # convert (month, year) to a datetime object
        month_dt = datetime.datetime(year=year, month=month, day=1)

        # get the number of days in the month using datetime.timedelta
        num_days_in_month = (month_dt.replace(day=1) + datetime.timedelta(days=32)).replace(day=1) - month_dt

        # adjust month_dt to be the middle of the month
        month_dt = month_dt + num_days_in_month / 2

        for author in sorted_authors:
            ax.bar(month_dt, author[1], label=author[0], width=num_days_in_month - datetime.timedelta(8),
                   color=author_colour_map[author[0]]['color'])
        datecounter += 1

    ax.set_xlabel('Month')
    ax.set_ylabel('Number of Commits')
    ax.set_title('Number of Commits per Month')

    adjust_dates_on_xaxis(ax, date_data_copy)

    # # Plot the data
    # for author in author_commit_frequency_per_month:
    #     # Transform author_commit_frequency_per_month[author].keys() into datetime objects
    #     months = [datetime.datetime(year=year, month=month, day=1) for (month, year) in author_commit_frequency_per_month[author].keys()]
    #     # ax.plot(months, author_commit_frequency_per_month[author].values(), label=author)
    #     # Plot as a histogram
    #     ax.hist(months, weights=author_commit_frequency_per_month[author].values(), label=author, bins=len(months))
    #

    # For

    # Plot the data
    # for author in author_commit_frequency_per_month:
    #     ax.plot(months, author_commit_frequency_per_month[author], label=author)

    # Label the x axis as Month
    ax.set_xlabel('Time (bin size = 1 month)')

    # Label the y axis as Number of Commits
    ax.set_ylabel('Number of Commits')

    # Give the plot a title
    ax.set_title(f'{csv_name}')

    # Add a legend for the unique authors
    handles, labels = ax.get_legend_handles_labels()
    newLabels, newHandles = [], []
    for handle, label in zip(handles, labels):
        if label not in newLabels:
            newLabels.append(label)
            newHandles.append(handle)

    ax.legend(newHandles, newLabels, loc='upper left')

    # Save the plot
    if save:
        fig.savefig(f'postprocessing/graphs/{savedir}/{csv_name}/{csv_name}-commit-frequency.png',
                    bbox_inches='tight')
        plt.close(fig)


def plot_timespan(data, csv_name, save=True, plot=None, pos=0, multiple=False, savedir=None, labels=None,
                  commits_prev_compiling_range=None):
    if plot is None:
        plot = plt.subplots(figsize=DEFAULT_FIGSIZE)
    (fig, ax) = plot
    # This time, don't clean the data of compileErrors
    cleaned_data = utils.clean_data(data)

    # Get the start and end dates
    date_data = utils.get_columns(cleaned_data, ['time'])[0]
    start_date = min(date_data)
    end_date = max(date_data)
    idx = pos
    pos *= -1

    bar_height = 0.5

    # Get the list of colour from mcolors.TABLEAU_COLORS
    colours = list(mcolors.TABLEAU_COLORS.values())

    # The 250 revs in Covrig (looking at table 1 and cross-referencing ELOC) are the 250 most recent commits of the legacy that modify exec code/tests

    if commits_prev_compiling_range is not None:
        lowered = [(x.lower(), x) for x in commits_prev_compiling_range.keys()]
        for i in range(len(lowered)):
            if lowered[i][0] in csv_name.lower():
                daterange = commits_prev_compiling_range[lowered[i][1]]
                # If it's a new repository (not in legacy Covrig) then just plot from start to end
                if daterange is None or daterange == (-1, -1):
                    if daterange == (-1, -1):
                        ax.barh(pos, end_date - start_date, left=start_date, height=bar_height, color=colours[idx],
                                edgecolor='black', zorder=3)
                    break
                # If it's a repository in legacy Covrig then plot from the daterange first
                # convert daterange to datetime objects
                start_date_p_d = datetime.datetime.fromtimestamp(daterange[0])
                end_date_p = datetime.datetime.fromtimestamp(daterange[1])
                # Get the index of date_data that has the value end_date_p
                if end_date_p in date_data:
                    end_date_p_index = date_data.index(end_date_p)
                else:
                    # Iterate through date_data to find the closest date to end_date_p
                    end_date_p_index = 0
                    for j in range(len(date_data)):
                        end_date_p_index = j
                        if date_data[j] > end_date_p:
                            break
                    end_date_p = date_data[end_date_p_index]

                # use the operating range to get the start date of the legacy data (not first data point, first one used in study)
                start_date_p = datetime.datetime.fromtimestamp(commits_prev_operating_range[lowered[i][1]][0])
                print(
                    f"Covrig (250) data for {csv_name} is from {int(start_date_p.timestamp())} to {int(end_date_p.timestamp())}")

                # Bar for the legacy data
                prev_bar = ax.barh(pos, end_date_p - start_date_p, left=start_date_p, height=bar_height,
                                   color=colours[idx], hatch='//////', edgecolor='black', zorder=3)

                # plot the same bar again but transparently, a little hack to only display one legend entry
                # works on assumption that second bar has legacy data (since apr doesn't) - no need to overengineer this
                if idx == 1:
                    dummy_bar = ax.barh(pos, end_date_p - start_date_p, left=start_date_p, height=bar_height,
                                        facecolor='none', hatch='//////', edgecolor='black', zorder=3,
                                        label='Legacy data for original Covrig paper (250 commits)')

                # Start of all the data in jun2015data/
                # ax.barh(pos, 15, left=start_date_p_d, height=bar_height, color='black', zorder=4)
                # # End of the 250 revisions studied under Covrig
                # ax.barh(pos, 10, left=end_date_p, height=bar_height, color='#333333', zorder=4)
                # # Start of the 250 revisions studied under Covrig
                # ax.barh(pos, 10, left=start_date_p, height=bar_height, color='#333333', zorder=5)

                # Bar for the new data
                ax.barh(pos, end_date - end_date_p, left=end_date_p, height=bar_height, color=colours[idx],
                        edgecolor='black',
                        zorder=3)
                break

    # Label the x axis as Date
    ax.set_xlabel('Date')

    # Show x ticks at full years
    ax.xaxis.set_major_locator(mdates.YearLocator())
    # Make sure they are shown as years in the format YYYY
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

    # Make sure len(csv_names) yticks are shown
    if labels is not None:
        ax.set_yticks([-x for x in range(len(labels))])
        ax.set_yticklabels(labels)

    if not multiple:
        # Give the plot a title
        ax.set_title(f'{csv_name} Timespan')
    else:
        ax.set_title(f'Timespan for projects (excluding compileErrors)')

    # Move title to the left
    ax.title.set_position([0.5, 1.05])

    # Get the year of the start date as a datetime object
    start_date_year = datetime.datetime(year=start_date.year, month=1, day=1)

    # Make it a vertical only grid
    if pos == 0:
        ax.grid(visible=True, axis='x', zorder=0)
        ax.set_xlim(left=start_date_year)

    # Get the current left xlim using num2date
    left_xlim = mdates.num2date(ax.get_xlim()[0]).replace(tzinfo=None)
    # Make the left xlim this if it is less than left_xlim
    if start_date_year < left_xlim:
        ax.set_xlim(left=start_date_year)

    # Change ylims so there is a little space at the top and bottom
    if idx == 8 and multiple:
        ax.set_ylim(top=1, bottom=-9)

    # Put the legend in the upper right corner
    ax.legend(loc='upper right')

    # Save the plot
    if save:
        fig.savefig(f'postprocessing/graphs/{savedir}/{csv_name}/{csv_name}-timespan.png', bbox_inches='tight')
        plt.close(fig)


def plot_diffcov_hist(data, csv_name, save=True, plot=None, type='line', savedir=None, size=DEFAULT_FIGSIZE, merge=True):
    if plot is None:
        plot = plt.subplots(figsize=size)
    (fig, ax) = plot

    # Take the row according to the type.
    type_to_line = {'line': 0, 'function': 1, 'branch': 2}
    row = data[type_to_line[type]]

    # Make all data ints
    row = [int(x) for x in row]

    bins = ['UNC', 'LBC', 'UIC', 'UBC', 'GBC', 'GIC', 'GNC', 'CBC', 'EUB', 'ECB', 'DUB', 'DCB']

    colours = ["#ff622a", "#cc6666", "#eeaa30", "#fde007", "#448844", "#30cc37", "#b5f7af", "#cad7fe", "#dddddd",
               "#cc66ff", "#eeeeee", "#ffffff"]

    if merge:
        # Get the index of UIC, and merge into UNC
        merge_targets = [('UIC', 'UNC'), ('GIC', 'GNC'), ('EUB', 'DUB'), ('ECB', 'DCB')]

        for merge_target in merge_targets:
            idx = bins.index(merge_target[0])
            target = bins.index(merge_target[1])
            row[target] += row[idx]
            # Get rid of the merged bin
            row.pop(idx)
            bins.pop(idx)
            colours.pop(idx)


    # Plot the data
    ax.bar(bins, row, color=colours, edgecolor='black')

    # Label the x axis as coverage type
    ax.set_xlabel('Differential Coverage Categories')

    # Label the y axis as Count
    # take type_to_line[type] and make its first letter uppercase
    ax.set_ylabel(f'{type.capitalize()} Count')

    # Give the plot a title
    ax.set_title(f'{csv_name}')

    # Save the plot
    if save:
        fig.savefig(f'postprocessing/graphs/{savedir}/{csv_name}/{csv_name}-diffcov-{type}.png',
                    bbox_inches='tight')
        plt.close(fig)


def plot_diffcov_bars(data, csv_name, save=True, plot=None, type='line', savedir=None, size=DEFAULT_FIGSIZE, pos=0,
                      multiple=False, merge=True):
    if plot is None:
        plot = plt.subplots(figsize=DEFAULT_FIGSIZE)
    (fig, ax) = plot

    type_to_line = {'line': 0, 'function': 1, 'branch': 2}
    row = data[type_to_line[type]]

    # Make all data ints
    row = [int(x) for x in row]

    bins = ['UNC', 'LBC', 'UIC', 'UBC', 'GBC', 'GIC', 'GNC', 'CBC', 'EUB', 'ECB', 'DUB', 'DCB']

    names = ['Added Uncovered Code', 'Lost Baseline Cov.', 'Included Uncovered Code', 'Baseline Uncovered Code',
             'Gained Baseline Cov.', 'Included Covered Code', 'Added Covered Code', 'Covered Baseline Code',
             'Excluded Uncovered Code', 'Excluded Covered Code', 'Deleted Uncovered Code', 'Deleted Covered Code']

    colours = ["#ff622a", "#cc6666", "#eeaa30", "#fde007", "#448844", "#30cc37", "#b5f7af", "#cad7fe", "#dddddd",
               "#cc66ff", "#eeeeee", "#ffffff"]

    if merge:
        # Get the index of UIC, and merge into UNC
        merge_targets = [('UIC', 'UNC'), ('GIC', 'GNC'), ('EUB', 'DUB'), ('ECB', 'DCB')]

        for merge_target in merge_targets:
            idx = bins.index(merge_target[0])
            target = bins.index(merge_target[1])
            row[target] += row[idx]
            # Get rid of the merged bin
            row.pop(idx)
            bins.pop(idx)
            names.pop(idx)
            colours.pop(idx)

    # Pull out the data and put it in a map (int, bin, colour)
    data_map = {}
    for idx, val in enumerate(row):
        data_map[bins[idx]] = (val, names[idx], colours[idx])

    new_bin_order = ['UNC', 'LBC', 'UIC', 'UBC', 'GNC', 'GBC', 'GIC', 'CBC', 'EUB', 'ECB', 'DUB', 'DCB']

    if merge:
        # Remove UIC, GIC, EUB and ECB
        new_bin_order.remove('UIC')
        new_bin_order.remove('GIC')
        new_bin_order.remove('EUB')
        new_bin_order.remove('ECB')

    # Plot a stacked bar chart for the data (positives)
    minimum = -9999999
    maximum = 9999999
    width = 0.25
    total = 0
    for bin in new_bin_order:
        # Get the height of the bar
        height = data_map[bin][0]
        # Get the bottom of the bar
        # Plot the bar
        label = f"({bin}) {data_map[bin][1]}"
        if bin == 'CBC':
            # Plot negatively
            ax.bar(csv_name, height, bottom=-height, color=data_map[bin][2], edgecolor='black', zorder=3, align='edge',
                   width=-width, label=label)
            minimum = -height
        elif bin == 'GBC' or bin == 'GIC' or bin == 'GNC' or bin == 'DUB':
            ax.bar(csv_name, height, bottom=total, color=data_map[bin][2], edgecolor='black', zorder=3, align='edge',
                   width=-width, label=label)
            total += height
    maximum = total

    total = 0
    for bin in new_bin_order:
        # Get the height of the bar
        height = data_map[bin][0]
        # Get the bottom of the bar
        # Plot the bar
        label = f"({bin}) {data_map[bin][1]}"
        if bin == 'UBC':
            # Plot negatively
            ax.bar(csv_name, height, bottom=-height, color=data_map[bin][2], edgecolor='black', zorder=3, align='edge',
                   width=width, label=label)
            minimum = min(-height, minimum)
        elif bin == 'LBC' or bin == 'UIC' or bin == 'UNC' or bin == 'DCB':
            ax.bar(csv_name, height, bottom=total, color=data_map[bin][2], edgecolor='black', zorder=3, align='edge',
                   width=width, label=label)
            total += height
    maximum = max(total, maximum)

    # Plot a horizontal line at 0 across the whole graph
    ax.axhline(y=0, color='black', linewidth=1, zorder=2)

    # Label the y axis as Count
    # take type_to_line[type] and make its first letter uppercase
    ax.set_ylabel(f'{type.capitalize()} Count')

    # Give the plot a title
    if not multiple:
        ax.set_title(f'{csv_name}')
    else:
        ax.set_title(f'Differential Coverage across projects')
        # Make the xticks at 90 degrees
        plt.xticks(rotation=90)

    # Get the current y limits
    y_min, y_max = ax.get_ylim()
    # Check if y_min, y_max are smaller than minimum, maximum
    changed = False
    if y_min >= minimum:
        y_min = minimum + minimum * 0.1
        changed = True
    if y_max <= maximum:
        y_max = maximum + maximum * 0.1
        changed = True
    # Set the y limits
    ax.set_ylim(bottom=y_min, top=y_max)

    # Use locator params to have 9 ticks on the y axis
    ax.yaxis.set_major_locator(plt.MaxNLocator(19))

    # Give the plot a title
    ax.set_yticklabels([f'{abs(x):.0f}' for x in ax.get_yticks()])

    # Print the legend with the patch type names
    if pos == 0:
        # Define a title string
        title = f"Note: For each project, the sum of diff. cov. bins ({' + '.join(new_bin_order[:6])}) equals the ELOC of the final revision studied."
        # Wrap the title every 29 characters
        title = "\n".join(wrap(title, 29))
        # Draw a text box on the RHS outside the plot stating that for each project the sum of all new_bins[:8] is the final ELOC
        legend_suppl = ax.legend(handles=[], bbox_to_anchor=(1.05, 0.5),
                  title=title,
                  loc='upper left', title_fontsize=11)
        ax.add_artist(legend_suppl)

        handles, labels = ax.get_legend_handles_labels()
        main_legend = ax.legend(handles, labels, bbox_to_anchor=(1.05, 1), loc='upper left', title='Diff. Cov. Categories',
                  title_fontsize=12)


    # Make it a grid
    ax.grid(True, zorder=0, axis='y')

    # Save the plot
    if save:
        fig.savefig(f'postprocessing/graphs/{savedir}/{csv_name}/{csv_name}-diffcov-{type}-compressed.png',
                    bbox_inches='tight')
        plt.close(fig)


def plot_non_det_hist(data, csv_name, save=True, date=False, plot=None, savedir=None):
    if plot is None:
        plot = plt.subplots(figsize=DEFAULT_FIGSIZE)
    (fig, ax) = plot

    # Clean the data - we also don't want TimedOut as non-det errors with this usually mean the test timed out in
    # some of the runs but not others instead of passing and then failing
    cleaned_data = utils.clean_data(data, omit=['EmptyCommit', 'NoCoverage', 'compileError', 'TimedOut'])

    # This should only be called for files that have a non_det column
    date_data, non_det_data, repeats_data = utils.get_columns(cleaned_data, ['time', 'non_det', 'repeats'])

    repeats = repeats_data[0]

    # Set months to be a list of all months in the data
    time_bins = {}

    if date:
        # Populate time_bins with (month, year) tuples from the earliest commit to the latest commit
        # make a copy of the date_data list so we don't modify the original
        date_data_copy = deepcopy(date_data)
        # sort the date_data_copy list
        date_data_copy.sort()
        # get the earliest commit date
        earliest_commit_date, latest_commit_date = date_data_copy[0], date_data_copy[-1]
        # Initialize the time_bins dictionary with the earliest commit date up to the latest commit date in 1 month increments
        current_date = earliest_commit_date
        current_date = current_date.replace(day=1).replace(hour=0).replace(minute=0).replace(second=0).replace(
            microsecond=0)

        while current_date <= latest_commit_date:
            time_bins[(current_date.month, current_date.year)] = 0
            current_date = (current_date.replace(day=1) + datetime.timedelta(days=32)).replace(day=1)

        # Iterate: Look at date_data[i], get which month and year it is, increment time_bins[(month, year)] if non_det_data[i] is True
        for i in range(len(date_data)):
            # Get the month and year of the ith commit
            month, year = date_data[i].month, date_data[i].year
            # Increment the number of commits in that month
            non_det_value = non_det_data[i] == 'True'
            time_bins[(month, year)] += int(non_det_value)
    else:
        # We are constructing bins in relations to commits, not dates
        bin_size = 10
        # Populate time_bins with len(date_data) / bin_size bins (round up)
        num_bins = math.ceil(len(date_data) / bin_size)
        for i in range(num_bins):
            # So for bin_size = 10, we should have bins 0-9, 10-19, 20-29, etc.
            time_bins[i * bin_size] = 0

        # Start at the first commit, and increment the bin that it belongs to
        current_bin = 0
        for i in range(len(date_data)):
            # Increment the bin
            time_bins[current_bin] += int(non_det_data[i] == 'True')
            # If we have reached the end of the bin, increment the current_bin
            if (i + 1) % bin_size == 0:
                current_bin += bin_size

    # Plot the data
    # Get the x and y data
    if date:
        x_data = [dt.datetime(year=year, month=month, day=1) for (month, year) in time_bins.keys()]
    else:
        x_data = list(time_bins.keys())
    y_data = list(time_bins.values())

    # Plot the data as a histogram
    if date:
        ax.bar(x_data, y_data, width=30, color='#ff622a')
        # Make sure the x limits are the first and last month in the data
        ax.set_xlim(earliest_commit_date, latest_commit_date)
    else:
        ax.bar(x_data, y_data, color='#ff622a', align='edge', width=bin_size)
        # Make sure the x limits are 0 and the length of the data
        ax.set_xlim(0, len(date_data))

    # Label the x axis as Month
    if date:
        ax.set_xlabel('Time (bin size = 1 month)')
        # Format the x axis so we only show whole years
        adjust_dates_on_xaxis(ax, date_data_copy, adjust=7)
    else:
        ax.set_xlabel('Number of Commits (bin size = 10 commits)')
        # Set y lim to be 0 to bin_size
        ax.set_ylim(0, bin_size)

    # Label the y axis as Number of Nondet Commits
    ax.set_ylabel('Number of Flaky Commits')


    # Make sure y ticks only show whole numbers
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))

    # Give the plot a title
    ax.set_title(f'{csv_name} ({repeats} repeats)')

    # If we can find the legacy date, let's plot it as a vertical line
    plot_vert_at_timestamp(ax, csv_name, date, round_to_month=True)

    # Save the plot
    if save:
        fig.savefig(f'postprocessing/graphs/{savedir}/{csv_name}/{csv_name}-nondet{"-date" if date else ""}.png',
                    bbox_inches='tight')
        plt.close(fig)


""" Utility Functions """

def adjust_dates_on_xaxis(ax, date_data, adjust=6):
    base = 1
    # Figure out how many years are in the data
    num_years = date_data[-1].year - date_data[0].year
    # If there are more than 10 years, we want to show every 2 years
    if num_years > adjust:
        base = 2
    ax.xaxis.set_major_locator(mdates.YearLocator(base=base))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

def replace_names(author_data):

    # Do any name replacements we might need to do.

    # For Redis, replace all instances of 'antirez' with 'Salvatore Sanfilippo'
    author_data = [author.replace('antirez', 'Salvatore Sanfilippo') for author in author_data]

    return author_data

def anonymize_names(author_data):

    unique_authors = list(set(author_data))

    # Attempt to anonymize the authors by splitting on any spaces, and turning them into initials
    anonymized_authors = []
    for i in range(len(unique_authors)):
        # split on spaces
        split = unique_authors[i].split(' ')
        # get the first letter of each split
        initials = [s[0] for s in split]
        # Make initials[0] uppercase
        initials[0] = initials[0].upper()
        # join the initials together like "JH"
        anonymized_authors.append(''.join(initials))

    # Create a map between an anonymized author and a dupe count
    anonymized_author_to_dupe_count = {}
    for i in range(len(anonymized_authors)):
        if anonymized_authors[i] not in anonymized_author_to_dupe_count.keys():
            anonymized_author_to_dupe_count[anonymized_authors[i]] = 0
        anonymized_author_to_dupe_count[anonymized_authors[i]] += 1

    # Step through the anonymized authors, and if there are any duplicates, add a number to the end
    anonymized_authors_out = []
    for i in range(len(anonymized_authors)):
        out_str = anonymized_authors[i]
        if anonymized_author_to_dupe_count[anonymized_authors[i]] > 1:
            out_str += str(anonymized_author_to_dupe_count[anonymized_authors[i]])
            anonymized_author_to_dupe_count[anonymized_authors[i]] -= 1
        anonymized_authors_out.append(out_str)

    assert len(anonymized_authors_out) == len(anonymized_authors) == len(unique_authors)

    # Create a map between the anonymized authors and the original authors (original -> anonymized)
    anonymized_author_to_author = {}
    for i in range(len(anonymized_authors_out)):
        anonymized_author_to_author[unique_authors[i]] = anonymized_authors_out[i]

    # Return the map, and then later call anonymized_author_to_author[author] to get the anonymized author
    return anonymized_author_to_author


def moving_average(series, window_size):
    window = np.ones(window_size) / window_size
    return np.convolve(series, window, 'same')


def date_check(args: dict):
    # Extract the arguments
    csv_name = args['csv_name']
    dates = args['dates']

    for i in range(len(dates) - 1):
        if dates[i] > dates[i + 1] and csv_name not in date_warning_thrown:
            print(f'Warning: The dates for {csv_name} are not in order, {dates[i]} is after {dates[i + 1]} '
                  f'({dt.datetime.fromtimestamp(int(dates[i]))} is after '
                  f'{dt.datetime.fromtimestamp(int(dates[i + 1]))})')
            print(
                f'Maybe double check the git history using something like "git rev-list --reverse -n 3" on'
                f' the offending commit to check this is intended.')
            date_warning_thrown.append(csv_name)
            return False
    return True

def get_250_timestamp(csv_name):
    ret_date = -1
    # Get the lower case name of the csv
    lowered = [(x.lower(), x) for x in commits_prev_compiling_range.keys()]
    for i in range(len(lowered)):
        if lowered[i][0] == csv_name.lower():
            ret_date = commits_prev_compiling_range[lowered[i][1]][1]
            break

    # Return the date we believe is associated with the csv
    return ret_date


def plot_vert_at_timestamp(ax, csv_name, date, round_to_month=False):
    # If we can find the legacy date, let's plot it as a vertical line
    if (legacy_date := get_250_timestamp(csv_name)) and legacy_date != -1:
        if date:
            legacy_date = dt.datetime.fromtimestamp(legacy_date)
            if round_to_month:
                # round the date to halfway through the month it is in
                legacy_date = legacy_date.replace(day=15)
        else:
            legacy_date = LEGACY_NUM_REVS
        ax.axvline(x=legacy_date, color='gray', linestyle=':')


def plot_all_individual(data, csv_name, date, savedir=None):
    if savedir is None:
        savedir = args.input
    # Plot the individual data
    plot_eloc(data, csv_name, date=date, savedir=savedir)
    plot_tloc(data, csv_name, date=date, savedir=savedir)
    plot_evolution_of_eloc_and_tloc(data, csv_name, graph_mode="zeroone", savedir=savedir)
    plot_coverage(data, csv_name, date=date, savedir=savedir)

    plot_patch_coverage(data, csv_name, bucket_no=4, savedir=savedir)
    plot_patch_coverage(data, csv_name, bucket_no=6, savedir=savedir)
    plot_bucketed_patch_coverage(data, csv_name, savedir=savedir)
    # Note plot_patch_type will operate on filtered data here so there should be no 'other' category. Filtering is turned off for combined plot.
    plot_patch_type(data, csv_name, savedir=savedir)

    plot_exit_status_rates(data, csv_name, savedir=savedir)
    # plot_timespan(data, csv_name, savedir=savedir)

    plot_churn(data, csv_name, date=date, savedir=savedir)
    plot_author_dist(data, csv_name, date=date, limit_authors=2, savedir=savedir)

    plot_coverage_line_per_author(data, csv_name, date=date, limit_authors=5, savedir=savedir)
    plot_coverage_box_per_author(data, csv_name, date=date, limit_authors=10, savedir=savedir)
    # plot_patch_coverage_over_time(data, csv_name, date=date, savedir=savedir)
    plot_average_patch_coverage_per_author(data, csv_name, limit_authors=10, savedir=savedir)
    plot_patch_coverage_bins(data, csv_name, savedir=savedir)
    plot_commit_frequency(data, csv_name, savedir=savedir)

    # non-det graphs - old data won't have this
    included_names = ['Apr_repeats', 'BinutilsGdb_repeats', 'Curl_repeats', 'Git_repeats', 'Lighttpd2_repeats',
                      'Memcached_repeats', 'Redis_repeats', 'Vim_repeats', 'Zeromq_repeats']
    if csv_name in included_names:
        plot_non_det_hist(data, csv_name, date=date, savedir=savedir)


def plot_diffcov_individual(data, csv_name, savedir=None):
    if savedir is None:
        savedir = args.input

    diffcov_figsize = (7, 7)
    plot_diffcov_hist(data, csv_name, type='line', savedir=savedir, size=diffcov_figsize)
    plot_diffcov_hist(data, csv_name, type='function', savedir=savedir, size=diffcov_figsize)
    plot_diffcov_hist(data, csv_name, type='branch', savedir=savedir, size=diffcov_figsize)

    plot_diffcov_bars(data, csv_name, type='line', savedir=savedir, size=diffcov_figsize)


def plot_diffcov_multiple(paths, csv_names, savedir=None):
    if savedir is None:
        savedir = args.input

    plot_diffcov_format_multiple(plot_diffcov_hist, 'diffcov-line', paths, csv_names, type='line')
    plot_diffcov_format_multiple(plot_diffcov_hist, 'diffcov-function', paths, csv_names, type='function')
    plot_diffcov_format_multiple(plot_diffcov_hist, 'diffcov-branch', paths, csv_names, type='branch')

    plot_diffcov_format_combined(plot_diffcov_bars, 'diffcov-line-compressed', paths, csv_names, type='line',
                                 custom_figsize=(9, 9))


def plot_diffcov_format_multiple(metric, outname, paths, csv_names, **kwargs):
    """ Plot a metric for multiple CSVs on subplots of the same figure. """
    # Would be nice to have a smarter way of doing this, but for now we'll just hardcode the number of rows and columns
    rows, columns = 2, 3
    size = DEFAULT_FIGSIZE
    if len(csv_names) > rows * columns:
        rows, columns = 3, 3
        size = EXPANDED_FIGSIZE
    fig, axs = plt.subplots(rows, columns, figsize=size)
    idxs = (0, 0)
    for i in range(len(csv_names)):
        diffcov_data = utils.extract_diffcov_data(paths[i], csv_names[i])
        if diffcov_data is not None:
            metric(diffcov_data, csv_names[i], plot=(fig, axs[idxs]), save=False, **kwargs)
            # Wrap around the indexs or increment
            idxs = (idxs[0], idxs[1] + 1)
            if idxs[1] >= columns:
                idxs = (idxs[0] + 1, 0)

    fig.tight_layout()
    fig.subplots_adjust(top=0.92)
    fig.savefig(f'postprocessing/graphs/{args.input}/{outname}.png', bbox_inches='tight', dpi=300)
    print(f'Finished plotting combined {outname}. You can find the plots in graphs/{args.input}')


def plot_diffcov_format_combined(metric, outname, paths, csv_names, **kwargs):
    """ Plot a metric for multiple CSVs on subplots of the same figure. """
    custom_figsize = kwargs.get('custom_figsize', None)
    if custom_figsize is not None:
        del kwargs['custom_figsize']
    fig, axs = plt.subplots(figsize=custom_figsize if custom_figsize is not None else EXPANDED_FIGSIZE)
    for i in range(len(csv_names)):
        diffcov_data = utils.extract_diffcov_data(paths[i], csv_names[i])
        if diffcov_data is not None:
            metric(diffcov_data, csv_names[i], plot=(fig, axs), save=False, pos=i, multiple=True, **kwargs)

    fig.tight_layout()
    fig.savefig(f'postprocessing/graphs/{args.input}/{outname}.png', bbox_inches='tight', dpi=300)
    print(f'Finished plotting combined {outname}. You can find the plots in graphs/{args.input}')


def plot_all_multiple(paths, csv_names, date, limit=None):
    # Plot each of the combined graphs
    plot_metric_multiple(plot_eloc, 'eloc', paths, csv_names, date=date, custom_figsize=(10, 10), limit=limit)
    plot_metric_multiple(plot_tloc, 'tloc', paths, csv_names, date=date, custom_figsize=(10, 10), limit=limit)
    plot_metric_multiple(plot_evolution_of_eloc_and_tloc, 'evolution_of_eloc_and_tloc', paths, csv_names, date=date,
                         custom_figsize=(10, 10), limit=limit)
    plot_metric_multiple(plot_coverage, 'coverage', paths, csv_names, date=date, custom_figsize=(9, 11), limit=limit)

    plot_metric_multiple(plot_average_patch_coverage_per_author, 'average_patch_coverage_per_author', paths, csv_names,
                         limit_authors=10, limit=limit)
    plot_metric_multiple(plot_patch_coverage_bins, 'patch_coverage_bins', paths, csv_names, limit=limit)
    plot_metric_multiple(plot_commit_frequency, 'commit_frequency', paths, csv_names, limit=limit)

    # TODO: do a plot_metric_multiple for the non-det graphs (so only for the ones that have non-det data)

    # The combined graphs for patch coverage and patch type are a bit different - they need to be plotted on the same graph rather than subplots
    plot_metric_combined(plot_patch_coverage, 'patch_coverage', paths, csv_names, custom_figsize=(10, 9), bucket_no=4, limit=limit)
    plot_metric_combined(plot_patch_coverage, 'patch_coverage', paths, csv_names, custom_figsize=(10, 9), bucket_no=6, weighted=False,
                         limit=limit)
    plot_metric_combined(plot_patch_coverage, 'patch_coverage', paths, csv_names, custom_figsize=(10, 9), bucket_no=6, weighted=True,
                         limit=limit)
    plot_metric_combined(plot_bucketed_patch_coverage, 'bucketed_patch_coverage', paths, csv_names, custom_figsize=(15, 7),
                         limit=limit, reverse=True)
    plot_metric_combined(plot_bucketed_patch_coverage, 'bucketed_patch_coverage', paths, csv_names,
                         custom_figsize=(15, 7),
                         limit=limit, reverse=True, weighted=True)

    # Both patch type and exit status rates don't filter the data to only include revisions that modify code and/or tests
    plot_metric_combined(plot_patch_type, 'patch_type-absolute', paths, csv_names, custom_figsize=(10, 9), limit=limit,
                         no_filter=True, proportional=False)
    plot_metric_combined(plot_patch_type, 'patch_type', paths, csv_names, custom_figsize=(10, 9), limit=limit, no_filter=True, proportional=True)

    plot_metric_combined(plot_exit_status_rates, 'exit_status_rates', paths, csv_names, custom_figsize=(10, 9), limit=limit, no_filter=True)
    plot_metric_combined(plot_timespan, 'timespan', paths, csv_names, custom_figsize=(10, 7), labels=csv_names,
                         commits_prev_compiling_range=commits_prev_compiling_range, dpi=300, limit=limit)

    paths, csv_names = utils.filter_to_non_det_supported(paths, csv_names)

    # Plot the non-det graphs
    plot_metric_multiple(plot_non_det_hist, 'non_det_hist', paths, csv_names, date=date, limit=limit)


def plot_metric_multiple(metric, outname, paths, csv_names, **kwargs):
    """ Plot a metric for multiple CSVs on subplots of the same figure. """
    # Would be nice to have a smarter way of doing this, but for now we'll just hardcode the number of rows and columns
    rows, columns = 2, 3
    # extract var custom_figsize from kwargs, if it exists
    custom_figsize = kwargs.get('custom_figsize', None)
    if custom_figsize is not None:
        del kwargs['custom_figsize']
    else:
        custom_figsize = DEFAULT_FIGSIZE
    limit = kwargs.get('limit', None)
    del kwargs['limit']
    if len(csv_names) > rows * columns:
        rows, columns = 3, 3
    fig, axs = plt.subplots(rows, columns, figsize=custom_figsize)
    idxs = (0, 0)
    for i in range(len(csv_names)):
        csv_data = utils.extract_data(f'{paths[i]}', csv_names[i], callback=date_check)
        # Filter the data to only include revisions that modify executable code or test files
        csv_data, _ = utils.filter_data_by_exec_test(csv_data)
        if limit is not None:
            csv_data = csv_data[-limit:]
        if csv_data is not None:
            metric(csv_data, csv_names[i], plot=(fig, axs[idxs]), save=False, **kwargs)
            # Wrap around the indexs or increment
            idxs = (idxs[0], idxs[1] + 1)
            if idxs[1] >= columns:
                idxs = (idxs[0] + 1, 0)

    fig.tight_layout()
    fig.subplots_adjust(top=0.92)
    # Check if kwargs contains date, if so, add it to the filename
    date = kwargs.get('date', False)
    fig.savefig(f'postprocessing/graphs/{args.input}/{outname}{"-date" if date else ""}.png', bbox_inches='tight',
                dpi=300)
    print(f'Finished plotting combined {outname}. You can find the plots in graphs/{args.input}')
    # Close the figure to free up memory
    plt.close(fig)


def plot_metric_combined(metric, outname, paths, csv_names, **kwargs):
    """ Plot a metric for multiple CSVs on the same graph of a figure. """
    # extract var custom_figsize from kwargs, if it exists
    custom_figsize = kwargs.get('custom_figsize', None)
    dpi = kwargs.get('dpi', None)
    if custom_figsize is not None:
        del kwargs['custom_figsize']
    limit = kwargs.get('limit', None)
    del kwargs['limit']
    if dpi is not None:
        del kwargs['dpi']
    no_filter = kwargs.get('no_filter', None)
    if no_filter is not None:
        del kwargs['no_filter']
    # Reverse is useful if we want to plot the graphs in reverse order (e.g. for timespan)
    reverse = kwargs.get('reverse', None)
    if reverse is not None:
        del kwargs['reverse']
        paths = paths[::-1]
        csv_names = csv_names[::-1]
    fig, axs = plt.subplots(figsize=custom_figsize if custom_figsize is not None else EXPANDED_FIGSIZE)
    for i in range(len(csv_names)):
        csv_data = utils.extract_data(f'{paths[i]}', csv_names[i], callback=date_check)
        # Filter the data to only include revisions that modify executable code or test files (don't filter for patch type)
        if no_filter is None and limit is None:
            # i.e. if we are allowed to filter and we are not limiting the number of revisions, then only filter
            csv_data, _ = utils.filter_data_by_exec_test(csv_data)
        if no_filter is not None and limit is not None:
            # i.e. if we are not allowed to filter and we are limiting the number of revisions, then filter and limit
            # by getting the nth (reversed) exec/test-changing rev, then working forward until the end
            csv_data_filtered, idxs = utils.filter_data_by_exec_test(csv_data)
            if limit > len(idxs):
                limit = len(idxs)
            first_idx = idxs[-limit]
            # Print out the timestamp at first_idx
            print(f"{csv_names[i]} starts at: {csv_data[first_idx][config.file_header_list.index('time')]}")
            csv_data = csv_data[first_idx:]
        if no_filter is None and limit is not None:
            # We are allowed to filter, and allowed to limit
            csv_data, _ = utils.filter_data_by_exec_test(csv_data)
            csv_data = csv_data[-limit:]
        if csv_data is not None:
            metric(csv_data, csv_names[i], plot=(fig, axs), save=False, pos=i, multiple=True, **kwargs)

    # Check if kwargs contains date, if so, add it to the filename
    date = kwargs.get('date', False)
    bucket_no = kwargs.get('bucket_no', None)
    weighted = kwargs.get('weighted', False)
    fig.savefig(
        f'postprocessing/graphs/{args.input}/{outname}{"-date" if date else ""}{bucket_no if bucket_no is not None else ""}{"-weighted" if weighted else ""}.png',
        bbox_inches='tight', dpi=dpi)
    print(
        f'Finished plotting combined {outname}{"-date" if date else ""}. You can find the plots in graphs/{args.input}')


if __name__ == '__main__':
    import os
    import argparse
    import math
    import glob
    import shutil

    # argparse the location of the input file (e.g. remotedata/apr/Apr.csv)
    parser = argparse.ArgumentParser()
    # argparse for either an input file or a directory
    parser.add_argument('input', help='The input file or directory to process')
    # add a directory option so if --dir is present, the input is a directory, otherwise it is a file
    parser.add_argument('--dir', action='store_true',
                        help='The input is a directory (dir/repo1/*.csv, dir/repo2/*.csv)')
    # add a byDate option so if --date is present, the X axis is time, otherwise it is revision number
    parser.add_argument('--date', action='store_true', help='Plot by date')
    # add an arg to do diffcov plots
    parser.add_argument('--diffcov', action='store_true', help='Plot diffcov plots')
    # add an arg to limit the number of commits to plot
    parser.add_argument('--limit', type=int, help='Limit the number of commits to plot')

    args = parser.parse_args()

    if args.dir:
        # Make sure the input is a directory
        if not os.path.isdir(args.input):
            raise NotADirectoryError(f'{args.input} is not a directory')

        # Strip trailing slash
        if args.input[-1] == '/':
            args.input = args.input[:-1]

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

        # Make sure we have at least one CSV file
        if len(paths) == 0:
            raise FileNotFoundError(f'No CSV files found in {args.input}')

        paths = [x for x in paths if x in included_paths]

        # Make sure no paths include the #diffcov directory
        paths = [x for x in paths if 'diffcov_' not in x]

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
        diffcov_names = []
        diffcov_paths = []

        print(f'Paths: {paths}')
        # Print the names of the CSV files
        print(f'CSV names: {csv_names}')
        print("=====================================================")
        for i in range(len(csv_names)):
            # Make the directory /graphs if it doesn't exist
            if not os.path.exists('postprocessing/graphs'):
                os.makedirs('postprocessing/graphs')

            # Make the directory /graphs/{args.input} if it doesn't exist
            if not os.path.exists(f'postprocessing/graphs/{args.input}'):
                os.makedirs(f'postprocessing/graphs/{args.input}')

            # Make the directory for the graphs if it doesn't exist
            if not os.path.exists(f'postprocessing/graphs/{args.input}/{csv_names[i]}'):
                os.makedirs(f'postprocessing/graphs/{args.input}/{csv_names[i]}')

            search_dir = None

            csv_data = utils.extract_data(f'{paths[i]}', csv_names[i], callback=date_check)
            csv_data, _ = utils.filter_data_by_exec_test(csv_data)
            if args.limit:
                csv_data = csv_data[-args.limit:]
            if csv_data is not None:
                plot_all_individual(csv_data, csv_names[i], date=args.date)
                print(
                    f'Finished plotting {csv_names[i]}. You can find the plots in graphs/{args.input}/{csv_names[i]}')
                search_dir = os.path.dirname(paths[i])
            else:
                # Replace paths[i] and csv_names[i] with None so that they are not plotted
                paths[i] = None
                csv_names[i] = None

            # if diffcov arg and diffcov dir exists, plot diffcov plots
            if args.diffcov and search_dir is not None:
                # Try to find a csv file in the same directory with name diffcov_*.csv
                diffcov_csv = glob.glob(f'{search_dir}/diffcov_*.csv')
                if len(diffcov_csv) == 0:
                    print(f'No diffcov csv found for {csv_names[i]}')
                else:
                    diffcov_csv = diffcov_csv[0]
                    diffcov_data = utils.extract_diffcov_data(diffcov_csv, csv_names[i])
                    if diffcov_data is not None:
                        plot_diffcov_individual(diffcov_data, csv_names[i], savedir=args.input)
                        diffcov_paths.append(diffcov_csv)
                        diffcov_names.append(csv_names[i])

        # Now remove the None values from the lists
        paths = [x for x in paths if x is not None]
        csv_names = [x for x in csv_names if x is not None]

        # Plots that will need subplots: eloc, tloc, eloc/tloc co-evolution, coverage.
        # Plots that are to be plotted on the same graph: patch coverage, patch types.
        # Plots that are to be plotted on their own: churn.

        print("------------------------------------------")
        print("Now plotting combined graphs...")

        # Plot all repos' eloc on the same graph
        plot_all_multiple(paths, csv_names, date=args.date, limit=args.limit)
        diffcov_csvs = glob.glob(f'{args.input}/*/diffcov_*.csv')
        if args.diffcov:
            plot_diffcov_multiple(diffcov_paths, diffcov_names)

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
        directory = os.path.dirname(args.input)
        subdir = None
        search_dir = None
        splitdir = directory.split('/')

        # only keep the last part of the directory
        if len(splitdir) > 1:
            directory = splitdir[-2]
            subdir = splitdir[-1]
        else:
            directory = splitdir[-1]

        search_dir = directory

        if subdir is not None:
            search_dir = f'{directory}/{subdir}'

        # Remove the .csv extension
        csv_name = csv_name[:-4]

        # Make the directory /graphs if it doesn't exist
        if not os.path.exists('postprocessing/graphs'):
            os.makedirs('postprocessing/graphs')

        # Make the directory /graphs/{args.input} if it doesn't exist
        if not os.path.exists(f'postprocessing/graphs/{directory}'):
            os.makedirs(f'postprocessing/graphs/{directory}')

        # Make the directory for the graphs if it doesn't exist
        if not os.path.exists(f'postprocessing/graphs/{directory}/{csv_name}'):
            os.makedirs(f'postprocessing/graphs/{directory}/{csv_name}')

        data = utils.extract_data(args.input, csv_name, callback=date_check)
        data, _ = utils.filter_data_by_exec_test(data)

        if args.limit:
            data = data[-args.limit:]

        plot_all_individual(data, csv_name, date=args.date, savedir=directory)

        if args.diffcov:
            # Try to find a csv file in the same directory with name diffcov_*.csv
            diffcov_csv = glob.glob(f'{search_dir}/diffcov_*.csv')
            if len(diffcov_csv) == 0:
                print(f'No diffcov csv found for {csv_name}')
            else:
                diffcov_csv = diffcov_csv[0]
                diffcov_data = utils.extract_diffcov_data(diffcov_csv, csv_name)
                if diffcov_data is not None:
                    plot_diffcov_individual(diffcov_data, csv_name, savedir=directory)

        print("=====================================================")
        print(f'Finished plotting {csv_name}. You can find the plots in graphs/{csv_name}')

    if args.dir:
        path = args.input
    else:
        path = directory

    # Create a directory for the graphs if it doesn't exist
    if not os.path.exists(f'graphs/{path}'):
        os.makedirs(f'graphs/{path}')

    # Move all the png files to the graphs directory
    for file in glob.glob(f'postprocessing/graphs/{path}/*/*.png'):
        # Get the name of the file and the directory it is in
        filename = os.path.basename(file)
        directory = os.path.dirname(file)

        # only keep the last part of the directory
        directory = directory.split('/')[-1]

        # Create the directory in the graphs directory if it doesn't exist
        if not os.path.exists(f'graphs/{path}/{directory}'):
            os.makedirs(f'graphs/{path}/{directory}')

        # Move the file to the graphs directory
        shutil.move(file, f'graphs/{path}/{directory}/{filename}')

        # Remove all empty directories in the postprocessing/graphs/{path} directory
        if not os.listdir(f'postprocessing/graphs/{path}/{directory}'):
            os.rmdir(f'postprocessing/graphs/{path}/{directory}')

    # Move all the combined png files to the graphs directory
    for file in glob.glob(f'postprocessing/graphs/{path}/*.png'):
        # Get the name of the file and the directory it is in
        filename = os.path.basename(file)

        # Move the file to the graphs directory
        shutil.move(file, f'graphs/{path}/{filename}')

    # Remove postprocessing/graphs/{path} directory if it is empty
    if not os.listdir(f'postprocessing/graphs/{path}'):
        os.rmdir(f'postprocessing/graphs/{path}')

    print("All done!")
