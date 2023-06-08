import csv
import os
import statistics
from scipy.stats import levene, chisquare

# Config for the csv files' layout (edit as necessary)
import internal.csv_config as config
import internal.csv_utils as utils

# Same as in gen_graphs but for commits. Would be nice to automate this or have shared in the config file
commits_prev_operating_range = {
    'Apr': (None, None),
    'Binutils': ('3d62a77', '2b9ed0a'),
    'Curl': (None, None),
    'Git': ('001d116', '694a88a'),
    'Lighttpd': ('c972bea', '0d40b25'),
    'Lighttpd2': ('c972bea', '0d40b25'),
    'Memcached': ('d9220d6', 'f99755c'),
    'Redis': ('011fa89', '3c9bb87'),
    'Vim': (None, None),
    'Zeromq': ('36bfaaa', '573d7b0'),
}


# Commands run:
# python3 postprocessing/compare_csv.py jun2015data/Binutils/Binutils.csv remotedata/binutils/Binutils_all.csv --limit 250
# python3 postprocessing/compare_csv.py jun2015data/Git/Git.csv remotedata/git/Git_all.csv --limit 250
# python3 postprocessing/compare_csv.py jun2015data/Lighttpd-gnutls/Lighttpd.csv remotedata/lighttpd2/Lighttpd2_nr.csv --limit 250
# python3 postprocessing/compare_csv.py jun2015data/Memcached/Memcached.csv remotedata/memcached/Memcached_all.csv --limit 250
# python3 postprocessing/compare_csv.py jun2015data/Redis/Redis.csv remotedata/redis/tmp/Redis_all_rep_no_non_det_stats.csv --limit 250
# python3 postprocessing/compare_csv.py jun2015data/Zeromq/Zeromq.csv remotedata/zeromq/Zeromq.csv --limit 250

# No libsodium comparison
# python3 postprocessing/compare_csv.py jun2015data/Zeromq/Zeromq.csv remotedata/zeromq-no-ls/Zeromq_no_ls.csv --limit 250
def compare_csv(data1, data2):
    # Create an array to store the differences for each column
    # Work with file_header_list_v1 since Covrig data is in v1 format
    differences = [0] * len(config.file_header_list_v1)
    differences_data = [[0 for i in range(len(config.file_header_list_v1))] for j in range(len(data1))]

    # Go through each row and each column and compare the values
    for i in range(len(data1)):
        for j in range(len(data1[i])):
            # Use file_header_list_v1 to get the column name
            col_name = config.file_header_list_v1[j]
            # Get the value from the two files and convert it to the correct type
            val1 = config.file_header_type[col_name](data1[i][j])
            val2 = config.file_header_type[col_name](data2[i][j])

            # Get the type of the value from file_header_type
            val_type = config.file_header_type[col_name].__name__

            # If the value is an int or a float, compute the difference
            val_difference = 0
            if val_type == 'int' or val_type == 'float':
                val_difference = abs(val1 - val2)
            elif val_type == 'str':
                val_difference = 10 if val1 != val2 else 0
            else:
                print(f'Unknown type {val_type} for column {col_name}')

            # Update the difference for this column
            differences[j] += val_difference
            differences_data[i][j] = val_difference

    # Compute the average difference for each column with a map
    avg_differences = list(map(lambda x: x / len(data1), differences))

    return avg_differences, differences_data


def calculate_variance_for_columns(data, column_idxs):
    # Calculate the variance for each column supplied in data
    variances = [0] * len(column_idxs)

    # For each column in data given by column_idxs, calculate the variance
    for i in range(len(column_idxs)):
        # Get the column index
        col_idx = column_idxs[i]
        # Get the column data
        col_data = [data[j][col_idx] for j in range(len(data))]
        # Convert the data to the correct type
        this_type = config.file_header_type[config.file_header_list_v1[col_idx]]
        col_data = list(map(this_type, col_data))
        # If the type is a string, continue
        if this_type == str:
            variances[i] = -1
            continue
        # Calculate the variance
        variances[i] = statistics.variance(col_data)

    return variances


