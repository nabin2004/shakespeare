"""In-process label index over generated ontology Turtle for alignment (STRUCTSENSE alignment-agent substitute)."""

from __future__ import annotations

from pathlib import Path

from rdflib import Graph, OWL, RDF, RDFS, URIRef


class OntologyIndex:
    def __init__(self, graph: Graph) -> None:
        self._g = graph

    @classmethod
    def from_turtle(cls, path: Path | str) -> "OntologyIndex":
        g = Graph()
        g.parse(path, format="turtle")
        return cls(g)

    @classmethod
    def from_path_auto(cls, path: Path | str) -> "OntologyIndex":
        p = Path(path)
        fmt = "turtle" if p.suffix.lower() in {".ttl", ".turtle"} else "xml"
        g = Graph()
        g.parse(path, format=fmt)
        return cls(g)

    def class_labels(self) -> dict[str, str]:
        """Map class URI string -> best label."""
        out: dict[str, str] = {}
        for cls_uri in self._g.subjects(RDF.type, OWL.Class):
            if not isinstance(cls_uri, URIRef):
                continue
            u = str(cls_uri)
            labels = list(self._g.objects(cls_uri, RDFS.label))
            if labels:
                out[u] = str(labels[0])
        return out

    def best_class_match(self, mention: str) -> tuple[str | None, float]:
        """Return (class_uri, score) for a simple case-insensitive substring match over class labels."""
        m = mention.strip().lower()
        if not m:
            return None, 0.0
        best_uri: str | None = None
        best_score = 0.0
        for uri, lab in self.class_labels().items():
            ll = lab.lower()
            if m == ll:
                score = 1.0
            elif m in ll or ll in m:
                score = 0.75
            else:
                continue
            if score > best_score:
                best_score = score
                best_uri = uri
        return best_uri, best_score
