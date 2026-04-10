// Box-Box: F1 Data Fetcher
// Downloads session data from F1's static timing API

import { mkdirSync, writeFileSync, existsSync } from "fs";
import { join } from "path";
import { inflateRawSync } from "zlib";

const BASE_URL = "https://livetiming.formula1.com/static";

// --- Types ---
interface SessionIndex {
  Feeds: Record<
    string,
    {
      KeyFramePath: string;
      StreamPath: string;
    }
  >;
}

interface Meeting {
  Key: number;
  Code: string;
  Number: number;
  Location: string;
  OfficialName: string;
  Name: string;
  Country: { Key: number; Code: string; Name: string };
  Circuit: { Key: number; ShortName: string };
  Sessions: SessionInfo[];
}

interface SessionInfo {
  Key: number;
  Type: string;
  Number?: number;
  Name: string;
  StartDate: string;
  EndDate: string;
  GmtOffset: string;
  Path: string;
}

interface SeasonIndex {
  Year: number;
  Meetings: Meeting[];
}

type OutputFormat = "json" | "jsonStream" | "both";

// --- Helpers ---
function parseJsonWithBOM(text: string): unknown {
  // F1 API sometimes returns BOM
  return JSON.parse(text.replace(/^\uFEFF/, ""));
}

function decompressZ(base64Data: string): string {
  const raw = Buffer.from(base64Data, "base64");
  const decompressed = inflateRawSync(raw);
  return decompressed.toString("utf-8");
}

function parseJsonStream(stream: string): unknown[] {
  // jsonStream format: each line is "length\x12data\n"
  const entries: unknown[] = [];
  for (const line of stream.split("\n")) {
    if (!line.trim()) continue;
    const sepIdx = line.indexOf("\x12");
    if (sepIdx === -1) {
      // Might be plain JSON
      try {
        entries.push(JSON.parse(line));
      } catch {
        // skip
      }
      continue;
    }
    const data = line.substring(sepIdx + 1);
    try {
      entries.push(JSON.parse(data));
    } catch {
      // skip malformed
    }
  }
  return entries;
}

// --- API ---
async function fetchSeason(year: number): Promise<SeasonIndex> {
  console.log(`📅 Fetching ${year} season index...`);
  const resp = await fetch(`${BASE_URL}/${year}/Index.json`);
  if (!resp.ok) throw new Error(`Season ${year} not found: ${resp.status}`);
  const text = await resp.text();
  return parseJsonWithBOM(text) as SeasonIndex;
}

async function fetchSessionIndex(sessionPath: string): Promise<SessionIndex> {
  const resp = await fetch(`${BASE_URL}/${sessionPath}Index.json`);
  if (!resp.ok) throw new Error(`Session index not found: ${resp.status}`);
  const text = await resp.text();
  return parseJsonWithBOM(text) as SessionIndex;
}

async function fetchData(
  sessionPath: string,
  feed: string,
  format: "json" | "jsonStream" = "json",
): Promise<string> {
  const suffix = format === "jsonStream" ? ".jsonStream" : ".json";
  const url = `${BASE_URL}/${sessionPath}${feed}${suffix}`;
  const resp = await fetch(url);
  if (!resp.ok) throw new Error(`Feed ${feed} not found: ${resp.status}`);
  return await resp.text();
}

// --- Commands ---
async function listSeason(year: number): Promise<void> {
  const season = await fetchSeason(year);
  console.log(`\n🏎️ ${year} Season — ${season.Meetings.length} events\n`);

  for (const meeting of season.Meetings) {
    if (meeting.Sessions[0]?.Type === "Practice" && !meeting.Sessions[0]?.Number) {
      // Testing, skip
      continue;
    }
    const race = meeting.Sessions.find((s) => s.Type === "Race" && s.Name === "Race");
    const date = race?.StartDate?.substring(0, 10) || "?";
    console.log(
      `  R${String(meeting.Number).padStart(2, "0")} ${date}  ${meeting.Name.padEnd(30)} [${meeting.Location}]`,
    );
  }
}

async function listSession(year: number, round: number): Promise<void> {
  const season = await fetchSeason(year);
  const meeting = season.Meetings.find(
    (m) => m.Number === round && !m.Code.includes("T0"),
  );
  if (!meeting) {
    console.error(`❌ Round ${round} not found in ${year}`);
    return;
  }

  console.log(`\n🏆 ${meeting.OfficialName}\n`);
  console.log(`   Location: ${meeting.Location}, ${meeting.Country.Name}`);
  console.log(`   Circuit:  ${meeting.Circuit.ShortName}\n`);
  console.log("   Sessions:");

  for (const session of meeting.Sessions) {
    const path = session.Path;
    console.log(
      `     ${session.Type.padEnd(12)} ${session.Name.padEnd(20)} ${session.StartDate.substring(0, 16)}  →  ${path}`,
    );
  }
}

async function showFeeds(sessionPath: string): Promise<void> {
  const index = await fetchSessionIndex(sessionPath);
  console.log(`\n📡 Available feeds for ${sessionPath}\n`);
  for (const [name, feed] of Object.entries(index.Feeds)) {
    console.log(`  ${name.padEnd(25)} ${feed.KeyFramePath || ""} ${feed.StreamPath || ""}`);
  }
  console.log(`\n  Total: ${Object.keys(index.Feeds).length} feeds`);
}

