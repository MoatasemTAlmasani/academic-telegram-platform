"""Authorization, tenant-target scoping, and concurrency guards for Module 02."""

import asyncio
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.routing import APIRoute
from sqlalchemy import update

from backend.app.api.routes import admin_users
from backend.app.api.rbac_dependencies import require_permission
from backend.app.modules.authentication.permissions import Permission
from database.models.identity import UserSession


class _Result:
    def __init__(self, value=None, *, rowcount=0):
        self.value = value
        self.rowcount = rowcount

    def scalar_one_or_none(self):
        return self.value

    def scalar_one(self):
        return self.value


class _Session:
    def __init__(self, results=()):
        self.results = list(results)
        self.statements = []
        self.added = []
        self.committed = False

    async def execute(self, statement):
        self.statements.append(statement)
        if self.results:
            result = self.results.pop(0)
            return result
        return _Result()

    def add(self, value):
        self.added.append(value)

    async def commit(self):
        self.committed = True


def _dependency_tree(dependencies):
    for dependency in dependencies:
        yield dependency
        yield from _dependency_tree(dependency.dependencies)


def test_every_admin_user_route_requires_authentication_and_rbac_permission():
    routes = [route-®ιάjΧ