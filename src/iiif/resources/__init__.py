from rdflib import Graph, Namespace, URIRef
import rdflib
from rdflib.namespace._DC import DC
from rdflib.namespace._DCTERMS import DCTERMS
from rdflib.namespace._DOAP import DOAP
from rdflib.namespace._FOAF import FOAF
from rdflib.namespace._RDF import RDF
from rdflib.namespace._RDFS import RDFS
from rdflib.namespace._XSD import XSD
from rdflib.plugins.shared.jsonld.context import Context
from rdflib.plugins.sparql.processor import prepareQuery
import json


SC = Namespace("http://iiif.io/api/presentation/2#")
IIIF = Namespace("http://iiif.io/api/image/2#")
EXIF = Namespace("http://www.w3.org/2003/12/exif/ns#")
OA = Namespace("http://www.w3.org/ns/oa#")
CNT = Namespace("http://www.w3.org/2011/content#")
DCTYPES = Namespace("http://purl.org/dc/dcmitype/")
SVCS = Namespace("http://rdfs.org/sioc/services#")
AS = Namespace("http://www.w3.org/ns/activitystreams#")


def rdflist2list(graph, node):
    return rdflist2list1(graph, node, [])


def rdflist2list1(graph, node, acc):
    head = graph.value(node, RDF.first)
    acc.append(head)
    if (tail := graph.value(node, RDF.rest)) == RDF.nil:
        return acc
    else:
        return rdflist2list1(graph, tail, acc)


class ResourceFactory:
    manifest_namespaces = {
        "sc": Namespace("http://iiif.io/api/presentation/2#"),
        "iiif": Namespace("http://iiif.io/api/image/2#"),
        "exif": Namespace("http://www.w3.org/2003/12/exif/ns#"),
        "oa": Namespace("http://www.w3.org/ns/oa#"),
        "cnt": Namespace("http://www.w3.org/2011/content#"),
        "dc": DC,
        "dcterms": DCTERMS,
        "dctypes": Namespace("http://purl.org/dc/dcmitype/"),
        "doap": DOAP,
        "foaf": FOAF,
        "rdf": RDF,
        "rdfs": RDFS,
        "xsd": XSD,
        "svcs": Namespace("http://rdfs.org/sioc/services#"),
        "as": Namespace("http://www.w3.org/ns/activitystreams#"),
    }

    def manifest(self, uri):
        graph: rdflib.Graph = Graph()
        [graph.bind(k, v) for k, v in self.manifest_namespaces.items()]
        graph.parse(
            uri,
            format='json-ld',
            context="http://iiif.io/api/presentation/2/context.json",
        )
        manifest_ref: URIRef = next(graph.subjects(RDF.type, SC.Manifest))
        return Manifest(manifest_ref, graph)


class Resource:
    def __init__(self, ref: URIRef, graph: Graph):
        self.ref = ref
        self.graph = graph

    def as_jsonld(self):
        g = Graph()
        g += self.graph.triples((self.ref, None, None))
        return json.loads(g.serialize(format="json-ld"))

    @property
    def id(self):
        return str(self.ref)

    @property
    def type(self):
        return str(self.graph.value(self.ref, RDF.type))

    @property
    def label(self) -> str:
        return str(self.graph.value(self.ref, RDFS.label))


class Manifest(Resource):
    def __init__(self, ref: URIRef, graph: Graph):
        super().__init__(ref, graph)
        self._canvases = None
        self._sequences = None

    def __repr__(self) -> str:
        return f"Manifest({self.label})"

    @property
    def label(self) -> str:
        return str(self.graph.value(self.ref, RDFS.label))

    @property
    def sequences(self):
        if self._sequences is None:
            BNode = next(
                self.graph.objects(subject=self.ref, predicate=SC.hasSequences)
            )
            self._sequences = [
                Sequence(s, self.graph) for s in rdflist2list(self.graph, BNode)
            ]
        return self._sequences

    @property
    def metadata(self):
        def convert_list(graph, node, acc=[]):
            head = graph.value(node, RDF.first)
            label = graph.value(head, RDFS.label)
            value = graph.value(head, RDF.value)
            acc.append(list((str(label), str(value))))
            if (tail := graph.value(node, RDF.rest)) == RDF.nil:
                return acc
            return convert_list(graph, tail, acc)

        manifest = self.graph.value(predicate=RDF.type, object=SC.Manifest)
        metadata_list = self.graph.value(subject=manifest, predicate=SC.metadataLabels)
        return {k: v for (k, v) in convert_list(self.graph, metadata_list)}


class Sequence(Resource):
    def __init__(self, ref: URIRef, graph: Graph):
        super().__init__(ref, graph)
        self._canvases = None

    def __repr__(self) -> str:
        return f"Sequence({self.name})"

    @property
    def name(self) -> str:
        '''The name of a Sequence is derived from the Sequence's
        id (a URI), which has a specified structure; the name is
        the last unit in the URI.
        '''
        return str(self.ref).split('/')[-1]

    @property
    def canvases(self):
        if self._canvases is None:
            canvas_list = next(self.graph.objects(self.ref, SC.hasCanvases))
            self._canvases = [
                Canvas(c, self.graph) for c in rdflist2list(self.graph, canvas_list)
            ]
        return self._canvases


class Canvas(Resource):
    def __init__(self, ref: URIRef, graph: Graph):
        super().__init__(ref, graph)

    def __repr__(self) -> str:
        return f"Canvas({self.label})"

    @property
    def name(self) -> str:
        '''The name of a Canvas is derived from the Canvas's
        id (a URI), which has a specified structure; the name is
        the last unit in the URI.
        '''
        return str(self.ref).split('/')[-1]

    @property
    def height(self) -> int:
        term = next(self.graph.objects(self.ref, EXIF.height))
        return int(term)

    @property
    def width(self) -> int:
        term = next(self.graph.objects(self.ref, EXIF.width))
        return int(term)

    # The Figgy manifests do not follow the specification for
    # associating images with a Canvas.  Where the spec says images
    # are simply annotations with the painting motivation, these
    # manifests use the sc:hasImageAnnotations property
    @property
    def images(self):
        q = prepareQuery(
            '''SELECT ?image
            WHERE
            {
            ?canvas sc:hasImageAnnotations ?list .
            ?list rdf:rest*/rdf:first ?image .
            }''',
            initNs={"rdf": RDF, "sc": SC},
        )

        q_result = self.graph.query(q, initBindings={"canvas": self.ref})
        images = [r['image'] for r in q_result]
        return [Image(iref, self.graph) for iref in images]


class Annotation(Resource):
    def __init__(self, ref: URIRef, graph: Graph):
        super().__init__(ref, graph)

    @property
    def body(self):
        return next(self.graph.objects(self.ref, OA.hasBody))

    @property
    def target(self):
        return next(self.graph.objects(self.ref, OA.hasTarget))

    @property
    def resource(self):
        return str(self.body)


class Image(Annotation):
    def __init__(self, ref: URIRef, graph: Graph):
        super().__init__(ref, graph)
