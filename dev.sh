#! /bin/bash

yellow='\033[0;33m'
green='\033[0;32m'
clear='\033[0m'

echo -e "${yellow}Starting development environment with Docker Watch...${clear}"
echo -e "${green}Frontend: http://localhost:3000  |  Backend: http://localhost:4000${clear}"
echo ""
echo "Source changes in frontend/src/ sync instantly (no rebuild)."
echo "package.json / config changes trigger an image rebuild."
echo ""

docker compose -f compose.yml -f compose.dev.yml watch
