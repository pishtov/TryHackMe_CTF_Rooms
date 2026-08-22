# TryHackMe — W1seGuy

> **Category:** Cryptography / Source Code Analysis
> **Difficulty:** Easy
> **Target:** `10.112.146.85:1337`

---

## Overview

This room involves source-code analysis, TCP enumeration, XOR encryption, known-plaintext attacks, and repeating-key cryptography.

**Attack summary:** connect to the TCP service, analyze the provided source code, identify the repeating 5-character XOR key, recover the key using known plaintext, and submit it to obtain the second flag.

| Detail | Value |
|---|---|
| Machine IP | `10.112.146.85` |
| Port | `1337` |
| Vulnerability | Repeating-key XOR + known plaintext |
| Key length | 5 characters |

---

## Step 1 — Source Code Analysis

The provided source code immediately showed how the challenge worked.

**The server listens on:**

```python
socketserver.ThreadingTCPServer(('0.0.0.0', 1337), RequestHandler)
```

This means the service can be reached with:

```bash
nc 10.112.146.85 1337
```

**The encryption routine:**

```python
for i in range(0, len(flag)):
    xored += chr(ord(flag[i]) ^ ord(key[i % len(key)]))
```

This confirms the flag is encrypted using XOR.

**The key generation:**

```python
res = ''.join(random.choices(string.ascii_letters + string.digits, k=5))
key = str(res)
```

So the encryption key is:

- Exactly 5 characters
- Randomly generated
- Made from letters and digits

The critical line is `key[i % len(key)]` — because the key length is 5, it repeats indefinitely:

```
ABCDEABCDEABCDEABCDE...
```

---

## Step 2 — Connecting to the Server

```bash
nc 10.112.146.85 1337
```

The server responded with something similar to:

```
This XOR encoded text has flag 1: 17300a2a2072192b3f240600331024374c243a3302163562312f343e3905310c3e6125310008232d
What is the encryption key?
```

The server then waits for the encryption key — at this point, guessing was not an option.

---

## Step 3 — Understanding the XOR Encryption

The encryption operation is:

```
plaintext XOR key = ciphertext
```

Because XOR is reversible:

```
ciphertext XOR plaintext = key
```

If part of the plaintext is known, the corresponding part of the key can be recovered directly — a **known-plaintext attack**.

---

## Step 4 — Known Plaintext

The source code contained a placeholder flag:

```python
flag = 'THM{thisisafakeflag}'
```

Combined with TryHackMe's standard flag format `THM{...}`, this gives a reliable known-plaintext anchor.

The actual plaintext used by the running challenge was:

```
THM{p1alntExtAtt4ckcAnr3alLyhUrty0urxOr}
```

With both plaintext and ciphertext known, XOR-ing them together recovers the key bytes:

```
Ciphertext:  17 30 0a 2a ...
Plaintext:   54 48 4d 7b ...
XOR:         43 78 47 51 ...
```

---

## Step 5 — Recovering the 5-Character Key

Since the key is only five characters long, the first five recovered bytes repeat throughout the entire ciphertext:

```
KEY12KEY12KEY12KEY12...
```

**Recovered key for this connection:**

```
CxGQP
```

> **Important:** The key is unique to the specific TCP connection that generated the ciphertext. Every new connection re-runs the key generator:
>
> ```python
> res = ''.join(random.choices(string.ascii_letters + string.digits, k=5))
> ```
>
> | Connection | Key |
> |---|---|
> | 1 | Random key A |
> | 2 | Random key B |
> | 3 | Random key C |
>
> A key recovered from one connection **cannot** be reused on another.

---

## Step 6 — Submitting the Key

While the original Netcat connection was still waiting at:

```
What is the encryption key?
```

The recovered key was entered:

```
CxGQP
```

The server verifies it with:

```python
if key_answer == key:
```

Since the key matched, the server returned **Flag 2**, completing the challenge.

---

## Why the Attack Works

The vulnerability results from several weaknesses stacked together:

1. **XOR encryption** — `flag[i] ^ key[i]`. XOR isn't inherently insecure, but its safety depends entirely on key usage.
2. **Extremely short key** — only 5 characters.
3. **Key reuse** — `key[i % len(key)]` produces an obviously repeating pattern:
   ```
   ABCDEABCDEABCDEABCDE...
   ```
4. **Known plaintext** — the `THM{` flag format gives an immediate anchor:
   ```
   ciphertext XOR known plaintext = key
   ```

---

## Attack Chain

```
10.112.146.85:1337
        |
        v
Connect using Netcat
        |
        v
Receive XOR ciphertext
        |
        v
Analyze source code
        |
        v
Identify repeating 5-character XOR key
        |
        v
Use known plaintext
        |
        v
Ciphertext XOR plaintext
        |
        v
Recover encryption key
        |
        v
Submit key to same TCP connection
        |
        v
Receive Flag 2
```

---

## Key Lessons

Repeating-key XOR is vulnerable whenever an attacker knows or can predict part of the plaintext.

The core relationship:

```
Plaintext XOR Key = Ciphertext
Ciphertext XOR Plaintext = Key   (since XOR is reversible)
```

A five-character repeating key makes exploitation trivial — this challenge isn't about brute-forcing the keyspace; the source code plus known plaintext let the key be recovered directly.

---

## Commands Used

**Connect to the challenge:**

```bash
nc 10.112.146.85 1337
```

**Key details pulled from source:**

```python
key = ''.join(random.choices(string.ascii_letters + string.digits, k=5))
flag[i] ^ key[i % len(key)]
```

**Key recovery relation:**

```
ciphertext XOR plaintext = key
```

**Recovered key:**

```
CxGQP
```

Entering that key into the same Netcat session returned the second flag.
