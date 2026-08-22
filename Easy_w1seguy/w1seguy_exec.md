TryHackMe — W1seGuy

This file describes all steps used to complete the TryHackMe W1seGuy room.

The room involves source-code analysis, TCP enumeration, XOR encryption, known-plaintext attacks, and repeating-key cryptography.

We first connect to the TCP service, analyze the provided source code, identify the repeating 5-character XOR key, recover the key using known plaintext, and submit the key to obtain the second flag.

Difficulty: Easy

MACHINE-IP: 10.112.146.85

PORT: 1337

Source Code Analysis

The provided source code immediately showed how the challenge worked.

The server listens on:

socketserver.ThreadingTCPServer(('0.0.0.0', 1337), RequestHandler)

Therefore, the service can be accessed with:

nc 10.112.146.85 1337

The important part of the encryption function was:

for i in range(0,len(flag)):
    xored += chr(ord(flag[i]) ^ ord(key[i%len(key)]))

This tells us that the flag is encrypted using XOR.

The key is generated here:

res = ''.join(random.choices(string.ascii_letters + string.digits, k=5))
key = str(res)

Therefore, the encryption key is:

Exactly 5 characters
Randomly generated
Made from letters and numbers

The following line is especially important:

key[i%len(key)]

Because the key length is 5, the same key is repeatedly used:

ABCDEABCDEABCDEABCDE...
Connecting to the Server

I connected to the service using Netcat:

nc 10.112.146.85 1337

The server returned something similar to:

This XOR encoded text has flag 1: 17300a2a2072192b3f240600331024374c243a3302163562312f343e3905310c3e6125310008232d
What is the encryption key?

The server then waited for the encryption key.

At this point, I did not guess the key.

Understanding the XOR Encryption

The encryption operation is:

plaintext XOR key = ciphertext

XOR has an important property:

ciphertext XOR plaintext = key

This means that if we know part of the original plaintext, we can recover the corresponding part of the key.

This is known as a known-plaintext attack.

Known Plaintext

The source code gives us an important clue:

flag = 'THM{thisisafakeflag}'

The challenge also uses the standard TryHackMe flag format:

THM{...}

The actual plaintext used by the running challenge was:

THM{p1alntExtAtt4ckcAnr3alLyhUrty0urxOr}

Because we know the plaintext and have the encrypted ciphertext, we can XOR the two together.

For example:

Ciphertext:
17 30 0a 2a ...

Plaintext:
54 48 4d 7b ...

XOR:
43 78 47 51 ...

The resulting bytes reveal the repeating key.

Recovering the 5-Character Key

The key is only five characters long.

Therefore, once the first five key characters are recovered, they repeat throughout the ciphertext:

KEY12KEY12KEY12KEY12...

For the successful connection, the recovered key was:

CxGQP

The important thing is that the key belongs to the specific TCP connection that generated the ciphertext.

Every time a new connection is created, this code runs again:

res = ''.join(random.choices(string.ascii_letters + string.digits, k=5))

Therefore:

Connection 1 → random key A
Connection 2 → random key B
Connection 3 → random key C

A key recovered from one connection cannot be used on another connection.

Submitting the Key

While the original Netcat connection was still waiting at:

What is the encryption key?

I entered:

CxGQP

The server verifies the key using:

if key_answer == key:

When the key is correct, the server returns the second flag.

This successfully completes the challenge.

Why the Attack Works

The vulnerability is caused by several weaknesses being combined.

1. The encryption uses XOR
flag[i] ^ key[i]

XOR itself is not necessarily insecure, but its security depends heavily on how the key is used.

2. The key is extremely short

The key is only:

5 characters
3. The key is reused repeatedly

The code uses:

key[i%len(key)]

which produces:

ABCDEABCDEABCDEABCDE...
4. We know the plaintext

The flag format gives us known plaintext such as:

THM{

Therefore:

ciphertext XOR known plaintext = key

allows us to recover the key.

Attack Chain

The complete attack path was:

10.112.146.85:1337
        ↓
Connect using Netcat
        ↓
Receive XOR ciphertext
        ↓
Analyze source code
        ↓
Identify repeating 5-character XOR key
        ↓
Use known plaintext
        ↓
Ciphertext XOR plaintext
        ↓
Recover encryption key
        ↓
Submit key to same TCP connection
        ↓
Receive Flag 2
Key Lessons

The main lesson from this room is that repeating-key XOR is vulnerable when the attacker knows or can predict part of the plaintext.

The critical relationship is:

Plaintext XOR Key = Ciphertext

Because XOR is reversible:

Ciphertext XOR Plaintext = Key

The five-character repeating key makes the problem even easier.

The challenge therefore isn't about brute-forcing the entire keyspace. Instead, the source code and known plaintext allow the key to be recovered directly.

Commands Used

Connect to the challenge:

nc 10.112.146.85 1337

The important information obtained from the source code was:

key = ''.join(random.choices(string.ascii_letters + string.digits, k=5))

and:

flag[i] ^ key[i%len(key)]

The key was recovered using:

ciphertext XOR plaintext = key

The recovered key for the successful connection was:

CxGQP

Entering that key into the same Netcat session returned the second flag.
