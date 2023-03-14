import pytest
from urllib import parse
from iiif.resources import ResourceFactory, Manifest, Sequence, Canvas


@pytest.fixture
def a_manifest():
    uri = 'https://figgy.princeton.edu/concern/scanned_resources/a3b5a622-8608-4a05-91cb-bc3840a44ef9/manifest'
    return ResourceFactory().manifest(uri)


@pytest.fixture
def a_canvas(a_manifest):
    return a_manifest.sequences[0].canvases[0]


def test_id(a_canvas):
    '''The identifier in @id must always be able to be dereferenced to retrieve the JSON description of the manifest, and thus must use the http(s) URI scheme.'''
    assert parse.urlparse(a_canvas.id).scheme in ['http', 'https']


def test_label(a_canvas):
    assert a_canvas.label == '1'


def test_name(a_canvas):
    assert a_canvas.name == '2ae6db12-575c-4708-a8a9-8b8408c171b7'


def test_height(a_canvas):
    assert a_canvas.height == int(4700)


def test_width(a_canvas):
    assert a_canvas.width == int(3677)


def test_images(a_canvas):
    image_annotations = a_canvas.images
    assert len(image_annotations) == 1
    image = image_annotations[0]
    assert (
        image.resource
        == 'https://iiif-cloud.princeton.edu/iiif/2/33%2F4f%2F82%2F334f828b1c7f44ecb18c7c0d55fec740%2Fintermediate_file/full/1000,/0/default.jpg'
    )