def levenes_test(data1, data2, column_idxs):
    # Calculate the Levene's test for each column supplied in data
    levenes = [0] * len(column_idxs)
    p_vals = [0] * len(column_idxs)

    # For each column in data given by column_idxs, calculate the Levene's test
    for i in range(len(column_idxs)):
        # Get the column index
        col_idx = column_idxs[i]
        # Get the column data
        col_data1 = [data1[j][col_idx] for j in range(len(data1))]
        col_data2 = [data2[j][col_idx] for j in range(len(data2))]
        # Convert the data to the correct type
        this_type = config.file_header_type[config.file_header_list_v1[col_idx]]
        col_data1 = list(map(this_type, col_data1))
        col_data2 = list(map(this_type, col_data2))
        # If we have strings, skip this column
        if this_type.__name__ == 'str':
            levenes[i] = -1
            p_vals[i] = -1
            continue
        # Calculate the Levene's test
        levenes[i], p_vals[i] = levene(col_data1, col_data2, center='median')

    return levenes, p_vals


def chi_squared(data1, data2, column_idxs):
    # Calculate the chi squared test for each column supplied in data
    chisq = [0] * len(column_idxs)
    p_vals = [0] * len(column_idxs)

    # Calculate the degrees of freedom
    dof = len(data1) - 1

    dists = [[] for i in range(len(data1))]

    # For each column in data given by column_idxs, calculate the chi squared test
    for i in range(len(column_idxs)):
        # Get the column index
        col_idx = column_idxs[i]
        # Get the column data
        col_data1 = [data1[j][col_idx] for j in range(len(data1))]
        col_data2 = [data2[j][col_idx] for j in range(len(data2))]
        # Convert the data to the correct type
        this_type = config.file_header_type[config.file_header_list_v1[col_idx]]
        col_data1 = list(map(this_type, col_data1))
        col_data2 = list(map(this_type, col_data2))
        # If we have strings, skip this column
        if this_type.__name__ != 'str':
            chisq[i] = -1
            p_vals[i] = -1
            continue
        # Calculate the chi squared test
        # Emit a waring if the name of the column isn't exit
        if config.file_header_list_v1[col_idx] != 'exit':
            print(f'Warning: column {config.file_header_list_v1[col_idx]} is not exit - something\'s probably wrong since this is the only string column that could differ')
            chisq[i] = -1
            p_vals[i] = -1
            continue
        # Convert col_data1 and col_data2 using exit_codes
        # Get the counts for each exit code
        exit_codes = config.exit_codes
        col_data1_converted = [0] * len(exit_codes)
        col_data2_converted = [0] * len(exit_codes)
        for j in range(len(col_data1)):
            col_data1_converted[exit_codes[col_data1[j]]] += 1
            col_data2_converted[exit_codes[col_data2[j]]] += 1
        # Get indices where either col_data1_converted or col_data2_converted are non-zero
        non_zero_indices = []
        for j in range(len(col_data1_converted)):
            if col_data1_converted[j] != 0 or col_data2_converted[j] != 0:
                non_zero_indices.append(j)
        # Remove all indices where both col_data1_converted and col_data2_converted are zero
        col_data1_converted = [col_data1_converted[j] for j in non_zero_indices]
        col_data2_converted = [col_data2_converted[j] for j in non_zero_indices]
        col_data1_converted_adj = col_data1_converted.copy()
        col_data2_converted_adj = col_data2_converted.copy()
        # Remove all indices where one of col_data1_converted or col_data2_converted is zero, add 1 to each to avoid divide by zero and mitigate large skew of results
        for j in range(len(col_data1_converted_adj)):
            if col_data1_converted_adj[j] == 0 or col_data2_converted_adj[j] == 0:
                col_data1_converted_adj[j] += 1
                col_data2_converted_adj[j] += 1
        chisq[i], p_vals[i] = chisquare(f_obs=col_data1_converted_adj, f_exp=col_data2_converted_adj)
        dists[i] = [col_data1_converted, col_data2_converted]

    return chisq, p_vals, dists


