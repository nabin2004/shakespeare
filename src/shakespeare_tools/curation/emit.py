"""Serialize approved rows to RDF (TriG for named graph IRIs)."""

from __future__ import annotations

from rdflib import XSD, Dataset, Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS

from shakespeare_tools.curation.models import ApprovedDramaticEvent, CurationDraftBundle

DCT = Namespace("http://purl.org/dc/terms/")


def expand_curie(curie: str) -> str:
    if curie.startswith("http://") or curie.startswith("https://"):
        return curie
    if ":" not in curie:
        return f"https://w3id.org/shakespeare-crm/{curie}"
    ns, rest = curie.split(":", 1)
    if ns == "sc":
        return f"https://w3id.org/shakespeare-crm/{rest}"
    if ns == "crm":
        return f"http://www.cidoc-crm.org/cidoc-crm/{rest}"
    raise ValueError(f"Unsupported CURIE prefix: {curie}")


def _add_dramatic_event(g: Graph, ev: ApprovedDramaticEvent) -> None:
    node = URIRef(expand_curie(ev.id))
    tbox_event = URIRef("https://w3id.org/shakespeare-crm/DramaticEvent")
    tbox_in_work = URIRef("https://w3id.org/shakespeare-crm/in_work")
    tbox_motif = URIRef("https://w3id.org/shakespeare-crm/motif_type")
    tbox_act = URIRef("https://w3id.org/shakespeare-crm/dramatic_act")
    tbox_scene = URIRef("https://w3id.org/shakespeare-crm/dramatic_scene")
    tbox_anchor = URIRef("https://w3id.org/shakespeare-crm/line_anchor")
    tbox_speaker = URIRef("https://w3id.org/shakespeare-crm/speaker_label")
    p11 = URIRef("http://www.cidoc-crm.org/cidoc-crm/P11_had_participant")
    g.add((node, RDF.type, tbox_event))
    g.add((node, RDFS.label, Literal(ev.label)))
    g.add((node, tbox_in_work, URIRef(expand_curie(ev.in_work))))
    if ev.motif_type:
        g.add((node, tbox_motif, Literal(ev.motif_type)))
    for part in ev.p11_had_participant:
        g.add((node, p11, URIRef(expand_curie(part))))
    g.add((node, DCT.provenance, Literal(ev.evidence_span_id)))
    if ev.dramatic_act is not None:
        g.add((node, tbox_act, Literal(ev.dramatic_act, datatype=XSD.integer)))
    if ev.dramatic_scene is not None:
        g.add((node, tbox_scene, Literal(ev.dramatic_scene, datatype=XSD.integer)))
    if ev.line_anchor:
        g.add((node, tbox_anchor, Literal(ev.line_anchor)))
    if ev.speaker_label:
        g.add((node, tbox_speaker, Literal(ev.speaker_label)))
    if ev.evidence_text and ev.evidence_text.strip():
        g.add((node, DCT.description, Literal(ev.evidence_text.strip())))


def bundle_to_dataset(bundle: CurationDraftBundle, instances_graph_iri: str) -> Dataset:
    ds = Dataset(default_union=True)
    ctx = URIRef(instances_graph_iri)
    ng = ds.graph(ctx)
    for ev in bundle.approved_events:
        _add_dramatic_event(ng, ev)
    return ds


def emit_trig(bundle: CurationDraftBundle, instances_graph_iri: str) -> str:
    return bundle_to_dataset(bundle, instances_graph_iri).serialize(format="trig")


def emit_turtle_flat(bundle: CurationDraftBundle) -> str:
    flat = Graph()
    for ev in bundle.approved_events:
        _add_dramatic_event(flat, ev)
    return flat.serialize(format="turtle")
