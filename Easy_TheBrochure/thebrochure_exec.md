This file describes all steps of exection for THM room (The Brochure)
Difficulty - Very Easy

Target IP: NO IP

There is an attachment that needs to be downloaded.
Containts image of a brochure.

Task is to identify the image for hidden clues, weird text or anomalies.

Interesting text:
"Some things aren't posted. Some clues are. Find us on instagram or not."

I checked their instagram where the same image was posted and there was
another one with a beach view.

Back on the brochure image there was another clue:
"CONCIERGE. VERA can assist you with further information."

I went to back the instagram page and there was 1 person which the page was following.

-VERA

Checked vera account, and there were 3 posts. A big base64 hash seperated through those 3 images.

Connect the parts and we get:

VEhNe1YzckBzX2FD QzB1bnRfaDRzX2Iz M25fZjB1bmQhfQ==

Decided to decrypt it via terminal
` echo 'VEhNe1YzckBzX2FDQzB1bnRfaDRzX2IzM25fZjB1bmQhfQ==' | base64 -d `

<details>
<summary>Spoiler Alert!</summary>

THM{V3r@s_aCC0unt_h4s_b33n_f0und!}

</details>

FLAG FOUND
Room completed.
