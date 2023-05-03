# Now that we have our archives of coverage data, we need to modify the pregenerated info file to point to local source files.

# Example of a pregenerated info file:
# SF:/home/redis/src/ae.c
# Desired output:
# SF:tmp/src/ae.c

# usage:
# python3 utils/localize_info_src.py tmp2-current/total.info /home/redis $(realpath tmp2-current)


# take in an info file, the path to strip and the path to prepend
def modify_info(args):
    # read input file
    with args.file as f:
        lines = f.readlines()

    # delete the file
    os.remove(args.file.name)

    # create a new file with the same name
    modify_count = 0
    with open(args.file.name, 'w') as f_out:
        for line in lines:
            if line.startswith('SF:'):
                # get the file path
                file_path = line.split(':')[1].strip()
                # strip the path
                file_path = file_path.replace(args.strip, '')
                # prepend the path
                file_path = args.prepend + file_path + '\n'
                # write to output file
                f_out.write('SF:' + file_path)
                modify_count += 1
            else:
                # write the line to the output file
                f_out.write(line)

    print("Done! Modified {} lines.".format(modify_count))


if __name__ == '__main__':
    import argparse
    import os

    # use argparse to get the info file, the path to strip and the path to prepend
    parser = argparse.ArgumentParser(description='Modify the info file to point to local source files.')
    parser.add_argument('file', type=argparse.FileType('r'),
                        help='File to modify')
    parser.add_argument('strip', type=str,
                        help='Path to strip')
    parser.add_argument('prepend', type=str,
                        help='Path to prepend')
    args = parser.parse_args()
    modify_info(args)
