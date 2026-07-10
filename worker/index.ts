// Thin Cloudflare Worker that fronts the BridgeAid container.
//
// Every request is forwarded, unmodified, to a single named container instance
// so the app's in-memory session/reminder state is shared while awake. The raw
// request body is preserved — LINE webhook signature verification (HMAC-SHA256
// over the raw body) depends on it.
import { Container, getContainer } from "@cloudflare/containers";

interface Env {
  BRIDGEAID: DurableObjectNamespace<BridgeAidContainer>;
  // LINE secrets, injected into the container's environment (wrangler secret put ...).
  LINE_CHANNEL_ID?: string;
  LINE_CHANNEL_SECRET?: string;
  LINE_CHANNEL_ACCESS_TOKEN?: string;
}

export class BridgeAidContainer extends Container<Env> {
  defaultPort = 8080;
  // Keep the instance warm for a while during a demo to avoid cold starts.
  // Note: on sleep, in-memory sessions and scheduled reminders are lost (no DB).
  sleepAfter = "20m";

  // Pass LINE secrets through to the FastAPI process. config.get_secret() reads
  // these via its environment-variable fallback. Undefined secrets are dropped.
  envVars = Object.fromEntries(
    Object.entries({
      LINE_CHANNEL_ID: this.env.LINE_CHANNEL_ID,
      LINE_CHANNEL_SECRET: this.env.LINE_CHANNEL_SECRET,
      LINE_CHANNEL_ACCESS_TOKEN: this.env.LINE_CHANNEL_ACCESS_TOKEN,
    }).filter(([, v]) => v !== undefined),
  ) as Record<string, string>;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    // Single fixed-name instance -> all requests hit the same container.
    const container = getContainer(env.BRIDGEAID, "bridgeaid");
    return container.fetch(request);
  },
};
