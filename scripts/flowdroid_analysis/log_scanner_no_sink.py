#!/usr/bin/env python3
"""
Script to move log files that DO contain the specific error message
from a source directory to a destination directory.
"""

import os
import sys
import argparse
import shutil
from pathlib import Path
import re
import datetime


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
            content = file.read()
            if error_message in content:
                return True
            return False
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return False


def get_files_with_error(search_path, error_message, file_pattern=None):
    """
    Get files that DO contain the error message.
    
    Args:
        search_path (Path): Directory to scan
        error_message (str): Error message to search for
        file_pattern (str, optional): Regex pattern to match filenames
    
    Returns:
        list: List of file paths that contain the error message
    """
    matching_files = []
    pattern = re.compile(file_pattern) if file_pattern else None
    
    if not search_path.is_dir():
        print(f"Error: {search_path} is not a directory.")
        return []
    
    print(f"Looking for error message: '{error_message}'")
    
    for root, _, files in os.walk(search_path):
        for filename in files:
            # Skip files that don't match the pattern if provided
            if pattern and not pattern.search(filename):
                continue
                
            file_path = os.path.join(root, filename)
            # Only include files that DO have the error
            if check_file_for_error(file_path, error_message):
                print(f"Found error in: {file_path}")
                matching_files.append(file_path)
    
    return matching_files


def move_files(file_list, destination_dir):
    """
    Move files to the destination directory.
    
    Args:
        file_list (list): List of file paths to move
        destination_dir (str): Destination directory
    
    Returns:
        tuple: (List of successfully moved files, List of failed files with error messages)
    """
    # Create destination directory if it doesn't exist
    os.makedirs(destination_dir, exist_ok=True)
    
    moved_files = []
    failed_files = []
    
    for file_path in file_list:
        try:
            # Get just the filename without path
            filename = os.path.basename(file_path)
            # Destination path
            dest_path = os.path.join(destination_dir, filename)
            
            # Move the file
            shutil.move(file_path, dest_path)
            moved_files.append(file_path)
        except Exception as e:
            failed_files.append((file_path, str(e)))
    
    return moved_files, failed_files


def main():
    parser = argparse.ArgumentParser(description='Move log files with the error message.')
    parser.add_argument('source', help='Source directory containing log files')
    parser.add_argument('-p', '--pattern', default='.*\.log$',
                        help='Regex pattern for matching filenames (default: .*\.log$)')
    parser.add_argument('-o', '--output', default='error_files_report.txt',
                        help='Output file to save report (default: error_files_report.txt)')
    parser.add_argument('-d', '--destination', 
                        default='./FlowDroid_output_minor/with_error',
                        help='Destination directory for copying files with error')
    parser.add_argument('--dry-run', action='store_true',
                        help='Only generate report without copying files')
    
    args = parser.parse_args()
    
    # Error message to look for (we want files that DO have this)
    error_message = "[main] ERROR soot.jimple.infoflow.android.SetupApplication$InPlaceInfoflow - No sinks found, aborting analysis"
    print(f"Using error message: '{error_message}'")
    print(f"Message length: {len(error_message)} characters")
    
    source_path = Path(args.source)
    if not source_path.exists() or not source_path.is_dir():
        print(f"Error: Source path '{source_path}' does not exist or is not a directory.")
        sys.exit(1)
    
    # Find all files that DO contain the error
    print(f"Scanning for log files that DO contain the error message...")
    files_with_error = get_files_with_error(source_path, error_message, args.pattern)
    print(f"Found {len(files_with_error)} files with the error message.")
    
    # Write results to the output file
    with open(args.output, 'w', encoding='utf-8') as output_file:
        # Write header with summary
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        output_file.write(f"Error Log Files Report - {timestamp}\n")
        output_file.write(f"Files that DO contain the error: {error_message}\n\n")
        output_file.write(f"SUMMARY\n")
        output_file.write(f"-------\n")
        output_file.write(f"Total files with error: {len(files_with_error)}\n\n")
        
        # Write the list of files
        output_file.write(f"LIST OF FILES WITH ERROR\n")
        output_file.write(f"----------------------\n")
        
        if files_with_error:
            for i, file_path in enumerate(files_with_error, 1):
                output_file.write(f"{i}. {file_path}\n")
        else:
            output_file.write("No files with the error were found.\n")
    
    print(f"Report saved to {args.output}")
    
    # Move files if not in dry-run mode
    if not args.dry_run and files_with_error:
        print(f"Moving {len(files_with_error)} files to {args.destination}...")
        moved, failed = move_files(files_with_error, args.destination)
        
        print(f"Successfully moved {len(moved)} files.")
        
        if failed:
            print(f"Failed to move {len(failed)} files:")
            for file_path, error in failed:
                print(f"  {file_path}: {error}")
    elif args.dry_run:
        print("Dry run mode: No files were moved.")


if __name__ == "__main__":
    main()