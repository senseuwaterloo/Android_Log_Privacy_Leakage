#!/usr/bin/env python3
"""
Script to analyze CSV file and identify Timber library specific log levels.
Focuses on Timber logging methods: FATAL, ERROR, WARN, INFO, DEBUG, TRACE
(ordered from highest to lowest severity)
"""

import pandas as pd
import re
from collections import Counter
import sys

def identify_timber_log_level(sink_text):
    """
    Simple keyword-based identification of Timber log level.
    First check if it's Timber related, then look for keywords including single-letter methods.
    """
    if not sink_text or pd.isna(sink_text):
        return 'Unknown'
    
    # Convert to string and normalize
    sink_str = str(sink_text).lower()
    
    # First check if it's Timber related
    if not is_timber_related(sink_str):
        return 'Unknown'
    
    # Simple keyword matching for Timber log levels (highest to lowest severity)
    # Check for FATAL first (highest priority)
    if any(keyword in sink_str for keyword in ['fatal', 'wtf']):
        return 'FATAL'
    
    # Check for ERROR - look for 'void e(' pattern specifically
    elif any(keyword in sink_str for keyword in ['void error(', 'void e(']):
        return 'ERROR'
    
    # Check for WARN - look for 'void w(' pattern specifically  
    elif any(keyword in sink_str for keyword in ['void warn(', 'void w(']):
        return 'WARN'
    
    # Check for INFO - look for 'void i(' pattern specifically
    elif any(keyword in sink_str for keyword in ['void info(', 'void i(']):
        return 'INFO'
    
    # Check for DEBUG - look for 'void d(' pattern specifically
    elif any(keyword in sink_str for keyword in ['void debug(', 'void d(']):
        return 'DEBUG'
    
    # Check for TRACE - look for 'void v(' pattern specifically
    elif any(keyword in sink_str for keyword in ['void trace(', 'void v(']):
        return 'TRACE'
    
    else:
        return 'TIMBER_OTHER'

def is_timber_related(sink_text):
    """
    Check if the sink text is specifically related to Timber logging.
    Only matches explicit Timber references to avoid false positives.
    """
    if not sink_text or pd.isna(sink_text):
        return False
    
    sink_str = str(sink_text).lower()
    
    # Strict Timber-only indicators
    timber_indicators = [
        'timber',              # Direct reference to timber
        'com.jakewharton.timber',  # Full package name
        'jakewharton.timber',  # Partial package name
    ]
    
    # Additional check for common Timber patterns
    timber_patterns = [
        'timber.plant',        # Timber.plant() method
        'timber.tree',         # Timber.Tree class
        'timber.debugtree',    # Timber.DebugTree
        'timber.log',          # Timber logging methods
        'timber.tag',          # Timber.tag() method
    ]
    
    # Check for direct Timber references
    for indicator in timber_indicators:
        if indicator in sink_str:
            return True
    
    # Check for Timber-specific patterns
    for pattern in timber_patterns:
        if pattern in sink_str:
            return True
    
    return False

