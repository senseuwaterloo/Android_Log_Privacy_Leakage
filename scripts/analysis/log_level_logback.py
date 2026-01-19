#!/usr/bin/env python3
"""
Script to analyze CSV file and identify Logback library specific log levels.
Focuses on Logback Classic Logger methods: ERROR, WARN, INFO, DEBUG, TRACE
(ordered from highest to lowest severity)
"""

import pandas as pd
import re
from collections import Counter
import sys

def identify_logback_log_level(sink_text):
    """
    Simple keyword-based identification of Logback log level.
    First check if it's Logback related, then look for keywords.
    """
    if not sink_text or pd.isna(sink_text):
        return 'Unknown'
    
    # Convert to string and normalize
    sink_str = str(sink_text).lower()
    
    # First check if it's Logback related
    if not is_logback_related(sink_str):
        return 'Unknown'
    
    # Simple keyword matching for Logback log levels (highest to lowest severity)
    # Check for ERROR first (highest priority)
    if any(keyword in sink_str for keyword in ['void error(', 'error(']):
        return 'ERROR'
    
    # Check for WARN
    elif any(keyword in sink_str for keyword in ['void warn(', 'warn(']):
        return 'WARN'
    
    # Check for INFO
    elif any(keyword in sink_str for keyword in ['void info(', 'info(']):
        return 'INFO'
    
    # Check for DEBUG
    elif any(keyword in sink_str for keyword in ['void debug(', 'debug(']):
        return 'DEBUG'
    
    # Check for TRACE
    elif any(keyword in sink_str for keyword in ['void trace(', 'trace(']):
        return 'TRACE'
    
    # Check for generic log() methods
    elif any(keyword in sink_str for keyword in ['void log(', 'log(']):
        return 'GENERIC_LOG'
    
    # Check for appender methods (output/sink points)
    elif any(keyword in sink_str for keyword in ['doappend', 'writeout', 'callappenders', 'appendloopOnappenders']):
        return 'APPENDER'
    
    else:
        return 'LOGBACK_OTHER'

def is_logback_related(sink_text):
    """
    Check if the sink text is specifically related to Logback logging.
    Only matches explicit Logback references to avoid false positives.
    """
    if not sink_text or pd.isna(sink_text):
        return False
    
    sink_str = str(sink_text).lower()
    
    # Strict Logback-only indicators
    logback_indicators = [
        'ch.qos.logback',           # Full Logback package name
        'logback',                  # Direct reference to logback
    ]
    
    # Additional check for common Logback patterns
    logback_patterns = [
        'ch.qos.logback.classic.logger',    # Logback Classic Logger
        'ch.qos.logback.core',              # Logback Core components
        'logback.classic',                  # Classic module
        'logback.core',                     # Core module
        'logcatappender',                   # Android Logcat appender
        'rollingfileappender',              # Rolling file appender
        'consoleappender',                  # Console appender
        'fileappender',                     # File appender
        'appenderbase',                     # Base appender class
    ]
    
    # Check for direct Logback references
    for indicator in logback_indicators:
        if indicator in sink_str:
            return True
    
    # Check for Logback-specific patterns
    for pattern in logback_patterns:
        if pattern in sink_str:
            return True
    
    return False

