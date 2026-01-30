# DataFlow-WebUI

[![](https://img.shields.io/github/repo-size/OpenDCAI/DataFlow-webui?color=green)](https://github.com/OpenDCAI/DataFlow-webui)

## Frontend Installation
1. NVM(Node Version Manager) installation
```shell
# github download
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
# Mirror Download (faster in China)
curl -so- https://gitee.com/mirrors/nvm/raw/v0.39.7/install.sh | bash
```
2. Refresh the terminal to activate the NVM command
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

4. check version for node and NPM, node should be version `v20.x.x`
```shell
node -v
npm -v
```

5. Build the frontend, after this, the built frontend page files will appear under `frontend/dist`.
```shell
cd frontend/
npm i
npm run build
```

## Backend Installation
1. Install [DataFlow](https://github.com/OpenDCAI/DataFlow)

    There are two options. The first one is installing the latest DataFlow from GitHub
    ```shell
    git clone https://github.com/OpenDCAI/DataFlow
    cd DataFlow
    pip install -e .
    ```

    The second option is  to install the stable DataFlow from PyPI
    ```shell
    pip install open-dataflow
    ```


2. Then you need to install the actual dependency for `DataFlow-webui`.
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
# If you are using Linux
make dev
# If you are using Windows
uvicorn app.main:app --reload --port 8000  --reload-dir app --host=0.0.0.0
```

Then you can visit `http://localhost:<backend port>/` to use the DataFlow-webUI. By default, the `<backend port>` is set to 8000.