def analyze_timber_log_levels(filename, timber_only=True):
    """
    Analyze the CSV file specifically for Timber log levels.
    
    Args:
        filename: CSV file to analyze
        timber_only: If True, only analyze Timber-related entries
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
        
        # Filter for Timber-related entries if requested
        if timber_only:
            df['is_timber'] = df['sink'].apply(lambda x: is_timber_related(str(x)))
            timber_df = df[df['is_timber']].copy()
            print(f"Timber-related rows: {len(timber_df)}")
            print("-" * 50)
            
            if len(timber_df) == 0:
                print("No Timber-related log entries found!")
                return
            
            analysis_df = timber_df
        else:
            analysis_df = df.copy()
            print("-" * 50)
        
        # Identify Timber log levels for each row
        analysis_df['timber_log_level'] = analysis_df['sink'].apply(identify_timber_log_level)
        
        # Count occurrences of each log level
        level_counts = analysis_df['timber_log_level'].value_counts()
        
        print("Timber Log Level Distribution:")
        print("=" * 40)
        
        # Define Timber standard order (highest to lowest severity)
        timber_levels = ['FATAL', 'ERROR', 'WARN', 'INFO', 'DEBUG', 'TRACE']
        other_levels = [level for level in level_counts.index if level not in timber_levels]
        
        total_entries = len(analysis_df)
        
        # Show Timber standard levels first
        print("Timber Standard Levels (highest to lowest severity):")
        print("-" * 20)
        for level in timber_levels:
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
        print("\nExamples by Timber Log Level:")
        print("=" * 50)
        
        for level in level_counts.index:
            if level_counts[level] > 0:
                samples = analysis_df[analysis_df['timber_log_level'] == level]['sink'].head(3)
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
        suffix = '_timber_only' if timber_only else '_all'
        
        # Detailed output
        output_filename = filename.replace('.csv', f'{suffix}_log_levels.csv')
        if 'app_name' in analysis_df.columns:
            analysis_df[['app_name', 'sink', 'timber_log_level']].to_csv(output_filename, index=False, mode='w')
        else:
            analysis_df[['sink', 'timber_log_level']].to_csv(output_filename, index=False, mode='w')
        print(f"\nDetailed Timber log level analysis saved to: {output_filename}")
        
        # Summary output
        summary_filename = filename.replace('.csv', f'{suffix}_log_level_summary.csv')
        summary_df = pd.DataFrame({
            'timber_log_level': level_counts.index,
            'count': level_counts.values,
            'percentage': (level_counts.values / total_entries * 100).round(1)
        })
        summary_df.to_csv(summary_filename, index=False, mode='w')
        print(f"Timber log level summary saved to: {summary_filename}")
        
        # Show statistics for Timber standard levels only
        standard_level_counts = {level: level_counts.get(level, 0) for level in timber_levels}
        standard_total = sum(standard_level_counts.values())
        
        if standard_total > 0:
            print(f"\nTimber Standard Levels Summary:")
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
    Test function to verify the simple keyword matching works correctly for Timber.
    """
    test_cases = [
        "Timber.wtf('Fatal error occurred')",
        "Timber.e('Error message')",
        "Timber.w('Warning message')", 
        "Timber.i('Info message')",
        "Timber.d('Debug message')",
        "Timber.v('Verbose trace message')",
        "com.jakewharton.timber.Timber.plant(new DebugTree())",
        "timber.log.error('Error via log method')",
        "staticinvoke <timber.log.Timber: void i(java.lang.String,java.lang.Object[])>($r2, $r3)",
        "staticinvoke <timber.log.Timber: void e(java.lang.String,java.lang.Object[])>($r2, $r3)",
        "staticinvoke <timber.log.Timber: void d(java.lang.String,java.lang.Object[])>($r2, $r3)",
        "staticinvoke <timber.log.Timber: void w(java.lang.String,java.lang.Object[])>($r2, $r3)",
        "some other logger that is not timber"
    ]
    
    print("Testing Timber keyword matching (including bytecode patterns):")
    print("-" * 60)
    for test in test_cases:
        result = identify_timber_log_level(test)
        timber_check = is_timber_related(test.lower())
        print(f"Input: {test[:60]}...")
        print(f"Is Timber: {timber_check}")
        print(f"Log Level: {result}")
        print()

def main():
    """
    Main function to run the Timber log level analysis.
    """
    # Default filename
    filename = './results/processed_data/flowdriod_outcome_2/flowdroid_data_flows.csv'
    timber_only = True
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    
    # Check for flags
    if len(sys.argv) > 2:
        if sys.argv[2].lower() in ['--all', '-a']:
            timber_only = False
        elif sys.argv[2].lower() in ['--test', '-t']:
            test_patterns()
            return
    
    print(f"Analyzing Timber log levels in: {filename}")
    if timber_only:
        print("Mode: Timber entries only")
    else:
        print("Mode: All entries")
    print("=" * 60)
    
    results = analyze_timber_log_levels(filename, timber_only)
    
    if results is not None:
        print(f"\nAnalysis complete!")
        print(f"Found {len(results)} different log level categories.")
        print(f"\nUsage: python3 {sys.argv[0]} [filename.csv] [--all|-a] [--test|-t]")
        print(f"  --all or -a: Analyze all entries, not just Timber-related ones")
        print(f"  --test or -t: Test keyword patterns with sample data")

if __name__ == "__main__":
    main()