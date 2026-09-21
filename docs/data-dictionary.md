# Data Dictionary — Raw Layer (`data/raw/products_raw_*.json`)

Source: [DummyJSON Products API](https://dummyjson.com/docs/products) (see
[ADR 0002](adr/0002-data-source-selection.md)). Schema confirmed against a
live API sample on 2026-09-20.

## Envelope (added by the Extract stage)

| Field | Type | Description |
|---|---|---|
| `extracted_at` | string (ISO 8601, UTC) | Timestamp when the Extract script ran. |
| `source` | string (URL) | Full endpoint URL the data was pulled from. |
| `record_count` | integer | Number of product records in this snapshot (`len(products)`). |
| `products` | array of objects | The product records, schema below. |

## `products[]` — one record per product

| Field | Type | Nullable | Description | Example |
|---|---|---|---|---|
| `id` | integer | No | Product identifier. **Unique within a single snapshot only** — not stable as a long-term key across runs (see [data lineage](data-lineage.md#grain-and-identity-notes)). | `1` |
| `title` | string | No | Product name. | `"Essence Mascara Lash Princess"` |
| `description` | string | No | Free-text product description. | `"The Essence Mascara..."` |
| `category` | string | No | Product category slug. | `"beauty"` |
| `price` | float | No | Unit price in USD. | `9.99` |
| `discountPercentage` | float | No | Discount percentage (0–100). | `10.48` |
| `rating` | float | No | Average customer rating (0–5). | `2.56` |
| `stock` | integer | No | Units available. | `99` |
| `tags` | array of string | No | Freeform tags/keywords. | `["beauty", "mascara"]` |
| `brand` | string | Yes | Manufacturer/brand name. Absent for some categories (e.g. groceries). | `"Essence"` |
| `sku` | string | No | Stock-keeping unit code. | `"BEA-ESS-ESS-001"` |
| `weight` | float | No | Product weight (unit not specified by source; assume grams). | `4` |
| `dimensions.width` | float | No | Width (unit not specified by source; assume cm). | `15.14` |
| `dimensions.height` | float | No | Height. | `13.08` |
| `dimensions.depth` | float | No | Depth. | `22.99` |
| `warrantyInformation` | string | No | Warranty terms, free text. | `"1 week warranty"` |
| `shippingInformation` | string | No | Shipping terms, free text. | `"Ships in 3-5 business days"` |
| `availabilityStatus` | string (enum-like) | No | Stock availability label. Observed values include `"In Stock"`, `"Low Stock"`. | `"In Stock"` |
| `reviews[]` | array of object | No (can be empty) | Customer reviews for this product. See sub-table below. | — |
| `returnPolicy` | string | No | Return policy, free text. | `"No return policy"` |
| `minimumOrderQuantity` | integer | No | Minimum order quantity. | `48` |
| `meta.createdAt` | string (ISO 8601) | No | Record creation timestamp **on the source system** (synthetic; not the extraction date). | `"2025-10-09T14:47:01.588Z"` |
| `meta.updatedAt` | string (ISO 8601) | No | Record last-updated timestamp on the source system (synthetic; may be a future date relative to extraction — see [ADR 0002](adr/0002-data-source-selection.md)). | `"2026-05-23T11:27:41.868Z"` |
| `meta.barcode` | string | No | Synthetic barcode number. | `"5784719087687"` |
| `meta.qrCode` | string (URL) | No | URL to a synthetic QR code image. | `"https://cdn.dummyjson.com/public/qr-code.png"` |
| `images[]` | array of string (URL) | No | Product image URLs. | `["https://cdn.dummyjson.com/.../1.webp"]` |
| `thumbnail` | string (URL) | No | Thumbnail image URL. | `"https://cdn.dummyjson.com/.../thumbnail.webp"` |

## `reviews[]` — nested object

| Field | Type | Nullable | Description | Example |
|---|---|---|---|---|
| `rating` | integer | No | Reviewer's rating (1–5). | `4` |
| `comment` | string | No | Review text. | `"Very satisfied!"` |
| `date` | string (ISO 8601) | No | Review date. | `"2025-04-30T09:41:02.053Z"` |
| `reviewerName` | string | No | **Synthetic** reviewer name — not a real person. | `"Lucas Gordon"` |
| `reviewerEmail` | string | No | **Synthetic** reviewer email (`@x.dummyjson.com` domain) — not real PII. | `"lucas.gordon@x.dummyjson.com"` |

> **Privacy note**: `reviewerName`/`reviewerEmail` look like PII but are
> generated placeholder data from DummyJSON, not real individuals. No PII
> handling/masking is required for this dataset, but the fields are flagged
> here in case the pipeline is later pointed at a real data source with the
> same shape.

## Known data quality considerations (for the Transform stage)
- `brand` is missing for some categories — do not assume it is always present.
- `discountPercentage` and `rating` are floats but bounded (0–100 and 0–5
  respectively); worth a range check.
- `weight` and `dimensions` have no documented unit in the source API —
  treat as dimensionless/relative unless the source clarifies.
- `id` is only unique per snapshot, not across snapshots over time (see
  [data lineage](data-lineage.md)).
