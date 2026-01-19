#!/usr/bin/env python3
"""
log_scanner_other_error.py

This script scans log files to find those containing any "[main] ERROR" messages
that don't match previously identified specific error patterns,
and moves them to a destination folder.
"""

import os
import sys
import argparse
from pathlib import Path
import re
import datetime
import shutil


def check_file_for_generic_error(file_path, exclude_patterns=None):
    """
    Check if a file contains "[main] ERROR" but not any of the excluded patterns.
    
    Args:
        file_path (str): Path to the log file
        exclude_patterns (list): List of error patterns to exclude
    
    Returns:
        tuple: (bool indicating if generic error found, list of actual error messages found)
    """
    generic_error_pattern = r"\[main\] ERROR.*"
    
    if exclude_patterns is None:
        exclude_patterns = []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
            content = file.read()
            
            # Check if there's any generic error
            generic_errors = re.findall(generic_error_pattern, content)
            
            if not generic_errors:
                return False, []
                
            # Filter out the excluded patterns
            other_errors = []
            for error in generic_errors:
                excluded = False
                for pattern in exclude_patterns:
                    if pattern in error:
                        excluded = True
                        break
                if not excluded:
                    other_errors.append(error)
            
            return len(other_errors) > 0, other_errors
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return False, []


def scan_for_other_error_files(search_path, exclude_patterns=None, file_pattern=None):
    """
    Scan directory for log files containing generic errors but not excluded patterns.
    
    Args:
        search_path (Path): File or directory to scan
        exclude_patterns (list): List of error patterns to exclude
        file_pattern (str, optional): Regex pattern to match filenames
    
    Returns:
        dict: Dictionary mapping file paths to lists of error messages found
    """
    matching_files = {}
    pattern = re.compile(file_pattern) if file_pattern else None
    
    if search_path.is_file():
        has_errors, error_messages = check_file_for_generic_error(str(search_path), exclude_patterns)
        if has_errors:
            matching_files[str(search_path)] = error_messages
    elif search_path.is_dir():
        for root, _, files in os.walk(search_path):
            for filename in files:
                # Skip files that don't match the pattern if provided
                if pattern and not pattern.search(filename):
                    continue
                    
                file_path = os.path.join(root, filename)
                has_errors, error_messages = check_file_for_generic_error(file_path, exclude_patterns)
                if has_errors:
                    matching_files[file_path] = error_messages
    
    return matching_files


def main():
    parser = argparse.ArgumentParser(
        description='Scan log files for other error messages and move them.'
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
        default='other_error_report.txt',
        help='Output file to save report (default: other_error_report.txt)'
    )
    parser.add_argument(
        '-m', '--move-to', 
        default='./FlowDroid_output_minor/error/other',
        help='Directory to move files containing errors'
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help='Only generate report without moving files'
    )
    
    args = parser.parse_args()
    
    # Patterns to exclude (previously categorized errors)
    exclude_patterns = [
        "No sinks found, aborting analysis",
        "No sources found, aborting analysis",
        "Could not wait for executor termination"
    ]
    
    search_path = Path(args.directory)
    if not search_path.exists():
        print(f"Error: Directory '{search_path}' does not exist.")
        sys.exit(1)
    
    # Find all files containing other errors
    print(f"Scanning for files containing other '[main] ERROR' messages...")
    matching_files = scan_for_other_error_files(search_path, exclude_patterns, args.pattern)
    print(f"Found {len(matching_files)} files containing other error messages.")
    
    # Write results to the output file
    with open(args.output, 'w', encoding='utf-8') as output_file:
        # Write header with summary
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        output_file.write(f"Other Error Messages Report - {timestamp}\n")
        output_file.write(f"Files containing '[main] ERROR' messages excluding previously categorized errors\n\n")
        output_file.write(f"SUMMARY\n")
        output_file.write(f"-------\n")
        output_file.write(f"Total files with other error messages: {len(matching_files)}\n\n")
        
        # Write the list of files with their error messages
        output_file.write(f"LIST OF FILES CONTAINING OTHER ERRORS\n")
        output_file.write(f"------------------------------------\n")
        
        if matching_files:
            for i, (file_path, error_messages) in enumerate(matching_files.items(), 1):
                output_file.write(f"{i}. {file_path}\n")
                output_file.write(f"   Error messages ({len(error_messages)}):\n")
                for j, error in enumerate(error_messages[:5], 1):  # Show at most 5 errors per file
                    output_file.write(f"   {j}. {error.strip()}\n")
                if len(error_messages) > 5:
                    output_file.write(f"   ... and {len(error_messages) - 5} more error messages\n")
                output_file.write("\n")
        else:
            output_file.write("No files containing other error messages were found.\n")
    
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