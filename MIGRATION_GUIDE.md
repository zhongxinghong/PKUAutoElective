Migration Guide
====================

v5.0.1 -> 6.0.0
------------------
- 新的验证码识别模块依赖 opencv，安装命令 `pip3 install opencv-python`
- 新的验证码识别模块不再依赖于 joblib，并删除了对 simplejson 的可选依赖
- PyTorch 版本需保证大于 1.4.x，否则无法读取 CNN 模型

v3.0.8 -> 5.0.1
------------------
- `config.ini` 中添加 `elective_client_max_life` 用于设置 elective 客户端的存活时间，到期后 elective 会话会被主动关闭
- `config.ini` 中添加 `print_mutex_rules` 选项，可以选择是否打印完整的互斥规则列表

v3.0.6 -> 3.0.8
------------------
- 添加了 [Issue #28](https://github.com/zhongxinghong/PKUAutoElective/issues/28) 所提的建议，引入了延迟规则的定义，如果你需要使用，请注意 [README.md](/README.md) 中 [延迟规则](/README.md#延迟规则) 小节


v3.0.5 -> 3.0.6
------------------
- 修复了 [Issue #25](https://github.com/zhongxinghong/PKUAutoElective/issues/25) 所提的 bug，如果你在使用互斥规则，请你注意下 [README.md](/README.md) 中 [互斥规则](/README.md#互斥规则) 小节的更新


v3.0.3 -> 3.0.5
------------------
- 现在定义在 `config.ini` 中的课程将会像原来那样保持其在文件中的先后顺序，相应的选课优先级按从上到下的顺序从高到低排


v3.0.1 beta -> v3.0.3
------------------
- 旧版本的 iaaa 和 elective 的部分 API 已经失效，请赶紧更新到最新 v3.0.3 及以上版本，旧版本将不再维护


v2.1.0 -> v3.0.1 beta
------------------
- 不再使用 `course.csv` 定义课程列表，而是合并到 `config.ini` 中，因此需要仔细查看手册的 [基本用法](/README.md#基本用法) 一节，以明确新的课程定义方法。最好对 `config.ini` 进行完全重写
- 修改了 `config.ini` 中 `student_ID` 键名为 `student_id`
- 新引入了自定义选课规则的功能，更多请查看手册的 [基本用法](/README.md#基本用法) 一节
- 修改了监视器路由，详细查看手册的 [监视器](/README.md#监视器) 一节
- 更多改动细节请查看 [HISTORY.md](/HISTORY.md) 并重新阅读手册 [README.md](/README.md)

#### Development Related
- 这版在诸多方面均有较大改动，详细请查看 [HISTORY.md](/HISTORY.md)
- 这版开始我不打算再提供项目的架构细节说明，如果你需要了解项目的实现细节，可以自行阅读源码


v2.0.9 -> v2.1.0
------------------

#### Development Related
- Windows 在创建多进程时只能采用 `spawn` 方法，子进程创建后并不直接共享父进程已经设置好的的用户配置项，因此还需要将用户配置项 `userInfo` 在进程中共享。但是 `userInfo` 直接影响着最基本的 `config.py` ，为了让用户自定义配置 `userInfo` 能够在子进程中被正确应用，`userInfo` 的更新至子线程 `_internal.py` 和 `config` 单例的第一次初始化必须早于任何依赖于 `config` 单例的方法的调用。
- 因此，这一版中对包调用的逻辑进行了大幅度的修改，删减了大部分包的在导入时即创建 `_config` 全局变量的逻辑，改成将 `config` 变量在函数使用时才创建，并且将 `loop.py` 和 `monitor.py` 中的所有全局变量和全局函数声明为局部
- 个人觉得这个改动很丑陋，但是由于我的开发经验有限，一时想不到其他的写法，如果你对这个问题有更好的解决方法，欢迎发 Issue ！
- 个人的一个改进想法是把多进程全部换成多线程，这样就不需要考虑资源共享的问题


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
