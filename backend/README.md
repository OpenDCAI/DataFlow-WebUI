# 后端开发文档
## 启动
启动服务器
```bash
# 如果系统上有make
make dev

# 如果是windows，可以尝试自己安装make，也可以直接执行这个指令：
uvicorn app.main:app --reload --port 8000  --reload-dir app --host=0.0.0.0
```

启动API Swagger文档
```bash
# 如果系统上有make
make doc
```
如果是其他系统，直接打开如下如下地址即可：
http://0.0.0.0:8000/docs