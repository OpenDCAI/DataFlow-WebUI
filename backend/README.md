# 后端开发文档
## 前言
### 不熟前后端的碎碎念
后端的逻辑就是，通过HTTP请求，比如GET，POST等等网络请求，实现数据的发送和通信。实现前端界面（浏览器看到的内容）和后端平台（比如数据库和其周围逻辑代码）的通信。

后端一般传输的内容是纯字符串，经常是json构成的字典和列表；或者多媒体数据，以二进制包，以及base64构成居多。

所以就是，输一个URL，返回给你一坨数据，而我们就要实现这个逻辑。
### DataFlow后端需要做什么
前端就好像一个PPT，几乎只能承担及其基础的逻辑。所以大部分数据管理，算子管理，pipeline管理，实际的逻辑和调度都发生在后端。

前端和后端之间需要不断的通信来传输，可视化这个过程中发生的事情。**一般情况下，这些内容都是Json。**

如果用一个我们都能熟悉的东西，OpenAI的Chat completions理解会更好，这就是一个典型的后端干的事情。通过DataFlow中的`api_llm_serving_request`为例。从这个[链接](https://github.com/OpenDCAI/DataFlow/blob/4efc1643d768c12adad84ef9e2b262edc4a41b41/dataflow/serving/api_llm_serving_request.py#L77)看起。

这是一个Post请求，发送了一个这样的Payload：
```json
    {
        "model": model,
        "messages": [
            {"role": "system", "content": system_info},
            {"role": "user", "content": messages}
        ],
        "temperature": 0.0   
    }
```

然后GPT官方的后端会返回一个Response，这也是个Json，我们可以从里面拿到想要的信息。

这个流程就是典型后端的流程，所以逻辑上就是，把所有的逻辑相关的操作（比如传数据，可视化，编排算子，编排流水线），都制定一个协议，通过JSON和前端通信，供前端调用，请求和可视化。

## 教程链接
FastAPI的教程十分的详细，请参考如下链接：
[https://fastapi.tiangolo.com/zh/](https://fastapi.tiangolo.com/zh/)

一定在本地跟着写一写，很快就能理解它的模式和网络请求的实际意义，多用浏览器和自己本地部署的API访问交互。领略FastAPI是如何完成网络请求和回应，以及对于数据经过pydantic定义做检查的这套模式。

## 如何定义API
定义API就是一份需求文档，也是后续开发文档的基础。每个API的任务如下：
1. 定义api接受URL的逻辑（需要提供什么信息给后端）
2. 定义自己传输的数据的结构格式（Json长什么样子，如何能合理高效精简地给前端使用）
3. 书写具体的Python逻辑，实现该API的功能。


## API概览
### 1. 数据集管理
1. 提供目前example下所有的的数据集的概览信息：
   1. 用途：列一个数据集概览表，方便用户进一步选择想要的数据集，有一些粗略的信息。
   2. 粗略信息：
      1. 名称
      2. 数据集大小
      3. 建议pipeline名称
2. 
### DataFlow内核逻辑

### DataFlow Agent内核逻辑

