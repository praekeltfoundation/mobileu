from django.utils.timezone import now
from django.conf import settings
from elasticsearch import helpers as es_help, Elasticsearch
from organisation.models import School


def ensure_indices():
    school_idx = SchoolIndex()
    school_idx.ensure_index()


class ElasticSearchIndex:
    base_index_name = None
    index_name = None

    def __init__(self):
        self.es = Elasticsearch([settings.ELASTICSEARCH_URL])
        if settings.ELASTICSEARCH_INDEX_PREFIX:
            self.index_name = settings.ELASTICSEARCH_INDEX_PREFIX + self.base_index_name
        else:
            self.index_name = self.base_index_name

    def ensure_index(self):
        if not self.index_name:
            raise AssertionError('Index name not set.')

        if not self.es.indices.exists(self.index_name):
            self.es.indices.create(self.index_name)

    def delete_index(self):
        if not self.index_name:
            raise AssertionError('Index name not set.')

        if not self.es.indices.exists(self.index_name):
            self.es.indices.delete(self.index_name)

    def all(self):
        results = self.es.search(self.index_name, body={'query': {'match_all': {}}})
        while type(results) == dict and results.get('hits', None):
            results = results.pop('hits', None)
        return results

    def count(self):
        count = self.es.count(index=self.index_name)
        return count['count']


class SchoolIndex(ElasticSearchIndex):
    base_index_name = 'school'

    def update_index(self, update_time=now(), delete_stale=False):
        update_gen = ({
                '_id': school.pk,
                '_index': self.index_name,
                '_op_type': 'index',
                '_type': 'document',
                'date_updated': update_time,
                'name': school.name,
                'province': school.province,
            } for school in School.objects.all())

        num_successful, errors = es_help.bulk(self.es, update_gen)

        if errors:
            pass

        if delete_stale:
            self.es.delete_by_query(self.index_name, {'query': {'range': {'date_updated': {'lt': update_time}}}})

        return num_successful, errors
