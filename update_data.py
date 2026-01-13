"""
SPINS Data Updater Script
This script helps update the dashboard with new weekly SPINS data
"""

import pandas as pd
import os
from datetime import datetime
import shutil

class SPINSDataUpdater:
    def __init__(self, data_directory="."):
        self.data_dir = data_directory
        self.archive_dir = os.path.join(data_directory, "archive")
        os.makedirs(self.archive_dir, exist_ok=True)

    def archive_old_data(self):
        """Archive existing data files before updating"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Find existing files
        existing_files = [
            f for f in os.listdir(self.data_dir)
            if f.startswith("SPIN") and f.endswith(".xlsx")
        ]

        for file in existing_files:
            src = os.path.join(self.data_dir, file)
            dst = os.path.join(self.archive_dir, f"{timestamp}_{file}")
            shutil.copy2(src, dst)
            print(f"✓ Archived: {file} -> archive/{timestamp}_{file}")

    def validate_file(self, filepath, expected_sheets):
        """Validate that a file has the expected structure"""
        try:
            xl_file = pd.ExcelFile(filepath)
            missing_sheets = set(expected_sheets) - set(xl_file.sheet_names)

            if missing_sheets:
                print(f"⚠ Warning: Missing sheets in {filepath}: {missing_sheets}")
                return False

            print(f"✓ Valid: {os.path.basename(filepath)}")
            return True
        except Exception as e:
            print(f"✗ Error validating {filepath}: {e}")
            return False

    def update_brand_data(self, new_file_path):
        """Update the brand and retailers data file"""
        expected_sheets = ['Raw', 'Pivot', 'Category Charts (52-wks)']

        if not os.path.exists(new_file_path):
            print(f"✗ File not found: {new_file_path}")
            return False

        if self.validate_file(new_file_path, expected_sheets):
            # Archive old file
            old_file = os.path.join(self.data_dir, "SPINs Brand and Retailers_110225.xlsx")
            if os.path.exists(old_file):
                self.archive_old_data()

            # Copy new file
            dest_file = os.path.join(self.data_dir, os.path.basename(new_file_path))
            shutil.copy2(new_file_path, dest_file)
            print(f"✓ Updated brand data: {os.path.basename(new_file_path)}")

            # Load and check data
            df = pd.read_excel(dest_file, sheet_name='Raw')
            print(f"  Records: {len(df):,}")
            print(f"  Brands: {df['DESCRIPTION'].nunique()}")
            print(f"  Time periods: {df['TIME FRAME'].unique()}")

            return True

        return False

    def update_trend_data(self, new_file_path):
        """Update the Humble trend data file"""
        expected_sheets = ['Raw', 'Charts']

        if not os.path.exists(new_file_path):
            print(f"✗ File not found: {new_file_path}")
            return False

        if self.validate_file(new_file_path, expected_sheets):
            # Archive old file
            old_file = os.path.join(self.data_dir, "SPINs Humble_Trended Sale_100525.xlsx")
            if os.path.exists(old_file):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                archive_path = os.path.join(self.archive_dir, f"{timestamp}_{os.path.basename(old_file)}")
                shutil.copy2(old_file, archive_path)
                print(f"✓ Archived: {os.path.basename(old_file)}")

            # Copy new file
            dest_file = os.path.join(self.data_dir, os.path.basename(new_file_path))
            shutil.copy2(new_file_path, dest_file)
            print(f"✓ Updated trend data: {os.path.basename(new_file_path)}")

            # Load and check data
            df = pd.read_excel(dest_file, sheet_name='Raw')
            print(f"  Records: {len(df):,}")
            print(f"  Time periods: {df['TIME FRAME'].nunique()}")

            return True

        return False

    def run_update(self, brand_file=None, trend_file=None):
        """Run the complete update process"""
        print("="*80)
        print("SPINS DATA UPDATER")
        print("="*80)
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        success = True

        if brand_file:
            print("Updating Brand & Retailers data...")
            success &= self.update_brand_data(brand_file)
            print()

        if trend_file:
            print("Updating Trend data...")
            success &= self.update_trend_data(trend_file)
            print()

        if success:
            print("="*80)
            print("✓ DATA UPDATE COMPLETE")
            print("="*80)
            print("\nNext steps:")
            print("1. Run the dashboard: streamlit run spins_dashboard.py")
            print("2. Verify the new data displays correctly")
            print("3. Check that date ranges and metrics look accurate")
        else:
            print("="*80)
            print("✗ UPDATE FAILED - Please check errors above")
            print("="*80)

        return success


def main():
    """Main function for command-line usage"""
    import argparse

    parser = argparse.ArgumentParser(description='Update SPINS dashboard data')
    parser.add_argument('--brand-file', help='Path to new brand & retailers Excel file')
    parser.add_argument('--trend-file', help='Path to new trend Excel file')
    parser.add_argument('--data-dir', default='.', help='Data directory (default: current)')

    args = parser.parse_args()

    if not args.brand_file and not args.trend_file:
        print("Error: Please specify at least one file to update")
        print("Usage: python update_data.py --brand-file <path> --trend-file <path>")
        return

    updater = SPINSDataUpdater(args.data_dir)
    updater.run_update(args.brand_file, args.trend_file)


if __name__ == "__main__":
    main()
