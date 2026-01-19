#!/usr/bin/env python3
"""
Script to analyze CSV file and identify Orhanobut Logger library specific log levels.
Focuses on com.orhanobut.logger.Logger methods: VERBOSE, DEBUG, INFO, WARN, ERROR, WTF
(ordered from most to least detailed)
"""

import pandas as pd
import re
from collections import Counter
import sys

def identify_orhanobut_log_level(sink_text):
    """
    Simple keyword-based identification of Orhanobut Logger level.
    First check if it's Orhanobut Logger related, then look for keywords.
    Only classify the 6 standard log levels, everything else is OTHERS.
    """
    if not sink_text or pd.isna(sink_text):
        return 'Unknown'
    
    # Convert to string and normalize
    sink_str = str(sink_text).lower()
    
    # First check if it's Orhanobut Logger related
    if not is_orhanobut_logger_related(sink_str):
        return 'Unknown'
    
    # Simple keyword matching for Orhanobut Logger levels (ordered by detail level)
    # Check for WTF first (most critical)
    if any(keyword in sink_str for keyword in ['void wtf(', '.wtf(', 'wtf(']):
        return 'WTF'
    
    # Check for ERROR
    elif any(keyword in sink_str for keyword in ['void e(', '.e(']):
        return 'ERROR'
    
    # Check for WARN
    elif any(keyword in sink_str for keyword in ['void w(', '.w(']):
        return 'WARN'
    
    # Check for INFO
    elif any(keyword in sink_str for keyword in ['void i(', '.i(']):
        return 'INFO'
    
    # Check for DEBUG
    elif any(keyword in sink_str for keyword in ['void d(', '.d(']):
        return 'DEBUG'
    
    # Check for VERBOSE
    elif any(keyword in sink_str for keyword in ['void v(', '.v(']):
        return 'VERBOSE'
    
    # Everything else that's Orhanobut Logger related but not the 6 standard levels
    else:
        return 'OTHERS'

def is_orhanobut_logger_related(sink_text):
    """
    Check if the sink text is specifically related to Orhanobut Logger library.
    Only matches explicit Orhanobut Logger references to avoid false positives.
    """
    if not sink_text or pd.isna(sink_text):
        return False
    
    sink_str = str(sink_text).lower()
    
    # Strict Orhanobut Logger-only indicators
    orhanobut_indicators = [
        'com.orhanobut.logger',     # Full package name
        'orhanobut.logger',         # Partial package name
    ]
    
    # Additional check for common Orhanobut Logger patterns
    orhanobut_patterns = [
        'com.orhanobut.logger.logger',          # Main Logger class
        'com.orhanobut.logger.androidlogadapter', # Android adapter
        'com.orhanobut.logger.disklogadapter',    # Disk adapter
        'com.orhanobut.logger.logadapter',        # Base adapter
        'com.orhanobut.logger.printer',           # Printer class
        'com.orhanobut.logger.prettyformatstrategy', # Pretty format
        'com.orhanobut.logger.csvformatstrategy',    # CSV format
        'com.orhanobut.logger.formatstrategy',       # Base format strategy
    ]
    
    # Check for direct Orhanobut Logger references
    for indicator in orhanobut_indicators:
        if indicator in sink_str:
            return True
    
    # Check for Orhanobut Logger-specific patterns
    for pattern in orhanobut_patterns:
        if pattern in sink_str:
            return True
    
    return False

