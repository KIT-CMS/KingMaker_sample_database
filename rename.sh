#!/bin/bash

BASE="/store/user/sgiappic/CROWN/ntuples/htt_251127_2024-25/CROWNRun/2025"

xrdfs cmsdcache-kit-disk.gridka.de ls -R $BASE | grep '_RunIII2024' | sort -r | while read oldpath; do
    newpath="${oldpath/_RunIII2024/_RunIII2025}"
    newdir=$(dirname "$newpath")
    # Create the target directory if it doesn't exist
    xrdfs cmsdcache-kit-disk.gridka.de mkdir -p "$newdir"
    # Now move the file or directory
    xrdfs cmsdcache-kit-disk.gridka.de mv "$oldpath" "$newpath"
    echo "Renamed: $oldpath -> $newpath"
done

xrdfs cmsdcache-kit-disk.gridka.de ls -R /store/user/sgiappic/CROWN/ntuples/htt_251127_2024-25/CROWNRun/2025 | grep 'RunIII2024' | sort -r | while read path; do
  # Check if it's a directory (xrdfs stat returns "Is a directory" in stderr for dirs)
  if xrdfs cmsdcache-kit-disk.gridka.de stat "$path" 2>&1 | grep -q "Is a directory"; then
    xrdfs cmsdcache-kit-disk.gridka.de rm -r "$path"
    echo "Removed directory: $path"
  fi
done