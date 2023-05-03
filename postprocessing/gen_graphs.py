# Globals that tell the script the layout of the csv files
from matplotlib import pyplot as plt
# Config for the csv files' layout (edit as necessary)
import internal.csv_config as config
import internal.csv_utils as utils

# Remove any # or *s from the file_header after splitting by string
file_header_list = config.file_header_list

# Create a map to hold the type of each column
file_header_type = config.file_header_type

# Other globals
output_location = 'postprocessing/graphs/'
default_figsize = (11, 11)
expanded_figsize = (15, 15)
date_warning_thrown = []


def plot_eloc(data, csv_name, save=True, date=False, plot=None, savedir=None):
    if plot is None:
        plot = plt.subplots(figsize=default_figsize)
    (fig, ax) = plot
    # Clean the data to ignore rows with exits "EmptyCommit", "NoCoverage" or "compileError"
    cleaned_data = utils.clean_data(data)

    # Use utils.get_columns to get the eloc and time data from data
    eloc_data, dates = utils.get_columns(cleaned_data, ['eloc', 'time'])

    # Plot the eloc data against the dates as small dots
    if date:
        ax.plot(dates, eloc_data, '+', markersize=5)
        ax.tick_params(axis='x', rotation=45)
        ax.set_xlim(dates[0], dates[-1])
    else:
        ax.plot(eloc_data, '+', markersize=5)
        ax.set_xlabel('Revision')
        ax.set_xlim(0, len(eloc_data))
    # Label the axes, do not show xticks
    ax.set_ylabel('ELOC')
    ax.set_ylim(0, math.ceil(max(eloc_data) / 500) * 500)
    # Title the plot
    ax.set_title(f'{csv_name}')

    # Use locator_params to make the y axis have 10 ticks
    ax.locator_params(axis='y', nbins=10)

    # Save the plot
    if save:
        ax.set_title(f'ELOC over time for {csv_name}')
        fig.savefig(f'postprocessing/graphs/{savedir}/{csv_name}/{csv_name}-eloc{"-date" if date else ""}.png',
                    bbox_inches='tight')
        # Close the figure to save memory (if we're saving, we do not need to keep the figure in memory)
        plt.close(fig)


def plot_tloc(data, csv_name, save=True, date=False, plot=None, savedir=None):
    if plot is None:
        plot = plt.subplots(figsize=default_figsize)
    (fig, ax) = plot
    # Clean the data to ignore rows with exits "EmptyCommit", "NoCoverage" or "compileError"
    cleaned_data = utils.clean_data(data)

    # Get the tloc and time data from data
    tloc_data, dates = utils.get_columns(cleaned_data, ['testsize', 'time'])

    # Plot the eloc data against the dates as small dots
    if date:
        ax.plot(dates, tloc_data, '+', markersize=5, color='red')
        ax.tick_params(axis='x', rotation=45)
        ax.set_xlim(left=dates[0], right=dates[-1])
    else:
        ax.plot(tloc_data, '+', markersize=5, color='red')
        ax.set_xlabel('Revision')
        ax.set_xlim(left=0, right=len(tloc_data))
    # Label the axes, do not show xticks
    ax.set_ylabel('TLOC')
    ax.set_ylim(bottom=0, top=math.ceil(max(tloc_data) / 100) * 100)
    # Title the plot
    ax.set_title(f'{csv_name}')

    # Use locator_params to make the y axis have 10 ticks
    ax.locator_params(axis='y', nbins=10)

    # Save the plot
    if save:
        ax.set_title(f'Test LOC over time for {csv_name}')
        fig.savefig(f'postprocessing/graphs/{savedir}/{csv_name}/{csv_name}-tloc{"-date" if date else ""}.png',
                    bbox_inches='tight')
        plt.close(fig)


def plot_evolution_of_eloc_and_tloc(data, csv_name, save=True, graph_mode="zeroone", date=False,
                                    plot=None, savedir=None):
    if plot is None:
        plot = plt.subplots(figsize=default_figsize)
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
    # Draw a grid
    ax.grid()

    # Label the x axis as Commits (i.e. the number of commits)
    ax.set_xlabel('Commits')

    ax.legend(['Code', 'Test'], loc='upper left')

    # Save the plot
    if save:
        ax.set_title(f'Co-evolution of executable and test code for {csv_name}')
        fig.savefig(f'postprocessing/graphs/{savedir}/{csv_name}/{csv_name}-evolution{"-date" if date else ""}.png',
                    bbox_inches='tight')
        plt.close(fig)


