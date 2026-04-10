# 🏎️ Box-Box

F1 Live Timing data collector and analytics platform.

Collects real-time and historical Formula 1 data from the official F1 Live Timing SignalR API.

## Data Sources

### F1 Live Timing API (SignalR)

The official F1 timing data stream, same one used by F1 TV and the F1 app.

**Endpoints:**
- Negotiate: `https://livetiming.formula1.com/signalr/negotiate`
- WebSocket: `wss://livetiming.formula1.com/signalr/connect`
- SignalR Core (replay): `wss://livetiming.formula1.com/signalrcore`

### Connection Flow

1. **Negotiate** — GET request to obtain `ConnectionToken` + cookie
   ```
   GET https://livetiming.formula1.com/signalr/negotiate
       ?connectionData=[{"name":"Streaming"}]
       &clientProtocol=1.5
   ```

2. **WebSocket** — Connect with token and specific headers
   ```
   wss://livetiming.formula1.com/signalr/connect
       ?clientProtocol=1.5
       &transport=webSockets
       &connectionToken=<token>
       &connectionData=[{"name":"Streaming"}]
   ```
   Required headers (case-sensitive!):
   - `User-Agent: BestHTTP`
   - `Accept-Encoding: gzip,identity`
   - `Cookie: <cookie from negotiate>`

3. **Subscribe** — Send subscription message
   ```json
   {
     "H": "Streaming",
     "M": "Subscribe",
     "A": [["TimingData", "CarData.z", "Position.z", ...]],
     "I": 1
   }
   ```

### Available Data Streams

| Topic | Description | Compressed |
|-------|-------------|------------|
| `TimingData` | Lap times, sectors, gaps | No |
| `TimingAppData` | Tyre data, stint info | No |
| `TimingStats` | Personal best laps | No |
| `CarData.z` | Telemetry (speed, RPM, brake, throttle, DRS) | Yes |
| `Position.z` | GPS car positions | Yes |
| `WeatherData` | Temperature, humidity, wind, rain | No |
| `RaceControlMessages` | Penalties, flags, VSC | No |
| `TrackStatus` | Green/yellow/SC/VSC/red | No |
| `DriverList` | Driver metadata, team colors | No |
| `LapCount` | Current lap / total | No |
| `SessionInfo` | Session metadata | No |
| `SessionData` | Additional session data | No |
| `TopThree` | Top 3 drivers | No |
| `Heartbeat` | Keep-alive ping | No |
| `ExtrapolatedClock` | Session clock | No |

**Note:** Topics ending in `.z` are compressed with **base64 + zlib deflate**.

## Roadmap

- [ ] SignalR client connection
- [ ] Data stream parser
- [ ] Replay support for past sessions
- [ ] Data storage (SQLite/CSV)
- [ ] Analytics scripts
- [ ] Dashboard

## Requirements

- F1TV subscription (for live timing access)
- Python 3.11+ or Bun/Node.js

## License

MIT
