import pytest
from urllib import parse
from iiif.resources import Manifest, ResourceFactory


@pytest.fixture
def factory():
    return ResourceFactory()


@pytest.fixture
def a_manifest(factory):
    uri = 'https://figgy.princeton.edu/concern/scanned_resources/a3b5a622-8608-4a05-91cb-bc3840a44ef9/manifest'
    return factory.manifest(uri)


def test_label(a_manifest):
    assert a_manifest.label == "Index of Permanent Files"


def test_id(a_manifest):
    '''The identifier in @id must always be able to be dereferenced to retrieve the JSON description of the manifest, and thus must use the http(s) URI scheme.'''
    assert parse.urlparse(a_manifest.id).scheme in ['http', 'https']


def test_sequences(a_manifest):
    assert len(a_manifest.sequences) > 0


def test_metadata(a_manifest):
    assert a_manifest.metadata['Title'] == 'Index of Permanent Files'
