import os
import subprocess
import time
import re
import shutil

jar_path = "./soot-infoflow-cmd-2.13.0-jar-with-dependencies.jar"
sink_And_source_path = "./sinkAndSouce_test1.txt"
platform_path = "./platforms"
output = "./FlowDroid_output3"

# Create result directories if they don't exist
os.makedirs(output + "/successful", exist_ok=True)
os.makedirs(output + "/overtime", exist_ok=True)
os.makedirs(output + "/failure", exist_ok=True)

apk_list = {}
results = {"successful": [], "overtime": [], "failure": []}

# Time threshold for classification (in seconds)
TIME_THRESHOLD = 600

# Set to track processed APKs to avoid duplicates
processed_apks = set()

def get_apk_list(path, tag):
    if tag is not None:
        files = [entry.name for entry in os.scandir(path) if entry.is_file()]
        apk_address = []
        for tmp in files:
            if tmp.endswith(".apk"):
                full_address = path + '/' + tmp
                apk_address.append(full_address)
        if len(apk_address) > 0:
            apk_list[tag] = apk_address
    
    directories = [entry.name for entry in os.scandir(path) if entry.is_dir()]
    for i in directories:
        next_dir = path + '/' + i
        get_apk_list(next_dir, i)

def cleanup_empty_result_folders():
    """Remove empty result folders in the category directories"""
    for category in ["successful", "overtime", "failure"]:
        category_dir = os.path.join(output, category)
        if os.path.exists(category_dir):
            for item in os.listdir(category_dir):
                item_path = os.path.join(category_dir, item)
                if os.path.isdir(item_path) and item.endswith("_results"):
                    # Check if directory is empty
                    if not os.listdir(item_path):
                        print(f"Removing empty results folder: {item_path}")
                        os.rmdir(item_path)

def load_previously_processed_apks():
    """Load already processed APKs from the output directories"""
    for category in ["successful", "overtime", "failure"]:
        category_dir = os.path.join(output, category)
        if os.path.exists(category_dir):
            # Get log files which indicate processed APKs
            for filename in os.listdir(category_dir):
                if filename.endswith(".log"):
                    # Remove the .log extension to get the APK name
                    apk_name = filename[:-4]
                    processed_apks.add(apk_name)
                    results[category].append(apk_name)
    
    print(f"Found {len(processed_apks)} previously processed APKs")

