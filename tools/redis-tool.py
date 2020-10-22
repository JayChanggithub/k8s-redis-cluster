#!/opt/app-root/bin/python
# -*- coding: utf-8 -*-

import logging
from textwrap import dedent
from json import dumps, loads
from time import strftime, mktime
from sys import version_info, argv
from re import sub, search, findall
from multiprocessing import Process
from requests import get, post, delete
from time import time, localtime, strftime, sleep
from argparse import ArgumentParser, RawTextHelpFormatter

from os import (
    chdir,
    listdir,
    remove,
    getcwd,
    popen,
    makedirs,
    system
)

from os.path import (
    join,
    isdir,
    isfile,
    splitext,
    dirname,
    basename,
    getmtime,
    abspath
)

from rediscluster import RedisCluster
from kubernetes import client, config
class redis_cluster(object):

    k8s_config = join(getcwd(), 'config')
    redis_pods = [
        'redis-app-0',
        'redis-app-1',
        'redis-app-2',
        'redis-app-3',
        'redis-app-4',
        'redis-app-5'
    ]

    def __init__(self):

        self.migration_dir = '/usr/local/redis-shake/'
        self.migration_tool = '/usr/local/redis-shake/redis-shake.linux'
        self.sync_check = '/usr/local/redis-full-check/redis-full-check'
        self.redis_fqdn = [
            {
                'host': 'redis-app-0.redis-service.{0}.svc.cluster.local'.format(ns),
                'port': port
            },
            {
                'host': 'redis-app-1.redis-service.{0}.svc.cluster.local'.format(ns),
                'port': port
            },
            {
                'host': 'redis-app-2.redis-service.{0}.svc.cluster.local'.format(ns),
                'port': port
            },
            {
                'host': 'redis-app-3.redis-service.{0}.svc.cluster.local'.format(ns),
                'port': port
            },
            {
                'host': 'redis-app-4.redis-service.{0}.svc.cluster.local'.format(ns),
                'port': port
            },
            {
                'host': 'redis-app-5.redis-service.{0}.svc.cluster.local'.format(ns),
                'port': port
            }
        ]

    def fopen(self, file='', content='',
              mode='r', json=False):
        data = ''
        f = open(file, mode)
        if mode == 'w' or mode == 'a':
            if json:
                f.write(dumps(content, indent=4, sort_keys=False) + '\n')
            else:
                f.write(str(content))
        else:
            if json:
                data = eval(f.read())
            else:
                data = f.read()
        f.close()
        return data

    @staticmethod
    def get_podip(ns):

        config.kube_config.load_kube_config(config_file=redis_cluster.k8s_config)
        api = client.CoreV1Api()

        redis_list = [
            api.read_namespaced_pod(namespace=ns, name=name).status.pod_ip
            for name in redis_cluster.redis_pods if name
        ]

        return redis_list

    def connect_redis_cluster(self):

        try:
            conn = RedisCluster(
                startup_nodes=self.redis_fqdn,
                skip_full_coverage_check=True,
                decode_responses=True
            )
            logging.info('=> connect success.')
        except Exception as error:
            logging.warning('=> connect exception.')
            raise SystemExit(-1)

        pod_ips = redis_cluster.get_podip(ns)

        master_nodes = [
            node + ':6379' for node in pod_ips
            if conn.info()[node + ':6379']['role'] == 'master'
        ]

        slave_nodes = [
            node + ':6379' for node in pod_ips
            if conn.info()[node + ':6379']['role'] == 'slave'
        ]

        node_dict = {
            'master': master_nodes,
            'slave': slave_nodes
        }

        return node_dict

    def sync_db(self):

        print('startup sync up data ....')
        sync_cmd = [
            '{0}'.format(self.migration_tool),
            '-type',
            '{0}'.format(mode),
            '-conf',
            '{0}'.format(update_conf),
            '&'
        ]
        popen(' '.join(sync_cmd)).read()
        return True

    def dump_db(self):

        print('startup dump data to rdb ....')

        if src_type == 'cluster':
            cluster = RedisCluster(
                startup_nodes=self.redis_fqdn,
                skip_full_coverage_check=True,
                decode_responses=True
            )
            cluster.bgsave()
        elif src_type == 'standalone':

            save_cmd = [
                'redis-cli',
                '-h',
                '{0}'.format(src_ip),
                '-p',
                '{0}'.format(port),
                'bgsave'
            ]
            popen(' '.join(save_cmd)).read()
        dump_cmd = [
            '{0}'.format(self.migration_tool),
            '-type',
            '{0}'.format(mode),
            '-conf',
            '{0}'.format(update_conf)
        ]
        popen(' '.join(dump_cmd)).read()
        return True

    def restore_db(self):

        print('restore db from rdb data ....')
        restore_cmd = [
            '{0}'.format(self.migration_tool),
            '-type',
            '{0}'.format(mode),
            '-conf',
            '{0}'.format(update_conf)
        ]

        popen(' '.join(restore_cmd)).read()
        return True

    def check_sync(self):

        print('startup check datas ....')
        cache_datas = self.fopen(file=cache_file).splitlines()

        for line in cache_datas:
            if 'src_ip' in line:
                src_ip = line.split()[1].strip()
            elif 'src_db' in line:
                src_db = line.split()[1].strip()
            elif 'target_ip' in line:
                target_ip = line.split()[1].strip()
            elif 'target_db' in line:
                target_db = line.split()[1].strip()

        check_cmd = [
            '{0}'.format(self.sync_check),
            '-s',
            '"{0}"'.format(src_ip),
            '-t',
            '"{0}"'.format(target_ip),
            '--comparemode=1',
            '--comparetimes=1',
            '--qps=10',
            '--batchcount=100',
            '--sourcedbtype={0}'.format(src_db),
            '--targetdbtype={0}'.format(target_db),
            '--targetdbfilterlist=0',
            '-m',
            '1'
        ]

        while True:
            status = popen(
                ' '.join(
                    check_cmd
                )
            ).read().split('\n')[-2]
            if findall(r'\d+', status).count('0') == 2:
                logging.info('=> success sync the redis db process, status: {0}.'.format(status))
                print('=> success sync the redis db process, status: {0}.'.format(status))
                break
        return True

    def preconfig(self):

        for fs in (cache_file, update_conf):
            if isfile(fs):
                remove(fs)

        datas = self.fopen(file=org_conf).splitlines()

        if mode == 'sync':

            if src_type.lower() == 'cluster':
                s_ip = ';'.join(nodes_data['master']).rstrip(';')
                src_db_type = 1
            elif src_type.lower() == 'standalone':
                s_ip = src_ip + ':' + port
                src_db_type = 0
            else:
                logging.warning('=> source type none support.')
                raise SystemExit(-1)

            if target_type.lower() == 'cluster':
                t_ip = ';'.join(nodes_data['master']).rstrip(';')
                target_db_type = 1
            elif target_type.lower() == 'standalone':
                t_ip = target_ip + ':' + port
                target_db_type = 0
            else:
                logging.warning('=> target type none support.')
                raise SystemExit(-1)

            for line in datas:
                if 'source.type' in line:
                    src_type_idx = datas.index(line)
                    datas[src_type_idx] = line.replace('src.type', src_type.lower())
                elif 'source.address' in line:
                    src_addr_idx = datas.index(line)
                    datas[src_addr_idx] = line.replace('source.ips', s_ip)
                elif 'target.type' in line:
                    target_type_idx = datas.index(line)
                    datas[target_type_idx] = line.replace('des.type', target_type.lower())
                elif 'target.address' in line:
                    target_addr_idx = datas.index(line)
                    datas[target_addr_idx] = line.replace('target.ips', t_ip)
                elif 'log.file' in line:
                    log_idx = datas.index(line)
                    datas[log_idx] = line.replace('log-file', join(pwd, 'reports', 'redis-shake-sync.log'))
                server_data = '\n'.join([
                    'src_ip: {0}'.format(s_ip),
                    'src_db: {0}'.format(src_db_type),
                    'src_type: {0}'.format(src_type.lower()),
                    'target_ip: {0}'.format(t_ip),
                    'target_db: {0}'.format(target_db_type),
                    'target_type: {0}'.format(target_type.lower())
                ])
                self.fopen(file=cache_file, content=server_data, mode='w')

        elif mode == 'dump':
            dump_dir = join(pwd, 'reports', t_msg)
            dump_file_name = 'dump-' + t_msg
            if not isdir(dump_dir):
                makedirs(dump_dir)
            if src_type.lower() == 'cluster':
                s_ip = ';'.join(nodes_data['master']).rstrip(';')
            elif src_type.lower() == 'standalone':
                s_ip = src_ip + ':' + port
            else:
                logging.warning('=> source type none support.')
                raise SystemExit(-1)
            for line in datas:
                if 'source.type' in line:
                    src_type_idx = datas.index(line)
                    datas[src_type_idx] = line.replace('src.type', src_type.lower())
                elif 'source.address' in line:
                    src_addr_idx = datas.index(line)
                    datas[src_addr_idx] = line.replace('source.ips', s_ip)
                elif 'target.rdb.output' in line:
                    target_rdb_output_idx = datas.index(line)
                    datas[target_rdb_output_idx] = line.replace('output_file', join(dump_dir, dump_file_name))
                elif 'log.file' in line:
                    log_idx = datas.index(line)
                    datas[log_idx] = line.replace('log-file', join(pwd, 'reports', 'redis-shake-dump.log'))

        elif mode == 'restore':

            if not isdir(rdir):
                print('no such file or directory => {0}'.format(rdir))
                logging.warning('=> no such file or directory => {0}.'.format(rdir))
                raise SystemExit(-1)

            restore_files = [
                 f for f in listdir(rdir)
                 if search(r'dump*', f)
            ]

            if len(restore_files) == 0:
                print('no such restore dump data.')
                logging.warning('=> no such restore dump data.')
                raise SystemExit(-1)
            elif len(restore_files) == 1:
                inpfiles = join(rdir, restore_files[0])
            elif len(restore_files) > 1:
                inpfiles = [
                    join(rdir, f)
                    for f in restore_files
                ]
                inpfiles = ';'.join(inpfiles)

            if target_type.lower() == 'cluster':
                t_ip = ';'.join(nodes_data['master']).rstrip(';')
            elif target_type.lower() == 'standalone':
                t_ip = target_ip + ':' + port
            else:
                logging.warning('=> source type none support.')
                raise SystemExit(-1)

            for line in datas:
                if 'target.type' in line:
                    target_type_idx = datas.index(line)
                    datas[target_type_idx] = line.replace('des.type', target_type.lower())
                elif 'target.address' in line:
                    target_addr_idx = datas.index(line)
                    datas[target_addr_idx] = line.replace('target.ips', t_ip)
                elif 'source.rdb.input' in line:
                    source_rdb_input_idx = datas.index(line)
                    datas[source_rdb_input_idx] = line.replace('input_file', inpfiles)
                elif 'log.file' in line:
                    log_idx = datas.index(line)
                    datas[log_idx] = line.replace('log-file', join(pwd, 'reports', 'redis-shake-restore.log'))

        info = '\n'.join(datas)
        self.fopen(file=update_conf, content=info, mode='a')
        return True

