# DataFlow-WebUI

[![](https://img.shields.io/github/repo-size/OpenDCAI/DataFlow-webui?color=green)](https://github.com/OpenDCAI/DataFlow-webui)

## Frontend Installation
1. npm installation
```shell
# github download
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
# Mirror Download (faster in China)
curl -so- https://gitee.com/mirrors/nvm/raw/v0.39.7/install.sh | bash
```
2. Refresh the terminal to activate the nvm command
```shell
# using bash
source ~/.bashrc
# using zsh
source ~/.zshrc
```
3. Install NVM 20
```shell
nvm install 20
nvm use 20
nvm alias default 20
```

4. check version

```shell
node -v
npm -v
```

## Backend Installation
1. Install DataFlow

    There are two options, First one is installing the latest DataFlow from Github
    ```shell
    git clone https://github.com/OpenDCAI/DataFlow
    cd DataFlow
    pip install -e .
    ```

    The second option is  to install the stable DataFlow from Pypi
    ```shell
    pip install open-dataflow
    ```


2. Then you need to install the actual dependency for `DataFlow-webui`
    ```shell
    pip install -r backend/requirements.txt
    ```

## Run this project
1. Frontend compilation
```shell
cd frontend/
npm i
npm run build
```
2. Backend Run
```shell
cd backend/
# If you are linux
make dev
# If you are Windows
uvicorn app.main:app --reload --port 8000  --reload-dir app --host=0.0.0.0
```

Then you can visit `http://localhost:<backend port>/ui/` for webui usage. By default, the `<backend port>` is set to 8000.

