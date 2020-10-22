FROM centos/python-36-centos7

USER root

ENV WORk_SOURCE /usr/src/

WORKDIR $WORk_SOURCE

RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime

RUN echo 'Asia/Shanghai' > /etc/timezone

RUN rm -rf /var/cache/yum/*

RUN yum update -y && yum install -y bash vim epel-release yum-utils

RUN yum install http://rpms.remirepo.net/enterprise/remi-release-7.rpm -y

RUN yum-config-manager --enable remi

RUN yum install redis -y

ADD redis-shake-v2.0.3.tar.gz /usr/local/

ADD redis-full-check-1.4.8.tar.gz /usr/local　

COPY . $WORk_SOURCE

RUN mv /usr/local/redis-shake-* /usr/local/redis-shake

RUN mv /usr/local/redis-full-check-* /usr/local/redis-full-check

RUN pip3 install --upgrade pip

RUN pip3 install \
    --trusted-host pypi.python.org \
    --trusted-host pypi.org \
    --trusted-host files.pythonhosted.org \
    -r requirements.txt
