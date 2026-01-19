# Replication Package: An Empirical Study of Privacy Leakage Vulnerability in Third-Party Android Logs Libraries

This repository contains the replication package for "An Empirical Study of Privacy Leakage Vulnerability in Third-Party Android Logs Libraries" manuscript.

## Overview

This study presents the first large-scale empirical analysis of privacy risks in Android logging practices, examining 48,702 Google Play applications from 2016-2021 to identify sensitive data leakage through third-party logging frameworks.

### Key Findings

- Only 3.4% of applications use third-party logging libraries
- Nearly half (49.3%) of logging-enabled apps exhibit privacy leaks
- Three libraries dominate: Timber (35.2%), SLF4J (35.1%), and Firebase (29.4%)
- 99.7% of violations occur in these three frameworks
- 62.5% of leaks occur through indirect data flows
- 68.2% of apps show improved privacy practices over time

## Repository Structure

```
├── README.md                           # This file
├── requirements.txt                    # Python dependencies
├── data/                              # Data directory (APKs not included)
│   ├── apks/                         # Downloaded APKs
│   └── metadata/                     # AndroZoo metadata
├── scripts/                           # Analysis scripts
│   ├── data_collection/               # APK download scripts
│   ├── flowdroid_analysis/            # FlowDroid execution
│   ├── preprocessing/                 # Data cleaning and filtering
│   ├── analysis/                     # Research question analysis
├── results/                          # Generated results
│   ├── raw_outputs/                  # Raw FlowDroid outputs
│   ├── processed_data/               # Cleaned datasets
│   ├── analysis/                     # Final analysis results
├── tools/                            # External tools
│   ├── soot-infoflow-cmd-2.13.0-jar-with-dependencies.jar
│   └── android/platforms/            # Android SDK platforms
└── config/                           # Configuration files
    └── sinkAndSouce_test1.txt        # FlowDroid sink/source config
```

## Prerequisites

### System Requirements

- **Operating System**: Linux/macOS (Windows with WSL recommended)
- **Memory**: Minimum 8GB RAM (16GB+ recommended for large-scale analysis)
- **Storage**: At least 100GB free space for APK storage and analysis
- **Java**: JDK 8 or higher
- **Python**: 3.8 or higher

### External Dependencies

- **FlowDroid**: Static taint analysis tool for Android
- **AndroZoo API Access**: Required for downloading APKs from [https://androzoo.uni.lu/](https://androzoo.uni.lu/)

## Quick Start

### Prerequisites
- **Java**: JDK 8 or higher
- **Python**: 3.8 or higher
- **FlowDroid**: Download from [official repository](https://github.com/secure-software-engineering/FlowDroid)
- **AndroZoo API**: Register at [https://androzoo.uni.lu/](https://androzoo.uni.lu/) for API access

### Installation
```bash
# Install Python dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir -p tools data/{apks,metadata} results/{raw_outputs,processed_data,analysis} config

# Download FlowDroid JAR file
wget https://github.com/secure-software-engineering/FlowDroid/releases/download/v2.13.0/soot-infoflow-cmd-2.13.0-jar-with-dependencies.jar -O tools/soot-infoflow-cmd-2.13.0-jar-with-dependencies.jar
```

**Important**: Before running any scripts, update the hardcoded paths in the Python files to match your directory structure.

### Manual Execution Steps

**Step 1: Download APKs from AndroZoo**

```bash
# Download main dataset (2016-2021 Google Play APKs)
python scripts/data_collection/download_main_dataset.py

# For temporal analysis (RQ4): Download 2023 versions of leaking apps
python scripts/data_collection/leaking_app_downloader.py
```

**Note**: This step requires AndroZoo API access. You need to register at https://androzoo.uni.lu/ to obtain an API key and download the latest.csv metadata file before running the scripts.

**Step 2: Run FlowDroid Analysis**
```bash
# Execute FlowDroid on downloaded APKs
python scripts/flowdroid_analysis/flowdroid_script.py
# Edit jar_path, sink_And_source_path, platform_path, and output paths
```

**Step 3: Clean and Process Results**
```bash
# Clean raw FlowDroid outputs
python scripts/preprocessing/clean_source_toString.py
python scripts/preprocessing/combine_csv_outcome.py
python scripts/preprocessing/filtered_toStringCSV.py
```

**Step 4: Analyze Research Questions**
```bash
# RQ1: Library distribution analysis
python scripts/analysis/log_level_timber.py
python scripts/analysis/log_level_slf4j.py
python scripts/analysis/log_level_logger.py

# RQ2: Log level and source analysis
python scripts/analysis/source_category_scan.py
python scripts/analysis/source_statement_generator.py

# RQ3: Data flow complexity analysis
python scripts/preprocessing/get_user_input_app_name.py

# RQ4: Temporal analysis (compare 2016-2021 vs 2023 versions)
python scripts/data_collection/leaking_app_downloader.py
```


### Key Configuration Points

Before running the analysis, you need to update these paths in the scripts:

1. **FlowDroid Configuration** (`scripts/flowdroid_analysis/flowdroid_script.py`):
   - `jar_path`: Path to FlowDroid JAR file (e.g., `./tools/soot-infoflow-cmd-2.13.0-jar-with-dependencies.jar`)
   - `sink_And_source_path`: Path to sink/source configuration file (e.g., `./config/sinkAndSouce_test1.txt`)
   - `platform_path`: Path to Android platforms directory (e.g., `./tools/android/platforms`)
   - `output`: Path for FlowDroid results (e.g., `./results/raw_outputs`)

2. **Main Dataset Download** (`scripts/data_collection/download_main_dataset.py`):
   - `API_KEY`: Your AndroZoo API key
   - `latest_csv_path`: Path to AndroZoo metadata CSV (e.g., `./data/metadata/latest.csv`)
   - `download_folder`: Directory for downloaded APKs (e.g., `./data/apks/main_dataset`)

3. **Temporal Analysis Download** (`scripts/data_collection/leaking_app_downloader.py`):
   - `API_KEY`: Your AndroZoo API key
   - `latest_csv_path`: Path to AndroZoo metadata CSV (e.g., `./data/metadata/latest.csv`)
   - `leaking_apps_csv_path`: Path to list of apps with privacy leaks (generated from RQ1 analysis)
   - `download_folder`: Directory for downloaded APKs (e.g., `./data/apks/leaking_app_v2023`)
   - **Note**: This script is specifically for RQ4 temporal analysis - it downloads 2023 versions of apps that had leaks in the original dataset

4. **Data Processing Scripts** (`scripts/preprocessing/` and `scripts/analysis/`):
   - Update file paths in each script to use relative paths from repository root
   - Modify CSV file paths to point to `./results/` subdirectories

<!-- ### Processed Results

Processed analysis results are available at:
- **Figshare**: [https://figshare.com/s/558ce343893c8a88f4f8](https://figshare.com/s/558ce343893c8a88f4f8) -->
