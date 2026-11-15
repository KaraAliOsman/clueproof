// Clueproof live reading: a Cloudflare Worker that reads one demo photo with
// Claude Haiku 5.5 and returns the clues by type and position, never their values.
//
// The Anthropic key lives only here, as a Worker secret (ANTHROPIC_API_KEY).
// Abuse is bounded by design: the Worker accepts only the 20 demo photo IDs,
// fetches the images itself, and stores each reading in KV, so each photo is
// sent to the model once per CACHE_VERSION.

import Anthropic from "@anthropic-ai/sdk";
import { z } from "zod";
import { zodOutputFormat } from "@anthropic-ai/sdk/helpers/zod";

export interface Env {
  ANTHROPIC_API_KEY: string;
  READINGS: KVNamespace;
}

const MODEL = "claude-haiku-5-5";
const CACHE_VERSION = "v1";
const IMAGE_BASE = "https://mrchickenkk.github.io/clueproof/assets/photos/";

const PHOTOS: Record<string, string> = {
  S01: "S01-beach.jpg", S02: "S02-sunset.jpg", S03: "S03-ice-cream.jpg", S04: "S04-dog-beach.jpg",
  S05: "S05-house-number.jpg", S06: "S06-license-plate.jpg", S07: "S07-boarding-pass.jpg",
  S08: "S08-school-crest.jpg", S09: "S09-seagull.jpg", S10: "S10-parcel-label.jpg",
  S11: "S11-house-key.jpg", S12: "S12-mountain-lake.jpg",
  H01: "H01-id-card.jpg", H02: "H02-payment-card.jpg", H03: "H03-chat-screen.jpg",
  H04: "H04-wifi-password.jpg", H05: "H05-prescription.jpg", H06: "H06-plaza.jpg",
  H07: "H07-calculator.jpg", H08: "H08-coffee.jpg",
};

const ORIGINS = new Set(["https://mrchickenkk.github.io", "https://karaaliosman.github.io"]);
const LOCAL = /^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/;

const CODES = ["ADR", "MAL", "SCH", "PLT", "TKT", "IDD", "PAY", "SCR", "COD", "KEY", "MED", "FAC"] as const;
const POSITIONS = [
  "top left", "top center", "top right", "middle left", "center", "middle right",
  "bottom left", "bottom center", "bottom right", "whole photo",
] as const;

const Reading = z.object({
  clues: z.array(
    z.object({
      code: z.enum(CODES),
      label: z.string(),
      position: z.enum(POSITIONS),
      sure: z.boolean(),
    }),
  ),
  note: z.string(),
});

const SYSTEM = `You are the visual reading of Clueproof, a photo privacy check for families. You look at one photo and list every visible clue a stranger could use, by type and position only.

Clue types:
- ADR: house number or a readable postal address
- MAL: mail or package label with a name or address
- SCH: school name, logo, crest or name label on clothing or a bag
- PLT: readable vehicle license plate
- TKT: boarding pass, travel or event ticket, or a booking barcode or QR code
- IDD: identity document or ID card
- PAY: bank or payment card
- SCR: screen showing messages, email, accounts or codes
- COD: note with a password, Wi-Fi key, PIN or code
- KEY: house or car keys shown clearly enough to see their shape
- MED: prescription label or medical wristband
- FAC: faces of people in the background who are not the subject and could be recognized

Rules:
- Never write the value of a clue: no numbers, names, codes, addresses or any text read from the photo. Give the type, a short plain label (for example "House number") and where it is.
- Report a clue only when it is really visible. Set sure to false when you are not certain.
- Distant people whose faces cannot be recognized are not FAC.
- Report each object once, with the most specific type.
- If nothing qualifies, return an empty list.
- The note is one plain sentence for a parent: what the photo gives away, or that it gives nothing away. No values in the note either.`;

function cors(origin: string | null): Record<string, string> {
  const ok = origin && (ORIGINS.has(origin) || LOCAL.test(origin));
  return {
    "Access-Control-Allow-Origin": ok ? origin : "https://mrchickenkk.github.io",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Vary": "Origin",
  };
}

function json(body: unknown, status: number, origin: string | null, extra: Record<string, string> = {}): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8", ...cors(origin), ...extra },
  });
}

async function readPhoto(env: Env, id: string) {
  const client = new Anthropic({ apiKey: env.ANTHROPIC_API_KEY, maxRetries: 2, timeout: 90_000 });
  const response = await client.messages.parse({
    model: MODEL,
    max_tokens: 16000,
    system: SYSTEM,
    output_config: { effort: "high", format: zodOutputFormat(Reading) },
    messages: [
      {
        role: "user",
        content: [
          { type: "image", source: { type: "url", url: IMAGE_BASE + PHOTOS[id] } },
          { type: "text", text: "Read this photo for Clueproof." },
        ],
      },
    ],
  });
  if (response.stop_reason === "refusal") throw new Error("refusal");
  if (response.stop_reason === "max_tokens") throw new Error("max_tokens");
  if (!response.parsed_output) throw new Error("unparsed");
  return response.parsed_output;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const origin = request.headers.get("Origin");
    const url = new URL(request.url);

    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: cors(origin) });
    if (request.method !== "GET") return json({ error: "method" }, 405, origin);

    if (url.pathname === "/") {
      return json({ service: "Clueproof live reading", model: MODEL, photos: Object.keys(PHOTOS).length }, 200, origin);
    }
    if (url.pathname !== "/reading") return json({ error: "not found" }, 404, origin);

    const id = (url.searchParams.get("id") || "").toUpperCase();
    if (!Object.hasOwn(PHOTOS, id)) return json({ error: "unknown photo" }, 400, origin);

    const key = `${CACHE_VERSION}:${id}`;
    const cached = await env.READINGS.get(key, "json");
    if (cached) return json({ ...(cached as object), cached: true }, 200, origin, { "Cache-Control": "public, max-age=300" });

    try {
      const reading = await readPhoto(env, id);
      const body = { id, model: MODEL, effort: "high", at: new Date().toISOString(), ...reading };
      await env.READINGS.put(key, JSON.stringify(body));
      return json({ ...body, cached: false }, 200, origin);
    } catch (err) {
      const reason = err instanceof Anthropic.APIError ? `api ${err.status}` : err instanceof Error ? err.message : "error";
      console.error(`reading ${id} failed: ${reason}`);
      return json({ error: "reading unavailable", reason }, 502, origin);
    }
  },
};
