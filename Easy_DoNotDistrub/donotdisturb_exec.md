# TryHackMe — Do Not Disturb

This file describes all steps of execution for the TryHackMe room **Do Not Disturb**.

The room involves web enumeration, NoSQL injection, session hijacking, EJS Server-Side Template Injection (SSTI), and Node.js debugging. We first bypass the login using a MongoDB NoSQL injection, access the staff panel, exploit an EJS SSTI vulnerability to obtain a reverse shell, and then abuse Node.js debugging functionality to access the raw filesystem and retrieve the root flag.

Difficulty - Easy

---

MACHINE-IP: 10.112.171.99

---

# Scanning

I started by scanning the target and enumerating the web application.

The target was:

```text
10.112.171.99
```

After performing Nmap scans and directory enumeration, I discovered two interesting endpoints:

```text
/logout
/staff
```

I also identified some important information about the application:

* The application was built using **Node.js**.
* The application was using the **EJS** template engine.

These details became especially important later during exploitation.

---

# Web Enumeration

The application presented a sign-in form.

I first tested the login functionality normally, but I was unable to authenticate using standard credentials.

When I attempted to access:

```text
/staff
```

the application returned:

```text
403 Unauthorized
```

This indicated that the `/staff` endpoint existed but required an authenticated session with the appropriate permissions.

After spending some time testing the login functionality, I determined that the application was using **MongoDB**.

This suggested that the login form could potentially be vulnerable to a **NoSQL injection**.

---

# NoSQL Injection

I started by submitting the username:

```text
attendant
```

with no password.

I then intercepted the request using **Burp Suite**.

The first important change was modifying the request's `Content-Type` header.

I changed:

```http
Content-Type: application/x-www-form-urlencoded
```

to:

```http
Content-Type: application/json
```

I then replaced the request body with a MongoDB query using the `$ne` operator:

```json
{
  "username": "attendant",
  "password": {"$ne": null}
}
```

The `$ne` operator means "not equal", so the query effectively asks MongoDB to find the `attendant` user where the password is not equal to `null`.

The request was accepted by the application.

Instead of receiving an authentication error, I received:

```text
200 OK
```

The response also contained a session cookie belonging to a **staff** role account.

This confirmed that the login functionality was vulnerable to NoSQL injection.

---

# Accessing the Staff Panel

I used Burp Suite's **Open Response in Browser** functionality to open the authenticated response.

I then navigated to:

```text
http://10.112.171.99/staff
```

The `/staff` endpoint was now accessible.

If the browser does not automatically set the session cookie, the cookie can be added manually before accessing the endpoint.

After successfully setting the cookie, I was inside the staff panel.

---

# Server-Side Template Injection

At this point, I immediately noticed that the staff panel contained functionality vulnerable to **Server-Side Template Injection (SSTI)**.

The application was using the **EJS** template engine, which was particularly interesting because EJS allows JavaScript expressions to be evaluated when templates are rendered.

I tested the input field with an EJS expression to confirm that user-controlled input was being evaluated by the server.

The successful evaluation confirmed that the application was vulnerable to EJS SSTI.

Since EJS templates execute JavaScript on the server, this vulnerability could potentially be escalated from template injection to **remote code execution**.

---

# Getting a Reverse Shell

After confirming the SSTI vulnerability, I used an EJS payload capable of executing commands on the target.

I prepared a reverse shell connection back to my machine.

For the listener, I used **Penelope**, although Netcat can also be used.

I started the listener on my machine:

```bash
python3 penelope.py 4444
```

Before sending the payload, I determined my VPN interface IP address using:

```bash
ip a
```

The relevant address was the IP assigned to my `tun0` interface.

I then replaced:

```text
<ATTACKER_IP>
```

in the reverse shell payload with my own machine's IP address.

I submitted the payload through the vulnerable EJS template field.

The server executed the injected JavaScript and established a connection back to my listener.

I successfully obtained a reverse shell on the target.

---

# User Flag

Once I had shell access, I began enumerating the target filesystem and users.

The first objective was to locate the user flag.

After locating the appropriate flag file, I was able to retrieve the first flag.

<details>
<summary>Spoiler Alert!</summary>

```text
THM{w4rm_s3ss10n_h1j4ck3d}
```

</details>

---

# Privilege Escalation

With the user flag obtained, I continued enumerating the system for a way to reach the root flag.

While exploring the filesystem and user directories, I discovered another profile:

```text
pipelinesvc
```

Inside this profile was an interesting JavaScript file:

```text
processor.js
```

