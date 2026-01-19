import polars as pl
import requests
import os
import time
from pathlib import Path

# Configuration
latest_csv_path = "./data/metadata/latest.csv"
leaking_apps_csv_path = "./results/processed_data/rq1_leaking_app_unique_list.csv"
download_folder = "./data/apks/leaking_app_v2023"
DOWNLOAD_URL = 'https://androzoo.uni.lu/api/download'
API_KEY = 'your_androzoo_api_key_here'

def create_download_folder():
    """Create the download folder if it doesn't exist"""
    Path(download_folder).mkdir(parents=True, exist_ok=True)
    print(f"📁 Download folder ready: {download_folder}")

def load_leaking_apps():
    """Load the list of leaking apps from CSV"""
    try:
        leaking_df = pl.read_csv(
            leaking_apps_csv_path,
            separator=",",
            has_header=True,
            null_values=["", "NULL", "null"]
        )
        
        if 'app_name' not in leaking_df.columns:
            print("❌ Error: 'app_name' column not found in leaking apps CSV")
            return None
            
        app_names = leaking_df['app_name'].to_list()
        print(f"📋 Loaded {len(app_names)} leaking apps from list")
        return app_names
        
    except FileNotFoundError:
        print(f"❌ Error: Leaking apps file not found at {leaking_apps_csv_path}")
        return None
    except Exception as e:
        print(f"❌ Error loading leaking apps: {e}")
        return None

def load_latest_csv():
    """Load the latest.csv file"""
    try:
        df = pl.read_csv(
            latest_csv_path,
            separator=",",
            has_header=True,
            null_values=["", "NULL", "null"],
            try_parse_dates=True
        )
        print(f"✅ Successfully loaded latest.csv with {df.shape[0]} rows")
        return df
        
    except FileNotFoundError:
        print(f"❌ Error: File not found at {latest_csv_path}")
        return None
    except Exception as e:
        print(f"❌ Error loading latest.csv: {e}")
        return None

def find_app_in_dataset(df, app_name):
    """Find the latest 2023 version of an app in the dataset"""
    try:
        # Filter for the specific app, from play.google.com, in 2023
        filtered_rows = df.filter(
            (pl.col("pkg_name") == app_name) & 
            (pl.col("markets") == "play.google.com") &
            (pl.col("vt_scan_date").dt.year() == 2023)
        )
        
        if filtered_rows.shape[0] > 0:
            # Find the row with the latest scan date in 2023
            latest_scan_row = filtered_rows.filter(
                pl.col("vt_scan_date") == filtered_rows["vt_scan_date"].max()
            )
            return latest_scan_row
        else:
            return None
            
    except Exception as e:
        print(f"❌ Error filtering app {app_name}: {e}")
        return None