def run_flowdroid(app):
    app_name = os.path.basename(app)
    
    # Skip if this APK has already been processed
    if app_name in processed_apks:
        print(f"\nSkipping {app_name} - already processed")
        return
    
    app_output_dir = output + "/processing/" + app_name
    os.makedirs(app_output_dir, exist_ok=True)
    
    # Update command to use the same timeout value (600s)
    cmd = [
        "java", "-jar", jar_path,
        "-a", app,
        "-p", platform_path,
        "-s", sink_And_source_path,
        "-o", app_output_dir,
        "--timeout", str(TIME_THRESHOLD),
        "--resulttimeout", str(TIME_THRESHOLD),
        "-cg", "SPARK" 
    ]
    
    print(f"\nProcessing {app}")
    start_time = time.time()
    
    try:
        # Set subprocess timeout to just 10 seconds more than FlowDroid timeout
        result = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=TIME_THRESHOLD+10)
        execution_time = time.time() - start_time
        
        # Print the FlowDroid output
        print("\nFlowDroid STDOUT:")
        print("=" * 80)
        print(result.stdout)
        print("\nFlowDroid STDERR:")
        print("=" * 80)
        print(result.stderr)
        print("=" * 80)
        
        # Debug information
        print(f"Debug - Return code: {result.returncode}, Time: {execution_time:.2f}s")
        
        # Category determination logic
        if execution_time >= TIME_THRESHOLD:
            print("Debug - Execution time exceeded threshold")
            category = "overtime"
        elif result.returncode == 0 or "Analysis completed" in result.stdout:
            if result.returncode == 0:
                print("Debug - Success: Return code 0")
            if "Analysis completed" in result.stdout:
                print("Debug - Success: Completion message found")
            category = "successful"
        else:
            print("Debug - Both return code and completion message checks failed")
            category = "failure"
            
        # Log detailed info
        with open(f"{output}/{category}/{app_name}.log", "w") as f:
            f.write(f"Execution time: {execution_time:.2f} seconds\n")
            f.write(f"Return code: {result.returncode}\n")
            f.write("STDOUT:\n" + result.stdout + "\n")
            f.write("STDERR:\n" + result.stderr + "\n")
        
        # Move results to appropriate category folder
        target_dir = f"{output}/{category}/{app_name}_results"
        if os.path.exists(app_output_dir):
            # Check if the processing directory has any content
            contents = os.listdir(app_output_dir)
            if contents:
                os.makedirs(target_dir, exist_ok=True)
                for item in contents:
                    item_path = os.path.join(app_output_dir, item)
                    if os.path.isfile(item_path):
                        os.rename(item_path, os.path.join(target_dir, item))
            # Clean up the processing directory
            os.rmdir(app_output_dir)
            
            # If the target results directory is empty after transfer, remove it
            if os.path.exists(target_dir) and not os.listdir(target_dir):
                print(f"Removing empty results folder: {target_dir}")
                os.rmdir(target_dir)
            
        results[category].append(app_name)
        processed_apks.add(app_name)  # Mark as processed
        print(f"Final Result: {category} ({execution_time:.2f}s)")
        
    except subprocess.TimeoutExpired:
        execution_time = time.time() - start_time
        category = "overtime"
        with open(f"{output}/{category}/{app_name}.log", "w") as f:
            f.write(f"Execution time: {execution_time:.2f} seconds\n")
            f.write("Process exceeded the maximum allowed time\n")
        
        # Clean up any partial results from the processing directory
        if os.path.exists(app_output_dir):
            target_dir = f"{output}/{category}/{app_name}_results"
            contents = os.listdir(app_output_dir)
            if contents:
                os.makedirs(target_dir, exist_ok=True)
                for item in contents:
                    item_path = os.path.join(app_output_dir, item)
                    if os.path.isfile(item_path):
                        os.rename(item_path, os.path.join(target_dir, item))
            os.rmdir(app_output_dir)
            
            # If the target results directory is empty after transfer, remove it
            if os.path.exists(target_dir) and not os.listdir(target_dir):
                print(f"Removing empty results folder: {target_dir}")
                os.rmdir(target_dir)
                
        results[category].append(app_name)
        processed_apks.add(app_name)  # Mark as processed
        print(f"Final Result: {category} (exceeded maximum time)")
        
    except Exception as e:
        category = "failure"
        with open(f"{output}/{category}/{app_name}.log", "w") as f:
            f.write(f"Exception: {str(e)}\n")
        
        # Clean up any partial results from the processing directory
        if os.path.exists(app_output_dir):
            target_dir = f"{output}/{category}/{app_name}_results"
            contents = os.listdir(app_output_dir)
            if contents:
                os.makedirs(target_dir, exist_ok=True)
                for item in contents:
                    item_path = os.path.join(app_output_dir, item)
                    if os.path.isfile(item_path):
                        os.rename(item_path, os.path.join(target_dir, item))
            os.rmdir(app_output_dir)
            
            # If the target results directory is empty after transfer, remove it
            if os.path.exists(target_dir) and not os.listdir(target_dir):
                print(f"Removing empty results folder: {target_dir}")
                os.rmdir(target_dir)
                
        results[category].append(app_name)
        processed_apks.add(app_name)  # Mark as processed
        print(f"Final Result: {category} (exception: {str(e)})")

if __name__ == "__main__":
    # Create processing directory
    os.makedirs(output + "/processing", exist_ok=True)
    
    # Clean up any existing empty result folders
    cleanup_empty_result_folders()
    
    # Load previously processed APKs
    load_previously_processed_apks()
    
    # Get all APKs
    current_directory = "./data/apks"
    get_apk_list(current_directory, "")
    total_apks = sum(len(apks) for apks in apk_list.values())
    print(f"Found {total_apks} APK files")
    print(f"Will process {total_apks - len(processed_apks)} new APKs")
    
    # Process each APK
    for key, value in apk_list.items():
        for app in value:
            run_flowdroid(app)
    
    # Final cleanup of empty result folders
    cleanup_empty_result_folders()
    
    # Generate summary report
    with open(f"{output}/summary_report.txt", "w") as f:
        total_processed = sum(len(results[cat]) for cat in results)
        
        f.write("FlowDroid Analysis Summary\n")
        f.write("=========================\n\n")
        f.write(f"Total APKs processed: {total_processed}\n")
        f.write(f"Time threshold: {TIME_THRESHOLD} seconds\n\n")
        
        for category in ["successful", "overtime", "failure"]:
            category_count = len(results[category])
            percentage = (category_count / total_processed * 100) if total_processed > 0 else 0
            f.write(f"{category.capitalize()}: {category_count} ({percentage:.1f}%)\n")
        
        for category in ["successful", "overtime", "failure"]:
            f.write(f"\n{category.capitalize()} APKs:\n")
            f.write("--------------------------------\n")
            for app in results[category]:
                f.write(f"- {app}\n")
    
    print("\nAnalysis complete. Results summary:")
    print(f"  Successful: {len(results['successful'])}")
    print(f"  Overtime: {len(results['overtime'])}")
    print(f"  Failure: {len(results['failure'])}")
    print(f"See detailed report at {output}/summary_report.txt")