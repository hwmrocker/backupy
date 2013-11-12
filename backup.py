#!/usr/bin/env python
"""
Usage:
    backup.py [-f PATH] [-t PATH] [-e FILE] [[<from>] <to>]

Options:
    -f PATH, --from PATH  from [default: ~/], overides positional argument
    -t PATH, --to PATH    destination of the backup, overides positional argument
    -e FILE, --exclude    a file that contains all exclude patters for rsync
"""
#http://docopt.org/
# used the shellscript from https://github.com/laurent22/rsync-time-backup as a reference

from docopt import docopt
from datetime import datetime
import os
import re

INPROGRESS_FILE = "backup.inprogress"

if __name__ != '__main__':
    import sys
    sys.exit()

arguments = docopt(__doc__, version='0.1 alpha')
src_folder = arguments.get("<from>") if arguments.get("<from>") else arguments["--from"]
dst_folder = arguments.get("--to") if arguments.get("--to") else arguments["<to>"]
assert dst_folder, "You have to provide a destination for the backup"

def clean_path(path):
    assert path is None or "'" not in path
    #TODO expand ~
    return path

src_folder = clean_path(src_folder)
dst_folder = clean_path(dst_folder)
exclusion_file = clean_path(arguments.get('--exclude'))
print arguments
print src_folder
print dst_folder
# exit(0)
# TODO maybe later feature
# # -----------------------------------------------------------------------------
# # Check that the destination drive is a backup drive
# # -----------------------------------------------------------------------------

# DEST_MARKER_FILE=$DEST_FOLDER/backup.marker
# if [ ! -f "$DEST_MARKER_FILE" ]; then
#         echo "Safety check failed - the destination does not appear to be a backup folder or drive (marker file not found)."
#         echo "If it is indeed a backup folder, you may add the marker file by running the following command:"
#         echo ""
#         echo "touch -- \"$DEST_MARKER_FILE\""
#         echo ""
#         exit 1
# fi

# -----------------------------------------------------------------------------
# Setup additional variables
# -----------------------------------------------------------------------------

folder_reg = re.compile("\d{4}-\d\d-\d\d-\d{6}")

now = datetime.now().strftime("%Y-%m-%d-%H%M%S")
dst = os.path.join(dst_folder, now)
link = os.path.join(dst_folder, "latest")
prev_dst = None

last_times = sorted(f for f in os.listdir(dst_folder) if folder_reg.match(f))
if last_times:
    last_time = last_times[-1]
    prev_dst = os.path.join(dst_folder, last_time)

inprogress = os.path.join(dst_folder, INPROGRESS_FILE)

# -----------------------------------------------------------------------------
# Handle case where a previous backup failed or was interrupted.
# -----------------------------------------------------------------------------
if os.path.exists(inprogress):
    if prev_dst:
        print("%s already exists, resume backup" % inprogress)
        os.rename(prev_dst, dst)
        prev_dst = os.path.join(dst_folder, last_times[-2]) if len(last_times) >= 2 else None

# -----------------------------------------------------------------------------
# Check if we are doing an incremental backup (if previous backup exists) or not
# -----------------------------------------------------------------------------
options = ["rsync"]

if prev_dst:
    print("previous backup found, doing incremental backup from %s" % prev_dst)
    options.append("--link-dest=%r" % prev_dst)
else:
    print("Create new full backup")

# -----------------------------------------------------------------------------
# Create destination folder if it doesn't already exists
# -----------------------------------------------------------------------------

try:
    os.makedirs(dst)
    # os.system("mkdie -p %r" % dst)
except os.error, e:
    print("oO %s" % e)

# -----------------------------------------------------------------------------
# Start backup
# -----------------------------------------------------------------------------

print("Starting backup...")
print("From: %s" % src_folder)
print("To:   %s" % dst)

options.extend(["--compress",
"--numeric-ids",
"--links",
"--hard-links",
"--delete",
"--delete-excluded",
"--one-file-system",
"--archive",
"--progress",])

if exclusion_file:
    options.append("--exclude-from %r" % exclusion_file)

cmd = "%s %r %r" % (" ".join(options), src_folder, dst)
# CMD="$CMD -- '$LINK_DEST_OPTION' '$SRC_FOLDER/' '$DEST/'"
# CMD="$CMD | grep -E '^deleting|[^/]$'"

print("Running command:\n%s" % cmd)

with open(inprogress, "w") as fh:
    pass

exit_code = os.system(cmd)
if exit_code == 0:
    os.remove(inprogress)
    os.unlink(link)
    os.symlink(dst, link)
else:
    print("Error: Exited with error code %s" % exit_code)
