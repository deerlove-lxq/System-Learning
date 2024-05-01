# LuCache
## 模拟说明

1. 数据库以database.json代替，只包含一个键值对{"school": "hust"}
2. 缓存以frontend.json/caller_read.json分别代替，结构为：{key: {'value': value, 'visited': visited_list}}
3. 整体包含4个服务：frontend, caller_read, caller_write, callee(直接对数据库进行读写)
4. frontend, caller_read两个服务部署Cache，所有服务部署CacheManager
5. 基于flask框架，每个服务对应一个端口号，所有通信使用http get通信
6. Services
   - frontend
      - read_from_caller
      - write_to_caller
   - caller_read
      - call_read(k)
   - caller_write
      - call_write(k, v)
   - callee
      - read(k)
      - write(k, v)
7. 微服务架构示意图

![](.\data\LuCache-模拟微服务架构.png)

## 使用方法

运行main.py，根据命令行菜单的提示进行操作

## LuCache验证思路
1. 可选择仅在部分service上部署LuCache Protocol（验证：部分部署、使用cache的优越性）
2. 实现正常的cache缓存，复现cache hit/miss（验证：CM间通信、缓存一致性）
3. 开启两个线程，分别执行caller read和write并打印函数运行结束时间和read的结果（验证：线性存储）
4. 避免请求关键路径上的所有阻塞通信--允许向下游写入，而不会立即通知上游缓存，也不会阻塞读取。（验证：无阻塞）

**重点：**

- 为了体现离线管理缓存一致性，需要强调将Cache Manager与service分离，service不在关键步骤中等待请求执行。
- wrapper将任务请求发送至work queue中，CacheManager不断地从该全局队列中顺序取出指定给自己执行的任务，然后对cache/database进行读写操作。

## TestCases
### Test1
Enter your choice: 4
Enter the key: school
Enter the value: pku
Enter your choice: 1 
Enter the key: school   -> miss all
Enter your choice: 1 
Enter the key: school   -> hit all
Enter your choice: 3 
Enter the key: school   -> miss frontend, hit caller_read
Enter your choice: 3 
Enter the key: school   -> hit all
### Test2
Enter your choice: 4
Enter the key: school
Enter the value: pku
Enter your choice: 3 
Enter the key: school   -> miss all
Enter your choice: 1 
Enter the key: school   -> hit all
Enter your choice: 3 
Enter the key: school   -> hit all

### Test3(Linearizable Proof)

```python
    #验证线性存储的特征：比较read和write的完成次序，输出read返回的数据
    with open("./data/database.json", "w") as f:
        json.dump({"school": "pku"}, f)
    rt = threading.Thread(target=caller_read, args=('school',))
    wt = threading.Thread(target=caller_write, args=('school', 'hust'))
    rt.start()
    wt.start()
    rt.join()
    wt.join()
```

![](.\data\线性说明1.png)

![](.\data\线性说明2.png)

**根据图中的结果，可以发现只要写操作在读操作之前完成了，最终的结果一定会反映出写的效果。**
