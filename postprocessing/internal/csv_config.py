# Globals that tell the scripts the layout of the csv files

# Replace as necessary
file_header_raw = "rev,#eloc,coverage,testsize,author,#addedlines,#covlines,#notcovlines,patchcoverage,#covlinesprevpatches*,#covlinesprevpatches*,#covlinesprevpatches*,#covlinesprevpatches*,#covlinesprevpatches*,#covlinesprevpatches*,#covlinesprevpatches*,#covlinesprevpatches*,#covlinesprevpatches*,#covlinesprevpatches*,time,exit,hunks,ehunks,changed_files,echanged_files,changed_test_files,hunks3,ehunks3,merge,#br,#brcov"

# Remove any # or *s from the file_header after splitting by string
file_header_list = [x.replace('#', '').replace('*', '') for x in file_header_raw.split(',')]

# Create a map to hold the type of each column
file_header_type = {
    'rev': int,
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
    'merge': int,
    'br': int,
    'brcov': int
}