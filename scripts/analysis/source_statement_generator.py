import csv
import re
import os

def extract_statement_from_source(source_text):
    """
    Extract only the statement part from the source column.
    Looking for pattern: Statement: <actual_statement>
    """
    # Pattern to match "Statement: " followed by the actual statement
    pattern = r'Statement:\s*(.+?)(?:\s*$)'
    
    match = re.search(pattern, source_text)
    if match:
        return match.group(1).strip()
    return ""

def process_flowdroid_csv(input_csv_path):
    """
    Process the FlowDroid CSV and extract statements to a new CSV.
    """
    # Create output directory
    output_dir = "./results/processed_data/source_cluster"
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, "source_statement.csv")
    
    extracted_statements = []
    
    try:
        # Read the input CSV
        with open(input_csv_path, 'r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            
            for row in reader:
                app_name = row.get('app_name', '')
                source = row.get('source', '')
                sink = row.get('sink', '')
                
                # Extract the statement
                statement = extract_statement_from_source(source)
                
                if statement:  # Only add rows with valid statements
                    extracted_statements.append({
                        'app_name': app_name,
                        'source_statement': statement,
                        'sink': sink
                    })
        
        # Write to new CSV
        with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
            fieldnames = ['app_name', 'source_statement', 'sink']
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for row in extracted_statements:
                writer.writerow(row)
        
        print(f"Successfully extracted {len(extracted_statements)} statements")
        print(f"Output saved to: {output_file}")
        
        # Show some examples
        print("\nFirst 5 extracted statements:")
        for i, stmt in enumerate(extracted_statements[:5]):
            print(f"{i+1}. {stmt['source_statement']}")
            
    except FileNotFoundError:
        print(f"Error: Input file {input_csv_path} not found.")
    except Exception as e:
        print(f"Error processing file: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python script.py <input_csv_file>")
        print("Example: python script.py ./results/processed_data/flowdriod_outcome_2/flowdroid_data_flows.csv")
        sys.exit(1)
    
    input_file = sys.argv[1]
    process_flowdroid_csv(input_file)