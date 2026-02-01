<p align="center">
  <img src="src/assets/logo/logo.png" alt="Dataflow" width="120px"/>
</p>

# DataFlow WebUI

中文版本：[README_zh.md](docs/README_zh.md)

This is the **frontend interface** of DataFlow, built with **Vue 3 + Vite**.
If you are not familiar with frontend development — no worries. Just follow the steps below **in order**.

---

# 🧠 What You Are Setting Up (Big Picture)

You are installing:

| Tool        | What it does            | Why you need it               |
| ----------- | ----------------------- | ----------------------------- |
| **Node.js** | Runs JavaScript tools   | Required to build the project |
| **NVM**     | Manages Node versions   | Ensures correct Node version  |
| **Yarn**    | Package manager         | Installs project dependencies |
| **Vite**    | Dev server & build tool | Runs the frontend locally     |

---

# 🖥 0. Recommended Editor (Optional but helpful)

Install:

* **VS Code**: [https://code.visualstudio.com/](https://code.visualstudio.com/)
* **Volar extension** (Vue support)
* Disable **Vetur** if installed

---

# 🧩 1. Install NVM (Node Version Manager)

NVM lets you install the correct Node version easily.

### Mac / Linux

```bash
# Official
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash

# Faster mirror in China
curl -so- https://gitee.com/mirrors/nvm/raw/v0.39.7/install.sh | bash
```

### Then refresh terminal

```bash
# bash
source ~/.bashrc

# zsh
source ~/.zshrc
```

---

# 🟢 2. Install Node.js (Version 20)

```bash
nvm install 20
nvm use 20
nvm alias default 20
```

Check installation:

```bash
node -v   # should show v20.x.x
npm -v
```

---

# 📦 3. Install Yarn

Yarn installs all project packages.

```bash
corepack enable
corepack prepare yarn@stable --activate
yarn -v
```

---

# 📥 4. Download Project & Install Dependencies

Go to the project folder:

```bash
cd DataFlow-WebUI/frontend
```

Install everything the project needs:

```bash
yarn
```

*(This may take a few minutes the first time.)*

---

# 🔌 5. Connect to the Backend API

The frontend talks to a backend server (FastAPI).

Open:

```
vite.config.js
```

Find this section:

```js
server: {
    host: '0.0.0.0',
    proxy: {
        '/api': {
            target: 'http://100.64.0.91:8000/', // Backend address
            changeOrigin: true,
            rewrite: path => path.replace(/^\/api/, '')
        }
    }
}
```

🔁 **Replace the IP address** with your backend server address if different.

---

# ▶️ 6. Start Development Server

Run:

```bash
yarn dev
```

You should see something like:

```
Local: http://localhost:5173/
```

Open that link in your browser 🎉

The page will auto-reload when you change code.

---

# 🏗 7. Build for Production (Deployment)

When you want to deploy:

### Step 1: Set backend URL

In `.env.production`:

```
VITE_BACKEND_URL=http://your-backend-address:8000
```

### Step 2: Build

```bash
yarn build
```

A `dist/` folder will be generated.
This folder is what you deploy to a server.

---

# 📂 Project Structure (Simplified)

```
src/
├── axios/        → API request setup
├── components/   → Reusable UI components
├── views/        → Page-level components
├── router/       → Page routing
├── hooks/        → Shared logic
├── App.vue       → Root component
└── main.js       → App entry point
```

---

# 🔄 Update Backend API Automatically

If backend API changes:

In `package.json`:

```json
"api": "api-cli get http://100.64.0.91:8000/openapi.json -d ./src/axios"
```

Run:

```bash
yarn api
```

This regenerates API request code.

---

# 📡 How Frontend Calls Backend API

### Option 1 — In Vue Options API

```js
mounted() {
    this.$api.datasets.list_datasets().then(res => {
        console.log(res)
    })
}
```

### Option 2 — In Vue Composition API

```js
import { useGlobal } from "@/hooks/general/useGlobal";
const { $api } = useGlobal();

$api.datasets.list_datasets().then(res => {
    console.log(res)
});
```

---

# 🧰 Global Utilities Available

| Name      | Function          |
| --------- | ----------------- |
| `$api`    | Backend API calls |
| `$axios`  | Axios instance    |
| `$router` | Vue router        |
| `$Go`     | Navigate to page  |
| `$Back`   | Go back           |
| `$Jump`   | Open new page     |

---

# 🎨 Flow Design Rule

Edge format:

```
<property>::<source|target>::<edge_type>
```

Examples:

```
node::source::node
key_name::source::run_key
```

---

# ✅ If Something Doesn’t Work

Check:

1. Node version = **v20**
2. Backend server is running
3. IP address in `vite.config.js` is correct
4. Re-run:

```bash
rm -rf node_modules
yarn
```

## 🔹 UI Component Library

**English**

This project uses **VFluent3**, a Vue 3 component library inspired by Microsoft’s Fluent Design. It provides a set of clean, consistent, and practical UI components that fit well with modern Vue + Vite workflows.

GitHub: [https://github.com/Creator-SN/VFluent3](https://github.com/Creator-SN/VFluent3)
