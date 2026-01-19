import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import re
from collections import Counter, defaultdict
import os

# Set up the file path
csv_file_path = "./results/processed_data/flowdriod_outcome_2/flowdroid_data_flows.csv"

def extract_method_signature(source_text):
    """Extract the method signature from FlowDroid source text"""
    if not source_text or pd.isna(source_text):
        return None
    
    # Look for method signature pattern: <class: returnType method(params)>
    method_match = re.search(r'<([^:]+):\s*([^>]+)>', source_text)
    if method_match:
        class_name = method_match.group(1)
        method_signature = method_match.group(2)
        return class_name, method_signature
    
    return None, None

def categorize_source_by_susi(class_name, method_signature):
    """Categorize sources using SUSI's 12-category system"""
    if not class_name or not method_signature:
        return "unknown"
    
    class_lower = class_name.lower()
    method_lower = method_signature.lower()
    
    # Account category
    if any(keyword in class_lower for keyword in ['firebase.auth', 'google.auth', 'account', 'user', 'credential', 'signin']):
        return "account"
    if any(keyword in method_lower for keyword in ['getuid', 'getemail', 'getdisplayname', 'gettoken', 'getcredential']):
        return "account"
    
    # Bluetooth category
    if 'bluetooth' in class_lower or 'getaddress' in method_lower:
        return "bluetooth"
    
    # Browser category
    if any(keyword in class_lower for keyword in ['browser', 'webview', 'webkit']):
        return "browser"
    if any(keyword in method_lower for keyword in ['geturl', 'gettitle', 'bookmark']):
        return "browser"
    
    # Calendar category
    if any(keyword in class_lower for keyword in ['calendar', 'date', 'time']):
        return "calendar"
    
    # Contact category
    if any(keyword in class_lower for keyword in ['contact', 'address']):
        return "contact"
    
    # Database category
    if any(keyword in class_lower for keyword in ['database', 'sqlite', 'cursor', 'contentresolver']):
        return "database"
    if any(keyword in method_lower for keyword in ['query', 'getstring', 'getcursor']):
        return "database"
    
    # File category
    if any(keyword in class_lower for keyword in ['file', 'inputstream', 'outputstream', 'reader', 'writer', 'epub']):
        return "file"
    if any(keyword in method_lower for keyword in ['read', 'write', 'getinputstream', 'tostring', 'getabsolute']):
        return "file"
    
    # Network category
    if any(keyword in class_lower for keyword in ['http', 'url', 'network', 'wifi', 'telephony', 'gsm']):
        return "network"
    if any(keyword in method_lower for keyword in ['getmacaddress', 'getssid', 'getcid', 'getlac', 'getentity']):
        return "network"
    
    # NFC category
    if 'nfc' in class_lower:
        return "nfc"
    
    # Settings category
    if any(keyword in class_lower for keyword in ['preference', 'setting', 'config', 'locale']):
        return "settings"
    if any(keyword in method_lower for keyword in ['getcountry', 'getsharedpreferences']):
        return "settings"
    
    # Sync category
    if any(keyword in class_lower for keyword in ['sync', 'livedata', 'observable', 'binding']):
        return "sync"
    
    # Unique-identifier category
    if any(keyword in class_lower for keyword in ['telephonymanager']):
        return "unique-identifier"
    if any(keyword in method_lower for keyword in ['getdeviceid', 'getsubscriberid', 'getsim', 'getline1number']):
        return "unique-identifier"
    
    # Location (not in SUSI but important)
    if any(keyword in class_lower for keyword in ['location']):
        return "location"
    if any(keyword in method_lower for keyword in ['getlatitude', 'getlongitude', 'getlastknownlocation']):
        return "location"
    
    # User Input (not in SUSI but common in Android)
    if any(keyword in class_lower for keyword in ['edittext', 'textview', 'input', 'receiver', 'intent']):
        return "user-input"
    
    # Analytics/Logging
    if any(keyword in class_lower for keyword in ['analytics', 'firebase.analytics', 'log']):
        return "analytics"
    
    return "other"

