# README

## 项目结构

```
-- LuCache/										根目录
|-- orgService/									不包含Cache的微服务模拟系统
|-- exService/									部署了LuCache Protocol的微服务模拟系统（核心）
|   |-- README.md								项目设计说明
|   |-- main.py									主函数
|   |-- menu.py									菜单
|   |-- utils.py								包含一些自定义的数据结构
|   |-- data/                           		
|       |-- database.json                     	模拟数据库
|       |-- caller_read.json                    模拟caller_read的Cache
|       |-- frontend.json                   	模拟frontend的Cache
|       |-- *.png                   			图片展示
```

## MuCache Summary

- Key ideas
  - Non-blocking（TODO：requests async）
  - Provable correctness
  - Dynamic graphs
  - Linearizable datastores
- Key components
  - Cache
  - State
  - Context
  - Wrapper
  - Cache Manager