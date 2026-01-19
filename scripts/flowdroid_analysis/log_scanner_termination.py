#!/usr/bin/env python3
"""
log_scanner_termination.py

This script scans log files for a specific error message related to executor termination
and moves files containing this error to a specified directory.
"""

import os
import sys
import argparse
from pathlib import Path
import re
import datetime
import shutil


def check_file_for_error(file_path, error_message):
    """
    Check if a file contains the specified error message.
    
    Args:
        file_path (str): Path to the log file
        error_message (str): Error message to search for
    
    Returns:
        bool: True if error message is found, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
            for line in file:
                if error_message in line:
                    return True
        return False
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return False


def scan_for_error_files(search_path, error_message, file_pattern=None):
    """
    Scan directory for log files containing the error message.
    
    Args:
        search_path (Path): File or directory to scan
        error_message (str): Error message to search for
        file_pattern (str, optional): Regex pattern to match filenames
    
    Returns:
        list: List of file paths that contain the error message
    """
    matching_files = []
    pattern = re.compile(file_pattern) if file_pattern else None
    
    if search_path.is_file():
        if check_file_for_error(str(search_path), error_message):
            matching_files.append(str(search_path))
    elif search_path.is_dir():
        for root, _, files in os.walk(search_path):
            for filename in files:
                # Skip files that don't match the pattern if provided
                if pattern and not pattern.search(filename):
                    continue
                    
                file_path = os.path.join(root, filename)
                if check_file_for_error(file_path, error_message):
                    matching_files.append(file_path)
    
    return matching_files


def main():
    parser = argparse.ArgumentParser(
        description='Scan log files for executor termination error message and move them.'
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
        default='termination_error_report.txt',
        help='Output file to save report (default: termination_error_report.txt)'
    )
    parser.add_argument(
        '-m', '--move-to', 
        default='./FlowDroid_output_minor/error/termination',
        help='Directory to move files containing the error (default: ./FlowDroid_output_minor/error/termination)'
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help='Only generate report without moving files'
    )
    
    args = parser.parse_args()
    
    # Error message to look for
    error_message = "[main] ERROR soot.jimple.infoflow.android.SetupApplication$InPlaceInfoflow - Could not wait for executor termination"
    
    search_path = Path(args.directory)
    if not search_path.exists():
        print(f"Error: Directory '{search_path}' does not exist.")
        sys.exit(1)
    
    # Find all files containing the error
    print(f"Scanning for files containing the termination error message...")
    matching_files = scan_for_error_files(search_path, error_message, args.pattern)
    print(f"Found {len(matching_files)} files containing the termination error message.")
    
    # Write results to the output file
    with open(args.output, 'w', encoding='utf-8') as output_file:
        # Write header with summary
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        output_file.write(f"Executor Termination Error Report - {timestamp}\n")
        output_file.write(f"Error message: {error_message}\n\n")
        output_file.write(f"SUMMARY\n")
        output_file.write(f"-------\n")
        output_file.write(f"Total files with termination error: {len(matching_files)}\n\n")
        
        # Write the list of files
        output_file.write(f"LIST OF FILES CONTAINING THE TERMINATION ERROR\n")
        output_file.write(f"------------------------------------------\n")
        
        if matching_files:
            for i, file_path in enumerate(matching_files, 1):
                output_file.write(f"{i}. {file_path}\n")
        else:
            output_file.write("No files containing the termination error message were found.\n")
    
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