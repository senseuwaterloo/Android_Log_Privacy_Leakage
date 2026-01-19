import pandas as pd
import os

def split_csv_by_toString(input_file_path):
    """
    Split a CSV file into two files based on whether the 'source' column contains 'toString'
    
    Args:
        input_file_path (str): Path to the input CSV file
    """
    
    # Read the CSV file
    try:
        df = pd.read_csv(input_file_path)
        print(f"Successfully loaded CSV with {len(df)} rows and {len(df.columns)} columns")
        print(f"Columns: {list(df.columns)}")
        
    except FileNotFoundError:
        print(f"Error: File '{input_file_path}' not found.")
        return
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return
    
    # Check if 'source' column exists
    if 'source' not in df.columns:
        print("Error: 'source' column not found in the CSV file.")
        print(f"Available columns: {list(df.columns)}")
        return
    
    # Split the dataframe based on whether 'source' contains 'toString'
    # Rows where source contains 'toString'
    df_with_toString = df[df['source'].str.contains('toString', case=False, na=False)]
    
    # Rows where source does NOT contain 'toString'
    df_without_toString = df[~df['source'].str.contains('toString', case=False, na=False)]
    
    # Get the directory of the input file to save outputs in the same location
    input_dir = os.path.dirname(input_file_path)
    
    # Define output file paths
    output_toString = os.path.join(input_dir, 'source_toString.csv')
    output_no_toString = os.path.join(input_dir, 'source_no_toString.csv')
    
    # Save the split dataframes
    try:
        df_with_toString.to_csv(output_toString, index=False)
        df_without_toString.to_csv(output_no_toString, index=False)
        
        print(f"\nSuccessfully created:")
        print(f"- {output_toString} ({len(df_with_toString)} rows)")
        print(f"- {output_no_toString} ({len(df_without_toString)} rows)")
        
        # Print some statistics
        print(f"\nStatistics:")
        print(f"- Total rows: {len(df)}")
        print(f"- Rows with 'toString': {len(df_with_toString)} ({len(df_with_toString)/len(df)*100:.1f}%)")
        print(f"- Rows without 'toString': {len(df_without_toString)} ({len(df_without_toString)/len(df)*100:.1f}%)")
        
    except Exception as e:
        print(f"Error saving CSV files: {e}")

def main():
    # Set the input file path
    input_file = './results/processed_data/flowdroid_data_flows.csv'
    
    # Alternative: You can also use a relative path or ask for user input
    # input_file = input("Enter the path to your CSV file: ")
    
    print(f"Processing file: {input_file}")
    split_csv_by_toString(input_file)

if __name__ == "__main__":
    main()