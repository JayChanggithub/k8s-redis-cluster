## Cluster-NoSQL-Redis

[![](https://encrypted-tbn0.gstatic.com/images?q=tbn%3AANd9GcSDvmr8Rzm_79Sh5Ph1Lm_g9xu6KnaBn0y-1A&usqp=CAU)](#Cluster-NoSQL-Redis)

---

## Suitable Project

   - `None`

---

## Version

`Rev: 1.0.1`

---

## Status

[![pipeline status](http://ipt-gitlab.ies.inventec:8081/SIT-develop-tool/cluster-nosql-redis/badges/master/pipeline.svg)](http://ipt-gitlab.ies.inventec:8081/SIT-develop-tool/cluster-nosql-redis/-/commits/master)


---

## Description

  - Base on kubernetes cluster ecosystem to build up the redis HA cluster.
  - The purpose to deployment redis-tool is used to sync data, backup data and restore data.
  - Use cronjob object of kubernetes to backup/dump data every hour.


---

## Usage

  - Redis cluster instance.


    ```bash
    redis_pods = [
        'redis-app-0',
        'redis-app-1',
        'redis-app-2',
        'redis-app-3',
        'redis-app-4',
        'redis-app-5'
    ]
    ```

  - Execute the container from image of **redis-tool**.


    ```bash
    $ kubectl run -it redis-tool \
            --rm=true \
            --image="registry.ipt-gitlab:8081/sit-develop-tool/cluster-nosql-redis/redis-tool:$VERSION" \
            --overrides='{ "apiVersion": "v1", "spec": { "imagePullSecrets": [{"name": "gitlab-registry"}] } }' \
            --restart=Never bash -n kube-ops
    ```

  - Using python shell to list data keys.


    ```bash
    $ kubectl run -it redis-tool \
            --rm=true \
            --image="registry.ipt-gitlab:8081/sit-develop-tool/cluster-nosql-redis/redis-tool:$VERSION" \
            --overrides='{ "apiVersion": "v1", "spec": { "imagePullSecrets": [{"name": "gitlab-registry"}] } }' \
            --restart=Never bash -n kube-ops

    $ python


    import sys
    from rediscluster import RedisCluster
    def init_redis():
        startup_nodes = [
            {'host': 'redis-app-0.redis-service.kube-ops.svc.cluster.local', 'port': 6379},
            {'host': 'redis-app-1.redis-service.kube-ops.svc.cluster.local', 'port': 6379},
            {'host': 'redis-app-2.redis-service.kube-ops.svc.cluster.local', 'port': 6379},
            {'host': 'redis-app-3.redis-service.kube-ops.svc.cluster.local', 'port': 6379},
            {'host': 'redis-app-4.redis-service.kube-ops.svc.cluster.local', 'port': 6379},
            {'host': 'redis-app-5.redis-service.kube-ops.svc.cluster.local', 'port': 6379}
        ]
        try:
            conn = RedisCluster(startup_nodes=startup_nodes,
                                skip_full_coverage_check=True,
                                decode_responses=True)
            print('连接成功！！！！！1', conn)
            return conn
        except Exception as e:
            print("connect error ", str(e))
            sys.exit(1)

    rc = init_redis()
    rc.scan()
    ```

  - To **dump** the redis server data.


    ```bash

    # The first startup the container
    $ kubectl run -it redis-tool \
            --rm=true \
            --image="registry.ipt-gitlab:8081/sit-develop-tool/cluster-nosql-redis/redis-tool:$VERSION" \
            --overrides='{ "apiVersion": "v1", "spec": { "imagePullSecrets": [{"name": "gitlab-registry"}] } }' \
            --restart=Never bash -n kube-ops

    # When the redis-tool container was running
    $ kubectl exec -it redis-tool -n kube-ops bash


    # dump the cluster instance
    $ python redis-tool.py -n kube-ops -st cluster -m dump -p 6379

    # dump the standalone instance
    $ python redis-tool.py -n kube-ops -st standalone -s <instance_redis_ip> -m dump -p 6379

    # check dump data
    $ ls -al ./reports/$timestemp/
    ```

  - To **restore** the redis from specified data.


    ```bash
    # The first startup the container
    $ kubectl run -it redis-tool \
            --rm=true \
            --image="registry.ipt-gitlab:8081/sit-develop-tool/cluster-nosql-redis/redis-tool:$VERSION" \
            --overrides='{ "apiVersion": "v1", "spec": { "imagePullSecrets": [{"name": "gitlab-registry"}] } }' \
            --restart=Never bash -n kube-ops

    # When the redis-tool container was running
    $ kubectl exec -it redis-tool -n kube-ops bash

    # Restore the redis from specified data
    $ python redis-tool.py -n kube-ops -dt <standalone|cluster> -p 6379 -d <cluster_ignore|10.99.104.251> -m restore -rdir /usr/src/reports/$timestemp


    # check log showing as follow, press 'Ctrl + C'
    $ cat reports/redis-shake-restore.log
    2020/11/02 14:03:17 [INFO] restore from '[/usr/src/reports/20201102140026/dump-20201102140026.0 /usr/src/reports/20201102140026/dump-20201102140026.1 /usr/src/reports/20201102140026/dump-20201102140026.2]' to '[10.99.104.251:6379]' done
    2020/11/02 14:03:17 [INFO] Enabled http stats, set status (incr), and wait forever.
    ```


  - To **synchronize** the end-to-end redis instance


    ```bash
    # The first startup the container
    $ kubectl run -it redis-tool \
            --rm=true \
            --image="registry.ipt-gitlab:8081/sit-develop-tool/cluster-nosql-redis/redis-tool:$VERSION" \
            --overrides='{ "apiVersion": "v1", "spec": { "imagePullSecrets": [{"name": "gitlab-registry"}] } }' \
            --restart=Never bash -n kube-ops

    # When the redis-tool container was running
    $ kubectl exec -it redis-tool -n kube-ops bash


    # redis cluster to redis standalone(10.99.104.251)
    $ python redis-tool.py -p 6379 -n kube-ops -m sync

    # redis standalone instance(10.99.104.251) to cluster
    $ python redis-tool.py -p 6379 -n kube-ops -tt cluster  -s 10.99.104.251 -st standalone -m sync
    ```

---

## Log

  - The `dump` log is `reports/redis-shake-dump.log`
  - The `sync` log is `reports/redis-shake-sync.log`
  - The `restore` log is `reports/redis-shake-restore.log`

---

## Contact
##### Author: Chang.Jay
