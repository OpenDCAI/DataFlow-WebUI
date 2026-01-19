# DataFlow-WebUI

## Installation
1. npm installation
```
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
# bash
source ~/.bashrc

# zsh
# source ~/.zshrc
nvm install 20
nvm use 20
nvm alias default 20
# check version
node -v
npm -v
```
2. Python dependency installtion
```
# maybe conda scripts...
# Please install DataFlow(https://github.com/OpenDCAI/DataFlow) first, and then
pip install -r /backend/requirements.txt
```

## Quick Start

1. Frontend compilation
```
cd frontend/
npm i
npm run build
```
2. Backend Run
```
cd backend/
make dev
```

Then you can visit `http://localhost:<backend port>/ui/` for webui usage.

