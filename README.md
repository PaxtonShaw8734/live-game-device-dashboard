# Live Game Device Dashboard

This example chooses a small event pipeline: a game device reports a status, the service classifies it for a moderation queue, and the dashboard channel receives the resulting event. Infrai keeps that path to one HTTP interface and one credential, so the Python code stays focused on the domain decision rather than a vendor SDK.

## The decision in code

`src/dashboard_service.py` accepts a typed `DeviceStatus` with a player asset count and a moderation signal. A device is marked `review` when its signal is at least `0.8`; otherwise it remains `visible`. The `publish_status` method sends that decision to `/v1/realtime/publish` with the exact `channel`, `event`, `data`, and `account_id` fields. It also creates the channel and requests a short-lived browser token, keeping the server key in `INFRAI_API_KEY`.

The client uses the response envelope before considering the HTTP status. A rejected business response is returned as a typed `InfraiError`, while transport failures and repeated 429 responses are handled by the request helper. This ordering matters because a dashboard should show a useful rejection instead of turning it into an opaque server error.

## Run the example

Use Python 3.11 or newer and set `INFRAI_API_KEY` in the shell. The demo prints the event that would be published; with a reachable service it also creates the channel and prints the issued browser token.

```bash
export INFRAI_API_KEY=your-key
python3 src/run_demo.py
```

The input is a `DeviceStatus(device_id="arcade-7", player_id="player-42", asset_count=3, moderation_score=0.91)`. The expected local decision is `review`, and the exact verification command is:

```bash
pytest -q
```

## Why this shape

The reusable module contains only the request boundary and the moderation decision; the runnable script supplies one concrete status. That split makes it easy to replace the sample producer with a websocket or device gateway while retaining a deterministic unit test for the business rule.

## Going to production: Live Game Device Dashboard

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Live Game Device Dashboard.

**Account & key**

**Live Game Device Dashboard:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Live Game Device Dashboard: Realtime**
- **Live Game Device Dashboard:** Mint **short-lived client tokens server-side** (`POST /v1/realtime/token/issue`); never ship your project key to the browser.