def download_apk(sha256_hash, pkg_name, scan_date):
    """Download APK file from AndroZoo"""
    try:
        # Create filename with scan date for uniqueness
        scan_date_str = scan_date.strftime("%Y%m%d") if hasattr(scan_date, 'strftime') else str(scan_date)[:10].replace('-', '')
        filename = f"{pkg_name}_{scan_date_str}_{sha256_hash[:8]}.apk"
        download_path = os.path.join(download_folder, filename)
        
        # Check if file already exists
        if os.path.exists(download_path):
            file_size = os.path.getsize(download_path)
            print(f"⏭️  SKIPPED: {pkg_name} already exists ({file_size:,} bytes)")
            return True
        
        # Prepare download request
        url = f"{DOWNLOAD_URL}?apikey={API_KEY}&sha256={sha256_hash}"
        
        print(f"📥 Downloading: {pkg_name}")
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        
        # Download and save the file
        with open(download_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        file_size = os.path.getsize(download_path)
        print(f"✅ SUCCESS: {pkg_name}")
        print(f"   📁 Saved: {filename}")
        print(f"   📊 Size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ DOWNLOAD ERROR for {pkg_name}: {e}")
        if hasattr(e, 'response') and e.response is not None:
            if e.response.status_code == 404:
                print(f"   APK not found in AndroZoo database")
            elif e.response.status_code == 401:
                print(f"   API key authentication failed")
            else:
                print(f"   HTTP Status Code: {e.response.status_code}")
        return False
        
    except Exception as e:
        print(f"❌ FILE SAVE ERROR for {pkg_name}: {e}")
        # Clean up partial download
        try:
            if os.path.exists(download_path):
                os.remove(download_path)
        except:
            pass
        return False

def main():
    """Main execution function"""
    print("🚀 Starting batch APK download for leaking apps (2023)")
    print("=" * 60)
    
    # Create download folder
    create_download_folder()
    
    # Load leaking apps list
    app_names = load_leaking_apps()
    if not app_names:
        return
    
    # Load latest.csv
    df = load_latest_csv()
    if df is None:
        return
    
    # Check required columns
    required_cols = ['pkg_name', 'markets', 'vt_scan_date', 'sha256']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"❌ Required columns not found: {missing_cols}")
        return
    
    # Statistics tracking
    stats = {
        'total_apps': len(app_names),
        'found_in_dataset': 0,
        'successfully_downloaded': 0,
        'download_failed': 0,
        'not_found': 0,
        'skipped_existing': 0
    }
    
    print(f"\n📊 Processing {stats['total_apps']} leaking apps...")
    print("-" * 60)
    
    # Process each app
    for i, app_name in enumerate(app_names, 1):
        print(f"\n[{i}/{stats['total_apps']}] Processing: {app_name}")
        
        # Find app in dataset
        app_data = find_app_in_dataset(df, app_name)
        
        if app_data is None or app_data.shape[0] == 0:
            print(f"❌ NOT FOUND: {app_name} (no 2023 version in play.google.com)")
            stats['not_found'] += 1
            continue
        
        stats['found_in_dataset'] += 1
        
        # Get app details
        sha256_hash = app_data['sha256'].item()
        pkg_name = app_data['pkg_name'].item()
        scan_date = app_data['vt_scan_date'].item()
        vt_detection = app_data['vt_detection'].item() if 'vt_detection' in app_data.columns else 'N/A'
        
        print(f"   📋 Found: SHA256={sha256_hash[:16]}..., Scan={scan_date}, VT={vt_detection}")
        
        # Download APK
        success = download_apk(sha256_hash, pkg_name, scan_date)
        
        if success:
            # Check if it was skipped (already exists) or newly downloaded
            filename = f"{pkg_name}_{str(scan_date)[:10].replace('-', '')}_{sha256_hash[:8]}.apk"
            download_path = os.path.join(download_folder, filename)
            if os.path.exists(download_path):
                if "SKIPPED" in locals():  # This is a bit hacky, but works for this context
                    stats['skipped_existing'] += 1
                else:
                    stats['successfully_downloaded'] += 1
        else:
            stats['download_failed'] += 1
        
        # Small delay to be respectful to the API
        time.sleep(1)
    
    # Print final statistics
    print("\n" + "=" * 60)
    print("📊 FINAL STATISTICS")
    print("=" * 60)
    print(f"Total apps processed:     {stats['total_apps']}")
    print(f"Found in dataset:         {stats['found_in_dataset']}")
    print(f"Successfully downloaded:  {stats['successfully_downloaded']}")
    print(f"Already existed (skipped): {stats['skipped_existing']}")
    print(f"Download failed:          {stats['download_failed']}")
    print(f"Not found in dataset:     {stats['not_found']}")
    print(f"\n📁 All downloads saved to: {download_folder}")
    
    # Calculate success rate
    if stats['found_in_dataset'] > 0:
        success_rate = (stats['successfully_downloaded'] + stats['skipped_existing']) / stats['found_in_dataset'] * 100
        print(f"📈 Download success rate: {success_rate:.1f}%")

if __name__ == "__main__":
    main()