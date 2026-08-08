This file describes all steps of execution for the THM room.

Difficulty - Easy

Target IP: http://10.112.167.155

A scan was performed using nmap:

`nmap -T4 -p- -A -Pn -oN nmap.txt 10.112.167.155`

The scan showed a web server running on port 80.

I opened the website:

`http://10.112.167.155`

The website provided a login page.

I started looking for credentials to access the application.

By checking the page source, I found a developer comment containing the credentials:

Username: dj
Password: dj

I used these credentials to log in.

After logging in, the application provided several pages:

Dashboard
Import
Export

The **Import** page immediately stood out because it allowed playlists to be uploaded in **YAML** format.

Before trying anything, I opened the Export page and downloaded one of the existing playlists.

This allowed me to see the expected YAML structure and use it as a template for testing.

I then started testing how the application processed YAML files.

I created a simple playlist containing different YAML data types:

```yaml
playlist:
  number: 123
  decimal: 1.5
  enabled: true
  empty: null
  date: 2026-07-31
```

After clicking **Load playlist**, the application displayed:

```text
{'playlist': {'number': 123, 'decimal': 1.5, 'enabled': True,
'empty': None, 'date': datetime.date(2026, 7, 31)}}
```

This showed that the application was not simply displaying the YAML as text.

Instead, it was converting the YAML values into Python objects.

For example:

123 -> integer

1.5 -> float

true -> True

null -> None

This indicated that the server was **deserializing the YAML into Python objects**.

It also suggested that the application was using a Python YAML parser such as PyYAML.

I then tested whether Python-specific YAML tags were supported.

I submitted:

```yaml
playlist:
  test: !!python/name:os.getcwd
```

After loading the playlist, the application returned:

```text
<built-in function getcwd>
```

This confirmed that the application was resolving Python-specific YAML constructors rather than treating them as ordinary text.

At this point, I knew that Python constructors were being processed by the YAML parser.

The next step was to determine whether this could be abused to execute commands on the server.

I used a Python function capable of executing system commands and prepared a reverse-shell payload.

Before executing the payload, I started a listener:

`nc -lvnp 444`

After executing the payload, I received a shell on the target machine.

I then searched the filesystem for the user flag:

`find / -type f -name user.txt 2>/dev/null`

The user flag was found.

#1 FLAG FOUND / user flag:

<details>
<summary>Spoiler Alert!</summary>

THM{y4ml_pl4yl1st_pwns_th3_b34ch}

</details>

After obtaining a shell as the **bartender** user, I started looking for a way to escalate privileges.

I began by enumerating the application files under:

`/opt`

I found a Python script used by the jukebox service.

While reviewing the script, I noticed that the application required a password when it started.

The relevant section was:

```text
parser.add_argument(
    "--stream-pass",
    required=True,
    help="stream backend password"
)
```

The important part was:

`required=True`

This meant that the application could not start unless a password was supplied.

The supplied value was then stored after parsing the arguments:

`args = parser.parse_args()`

Since the application was running as a **systemd service**, I checked how the service was started.

I used:

`systemctl show jukeboxd.service | grep ExecStart`

The service configuration showed that the password was being passed directly as a command-line argument.

This is insecure because command-line arguments can be exposed through tools and interfaces such as:

`systemctl show`

`ps`

`/proc`

The password was visible in the service configuration:

`SunsetSpritz2024!`

I then used the discovered credentials to obtain root access.

After becoming root, I retrieved the root flag.

#2 FLAG FOUND / root flag:

Room completed.
