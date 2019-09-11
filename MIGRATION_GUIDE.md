Migration Guide
====================

v2.0.6 -> v2.0.7
------------------
- monitor 进程中 `/loop` 路由细分为 `/main_loop` 和 `/login_loop` 两个路由
- monitor 进程中 `/all` 路由添加了与错误捕获记录相关的键
- monitor 进程中添加了 `/errors` 路由

#### Development Related
- 进程共享的 status 对象中的 `loop` 项细分为了 `main_loop` 和 `login_loop` 两个值，并添加了与错误捕获记录相关的键


v2.0.4 -> v2.0.5
------------------

#### Development Related

- 修改了错误类 `IAAANotSuccessError` 的全局错误码

v2.0.3 -> v2.0.4
------------------
- `config.ini` 内添加了 elective 多会话相关的配置
- `config.ini` 内删除了 `iaaa_relogin_interval` 字段

#### Development Related

- 为了应对选课网偶发的会话过期问题，为 elective 客户端引入了多会话机制，并删除了旧有的定时重登机制。具体见 README 中的 [运行流程](/README.md#运行流程) 小节

v2.0.1 -> v2.0.2
------------------
- `config.ini` 内添加了 `client/supply_cancel_page` 值，以支持不处于选课计划第一页的课程

v1.0.4 -> v2.0.1
------------------
- 新版对 `config.ini` 内的绝大多数配置项名称做了修改，需要用新提供 `config.sample.ini` 重新填写一遍配置
- 添加了自定义 `config.ini` 和 `course.csv`
- 添加了对 `Flask` 库的依赖，对于尚未安装该依赖的环境，还需额外运行 `pip3 install flask`

#### For 'git pull' Comment

如果你使用了 `git` 命令更新该项目，在输入 `git pull origin master` 后，可能会报错 `error: Your local changes to the following files would be overwritten by merge:` ，这是因为新版删除了 `config.ini` 和 `course.*.csv` 文件，而改用 `config.sample.ini` 和 `course.*.sample.csv` 代替。只需要输入以下命令即可消除冲突：

在项目根目录下：
```console
$ git checkout config.ini
$ git checkout course.utf-8.csv
$ git checkout course.gbk.csv
```

#### Development Related

- 在 `BaseClient` 内添加了 `persist_cookies` 方法，会在 `hooks.py` 内被调用，以确保在一些特定的错误下仍然可以保持会话
- 在 `elective.py` 的 `sso_login` 的请求头中添加了一个固定的无效 `Cookie` 以防止登录时报 `101` 状态码
- 修改了 `IAAA` 的重新登录逻辑，由原来的遇到错误重登，变为每隔一段时间重登
- 在 `loop.py` 中对 `elective.py` 的 `get_Validate` 方法的调用结果添加了一层错误捕获，以应对非 JSON 格式的响应体
