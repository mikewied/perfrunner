import logger
from perfrunner.helpers.cbmonitor import with_stats
from perfrunner.tests import PerfTest
from perfrunner.workloads.n1ql import INDEX_STATEMENTS



class N1QLTest(PerfTest):

    def __init__(self, *args, **kwargs):
        super(N1QLTest, self).__init__(*args, **kwargs)

    def build_index(self):
        with_gsi = ''
        if self.test_config.index_settings.use_gsi:
            with_gsi = 'using gsi'

        for name, servers in self.cluster_spec.yield_servers_by_role('n1ql'):
            if not servers:
                raise Exception('No query servers specified for cluster \"{}\",'
                                ' cannot create indexes'.format(name))

            if not self.test_config.buckets:
                raise Exception('No buckets specified for cluster \"{}\",'
                                ' cannot create indexes'.format(name))

            query_node = servers[0].split(':')[0]
            for bucket in self.test_config.buckets:
                self._build_primary_index(query_node, bucket, with_gsi)
                self._build_secondary_indexes(query_node, bucket, with_gsi)

    def _build_primary_index(self, query_node, bucket, with_gsi):
        if self.test_config.index_settings.primary_indexes:
            query = 'CREATE PRIMARY INDEX ON `{}` {};'.format(bucket, with_gsi)
            self.rest.n1ql_query(query_node, query)

    def _build_secondary_indexes(self, query_node, bucket, with_gsi):
        statements = INDEX_STATEMENTS[
            self.test_config.index_settings.index_type
        ]
        for statement in statements:
            query = statement.format(bucket, with_gsi)
            self.rest.n1ql_query(query_node, query)

    @with_stats
    def access(self):
        super(N1QLTest, self).timer()

    def run(self):
        self.load()
        self.wait_for_persistence()
        self.compact_bucket()

        self.build_index()

        self.workload = self.test_config.access_settings
        self.access_bg()
        self.access()

