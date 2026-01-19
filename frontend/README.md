# DataFlow-WebUI

This template should help get you started developing with Vue 3 in Vite.

## Recommended IDE Setup

[VSCode](https://code.visualstudio.com/) + [Volar](https://marketplace.visualstudio.com/items?itemName=Vue.volar) (and disable Vetur).

## Customize configuration

See [Vite Configuration Reference](https://vitejs.dev/config/).

## Project Setup

```sh
yarn
```

### Compile and Hot-Reload for Development

```sh
yarn dev
```

### Compile and Minify for Production

在`.env.production`中设定`VITE_BACKEND_URL`为后端FastAPI地址.

```sh
yarn build
```

生成dist目录用于部署.

## 项目结构

```
src/
├── axios/ # 后端API调用配置
│   ├── config.js
│   └── index.js
├── components/ # 前端组件
│   ├── DataFlow.vue
│   └── ...
├── hooks/ # 前端钩子函数
│   ├── general/
│   │   └── useGlobal.js
│   └── ...
├── router/ # 前端路由配置
│   ├── index.js
│   └── ...
├── views/ # 前端视图组件
│   ├── DataFlow.vue
│   └── ...
├── App.vue # 前端入口组件
├── main.js # 前端入口文件
└── ...
```

## 配置

### 更新后端API

在`package.json`里头`scripts`设定后端Swagger API地址: "api": "api-cli get http://100.64.0.91:8000/openapi.json -d ./src/axios"

然后运行:

```sh
yarn api
```

### 配置后端API

`axios/config.js`里头设定`baseURL` (开启了反向代理, 指向`/api`路由, 一般不需要修改)

`vite.config.js`:

```javascript
server: {
        proxy: {
            '/api': {
                target: 'http://100.64.0.91:8000/', // 后端 FastAPI 地址
                changeOrigin: true,
                rewrite: path => path.replace(/^\/api/, '') // 如果后端没有 /api 前缀
            }
        }
    }
```
在这里, 我们将`/api`路由指向了`http://100.64.0.91:8000/`, 这是后端FastAPI的地址.

### 使用后端API

1. 选项式

直接在代码中通过`this.$api`调用后端API.

```javascript
export default {
    name: 'DataFlow',
    mounted() {
        this.$api.datasets.list_datasets().then((res) => {
            console.log(res)
        })
    }
}
```

2. 组合式

```javascript
import { useGlobal } from "@/hooks/general/useGlobal";
const { $api } = useGlobal();

$api.datasets.list_datasets().then((res) => {
    console.log(res)
})
```

### 全局方法

除了`$api`, 还有一些全局方法可以在前端代码中使用.

- `$api`: 后端API调用实例, 可以直接调用后端API.
- `$axios`: Axios实例, 可以直接调用Axios API.
- `$router`: 路由实例, 可以直接调用路由API.
- `$Go`: 路由跳转方法, 可以直接调用路由跳转.
- `$Back`: 路由返回方法, 可以直接调用路由返回.
- `$Jump`: 路由跳转方法, 可以直接调用路由跳转, 类似于`window.open`.

要配置更多方法, 可以在`useGlobal.js`中添加.

## 设计规范

### Flow

1. Handle

<属性名>::<出边|入边>::<边类型>

如节点边:

node::source::node

参数边:

<key_name>::source::run_key
