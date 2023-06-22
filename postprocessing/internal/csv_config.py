# Globals that tell the scripts the layout of the csv files

# Replace as necessary
file_header_raw = "rev,#eloc,coverage,testsize,author,#addedlines,#covlines,#notcovlines,patchcoverage," \
                  "#covlinesprevpatches*,#covlinesprevpatches*,#covlinesprevpatches*,#covlinesprevpatches*," \
                  "#covlinesprevpatches*,#covlinesprevpatches*,#covlinesprevpatches*,#covlinesprevpatches*," \
                  "#covlinesprevpatches*,#covlinesprevpatches*,time,exit,hunks,ehunks,changed_files,echanged_files," \
                  "changed_test_files,hunks3,ehunks3,merge,#br,#brcov,repeats,non_det"

# Remove any # or *s from the file_header after splitting by string (V2)
file_header_list = [x.replace('#', '').replace('*', '') for x in file_header_raw.split(',')]

# V1 is without last two columns
file_header_list_v1 = file_header_list[:-2]

file_header_list_v1_no_br = file_header_list_v1[:-2]

# Legacy is without last two columns and with only one covlinesprevpatches column in that list (so 0 to 9 and 19 to the end)
file_header_list_legacy = file_header_list_v1[:10] + file_header_list_v1[19:]

# The case for Lighttpd-gnutls.csv
file_header_list_legacy_nobr = file_header_list_legacy[:-2]

# Create a map to hold the type of each column
file_header_type = {
    'rev': str,
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
    'merge': str,
    'br': int,
    'brcov': int,
    'repeats': int,
    'non_det': str,
}

exit_codes = {
    'OK': 0,
    'SomeTestFailed': 1,
    'TimedOut': 2,
    'compileError': 3,
    'NoCoverage': 4,
    'EmptyCommit': 5,
}
