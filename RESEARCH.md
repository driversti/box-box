# Box-Box Research Notes

## SignalR Protocol

### Authentication
F1TV subscription required. The live timing endpoint doesn't require explicit auth tokens for basic data streams. For replay sessions, the SignalR Core endpoint is used.

### Data Format
- JSON messages over WebSocket
- `.z` streams: base64 encoded → zlib deflate decompressed → JSON
- Messages contain incremental updates (not full state)

### Message Structure
```json
{
  "H": "Streaming",    // Hub name
  "M": "Subscribe",    // Method name
  "A": [["Topic1", "Topic2"]],  // Arguments (array of arrays)
  "I": 1               // Request ID
}
```

### Replay (Past Sessions)
SignalR Core protocol (v2):
- Negotiate: `https://livetiming.formula1.com/signalrcore/negotiate?negotiateVersion=1`
- WebSocket: `wss://livetiming.formula1.com/signalrcore`
- Session key format: `/{season}/{round}/{session_type}` (e.g., `/2026/3/R`)

### Data Decompression (Python)
```python
import base64, zlib
import json

def decompress_z(data: str) -> dict:
    raw = base64.b64decode(data)
    decompressed = zlib.decompress(raw, -zlib.MAX_WBITS)
    return json.loads(decompressed)
```

### Data Decompression (TypeScript)
```typescript
function decompressZ(data: string): any {
  const raw = atob(data);
  const bytes = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i++) bytes[i] = raw.charCodeAt(i);
  const decompressed = new DecompressionStream('deflate-raw');
  // ... pipe through decompression stream
}
```

## References
- SignalR protocol: https://dotnet.microsoft.com/apps/aspnet/signalr
- OpenF1: https://openf1.org
- Ergast API: https://ergast.com/mrd/
- Jolpica (Ergast fork): https://github.com/jolpica/jolpica-f1
