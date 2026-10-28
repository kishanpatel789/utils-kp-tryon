#!/usr/bin/env sh

[ -z $1 ] && { echo "Error: Don't forget to include the model name as an argument"; exit 1; }

manifest_path="$HOME/code/tryon-datalake/tryon_dbt/target/manifest.json"
target_path="model.tryon_dbt.$1"

jq --arg target_path "$target_path" '.parent_map | with_entries(select(.key == $target_path))' $manifest_path