def plot_coverage(data, csv_name, save=True, date=False, plot=None, savedir=None):
    if plot is None:
        plot = plt.subplots(figsize=default_figsize)
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
        ax.plot(corresponding_dates, line_coverage, '+', markersize=5)
        ax.plot(corresponding_dates, br_coverage, 'x', markersize=5, color='red')
        ax.tick_params(axis='x', rotation=45)
        ax.set_xlim(left=dates[0], right=dates[-1])
    else:
        ax.plot(line_coverage, '+', markersize=5)
        ax.plot(br_coverage, 'x', markersize=5, color='red')
        ax.set_xlabel('Revision')
        ax.set_xlim(left=0, right=len(dates))

    # Set the y axis from 0 to 100
    ax.set_ylim(bottom=0, top=100)

    # Label the y axis as Coverage
    ax.set_ylabel('Coverage (%)')

    # Give the plot a title
    ax.set_title(f'{csv_name}')

    # Print the legend
    ax.legend(['Line Coverage', 'Branch Coverage'])

    # Save the plot
    if save:
        ax.set_title(f'Coverage for {csv_name}')
        fig.savefig(f'postprocessing/graphs/{savedir}/{csv_name}/{csv_name}-coverage{"-date" if date else ""}.png',
                    bbox_inches='tight')
        plt.close(fig)


def plot_churn(data, csv_name, save=True, date=False, plot=None, savedir=None):
    if plot is None:
        plot = plt.subplots(figsize=default_figsize)
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
        ax.plot(corresponding_dates, churn_list, '+', markersize=5)
        ax.tick_params(axis='x', rotation=45)
    else:
        ax.plot(churn_list, '+', markersize=5)
        ax.set_xlabel('Revision')

    # Label the y axis as Churn
    ax.set_ylabel('Churn')

    # Give the plot a title
    ax.set_title(f'{csv_name}')

    # Save the plot
    if save:
        ax.set_title(f'Churn for {csv_name}')
        fig.savefig(f'postprocessing/graphs/{savedir}/{csv_name}/{csv_name}-churn{"-date" if date else ""}.png',
                    bbox_inches='tight')
        plt.close(fig)


def plot_patch_coverage(data, csv_name, save=True, bucket_no=6, plot=None, pos=0, multiple=False, savedir=None):
    if plot is None:
        plot = plt.subplots(figsize=default_figsize)
    (fig, ax) = plot
    # Clean the data to ignore rows with exits "EmptyCommit", "NoCoverage" or "compileError"
    cleaned_data = utils.clean_data(data)

    # Get the coverage data using eloc_data, coverage_data, branch_data, branch_coverage_data and dates
    covered_lines_data, not_covered_lines_data = utils.get_columns(cleaned_data, ['covlines', 'notcovlines'])

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

    colours = ["#ad302e", "#de5434", "#e9923e", "#f8cc47", "#8bb954", "#428f4d"]
    if bucket_no == covrig_buckets:
        colours = ["#ffffff", "#bd2121", "#ffba0f", "#c9ff70", "#4d9b00", "#ffffff"]

    # Plot the data as a stacked vertical bar chart
    cumulative_total = 0
    idx = 0
    for bucket_p in bucket_percentages:
        ax.bar(csv_name if multiple else 0, bucket_p, bottom=cumulative_total, label=bucket_names[idx], width=0.5,
               color=colours[idx],
               edgecolor='black', zorder=3)
        cumulative_total += bucket_p
        idx += 1

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
        ax.set_title(f'Patch Coverage across projects')

    # Print the legend with the bucket names [0%, 25%], (25%, 50%], (50%, 75%], (75%, 100%]
    # or if we are in large scale mode (0%, 25%], (25%, 50%], (50%, 75%], (75%, 100%], 0%, 100%

    # Do plt.legend(bucket_names) but in reverse order
    handles, labels = ax.get_legend_handles_labels()

    # if we are in covrig mode, do not plot the 0% and 100% buckets. Only print the legend once
    if pos == 0:
        if bucket_no == covrig_buckets:
            # Move the legend to the side
            ax.legend(handles[::-1][1:5], labels[::-1][1:5], bbox_to_anchor=(1.05, 1), loc='upper left')
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


