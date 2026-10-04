# Data access findings

The existing FactSet Formula subscription returned usable current gold futures prices for GCZ26-USA and related active identifiers. A longer probe of timed contracts from 2006 through 2027 returned null histories for expired contracts. Only three of 236 proposed monthly intervals had both marks. This is not a validated historical rolled-futures panel.

The Formula field was P_PRICE. Naming its output settlement does not establish settlement semantics; the private prototype's column alias must not be treated as a verified exchange settlement. No historical futures P&L enters the reported models.

FactSet's historical option chains and prices endpoints returned HTTP 403 with an explicit permission denial for the existing client. No additional subscription was purchased. Gold and silver option simulations therefore use hypothetical paid premiums, not observed executions.

Registered Yahoo adjusted-close histories support the financed bullion implementation. Private snapshots include explicit-date requests, hashes and coverage. SEC companyfacts supplies public annual financial facts with filing dates and accession numbers; nonstandard issuer tags and older foreign histories are incomplete.
