import argparse
import internal.csv_config as config
import internal.csv_utils as utils


# This script is useful for parallel runs of memcached with repeats which for some reason returns revisions with no coverage occasionally
def main():
    # Parse arguments - input file (with fixed coverage), and output file (with no coverage)
    parser = argparse.ArgumentParser(description='Replace no coverage with 0 coverage')
    parser.add_argument('input_fix_file', type=str, help='Input fixed file')
    parser.add_argument('input_faulty_file', type=str, help='Input faulty file')
    parser.add_argument('output_file', type=str, help='Output file')
    args = parser.parse_args()

    data_in = utils.extract_data(args.input_fix_file, 'input')
    data_in_faulty = utils.extract_data(args.input_faulty_file, 'input_faulty')

    # Get all lines in data_out that have no coverage
    revs, exit_statuses = utils.get_columns(data_in_faulty, ['rev', 'exit'])

    revs_fixed = utils.get_columns(data_in, ['rev'])[0]

    # Create a map from rev to idx in data_in
    rev_to_idx = {rev: i for i, rev in enumerate(revs_fixed)}

    corrected_out = []
    corrected_counter = 0
    # Step through each line of data_out, and if the exit status is no coverage, replace the line in data_out with the corresponding line in data_in
    for i in range(len(data_in_faulty)):
        if exit_statuses[i] == 'NoCoverage':
            # Find the index of the revision in data_in
            idx = rev_to_idx[revs[i]]
            # Replace the line in data_out with the corresponding line in data_in
            corrected_out.append(data_in[idx])
            corrected_counter += 1
        else:
            corrected_out.append(data_in_faulty[i])

    print(f'Replaced {corrected_counter} lines')

    # Write the corrected data to the output file
    # Write the header first (file_header_raw)
    with open(args.output_file, 'w') as f:
        f.write(config.file_header_raw + '\n')
        for line in corrected_out:
            f.write(','.join(line) + '\n')

    print(f'Wrote to {args.output_file}.')


if __name__ == '__main__':
    main()