def plot_patch_type(data, csv_name, save=True, plot=None, pos=0, multiple=False, savedir=None):
    if plot is None:
        plot = plt.subplots(figsize=default_figsize)
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

    # Plot the data as a stacked vertical bar chart
    cumulative_total = 0
    idx = 0
    for patch_type in patch_types:
        ax.bar(csv_name if multiple else 0, patch_types[patch_type], bottom=cumulative_total, label=patch_type,
               width=0.5,
               color=patch_type_colours[idx], edgecolor='black', zorder=3)
        cumulative_total += patch_types[patch_type]
        idx += 1

    # Turn off ticks for the x axis
    if not multiple:
        ax.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)
        ax.set_xlim(-1, 1)

    # Label the y axis as Number of Patches
    ax.set_ylabel('Number of Patches')

    # Give the plot a title
    if not multiple:
        ax.set_title(f'{csv_name}')
    else:
        ax.set_title(f'Patch Types across projects')

    # Print the legend with the patch type names
    if pos == 0:
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles[::-1], labels[::-1], bbox_to_anchor=(1.05, 1), loc='upper left')

    # Make it a dotted grid
    ax.grid(linestyle='dotted', zorder=0, axis='y')

    # Save the plot
    if save:
        ax.set_title(f'Patch Types for {csv_name}')
        fig.savefig(f'postprocessing/graphs/{savedir}/{csv_name}/{csv_name}-patch-types.png', bbox_inches='tight')
        plt.close(fig)


