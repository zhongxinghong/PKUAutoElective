# PKUAutoElective

北大选课网 **补退选** 阶段自动选课小工具 v1.0.1 (2019.02.18)


## 特点

- 运行过程中不需要进行任何人为操作，且支持同时通过其他设备、IP 访问选课网。
- 利用机器学习模型自动识别验证码，具体参见我的项目 [PKUElectiveCaptcha](https://github.com/zhongxinghong/PKUElectiveCaptcha) ，识别率测试值为 **95.6%** 。
- 具有较为完善的错误捕获机制，可以应对大部分常见的异常情况，确保程序有足够的强健性，不容易因为异常而中断。


## 安装

该项目至少需要 Python 3 （项目开发环境为 Python 3.6.6），可以从 [Python 官网](https://www.python.org/) 下载并安装。
```console
$ apt-get install python3
```

下载这个 repo 至本地
```console
$ git clone https://github.com/zhongxinghong/PKUAutoElective.git
```

安装依赖包
```console
$ pip3 install requests lxml Pillow numpy sklearn
```

可以改用清华 pip 源，加快下载速度
```console
$ pip3 install requests lxml Pillow numpy sklearn -i https://pypi.tuna.tsinghua.edu.cn/simple
```

可选依赖包
```console
$ pip3 install simplejson
```


## 基本用法

1. 根据当前系统类型选择合适的 `course.csv` ，以确保 csv 表格用软件打开后不会乱码，并修改 `config.ini` 中的相应配置，使之与实际使用编码匹配。
    - **Linux** 若使用 `utf-8` 编码，可以用 LibreOffice 以 `UTF-8` 编码打开，若使用 `gbk` 编码，可以用 LibreOffice 以 `GB-18030` 编码打开
    - **Windows** 使用 `gbk` 编码，可以用 MS Excel 打开
    - **MacOS** 若使用 `gbk` 编码，可以用 MS Excel 打开，若使用 `utf-8` 编码，可以用 numbers 打开
2. 将待选课程手动添加到选课网的 “选课计划” 中，并确保所选课程处在 **补退选页** 中 “选课计划” 列表的 **第 1 页**（为了保证刷新速度，该项目不支持解析位于选课计划第二页的课程）。
3. 将相应课程的 `课程名`, `班号`, `开课单位` 填入 `course.csv` 中（本项目根据这三个字段唯一确定一个课程），每个课程占一行，高优先级的课程在上（即如果当前循环回合同时发现多个课程可选，则按照从上往下的优先级顺序依次提交选课请求）。
4. 修改 `config.ini`
    - 修改 `CSV_Coding` 项，使之与所用 `course.csv` 的编码匹配
    - 填写 IAAA 认证所用的学号和密码
    - 如有需要，可以修改刷新间隔
5. 进入项目根目录，利用 `python3 main.py` 命令运行主程序，即可实现自动选课。


## 项目结构与构建思路
```console
.
├── LICENSE
├── README.md
├── autoelective
│   ├── __init__.py
│   ├── _compat.py
│   ├── captcha
│   │   ├── __init__.py                          定义用于验证码识别的主类
│   │   ├── classifier.py                        定义各模型对应的分类器
│   │   ├── feature.py                           定义特征提取函数
│   │   ├── model
│   │   │   ├── KNN.model.f5.l1.c1.bz2
│   │   │   ├── RandomForest.model.f2.c6.bz2
│   │   │   └── SVM.model.f3.l1.c9.xz
│   │   └── preprocess.py                        定义图像处理相关的函数
│   ├── client.py                              定义客户端抽象基类
│   ├── config.py
│   ├── const.py
│   ├── course.py                              定义 Course 课程类
│   ├── elective.py                            定义用于 elective.pku.edu.cn 的客户端类
│   ├── exceptions.py
│   ├── hook.py                                定义用于请求结果校验的 hooks
│   ├── iaaa.py                                定义用于 iaaa.pku.edu.cn 的客户端类
│   ├── logger.py
│   ├── parser.py                              定义解析 HTML 的和解析 csv 的函数
│   └── util.py
├── cache
├── config.ini                               主配置文件
├── course.gbk.csv                           GBK 编码的 course.csv 待选课程表
├── course.utf-8.csv                         UTF-8 编码的 course.csv 待选课程表
├── log
├── main.py                                  项目主程序
└── requirements.txt
```


在 `main.py` 中，利用 `iaaa.py` 和 `elective.py` 定义的客户端类与服务器进行交互，`hook.py` 借助 `parser.py` 定义的函数解析 response，对每次请求结果进行校验，如果遇到错误，则抛出 `exceptions.py` 中定义的错误类，`main.py` 主程序通过捕获这些错误来把握客户端的运行情况，并及时做出相应的反应。


## 运行流程

1. 一次循环回合开始，打印候选课程的列表和已忽略课程的列表。
2. 利用本地 cookies, token 缓存尝试直接登录，如果失败，则重新登录（惰性登录机制），并结束当次回合。
3. 获得补退选页的 HTML ，并解析 “选课计划” 列表和 “已选课程” 列表。
4. 校验 `course.csv` 所列课程的合理性（即必须出现在 “选课计划” 或 “已选课程” 中），随后结合上步的结果筛选出本回合可选课程。
5. 依次提交选课请求，并在每次提交前先自动识别一张验证码。
6. 根据提交请求的响应结果调整候选课程列表，并结束当次回合。
7. 当次循环回合结束后，等待一个带随机偏量的 `Refresh_Interval` 时间（可在 `config.ini` 中修改该值）。


## 异常处理

各种异常类定义参看 `exceptions.py` 。每个类下均有简短的文字说明。

### 系统异常

对应于 elective.pku.edu.cn 的各种系统异常页，目前可识别：

- **Token无效：** token 失效
- **尚未登录或者会话超时：** cookies 中的 session 信息过期
- **不在操作时段：** 例如，在预选阶段试图打开补退选页
- **索引错误：** 貌似是因为在其他客户端操作导致课程列表中的索引值变化
- **验证码不正确：** 在补退选页填写了错误验证码后刷新页面
- **请不要用刷课机刷课：** 请求头未设置 `Referer` 字段，或者未事先提交验证码校验请求，就提交选课请求（比如在 Chrome 的开发者工具中，直接找到 “补选” 按钮在 DOM 中对应的链接地址并单击访问。

### 提示框反馈

对应于 “补退选页” 各种提交操作（补选、退选等）后的提示框反馈，目前可识别：

- **补选课程成功：** 成功选课后的提示
- **您已经选过该课程了：** 已经选了相同课号的课程（可能是别的院开的相同课，也可能是同一门课的不同班）
- **上课时间冲突：** 待选课程与某已选课程的上课时间存在冲突
- **超时操作，请重新登录：** 貌似是在 cookies 失效时提交选课请求（比如在退出登录或清空 `session.cookies` 的情况下，直接提交选课请求）
- **该课程在补退选阶段开始后的约一周开放选课：** 跨院系选课阶段未开放时，试图选其他院的专业课
- **您本学期所选课程的总学分已经超过规定学分上限：** 选课超学分
- **选课操作失败，请稍后再试：** 未知的操作失败，貌似是因为请求过快


## 说明与注意事项

- 为了避免访问频率过快，每一循环回合，不管是正常结束还是由于未知异常结束，都会暂停一下，每两回合间保持适当的时间间隔，**这个时间间隔不可以改得过短** ，否则有可能对学校服务器造成压力！
- 不要修改 `course.csv` 的文件名、文件编码、表头字段、文件格式，不要添加或删除列，不要在空列填写任何字符，否则可能会造成 csv 文件不能正常读取。
- 请确保 `course.csv` 中每一行的所有字段都被填写，**信息填写不完整的行将会被自动忽略，并且不会抛出异常** 。
- 该项目通过统一设置 I/O 输入编码为 `utf-8-sig` 来兼容带 BOM 头的 UTF-8 编码的文件，包括 `config.ini`, `course.csv` ，如果仍然存在问题，请不要使用 `记事本 NotePad` 进行文件编辑，而改用更加专业的编辑工具，例如 `NotePad ++`, `Sublime Text` ，进行文件修改，或者改用代码编辑器，例如 `PyCharm` ，进行修改，并以 `无 BOM 的 UTF-8` 编码保存文件。
- 该项目根据预选页和补退选页进行设计，许多接口，例如 `elective.py` 定义的 `ElectiveClient` 下的接口，只适用于 **补退选** 阶段，不能保证能适用于其他阶段。

## 免责声明

本项目仅供参考学习，你可以修改和使用这个项目，但请自行承担由此造成的一切后果。


## 证书

- PKUElectiveCaptcha [MIT LICENSE](https://github.com/zhongxinghong/PKUElectiveCaptcha/blob/master/LICENSE)
- PKUAutoElective [MIT LICENSE](https://github.com/zhongxinghong/PKUAutoElective/blob/master/LICENSE)