if __name__ == '__main__':

    pwd = getcwd()
    script = __file__
    logdir = join(pwd, 'reports')
    script_logname = script.split('.')[0] + '.log'
    cache_file = join(pwd, 'server_cache')
    logging.basicConfig(
        filename=join(logdir, script_logname),
        level=logging.INFO,
        format='[%(asctime)-12s] %(levelname)-8s : %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    t_msg = ''.join(strftime('%Y-%m-%d-%H-%M-%S').split('-'))
    defaut_src_ips = [
        ip + ':6379;'
        for ip in redis_cluster.get_podip('kube-ops')[:3]
    ]

    parser = ArgumentParser()
    parser.add_argument(
        '-p',
        '--port',
        dest='port',
        type=str,
        default='6379',
        help='redis service port'
    )

    parser.add_argument(
        '-s',
        '--source',
        dest='source',
        type=str,
        default='{0}'.format(''.join(defaut_src_ips).rstrip(';')),
        help='source cluster or standalone redis instances ip'
    )

    parser.add_argument(
        '-st',
        '--source-type',
        dest='sourcetype',
        type=str,
        default='cluster',
        choices=['cluster', 'standalone'],
        help='specified the source redis standalone or cluster'
    )

    parser.add_argument(
        '-d',
        '--des',
        dest='des',
        type=str,
        default='10.99.104.251',
        help='destination cluster or standalone redis instances ip'
    )

    parser.add_argument(
        '-dt',
        '--des-type',
        dest='destype',
        type=str,
        default='standalone',
        choices=['cluster', 'standalone'],
        help='specified the destination redis standalone or cluster'
    )

    parser.add_argument(
        '-n',
        '--namespace',
        dest='namespace',
        type=str,
        default='kube-ops',
        help='specified the redis cluster namespace in kubernetes'
    )

    parser.add_argument(
        '-m',
        '--mode',
        dest='mode',
        type=str,
        default='dump',
        choices=['dump', 'restore', 'sync'],
        help='specified the action mode'
    )

    parser.add_argument(
        '-rdir',
        '--restore-dir',
        dest='rdir',
        type=str,
        help='specified the restore directory absolute path'
    )

    args = parser.parse_args()
    ns = args.namespace
    port = args.port
    src_type = args.sourcetype
    src_ip = args.source
    target_ip = args.des
    target_type = args.destype
    mode = args.mode
    rdir = args.rdir
    redis = redis_cluster()
    update_conf = join(redis.migration_dir, 'redis-shake-cluster.conf')
    nodes_data = redis.connect_redis_cluster()

    if  mode == 'sync':
        org_conf = join(pwd, 'redis-shake-sync-org.conf')
        redis.preconfig()
        sync_process = Process(target=redis.sync_db)
        check_process = Process(target=redis.check_sync)
        sync_process.start()
        check_process.start()
        while True:
            if not check_process.is_alive():
                check_process.join()
                sync_process.terminate()
                logging.info('=> progress done.')
                break
        raise SystemExit(0)
    elif mode == 'restore':
        org_conf = join(pwd, 'redis-shake-restore-org.conf')
        redis.preconfig()
        restore_process = Process(target=redis.restore_db)
        restore_process.start()
        restore_process.join()
        restore_process.terminate()
        raise SystemExit(0)
    elif mode == 'dump':
        org_conf = join(pwd, 'redis-shake-dump-org.conf')
        redis.preconfig()
        dump_process = Process(target=redis.dump_db)
        dump_process.start()
        dump_process.join()
        dump_process.terminate()
        raise SystemExit(0)
    else:
        print('invaild args of mode options ....')
        logging.warning('=> invaild args of mode options ....')
        raise SystemExit(-1)
