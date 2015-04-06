from perfrunner.helpers.cbmonitor import with_stats
from perfrunner.tests import PerfTest, TargetIterator
from perfrunner.workloads.n1ql import INDEX_STATEMENTS
from logger import logger

import requests
import math
from tuqquey.tuq import QueryTests


class TuqOptionsTest(QueryTests):

    COLLECTORS = {'n1ql_latency': True}

    def __init__(self, *args, **kwargs):
        super(TuqTest, self).__init__(*args, **kwargs)
        self.n1ql = True
        self.target_iterator = TargetIterator(self.cluster_spec,
                                              self.test_config,
                                              prefix='')

    def run_cbq_query(self, q)
        url = 'http://{}/query/service -d "statement={}?{}'.format(query_node(self.server_node), q)
        resp = self.session.get(url=url)
        return resp.status_code,resp.text

    def _is_index_create_completed (self, bucket, index_name, server = None)
        if index_name = "PRIMARY":
            ddoc_name = 'ddl_#primary'
        else:
            ddoc_name = index_name

        mquery = "SELECT * FROM system:indexes"
        rc,res = self.run_cbq_query(self, mquery)
        while rc = 200:
             this is a cludge, remove when there is a safe way to determine
             an index build is completed
             ###
             if ((int(time.time() * 1000) - start_time_ms) > 7200000):
                 logger.info(build index {} time {} FAILED to complete'.format(bucket, 7200000) 
                 done = True
             rc,res = self.run_cbq_query(mquery)
    
    def build_index(self):
        pdb.set_trce()
        statements = INDEX_STATEMENTS[
            self.test_config.index_settings.index_type
        ]
        for master in self.cluster_spec.yield_masters():
            for bucket in self.test_config.buckets:
                if self.build >= '3.5.0':
                   use_gsi = self.test_config.buckets.use_gsi
                   for statement in statements:
                       host = master.split(':')[0]
                       if "PRIMARY" in statement:
                           index_name = "PRIMARY"
                       else:
                           lh,rh = statement.split(")")  
                           index_name = lh.split("(")  
                       start_time_ms = int(time.time() * 1000)
                       self.rest.exec_n1ql_stmnt(host, statement.format(bucket, use_gsi))
                       if not self.is_index_create_finished(bucket, index_name):
                           end_time_ms = int(time.time() * 1000)
                           logger.info('build index {} time {} FAILED'.format(bucket, end_time_ms - start_time_ms))
                           break 
                else:
                    for statement in statements:
                        host = master.split(':')[0]
                        start_time_ms = int(time.time() * 1000)
                        self.rest.exec_n1ql_stmnt(host, statement.format(bucket, use_gsi))

                end_time_ms = int(time.time() * 1000)
                logger.info('build index {} time {}'.format(bucket, end_time_ms - start_time_ms))

    @with_stats
    def access(self):
        super(TuqTest, self).timer()

    def run(self):
        self.load()
        self.wait_for_persistence()
        self.compact_bucket()

        self.build_index()

        self.workload = self.test_config.access_settings
        self.access_bg()
        self.access()
