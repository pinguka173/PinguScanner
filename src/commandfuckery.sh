#!/bin/bash

if [[ "$1" == "-h" || "$1" == "--help" ]]; then
  echo
  echo "Usage: $0 -s <target> -p <preset> [-to <timeout>]"
  echo "Example: $0 -s scanme.nmap.org -p web -to 20"
  echo
  echo "Use $0 --commands for commands list"
  echo
  exit 0
fi

if [[ "$1" == "-c" || "$1" == "--commands" ]]; then
  echo
  echo "--help                     |       Displays basic information about the program"
  echo "--commands                 |       Displays all available commands and usage"
  echo "--presets                  |       Displays all available presets"
  echo "--presets-details {preset} |       Displays the given preset's content"
  echo "--update                   |       Updates to the newest version"
  echo "-V, --version              |       Displays current version"
  echo "-s {target}                |       Sets a target IP/Domain for the scan"
  echo "-p {preset}                |       Sets a port preset"
  echo "-t {value}                 |       Sets a timeout for the scan"
  echo
  exit 0
fi

if [[ "$1" == "--presets" ]]; then
  echo
  echo "Available presets:"
  jq -r 'keys[]' presets/port_presets.json
  exit 0
fi

if [[ "$1" == "--presets-details" ]]; then
  echo
  if [[ -z "$2" ]]; then
    echo "Presets and their ports:"
    jq -r 'to_entries[] | "\(.key): \(.value | join(\", \"))"' presets/port_presets.json
  else
    preset_ports=$(jq -r --arg name "$2" '.[$name] // empty | join(", ")' presets/port_presets.json)
    if [[ -z "$preset_ports" ]]; then
      echo "No such preset: $2"
      exit 1
    fi
    echo "$2: $preset_ports"
  fi
  exit 0
fi

if [[ "$1" == "-V" || "$1" == "--version" ]]; then
  echo
  echo "PinguScan/v1.2.0"
  echo
fi

if [[ "$1" == "-s" && "$2" == "--help" ]]; then
  echo
  echo "Usage:"
  echo "  $0 -s {target}             # Set a target for the scan"
  echo
  echo "Examples:"
  echo "  $0 -s scanme.nmap.org -p web"
  echo "      ^ Set \"scanme.nmap.org\" as a target"
  echo
  echo " $0 -s http://scanme.nmap.org/ -p web"
  echo "     ^ You can have prefix and suffix."
  exit 0
fi

if [[ "$1" == "-p" && "$2" == "--help" ]]; then
  echo
  echo "Usage:"
  echo "  $0 -p {preset}           # Use an existing port preset"
  echo "  $0 -p create {name} {ports...}   # Create your own preset"
  echo
  echo "Examples:"
  echo "  $0 -s scanme.nmap.org -p web"
  echo "      ^ Scans using the 'web' preset (HTTP, HTTPS, etc.)"
  echo
  echo "  $0 -p create test 20 21 22 80 443"
  echo "      ^ Makes a new preset called 'test' with those ports"
  echo
  echo "NOTE: Ports must be space-separated."
  exit 0
fi

if [[ "$1" == "-p" && "$2" == "create" ]]; then
  PRESET_NAME="$3"
  PRESET_FILE="presets/port_presets.json"
  shift 3
  PORTS=("$@")
  if [[ -z "$PRESET_NAME" ]]; then
    echo "No preset name provided"
    exit 1
  fi
  if [[ "${#PORTS[@]}" -eq 0 ]]; then
    echo "No ports specified"
    exit 1
  fi
  if jq -e --arg name "$PRESET_NAME" '.[$name]' "$PRESET_FILE" > /dev/null; then
    echo "Preset '$PRESET_NAME' already exists. Overwrite? [y/N]"
    read -r confirm
    [[ "$confirm" =~ ^[Yy]$ ]] || exit 1
  fi
  for port in "${PORTS[@]}"; do
    if ! [[ "$port" =~ ^[0-9]+$ ]]; then
      echo "Invalid port: $port"
      exit 1
    fi
  done
  if [[ ! -f "$PRESET_FILE" ]]; then
    echo "{}" > "$PRESET_FILE"
  fi
  tmp=$(mktemp)
  jq --arg name "$PRESET_NAME" --argjson ports "$(printf '%s\n' "${PORTS[@]}" | jq -R . | jq -s .)" '. + {($name): $ports}' "$PRESET_FILE" > "$tmp" && mv "$tmp" "$PRESET_FILE"
  echo "Preset '$PRESET_NAME' created with ports: ${PORTS[*]}"
  exit 0
fi

if [[ "$1" == "-t" && "$2" == "--help" ]]; then
  echo
  echo "Usage:"
  echo "  $0 -t {value}           # Set a timeout in seconds"
  echo
  echo "Examples:"
  echo "  $0 -s scanme.nmap.org -p web -to 20"
  echo "                                ^ Sets a timeout for 20 seconds"
  echo
  echo "NOTE: Setting a timeout is optional, but highly recommended."
  exit 0
fi

ip=""
selected_port_preset=""
set_timeout=""

#!/bin/bash

while getopts s:p:t:j: flag
do
    case "${flag}" in
        s) target=${OPTARG};;
        p) preset=${OPTARG};;
        t) timeout=${OPTARG};;
        j) json=${OPTARG};;
    esac
done

CMD="python3 main.py -s $target -p $preset"

if [ ! -z "$timeout" ]; then
    CMD="$CMD -t $timeout"
fi

if [ ! -z "$json" ]; then
    CMD="$CMD --presets $json"
fi

eval $CMD

echo "Target: $ip"
echo "Port preset: $selected_port_preset"

export ip
export selected_port_preset
export set_timeout

source commandfuckery.sh
python3 main.py