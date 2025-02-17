# Group and Rename astrophotography data for PixInsight WBPP

This script helps group flat frames and light frames based on the dates they were taken. The grouping keyword `Grp` is added as a prefix to each file name, which can be used in PixInsight's WBPP for easy batch processing.

## Overview

The script can process directories with the following structure:
```
WitchHead/ 
        ├── IC2118_Pane_01
        │   ├── System1
        │   │   ├── L
        │   │   │   ├── FLAT
        |   |   |   ├── LIGHT
        |   |   ├── Ha
        │   │   │   ├── FLAT
        |   |   |   ├── LIGHT
        │   ├── System2
        │   │   ├── L
        │   │   │   ├── FLAT
        |   |   |   ├── LIGHT
        |   |   ├── Ha
        │   │   │   ├── FLAT
        |   |   |   ├── LIGHT
```


For each filter folder (such as `B`, `R`, etc.) containing `FLAT` and `LIGHT` subfolders, the script performs the following tasks:

1. **Grouping FLAT Frames:**  
   Scans the `FLAT` folder and groups files by the date they were taken (ignoring the time portion). All FLAT files taken on the same day are assigned the same group.

2. **Renaming Files:**  
   Renames each FLAT file by adding a prefix like `Grp_XX_` (where `XX` is a two-digit group number).  
   Renames each LIGHT file based on one of two grouping logics (see below), also prefixing the file name with `Grp_XX_`.

## Grouping Logics

The script supports two grouping logics, selectable via the `--logic` argument:

### 1. Direct Logic

- **Description:**  
  LIGHT frames are grouped directly based on the FLAT dates.  
  **Example:**  
  If LIGHT frames were captured every day from **2024-11-15** to **2024-11-30**, but FLAT frames were taken on:
  - **2024-11-15**
  - **2024-11-20**
  - **2024-11-27**

  then the groups would be:
  - **Grp_01:** LIGHT frames captured from 2024-11-15 up to (but not including) 2024-11-20.
  - **Grp_02:** LIGHT frames captured from 2024-11-20 up to (but not including) 2024-11-27.
  - **Grp_03:** LIGHT frames captured on or after 2024-11-27.

### 2. Midpoint Logic

- **Description:**  
  The script computes boundaries as the midpoints between consecutive FLAT dates (using midnight for each date).  
  **Example:**  
  If FLAT frames were taken on:
  - **2024-10-15** and
  - **2024-10-31**

  the midpoint would be approximately **2024-10-23**. Then:
  - LIGHT frames captured **before 2024-10-23** are assigned to **Grp_01**.
  - LIGHT frames captured **on or after 2024-10-23** are assigned to **Grp_02**.

  This ensures that, for example, a LIGHT frame captured on **2024-10-24** is grouped as **Grp_02**.

## Command-Line Usage

The script is executed from the command line and accepts the following arguments:

- `root_dir`: The root directory where your folder structure begins (e.g., `WitchHead`).
- `--logic`: The grouping logic to use. Options:
  - `direct` (default): Groups LIGHT frames directly based on FLAT dates.
  - `midpoint`: Groups LIGHT frames based on computed midpoints between FLAT dates.
- `--start-index`: The starting group number (default is `1`). This allows you to offset the group numbering (e.g., starting from `Grp_05`).

### Example Commands

```bash
# Using direct logic with default starting index (1)
python group_and_rename.py WitchHead --logic direct --start-index 1

# Using midpoint logic with a starting index of 5
python group_and_rename.py WitchHead --logic midpoint --start-index 5