async function downloadSession(
  sessionPath: string,
  outputDir: string,
  feeds?: string[],
): Promise<void> {
  const index = await fetchSessionIndex(sessionPath);
  const availableFeeds = Object.keys(index.Feeds);

  const feedsToDownload = feeds
    ? feeds.filter((f) => availableFeeds.includes(f))
    : availableFeeds;

  if (feedsToDownload.length === 0) {
    console.error("❌ No feeds to download");
    return;
  }

  // Create output directory
  const fullDir = join("data", outputDir);
  mkdirSync(fullDir, { recursive: true });

  console.log(
    `\n📥 Downloading ${feedsToDownload.length} feeds → ${fullDir}\n`,
  );

  let success = 0;
  let failed = 0;

  for (const feed of feedsToDownload) {
    try {
      // Try jsonStream first (more data), then fall back to json
      let data: string;
      let ext: string;

      try {
        data = await fetchData(sessionPath, feed, "jsonStream");
        ext = ".jsonStream";
      } catch {
        data = await fetchData(sessionPath, feed, "json");
        ext = ".json";
      }

      // Decompress .z feeds
      if (feed.endsWith(".z")) {
        console.log(`  🔧 Decompressing ${feed}...`);
        const entries = parseJsonStream(data);
        // Save decompressed
        writeFileSync(
          join(fullDir, `${feed}${ext}`),
          data,
        );
        writeFileSync(
          join(fullDir, `${feed.replace(".z", "")}.json`),
          JSON.stringify(entries, null, 2),
        );
      } else {
        writeFileSync(join(fullDir, `${feed}${ext}`), data);
        // Also save parsed
        try {
          const parsed = parseJsonWithBOM(data);
          writeFileSync(
            join(fullDir, `${feed}.parsed.json`),
            JSON.stringify(parsed, null, 2),
          );
        } catch {
          // raw data
        }
      }

      const sizeKB = (Buffer.byteLength(data) / 1024).toFixed(1);
      console.log(`  ✅ ${feed.padEnd(25)} ${sizeKB} KB`);
      success++;
    } catch (err) {
      console.log(`  ❌ ${feed.padEnd(25)} failed: ${(err as Error).message}`);
      failed++;
    }
  }

  console.log(
    `\n🏁 Done! ${success} downloaded, ${failed} failed → ${fullDir}`,
  );
}

// --- CLI ---
function printUsage(): void {
  console.log(`
🏎️ Box-Box — F1 Data Fetcher

Usage:
  bun run src/fetcher.ts <command> [options]

Commands:
  season <year>                          List all events in a season
  sessions <year> <round>                List sessions for an event
  feeds <year> <round> <sessionType>     Show available data feeds
  download <year> <round> <sessionType>  Download all session data
    [--feeds Feed1,Feed2]                Download specific feeds only
    [--output <dir>]                     Output subdirectory (default: auto)

Session types: Practice 1, Practice 2, Practice 3, Qualifying, Race, Sprint, Sprint Qualifying

Examples:
  bun run src/fetcher.ts season 2026
  bun run src/fetcher.ts sessions 2026 3
  bun run src/fetcher.ts feeds 2026 3 Race
  bun run src/fetcher.ts download 2026 3 Race
  bun run src/fetcher.ts download 2026 3 Race --feeds TimingData,TopThree
`);
}

function findSession(
  season: SeasonIndex,
  round: number,
  sessionType: string,
): SessionInfo | undefined {
  const meeting = season.Meetings.find(
    (m) => m.Number === round && !m.Code.includes("T0"),
  );
  if (!meeting) return undefined;
  return meeting.Sessions.find((s) => {
    const type = sessionType.toLowerCase().replace(/\s+/g, "");
    const sType = s.Type.toLowerCase().replace(/\s+/g, "");
    const sName = s.Name.toLowerCase().replace(/\s+/g, "");
    return sType === type || sName === type;
  });
}

async function main(): Promise<void> {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    printUsage();
    return;
  }

  const command = args[0];

  try {
    switch (command) {
      case "season": {
        const year = parseInt(args[1]);
        await listSeason(year);
        break;
      }

      case "sessions": {
        const year = parseInt(args[1]);
        const round = parseInt(args[2]);
        await listSession(year, round);
        break;
      }

      case "feeds": {
        const year = parseInt(args[1]);
        const round = parseInt(args[2]);
        const sessionType = args.slice(3).join(" ");
        const season = await fetchSeason(year);
        const session = findSession(season, round, sessionType);
        if (!session) {
          console.error(`❌ Session not found: ${sessionType}`);
          return;
        }
        await showFeeds(session.Path);
        break;
      }

      case "download": {
        const year = parseInt(args[1]);
        const round = parseInt(args[2]);
        // Parse remaining args for session type and flags
        const remaining = args.slice(3);
        let sessionType = "Race";
        let feedFilter: string[] | undefined;
        let outputDir: string | undefined;

        for (let i = 0; i < remaining.length; i++) {
          if (remaining[i] === "--feeds" && remaining[i + 1]) {
            feedFilter = remaining[++i].split(",");
          } else if (remaining[i] === "--output" && remaining[i + 1]) {
            outputDir = remaining[++i];
          } else if (!remaining[i].startsWith("--")) {
            sessionType = remaining[i];
          }
        }

        const season = await fetchSeason(year);
        const session = findSession(season, round, sessionType);
        if (!session) {
          console.error(`❌ Session not found: ${sessionType}`);
          return;
        }

        const defaultDir = session.Path.replace(/\//g, "_").replace(/_$/, "");
        await downloadSession(
          session.Path,
          outputDir || defaultDir,
          feedFilter,
        );
        break;
      }

      default:
        printUsage();
    }
  } catch (err) {
    console.error(`\n❌ Error: ${(err as Error).message}`);
    process.exit(1);
  }
}

main();
