Dear Editors,

Please consider our Article, "Query-certified operator learning for topology-indexed responses", for publication in Nature Computational Science.

Scientific models are often reused under inputs or structures that differ from those observed during fitting. In evolving networks, a representation may reproduce observed trajectories yet discard the topology argument required to evaluate a changed network. We formulate this mismatch as a computational question: does the requested topology-indexed response factor through the retained representation?

The manuscript introduces query-certified operator learning. For row-separable finite-basis operators, an exact kernel and row-space criterion determines whether a retained object supports a complete topology-indexed endpoint. The theorem covers one- and two-hop bases, establishes a strict family inclusion on the declared topology domain and supplies constructive inverses under explicit structure: whenever the criterion holds, responses of the fitted operator `M_{k,t}(W)=A_{k,t}+B_{k,t}W` remain computable on the supplied topology argument. The criterion turns downstream computability into a property that can be checked before numerical recovery is claimed.

Controlled experiments evaluate recovery only after endpoint availability has been assigned. Each primary scale, N = 15 and N = 30, uses 20 replications. A separated CP implementation reduced median effective-operator error by 93.6% and 96.8% relative to unrestricted local rolling estimation. Median finite-horizon unit-shock response error decreased by 82.5% and 87.3% under the same target-matched comparison. CP is the implementation layer; the contribution is a representation-level contribution: the criterion and its query-specific qualification sequence attached to each fitted representation.

The work addresses a broad computational science problem because learned scientific objects are increasingly compressed, regularized and reused under changed inputs or structures. Query certification supplies a concrete design rule: preserve the arguments required by the downstream computation, provide a verified inverse or mark the query unavailable. Under this rule, topology-substitution readouts remain available exactly when the retained object keeps the supplied topology argument callable, which makes the network setting an exact, testable and computationally consequential instance of representation-level design.

Competing-interest and AI-use disclosures accompany the manuscript draft.

Sincerely,

Yilin Wu
