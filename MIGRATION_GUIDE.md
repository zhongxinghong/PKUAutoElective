Migration Guide
====================

v1.0.4 -> v2.0.1
------------------
- 新版对 `config.ini` 内的绝大多数配置项名称做了修改，需要用新提供 `config.sample.ini` 重新填写一遍配置
- 添加了自定义 `config.ini` 和 `course.csv`

#### Development Related

- 在 `BaseClient` 内添加了 `persist_cookies` 方法，会在 `hooks.py` 内被调用，以确保在一些特定的错误下仍然可以保持会话
- 在 `elective.py` 的 `sso_login` 的请求头中添加了一个固定的无效 `Cookie` 以防止登录时报 `101` 状态码
- 修改了 `IAAA` 的重新登录逻辑，由原来的遇到错误重登，变为每隔一段时间重登
- 在 `loop.py` 中对 `elective.py` 的 `get_Validate` 方法的调用结果添加了一层错误捕获，以应对非 JSON 格式的响应体
