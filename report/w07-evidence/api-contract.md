# W-07 API contract

The learning routes derive the learner from the authenticated session and the document/version from the member course. Requests cannot supply or override `owner`, `doc_id`, or graph version.

## `GET /api/v1/courses/{cid}/progress`

Returns the existing `progress-1` response plus `course_id`:

```json
{
  "course_id": "<course UUID>",
  "contract_version": "progress-1",
  "doc_id": "doc-1",
  "nodes": {
    "<node_id>": {
      "state": "not_learned",
      "source": null,
      "updated_at": null
    }
  },
  "modules": [
    {"module_id": "<module_id>", "learned": 0, "total": 1}
  ]
}
```

`nodes` contains only learnable nodes in the course's published graph. `source` is `null`, `learner`, or `quiz` as defined by `progress-1`.

## `PUT /api/v1/courses/{cid}/progress/{node_id}`

Accepts exactly `{"learned": true}` or `{"learned": false}`. Extra properties and non-boolean values are rejected. The response is the full `GET .../progress` shape after the write.

Private courses and unknown/non-learnable node IDs return the standard `not_found` envelope. Both operations are bound to the authenticated actor, course document, and published graph version.

## `GET /api/v1/courses/{cid}/roadmap`

Retains the W-06 response and adds a top-level `progress: {"learned": number, "total": number}` plus the same `progress` summary to each module. Concept ordering follows the published module's `node_ids` sequence; only learnable nodes are included. Existing concept fields remain unchanged.
