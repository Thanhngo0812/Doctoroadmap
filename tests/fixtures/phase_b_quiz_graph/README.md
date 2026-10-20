# Quiz regression fixture

Synthetic geometry examples from the in-test `Graph` model, serialized through
`JsonArtifactStore.save_parse`, `save_chunks` and `save_graph`. The three concepts
have dictionary aliases and two source sentences each, allowing five offline
questions and the assistant's quiz reference to be checked through the real
artifact loader. Graph v1 pins chunks v1 and parse v1.

This fixture replaces the deleted external doc-1 graph v45 dependency. It contains
no book extract, paid model response or held-out data. Keep it read-only during
tests; do not regenerate it from the shared artifact store.
