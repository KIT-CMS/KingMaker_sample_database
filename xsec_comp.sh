# Get all nicks and cross sections in Moritz' and Sofia's databases

# Debug: Print the JSON data fetched for Moritz
xsecs_moritz_json=$(git show nanoAOD_v15:nanoAOD_v12/datasets.json | jq -r ' to_entries | map(select(.value.era == "2022preEE") | {(.key | split("13p6TeV")[0] + "13p6TeV"): {"xsec_moritz": .value.xsec}}) | add ')
#echo "Moritz JSON Data: ${xsecs_moritz_json}"

# Debug: Print the JSON data fetched for Sofia
xsecs_sofia_json=$(git show nanoAOD_v15:nanoAOD_v15/datasets.json | jq -r ' to_entries | map(select(.value.era == "2024") | {(.key | gsub("_MLL"; "_Bin-MLL") | split("13p6TeV")[0] + "13p6TeV"): {"xsec_sofia": .value.xsec}}) | add ')
#echo "Sofia JSON Data: ${xsecs_sofia_json}"

# Debug: Print the merged JSON data
xsecs_merged=$(jq -s -r ' .[0] * .[1] ' <(cat <<< "${xsecs_moritz_json}") <(cat <<< "${xsecs_sofia_json}"))
#echo "Merged JSON Data: ${xsecs_merged}"

# Debug: Print the keys in the merged JSON data
jq 'keys' <(cat <<< "${xsecs_merged}")

# Debug: Print the structure of the merged JSON data
jq '.' <(cat <<< "${xsecs_merged}")

# Filter the merged JSON data to include only entries with differing xsec values
xsecs_both=$(jq -r ' to_entries | map(select((.value | has("xsec_moritz")) and (.value | has("xsec_sofia")) and (.value.xsec_moritz != .value.xsec_sofia)) | {(.key): .value}) | add ' <(cat <<< "${xsecs_merged}"))

# Debug: Print the filtered JSON data
echo "Filtered JSON Data (Differing xsec values): ${xsecs_both}"

# Debug: Validate the structure of Moritz JSON data
jq . <(cat <<< "${xsecs_moritz_json}") > /dev/null 2>&1
if [ $? -ne 0 ]; then
  echo "Error: Moritz JSON data is not valid JSON."
  exit 1
fi

# Debug: Validate the structure of Sofia JSON data
jq . <(cat <<< "${xsecs_sofia_json}") > /dev/null 2>&1
if [ $? -ne 0 ]; then
  echo "Error: Sofia JSON data is not valid JSON."
  exit 1
fi

# Debug: Validate the structure of merged JSON data
jq . <(cat <<< "${xsecs_merged}") > /dev/null 2>&1
if [ $? -ne 0 ]; then
  echo "Error: Merged JSON data is not valid JSON."
  exit 1
fi

# Debug: Validate the structure of filtered JSON data
jq . <(cat <<< "${xsecs_both}") > /dev/null 2>&1
if [ $? -ne 0 ]; then
  echo "Error: Filtered JSON data is not valid JSON."
  exit 1
fi

echo "${xsecs_both}" > "compare_xsecs_sofia_moritz.txt"