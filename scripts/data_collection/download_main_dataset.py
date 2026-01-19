#!/usr/bin/env python3
"""
RQ1 Dataset Downloader for Android Logging Privacy Study

This script downloads the main dataset (2016-2021 Google Play APKs) from AndroZoo
for the empirical study of privacy leakage vulnerability in third-party Android logs libraries.

Based on the RQ4 temporal analysis script but adapted for the main dataset collection.
"""

import polars as pl
import requests
import os
import time
import argparse
from pathlib import Path
from datetime import datetime
import logging

# Configuration
DOWNLOAD_URL = 'https://androzoo.uni.lu/api/download'
API_KEY = 'your_androzoo_api_key_here'
latest_csv_path = "./data/metadata/latest.csv"
download_folder = "./data/apks/main_dataset"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('download_log.txt'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def create_download_folder():
    """Create the download folder if it doesn't exist"""
    Path(download_folder).mkdir(parents=True, exist_ok=True)
    logger.info(f"📁 Download folder ready: {download_folder}")

def load_latest_csv():
    """Load the latest.csv file from AndroZoo"""
    try:
        df = pl.read_csv(
            latest_csv_path,
            separator=",",
            has_header=True,
            null_values=["", "NULL", "null"],
            try_parse_dates=True
        )
        logger.info(f"✅ Successfully loaded latest.csv with {df.shape[0]} rows")
        return df
        
    except FileNotFoundError:
        logger.error(f"❌ Error: File not found at {latest_csv_path}")
        logger.error("Please download latest.csv from AndroZoo and place it in ./data/metadata/")
        return None
    except Exception as e:
        logger.error(f"❌ Error loading latest.csv: {e}")
        return None

def filter_main_dataset(df, max_apps=None, sample_rate=1.0):
    """
    Filter the dataset for main study requirements:
    - Google Play Store apps only
    - Years 2016-2021
    - Optional sampling for testing
    """
    try:
        logger.info("🔍 Filtering dataset for main study requirements...")
        
        # Filter for Google Play Store apps from 2016-2021
        filtered_df = df.filter(
            (pl.col("markets") == "play.google.com") &
            (pl.col("vt_scan_date").dt.year() >= 2016) &
            (pl.col("vt_scan_date").dt.year() <= 2021)
        )
        
        logger.info(f"📊 Found {filtered_df.shape[0]} Google Play apps from 2016-2021")
        
        # Sample if requested
        if sample_rate < 1.0:
            sample_size = int(filtered_df.shape[0] * sample_rate)
            filtered_df = filtered_df.sample(n=sample_size, seed=42)
            logger.info(f"🎯 Sampled {sample_size} apps for testing (rate: {sample_rate})")
        
        # Limit total apps if specified
        if max_apps and filtered_df.shape[0] > max_apps:
            filtered_df = filtered_df.head(max_apps)
            logger.info(f"🎯 Limited to {max_apps} apps")
        
        # Sort by scan date (newest first)
        filtered_df = filtered_df.sort("vt_scan_date", descending=True)
        
        logger.info(f"✅ Final dataset: {filtered_df.shape[0]} apps ready for download")
        return filtered_df
        
    except Exception as e:
        logger.error(f"❌ Error filtering dataset: {e}")
        return None

def download_apk(sha256_hash, pkg_name, scan_date, retry_count=3):
    """Download APK file from AndroZoo with retry logic"""
    for attempt in range(retry_count):
        try:
            # Create filename with scan date for uniqueness
            scan_date_str = scan_date.strftime("%Y%m%d") if hasattr(scan_date, 'strftime') else str(scan_date)[:10].replace('-', '')
            filename = f"{pkg_name}_{scan_date_str}_{sha256_hash[:8]}.apk"
            download_path = os.path.join(download_folder, filename)
            
            # Check if file already exists
            if os.path.exists(download_path):
                file_size = os.path.getsize(download_path)
                logger.info(f"⏭️  SKIPPED: {pkg_name} already exists ({file_size:,} bytes)")
                return True
            
            # Prepare download request
            url = f"{DOWNLOAD_URL}?apikey={API_KEY}&sha256={sha256_hash}"
            
            logger.info(f"📥 Downloading: {pkg_name} (attempt {attempt + 1})")
            response = requests.get(url, stream=True, timeout=300)
            response.raise_for_status()
            
            # Download and save the file
            with open(download_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            file_size = os.path.getsize(download_path)
            logger.info(f"✅ SUCCESS: {pkg_name}")
            logger.info(f"   📁 Saved: {filename}")
            logger.info(f"   📊 Size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"⚠️  DOWNLOAD ERROR for {pkg_name} (attempt {attempt + 1}): {e}")
            if hasattr(e, 'response') and e.response is not None:
                if e.response.status_code == 404:
                    logger.warning(f"   APK not found in AndroZoo database")
                    break  # Don't retry for 404
                elif e.response.status_code == 401:
                    logger.error(f"   API key authentication failed")
                    break  # Don't retry for 401
                else:
                    logger.warning(f"   HTTP Status Code: {e.response.status_code}")
            
            if attempt < retry_count - 1:
                wait_time = (attempt + 1) * 5  # Exponential backoff
                logger.info(f"   ⏳ Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            
        except Exception as e:
            logger.error(f"❌ FILE SAVE ERROR for {pkg_name}: {e}")
            # Clean up partial download
            try:
                if os.path.exists(download_path):
                    os.remove(download_path)
            except:
                pass
            break
    
    return False

def save_progress(stats, processed_apps):
    """Save download progress to resume later"""
    progress_file = "./data/metadata/download_progress.json"
    progress_data = {
        "stats": stats,
        "processed_apps": processed_apps,
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        import json
        with open(progress_file, 'w') as f:
            json.dump(progress_data, f, indent=2)
        logger.info(f"💾 Progress saved to {progress_file}")
    except Exception as e:
        logger.warning(f"⚠️  Could not save progress: {e}")

def load_progress():
    """Load previous download progress"""
    progress_file = "./data/metadata/download_progress.json"
    try:
        import json
        with open(progress_file, 'r') as f:
            progress_data = json.load(f)
        logger.info(f"📂 Loaded previous progress from {progress_file}")
        return progress_data.get("processed_apps", set()), progress_data.get("stats", {})
    except FileNotFoundError:
        logger.info("📂 No previous progress found, starting fresh")
        return set(), {}
    except Exception as e:
        logger.warning(f"⚠️  Could not load progress: {e}")
        return set(), {}

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Download main dataset for Android Logging Privacy Study')
    parser.add_argument('--max-apps', type=int, help='Maximum number of apps to download (for testing)')
    parser.add_argument('--sample-rate', type=float, default=1.0, help='Sample rate (0.1 = 10% of dataset)')
    parser.add_argument('--resume', action='store_true', help='Resume previous download')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be downloaded without actually downloading')
    
    args = parser.parse_args()
    
    logger.info("🚀 Starting main dataset download for Android Logging Privacy Study")
    logger.info("=" * 80)
    
    # Create download folder
    create_download_folder()
    
    # Load latest.csv
    df = load_latest_csv()
    if df is None:
        return
    
    # Check required columns
    required_cols = ['pkg_name', 'markets', 'vt_scan_date', 'sha256']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.error(f"❌ Required columns not found: {missing_cols}")
        return
    
    # Filter dataset
    filtered_df = filter_main_dataset(df, args.max_apps, args.sample_rate)
    if filtered_df is None:
        return
    
    # Load previous progress if resuming
    processed_apps, previous_stats = load_progress() if args.resume else (set(), {})
    
    # Statistics tracking
    stats = {
        'total_apps': filtered_df.shape[0],
        'successfully_downloaded': previous_stats.get('successfully_downloaded', 0),
        'download_failed': previous_stats.get('download_failed', 0),
        'skipped_existing': previous_stats.get('skipped_existing', 0),
        'processed': len(processed_apps)
    }
    
    logger.info(f"\n📊 Processing {stats['total_apps']} apps...")
    if args.resume:
        logger.info(f"📂 Resuming from {stats['processed']} previously processed apps")
    logger.info("-" * 80)
    
    # Process each app
    for i, row in enumerate(filtered_df.iter_rows(named=True), 1):
        pkg_name = row['pkg_name']
        sha256_hash = row['sha256']
        scan_date = row['vt_scan_date']
        
        # Skip if already processed
        if pkg_name in processed_apps:
            continue
        
        logger.info(f"\n[{i}/{stats['total_apps']}] Processing: {pkg_name}")
        
        if args.dry_run:
            logger.info(f"🔍 DRY RUN: Would download {pkg_name}")
            stats['successfully_downloaded'] += 1
        else:
            # Download APK
            if download_apk(sha256_hash, pkg_name, scan_date):
                stats['successfully_downloaded'] += 1
            else:
                stats['download_failed'] += 1
        
        # Mark as processed
        processed_apps.add(pkg_name)
        stats['processed'] = len(processed_apps)
        
        # Save progress every 10 downloads
        if i % 10 == 0:
            save_progress(stats, processed_apps)
        
        # Rate limiting
        if not args.dry_run:
            time.sleep(1)  # 1 second delay between downloads
    
    # Final statistics
    logger.info("\n" + "=" * 80)
    logger.info("📊 DOWNLOAD SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total apps processed: {stats['processed']}")
    logger.info(f"Successfully downloaded: {stats['successfully_downloaded']}")
    logger.info(f"Download failed: {stats['download_failed']}")
    logger.info(f"Success rate: {stats['successfully_downloaded']/stats['processed']*100:.1f}%")
    
    # Clean up progress file if completed
    if stats['processed'] == stats['total_apps']:
        try:
            os.remove("./data/metadata/download_progress.json")
            logger.info("🧹 Cleaned up progress file (download completed)")
        except:
            pass

if __name__ == "__main__":
    main()