I examined the contents of the file to understand what process it was running.

---

# Discovering the Node.js Debugger

The `processor.js` file contained a process that was running continuously in a loop.

Further investigation showed that the process exposed a Node.js debugging interface on:

```text
127.0.0.1:9229
```

Port `9229` is commonly associated with the Node.js inspector/debugging interface.

Since the service was bound to localhost, it was not directly accessible from my machine, but I already had a shell on the target.

This meant I could interact with it locally.

---

# Connecting to the Node.js Process

I used the Node.js inspector to connect to the running process:

```bash
node inspect 127.0.0.1:9229
```

After connecting, I entered the REPL:

```text
repl
```

I then tested whether I had access to the Node.js process by executing:

```javascript
process.getuid()
```

The command successfully returned information about the process user.

This confirmed that I had access to the JavaScript execution environment of the running Node.js process.

Because the process had elevated privileges, this provided an interesting route toward accessing files that were normally protected by Linux filesystem permissions.

---

# Raw Disk Access

The next step was to investigate the underlying disk devices.

The goal was to determine whether the filesystem containing `/root` could be accessed directly through its raw block device.

Normally, Linux filesystem permissions prevent an unprivileged user from simply reading:

```text
/root/root.txt
```

However, accessing the underlying filesystem directly can bypass those normal path-based permission checks.

---

## 1. Disk Discovery

I first enumerated the available disks and partitions on the system.

The relevant partition was:

```text
/dev/nvme0n1p1
```

This appeared to contain the system filesystem.

---

## 2. Raw Filesystem Directory Listing

I then used `debugfs`, the Linux filesystem debugger for ext2/ext3/ext4 filesystems, against the raw partition.

The purpose was to inspect the filesystem directly rather than accessing `/root` through the normal Linux filesystem hierarchy.

The relevant device was:

```text
/dev/nvme0n1p1
```

Using `debugfs`, I was able to inspect the contents of the filesystem and locate:

```text
/root/root.txt
```

This was significant because the file was protected from normal filesystem access.

---

## 3. Extracting the Root Flag

Once the location of the flag was identified, I used `debugfs` to dump the contents of:

```text
/root/root.txt
```

directly from the raw filesystem partition:

```text
/dev/nvme0n1p1
```

This allowed me to retrieve the contents of the protected file without relying on the normal Linux permission checks for `/root`.

The final flag was successfully recovered.

<details>
<summary>Spoiler Alert!</summary>

```text
THM{r4w_d1sk_4cc3ss_w4s_t00_much}
```

</details>

---

# Room Completed

The room was completed by chaining together several vulnerabilities and misconfigurations.

The main attack path was:

1. Scan the target and enumerate the web application.
2. Discover the `/logout` and `/staff` endpoints.
3. Identify that the application uses Node.js and EJS.
4. Determine that the login functionality uses MongoDB.
5. Exploit the login form using a MongoDB NoSQL injection.
6. Obtain a valid staff session cookie.
7. Use the session cookie to access `/staff`.
8. Discover the EJS Server-Side Template Injection vulnerability.
9. Use the SSTI to achieve remote command execution.
10. Establish a reverse shell on the target.
11. Retrieve the first flag.
12. Discover the `pipelinesvc` profile and `processor.js`.
13. Identify the Node.js debugger running on `127.0.0.1:9229`.
14. Connect to the Node.js inspector using `node inspect`.
15. Access the Node.js REPL and confirm execution with `process.getuid()`.
16. Enumerate the available disk partitions.
17. Identify `/dev/nvme0n1p1` as the relevant filesystem partition.
18. Use `debugfs` to inspect the raw filesystem.
19. Locate `/root/root.txt`.
20. Extract the root flag directly from the raw filesystem.

---

# Flags

### First Flag

<details>
<summary>Spoiler Alert!</summary>

```text
THM{w4rm_s3ss10n_h1j4ck3d}
```

</details>

### Root Flag

<details>
<summary>Spoiler Alert!</summary>

```text
THM{r4w_d1sk_4cc3ss_w4s_t00_much}
```

</details>

---

# Final Attack Chain

```text
NoSQL Injection
       ↓
Staff Session Cookie
       ↓
/staff Access
       ↓
EJS SSTI
       ↓
Remote Command Execution
       ↓
Reverse Shell
       ↓
User Flag
       ↓
pipelinesvc / processor.js
       ↓
Node.js Debugger :9229
       ↓
Node.js REPL
       ↓
Raw Disk Access
       ↓
debugfs
       ↓
/root/root.txt
       ↓
Root Flag
```
