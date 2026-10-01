"""Locations used by the builders, relative to this repository.

The companion projects are expected next to this repository (sibling clones):

    <parent>/nodejs-tutorials/      <- this repo
    <parent>/fastify-tasks-api/
    <parent>/temporal-order-service/
    <parent>/fastify-temporal-orders/
    <parent>/temporal-examples/
    <parent>/fastify-examples/

Set PROJECTS_DIR to use another location.
"""
import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_DIR = os.path.join(REPO_ROOT, 'pdfs')
PROJECTS_DIR = os.environ.get('PROJECTS_DIR', os.path.dirname(REPO_ROOT))


def pdf(name):
    os.makedirs(PDF_DIR, exist_ok=True)
    return os.path.join(PDF_DIR, name)


def project(name):
    path = os.path.join(PROJECTS_DIR, name)
    if not os.path.isdir(path):
        raise SystemExit(f'Companion project not found: {path} '
                         f'(clone it next to this repo or set PROJECTS_DIR)')
    return path
