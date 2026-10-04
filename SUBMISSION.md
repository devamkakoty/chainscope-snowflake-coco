# ChainScope - Submission Copy

**Problem statement:** 05 - Supply Chain Ontology and Governed Conversational Analytics  
**Event:** Snowflake CoCo CLI Hackathon GCC Edition  
**Owner-provided deadline:** October 4, 2026, 23:59 IST  
**Status:** Draft package prepared; not published or submitted

## Short Description

I built ChainScope to turn disconnected supply-chain signals into governed,
source-linked answers. It connects suppliers, parts, plants, shipments, orders
and customers through explicit relationships. A buyer-facing late-order answer
comes with the approved metric, calculation and inspectable source records,
not just a plausible sentence.

## Problem and Solution

A late inbound shipment matters when it threatens a specific customer
commitment. Traditional dashboards often separate supplier performance,
inventory and order risk, while unconstrained conversational tools can mix
metric definitions or disclose commercial information.

ChainScope demonstrates seven deterministic questions over a synthetic GCC
manufacturing network. Explicit shipment-to-order allocations connect supply
issues to affected commitments. Operations users can inspect delivery and
inventory evidence; a separate commercial role exposes gross open-order value.
Unsupported questions and unauthorized financial requests are refused.

## What Is Working

- A local web control room and CLI, both runnable with Python's standard library.
- Seven metric contracts with explicit grain, approved SQL and record citations.
- Six-entity interactive ontology with inventory, sourcing and allocation bridges.
- Role-aware source redaction, pre-query checks and session decision audit.
- Reproducible synthetic data with checksum manifest.
- GitHub Pages-ready static replay, explicitly labeled public and illustrative.
- Automated local metric, data-integrity, API and browser checks.

The synthetic snapshot contains **163 records**, including **32 shipments** and
**14 orders**. Results include **5 overdue inbound shipments**, **4 at-risk
orders**, **55.2% supplier on-time delivery**, **41.6% unit fill** and
**USD 67,050.00 in gross open-order exposure**. These are demonstration results,
not measured client outcomes or realized revenue.

## Snowflake and CoCo Technical Path

I included Snowflake setup SQL, reproducible load SQL, shared calculation views,
native Cortex Analyst-compatible Semantic Views, separate operations/commercial
object grants, and positive/negative validation queries. CoCo CLI review and
account-validation prompts are provided with an explicit plan-mode workflow.

**Important status:** I have not yet run this package against a Snowflake
account or executed the supplied CoCo workflow. The local copilot is
deterministic, not an LLM. Native semantic views follow current official
documentation but still need account compilation and result verification.
The static demo replays public precomputed synthetic fixtures, not live queries.

## Evaluation Alignment

| Criterion | Demonstrated evidence |
|---|---|
| Real-world relevance, 30% | Trace a late supply commitment to specific open customer demand; preserve commercial boundaries |
| Technical execution, 40% | Explicit ontology, shared deterministic SQL, fanout-safe line risk, source citations, semantic views and tests |
| Completeness, 30% | Runnable app and CLI, static demo package, synthetic data provenance, screenshots, deployment runbook and honest limitations |

Weights and deadline are supplied by the owner; no independent organizer
eligibility or completion claim is made here.

## 90-Second Pitch

"A late shipment is not yet an explanation. ChainScope shows which customer
commitment it threatens, how the metric was calculated, and the exact source
records behind the answer.

Here are five overdue inbound shipments. I trace ORD-013 through its allocated
shipment, part and plant to the customer. The order is still open, and the
inbound allocation gives us an explicit risk trigger rather than a guessed join.

An operations analyst can inspect those records, but financial exposure is
denied. The commercial demo identity sees USD 67,050 in gross open-order
exposure, not a prediction of loss. The audit records both decisions.

Everything here is synthetic and runnable locally. I also provide Snowflake
Semantic Views, role grants and a CoCo validation workflow. Account-side
execution is the next verification step, not a result I am claiming today."

## Submission Checklist

- [x] Source, local run instructions and reproducible synthetic scenario.
- [x] Metric definitions, source evidence, Snowflake assets and tests.
- [x] Static deployable `docs/` package and concise submission copy.
- [ ] Owner reviews final submission fields and organizer requirements.
- [ ] Actual Snowflake and CoCo validation, if account access becomes available.
- [ ] Owner-authorized repository/demo publication and video upload.
- [ ] Owner enters actual URLs and submits before the deadline.

No repository URL, hosted demo URL, video, Snowflake query ID or CoCo receipt
has been invented. Use only actual owner-approved links in the submission form.
