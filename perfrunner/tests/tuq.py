import logger
import json
import uuid
import math
from datetime import date, timedelta
import datetime
import time
from perfrunner.helpers.cbmonitor import with_stats
from perfrunner.tests import PerfTest, TargetIterator
from perfrunner.workloads.n1ql import INDEX_STATEMENTS


class TuqTest(PerfTest):

    COLLECTORS = {'n1ql_latency': True}

    def __init__(self, *args, **kwargs):
        super(TuqTest, self).__init__(*args, **kwargs)
        self.n1ql = True
        self.target_iterator = TargetIterator(self.cluster_spec,
                                              self.test_config,
                                              prefix='')

    def build_index(self):
        statements = INDEX_STATEMENTS[
            self.test_config.index_settings.index_type
        ]
        for master in self.cluster_spec.yield_masters():
            for bucket in self.test_config.buckets:
                use_gsi = bucket.use_gsi
                for statement in statements:
                    host = master.split(':')[0]
                    self.rest.exec_n1ql_stmnt(host, statement.format(bucket,use_gsi_str))

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
