# PKUAutoElective

北大选课网 **补退选** 阶段自动选课小工具 v2.0.9 (2019.09.12)

目前支持 `本科生（含辅双）` 和 `研究生` 选课


## 特点

- 运行过程中不需要进行任何人为操作，且支持同时通过其他设备、IP 访问选课网
- 利用机器学习模型自动识别验证码，具体参见我的项目 [PKUElectiveCaptcha](https://github.com/zhongxinghong/PKUElectiveCaptcha) ，识别率测试值为 **95.6%**
- 具有较为完善的错误捕获机制，不容易在运行中意外退出
- 可以选择性开启额外的监视器进程，之后可以通过端口监听当前的选课状况
- 支持多进程下的多账号/多身份选课


## 安装

该项目至少需要 Python 3 （项目开发环境为 Python 3.6.6），可以从 [Python 官网](https://www.python.org/) 下载并安装

例如在 Debian-Linux 下运行：
```console
$ apt-get install python3
```

下载这个 repo 至本地。点击右上角的 `Clone or download` 即可下载

对于 git 命令行：
```console
$ git clone https://github.com/zhongxinghong/PKUAutoElective.git
```

安装依赖包
```console
$ pip3 install requests lxml Pillow numpy sklearn flask
```

可以改用清华 pip 源，加快下载速度
```console
$ pip3 install requests lxml Pillow numpy sklearn flask -i https://pypi.tuna.tsinghua.edu.cn/simple
```

可选依赖包
```console
$ pip3 install simplejson
```

## 基本用法

1. 复制 `config.sample.ini` 文件，并将所复制得的文件重命名为 `config.ini`
2. 根据系统类型选择合适的 `course.csv` ，同理复制 `course.*.sample.csv` 并将所得文件重命名为 `course.*.csv` ，即 `course.utf-8.csv/course.gbk.csv` ，以确保 csv 表格用软件打开后不会乱码
    - **Linux** 若使用 `utf-8` 编码，可以用 LibreOffice 以 `UTF-8` 编码打开，若使用 `gbk` 编码，可以用 LibreOffice 以 `GB-18030` 编码打开
    - **Windows** 使用 `gbk` 编码，可以用 MS Excel 打开
    - **MacOS** 若使用 `gbk` 编码，可以用 MS Excel 打开，若使用 `utf-8` 编码，可以用 numbers 打开
3. 将待选课程手动添加到选课网的 “选课计划” 中，并确保所选课程处在 **补退选页** 中 “选课计划” 列表的 **第 1 页** 。
    - 注：为了保证刷新速度，减小服务器压力，该项目不解析位于选课计划第 1 页之后的课程
    - 注：该项目不会事前校验待选课程的合理性，只会根据选课提交结果来判断是否提交成功，所以请自行 **确保填写的课程在有名额的时候可以被选上** ，以免浪费时间。部分常见错误可参看 [异常处理](#异常处理) 小节
4. 将待选课程的 `课程名`, `班号`, `开课单位` 对应复制到 `course.csv` 中（本项目根据这三个字段唯一确定一个课程），每个课程占一行，高优先级的课程在上（即如果当前循环回合同时发现多个课程可选，则按照从上往下的优先级顺序依次提交选课请求）
    - 注：考虑到 csv 格式不区分数字和字符串，该项目允许将课号 `01` 以数字 `1` 的形式直接录入
    - 注：请确保每一行的所有字段都被填写，**信息填写不完整的行会被自动忽略，并且不会抛出异常**
5. 配置 `config.ini`
    - 修改 `coding/csv_coding` 项，使之与所用 `course.*.csv` 的编码匹配
    - 填写 IAAA 认证所用的学号和密码
    - 如果是双学位账号，则设置 `dual_degree` 项为 `true` ，同时设置双学位登录身份 `identity` ，只能填 `bzx`, `bfx` ，分别代表 `主修` 和 `辅双` ；对于非双学位账号，则设置 `dual_degree` 为 `false` ，此时登录身份项没有意义。注：以 **双学位账号的主学位身份** 进行选课仍然需要将 `dual_degree` 设为 `true` ，否则可能会遇到一直显示会话过期/尚未登录的情况。
    - 如果待选的课程不在选课计划的第一页，并且无法将第一页的其他课程删除，你可以通过修改 `supply_cancel_page` 来指定实际刷新第几页。注：该项目一个进程只能刷新一页的选课计划，如果你需要选的课处于选课计划的不同页，则需要为每个页面分别开一个进程，详见 [高级用法](#高级用法) 中的 [多账号设置](#多账号设置) 小节
    - 如有需要，可以修改刷新间隔项 `refresh_interval` 和 `random_deviation`，但 **不要将刷新间隔改得过短！**
6. 进入项目根目录，利用 `python3 main.py` 命令运行主程序，即可开始自动选课。


## 测试方法

如有需要，可以进行下面的部分测试，确保程序可以在 `你的补退选页` 中正常运行：

- 可以通过向课程列表中添加如下几种课程，测试程序的反应：

    - 正常的可以直接补选上的课程
    - 已经选满的课程
    - 上课时间/考试时间冲突的课程
    - 相同课号的课程（其他院的相同课或同一门课的不同班）
    - 性质互斥的课程（例如：线代与高代）
    - 跨院系选课阶段开放的其他院专业课

- 可以尝试一下超学分选课会出现什么情况

#### 注意：

- 之后手动退选的时候不要点错课噢 QvQ
- 研究生不能修改选课计划，请慎重测试，不要随便添加其他课程，以免造成不必要的麻烦！


## 高级用法

自 `v2.0.0` 起，可以在程序运行时指定命令行选项。通过 `python3 main.py --help` 查看帮助。
```console
$ python3 main.py --help

Usage: main.py [options]

PKU Auto-Elective Tool v2.0.1 (2019.09.09)

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  --config=FILE         custom config file encoded with utf8
  --course-csv-utf8=FILE
                        custom course.csv file encoded with utf8
  --course-csv-gbk=FILE
                        custom course.csv file encoded with gbk
  --with-monitor        run the monitor process simultaneously

```

通过指定命令行参数，可以开启以下的功能：

### 多账号设置

可以为每一个账号单独创建一个配置文件和一个课程列表，在不同的进程中以不同的配置文件运行该项目，以实现多账号同时刷课

假如为 Alice 和 Bob 同学创建了如下的文件，填写好了相应配置。假设它们与 `main.py` 处于同一目录下
```console
$ ls

config.alice.ini  course.utf-8.alice.csv  config.bob.ini  course.gbk.bob.csv  main.py

```

接下来分别在两个终端中运行下面两个命令，即可实现多账号刷课
```console
$ python3 main.py --config ./config.alice.ini --course-csv-utf8 ./course.utf-8.alice.csv
$ python3 main.py --config ./config.bob.ini --course-csv-gbk ./course.gbk.bob.csv

```

由于选课网存在会话数上限，开启多进程的时候还需要调整各进程的配置文件中的 `client/elective_client_pool_size` 项，合理分配各个进程的会话数。详见 [其他配置项](#其他配置项) 。同一 IP 下所有进程的会话总数不超过 5 。建议值： 单进程 4; 两进程 2+2; 三进程 1+1+2 ......


### 开启监视器

假如你拥有一个可以连上 `elective.pku.edu.cn` 和 `iaaa.pku.edu.cn` 的服务器，你可以在服务器上运行这个项目，并开启监听进程，然后通过访问特定地址来查看当前的运行状态。具体的配置方法如下：

1. 在 `config.ini` 中修改需要绑定的 `host/post`
2. 在运行时指定 `--with-monitor` 参数，即 `python3 main.py --with-monitor`
3. 请求相应的地址即可查看运行状态。例如按照默认设置，可以请求 `http://127.0.0.1:7074`

可以通过 nginx 进行反向代理，配置示例如下：
```nginx
# filename: nginx.autoelective.conf
# coding: utf-8

server {

    listen       12345;
    server_name  10.123.124.125;
    charset      UTF-8;

    location / {

        proxy_pass  http://127.0.0.1:7074;
    }
}

```

在这个示例中，通过访问 `http://10.123.124.125:12345` 可以查看运行状态

该项目为这个监视器注册了如下路由：
```
GET  /            同 /rules
GET  /all         完整的状态
GET  /current     当前候选的课程
GET  /errors      当前已捕获到的错误数
GET  /goals       输出原始的选课计划（直接从 course.csv 中读取到的课程）
GET  /ignored     已经被忽略的课程及相应原因（已选上/无法选）
GET  /login_loop  login-loop 当前循环数
GET  /main_loop   main-loop 当前循环数
GET  /rules       输出这个路由列表

```

例如，请求 `http://10.123.124.125:12345/all` 可以查看完整的状态


## 项目架构与分析

`autoelective/` 目录结构如下
```console
$ tree autoelective/
autoelective/
├── captcha                                   验证码相关
│   ├── classifier.py                         模型导入与分类器类
│   ├── feature.py                            与特征向量提取相关的函数
│   ├── __init__.py                           验证码识别结果的模型和验证码识别类
│   ├── model                                 可用模型
│   │   ├── KNN.model.f5.l1.c1.bz2
│   │   ├── RandomForest.model.f2.c6.bz2
│   │   └── SVM.model.f3.l1.c9.xz
│   └── processor.py                          验证码图像处理相关的函数
├── client.py                                 客户端的基类
├── config.py                                 ini 配置文件的解析类及配置的模型声明
├── const.py                                  文件夹路径、URL 等常数
├── course.py                                 课程模型
├── elective.py                               与 elective.pku.edu.cn 的接口通信的客户端类
├── exceptions.py                             错误类
├── hook.py                                   对客户端请求结果进行校验的相关函数
├── iaaa.py                                   与 iaaa.pku.edu.cn 的接口通信的客户端类
├── __init__.py
├── _internal.py                              内部工具函数
├── logger.py                                 日志类声明
├── loop.py                                   主循环进程的入口
├── monitor.py                                监视器进程的入口
├── parser.py                                 网页解析相关的函数
└── utils.py                                  通用工具函数

```

## 运行流程

#### loop 进程

基本的思路是轮询服务器。利用 `iaaa.py` 和 `elective.py` 中定义的客户端类与服务器进行交互，请求结果借助 `parser.py` 中定义的函数进行解析，然后通过 `hook.py` 中定义的函数对结果进行校验，如果遇到错误，则抛出 `exceptions.py` 中定义的错误类，循环体外层可以捕获相应的错误。并判断应该退出还是进入下回合。

采用多 elective 客户端的机制，存在着可用的 elective 客户端池 `electivePool` 和需登录/重登的 elective 客户端池 `loginPool`，在 loop 进程内有 `login-loop` 和 `main-loop` 两个子线程。

##### login-loop 线程

该线程维护一个登录循环：

1. 监听 `loginPool` ，阻塞线程，直到出现需要登录的客户端
2. 就尝试对该客户端进行登录
3. 登录成功后将该客户端放入 `electivePool` ，如果登录失败，则持有该客户端进入下一回合
4. 结束循环，不管成功失败，等待 `login_loop_interval` 时间（可在 `config.ini` 中修改）

##### main-loop 线程

该线程负责轮询选课网及提交选课请求，运行流程如下：

1. 一次循环回合开始，打印候选课程的列表和已忽略课程的列表。
2. 从 `electivePool` 中获取一个客户端，如果 `electivePool` 为空则阻塞线程，如果客户端尚未登录，则立刻停止当前回合，跳至步骤 (8)
3. 获得补退选页的 HTML ，并解析 “选课计划” 列表和 “已选课程” 列表。
4. 校验 `course.csv` 所列课程的合理性（即必须出现在 “选课计划” 或 “已选课程” 中），随后结合上一步的结果筛选出当回合有选课名额的课程。
5. 如果发现存在可选的课程，则依次提交选课请求。在每次提交前先自动识别一张验证码。
6. 根据请求结果调整候选课程列表，并结束当次回合。
7. 将当前客户端放回 `electivePool` ，下回合会重新选择一个客户端
8. 当次循环回合结束后，等待一个带随机偏量的 `refresh_interval` 时间（可在 `config.ini` 中修改该值）。

#### monitor 进程

在运行时指定 `--with-monitor` 参数，可以开启 `monitor` 进程。此时会在主进程中开启 `loop` 和 `monitor` 两个子进程，它们通过 `multiprocessing.Manager` 共享一部分资源（计划选课列表、已忽略课程列表等）。monitor 本质是一个 server 应用，它注册了可以用于查询共享资源状态的路由，此时通过访问 server 所绑定的地址，即可实现对 loop 状态的监听。


## DEBUG 相关

在 `config.ini` 中提供了如下的选项：

- `client/debug_print_request` 如果你需要了解每个请求的细节，可以将该项设为 `true` ，会将与请求相关的一些重要信息打印到终端。如果你需要知道其他的请求信息，可以自行修改 `hook.py` 下的 `debug_print_request` 函数
- `client/debug_dump_request` 会用 `pickle/gzip` 记录该请求的 `Response` 对象，如果发生未知的错误，仍然可以恢复出当时的请求。如有必要可以将该项设为 `True` 以开启该功能。关于未知错误，详见 [未知错误警告](#未知错误警告) 小节。日志会被记录在 `log/request/` 目录下，可以通过 `utils.py` 中的 `pickle_gzip_load` 函数重新导入


## 其他配置项

- `client/iaaa_client_timeout` IAAA 客户端的最长请求超时
- `client/elective_client_timeout` Elective 客户端的最长请求超时，考虑到选课网在网络阻塞的时候响应时间会很长，这个时间默认比 IAAA 的客户端要长
- `client/elective_client_pool_size` Elective 客户端池的最大容量。注：根据观察，每个 IP 似乎只能总共同时持有 **5 个会话**，否则会遇到 elective 登录时无限超时的问题。因此这个这个值不宜大于 5 （如果你还需要通过浏览器访问选课网，则不能大于 4）。
- `client/login_loop_interval` IAAA 登录循环每两回合的时间间隔


## 异常处理

各种异常类定义参看 `exceptions.py` 。每个类下均有简短的文字说明。

### 系统异常 `SystemException`

对应于 `elective.pku.edu.cn` 的各种系统异常页，目前可识别：

- **请不要用刷课机刷课：** 请求头未设置 `Referer` 字段，或者未事先提交验证码校验请求，就提交选课请求（比如在 Chrome 的开发者工具中，直接找到 “补选” 按钮在 DOM 中对应的链接地址并单击访问。
- **Token无效：** token 失效
- **尚未登录或者会话超时：** cookies 中的 session 信息过期
- **不在操作时段：** 例如，在预选阶段试图打开补退选页
- **索引错误：** 貌似是因为在其他客户端操作导致课程列表中的索引值变化
- **验证码不正确：** 在补退选页填写了错误验证码后刷新页面
- **无验证信息：** 辅双登录时可能出现，原因不明
- **你与他人共享了回话，请退出浏览器重新登录：** 同一浏览器内登录了第二个人的账号，则原账号选课页会报此错误（由于共用 cookies）
- **只有同意选课协议才可以继续选课！** 第一次选课时需要先同意选课协议

### 提示框反馈 `TipsException`

对应于 `补退选页` 各种提交操作（补选、退选等）后的提示框反馈，目前可识别：

- **补选课程成功：** 成功选课后的提示
- **您已经选过该课程了：** 已经选了相同课号的课程（可能是别的院开的相同课，也可能是同一门课的不同班）
- **上课时间冲突：** 上课时间冲突
- **考试时间冲突** 考试时间冲突
- **超时操作，请重新登录：** 貌似是在 cookies 失效时提交选课请求（比如在退出登录或清空 `session.cookies` 的情况下，直接提交选课请求）
- **该课程在补退选阶段开始后的约一周开放选课：** 跨院系选课阶段未开放时，试图选其他院的专业课
- **您本学期所选课程的总学分已经超过规定学分上限：** 选课超学分
- **选课操作失败，请稍后再试：** 未知的操作失败，貌似是因为请求过快
- **只能选其一门：** 已选过与待选课程性质互斥的课程（例如：高代与线代）
- **学校规定每学期只能修一门英语课：** 一学期试图选修多门英语课


## 说明与注意事项

- 为了避免访问频率过快，每一个循环回合结束后，都会暂停一下，确保每两回合间保持适当的间隔，**这个时间间隔不可以改得过短** ，否则有可能对服务器造成压力！（据说校方选课网所在的服务器为单机）
- 不要修改 `course.csv` 的文件编码、表头字段、文件格式，不要添加或删除列，不要在空列填写任何字符，否则可能会造成 csv 文件不能正常读取。
- 该项目通过指定 I/O 相关函数的 `encoding` 参数为 `utf-8-sig` 来兼容带 BOM 头的 UTF-8 编码的文件，包括 `config.ini`, `course.csv` ，如果仍然存在问题，请不要使用 `记事本 NotePad` 进行文件编辑，应改用更加专业的编辑工具或者代码编辑器，例如 `NotePad ++`, `Sublime Text`, `VSCode`, `PyCharm` 等，对配置文件进行修改，并以 `无 BOM 的 UTF-8` 编码保存文件。
- 该项目针对 `预选页` 和 `补退选页` 相关的接口进行设计，`elective.py` 内定义的接口请求方法，只在 **补退选** 阶段进行过测试，不能保证适用于其他阶段。
- 该项目针对如下的情景设计：课在有空位的时候可以选，但是当前满人无法选上，需要长时间不断刷新页面。对于有名额但是网络拥堵的情况（比如到达某个特定的选课时间节点时），用该项目选课 **不一定比手选快**，因为该项目在每次启动前会先登录一次 IAAA ，这个请求在网络堵塞的时候可能很难完成。如果你已经通过浏览器提前登入了选课网，那么手选可能是个更好的选择。


## 未知错误警告

- 在 2019.02.22 下午 5:00 跨院系选课名额开放的时刻，有人使用该项目试图抢 `程设3班`，终端日志表明，程序运行时发现 `程设3班` 存在空位，并成功选上，但人工登录选课网后发现，实际选上了 `程设4班（英文班）` 。使用者并未打算选修英文班，且并未将 `程设4班` 加入到 `course.csv` 中，而仅仅将其添加到教学网　“选课计划”　中，在网页中与 `程设3班` 相隔一行。从本项目的代码逻辑上我可以断定，网页的解析部分是不会出错的，对应的提交选课链接一定是 `程设3班` 的链接。可惜没有用文件日志记录网页结构，当时的请求结果已无从考证。从这一极其奇怪的现象中我猜测，北大选课网的数据库或服务器有可能存在 **线程不安全** 的设计，也有可能在高并发时会偶发 **Race condition** 漏洞。因此，我在此 **强烈建议： (1) 不要把同班号、有空位，但是不想选的课放在选课计划内； (2) 不要在学校服务器遭遇突发流量的时候拥挤选课。** 否则很有可能遭遇 **未知错误！**


## 历史更新信息

见 [Realease History](/HISTORY.md)


## 版本迁移指南

见 [Migration Guide](/MIGRATION_GUIDE.md)


## 责任须知

- 本项目仅供参考学习，你可以修改和使用这个项目，但请自行承担由此造成的一切后果
- 严禁在公共场合扩散这个项目，以免给你我都造成不必要的麻烦


## 证书

- PKUElectiveCaptcha [MIT LICENSE](https://github.com/zhongxinghong/PKUElectiveCaptcha/blob/master/LICENSE)
- PKUAutoElective [MIT LICENSE](https://github.com/zhongxinghong/PKUAutoElective/blob/master/LICENSE)