def report_diffs(diffs):
    # Print the differences in a nice format
    print('Int/Float differences are absolute values (abs(x - y)), String differences are 1 if different, 0 if same')
    print('Differences:')
    for i in range(len(diffs)):
        print(f'{config.file_header_list_v1[i]}: {diffs[i]:.2f}')
    print("-" * 25)

def match_commits(data1, data2):
    # Get the commit hashes from each data set
    commits1 = utils.get_columns(data1, ['rev'])[0]
    commits2 = utils.get_columns(data2, ['rev'])[0]

    # Get the intersection of the two commit lists
    commits = list(set(commits1).intersection(commits2))

    # Get the indices of the commits in data1 and data2
    idxs1 = [commits1.index(commit) for commit in commits]
    idxs2 = [commits2.index(commit) for commit in commits]

    # Get the data for each commit
    ret_data1 = [data1[idx] for idx in idxs1]
    ret_data2 = [data2[idx] for idx in idxs2]

    # Step through the data and make sure the commits match
    for i in range(len(ret_data1)):
        if ret_data1[i][0] != ret_data2[i][0]:
            print(f'Warning: commits {ret_data1[i][0]} and {ret_data2[i][0]} do not match')

    return ret_data1, ret_data2

def dump_csv(avg_differences, significant_diffs_idxs, significant_diffs_names, significant_diffs_types, p_val_list, p):
    # Check if the output directory exists, if not, create it - compare_stats
    if not os.path.exists('compare_stats'):
        os.mkdir('compare_stats')

    # Get the name of the CSV file (basename)
    csv_name = os.path.basename(args.basefile)
    # Get the name of the CSV file without the extension
    csv_name = os.path.splitext(csv_name)[0] + '_comparison.csv'

    prev_patches_avg = 0
    count = 0

    # Open the CSV file for writing
    with open(os.path.join('compare_stats', csv_name), 'w') as f:
        # Write the header - Field, Abs. Difference, P-Value
        f.write('Field,Mean Abs. $\Delta$,p-Value\n')
        # Write the data
        for i in range(len(avg_differences)):
            # Use config.file_header_list_v1 to get the name of the field
            field_name = config.file_header_list_v1[i]

            # Average this field
            if field_name == 'covlinesprevpatches':
                count += 1
                prev_patches_avg += avg_differences[i]
                if count < 10:
                    continue
                abs_diff = prev_patches_avg / count
                field_name = f"{field_name}*"
            else:
                # Get the absolute difference
                abs_diff = avg_differences[i]
            # Get the p-value if applicable
            if i in significant_diffs_idxs:
                # Get the index of i
                idx = significant_diffs_idxs.index(i)
                if significant_diffs_types[idx] == 'str':
                    p_val = p_val_list[idx]
                else:
                    p_val = p[idx]
                p_val = f'{p_val:.5f}'
            else:
                p_val = "-"
            # Write the data to the CSV file
            f.write(f'{field_name},{abs_diff:.2f},{p_val}\n')

        print(f'Wrote comparison data to {os.path.join("compare_stats", csv_name)}')

# def report_vars(vars, names):
#     # Print the variances in a nice format
#     print('Variances:')
#     for i in range(len(vars)):
#         print(f'{names[i]}: {vars[i]}')
#     print("-" * 25)

