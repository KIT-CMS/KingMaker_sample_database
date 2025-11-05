# Get all nicks and cross sections in Moritz' and Sofia's databases

xsecs_moritz_json=$(git show nanoAOD_v15:nanoAOD_v12/datasets.json | jq -r ' to_entries | map(select(.value.era == "2022preEE") | {(.key): {"xsec_moritz": .value.xsec}}) | add ')
xsecs_sofia_json=$(git show nanoAOD_v15:nanoAOD_v12/datasets.json | jq -r ' to_entries | map(select(.value.era == "2023preBPix") | {(.key): {"xsec_sofia": .value.xsec}}) | add ')
xsecs_merged=$(jq -s -r ' .[0] * .[1] ' <(cat <<< "${xsecs_moritz_json}") <(cat <<< "${xsecs_sofia_json}"))
xsecs_both=$(jq -r ' to_entries | map(select((.value | has("xsec_moritz")) and (.value | has("xsec_sofia"))) | {(.key): .value}) | add ' <(cat <<< "${xsecs_merged}"))
echo "${xsecs_both}" > "compare_xsecs_sofia_moritz.txt"