def plot_author_dist(data, csv_name, save=True, date=False, plot=None, limit=5, savedir=None):
    if plot is None:
        plot = plt.subplots(figsize=default_figsize)
    (fig, ax) = plot
    # Clean the data to ignore rows with exits "EmptyCommit", "NoCoverage" or "compileError"
    cleaned_data = utils.clean_data(data)

    author, added_lines, dates = utils.get_columns(cleaned_data, ['author', 'addedlines', 'time'])

    # Get the unique authors
    unique_authors = list(set(author))

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
        commits_per_author[author[i]] += 1
        lines_added_per_author[author[i]] += added_lines[i]

    # look at dictionary and remove authors with less than <limit> commits
    for key in list(commits_per_author.keys()):
        if commits_per_author[key] < limit:
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
        plot = plt.subplots(figsize=default_figsize)
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
        ax.bar(csv_name if multiple else 0, commits_per_exit_status[exit_status], bottom=cumulative_total,
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
        ax.set_title(f'Number of Commits per Exit Status for {csv_name}')
    else:
        ax.set_title(f'Number of Commits per Exit Status')

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


def date_check(args: dict):
    # Extract the arguments
    csv_name = args['csv_name']
    dates = args['dates']

    for i in range(len(dates) - 1):
        if dates[i] > dates[i + 1] and csv_name not in date_warning_thrown:
            print(f'Warning: The dates for {csv_name} are not in order, {dates[i]} is after {dates[i + 1]} '
                  f'({datetime.datetime.fromtimestamp(int(dates[i]))} is after '
                  f'{datetime.datetime.fromtimestamp(int(dates[i + 1]))})')
            print(
                f'Maybe double check the git history using something like "git rev-list --reverse -n 3" on'
                f' the offending commit to check this is intended.')
            date_warning_thrown.append(csv_name)
            return False
    return True


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
    plot_patch_type(data, csv_name, savedir=savedir)

    plot_exit_status_rates(data, csv_name, savedir=savedir)

    plot_churn(data, csv_name, date=date, savedir=savedir)
    plot_author_dist(data, csv_name, date=date, limit=2, savedir=savedir)


def plot_all_multiple(paths, csv_names, date):
    # Plot each of the combined graphs
    plot_metric_multiple(plot_eloc, 'eloc', paths, csv_names, date=date)
    plot_metric_multiple(plot_tloc, 'tloc', paths, csv_names, date=date)
    plot_metric_multiple(plot_evolution_of_eloc_and_tloc, 'evolution_of_eloc_and_tloc', paths, csv_names, date=date)
    plot_metric_multiple(plot_coverage, 'coverage', paths, csv_names, date=date)

    # The combined graphs for patch coverage and patch type are a bit different - they need to be plotted on the same graph rather than subplots
    plot_metric_combined(plot_patch_coverage, 'patch_coverage', paths, csv_names, bucket_no=4)
    plot_metric_combined(plot_patch_coverage, 'patch_coverage', paths, csv_names, bucket_no=6)
    plot_metric_combined(plot_patch_type, 'patch_type', paths, csv_names)

    plot_metric_combined(plot_exit_status_rates, 'exit_status_rates', paths, csv_names)


def plot_metric_multiple(metric, outname, paths, csv_names, **kwargs):
    """ Plot a metric for multiple CSVs on subplots of the same figure. """
    # Would be nice to have a smarter way of doing this, but for now we'll just hardcode the number of rows and columns
    rows, columns = 2, 3
    size = default_figsize
    if len(csv_names) > rows * columns:
        rows, columns = 3, 4
        size = expanded_figsize
    fig, axs = plt.subplots(rows, columns, figsize=size)
    idxs = (0, 0)
    for i in range(len(csv_names)):
        csv_data = utils.extract_data(f'{paths[i]}', csv_names[i], callback=date_check)
        if csv_data is not None:
            metric(csv_data, csv_names[i], plot=(fig, axs[idxs]), save=False, **kwargs)
            # Wrap around the indexs or increment
            idxs = (idxs[0], idxs[1] + 1)
            if idxs[1] >= columns:
                idxs = (idxs[0] + 1, 0)

    fig.tight_layout()
    # Check if kwargs contains date, if so, add it to the filename
    date = kwargs.get('date', False)
    fig.savefig(f'postprocessing/graphs/{args.input}/{outname}{"-date" if date else ""}.png', bbox_inches='tight')
    print(f'Finished plotting combined {outname}. You can find the plots in graphs/{args.input}')


def plot_metric_combined(metric, outname, paths, csv_names, **kwargs):
    """ Plot a metric for multiple CSVs on the same graph of a figure. """
    fig, axs = plt.subplots(figsize=expanded_figsize)
    for i in range(len(csv_names)):
        csv_data = utils.extract_data(f'{paths[i]}', csv_names[i], callback=date_check)
        if csv_data is not None:
            metric(csv_data, csv_names[i], plot=(fig, axs), save=False, pos=i, multiple=True, **kwargs)

    # Check if kwargs contains date, if so, add it to the filename
    date = kwargs.get('date', False)
    bucket_no = kwargs.get('bucket_no', None)
    fig.savefig(
        f'postprocessing/graphs/{args.input}/{outname}{"-date" if date else ""}{bucket_no if bucket_no is not None else ""}.png',
        bbox_inches='tight')
    print(
        f'Finished plotting combined {outname}{"-date" if date else ""}. You can find the plots in graphs/{args.input}')


if __name__ == '__main__':
    import os
    import argparse
    import math
    import datetime
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

    args = parser.parse_args()

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

            csv_data = utils.extract_data(f'{paths[i]}', csv_names[i], callback=date_check)
            if csv_data is not None:
                plot_all_individual(csv_data, csv_names[i], date=args.date)
                print(
                    f'Finished plotting {csv_names[i]}. You can find the plots in graphs/{args.input}/{csv_names[i]}')
            else:
                # Replace paths[i] and csv_names[i] with None so that they are not plotted
                paths[i] = None
                csv_names[i] = None

        # Now remove the None values from the lists
        paths = [x for x in paths if x is not None]
        csv_names = [x for x in csv_names if x is not None]

        # Plots that will need subplots: eloc, tloc, eloc/tloc co-evolution, coverage.
        # Plots that are to be plotted on the same graph: patch coverage, patch types.
        # Plots that are to be plotted on their own: churn.

        print("------------------------------------------")
        print("Now plotting combined graphs...")

        # Plot all repos' eloc on the same graph
        plot_all_multiple(paths, csv_names, date=args.date)

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

        # only keep the last part of the directory
        if len(directory.split('/')) > 1:
            directory = directory.split('/')[-2]
        else:
            directory = directory.split('/')[-1]
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

        plot_all_individual(data, csv_name, date=args.date, savedir=directory)

        print("=====================================================")
        print(f'Finished plotting {csv_name}. You can find the plots in graphs/{args.input}/{csv_name}')

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
