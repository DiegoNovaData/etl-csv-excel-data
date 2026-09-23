# 0004. Data contracts as YAML (Data Contract Specification)

## Status
Accepted

## Context
The Load layer (`data/output/*.csv`) is meant to be consumed by other tools
or people, and eventually loaded into a real database (see
[docs/entity-relationship-diagram.md](../entity-relationship-diagram.md)).
It needs an explicit, versioned description of its schema and quality rules
— not just "read the code to find out".

## Decision
Describe each output table (`products`, `product_reviews`, `product_tags`,
`product_images`) as a YAML file in [`contracts/`](../../contracts/),
following the open [Data Contract Specification](https://datacontract.com)
(`dataContractSpecification: 1.1.0`). Each contract documents fields, types,
nullability, primary/foreign keys, and a plain-language summary of the
quality rules enforced by Great Expectations
([ADR 0005](0005-data-quality-great-expectations.md)).

## Consequences
- The contracts are **documentation, not automatically enforced**: nothing
  in the pipeline parses `contracts/*.yaml` today and fails the build if the
  code drifts from it. Enforcement lives in
  [`src/quality/expectations.py`](../../src/quality/expectations.py) and
  must be kept in sync with the contract by hand.
- **Known technical debt / next step**: migrate the contracts' field
  definitions into Pydantic models used directly by the Transform stage, so
  the "contract" and the "runtime validation" become the same artifact and
  cannot drift apart. Recorded here deliberately so it isn't lost as a vague
  TODO.
- Chosen over plain JSON Schema because the Data Contract Specification also
  captures ownership, status, and quality expectations in one place — closer
  to how data contracts are used on real data platform teams, and a term
  recognizable to clients/reviewers evaluating this portfolio.
