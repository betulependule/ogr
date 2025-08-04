# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import pytest
from requre.helpers import record_httpx

from ogr.abstract import IssueStatus
from ogr.exceptions import (
    OperationNotSupported,
)


@record_httpx()
def test_issue_list(project):
    issue_list = project.get_issue_list(status=IssueStatus.all)
    assert issue_list
    assert len(issue_list) >= 100

    issue_list = project.get_issue_list(status=IssueStatus.closed)
    assert issue_list
    assert len(issue_list) >= 25

    issue_list = project.get_issue_list(status=IssueStatus.open)
    assert issue_list
    assert len(issue_list) >= 50


@record_httpx()
def test_create_issue(hello_world_project):
    title = "Test Issue"
    description = "a real nice testing description"

    labels = ["label1", "label2"]
    issue = hello_world_project.create_issue(
        title=title,
        body=description,
        labels=labels,
    )

    assert issue.title == title
    assert issue.description == description
    for issue_label, label in zip(issue.labels, labels):
        assert issue_label.name == label


@record_httpx()
def test_create_private_issue(hello_world_project):
    title = "Test Issue"
    description = "a real nice testing description"

    with pytest.raises(OperationNotSupported):
        hello_world_project.create_issue(
            title=title,
            body=description,
            private=True,
        )


@record_httpx()
def test_create_issue_with_assignee(hello_world_project):
    title = "Test Issue bububa"
    description = "a real nice testing description"

    labels = ["label1", "label2"]
    assignee = ["TomasTomecek"]
    issue = hello_world_project.create_issue(
        title=title,
        body=description,
        labels=labels,
        assignees=assignee,
    )
    assert issue.title == title
    assert issue.description == description
    assert issue.assignees[0].login == assignee[0]


@record_httpx()
def test_issue_list_author(project):
    issue_list = project.get_issue_list(
        status=IssueStatus.all,
        author="mfocko",
    )
    assert issue_list
    assert len(issue_list) >= 9


@record_httpx()
def test_issue_list_nonexisting_author(self):
    issue_list = self.ogr_project.get_issue_list(
        status=IssueStatus.all,
        author="the most nonexistent author that never nonexisted",
    )
    assert len(issue_list) == 0