def analyze_orhanobut_log_levels(filename, orhanobut_only=True):
    """
    Analyze the CSV file specifically for Orhanobut Logger levels.
    
    Args:
        filename: CSV file to analyze
        orhanobut_only: If True, only analyze Orhanobut Logger-related entries
    """
    try:
        # Read the CSV file
        df = pd.read_csv(filename)
        
        # Check if 'sink' column exists
        if 'sink' not in df.columns:
            print(f"Error: 'sink' column not found in {filename}")
            print(f"Available columns: {list(df.columns)}")
            return
        
        print(f"Successfully loaded {filename}")
        print(f"Total rows: {len(df)}")
        
        # Filter for Orhanobut Logger-related entries if requested
        if orhanobut_only:
            df['is_orhanobut'] = df['sink'].apply(lambda x: is_orhanobut_logger_related(str(x)))
            orhanobut_df = df[df['is_orhanobut']].copy()
            print(f"Orhanobut Logger-related rows: {len(orhanobut_df)}")
            print("-" * 50)
            
            if len(orhanobut_df) == 0:
                print("No Orhanobut Logger-related entries found!")
                return
            
            analysis_df = orhanobut_df
        else:
            analysis_df = df.copy()
            print("-" * 50)
        
        # Identify Orhanobut Logger levels for each row
        analysis_df['orhanobut_log_level'] = analysis_df['sink'].apply(identify_orhanobut_log_level)
        
        # Count occurrences of each log level
        level_counts = analysis_df['orhanobut_log_level'].value_counts()
        
        print("Orhanobut Logger Level Distribution:")
        print("=" * 40)
        
        # Define Orhanobut Logger order (most to least detailed)
        orhanobut_levels = ['VERBOSE', 'DEBUG', 'INFO', 'WARN', 'ERROR', 'WTF']
        other_levels = [level for level in level_counts.index if level not in orhanobut_levels]
        
        total_entries = len(analysis_df)
        
        # Show Orhanobut Logger standard levels first
        print("Orhanobut Logger Standard Levels (most to least detailed):")
        print("-" * 20)
        for level in orhanobut_levels:
            count = level_counts.get(level, 0)
            percentage = (count / total_entries) * 100 if total_entries > 0 else 0
            # Add method names for clarity
            method_map = {
                'VERBOSE': 'v()',
                'DEBUG': 'd()', 
                'INFO': 'i()',
                'WARN': 'w()',
                'ERROR': 'e()',
                'WTF': 'wtf()'
            }
            method_name = method_map.get(level, '')
            print(f"{level:<10} {method_name:<6}: {count:>4} ({percentage:>5.1f}%)")
        
        # Show other categories (should mainly be OTHERS now)
        if other_levels:
            print("\nOther Categories:")
            print("-" * 20)
            for level in other_levels:
                count = level_counts[level]
                percentage = (count / total_entries) * 100
                print(f"{level:<15}: {count:>4} ({percentage:>5.1f}%)")
        
        print("-" * 40)
        print(f"{'Total':<15}: {total_entries:>4} (100.0%)")
        
        # Show examples for each level found
        print("\nExamples by Orhanobut Logger Level:")
        print("=" * 50)
        
        for level in level_counts.index:
            if level_counts[level] > 0:
                samples = analysis_df[analysis_df['orhanobut_log_level'] == level]['sink'].head(3)
                print(f"\n{level} ({level_counts[level]} occurrences):")
                for i, sample in enumerate(samples, 1):
                    # Clean up the display
                    if 'Statement:' in sample:
                        method_part = sample.split('Statement:')[1].strip()
                        display_text = method_part[:100] + "..." if len(method_part) > 100 else method_part
                    else:
                        display_text = sample[:100] + "..." if len(sample) > 100 else sample
                    print(f"  {i}. {display_text}")
                    if i >= 2:  # Limit to 2 examples per level
                        break
        
        # Save detailed results
        suffix = '_orhanobut_only' if orhanobut_only else '_all'
        
        # Detailed output
        output_filename = filename.replace('.csv', f'{suffix}_log_levels.csv')
        if 'app_name' in analysis_df.columns:
            analysis_df[['app_name', 'sink', 'orhanobut_log_level']].to_csv(output_filename, index=False, mode='w')
        else:
            analysis_df[['sink', 'orhanobut_log_level']].to_csv(output_filename, index=False, mode='w')
        print(f"\nDetailed Orhanobut Logger level analysis saved to: {output_filename}")
        
        # Summary output
        summary_filename = filename.replace('.csv', f'{suffix}_log_level_summary.csv')
        summary_df = pd.DataFrame({
            'orhanobut_log_level': level_counts.index,
            'count': level_counts.values,
            'percentage': (level_counts.values / total_entries * 100).round(1)
        })
        summary_df.to_csv(summary_filename, index=False, mode='w')
        print(f"Orhanobut Logger level summary saved to: {summary_filename}")
        
        # Show statistics for Orhanobut Logger standard levels only
        standard_level_counts = {level: level_counts.get(level, 0) for level in orhanobut_levels}
        standard_total = sum(standard_level_counts.values())
        
        if standard_total > 0:
            print(f"\nOrhanobut Logger Standard Levels Summary:")
            print(f"Total standard log calls: {standard_total}")
            print(f"Percentage of analyzed data: {(standard_total/total_entries)*100:.1f}%")
        
        return level_counts
        
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        return None
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        return None

