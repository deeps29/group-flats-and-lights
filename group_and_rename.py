import os
import re
from datetime import datetime, timedelta
import argparse

def extract_date(filename):
    """
    Extracts just the YYYY-MM-DD portion from the filename and returns a date object.
    For example: 'IC2118_Pane_01_System_1_B_2024-10-15_22-11-30_...' → date(2024, 10, 15).
    """
    match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
    if match:
        try:
            return datetime.strptime(match.group(1), '%Y-%m-%d').date()
        except ValueError:
            return None
    return None

def process_light_folder(light_dir, flat_dir, start_index, logic):
    """
    Processes one filter folder (e.g., .../System1/B) by:
      1. Gathering all FLAT files (using only their calendar date) and creating a sorted list
         of unique flat dates.
      2. Renaming each FLAT file with a prefix "Grp_XX_" where XX is determined by the date’s order,
         plus the starting index.
      3. Renaming each LIGHT file based on the chosen grouping logic:
           - "direct": Each LIGHT file is assigned to the group where its date is >= a flat date
                       and (if not the last group) before the next flat date.
           - "midpoint": Boundaries are computed as midpoints (using midnight) between consecutive
                         flat dates; each LIGHT file is assigned to a group based on how many boundaries
                         its date exceeds.
    """
    # --- 1) Gather FLAT files and extract their dates ---
    try:
        flat_files = [f for f in os.listdir(flat_dir) if os.path.isfile(os.path.join(flat_dir, f))]
    except Exception as e:
        print(f"Error reading FLAT folder {flat_dir}: {e}")
        return

    flat_dates_list = []
    for f in flat_files:
        d = extract_date(f)
        if d:
            flat_dates_list.append(d)

    if not flat_dates_list:
        print(f"No FLAT dates found in {flat_dir}. Skipping folder: {light_dir}")
        return

    unique_flat_dates = sorted(set(flat_dates_list))
    print(f"\nFound FLAT dates in '{flat_dir}': {unique_flat_dates}")

    # --- 2) Rename FLAT files so that all flats on the same day share the same group ---
    # Group number = index in unique_flat_dates + start_index.
    for f in flat_files:
        if f.startswith("Grp_"):
            continue  # Already renamed.
        d = extract_date(f)
        if not d:
            print(f"Could not extract date from FLAT file '{f}' in {flat_dir}, skipping.")
            continue
        try:
            group_idx = unique_flat_dates.index(d) + start_index
        except ValueError:
            group_idx = start_index
        new_name = f"Grp_{group_idx:02d}_" + f
        old_path = os.path.join(flat_dir, f)
        new_path = os.path.join(flat_dir, new_name)
        print(f"Renaming FLAT file:\n  {old_path}\n  to\n  {new_path}\n")
        try:
            os.rename(old_path, new_path)
        except Exception as e:
            print(f"Error renaming FLAT file {old_path} to {new_path}: {e}")

    # --- 3) Process LIGHT files based on the chosen grouping logic ---
    try:
        light_files = [f for f in os.listdir(light_dir) if os.path.isfile(os.path.join(light_dir, f))]
    except Exception as e:
        print(f"Error reading LIGHT folder {light_dir}: {e}")
        return

    if logic == "direct":
        # Direct grouping: Use each flat date as the boundary.
        for f in light_files:
            if f.startswith("Grp_"):
                continue
            d = extract_date(f)
            if not d:
                print(f"Could not extract date from LIGHT file '{f}' in {light_dir}, skipping.")
                continue

            group = None
            for i, flat_date in enumerate(unique_flat_dates):
                # If this is the last flat date or if the light date is before the next flat date:
                if d >= flat_date and (i == len(unique_flat_dates) - 1 or d < unique_flat_dates[i + 1]):
                    group = i + start_index
                    break

            if group is None:
                group = start_index

            new_name = f"Grp_{group:02d}_" + f
            old_path = os.path.join(light_dir, f)
            new_path = os.path.join(light_dir, new_name)
            print(f"Renaming LIGHT file:\n  {old_path}\n  to\n  {new_path}\n")
            try:
                os.rename(old_path, new_path)
            except Exception as e:
                print(f"Error renaming LIGHT file {old_path} to {new_path}: {e}")

    elif logic == "midpoint":
        # Midpoint grouping: Compute boundaries as midpoints between consecutive flat dates.
        flat_midnights = [datetime(d.year, d.month, d.day) for d in unique_flat_dates]
        boundaries = []
        for i in range(len(flat_midnights) - 1):
            start_time = flat_midnights[i]
            end_time = flat_midnights[i + 1]
            midpoint = start_time + (end_time - start_time) / 2
            boundaries.append(midpoint)
        print(f"Computed boundaries: {boundaries}")

        for f in light_files:
            if f.startswith("Grp_"):
                continue
            d = extract_date(f)
            if not d:
                print(f"Could not extract date from LIGHT file '{f}' in {light_dir}, skipping.")
                continue
            light_dt = datetime(d.year, d.month, d.day)
            group = start_index
            for boundary in boundaries:
                if light_dt >= boundary:
                    group += 1
                else:
                    break

            new_name = f"Grp_{group:02d}_" + f
            old_path = os.path.join(light_dir, f)
            new_path = os.path.join(light_dir, new_name)
            print(f"Renaming LIGHT file:\n  {old_path}\n  to\n  {new_path}\n")
            try:
                os.rename(old_path, new_path)
            except Exception as e:
                print(f"Error renaming LIGHT file {old_path} to {new_path}: {e}")
    else:
        print(f"Unknown grouping logic: {logic}")

def process_directory(root_dir, start_index, logic):
    """
    Walks the directory tree starting at root_dir, looking for folders named LIGHT
    that have a sibling FLAT folder. Processes each filter folder independently.
    """
    for dirpath, dirnames, filenames in os.walk(root_dir):
        if os.path.basename(dirpath).upper() == "LIGHT":
            parent_dir = os.path.dirname(dirpath)
            flat_dir = os.path.join(parent_dir, "FLAT")
            if not os.path.exists(flat_dir):
                print(f"FLAT folder not found next to LIGHT folder: {dirpath}")
                continue

            print(f"\nProcessing filter folder: {parent_dir}")
            process_light_folder(dirpath, flat_dir, start_index, logic)

def main():
    parser = argparse.ArgumentParser(
        description="Group and rename LIGHT/FLAT files by date with selectable grouping logic."
    )
    parser.add_argument("root_dir", help="Root directory (e.g., WitchHead) where the folder structure begins.")
    parser.add_argument("--start-index", type=int, default=1,
                        help="Starting group index (default: 1)")
    parser.add_argument("--logic", choices=["direct", "midpoint"], default="direct",
                        help=("Grouping logic to use: 'direct' uses flat dates as boundaries (lights taken on/after a flat date and "
                              "before the next flat date are grouped together), while 'midpoint' computes midpoints between flat dates "
                              "and assigns lights based on those boundaries."))
    args = parser.parse_args()

    if not os.path.exists(args.root_dir):
        print(f"The directory {args.root_dir} does not exist.")
        return

    process_directory(args.root_dir, args.start_index, args.logic)

if __name__ == "__main__":
    main()
