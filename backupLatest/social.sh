#!/bin/bash

# Initialize previous hour and minute to a default value
previous_hour=$(date +'%H')
previous_minute=$(date +'%M')

log_file="/home/fedora/log/social_$(date +%Y%m%d).log"

while true; do
  # Get the current hour and minute
  current_hour=$(date +'%H')
  current_minute=$(date +'%M')

  # Convert current and previous times to minutes since midnight
  current_time_in_minutes=$((10#$current_hour * 60 + 10#$current_minute))
  previous_time_in_minutes=$((10#$previous_hour * 60 + 10#$previous_minute))

  # Times to trigger the script (in minutes since midnight)
  target_times=(420 660 840 )  # 08:30 -510, 11:30, 14:30, 17:30, 20:30 - 1230 , 23:30 - 1410

  log_entry="Checking time: $(date +'%Y-%m-%d %H:%M:%S')"
  
  # Log the time of the check
  echo "$log_entry" >> "$log_file"

  triggered=false

  for target_time in "${target_times[@]}"; do
    if [[ "$previous_time_in_minutes" -lt "$target_time" && "$current_time_in_minutes" -ge "$target_time" ]]; then
      # Log that the time has triggered
      echo "Trigger time reached: $(date +'%Y-%m-%d %H:%M:%S') - Executing scripts" >> "$log_file"
      
      # Run the scripts
      /usr/bin/python3 /home/fedora/jobs/socialmediadata/MainScriptXfeed.py >> "$log_file" 2>/dev/null
      sleep 60
      /usr/bin/python3 /home/fedora/jobs/socialmediadata/MainapifyFacebook.py >> "$log_file" 2>/dev/null
      sleep 60
      /usr/bin/python3 /home/fedora/jobs/socialmediadata/MainScriptYoutubeAll.py >> "$log_file" 2>/dev/null
      sleep 60
      /usr/bin/python3 /home/fedora/jobs/socialmediadata/MainScriptyoutube.py >> "$log_file" 2>/dev/null
      sleep 60
      /usr/bin/python3 /home/fedora/jobs/socialmediadata/mongodbtocollectionpnqxfeed.py >> "$log_file" 2>/dev/null
      sleep 60
      /usr/bin/python3 /home/fedora/jobs/socialmediadata/mongodbtocollectionpnqyoutube.py >> "$log_file" 2>/dev/null
      sleep 60
      /usr/bin/python3 /home/fedora/jobs/socialmediadata/facebookdatatomongo.py >> "$log_file" 2>/dev/null
      
      triggered=true
      break
    fi
  done

  if [[ "$triggered" == "false" ]]; then
    echo "No trigger time reached: $(date +'%Y-%m-%d %H:%M:%S')" >> "$log_file"
  fi

  # Update the previous time
  previous_hour=$current_hour
  previous_minute=$current_minute

  # Wait for 900 seconds (15 minutes) before checking the time again
  sleep 900
done
