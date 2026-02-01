# DataFlow-WebUI

[![](https://img.shields.io/github/repo-size/OpenDCAI/DataFlow-webui?color=green)](https://github.com/OpenDCAI/DataFlow-webui)

**DataFlow-WebUI** is a full-stack open-source web application that provides a graphical interface for the [DataFlow](https://github.com/OpenDCAI/DataFlow) framework. This guide walks you through setting up both the frontend and backend so you can quickly get up and running.

---

## Prerequisites

Before you begin, make sure you have:

* **Python 3.10+**
* **pip**
* **Git**
* A Unix-like shell (Linux/macOS) or PowerShell / CMD (Windows)

---

## Clone This Repository

First, clone the **DataFlow-WebUI** repository and enter the project directory:

```shell
git clone https://github.com/OpenDCAI/DataFlow-WebUI.git
cd DataFlow-WebUI
```

---

## Frontend Installation

The frontend is built with Node.js. We recommend using **NVM (Node Version Manager)** to manage your Node.js version.

### 1. Install NVM

```shell
# Download from GitHub
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash

# Mirror download (recommended if you are in China)
curl -so- https://gitee.com/mirrors/nvm/raw/v0.39.7/install.sh | bash
```

### 2. Reload your shell configuration

After installing NVM, restart your terminal or run one of the following commands:

```shell
# For bash
source ~/.bashrc

# For zsh
source ~/.zshrc
```

### 3. Install and use Node.js 20

```shell
nvm install 20
nvm use 20
nvm alias default 20
```

### 4. Verify Node.js and npm versions

Ensure that Node.js is version `v20.x.x`:

```shell
node -v
npm -v
```

---

## Backend Installation

The backend is powered by **DataFlow** and FastAPI.

### 1. Install DataFlow

You can install DataFlow in **one of two ways**:

#### Option A: Install the latest development version from GitHub

```shell
git clone https://github.com/OpenDCAI/DataFlow
cd DataFlow
pip install -e .
```

#### Option B: Install the stable release from PyPI (recommended for most users)

```shell
pip install open-dataflow
```

### 2. Install backend dependencies for DataFlow-WebUI

From the project root directory, run:

```shell
pip install -r backend/requirements.txt
```

---

## Running the Project

### 1. Build the frontend

```shell
cd frontend/
npm install
npm run build
```

This will generate the production-ready frontend assets.

### 2. Start the backend server

```shell
cd backend/
```

* **On Linux / macOS:**

```shell
make dev
```

* **On Windows:**

```shell
uvicorn app.main:app --reload --port 8000 --reload-dir app --host 0.0.0.0
```

---

## Access the Web UI

Once the backend is running, open your browser and visit:

```
http://localhost:8000/
```

> 💡 If you changed the backend port, replace `8000` with your custom port.

---

## 🎉 You’re All Set!

You should now have the full DataFlow-WebUI stack running locally. If you encounter issues, double-check your Node.js and Python versions, and feel free to open an issue on GitHub.

Happy hacking! 🚀


## Citation

If you use DataFlow in your research, feel free to give us a cite.

```bibtex
@article{liang2025dataflow,
  title={DataFlow: An LLM-Driven Framework for Unified Data Preparation and Workflow Automation in the Era of Data-Centric AI},
  author={Liang, Hao and Ma, Xiaochen and Liu, Zhou and Wong, Zhen Hao and Zhao, Zhengyang and Meng, Zimo and He, Runming and Shen, Chengyu and Cai, Qifeng and Han, Zhaoyang and others},
  journal={arXiv preprint arXiv:2512.16676},
  year={2025}
}
```