def analyze_flowdroid_sources():
    """Main analysis function"""
    try:
        # Read the CSV file
        print(f"Reading CSV file: {csv_file_path}")
        df = pd.read_csv(csv_file_path)
        
        print(f"Total rows: {len(df)}")
        print(f"Columns: {df.columns.tolist()}")
        
        # Display first few rows to understand structure
        print("\nFirst 3 rows:")
        for i in range(min(3, len(df))):
            print(f"Row {i}: {df.iloc[i]['source'] if 'source' in df.columns else 'No source column'}")
        
        # Extract and categorize sources
        source_categories = []
        source_methods = []
        source_classes = []
        
        print(f"\nParsing source methods...")
        
        for idx, row in df.iterrows():
            source_text = str(row['source']) if 'source' in df.columns else ""
            class_name, method_signature = extract_method_signature(source_text)
            
            # Debug output for first 5 rows
            if idx < 5:
                print(f"\nRow {idx}:")
                print(f"  Original: {source_text}")
                print(f"  Parsed Class: {class_name}")
                print(f"  Parsed Method: {method_signature}")
            
            if class_name:
                category = categorize_source_by_susi(class_name, method_signature)
                source_categories.append(category)
                source_methods.append(method_signature if method_signature else "unknown")
                source_classes.append(class_name)
                
                # Debug categorization for first 5 rows
                if idx < 5:
                    print(f"  Category: {category}")
            else:
                source_categories.append("unparseable")
                source_methods.append("unknown")
                source_classes.append("unknown")
        
        # Add categories to dataframe
        df['source_category'] = source_categories
        df['source_class'] = source_classes
        df['source_method'] = source_methods
        
        # Category distribution analysis
        category_counts = Counter(source_categories)
        
        print(f"\n{'='*60}")
        print("SOURCE CATEGORY DISTRIBUTION (SUSI Classification)")
        print(f"{'='*60}")
        
        for category, count in category_counts.most_common():
            percentage = (count / len(df)) * 100
            print(f"{category:<25}: {count:>5} flows ({percentage:>5.1f}%)")
        
        # Show top source classes for the most common category
        top_category = category_counts.most_common(1)[0][0]
        print(f"\nTop classes in '{top_category}' category:")
        print("-" * 40)
        
        top_category_df = df[df['source_category'] == top_category]
        top_classes_in_category = Counter(top_category_df['source_class'])
        for class_name, count in top_classes_in_category.most_common(5):
            print(f"  {class_name:<40}: {count:>3} flows")
        
        # App-wise category analysis
        if 'app_name' in df.columns:
            print(f"\n{'='*60}")
            print("CATEGORY DISTRIBUTION BY APP")
            print(f"{'='*60}")
            
            app_category_analysis = df.groupby(['app_name', 'source_category']).size().unstack(fill_value=0)
            print(app_category_analysis)
        
        # Top source classes overall
        print(f"\n{'='*60}")
        print("TOP 15 SOURCE CLASSES (All Categories)")
        print(f"{'='*60}")
        
        class_counts = Counter(source_classes)
        for class_name, count in class_counts.most_common(15):
            # Find the most common category for this class
            class_df = df[df['source_class'] == class_name]
            main_category = class_df['source_category'].mode().iloc[0] if len(class_df) > 0 else "unknown"
            print(f"{class_name:<50}: {count:>3} flows ({main_category})")
        
        # Create visualizations
        create_visualizations(df, category_counts, class_counts)
        
        # Save detailed results
        save_detailed_results(df, category_counts)
        
        return df, category_counts
        
    except FileNotFoundError:
        print(f"Error: File not found at {csv_file_path}")
        print("Please check the file path and ensure the file exists.")
        return None, None
    except Exception as e:
        print(f"Error analyzing file: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None

def create_visualizations(df, category_counts, class_counts):
    """Create visualization plots"""
    
    output_dir = "./results/processed_data/source_cluster"
    
    # Set up the plotting style
    plt.style.use('default')
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('FlowDroid Source Category Analysis', fontsize=16, fontweight='bold')
    
    # 1. Category distribution pie chart
    ax1 = axes[0, 0]
    categories = list(category_counts.keys())
    counts = list(category_counts.values())
    
    # Only show categories with more than 1% to avoid clutter
    threshold = max(1, len(df) * 0.01)
    filtered_data = [(cat, count) for cat, count in zip(categories, counts) if count >= threshold]
    other_count = sum(count for cat, count in zip(categories, counts) if count < threshold)
    
    if other_count > 0:
        filtered_data.append(('other_small', other_count))
    
    if filtered_data:
        filtered_categories, filtered_counts = zip(*filtered_data)
        ax1.pie(filtered_counts, labels=filtered_categories, autopct='%1.1f%%', startangle=90)
        ax1.set_title('Source Category Distribution')
    
    # 2. Category distribution bar chart
    ax2 = axes[0, 1]
    top_categories = category_counts.most_common(10)
    cats, cnts = zip(*top_categories)
    bars = ax2.bar(range(len(cats)), cnts, color='skyblue', alpha=0.7)
    ax2.set_xlabel('Category')
    ax2.set_ylabel('Number of Flows')
    ax2.set_title('Top 10 Source Categories')
    ax2.set_xticks(range(len(cats)))
    ax2.set_xticklabels(cats, rotation=45, ha='right')
    
    # Add value labels on bars
    for bar, count in zip(bars, cnts):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                f'{count}', ha='center', va='bottom')
    
    # 3. Top source classes
    ax3 = axes[1, 0]
    top_classes = class_counts.most_common(8)
    classes, class_cnts = zip(*top_classes)
    
    # Truncate long class names for display
    display_classes = [cls.split('.')[-1] if '.' in cls else cls for cls in classes]
    display_classes = [cls[:20] + '...' if len(cls) > 20 else cls for cls in display_classes]
    
    bars = ax3.barh(range(len(classes)), class_cnts, color='lightcoral', alpha=0.7)
    ax3.set_xlabel('Number of Flows')
    ax3.set_ylabel('Source Class')
    ax3.set_title('Top 8 Source Classes')
    ax3.set_yticks(range(len(classes)))
    ax3.set_yticklabels(display_classes)
    
    # 4. App-wise category distribution (if available)
    ax4 = axes[1, 1]
    if 'app_name' in df.columns and df['app_name'].nunique() > 1:
        app_category_counts = df.groupby(['app_name', 'source_category']).size().unstack(fill_value=0)
        app_category_counts.plot(kind='bar', stacked=True, ax=ax4, alpha=0.7)
        ax4.set_title('Source Categories by App')
        ax4.set_xlabel('App')
        ax4.set_ylabel('Number of Flows')
        ax4.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax4.tick_params(axis='x', rotation=45)
    else:
        ax4.text(0.5, 0.5, 'Single App Dataset\nor No App Data', 
                ha='center', va='center', transform=ax4.transAxes, fontsize=12)
        ax4.set_title('App Distribution')
    
    plt.tight_layout()
    
    # Save visualization
    viz_file = os.path.join(output_dir, 'source_analysis_charts.png')
    plt.savefig(viz_file, dpi=300, bbox_inches='tight')
    print(f"\n  Visualization saved to: source_analysis_charts.png")
    plt.show()

