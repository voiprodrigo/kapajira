import unittest

from unittest.mock import patch, Mock
from jira.resources import Component
from kapajira.jira.reporter import JiraReporter
from kapajira.jira.issues import Issue

config_mock_values = {'projects': ['some_project_1', 'some_project_2'],
                      'url': 'some_url',
                      'user': 'some_user',
                      'password': 'some_password'}


def mock_component(name):
    mock = Mock()
    mock.name = name
    return mock

project_components_mock_values = {
    'some_project_1': [mock_component('some_component_1'), mock_component('some_component_2')],
    'some_project_2': [mock_component('some_component_3'), mock_component('some_component_4')]}


def config_mock_getitem(name):
    return config_mock_values[name]


def jira_mock_getcomponents(project):
    return project_components_mock_values[project]


class TestJiraReporter(unittest.TestCase):
    JIRA_SEARCH_STRING = "description ~ 'hash' AND status != 'Closed'"

    @patch('kapajira.jira.reporter.JIRA')
    def test_issue_exist_if_it_is_found(self, jira_mock):
        jira_mock = jira_mock.return_value
        jira_mock.search_issues.return_value = ['some_issue']
        jp = JiraReporter()

        self.assertEqual('some_issue', jp.existing_issue('hash'))
        jira_mock.search_issues.assert_called_once_with(self.JIRA_SEARCH_STRING)

    @patch('kapajira.jira.reporter.JIRA')
    def test_issue_does_not_exist_if_it_is_not_found(self, jira_mock):
        jira_mock = jira_mock.return_value
        jira_mock.search_issues.return_value = []
        jp = JiraReporter()

        self.assertIsNone(jp.existing_issue('hash'))
        jira_mock.search_issues.assert_called_once_with(self.JIRA_SEARCH_STRING)

    @patch('kapajira.jira.reporter.JIRA')
    @patch('kapajira.jira.reporter.CFG')
    def test_issue_is_created_if_one_does_not_exist(self, config_mock, jira_mock):
        jira_mock = jira_mock.return_value
        jira_mock.search_issues.return_value = []

        config_mock.__getitem__.side_effect = config_mock_getitem

        jp = JiraReporter()

        issue_mock = Mock(spec=Issue)
        issue_mock.get_description.return_value = 'some_desc'
        issue_mock.get_issue_hash.return_value = 'some_hash'
        issue_mock.get_summary.return_value = 'some_summary'
        issue_mock.get_issue_type.return_value = 'some_issuetype'
        issue_mock.get_labels.return_value = ['some_label']

        jp.create_or_update_issue(issue_mock)
        jira_mock.create_issue.assert_called_once_with(fields={
            'project': 'some_project_1',
            'summary': 'some_summary',
            'description': 'some_desc',
            'issuetype': 'some_issuetype',
            'labels': ['some_label']
        })

    @patch('kapajira.jira.reporter.JIRA')
    @patch('kapajira.jira.reporter.CFG')
    def test_issue_is_created_if_one_does_not_exist_second_project(self, config_mock, jira_mock):
        jira_mock = jira_mock.return_value
        jira_mock.search_issues.return_value = []
        jira_mock.project_components.side_effect = jira_mock_getcomponents

        config_mock.__getitem__.side_effect = config_mock_getitem

        jp = JiraReporter()

        issue_mock = Mock(spec=Issue)
        issue_mock.get_description.return_value = 'some_desc'
        issue_mock.get_issue_hash.return_value = 'some_hash'
        issue_mock.get_summary.return_value = 'some_summary'
        issue_mock.get_issue_type.return_value = 'some_issuetype'
        issue_mock.get_labels.return_value = ['some_label']
        issue_mock.get_component.return_value = 'some_component_3'

        jp.create_or_update_issue(issue_mock)
        jira_mock.create_issue.assert_called_once_with(fields={
            'project': 'some_project_2',
            'summary': 'some_summary',
            'description': 'some_desc',
            'issuetype': 'some_issuetype',
            'labels': ['some_label'],
            'components': [{'name': 'some_component_3'}]
        })

    @patch('kapajira.jira.reporter.JIRA')
    def test_issue_is_not_created_if_one_exist(self, jira_mock):
        jira_issue_mock = Mock()

        jira_mock = jira_mock.return_value
        jira_mock.search_issues.return_value = [jira_issue_mock]

        jp = JiraReporter()
        issue_mock = Mock(spec=Issue)
        issue_mock.get_description.return_value = 'some_desc'

        jp.create_or_update_issue(issue_mock)
        jira_issue_mock.update.assert_called_once_with(fields={'description': 'some_desc'})
