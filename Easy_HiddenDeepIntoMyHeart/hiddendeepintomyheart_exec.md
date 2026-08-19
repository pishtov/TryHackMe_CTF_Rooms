This challenge involves simple **web enumeration and credential discovery**.
---

# Machine IP

```text
10.112.137.19:5000
```

---

# Web Enumeration

I started by running gobuster to find some hidden directories.
Only robots.txt showed up for this target - http://10.112.137.19.5000

```text
/robots.txt
```

The file contained:

```text
User-agent: *
Disallow: /cupids_secret_vault/*
# cupid_arrow_2026!!!
```

The interesting part was the hidden directory:

```text
/cupids_secret_vault/
```

and the comment:

```text
cupid_arrow_2026!!!
```

The comment looked like it could potentially be a password.

---

# Hidden Directory

I navigated to:

```text
/cupids_secret_vault/
```

The page didn't immediately reveal anything useful.

However, the page contained a message hinting that:

```text
there's more to discover
```

This suggested that there could be another hidden directory.

Instead of guessing paths manually, I used **Gobuster** to enumerate the directory.

---

# Directory Enumeration

Running Gobuster against:

```text
/cupids_secret_vault/
```

revealed an interesting endpoint:

```text
/administrator/
```

This looked like the obvious next step.

I opened:

```text
/cupids_secret_vault/administrator/
```

and found a login page.

---

# Administrator Login

At this point, we already had a potential password from `robots.txt`:

```text
cupid_arrow_2026!!!
```

I first tried using:

```text
Username: administrator
Password: cupid_arrow_2026!!!
```

but the login failed.

Since we were dealing with an administrator page, I then tried the simpler username:

```text
admin
```

using the same password:

```text
cupid_arrow_2026!!!
```

This time, the credentials worked.

No brute-force tools were required — the challenge was simply relying on information discovered during enumeration and a little bit of logical guessing.

---

# Flag
<details>
<summary>Spoiler Alert!</summary>

```text
THM{l0v3_is_in_th3_r0b0ts_txt}
```

</details>


---

# Attack Chain

```text
/robots.txt
      ↓
/cupids_secret_vault/
      ↓
Gobuster
      ↓
/administrator/
      ↓
Password discovered in robots.txt
      ↓
Username: admin
      ↓
Administrator Login
      ↓
Flag
```

---

# Why No Nmap?

Nmap wasn't necessary for this challenge because the target was already provided as a web application with a known port.

The challenge was clearly focused on **web enumeration**, so I went directly after the application.

---

# Why Use the robots.txt Password?

The password was deliberately exposed in `robots.txt`:

```text
# cupid_arrow_2026!!!
```

Since the challenge also gave us an administrator login, trying the discovered value as the password was a logical first step.

There was no reason to brute-force the login when the challenge had already handed us a potential credential.

---

# Why Gobuster?

There were no obvious input fields or URL parameters suggesting vulnerabilities such as SQL injection or XSS.

Instead, we had:

* A suspicious `robots.txt`
* A hidden directory
* A message saying **"there's more to discover"**

That strongly suggested further directory enumeration.

Gobuster quickly revealed:

```text
/administrator/
```

which led directly to the login page and, ultimately, the flag.