def test_patterns():
    """
    Test function to verify the simple keyword matching works correctly for Orhanobut Logger.
    """
    test_cases = [
        "<com.orhanobut.logger.Logger: void v(java.lang.String,java.lang.Object[])>",
        "<com.orhanobut.logger.Logger: void d(java.lang.Object)>",
        "<com.orhanobut.logger.Logger: void i(java.lang.String,java.lang.Object[])>",
        "<com.orhanobut.logger.Logger: void w(java.lang.Object)>",
        "<com.orhanobut.logger.Logger: void e(java.lang.Throwable)>",
        "<com.orhanobut.logger.Logger: void wtf(java.lang.String,java.lang.Object[])>",
        "<com.orhanobut.logger.Logger: void json(java.lang.String)>",
        "<com.orhanobut.logger.Logger: void xml(java.lang.String)>",
        "<com.orhanobut.logger.Logger: void log(int,java.lang.String,java.lang.String)>",
        "<com.orhanobut.logger.AndroidLogAdapter: void log(int,java.lang.String,java.lang.String)>",
        "<com.orhanobut.logger.PrettyFormatStrategy: void log(int,java.lang.String,java.lang.String)>",
        "some other logger that is not orhanobut"
    ]
    
    print("Testing Orhanobut Logger keyword matching:")
    print("-" * 60)
    for test in test_cases:
        result = identify_orhanobut_log_level(test)
        orhanobut_check = is_orhanobut_logger_related(test.lower())
        print(f"Input: {test[:60]}...")
        print(f"Is Orhanobut Logger: {orhanobut_check}")
        print(f"Log Level: {result}")
        print()

def main():
    """
    Main function to run the Orhanobut Logger level analysis.
    """
    # Default filename
    filename = './results/processed_data/flowdriod_outcome_2/flowdroid_data_flows.csv'
    orhanobut_only = True
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    
    # Check for flags
    if len(sys.argv) > 2:
        if sys.argv[2].lower() in ['--all', '-a']:
            orhanobut_only = False
        elif sys.argv[2].lower() in ['--test', '-t']:
            test_patterns()
            return
    
    print(f"Analyzing Orhanobut Logger levels in: {filename}")
    if orhanobut_only:
        print("Mode: Orhanobut Logger entries only")
    else:
        print("Mode: All entries")
    print("=" * 60)
    
    results = analyze_orhanobut_log_levels(filename, orhanobut_only)
    
    if results is not None:
        print(f"\nAnalysis complete!")
        print(f"Found {len(results)} different log level categories.")
        print(f"\nUsage: python3 {sys.argv[0]} [filename.csv] [--all|-a] [--test|-t]")
        print(f"  --all or -a: Analyze all entries, not just Orhanobut Logger-related ones")
        print(f"  --test or -t: Test keyword patterns with sample data")

if __name__ == "__main__":
    main()