def save_detailed_results(df, category_counts):
    """Save detailed analysis results to files"""
    
    # Save categorized dataframe
    output_file = 'flowdroid_categorized_sources.csv'
    df.to_csv(output_file, index=False)
    print(f"\nDetailed results saved to: {output_file}")
    
    # Save category summary
    summary_file = 'source_category_summary.txt'
    with open(summary_file, 'w') as f:
        f.write("FlowDroid Source Category Analysis Summary\n")
        f.write("="*50 + "\n\n")
        f.write(f"Total data flows analyzed: {len(df)}\n")
        f.write(f"Unique source categories: {len(category_counts)}\n\n")
        
        f.write("Category Distribution:\n")
        f.write("-" * 30 + "\n")
        for category, count in category_counts.most_common():
            percentage = (count / len(df)) * 100
            f.write(f"{category:<20}: {count:>5} ({percentage:>5.1f}%)\n")
    
    print(f"Summary saved to: {summary_file}")

if __name__ == "__main__":
    print("FlowDroid Source Category Analysis")
    print("="*50)
    
    # Check if file exists
    if not os.path.exists(csv_file_path):
        print(f"File not found: {csv_file_path}")
        print("Please verify the file path is correct.")
    else:
        df, category_counts = analyze_flowdroid_sources()
        
        if df is not None:
            print(f"\nAnalysis complete! Check the generated files:")
            print("- flowdroid_source_analysis.png (visualization)")
            print("- flowdroid_categorized_sources.csv (detailed data)")
            print("- source_category_summary.txt (summary)")