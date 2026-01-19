#!/usr/bin/env python3
"""
log_scanner_leak.py

This script scans log files to find those reporting non-zero leaks
(containing "Found X leaks" where X > 0) and moves them to a destination folder.
"""

import os
import sys
import argparse
from pathlib import Path
import re
import datetime
import shutil


def check_file_for_leaks(file_path):
    """
    Check if a file contains reports of non-zero leaks.
    
    Args:
        file_path (str): Path to the log file
    
    Returns:
        tuple: (bool indicating if non-zero leaks found, number of leaks if found, otherwise None)
    """
    zero_leaks_pattern = r"\[main\] INFO soot\.jimple\.infoflow\.android\.SetupApplication - Found 0 leaks"
    non_zero_leaks_pattern = r"\[main\] INFO soot\.jimple\.infoflow\.android\.SetupApplication - Found (\d+) leaks"
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
            content = file.read()
            
            # First check if there's a report of zero leaks
            zero_leaks_match = re.search(zero_leaks_pattern, content)
            if zero_leaks_match:
                return False, 0
            
            # Then check for non-zero leaks
            non_zero_match = re.search(non_zero_leaks_pattern, content)
            if non_zero_match:
                num_leaks = int(non_zero_match.group(1))
                if num_leaks > 0:
                    return True, num_leaks
            
            # If neither pattern matched or leaks is 0, return False
            return False, None
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return False, None


def scan_for_leak_files(search_path, file_pattern=None):
    """
    Scan directory for log files reporting non-zero leaks.
    
    Args:
        search_path (Path): File or directory to scan
        file_pattern (str, optional): Regex pattern to match filenames
    
    Returns:
        dict: Dictionary mapping file paths to number of leaks found
    """
    matching_files = {}
    pattern = re.compile(file_pattern) if file_pattern else None
    
    if search_path.is_file():
        has_leaks, num_leaks = check_file_for_leaks(str(search_path))
        if has_leaks:
            matching_files[str(search_path)] = num_leaks
    elif search_path.is_dir():
        for root, _, files in os.walk(search_path):
            for filename in files:
                # Skip files that don't match the pattern if provided
                if pattern and not pattern.search(filename):
                    continue
                    
                file_path = os.path.join(root, filename)
                has_leaks, num_leaks = check_file_for_leaks(file_path)
                if has_leaks:
                    matching_files[file_path] = num_leaks
    
    return matching_files


def main():
    parser = argparse.ArgumentParser(
        description='Scan log files for reports of non-zero leaks and move them.'
    )
    parser.add_argument(
        '-d', '--directory', 
        default='./FlowDroid_output_minor/successful',
        help='Directory containing log files to scan'
    )
    parser.add_argument(
        '-p', '--pattern', 
        default='.*\.log$',
        help='Regex pattern for matching filenames (default: .*\.log$)'
    )
    parser.add_argument(
        '-o', '--output', 
        default='leak_report.txt',
        help='Output file to save report (default: leak_report.txt)'
    )
    parser.add_argument(
        '-m', '--move-to', 
        default='./FlowDroid_output_minor/leak',
        help='Directory to move files reporting leaks'
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help='Only generate report without moving files'
    )
    
    args = parser.parse_args()
    
    search_path = Path(args.directory)
    if not search_path.exists():
        print(f"Error: Directory '{search_path}' does not exist.")
        sys.exit(1)
    
    # Find all files reporting non-zero leaks
    print(f"Scanning for files reporting non-zero leaks...")
    matching_files = scan_for_leak_files(search_path, args.pattern)
    print(f"Found {len(matching_files)} files reporting non-zero leaks.")
    
    # Write results to the output file
    with open(args.output, 'w', encoding='utf-8') as output_file:
        # Write header with summary
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        output_file.write(f"Non-Zero Leaks Report - {timestamp}\n")
        output_file.write(f"Files reporting leaks (more than 0)\n\n")
        output_file.write(f"SUMMARY\n")
        output_file.write(f"-------\n")
        output_file.write(f"Total files reporting leaks: {len(matching_files)}\n\n")
        
        # Write the list of files
        output_file.write(f"LIST OF FILES REPORTING LEAKS\n")
        output_file.write(f"----------------------------\n")
        
        if matching_files:
            for i, (file_path, num_leaks) in enumerate(sorted(matching_files.items(), key=lambda x: x[1], reverse=True), 1):
                output_file.write(f"{i}. {file_path} - Found {num_leaks} leaks\n")
        else:
            output_file.write("No files reporting leaks were found.\n")
    
    print(f"Report saved to {args.output}")
    
    # Move files if not in dry-run mode
    if not args.dry_run and matching_files:
        move_destination = Path(args.move_to)
        
        # Create destination directory if it doesn't exist
        os.makedirs(move_destination, exist_ok=True)
        
        print(f"Moving {len(matching_files)} files to {move_destination}...")
        moved = 0
        failed = 0
        
        for file_path in matching_files:
            try:
                # Get just the filename without path
                filename = os.path.basename(file_path)
                # Destination path
                dest_path = os.path.join(move_destination, filename)
                
                # Move the file
                shutil.move(file_path, dest_path)
                moved += 1
            except Exception as e:
                failed += 1
                print(f"Failed to move {file_path}: {e}")
        
        print(f"Successfully moved {moved} files. Failed to move {failed} files.")
    elif args.dry_run:
        print("Dry run mode: No files were moved.")


if __name__ == "__main__":
    main()