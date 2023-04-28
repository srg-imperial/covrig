from .csv_config import file_header_list, file_header_type
import datetime

def clean_data(data, omit=None):
    if omit is None:
        omit = ['EmptyCommit', 'NoCoverage', 'compileError']
    return [x for x in data if x[file_header_list.index('exit')] not in omit]


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

        # Split the lines by comma
        lines = [line.split(',') for line in lines]

        # Skip any lines that don't have the correct number of columns
        lines = [line for line in lines if len(line) == len(file_header_list)]

        if len(lines) == 0:
            print(f'Warning: {csv_name} is missing columns, skipping...')
            return None

    # Perform a sanity check on the data, that the timestamps are in order (low to high)
    dates = [line[file_header_list.index('time')] for line in lines]

    # Callback - e.g. making sure the dates are in order
    if callback is not None:
        callback({'dates': dates, 'csv_name': csv_name, 'input_file': input_file, 'lines': lines})

    return lines
