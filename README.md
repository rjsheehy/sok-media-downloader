# sok-media-downloader

A quick script to download conference videos from SOK Media (Source of Knowledge). If your shell is writing to a history file, don't forget to remove the lines calling the script after usage (to prevent credential leakage).

Currently configured to download BSidesLV 2016 and Defcon 2016 videos.

Usage:

python sok-downloader.py {conference} {output directory} {username} {password}

