# Garmin Connect Data Export CSV Parser

This script parses selected JSON files from a Garmin Connect data export and converts them into CSV format. It's designed to help users access and utilize their health and fitness data in a more traditional, tabular format for personal analysis, backup, or import into other systems.

## Features

*   Extracts data for User Biometrics, Sleep, and Max METs.
*   Filters data for a user-defined date range (default: Feb 2020 - mid 2025).
*   Outputs data into separate CSV files for each category.
*   Handles various Garmin timestamp formats.
*   Includes basic error handling and duplicate removal.

## Prerequisites

*   Python 3.x
*   A Garmin Connect data export (specifically the JSON files found within the `DI_CONNECT` directory structure).

## How to Use

1.  **Download Your Garmin Data**:
    *   Request your data export from Garmin Connect through your account settings.
    *   Once downloaded, unzip the export.

2.  **Set Up the Parser**:
    *   Clone this repository or download the `parser.py` script into a new folder (e.g., `garmin_csv_export`).
    *   Place the `parser.py` script in a directory. For example, if your Garmin export is unzipped to `~/Downloads/Garmin_Export`, and you create `~/Code/garmin_csv_export/` for this script, the script expects the `DI_CONNECT` folder to be at `~/Downloads/Garmin_Export/DI_CONNECT`.
    *   Modify the `BASE_SOURCE_DIR` variable in `parser.py` if your `DI_CONNECT` directory is located elsewhere relative to the script. The default is `../DI_CONNECT`, meaning it looks one directory up from where `parser.py` is located and then into `DI_CONNECT`.

3.  **Run the Script**:
    *   Navigate to the directory containing `parser.py` in your terminal.
    *   Execute the script:
        ```bash
        python parser.py
        ```

4.  **Access Your CSV Files**:
    *   The script will generate the following CSV files in the same directory where `parser.py` is located:
        *   `user_biometrics.csv`
        *   `sleep_data.csv`
        *   `max_met_data.csv`

## CSV Output Details

### `user_biometrics.csv`
*   **Source:** `DI_CONNECT/DI-Connect-Wellness/83630101_userBioMetrics.json`
*   **Description:** Contains periodic snapshots of biometric data, primarily profile changes like weight, height, and VO2Max. 
    *   **Note:** Many fields in the desired CSV structure (like daily resting HR, HRV, stress, SpO2) are *not* typically found in this specific JSON file. The script will create these columns, but they may be empty. These metrics are often in "Dailies" monitoring files not processed by this script version.
*   **Columns:** `datetime`, `resting_hr`, `hrv`, `stress_level`, `body_battery`, `spo2`, `respiration_rate`

### `sleep_data.csv`
*   **Source:** `DI_CONNECT/DI-Connect-Wellness/*_sleepData.json` files.
*   **Description:** Contains nightly sleep summaries, including duration, sleep stages, and some related metrics.
*   **Columns:** `date`, `sleep_duration` (minutes), `deep_sleep` (minutes), `rem_sleep` (minutes), `light_sleep` (minutes), `wake_time` (minutes), `sleep_score`, `resting_hr_sleep`, `hrv_sleep`
    *   **Note:** `sleep_score` and `hrv_sleep` might be empty if not available in the source JSONs.

### `max_met_data.csv`
*   **Source:** `DI_CONNECT/DI-Connect-Metrics/MetricsMaxMetData_*.json` files.
*   **Description:** Provides information about maximum metabolic equivalent (MET) and VO2 max values, often linked to activities.
*   **Columns:** `start_time`, `activity_type`, `duration_min`, `max_met`, `avg_hr`, `max_hr`, `training_effect`
    *   **Note:** `duration_min`, `avg_hr`, `max_hr`, and `training_effect` are typically found in detailed activity summary files (not processed by this script) and will likely be empty in this CSV.

## Customization

*   **Date Range:** Modify `START_DATE_FILTER` and `END_DATE_FILTER` in the script to change the processing window.
*   **Data Fields:** To extract additional fields or target different JSON files, you will need to modify the respective `process_...()` functions within the script. This includes updating `csv_headers` and the logic for `safe_get` calls to match the JSON structure of the desired data.
*   **File Paths:** Adjust `BASE_SOURCE_DIR` and `TARGET_DIR` as needed.

## Troubleshooting

*   **`FileNotFoundError`:** Ensure `BASE_SOURCE_DIR` correctly points to the parent directory of your `DI_CONNECT` folder.
*   **Timestamp Parsing Warnings:** The script attempts to parse common Garmin timestamp formats. If you see warnings like "Unrecognized date format" or "Could not parse timestamp," the `parse_garmin_timestamp` function may need to be updated to handle the specific format in your files.
*   **Missing Data in CSVs:** As noted, some requested CSV columns might be empty if the corresponding data is not present in the specific JSON files processed by this script or if it's under different keys. You might need to investigate other JSON files in your export (like those for individual activities or daily summaries) and extend the parser.

## Contributing

Contributions are welcome! If you improve the script or add new features, feel free to open a pull request or an issue.

## License

This project is open-source and available under the [MIT License](LICENSE.txt).