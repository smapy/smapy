# -*- coding: utf-8 -*-

import datetime
import functools

from bson import ObjectId

from smapy import utils
from smapy.resource import BaseResource


class MultiProcess(BaseResource):
    """Run a resource in multiple processes."""

    def process(self, message):
        processes = message.pop('processes')
        resource = message.pop('resource')
        messages = [message.copy() for _ in range(processes)]

        self.invoke(resource, messages, concurrency=processes, remote=True)
        results = [m['results'] for m in messages]
        message.update(functools.reduce(utils.sum_dicts, results))

        message['details'] = results


class HelloWorld(BaseResource):
    """Test to check API connection, Returns Hello World"""

    def process(self, message):
        self.invoke('hello.World', message, remote=True)


class Report(BaseResource):
    """Get a report about a past or ongoing session."""

    sync = True

    def get_action_details(self, match):
        match = {
            '$match': match
        }
        group = {
            '$group': {
                '_id': '$action',
                'OK': {
                    '$sum': {
                        '$cond': [{'$eq': ['$status', 'OK']}, 1, 0]
                    }
                },
                'EXCEPTION': {
                    '$sum': {
                        '$cond': [{'$eq': ['$status', 'EXCEPTION']}, 1, 0]
                    }
                },
                'called': {
                    '$sum': 1
                },
                'avg_ms': {
                    '$avg': '$elapsed'
                },
                'max_ms': {
                    '$max': '$elapsed'
                },
                'total_ms': {
                    '$sum': '$elapsed'
                }
            }
        }

        pipeline = [match, group]

        actions = dict()
        for action in self.auditdb.actions.aggregate(pipeline):
            actions[action.pop('_id').replace('.', '_')] = action

        return actions

    def get_action_summary(self, match):
        match = {
            '$match': match
        }
        group = {
            '$group': {
                '_id': '$status',
                'count': {
                    '$sum': 1
                }
            }
        }
        summary = self.auditdb.actions.aggregate([match, group])
        return {status['_id']: status['count'] for status in summary}

    def get_session_counts(self, session):
        match = {
            'session': session['_id'],
            'update_ts': {
                '$gte': session['in_ts']
            }
        }
        counts = {
            collection: self.mongodb[collection].count(match)
            for collection in ['links', 'post', 'occurrences']
        }
        match = {
            '$match': match
        }
        group1 = {
            '$group': {
                '_id': '$site'
            }
        }
        group2 = {
            '$group': {
                '_id': None,
                'count': {
                    '$sum': 1
                }
            }
        }
        pipeline = [match, group1, group2]
        results = list(self.mongodb.links.aggregate(pipeline))
        if results:
            counts['sites'] = results[0]['count']

        return counts

    def process(self, message):
        match = dict()

        session = message.get('session')
        resource = message.get('resource')
        if session:
            match['_id'] = ObjectId(session)

        elif resource:
            match['resource'] = {'$regex': resource}

        else:
            match['resource'] = {'$ne': self.name}

        sort = [('_id', -1)]

        session = self.mongodb.session.find_one(match, sort=sort)

        if session:
            out_ts = session.get('out_ts')
            if out_ts:
                status = 'DONE'

            else:
                status = 'RUNNING'
                out_ts = datetime.datetime.utcnow()

            session.setdefault('status', status)

            in_ts = session['in_ts']
            elapsed = out_ts - in_ts
            session['elapsed'] = str(elapsed)

            match = {
                'session': session['_id']
            }

            # message['actions'] = self.auditdb.actions.count(match)
            message['actions'] = self.get_action_summary(match)
            last_action = self.auditdb.actions.find_one(match, sort=sort)
            message['last_activity'] = last_action.get('end_ts') if last_action else None

            message['session_data'] = self.get_session_counts(session)

            if utils.get_bool(message, 'details'):
                message['details'] = self.get_action_details(match)

        message['session'] = session
