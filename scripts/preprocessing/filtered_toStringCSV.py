import pandas as pd
import os

def extract_specific_source_methods(input_file_path):
    """
    Extract rows from CSV where the 'source' column contains specific class names
    
    Args:
        input_file_path (str): Path to the input CSV file (toString_related.csv)
    """
    
    # Define the 4 class names to look for in source methods
    target_classes = [
        'android.widget.TextView',
        'android.text.Editable',
        'android.webkit.JavascriptInterface',
        'org.apache.http.util.EntityUtils'
    ]
    
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
    
    # Create a condition to match any of the target classes
    # Initialize with False condition for the first iteration
    condition = pd.Series([False] * len(df))
    
    # Check each target class and combine conditions with OR
    for target_class in target_classes:
        # Simple string contains check (no regex needed for class names)
        class_condition = df['source'].str.contains(target_class, case=False, na=False, regex=False)
        condition = condition | class_condition
        print(f"Found {class_condition.sum()} rows containing '{target_class}'")
    
    # Filter the dataframe
    filtered_df = df[condition]
    
    # Get statistics for each class
    print(f"\nBreakdown by class:")
    class_counts = {}
    for target_class in target_classes:
        count = df['source'].str.contains(target_class, case=False, na=False, regex=False).sum()
        class_counts[target_class] = count
        print(f"- {target_class}: {count} rows")
    
    # Get the directory of the input file to save output in the same location
    input_dir = os.path.dirname(input_file_path)
    
    # Define output file path
    output_file = os.path.join(input_dir, 'abstract_source_methods.csv')
    
    # Save the filtered dataframe
    try:
        filtered_df.to_csv(output_file, index=False)
        
        print(f"\nSuccessfully created:")
        print(f"- {output_file} ({len(filtered_df)} rows)")
        
        # Print overall statistics
        print(f"\nStatistics:")
        print(f"- Total rows in original file: {len(df)}")
        print(f"- Rows matching target classes: {len(filtered_df)} ({len(filtered_df)/len(df)*100:.1f}%)")
        
        if len(filtered_df) > 0:
            print(f"\nSample of extracted data:")
            print("First 3 rows of filtered data:")
            for idx, row in filtered_df.head(3).iterrows():
                print(f"  Row {idx}: {row['app_name']} -> {row['source'][:100]}...")
        else:
            print(f"\nNo rows found matching the target classes.")
            print("This might mean:")
            print("1. The classes are not present in your data")
            print("2. The format might be slightly different")
            print("3. The search pattern needs adjustment")
            
            print(f"\nFirst few unique source values for reference:")
            unique_sources = df['source'].unique()[:5]
            for i, source in enumerate(unique_sources, 1):
                print(f"  {i}. {source}")
        
    except Exception as e:
        print(f"Error saving CSV file: {e}")

def main():
    # Set the input file path for toString_related.csv
    # Assuming it's in the same directory as the original file
    input_file = './results/processed_data/source_toString.csv'
    
    # Alternative paths (uncomment the one you need):
    # input_file = './results/processed_data/toString_related.csv'
    # input_file = input("Enter the path to your toString_related.csv file: ")
    
    print(f"Processing file: {input_file}")
    print("Looking for these classes in source methods:")
    target_classes = [
        'android.widget.TextView',
        'android.text.Editable',
        'android.webkit.JavascriptInterface',
        'org.apache.http.util.EntityUtils'
    ]
    for i, class_name in enumerate(target_classes, 1):
        print(f"  {i}. {class_name}")
    
    extract_specific_source_methods(input_file)

if __name__ == "__main__":
    main()