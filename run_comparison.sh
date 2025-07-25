#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Define temporary file names
HEAD_FILE="gemini_head.md"
OLD_FILE="gemini_old.md"

# Ensure cleanup happens on script exit
trap 'rm -f "$HEAD_FILE" "$OLD_FILE"' EXIT

# 1. Get the current version of GEMINI.md from HEAD
echo "Extracting current version of GEMINI.md..."
git show HEAD:GEMINI.md > "$HEAD_FILE"

# 2. Get the version of GEMINI.md from approximately two days ago
# Find the hash of the first commit that is older than "2 days ago"
COMMIT_HASH=$(git rev-list -n 1 --before="2 days ago" main)

if [ -z "$COMMIT_HASH" ]; then
    echo "Error: Could not find a commit from two days ago."
    exit 1
fi

echo "Extracting version of GEMINI.md from commit $COMMIT_HASH..."
git show "$COMMIT_HASH":GEMINI.md > "$OLD_FILE"

# 3. Run the comparison script using uv
echo "Running comparison with compare_markdown.py..."
uv run python compare_markdown.py "$HEAD_FILE" "$OLD_FILE" --cluster --visualize

echo -e "\nComparison complete. The plot has been saved to similarity_plot.png."
