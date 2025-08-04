# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

import datetime
import logging
from typing import Optional

import pyforgejo
from pyforgejo.types import Issue as PyforgejoIssue

from ogr.abstract import Issue, IssueLabel, IssueStatus
from ogr.exceptions import (
    ForgejoAPIException,
    IssueTrackerDisabled,
    OperationNotSupported,
)
from ogr.services import forgejo
from ogr.services.base import BaseIssue
from ogr.services.forgejo.label import ForgejoIssueLabel

logger = logging.getLogger(__name__)


class ForgejoIssue(BaseIssue):
    def __init__(self, raw_issue: PyforgejoIssue, project: "forgejo.ForgejoProject"):
        super().__init__(raw_issue, project)

    @property
    def title(self) -> str:
        return self._raw_issue.title

    @title.setter
    def title(self, new_title: str) -> None:
        self._raw_issue.title = new_title

    @property
    def id(self) -> int:
        return self._raw_issue.id

    @property
    def status(self) -> IssueStatus:
        return IssueStatus[self._raw_issue.state]

    @property
    def url(self) -> str:
        return self._raw_issue.url

    @property
    def assignees(self) -> list:
        return self._raw_issue.assignees

    @property
    def author(self) -> str:
        return self._raw_issue.original_author

    @property
    def created(self) -> datetime.datetime:
        return self._raw_issue.created_at

    @property
    def labels(self) -> list[IssueLabel]:
        return [ForgejoIssueLabel(label, self) for label in self._raw_issue.labels]

    def __str__(self) -> str:
        return "Forgejo" + super().__str__()

    @staticmethod
    def create(
        project: "forgejo.ForgejoProject",
        title: str,
        body: str,
        private: Optional[bool] = None,
        labels: Optional[list[str]] = None,
        assignees: Optional[list] = None,
    ) -> "Issue":
        # private issues will be supported in the future: https://codeberg.org/forgejo/design/issues/2
        if private:
            raise OperationNotSupported("Private issues are not supported by Forgejo.")

        if not project.has_issues:
            raise IssueTrackerDisabled()

        int_labels = []

        if labels:
            int_labels = [int(label) for label in labels]

        try:
            owner = project.forgejo_repo.owner.login
            forgejo_repo = project.forgejo_repo

            issue = project.service.api.issue.create_issue(
                owner=owner,
                repo=forgejo_repo,
                title=title,
                assignees=assignees,
                body=body,
                labels=int_labels,
            )
            return ForgejoIssue(issue, project)

        except pyforgejo.NotFoundError as ex:  # 404 error
            logger.error("Issue could not be created.")
            raise ForgejoAPIException("Issue could not be created.") from ex

    @staticmethod
    def get(project: "forgejo.ForgejoProject", issue_id: int) -> "Issue":
        if not project.has_issues:
            raise IssueTrackerDisabled()

        try:
            owner = project.forgejo_repo.owner.login
            forgejo_repo = project.forgejo_repo

            issue = project.service.api.issue.get_issue(
                owner=owner,
                repo=forgejo_repo,
                index=issue_id,
            )

            return ForgejoIssue(issue, project)

        except pyforgejo.NotFoundError as ex:  # 404 error
            logger.error(f"Issue {issue_id} was not found.")
            raise ForgejoAPIException(f"Issue {issue_id} was not found.") from ex

    @staticmethod
    def get_list(
        project: "forgejo.ForgejoProject",
        status: IssueStatus = IssueStatus.open,
        author: Optional[str] = None,
        assignee: Optional[str] = None,
        labels: Optional[list[str]] = None,
    ) -> list["Issue"]:
        if not project.has_issues:
            raise IssueTrackerDisabled()

        try:
            owner = project.forgejo_repo.owner.login
            forgejo_repo = project.forgejo_repo
            labels_str = None

            if labels:
                labels_str = " ".join(labels)

            return project.service.api.issue.list_issues(
                owner=owner,
                repo=forgejo_repo,
                state=status.name,
                labels=labels_str,
                created_by=author,
                assigned_by=assignee,
            )

        except pyforgejo.NotFoundError as ex:  # 404 error
            logger.error("Could not access issues.")
            raise ForgejoAPIException("Could not access issues.") from ex

    def close(self) -> "Issue":
        self._raw_issue.state = "closed"
        return self

    def add_label(self, *labels: str) -> None:
        for label in labels:
            self._raw_issue.labels.append(label)

    def add_assignee(self, *assignees: str) -> None:
        self._raw_issue.assignees = assignees
