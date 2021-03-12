Release History
===============

v6.0.0 (2021-03-12)
-------------------
- 实现了对选课网新验证码的识别
- 更新了对选课网部分 API 的请求方法 (get_supplement, get_Validate)
- 修复了无法获取到位于补退选列表第一页之后课程的问题，详见 [Issue #54](https://github.com/zhongxinghong/PKUAutoElective/issues/54), [Issue #55](https://github.com/zhongxinghong/PKUAutoElective/issues/55)
- 修复了无法正确捕获会话超时的错误信息导致一直报错 UnexceptedHTMLFormat 的问题，详见 [Issue #56](https://github.com/zhongxinghong/PKUAutoElective/issues/56)
- 修复了无法正确识别补选课程成功时所返回的提示信息的问题


v5.0.1 (2020-09-25)
-------------------
- User-Agent 池的大小扩充至 6000+
- sso_login 时将使用随机生成的 dummy cookie
- 删除所有 `Sec-Fetch-*` 请求头
- 现在 elective 客户端可以设置存活时间，到期后 elective 会话将自动登出，以期解决 [Issue #47](https://github.com/zhongxinghong/PKUAutoElective/issues/47)
- 每次重新登录 elective 时都将更换 User-Agent
- 现在可以选择是否打印完整的互斥规则列表
- 修正了配置文件和用户手册中关于 `supply_cancel_page` 选项的说明
- 修改配置文件中 `elective_client_pool_size` 选项的默认值为 `2`
- 程序启动时将首先打印重要的配置信息
- 对 elective 可能返回的错误页面加以捕获，以期解决 [Issue #44](https://github.com/zhongxinghong/PKUAutoElective/issues/44)
- 修改 sso_login 接口的参数名 `rand` 为 `_rand`
- 更改识别 elective 响应结果的正则表达式，以确保包含空格的课程名也能被正确解析


v4.0.1 (2020-05-30)
-------------------
- 修复了 IAAA 登录报 500 状态码的问题，详见 [Issue #35](https://github.com/zhongxinghong/PKUAutoElective/issues/35)


v3.0.9 (2020-02-20)
-------------------
- 对相传可能出现的莫名其妙退课的情况做了防护，详见 [Issue #30](https://github.com/zhongxinghong/PKUAutoElective/issues/30)


v3.0.8 (2020-02-20)
-------------------
- 在 elective 两个刷新接口的 headers 中添加了 `Cache-Control: max-age=0`
- 现在可以为课程定义延迟规则，详见 [Issue #28](https://github.com/zhongxinghong/PKUAutoElective/issues/28)
- 修改了部分代码风格


v3.0.7 (2020-02-18)
-------------------
- 现在可以识别出因一学期选多门体育课而收到的来自选课网的错误提示
- 同一回合中出现多门可选的课，并且低优先级待选的课与高优先级已选的课因为 mutex rules 冲突，那么低优先级的课将会被提前忽略，详见 [Issue #25](https://github.com/zhongxinghong/PKUAutoElective/issues/25)


v3.0.6 (2020-02-18)
-------------------
- 修正了 `config.ini` 注释中把 `班号` 写成 `课号` 的笔误
- 选课网有的时候会突然显示某门课的已选人数为 0，而实际选课人数已满，此时会报一个 `Unknown tips` 的异常，现在程序可以对这种情况做出识别


v3.0.5 (2020-02-17)
-------------------
- 现在通过 `config.ini` 定义的课程列表可以像原来那样保持其在文件中的先后顺序，如果在同一循环中遇到同一列表中有多个课可选，将会按照从上往下的顺序依次提交
- 现在会捕获 `Ctrl + C` 在 `main.py` 中引发的 `KeyboardInterrupt`，这样 `Ctrl + C` 将不会再打印 traceback 而是正常退出


v3.0.4 (2020-02-17)
-------------------
- 修改了 `TypeError: argmax() got an unexcepted keyword argument 'axis'` 的错误


v3.0.3 (2020-02-17)
-------------------
- 修改了 iaaa 和 elective 相关接口的请求细节，包括更换某些 url，修改 headers，修改替换 scheme 为 https 等
- 修复了相同 Course 调用 `__eq__` 和 `__hash__` 得到不同值的 bug
- 修复了 `assert self._status is not None` 引发的 `AssertionError`
- 修复了 `mutexes` 在无规则时仍然 print 列表的 bug


v3.0.2 beta (2020-02-17)
-------------------
- 修复了 Windows 下 `Ctrl + C` 失效的问题


v3.0.1 beta (2020-02-17)
-------------------
- 改用 pytorch 训练的 CNN 模型进行验证码识别，提高了识别的准确率
- 优化了验证码图像处理函数的执行效率
- 将多进程架构重写为多线程架构，监控进程现在变为和主进程下的一个子线程
- 允许自定义 User-Agent 列表
- 配置文件中 `student_ID` 键名改成 `student_id`
- 不再使用 `course.csv` 文件配置课程列表，而是统一归入 `config.ini` 中
- 允许用户自定义互斥规则，详见 [Issue #8](https://github.com/zhongxinghong/PKUAutoElective/issues/8)
- 重新设计了 monitor 的路由
- 现在 monitor 不会在 iaaa_loop / elective_loop 正常退出的时候自动退出
- 修改了多处代码风格和设计细节，删除了大量冗余设计


v2.1.1 (2019-09-13)
-------------------
- 修复了 `OperationFailedError` 使用错误的父类派生而导致不能正常初始化的问题


v2.1.0 (2019-09-13)
-------------------
- 修复了 Windows 下自定义参数不生效的问题


v2.0.9 (2019-09-12)
-------------------
- 对 v2.0.8 版本的完善，现在删除了与 `signal` 相关的逻辑，统一了两种运行模式下主进程退出的方式，确保了 `Ctrl + C` 的信号和子进程内部发出的终止信号均能使主进程正常退出


v2.0.8 (2019-09-11)
-------------------
- 对 v2.0.6 版本的完善，该版本在不带 `--with-monitor` 运行的情况下，也可以正确地接收到来自 `Ctrl + C` 的终止命令


v2.0.7 (2019-09-11)
-------------------
- 为 monitor 添加了与错误捕获记录相关的路由


v2.0.6 (2019-09-11)
-------------------
- 修复了在 Windows 下 `Ctrl + C` 无法退出程序的问题


v2.0.5 (2019-09-11)
-------------------
- 可以捕获 IAAA 登录时的密码错误和多次登录失败导致账号已被封禁的错误
- 完善了对多进程/线程下进程死亡的处理，以确保主进程在遇到错误时可以完全退出
- 现在 monitor 进程会在 loop 进程结束后自动退出


v2.0.4 (2019-09-10)
-------------------
- elective 客户端采用多会话机制


v2.0.3 (2019-09-09)
-------------------
- 可以捕获来自 IAAA 的错误
- 丰富了部分错误的提示信息


v2.0.2 (2019.09.09)
-------------------
- 添加了对处于选课计划第一页之后的课程的支持


v2.0.1 (2019.09.09)
-------------------
- 代码重构，删减大量冗余设计
- 新增监视器进程，开启后可以通过特定端口监听运行状态
- 添加多账号支持，去除 cookies / token 本地共享的逻辑，并可以手动指定 config.ini / course.csv 文件的路径
- 修复了在一些情况下会话无法保持的错误
- 可以捕获几个新遇到的系统异常/错误提示
- 美化了终端的输出格式


v1.0.4 (2019.02.22)
-------------------
- 修复了一处语法错误，位于 **main.py** 第 216-235 行的 `ignored.append` 处
- 纠正了一些变量名的拼写错误
- 可以捕获多选英语课引起的错误


v1.0.3 (2019.02.20)
-------------------
- 兼容了本科生辅双的登录界面，主修身份选课测试通过，辅双身份选课支持第一页
- 可以捕获共享回话引起的系统异常
- 可以捕获辅双登录无验证信息的系统异常


v1.0.2 (2019.02.19)
-------------------
- 研究生选课测试通过
- 兼容了部分页面没有 `.//head/title` 标签的情况
- 修改 `Course` 类的 `classNo` 属性为 int 类型，确保 `01` 与 `1` 为同班号
- 主程序开始的第一个循环回合更改为首先主动登录一次，以免旧缓存导致无法切换账号
- 重新登录时会率先删除客户端已有的 cookies ，修复了一次重新登录需要花费两回合的问题
- 更改单一 `User-Agent` 为 `User-Agent` 池
- 可以捕获课程互斥引起的错误提示


v1.0.1 (2019.02.18)
-------------------
- 上线版本，支持非辅双本科生选课

