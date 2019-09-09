FROM python:slim

LABEL maintainer="you.siki@outlook.com"

RUN pip install --no-cache-dir \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    lxml \
    numpy \
    Pillow \
    sklearn \
    requests \
    simplejson 

RUN pip install --no-cache-dir \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    flask \
    werkzeug

ADD . /workspace

VOLUME [ "/config" ]

WORKDIR /workspace

CMD [ \
    "python", \
    "main.py", \
    "--with-monitor", \
    "--config=/config/config.ini", \
    "--course-csv-gbk=/config/course.gbk.csv", \
    "--course-csv-utf8=/config/course.utf-8.csv" ]