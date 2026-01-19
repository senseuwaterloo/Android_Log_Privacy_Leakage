#!/usr/bin/env python3
"""
Script to move log files that contain the specific "Found 0 leaks" message
from a source directory to a destination directory.
"""

import os
import sys
import argparse
import shutil
from pathlib import Path
import re
import datetime


def check_file_for_message(file_path, target_message):
    """
    Check if a file contains the specified message.
    
    Args:
        file_path (str): Path to the log file
        target_message (str): Message to search for
    
    Returns:
        bool: True if message is found, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
            content = file.read()
            if target_message in content:
                return True
            return False
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return False


def get_files_with_message(search_path, target_message, file_pattern=None):
    """
    Get files that contain the target message.
    
    Args:
        search_path (Path): Directory to scan
        target_message (str): Message to search for
        file_pattern (str, optional): Regex pattern to match filenames
    
    Returns:
        list: List of file paths that contain the message
    """
    matching_files = []
    pattern = re.compile(file_pattern) if file_pattern else None
    
    if not search_path.is_dir():
        print(f"Error: {search_path} is not a directory.")
        return []
    
    print(f"Looking for message: '{target_message}'")
    
    total_files = 0
    for root, _, files in os.walk(search_path):
        for filename in files:
            total_files += 1
            # Skip files that don't match the pattern if provided
            if pattern and not pattern.search(filename):
                continue
                
            file_path = os.path.join(root, filename)
            # Include files that have the message
            if check_file_for_message(file_path, target_message):
                print(f"Found message in: {file_path}")
                matching_files.append(file_path)
    
    print(f"Scanned {total_files} total files.")
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
            
            # Handle file name conflicts by adding a unique suffix
            if os.path.exists(dest_path):
                name_parts = os.path.splitext(filename)
                timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                unique_filename = f"{name_parts[0]}_{timestamp}{name_parts[1]}"
                dest_path = os.path.join(destination_dir, unique_filename)
                print(f"File already exists, renaming to: {unique_filename}")
            
            # Move the file
            shutil.move(file_path, dest_path)
            moved_files.append((file_path, dest_path))
        except Exception as e:
            failed_files.append((file_path, str(e)))
    
    return moved_files, failed_files


def main():
    parser = argparse.ArgumentParser(description='Move log files with the "Found 0 leaks" message.')
    parser.add_argument('source', help='Source directory containing log files')
    parser.add_argument('-p', '--pattern', default='.*\.log$',
                        help='Regex pattern for matching filenames (default: .*\.log$)')
    parser.add_argument('-o', '--output', default='zero_leaks_files_report.txt',
                        help='Output file to save report (default: zero_leaks_files_report.txt)')
    parser.add_argument('-d', '--destination', 
                        default='./zero_leaks_files',
                        help='Destination directory for moving files with the message')
    parser.add_argument('--dry-run', action='store_true',
                        help='Only generate report without moving files')
    
    args = parser.parse_args()
    
    # Message to look for
    target_message = "[main] INFO soot.jimple.infoflow.android.SetupApplication - Found 0 leaks"
    print(f"Using target message: '{target_message}'")
    print(f"Message length: {len(target_message)} characters")
    
    source_path = Path(args.source)
    if not source_path.exists() or not source_path.is_dir():
        print(f"Error: Source path '{source_path}' does not exist or is not a directory.")
        sys.exit(1)
    
    # Find all files that contain the message
    print(f"Scanning for log files that contain the 'Found 0 leaks' message...")
    files_with_message = get_files_with_message(source_path, target_message, args.pattern)
    print(f"Found {len(files_with_message)} files with the message.")
    
    # Write results to the output file
    with open(args.output, 'w', encoding='utf-8') as output_file:
        # Write header with summary
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        output_file.write(f"'Found 0 leaks' Log Files Report - {timestamp}\n")
        output_file.write(f"Files that contain the message: {target_message}\n\n")
        output_file.write(f"SUMMARY\n")
        output_file.write(f"-------\n")
        output_file.write(f"Total files with 'Found 0 leaks' message: {len(files_with_message)}\n\n")
        
        # Write the list of files
        output_file.write(f"LIST OF FILES WITH 'FOUND 0 LEAKS' MESSAGE\n")
        output_file.write(f"----------------------------------------\n")
        
        if files_with_message:
            for i, file_path in enumerate(files_with_message, 1):
                output_file.write(f"{i}. {file_path}\n")
        else:
            output_file.write("No files with the 'Found 0 leaks' message were found.\n")
    
    print(f"Report saved to {args.output}")
    
    # Move files if not in dry-run mode
    if not args.dry_run and files_with_message:
        print(f"Moving {len(files_with_message)} files to {args.destination}...")
        moved, failed = move_files(files_with_message, args.destination)
        
        print(f"Successfully moved {len(moved)} files.")
        
        if failed:
            print(f"Failed to move {len(failed)} files:")
            for file_path, error in failed:
                print(f"  {file_path}: {error}")
        
        # Add moved files info to the report
        with open(args.output, 'a', encoding='utf-8') as output_file:
            output_file.write(f"\nMOVED FILES DETAILS\n")
            output_file.write(f"------------------\n")
            
            for source, destination in moved:
                output_file.write(f"From: {source}\n")
                output_file.write(f"To:   {destination}\n\n")
    elif args.dry_run:
        print("Dry run mode: No files were moved.")


if __name__ == "__main__":
    main()