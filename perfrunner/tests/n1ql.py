import logger
from perfrunner.helpers.cbmonitor import with_stats
from perfrunner.tests import PerfTest
from exceptions import NotImplementedError


class N1QLTest(PerfTest):

    COLLECTORS = {
        'n1ql_latency': True,
        'n1ql_stats': True,
        'secondary_stats': True
    }

    def __init__(self, *args, **kwargs):
        super(N1QLTest, self).__init__(*args, **kwargs)

    def build_index(self):
        for name, servers in self.cluster_spec.yield_servers_by_role('n1ql'):
            if not servers:
                raise Exception('No query servers specified for cluster \"{}\",'
                                ' cannot create indexes'.format(name))

            if not self.test_config.buckets:
                raise Exception('No buckets specified for cluster \"{}\",'
                                ' cannot create indexes'.format(name))

            query_node = servers[0].split(':')[0]
            for bucket in self.test_config.buckets:
                self._build_index(query_node, bucket)

    def _build_index(self, query_node, bucket):
        for index in self.test_config.n1ql_settings.indexes:
            index_name = index.split('::')[0]
            index_query = index.split('::')[1]
            query = index_query.format(name=index_name, bucket=bucket)
            self.rest.n1ql_query(query_node, query)
            self.rest.wait_for_indexes_to_become_online(host=query_node,
                                                        index_name=index_name)

    def _create_prepared_statements(self):
        for name, servers in self.cluster_spec.yield_servers_by_role('n1ql'):
            if not servers:
                raise Exception('No query servers specified for cluster \"{}\",'
                                ' cannot create prepared statement'.format(name))

            if not self.test_config.buckets:
                raise Exception('No buckets specified for cluster \"{}\", '
                                'cannot create prepared statement'.format(name))

            query_node = servers[0].split(':')[0]

            self.n1ql_queries = []
            access_settings = self.test_config.access_settings
            for query in access_settings.n1ql_queries:
                if 'use_prepared' in query and query['use_prepared']:
                    stmt = 'PREPARE {}'.format(query['statement'])
                    resp = self.rest.n1ql_query(query_node, stmt)
                    del query['statement']
                    query['prepared'] = '"' + resp['results'][0]['name'] + '"'
                self.n1ql_queries.append(query)


    @with_stats
    def access(self):
        super(N1QLTest, self).timer()

    def run(self):
        raise NotImplementedError("N1QLTest is a base test and cannot be run")


class N1QLLatencyTest(N1QLTest):

    def __init__(self, *args, **kwargs):
        super(N1QLLatencyTest, self).__init__(*args, **kwargs)

    def run(self):
        self.load()
        self.wait_for_persistence()
        self.compact_bucket()

        self.build_index()

        self._create_prepared_statements()
        self.workload = self.test_config.access_settings
        self.access_bg()
        self.access()

        if self.test_config.stats_settings.enabled:
            self.reporter.post_to_sf(
                *self.metric_helper.calc_query_latency(percentile=80)
            )


class N1QLThroughputTest(N1QLTest):

    def __init__(self, *args, **kwargs):
        super(N1QLThroughputTest, self).__init__(*args, **kwargs)

    def run(self):
        self.load()
        self.wait_for_persistence()
        self.compact_bucket()

        self.build_index()

        self._create_prepared_statements()
        self.workload = self.test_config.access_settings
        self.access_bg()
        self.access()

        if self.test_config.stats_settings.enabled:
            self.reporter.post_to_sf(
                *self.metric_helper.calc_avg_n1ql_queries()
            )
