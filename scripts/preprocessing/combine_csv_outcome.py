import os
import polars as pl  # Import Polars

def path_collect():
    path = "./csv_collection"
    csv_chunks = []
    # Scan the directory for CSV files
    for chunk_folder in os.listdir(path):
        tmp_path = os.path.join(path, chunk_folder)
        for chunk_file in os.listdir(tmp_path):
            if chunk_file.endswith("summary.csv"):
                print(f"Found summary file: {chunk_file}") 
                csv_chunks.append(os.path.join(tmp_path, chunk_file))


    return csv_chunks

def creating_csv(output_path):
    # Create a new DataFrame
    df = pl.DataFrame(
        {
            "Class Name": [],
            "Method Name": [],
            "Descriptor": [],
            "Access Flags": [],
            "Freq": []
        }
    )
    # Save the DataFrame to a CSV file
    df.write_csv(output_path)
    print("file saved")

def mergerging_csv(summary_csv, raw_csv):
    df_1 = pl.read_csv(summary_csv)
    df_1 = df_1.with_columns(pl.col("Freq").cast(pl.Int64))
    df_2 = pl.read_csv(raw_csv)
    df_2 = df_2.with_columns(pl.col("Freq").cast(pl.Int64))
    # Merge the two DataFrames
    df = df_1.join(df_2, on=["Class Name", "Method Name", "Descriptor", "Access Flags"], how="outer").with_columns(
                    # Update the `Freq` column by summing where both exist
                    (pl.col("Freq").fill_null(0) + pl.col("Freq_right").fill_null(0)).alias("Freq"),
                    # Retain `Class Name` unless it is empty, then use `Class Name_right`
                    pl.when(pl.col("Class Name").is_null() | (pl.col("Class Name") == ""))
                    .then(pl.col("Class Name_right"))
                    .otherwise(pl.col("Class Name"))
                    .alias("Class Name"),
                    # Same for `Method Name`, `Descriptor`, and `Access Flags`
                    pl.when(pl.col("Method Name").is_null() | (pl.col("Method Name") == ""))
                    .then(pl.col("Method Name_right"))
                    .otherwise(pl.col("Method Name"))
                    .alias("Method Name"),
                    pl.when(pl.col("Descriptor").is_null() | (pl.col("Descriptor") == ""))
                    .then(pl.col("Descriptor_right"))
                    .otherwise(pl.col("Descriptor"))
                    .alias("Descriptor"),
                    pl.when(pl.col("Access Flags").is_null() | (pl.col("Access Flags") == ""))
                    .then(pl.col("Access Flags_right"))
                    .otherwise(pl.col("Access Flags"))
                    .alias("Access Flags")
                ).drop(
                    ["Freq_right", "Class Name_right", "Method Name_right", 
                     "Descriptor_right", "Access Flags_right"]
                )  # Merge all data
    # Save the DataFrame to a CSV file
    df.write_csv(output_path)

if __name__ == "__main__":
    output_path = "./outcome/summary.csv"
    if os.path.exists(output_path):
        print("Output path exists")
    else:
        print("Output path does not exist")
        creating_csv(output_path)

    csv_list = path_collect()
    for i in csv_list:
        print(i)
        mergerging_csv(output_path, i)
