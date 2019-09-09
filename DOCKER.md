# PKUAutoElective Docker Image

依赖于原项目v2.0.2(2019.09.09)版本。

## Tags

1. latest
2. monitor

## latest

包含python3，依赖库，以及项目源代码。

### 运行方法

``` bash
docker run -d \
           --name=pae \
           -v /path/to/config/folder:/config \
           yousiki/pkuautoelective:latest   # 运行工具
docker logs pae # 查看输出
docker stop pae # 停止工具
```

## monitor

额外包含Monitor运行依赖的库。

### 运行方法

`config.ini`中的`host`值建议设为`0.0.0.0`

``` bash
docker run -d \
           --name=pae \
           -p 7074:7074 \
           -v /path/to/config/folder:/config \
           yousiki/pkuautoelective:latest   # 运行工具
docker logs pae # 查看输出
docker stop pae # 停止工具
```