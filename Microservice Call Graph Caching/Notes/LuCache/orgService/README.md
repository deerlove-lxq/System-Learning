# 微服务模拟
## 组件说明
1. 数据库以database.json代替，只包含一个键值对{"school": "hust"}
2. 整体包含4个服务：frontend, caller_read, caller_write, callee(直接对数据库进行读写)
3. 每个服务对应一个端口号，以http post/get进行服务间通信
4. 信息（如端口号、upstream cm等）以硬编码的形式写入代码
5. Services
   - frontend
      - frontend_read
      - frontend_write
   - caller_read
      - caller_read(k)
   - caller_write
      - caller_write(k, v)
   - callee
      - read(k)
      - write(k, v)
6. 微服务架构示意图

![](.\data\LuCache-模拟微服务架构.png)

## 使用方法
1. 在4个不同终端分别运行frontend.py, caller_read.py, caller_write.py, callee.py
2. 新建1个终端作为控制台，运行menu.py
3. 在menu.py中选择具体的调用方式
## LuCache验证思路
1. 可选择仅在部分service上部署LuCache Protocol（验证：部分部署、使用cache的优越性）
2. 先使用caller_write修改数据库中的键值对，再查看caller_read和frontend的cache是否被更新（验证：CM间通信、缓存一致性）
3. 开启两个线程，分别执行read和write并打印函数运行结束时间和结果（验证：线性存储）
4. 避免请求关键路径上的所有阻塞通信--允许向下游写入，而不会立即通知上游缓存，也不会阻塞读取。（验证：无阻塞）