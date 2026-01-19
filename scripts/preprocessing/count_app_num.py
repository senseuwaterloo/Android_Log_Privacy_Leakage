import pandas as pd
import os

def combine_csv_and_count_apps(file1_path, file2_path):
    """
    Combine two CSV files and calculate the number of unique apps
    
    Args:
        file1_path (str): Path to source_no_toString.csv
        file2_path (str): Path to source_toString_notNoise.csv
    """
    
    # Read the first CSV file
    try:
        df1 = pd.read_csv(file1_path)
        print(f"Successfully loaded {file1_path}")
        print(f"- Rows: {len(df1)}, Columns: {len(df1.columns)}")
        print(f"- Columns: {list(df1.columns)}")
        
    except FileNotFoundError:
        print(f"Error: File '{file1_path}' not found.")
        return
    except Exception as e:
        print(f"Error reading {file1_path}: {e}")
        return
    
    # Read the second CSV file
    try:
        df2 = pd.read_csv(file2_path)
        print(f"\nSuccessfully loaded {file2_path}")
        print(f"- Rows: {len(df2)}, Columns: {len(df2.columns)}")
        print(f"- Columns: {list(df2.columns)}")
        
    except FileNotFoundError:
        print(f"Error: File '{file2_path}' not found.")
        return
    except Exception as e:
        print(f"Error reading {file2_path}: {e}")
        return
    
    # Check if both files have the same columns
    if list(df1.columns) != list(df2.columns):
        print("\nWarning: The files have different columns!")
        print(f"File 1 columns: {list(df1.columns)}")
        print(f"File 2 columns: {list(df2.columns)}")
        
        # Find common columns
        common_columns = list(set(df1.columns) & set(df2.columns))
        print(f"Common columns: {common_columns}")
        
        if len(common_columns) > 0:
            print("Proceeding with common columns only...")
            df1 = df1[common_columns]
            df2 = df2[common_columns]
        else:
            print("No common columns found. Cannot combine files.")
            return
    
    # Combine the dataframes
    combined_df = pd.concat([df1, df2], ignore_index=True)
    print(f"\nCombined DataFrame:")
    print(f"- Total rows: {len(combined_df)}")
    print(f"- Columns: {list(combined_df.columns)}")
    
    # Check if 'app_name' column exists for counting unique apps
    if 'app_name' in combined_df.columns:
        # Count unique apps
        unique_apps_df1 = df1['app_name'].nunique()
        unique_apps_df2 = df2['app_name'].nunique()
        unique_apps_combined = combined_df['app_name'].nunique()
        
        print(f"\nApp Statistics:")
        print(f"- Unique apps in {os.path.basename(file1_path)}: {unique_apps_df1}")
        print(f"- Unique apps in {os.path.basename(file2_path)}: {unique_apps_df2}")
        print(f"- Total unique apps in combined data: {unique_apps_combined}")
        
        # Calculate overlap
        apps_df1 = set(df1['app_name'].unique())
        apps_df2 = set(df2['app_name'].unique())
        overlap = len(apps_df1 & apps_df2)
        only_df1 = len(apps_df1 - apps_df2)
        only_df2 = len(apps_df2 - apps_df1)
        
        print(f"\nApp Overlap Analysis:")
        print(f"- Apps appearing in both files: {overlap}")
        print(f"- Apps only in {os.path.basename(file1_path)}: {only_df1}")
        print(f"- Apps only in {os.path.basename(file2_path)}: {only_df2}")
        
        # Show sample of unique apps from each file
        print(f"\nSample apps from {os.path.basename(file1_path)} (first 5):")
        for i, app in enumerate(df1['app_name'].unique()[:5], 1):
            print(f"  {i}. {app}")
            
        print(f"\nSample apps from {os.path.basename(file2_path)} (first 5):")
        for i, app in enumerate(df2['app_name'].unique()[:5], 1):
            print(f"  {i}. {app}")
            
    else:
        print(f"\nWarning: 'app_name' column not found in the data.")
        print(f"Available columns: {list(combined_df.columns)}")
        print("Cannot calculate unique app statistics.")
    
    # Save the combined file
    output_dir = os.path.dirname(file1_path)  # Save in same directory as first file
    output_file = os.path.join(output_dir, 'rq1_no_noise.csv')
    
    try:
        combined_df.to_csv(output_file, index=False)
        print(f"\nSuccessfully saved combined data to:")
        print(f"- {output_file}")
        print(f"- Total rows saved: {len(combined_df)}")
        
    except Exception as e:
        print(f"Error saving combined CSV file: {e}")
    
    # Additional statistics
    print(f"\nAdditional Statistics:")
    print(f"- Rows from file 1: {len(df1)} ({len(df1)/len(combined_df)*100:.1f}%)")
    print(f"- Rows from file 2: {len(df2)} ({len(df2)/len(combined_df)*100:.1f}%)")
    
    if 'source' in combined_df.columns:
        print(f"- Unique source methods in combined data: {combined_df['source'].nunique()}")
    
    if 'sink' in combined_df.columns:
        print(f"- Unique sink methods in combined data: {combined_df['sink'].nunique()}")

def main():
    # Define file paths
    file1_path = './results/processed_data/source_no_toString.csv'
    file2_path = './results/processed_data/source_toString_notNoise.csv'
    
    print("Combining CSV files and calculating app statistics")
    print(f"File 1: {file1_path}")
    print(f"File 2: {file2_path}")
    print("-" * 60)
    
    combine_csv_and_count_apps(file1_path, file2_path)

if __name__ == "__main__":
    main()