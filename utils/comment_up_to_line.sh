# Comment all lines apart from the first one up to a given line number

FILE=$1
SEARCH_STRING=$2
# Find the line number where the string SEARCH_STRING is
LINE_NUMBER=$(grep -n "$SEARCH_STRING" $1 | cut -d: -f1)

LINE_NUMBER=$((LINE_NUMBER-1))

# From line 2 to line LINE_NUMBER-1, comment the line
sed -i "2,$LINE_NUMBER s/^/#/" $1