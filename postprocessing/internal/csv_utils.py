from .csv_config import file_header_list, file_header_type, file_header_list_v1, file_header_list_legacy, \
    file_header_list_legacy_nobr
import datetime


def clean_data(data, omit=None):
    if omit is None:
        omit = ['EmptyCommit', 'NoCoverage', 'compileError']
    return [x for x in data if x[file_header_list.index('exit')] not in omit]


def limit_data(data, end_at_commit, limit=250):
    # Find the index of the commit to end at in data
    end_at_commit_index = [x[file_header_list.index('rev')] for x in data].index(end_at_commit)
    # print(f'Ending at commit {end_at_commit} (index {end_at_commit_index})')
    # Print a warning if end_at_commit_index is less than limit
    lower_bound = end_at_commit_index - limit
    if end_at_commit_index < limit:
        # print(f'Warning: end_at_commit_index {end_at_commit_index} is less than limit {limit}, returning {end_at_commit_index} commits...')
        lower_bound = 0
    # Return the data up to the end_at_commit_index
    return data[lower_bound:end_at_commit_index]


def get_data_with_commits(data, commits):
    # Get a list of the commits in the data
    data_commits = get_columns(data, ['rev'])[0]
    # Get the indices of the commits in the data
    data_commits_indices = [data_commits.index(x) for x in commits]

    # Return the data with the commits
    return [data[x] for x in data_commits_indices]


def filter_data_by_exec_test(data):
    # Take a list of rows (data) and return a list of rows that have 'covlines' + 'notcovlines' > 0 or 'changed_test_files' > 0

    # Get the columns
    covlines, notcovlines, changed_test_files = get_columns(data, ['covlines', 'notcovlines', 'changed_test_files'])

    # Get the indices of the rows that have 'covlines' + 'notcovlines' > 0 or 'changed_test_files' > 0
    indices = [i for i, x in enumerate(covlines) if x + notcovlines[i] > 0 or changed_test_files[i] > 0]

    # Return the data with the indices
    return [data[x] for x in indices], indices


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


def extract_diffcov_data(input_file, csv_name, callback=None):
    # Take the input file CSV and extract to an internal representation of the data

    # Open the file
    with open(input_file, 'r') as f:
        # Read the file
        lines = f.readlines()

        # Remove the header
        lines = lines[1:]

        # Ignore any lines that begin with a # (i.e. comments)
        lines = [line for line in lines if not line.startswith('#')]

        # Strip the new line characters and any leading or trailing white space
        lines = [line.strip() for line in lines]

        # Split the lines by comma
        lines = [line.split(',') for line in lines]

        if len(lines) == 0:
            print(f'Warning: {csv_name} is missing columns, skipping...')
            return None

        # Skip any lines that don't have the correct number of columns
        lines = [line for line in lines if len(line) == 12]

    return lines


def extract_data(input_file, csv_name, callback=None):
    # Take the input file CSV and extract to an internal representation of the data

    # Open the file
    with open(input_file, 'r') as f:
        # Read the file
        lines = f.readlines()

        # Remove the header
        lines = lines[1:]

        # Ignore any lines that begin with a # (i.e. comments)
        lines = [line for line in lines if not line.startswith('#')]

        # Strip the new line characters and any leading or trailing white space
        lines = [line.strip() for line in lines]

        # Split the lines by comma
        lines = [line.split(',') for line in lines]

        # Skip any lines that don't have the correct number of columns
        lines = [line for line in lines if
                 len(line) == len(file_header_list) or len(line) == len(file_header_list_v1) or len(line) == len(
                     file_header_list_legacy) or len(line) == len(file_header_list_legacy_nobr)]

        if len(lines) == 0:
            print(f'Warning: {csv_name} is missing columns, skipping...')
            return None

    # Perform a sanity check on the data, that the timestamps are in order (low to high)
    dates = [line[file_header_list.index('time')] for line in lines]

    # Callback - e.g. making sure the dates are in order
    if callback is not None:
        callback({'dates': dates, 'csv_name': csv_name, 'input_file': input_file, 'lines': lines})

    return lines
