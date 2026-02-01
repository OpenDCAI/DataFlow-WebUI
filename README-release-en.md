# DataFlow-WebUI (Release)

## English · Quick Start

### 1. Prepare Python

* Python **3.10 / 3.11** is recommended
* Make sure `python` is available in your shell

Choose one:

**Option A: venv**

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

**Option B: conda**

```bash
conda create -n dataflow python=3.10
conda activate dataflow
```

### 2. Install backend dependencies

```bash
cd backend
pip install -r requirements.txt
cd ..
```

### 3. Run

From the **release root directory**:

```bash
./run.sh
```

Windows:

```bat
run.bat
```

Open in browser:

```
http://localhost:8000/
```
