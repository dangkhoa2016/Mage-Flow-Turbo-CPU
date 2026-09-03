# REST API

The loopback REST service exposes the generic native inference core. It binds to `127.0.0.1` by default; public exposure stays a separate authenticated gateway that is not part of qualification.

## Endpoints

```text
GET  /healthz
GET  /readyz
GET  /v1/info
POST /v1/images/generate
GET  /v1/artifacts/<png>
```

## Start the service

```bash
mageflow-native serve --manifest configs/mage-flow-turbo-q8-reference.json \
    --backend cuda0 --host 127.0.0.1 --port 8090
```

## GET /healthz

```json
{ "status": "ok", "service": "mage-flow-turbo-native-inference" }
```

## GET /readyz

```json
{ "ready": true, "busy": false, "generation_concurrency": 1 }
```

Returns `503` when not ready or shutting down.

## GET /v1/info

Returns service identity, backend, the pinned runtime commit, frozen model hashes and single-flight status.

## POST /v1/images/generate

Body (JSON):

```json
{
  "prompt": "A small red fox in a quiet green forest",
  "seed": 42,
  "client_request_id": "optional-safe-id",
  "backend": "cpu",
  "params_backend": "cpu"
}
```

Validation:

- `prompt`: non-empty UTF-8 string, max 2000 characters
- `seed`: integer in `[0, 2^32-1]`
- `client_request_id`: 1..128 characters from `[A-Za-z0-9._-]`
- `backend`/`params_backend`: simple (`auto`, `cpu`, `cuda0`) or validated placement strings
- unknown fields are rejected

Success:

```json
{
  "status": "succeeded",
  "request_id": "...",
  "width": 512,
  "height": 512,
  "seed": 42,
  "elapsed_ms": 1234,
  "artifact": { "filename": "x.png", "bytes": 0, "sha256": "...", "width": 512, "height": 512 },
  "artifact_url": "/v1/artifacts/x.png"
}
```

Errors: `400 INVALID_REQUEST`, `409 BUSY_SINGLE_FLIGHT` (single-flight), `504 REQUEST_TIMEOUT`, `500 INFERENCE_FAILED`.

## GET /v1/artifacts/<png>

Serves a generated PNG. Accepts only a safe basename ending in `.png`; path traversal is rejected.

## Security

- The service binds loopback by default.
- Non-loopback bind requires an explicit opt-in flag/env and is not used by qualification.
- Public gateway remains outside the inference server.