def analyze_logback_log_levels(filename, logback_only=True):
    """
    Analyze the CSV file specifically for Logback log levels.
    
    Args:
        filename: CSV file to analyze
        logback_only: If True, only analyze Logback-related entries
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
        
        # Filter for Logback-related entries if requested
        if logback_only:
            df['is_logback'] = df['sink'].apply(lambda x: is_logback_related(str(x)))
            logback_df = df[df['is_logback']].copy()
            print(f"Logback-related rows: {len(logback_df)}")
            print("-" * 50)
            
            if len(logback_df) == 0:
                print("No Logback-related log entries found!")
                return
            
            analysis_df = logback_df
        else:
            analysis_df = df.copy()
            print("-" * 50)
        
        # Identify Logback log levels for each row
        analysis_df['logback_log_level'] = analysis_df['sink'].apply(identify_logback_log_level)
        
        # Count occurrences of each log level
        level_counts = analysis_df['logback_log_level'].value_counts()
        
        print("Logback Log Level Distribution:")
        print("=" * 40)
        
        # Define Logback standard order (highest to lowest severity)
        logback_levels = ['ERROR', 'WARN', 'INFO', 'DEBUG', 'TRACE']
        other_levels = [level for level in level_counts.index if level not in logback_levels]
        
        total_entries = len(analysis_df)
        
        # Show Logback standard levels first
        print("Logback Standard Levels (highest to lowest severity):")
        print("-" * 20)
        for level in logback_levels:
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
        print("\nExamples by Logback Log Level:")
        print("=" * 50)
        
        for level in level_counts.index:
            if level_counts[level] > 0:
                samples = analysis_df[analysis_df['logback_log_level'] == level]['sink'].head(3)
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
        suffix = '_logback_only' if logback_only else '_all'
        
        # Detailed output
        output_filename = filename.replace('.csv', f'{suffix}_log_levels.csv')
        if 'app_name' in analysis_df.columns:
            analysis_df[['app_name', 'sink', 'logback_log_level']].to_csv(output_filename, index=False, mode='w')
        else:
            analysis_df[['sink', 'logback_log_level']].to_csv(output_filename, index=False, mode='w')
        print(f"\nDetailed Logback log level analysis saved to: {output_filename}")
        
        # Summary output
        summary_filename = filename.replace('.csv', f'{suffix}_log_level_summary.csv')
        summary_df = pd.DataFrame({
            'logback_log_level': level_counts.index,
            'count': level_counts.values,
            'percentage': (level_counts.values / total_entries * 100).round(1)
        })
        summary_df.to_csv(summary_filename, index=False, mode='w')
        print(f"Logback log level summary saved to: {summary_filename}")
        
        # Show statistics for Logback standard levels only
        standard_level_counts = {level: level_counts.get(level, 0) for level in logback_levels}
        standard_total = sum(standard_level_counts.values())
        
        if standard_total > 0:
            print(f"\nLogback Standard Levels Summary:")
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
    Test function to verify the simple keyword matching works correctly for Logback.
    """
    test_cases = [
        "<ch.qos.logback.classic.Logger: void error(java.lang.String)>",
        "<ch.qos.logback.classic.Logger: void warn(java.lang.String,java.lang.Object)>",
        "<ch.qos.logback.classic.Logger: void info(java.lang.String,java.lang.Object[])>",
        "<ch.qos.logback.classic.Logger: void debug(java.lang.String,java.lang.Throwable)>",
        "<ch.qos.logback.classic.Logger: void trace(org.slf4j.Marker,java.lang.String)>",
        "<ch.qos.logback.classic.Logger: void log(org.slf4j.Marker,java.lang.String,int,java.lang.String,java.lang.Object[],java.lang.Throwable)>",
        "<ch.qos.logback.core.FileAppender: void doAppend(java.lang.Object)>",
        "<ch.qos.logback.core.ConsoleAppender: void doAppend(java.lang.Object)>",
        "<ch.qos.logback.classic.Logger: void callAppenders(ch.qos.logback.classic.spi.ILoggingEvent)>",
        "some other logger that is not logback"
    ]
    
    print("Testing Logback keyword matching:")
    print("-" * 60)
    for test in test_cases:
        result = identify_logback_log_level(test)
        logback_check = is_logback_related(test.lower())
        print(f"Input: {test[:60]}...")
        print(f"Is Logback: {logback_check}")
        print(f"Log Level: {result}")
        print()

def main():
    """
    Main function to run the Logback log level analysis.
    """
    # Default filename
    filename = './results/processed_data/flowdriod_outcome_2/flowdroid_data_flows.csv'
    logback_only = True
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    
    # Check for flags
    if len(sys.argv) > 2:
        if sys.argv[2].lower() in ['--all', '-a']:
            logback_only = False
        elif sys.argv[2].lower() in ['--test', '-t']:
            test_patterns()
            return
    
    print(f"Analyzing Logback log levels in: {filename}")
    if logback_only:
        print("Mode: Logback entries only")
    else:
        print("Mode: All entries")
    print("=" * 60)
    
    results = analyze_logback_log_levels(filename, logback_only)
    
    if results is not None:
        print(f"\nAnalysis complete!")
        print(f"Found {len(results)} different log level categories.")
        print(f"\nUsage: python3 {sys.argv[0]} [filename.csv] [--all|-a] [--test|-t]")
        print(f"  --all or -a: Analyze all entries, not just Logback-related ones")
        print(f"  --test or -t: Test keyword patterns with sample data")

if __name__ == "__main__":
    main()