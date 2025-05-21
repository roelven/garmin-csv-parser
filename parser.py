# This script will parse Garmin JSON data and export it to CSV files. 

import json
import csv
import os
from datetime import datetime, timezone

# --- Configuration ---
BASE_SOURCE_DIR = "../DI_CONNECT"  # Assuming parser.py is in garmin_csv_export
TARGET_DIR = "." # Output CSVs in the same directory as the script

# Date range for filtering
START_DATE_FILTER = datetime(2020, 2, 1, tzinfo=timezone.utc)
END_DATE_FILTER = datetime(2025, 6, 30, tzinfo=timezone.utc)

# --- Helper Functions ---
def safe_get(data, keys, default=None):
    """Safely get a value from a nested dictionary."""
    for key in keys:
        if isinstance(data, dict) and key in data:
            data = data[key]
        else:
            return default
    return data

def parse_garmin_timestamp(ts_str):
    """Parses various Garmin timestamp formats to a timezone-aware datetime object."""
    if not ts_str:
        return None
    try:
        # Try formats with milliseconds and timezone offset (e.g., "2020-02-15T13:19:26.265Z" or "...+00:00")
        if '.' in ts_str and ('Z' in ts_str or '+' in ts_str or '-' in ts_str[10:]): # Check for timezone indicator after year
            # Handle Z for UTC
            if ts_str.endswith('Z'):
                ts_str = ts_str[:-1] + "+00:00"
            
            # Handle timezone offsets like +02:00 or -0700
            if ":" == ts_str[-3:-2]: # e.g. +02:00
                 dt_obj = datetime.fromisoformat(ts_str)
            elif len(ts_str) > 6 and ts_str[-5] in ['+', '-'] and ts_str[-3] not in [':']: # e.g. -0700
                ts_str_with_colon = ts_str[:-2] + ":" + ts_str[-2:]
                dt_obj = datetime.fromisoformat(ts_str_with_colon)
            else: # Assume it's parsable if it has a decimal for seconds
                 dt_obj = datetime.fromisoformat(ts_str)

        # Try "YYYY-MM-DDTHH:MM:SS.0" (GMT/UTC assumed)
        elif '.' in ts_str:
            dt_obj = datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%S.%f").replace(tzinfo=timezone.utc)
        # Try "YYYY-MM-DDTHH:MM:SS" (GMT/UTC assumed)
        elif 'T' in ts_str and len(ts_str) == 19 :
             dt_obj = datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
        # Try "YYYY-MM-DD" (midnight UTC assumed)
        elif len(ts_str) == 10 and '-' in ts_str:
            dt_obj = datetime.strptime(ts_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        else:
            print(f"Warning: Unrecognized date format for timestamp: {ts_str}")
            return None
        
        return dt_obj.astimezone(timezone.utc) # Ensure all are UTC for comparison
    except ValueError as e:
        print(f"Warning: Could not parse timestamp '{ts_str}': {e}")
        return None

def is_in_date_range(dt_obj):
    if dt_obj is None:
        return False
    # Ensure dt_obj is timezone-aware (UTC) for comparison
    if dt_obj.tzinfo is None:
        dt_obj = dt_obj.replace(tzinfo=timezone.utc)
    return START_DATE_FILTER <= dt_obj <= END_DATE_FILTER

def format_datetime_csv(dt_obj):
    """Formats datetime object to 'YYYY-MM-DDTHH:MM:SS' for CSV."""
    if dt_obj:
        return dt_obj.strftime("%Y-%m-%dT%H:%M:%S")
    return ''

def format_date_csv(dt_obj):
    """Formats datetime object to 'YYYY-MM-DD' for CSV."""
    if dt_obj:
        return dt_obj.strftime("%Y-%m-%d")
    return ''

# --- Processing Functions ---

def process_user_biometrics():
    source_file = os.path.join(BASE_SOURCE_DIR, "DI-Connect-Wellness", "83630101_userBioMetrics.json")
    csv_file = os.path.join(TARGET_DIR, "user_biometrics.csv")
    csv_headers = ["datetime", "resting_hr", "hrv", "stress_level", "body_battery", "spo2", "respiration_rate"]

    print(f"Processing {source_file} for {csv_file}...")
    
    processed_rows = []
    if not os.path.exists(source_file):
        print(f"Warning: Source file not found: {source_file}")
        return

    with open(source_file, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from {source_file}: {e}")
            return

    for record in data:
        # 'calendarDate' in metaData is usually the primary timestamp
        # Sometimes it's a full datetime string, sometimes just a date.
        # If it's just a date, other fields might give time-specific data for that day
        # For simplicity, we'll use calendarDate as the primary datetime marker.
        # Resting HR, HRV, Stress etc. are often daily averages or specific samples.
        # The Garmin export doesn't always provide fine-grained continuous data here.

        record_dt_str = safe_get(record, ["metaData", "calendarDate"])
        record_dt = parse_garmin_timestamp(record_dt_str)

        if record_dt and is_in_date_range(record_dt):
            #resting_hr: Not directly available in userBioMetrics.json in a simple daily way.
            #   It's usually derived from wellness summaries or specific heart rate samples.
            #   We'll leave it blank for now.
            #hrv: Not directly available.
            #stress_level: Not directly available.
            #body_battery: Not directly available.
            #spo2: Not directly available as a simple daily value.
            #respiration_rate: Not directly available.
            
            # The provided CSV structure for user_biometrics.csv asks for fields
            # that are typically found in daily wellness summaries (often called "dailies" or "monitoring"),
            # not in the `userBioMetrics.json` file which mostly contains profile settings
            # and occasional snapshots of VO2Max, weight, height.
            # For this parser, we will output the datetime and leave others blank as they are not in this specific file.
            # A more complete solution would involve parsing other files (e.g. dailies if they exist in the export).

            csv_row = {
                "datetime": format_datetime_csv(record_dt),
                "resting_hr": safe_get(record, ["restingHeartRate"], ''), # Placeholder if available
                "hrv": '',         # Placeholder
                "stress_level": '',# Placeholder
                "body_battery": '',# Placeholder
                "spo2": '',        # Placeholder
                "respiration_rate": '' # Placeholder
            }
            # This file is more about profile changes. We might get multiple entries for the same day.
            # Let's just add one entry per valid date for demonstration.
            # A real use case might need to decide how to aggregate/select.
            if not any(r["datetime"] == csv_row["datetime"] for r in processed_rows):
                 processed_rows.append(csv_row)


    if processed_rows:
        # Sort by datetime just in case records are not ordered
        processed_rows.sort(key=lambda x: x["datetime"])
        with open(csv_file, 'w', newline='', encoding='utf-8') as f_csv:
            writer = csv.DictWriter(f_csv, fieldnames=csv_headers)
            writer.writeheader()
            writer.writerows(processed_rows)
        print(f"Finished processing. {len(processed_rows)} rows written to {csv_file}")
    else:
        print(f"No data found for the specified date range in {source_file}")
        # Create empty CSV with headers if no data
        with open(csv_file, 'w', newline='', encoding='utf-8') as f_csv:
            writer = csv.DictWriter(f_csv, fieldnames=csv_headers)
            writer.writeheader()


def process_sleep_data():
    source_dir = os.path.join(BASE_SOURCE_DIR, "DI-Connect-Wellness")
    csv_file = os.path.join(TARGET_DIR, "sleep_data.csv")
    csv_headers = ["date", "sleep_duration", "deep_sleep", "rem_sleep", "light_sleep", "wake_time", "sleep_score", "resting_hr_sleep", "hrv_sleep"]
    
    print(f"Processing sleep data from {source_dir} for {csv_file}...")
    all_sleep_records = []

    if not os.path.exists(source_dir):
        print(f"Warning: Source directory not found: {source_dir}")
        return

    for filename in os.listdir(source_dir):
        if "_sleepData.json" in filename:
            file_path = os.path.join(source_dir, filename)
            # Optional: Add filename-based date pre-filtering here if needed
            # to skip files entirely outside the Feb 2020 - June 2025 range.
            
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON from {file_path}: {e}")
                    continue
                
                for record in data:
                    record_date_str = safe_get(record, ["calendarDate"])
                    record_dt = parse_garmin_timestamp(record_date_str)

                    if record_dt and is_in_date_range(record_dt):
                        sleep_start_dt = parse_garmin_timestamp(safe_get(record, ["sleepStartTimestampGMT"]))
                        sleep_end_dt = parse_garmin_timestamp(safe_get(record, ["sleepEndTimestampGMT"]))
                        
                        duration_seconds = 0
                        if sleep_start_dt and sleep_end_dt:
                            duration_seconds = (sleep_end_dt - sleep_start_dt).total_seconds()
                        
                        deep_seconds = safe_get(record, ["deepSleepSeconds"], 0)
                        rem_seconds = safe_get(record, ["remSleepSeconds"], 0)
                        light_seconds = safe_get(record, ["lightSleepSeconds"], 0)
                        awake_seconds = safe_get(record, ["awakeSleepSeconds"], 0)
                        
                        # sleep_duration should be total time in bed or total sleep time?
                        # Garmin Connect usually shows total sleep time (deep+light+rem).
                        # Your example "423" suggests minutes for "sleep_duration".
                        total_sleep_minutes = round((deep_seconds + light_seconds + rem_seconds) / 60) if (deep_seconds + light_seconds + rem_seconds) > 0 else 0
                        
                        # wake_time in your example is "21". This could be (awake_seconds / 60).
                        wake_minutes = round(awake_seconds / 60) if awake_seconds else 0

                        # sleep_score: Not directly in this detailed sleepData.json. Often in a daily summary. Placeholder.
                        # resting_hr_sleep: Can sometimes be in spo2SleepSummary.averageHR. Placeholder.
                        # hrv_sleep: Not directly available in sleepData. Placeholder.

                        csv_row = {
                            "date": format_date_csv(record_dt),
                            "sleep_duration": total_sleep_minutes,
                            "deep_sleep": round(deep_seconds / 60) if deep_seconds else 0,
                            "rem_sleep": round(rem_seconds / 60) if rem_seconds else 0,
                            "light_sleep": round(light_seconds / 60) if light_seconds else 0,
                            "wake_time": wake_minutes,
                            "sleep_score": safe_get(record, ["overallSleepScore", "value"], ''), # Check if available
                            "resting_hr_sleep": safe_get(record, ["spo2SleepSummary", "averageHR"], ''),
                            "hrv_sleep": '' # Placeholder
                        }
                        all_sleep_records.append(csv_row)

    if all_sleep_records:
        all_sleep_records.sort(key=lambda x: x["date"])
        # Remove duplicates by date, keeping the first one encountered (or last, if sorted differently)
        unique_sleep_records = []
        seen_dates = set()
        for rec in all_sleep_records:
            if rec["date"] not in seen_dates:
                unique_sleep_records.append(rec)
                seen_dates.add(rec["date"])
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f_csv:
            writer = csv.DictWriter(f_csv, fieldnames=csv_headers)
            writer.writeheader()
            writer.writerows(unique_sleep_records)
        print(f"Finished processing sleep data. {len(unique_sleep_records)} rows written to {csv_file}")
    else:
        print(f"No sleep data found for the specified date range in {source_dir}")
        with open(csv_file, 'w', newline='', encoding='utf-8') as f_csv:
            writer = csv.DictWriter(f_csv, fieldnames=csv_headers)
            writer.writeheader()

def process_max_met_data():
    source_dir = os.path.join(BASE_SOURCE_DIR, "DI-Connect-Metrics")
    csv_file = os.path.join(TARGET_DIR, "max_met_data.csv")
    csv_headers = ["start_time", "activity_type", "duration_min", "max_met", "avg_hr", "max_hr", "training_effect"]

    print(f"Processing METs data from {source_dir} for {csv_file}...")
    all_met_records = []

    if not os.path.exists(source_dir):
        print(f"Warning: Source directory not found: {source_dir}")
        return

    for filename in os.listdir(source_dir):
        if "MetricsMaxMetData_" in filename and filename.endswith(".json"):
            file_path = os.path.join(source_dir, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON from {file_path}: {e}")
                    continue

                for record in data:
                    # 'updateTimestamp' seems to be the most relevant start_time for the MET data point
                    record_dt_str = safe_get(record, ["updateTimestamp"]) 
                    record_dt = parse_garmin_timestamp(record_dt_str)
                    
                    # Also check 'calendarDate' for filtering if 'updateTimestamp' is missing or out of primary range
                    if not record_dt:
                        calendar_date_str = safe_get(record, ["calendarDate"])
                        record_dt = parse_garmin_timestamp(calendar_date_str)


                    if record_dt and is_in_date_range(record_dt):
                        # duration_min, avg_hr, max_hr, training_effect are not directly in MetricsMaxMetData.
                        # These typically come from detailed activity files.
                        # We will populate what's available from MetricsMaxMetData.
                        csv_row = {
                            "start_time": format_datetime_csv(record_dt),
                            "activity_type": safe_get(record, ["sport"], ''),
                            "duration_min": '', # Placeholder
                            "max_met": safe_get(record, ["maxMet"], ''),
                            "avg_hr": '',       # Placeholder
                            "max_hr": '',       # Placeholder
                            "training_effect": '' # Placeholder
                        }
                        all_met_records.append(csv_row)
    
    if all_met_records:
        all_met_records.sort(key=lambda x: x["start_time"])
        # Remove duplicates by start_time, keeping the first
        unique_met_records = []
        seen_times = set()
        for rec in all_met_records:
            if rec["start_time"] not in seen_times:
                unique_met_records.append(rec)
                seen_times.add(rec["start_time"])

        with open(csv_file, 'w', newline='', encoding='utf-8') as f_csv:
            writer = csv.DictWriter(f_csv, fieldnames=csv_headers)
            writer.writeheader()
            writer.writerows(unique_met_records)
        print(f"Finished processing METs data. {len(unique_met_records)} rows written to {csv_file}")
    else:
        print(f"No METs data found for the specified date range in {source_dir}")
        with open(csv_file, 'w', newline='', encoding='utf-8') as f_csv:
            writer = csv.DictWriter(f_csv, fieldnames=csv_headers)
            writer.writeheader()


# --- Main Execution ---
if __name__ == "__main__":
    if not os.path.exists(TARGET_DIR):
        os.makedirs(TARGET_DIR)
    
    process_user_biometrics()
    process_sleep_data()
    process_max_met_data()
    
    print("\\nAll processing complete.") 