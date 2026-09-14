# Offline bridge adapter fixture

`BridgeCompletionAdapter` sends one unauthenticated request to an explicitly configured
HTTP(S) gateway origin. It owns a new client and transport for every completion.

```python
adapter = BridgeCompletionAdapter(
    base_url="https://gateway.example",
    provider="configured-provider",
    model="configured-model",
    defaults=Defaults(
        provider="configured-provider",
        model="configured-model",
        timeout=30,
        retry_attempts=1,
    ),
)
```

Offline tests use `httpx.MockTransport`; this fixture does not contact a gateway. The
endpoint does not accept `temperature`, so this adapter does not establish controlled-
temperature equivalence. `maxTokens` is a request hint, not proof of CLI enforcement.
It also does not establish gateway/model identity, upstream context isolation, authentication,
or live readiness.
