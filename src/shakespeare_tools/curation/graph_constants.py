"""Named graph IRIs and vocabulary namespaces for curation emit."""

from rdflib import Namespace

# Convention until Phase 0 locks IRIs in schema docs (see docs/CURATION_PIPELINE.md).
INSTANCE_GRAPH_IRI = "https://w3id.org/shakespeare-crm/graph/instances"
ONTOLOGY_GRAPH_IRI = "https://w3id.org/shakespeare-crm/graph/ontology"

SC = Namespace("https://w3id.org/shakespeare-crm/")
CRM = Namespace("http://www.cidoc-crm.org/cidoc-crm/")
RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