if __name__ == '__main__':
    import argparse
    import os

    # use argparse to get the two csv files
    parser = argparse.ArgumentParser(description='Compare two csv files.')
    parser.add_argument('basefile', help='Base file to compare')
    parser.add_argument('newfile', help='New file to compare')
    # Add other arguments, limit and endatcommit
    parser.add_argument('--limit', type=int, default=250,
                        help='Number of commits to compare')
    args = parser.parse_args()

    # Get basenames
    # Get the name of the CSV file (basename)
    csv_name1 = os.path.basename(args.basefile)
    csv_name2 = os.path.basename(args.newfile)

    # Remove the .csv extension
    csv_name1 = csv_name1[:-4]
    csv_name2 = csv_name2[:-4]

    data1 = utils.extract_data(args.basefile, csv_name1)
    data2 = utils.extract_data(args.newfile, csv_name2)

    start_idx = 0
    end_idx = 0
    commit_range = None
    lowered = [(x.lower(), x) for x in commits_prev_operating_range.keys()]
    for i in range(len(lowered)):
        if lowered[i][0] in csv_name1.lower():
            commit_range = commits_prev_operating_range[lowered[i][1]]
            # If it's a new repository (not in legacy Covrig) then just plot from start to end
            if commit_range is None or commit_range == (None, None):
                print(f'No commit range for {lowered[i][1]}')
                exit(0)

            # Get the start and end commits
            start_commit = commit_range[0]
            end_commit = commit_range[1]

            # Get the list of revs in data1
            revs = utils.get_columns(data1, ['rev'])[0]
            # Get the index of the start commit and end commit
            start_idx = revs.index(start_commit)
            end_idx = revs.index(end_commit)
            break
    if start_idx == 0 and end_idx == 0:
        print(f'Could not match {csv_name1} to a repository')
        exit(0)

    # Filter data1 to the range between start_commit and end_commit
    data1 = data1[start_idx:end_idx+1]

    # Filter to those that modify executable code or tests
    data1, _ = utils.filter_data_by_exec_test(data1)

    # Filter out the commits that have compile errors, empty commits or have no coverage (should already be done by filter_data_by_exec_test , but just in case)
    cleaned_data1 = utils.clean_data(data1)
    cleaned_data2 = utils.clean_data(data2)

    # Get all revs in cleaned_data1
    revs1 = utils.get_columns(cleaned_data1, ['rev'])[0]
    # Get all revs in cleaned_data2
    revs2 = utils.get_columns(cleaned_data2, ['rev'])[0]

    if revs1 != revs2:
        # Get the intersection of revs and revs2
        if csv_name2 == 'Zeromq_no_ls':
            revs1 = sorted(list(set(revs1).intersection(revs2)), key=revs2.index)
            # Filter cleaned_data1 to only include revs1
            cleaned_data1 = utils.get_data_with_commits(cleaned_data1, revs1)
        else:
            # Print warning
            print('Warning: Not the same set of revisions, attempting to match up the commits...')


    # Filter the data to include <limit> commits up to <endatcommit>
    limited_data1 = utils.limit_data(cleaned_data1, commit_range[1], limit=args.limit)

    limited_data2 = utils.get_data_with_commits(cleaned_data2, utils.get_columns(limited_data1, ['rev'])[0])

    # Emit a warning if data is not the same length
    if len(limited_data1) != len(limited_data2):
        print('Warning: Not the same set of revision when cleaned of compile errors, empty commits and no coverage')
        exit(0)

    # If revisions don't line up
    if utils.get_columns(limited_data1, ['rev'])[0] != utils.get_columns(limited_data2, ['rev'])[0]:
        print('Revisions don\'t line up (a rev likely compiles in one dataset but not in the other), attempting to match up the commits...')
        # Remove commits that are not in both data sets
        limited_data1, limited_data2 = match_commits(limited_data1, limited_data2)
        print(f'Number of commits matched: {len(limited_data1)}')

    # If rows don't have the same number of columns
    if len(limited_data1[0]) != len(limited_data2[0]):
        print('Warning: Rows don\'t have the same number of columns, assuming these are the last two')
        # Case of config.file_header_list_legacy_nobr
        if len(limited_data1[0]) > len(limited_data2[0]):
            limited_data1 = [row[:len(limited_data2[0])] for row in limited_data1]
        else:
            limited_data2 = [row[:len(limited_data1[0])] for row in limited_data2]
        print(f"Trimmed the rows to match, working on the remaining {len(limited_data1[0])} columns")

    # Compare the two data sets
    avg_differences, differences_data = compare_csv(limited_data1, limited_data2)
    report_diffs(avg_differences)

    # Define a threshold to check if the difference is significant by calculate the variance
    threshold = 1
    # For avg_differences, if the difference is greater than threshold, then it is significant
    # get the indices of the significant differences
    significant_diffs_idxs = [i for i in range(len(avg_differences)) if avg_differences[i] > threshold]
    significant_diffs_names = [config.file_header_list_v1[i] for i in significant_diffs_idxs]
    significant_diffs_types = [config.file_header_type[significant_diffs_names[i]].__name__ for i in
                               range(len(significant_diffs_names))]

    if len(significant_diffs_idxs) == 0:
        print('Success: No significant differences found between the two data sets when taking the average difference!')
        exit(0)

    # # Calculate the variance for each data set over the significant difference columns
    # # Idea: If the variances are similar, then we just have an offset between the two data sets, which is fine
    # # If the variances are different, then we have a problem
    # variances1 = calculate_variance_for_columns(limited_data1, significant_diffs_idxs)
    # variances2 = calculate_variance_for_columns(limited_data2, significant_diffs_idxs)
    #
    # # Print our variances as such: <column name> <variance1> <variance2>
    # print("Calculating variances...")
    # print('Variances: <column> <file1> <file2>')
    # for i in range(len(variances1)):
    #     if variances1[i] == -1 or variances2[i] == -1:  # i.e. string column
    #         continue
    #     print(f'{significant_diffs_names[i]}: {variances1[i]} {variances2[i]}')

    string_idxs = []
    p_val_list = None
    if 'str' in significant_diffs_types:
        # Calculate the ChiSq test for the string columns
        # Get the indices of the string columns
        string_idxs = [i for i in range(len(significant_diffs_types)) if significant_diffs_types[i] == 'str']
        chisq_list, p_val_list, dists = chi_squared(limited_data1, limited_data2, significant_diffs_idxs)

    ok_count = 0
    # Conduct a quick Levenes to see if the variances are significantly different for elements in the significant_diffs_idxs
    # If the variances are significantly different, then we have a problem
    p_value = 0.05
    # If p_values returned are less than p_value, then the variances are significantly different
    # print("-" * 25)
    print(f'Levene\'s test (variance similarity on those with difference > {threshold}):')
    print(f'p: {p_value} (H0: variances are similar with p-value >= {p_value}, H1: variances are significantly different with p < {p_value})')
    score, p = levenes_test(limited_data1, limited_data2, significant_diffs_idxs)
    for i in range(len(significant_diffs_idxs)):
        if score[i] == -1 or p[i] == -1:  # i.e. string column
            ok_count += 1
            continue
        if p[i] < p_value:
            info_string = 'Significantly different!'
        else:
            ok_count += 1
            info_string = 'Similar'
        print(f'{significant_diffs_names[i]}: Score: {score[i]:.5f} p-value: {p[i]:.5f} ({info_string})')

    if ok_count == len(significant_diffs_idxs):
        print('Success: All variances are similar, so we just have an offset between the two data sets, which is fine! (Caused by environmental factors)')
    else:
        print('Failure: We have a problem, the variances of the datasets are significantly different')

    ok_count = 0
    # Print the chi squared test results
    if 'str' in significant_diffs_types and len(string_idxs) > 0 and len(chisq_list) > 0 and len(p_val_list) > 0:
        print("-" * 25)
        print('Chi-Squared test:')
        print(f'p: {p_value} (H0: frequencies are similar with p-value >= {p_value}, H1: frequencies are significantly different with p-value < {p_value})')
        for i in string_idxs:
            # Check if the p-value is less than 0.05
            if chisq_list[i] == -1 or p_val_list[i] == -1:  # i.e. numeric column
                ok_count += 1
                continue
            if p_val_list[i] < 0.05:
                info_string = 'Significantly different!'
                info_string += f' (Distributions of labels were {" and ".join([str(x) for x in dists[i]])})'
            else:
                ok_count += 1
                info_string = 'Similar'
            print(
                f'{significant_diffs_names[i]}: Chi squared: {chisq_list[i]:.5f} p-value: {p_val_list[i]:.5f} {info_string}')

        if ok_count == len(string_idxs):
            print(
                'Success: All string distributions are similar!')
        else:
            print('Warning: The exit codes are not distributed similarly between the two data sets (different distributions of OK and SomeTestFailed)')
            print("This can be OK if dependency issues were resolved on the more recent data set.")
    dump_csv(avg_differences, significant_diffs_idxs, significant_diffs_names, significant_diffs_types, p_val_list=p_val_list, p=p)
