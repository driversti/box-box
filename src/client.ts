// F1 Live Timing SignalR Client
// Connects to the official F1 live timing stream and collects data

import WebSocket from "ws";
import { inflateRawSync } from "zlib";

// --- Config ---
const SIGNALR_NEGOTIATE_URL =
  "https://livetiming.formula1.com/signalr/negotiate";
const SIGNALR_WS_URL = "wss://livetiming.formula1.com/signalr/connect";
const HUB = "Streaming";
const CLIENT_PROTOCOL = "1.5";

const TOPICS = [
  "Heartbeat",
  "CarData.z",
  "Position.z",
  "ExtrapolatedClock",
  "TopThree",
  "RcmSeries",
  "TimingStats",
  "TimingAppData",
  "WeatherData",
  "TrackStatus",
  "DriverList",
  "RaceControlMessages",
  "SessionInfo",
  "SessionData",
  "LapCount",
  "TimingData",
];

// --- Types ---
interface NegotiateResponse {
  ConnectionToken: string;
  ConnectionId: string;
  KeepAliveTimeout: number;
  DisconnectTimeout: number;
  TryWebSockets: boolean;
  ProtocolVersion: string;
}

interface SignalRMessage {
  C?: string; // cursor
  S?: number; // state
  M?: SignalREvent[]; // messages
}

interface SignalREvent {
  H: string; // hub
  M: string; // method
  A: string[]; // arguments (JSON strings)
}

// --- Decompression ---
function decompressZ(data: string): string {
  const raw = Buffer.from(data, "base64");
  const decompressed = inflateRawSync(raw);
  return decompressed.toString("utf-8");
}

// --- Negotiate ---
async function negotiate(): Promise<{
  token: string;
  cookie: string;
}> {
  const hubData = encodeURIComponent(JSON.stringify([{ name: HUB }]));
  const url = `${SIGNALR_NEGOTIATE_URL}?connectionData=${hubData}&clientProtocol=${CLIENT_PROTOCOL}`;

  console.log("🔄 Negotiating connection...");

  const resp = await fetch(url);
  if (!resp.ok) {
    throw new Error(`Negotiate failed: ${resp.status} ${resp.statusText}`);
  }

  const data = (await resp.json()) as NegotiateResponse;
  const cookie = resp.headers.get("set-cookie") || "";

  console.log(`✅ Got token: ${data.ConnectionToken.substring(0, 20)}...`);
  console.log(`   ConnectionId: ${data.ConnectionId}`);

  return {
    token: data.ConnectionToken,
    cookie,
  };
}

// --- WebSocket Client ---
class F1LiveTimingClient {
  private ws: WebSocket | null = null;
  private dataHandler: (topic: string, data: unknown) => void;

  constructor(
    onData: (topic: string, data: unknown) => void,
  ) {
    this.dataHandler = onData;
  }

  async connect(): Promise<void> {
    const { token, cookie } = await negotiate();

    const hubData = encodeURIComponent(JSON.stringify([{ name: HUB }]));
    const encodedToken = encodeURIComponent(token);
    const url = `${SIGNALR_WS_URL}?clientProtocol=${CLIENT_PROTOCOL}&transport=webSockets&connectionToken=${encodedToken}&connectionData=${hubData}`;

    console.log("🔌 Connecting to WebSocket...");

    this.ws = new WebSocket(url, {
      headers: {
        "User-Agent": "BestHTTP",
        "Accept-Encoding": "gzip,identity",
        Cookie: cookie,
      },
    });

    return new Promise((resolve, reject) => {
      this.ws!.on("open", () => {
        console.log("✅ WebSocket connected!");
        this.subscribe();
        resolve();
      });

      this.ws!.on("message", (raw: Buffer) => {
        this.handleMessage(raw.toString());
      });

      this.ws!.on("error", (err: Error) => {
        console.error("❌ WebSocket error:", err.message);
        reject(err);
      });

      this.ws!.on("close", (code: number, reason: Buffer) => {
        console.log(`🔌 Disconnected: ${code} ${reason.toString()}`);
      });
    });
  }

  private subscribe(): void {
    const msg = {
      H: HUB,
      M: "Subscribe",
      A: [TOPICS],
      I: 1,
    };

    console.log(`📡 Subscribing to ${TOPICS.length} topics...`);
    this.ws!.send(JSON.stringify(msg));
  }

  private handleMessage(raw: string): void {
    if (!raw || raw === "{}") return;

    try {
      const msg: SignalRMessage = JSON.parse(raw);

      if (msg.M && msg.M.length > 0) {
        for (const event of msg.M) {
          if (event.M === "feed") {
            // Feed events: event.A = [topic, jsonData]
            const topic = event.A[0];
            let data = event.A[1];

            // Decompress .z topics
            if (topic.endsWith(".z")) {
              try {
                data = JSON.parse(decompressZ(data as string));
              } catch (e) {
                console.warn(`⚠️ Failed to decompress ${topic}`);
              }
            } else if (typeof data === "string") {
              try {
                data = JSON.parse(data);
              } catch {
                // keep as string
              }
            }

            this.dataHandler(topic, data);
          }
        }
      }
    } catch {
      // Non-JSON message (keepalive, etc.)
    }
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

// --- Main ---
async function main() {
  console.log("🏎️ Box-Box F1 Live Timing Client");
  console.log("================================\n");

  const stats = {
    messages: 0,
    topics: {} as Record<string, number>,
    startTime: Date.now(),
  };

  const client = new F1LiveTimingClient((topic, data) => {
    stats.messages++;
    stats.topics[topic] = (stats.topics[topic] || 0) + 1;

    // Log every message (truncate large payloads)
    const json = JSON.stringify(data);
    const preview = json.length > 200 ? json.substring(0, 200) + "..." : json;
    console.log(`📥 [${topic}] ${preview}`);
  });

  // Graceful shutdown
  process.on("SIGINT", () => {
    console.log("\n\n📊 Session Summary:");
    console.log(`   Duration: ${((Date.now() - stats.startTime) / 1000).toFixed(1)}s`);
    console.log(`   Messages: ${stats.messages}`);
    console.log("   By topic:");
    for (const [topic, count] of Object.entries(stats.topics).sort(
      (a, b) => b[1] - a[1],
    )) {
      console.log(`     ${topic}: ${count}`);
    }
    client.disconnect();
    process.exit(0);
  });

  try {
    await client.connect();
    console.log("\n🎯 Listening for data... (Ctrl+C to stop)\n");
  } catch (err) {
    console.error("Failed to connect:", err);
    process.exit(1);
  }
}

main();
