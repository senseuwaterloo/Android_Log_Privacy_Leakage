import os
import polars as pl  # Import Polars

summary_path = './data/metadata/output_summary.csv'
# Check if the file exists
if not os.path.exists(summary_path):
    print(f"CSV file not found at {summary_path}. Creating a new one.")
    
    # Ensure the parent directory exists
    os.makedirs(os.path.dirname(summary_path), exist_ok=True)
    
    # Initialize an empty DataFrame with the required structure
    empty_df = pl.DataFrame({
        "Class Name": [],
        "Method Name": [],
        "Descriptor": [],
        "Access Flags": [],
        "Freq": []
    })
    
    # Save the DataFrame to the specified CSV path
    empty_df.write_csv(summary_path)
    print(f"Empty CSV file created at {summary_path}")
else:
    print(f"Reading CSV  at {summary_path}")
    df_summary = pl.read_csv(summary_path,truncate_ragged_lines=True)
    # Initialize an empty DataFrame to accumulate results
    summary_df = pl.DataFrame({
        "Class Name": [],
        "Method Name": [],
        "Descriptor": [],
        "Access Flags": [],
        "Freq": []
    })


def parsing_csv_file(file_path):
    # Read the CSV file into a Polars DataFrame
    try:
        df = pl.read_csv(file_path)
        # Group by `Class Name` and `Method Name` to calculate frequencies
        freq_df = (
            df.group_by(["Class Name", "Method Name", "Descriptor", "Access Flags"])
              .count()
              .rename({"count": "Freq"})  # Rename the count column to Freq
        )
        return freq_df
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None



if __name__ == "__main__":
    path = "./data/metadata/gml_to_csv"
    # Scan the directory for CSV files
    csv_files = [file for file in os.listdir(path) if file.endswith(".csv")]
    # Print the list of CSV files found
    print(f"Found {len(csv_files)} CSV files:")

    for file in csv_files:
        file_path = os.path.join(path, file)  # Get the full path to the CSV file
        print(f"\nProcessing file: {file_path}")
        freq_df = parsing_csv_file(file_path)
        if freq_df is not None:
            # Merge into summary, handling cases where df_summary is empty
            if df_summary.height == 0:
                df_summary = freq_df
                print(f"Initialized df_summary with freq_df for file: {file_path}")
            else:
                df_summary = df_summary.join(
                    freq_df,
                    on=["Class Name", "Method Name", "Descriptor", "Access Flags"],
                    how="outer"  # Merge all data
                ).with_columns(
                    # Update `Freq` column, summing values where both exist
                    (pl.col("Freq").fill_null(0) + pl.col("Freq_right").fill_null(0)).alias("Freq")
                ).drop(
                    ["Freq_right", 
                     "Class Name_right", "Method Name_right", 
                     "Descriptor_right", "Access Flags_right"]
                )

        # Save the updated summary
        df_summary.write_csv(summary_path)
        print(f"Updated summary saved to {summary_path}")

    # # Process each CSV file
    # for file in csv_files:
    #     file_path = os.path.join(path, file)  # Get the full path to the CSV file
    #     print(f"\nProcessing file: {file_path}")
    #     freq_df = parsing_csv_file(file_path)
    #     if freq_df is not None:
    #          if "Class Name" in df_summary.columns and "Method Name" in df_summary.columns and "Descriptor" in df_summary.columns and "Access Flags" in df_summary.columns:
    #             # Merge freq_df into df_summary, accumulating `Freq` where keys match
    #             # If df_summary is empty, directly assign freq_df
    #             if df_summary.height == 0:  # Check if df_summary is empty
    #                 df_summary = freq_df
    #                 print(f"Initialized df_summary with freq_df for file: {file}")
    #             else:
    #                 try:
    #                     df_summary = df_summary.drop(
    #                         [
    #                             "Class Name_right", 
    #                             "Method Name_right", 
    #                             "Descriptor_right", 
    #                             "Access Flags_right", 
    #                             "Freq_left", 
    #                             "Freq_right"
    #                         ]
    #                     )
    #                 except:
    #                     print("enter")
    #                 df_summary =  df_summary.join(
    #                         freq_df,
    #                         on=["Class Name", "Method Name", "Descriptor", "Access Flags"],
    #                         how="full"
    #                     )

    #                 print(f"After join, df_summary has columns: {df_summary.columns}")
                    
    #                 # Check for missing or mismatched columns before processing
    #                 if "Freq_left" in df_summary.columns and "Freq_right" in df_summary.columns:
    #                     df_summary = df_summary.with_columns(
    #                         (pl.col("Freq_left").fill_null(0) + pl.col("Freq_right").fill_null(0))
    #                         .alias("Freq")
    #                     ).drop(["Freq_left", "Freq_right"])  # Drop intermediate columns
    #                             # Drop all unwanted columns
    #                     df_summary = df_summary.drop(
    #                         [
    #                             "Class Name_right", 
    #                             "Method Name_right", 
    #                             "Descriptor_right", 
    #                             "Access Flags_right", 
    #                             "Freq_left", 
    #                             "Freq_right"
    #                         ]
    #                     )
    #                 else:
    #                     # If Freq columns do not exist, create or update the "Freq" column
    #                     df_summary = df_summary.with_columns(
    #                         pl.col("Freq").fill_null(0).alias("Freq")
    #                     )
    #     # Save the updated summary to disk
    #     df_summary.write_csv(summary_path)
    #     print(df_summary)
    #     print(f"Updated summary saved to {summary_path}")
