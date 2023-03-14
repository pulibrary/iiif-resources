import pytest
from urllib import parse
from iiif.resources import ResourceFactory, Manifest, Sequence, Canvas, Annotation
from rdflib import URIRef


@pytest.fixture
def a_manifest():
    uri = 'https://figgy.princeton.edu/concern/scanned_resources/a3b5a622-8608-4a05-91cb-bc3840a44ef9/manifest'
    return ResourceFactory().manifest(uri)


@pytest.fixture
def a_canvas(a_manifest):
    return a_manifest.sequences[0].canvases[0]


@pytest.fixture
def an_annotation(a_canvas):
    return a_canvas.images[0]


@pytest.fixture
def a_body():
    return URIRef(
        'https://iiif-cloud.princeton.edu/iiif/2/33%2F4f%2F82%2F334f828b1c7f44ecb18c7c0d55fec740%2Fintermediate_file/full/1000,/0/default.jpg'
    )


def test_body(an_annotation, a_body):
    assert an_annotation.body == a_body


def test_target(an_annotation, a_canvas):
    assert an_annotation.target == a_canvas.ref
