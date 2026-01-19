#!/usr/bin/env python3
"""
Script to analyze CSV file and identify SLF4J specific log levels.
Focuses on SLF4J Logger interface methods: ERROR, WARN, INFO, DEBUG, TRACE
"""

import pandas as pd
import re
from collections import Counter
import sys

def identify_slf4j_log_level(sink_text):
    """
    Simple keyword-based identification of SLF4J log level.
    First check if it's SLF4J related, then look for keywords.
    """
    if not sink_text or pd.isna(sink_text):
        return 'Unknown'
    
    # Convert to string and normalize
    sink_str = str(sink_text).lower()
    
    # First check if it's SLF4J related
    if not ('org.slf4j' in sink_str or 'slf4j' in sink_str):
        return 'Unknown'
    
    # Simple keyword matching for SLF4J log levels
    if 'error' in sink_str:
        return 'ERROR'
    elif 'warn' in sink_str:
        return 'WARN'
    elif 'info' in sink_str:
        return 'INFO'
    elif 'debug' in sink_str:
        return 'DEBUG'
    elif 'trace' in sink_str:
        return 'TRACE'
    else:
        return 'SLF4J_OTHER'

def is_slf4j_related(sink_text):
    """
    Check if the sink text is specifically related to SLF4J logging.
    Only matches explicit SLF4J references to avoid false positives.
    """
    if not sink_text or pd.isna(sink_text):
        return False
    
    sink_str = str(sink_text).lower()
    
    # Strict SLF4J-only indicators
    slf4j_indicators = [
        'org.slf4j',           # Full package name
        'slf4j',               # Direct reference to slf4j
    ]
    
    # Additional check for common SLF4J Logger patterns
    slf4j_logger_patterns = [
        'org.slf4j.logger',
        'slf4j.logger',
        'loggerfactory.getlogger',  # SLF4J LoggerFactory pattern
        'org.slf4j.loggerfactory'
    ]
    
    # Check for direct SLF4J references
    for indicator in slf4j_indicators:
        if indicator in sink_str:
            return True
    
    # Check for SLF4J logger patterns
    for pattern in slf4j_logger_patterns:
        if pattern in sink_str:
            return True
    
    return False

def analyze_slf4j_log_levels(filename, slf4j_only=True):
    """
    Analyze the CSV file specifically for SLF4J log levels.
    
    Args:
        filename: CSV file to analyze
        slf4j_only: If True, only analyze SLF4J-related entries
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
        
        # Filter for SLF4J-related entries if requested
        if slf4j_only:
            df['is_slf4j'] = df['sink'].apply(is_slf4j_related)
            slf4j_df = df[df['is_slf4j']].copy()
            print(f"SLF4J-related rows: {len(slf4j_df)}")
            print("-" * 50)
            
            if len(slf4j_df) == 0:
                print("No SLF4J-related log entries found!")
                return
            
            analysis_df = slf4j_df
        else:
            analysis_df = df.copy()
            print("-" * 50)
        
        # Identify SLF4J log levels for each row
        analysis_df['slf4j_log_level'] = analysis_df['sink'].apply(identify_slf4j_log_level)
        
        # Count occurrences of each log level
        level_counts = analysis_df['slf4j_log_level'].value_counts()
        
        print("SLF4J Log Level Distribution:")
        print("=" * 40)
        
        # Define SLF4J standard order (highest to lowest severity)
        slf4j_levels = ['ERROR', 'WARN', 'INFO', 'DEBUG', 'TRACE']
        other_levels = [level for level in level_counts.index if level not in slf4j_levels]
        
        total_entries = len(analysis_df)
        
        # Show SLF4J standard levels first
        print("SLF4J Standard Levels (highest to lowest severity):")
        print("-" * 20)
        for level in slf4j_levels:
            count = level_counts.get(level, 0)
            percentage = (count / total_entries) * 100 if total_entries > 0 else 0
            print(f"{level:<10}: {count:>4} ({percentage:>5.1f}%)")
        
        # Show other categories
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
        print("\nExamples by SLF4J Log Level:")
        print("=" * 50)
        
        for level in level_counts.index:
            if level_counts[level] > 0:
                samples = analysis_df[analysis_df['slf4j_log_level'] == level]['sink'].head(3)
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
        suffix = '_slf4j_only' if slf4j_only else '_all'
        
        # Detailed output
        output_filename = filename.replace('.csv', f'{suffix}_log_levels.csv')
        if 'app_name' in analysis_df.columns:
            analysis_df[['app_name', 'sink', 'slf4j_log_level']].to_csv(output_filename, index=False, mode='w')
        else:
            analysis_df[['sink', 'slf4j_log_level']].to_csv(output_filename, index=False, mode='w')
        print(f"\nDetailed SLF4J log level analysis saved to: {output_filename}")
        
        # Summary output
        summary_filename = filename.replace('.csv', f'{suffix}_log_level_summary.csv')
        summary_df = pd.DataFrame({
            'slf4j_log_level': level_counts.index,
            'count': level_counts.values,
            'percentage': (level_counts.values / total_entries * 100).round(1)
        })
        summary_df.to_csv(summary_filename, index=False, mode='w')
        print(f"SLF4J log level summary saved to: {summary_filename}")
        
        # Show statistics for SLF4J standard levels only
        standard_level_counts = {level: level_counts.get(level, 0) for level in slf4j_levels}
        standard_total = sum(standard_level_counts.values())
        
        if standard_total > 0:
            print(f"\nSLF4J Standard Levels Summary:")
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
    Test function to verify the simple keyword matching works correctly.
    """
    test_cases = [
        "interfaceinvoke $r7.<org.slf4j.Logger: void error(java.lang.String)>($r2)",
        "interfaceinvoke $r3.<org.slf4j.Logger: void info(java.lang.String)>($r6)",
        "interfaceinvoke $r4.<org.slf4j.Logger: void warn(java.lang.String)>($r7)",
        "interfaceinvoke $r5.<org.slf4j.Logger: void debug(java.lang.String)>($r8)",
        "interfaceinvoke $r6.<org.slf4j.Logger: void trace(java.lang.String)>($r9)",
        "some other logger that is not slf4j"
    ]
    
    print("Testing simple keyword matching:")
    print("-" * 40)
    for test in test_cases:
        result = identify_slf4j_log_level(test)
        print(f"Input: {test[:50]}...")
        print(f"Result: {result}")
        print()

def main():
    """
    Main function to run the SLF4J log level analysis.
    """
    # Default filename
    filename = './results/processed_data/flowdriod_outcome_2/flowdroid_data_flows.csv'
    slf4j_only = True
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    
    # Check for flags
    if len(sys.argv) > 2:
        if sys.argv[2].lower() in ['--all', '-a']:
            slf4j_only = False
        elif sys.argv[2].lower() in ['--test', '-t']:
            test_patterns()
            return
    
    print(f"Analyzing SLF4J log levels in: {filename}")
    if slf4j_only:
        print("Mode: SLF4J entries only")
    else:
        print("Mode: All entries")
    print("=" * 60)
    
    results = analyze_slf4j_log_levels(filename, slf4j_only)
    
    if results is not None:
        print(f"\nAnalysis complete!")
        print(f"Found {len(results)} different log level categories.")
        print(f"\nUsage: python3 {sys.argv[0]} [filename.csv] [--all|-a] [--test|-t]")
        print(f"  --all or -a: Analyze all entries, not just SLF4J-related ones")
        print(f"  --test or -t: Test regex patterns with sample data")

if __name__ == "__main__":
    main()