# Right Time

Input: specification of the time moment in the near future (bound to the time of the round)

Output: answer should be submitted exactly at the specified time (+-2 seconds)

## Difficulty Level 1

Send the answer back exactly in the moment of time, specified in the task input.


* Time is always 1 minute in the future.
* Time is given as string in the format "2025-07-02T15:04:05+02:00" (ISO 8601 format).

## Difficulty Level 2

* Time is in the range of 1-20 minutes in the future.

## Difficulty Level 3

* Time is given in specified timezone. Timezones: CEST, CET, MSK, UTC

## Difficulty Level 4

Time is in the range of 1 minute — 2 hours in the future.

Time is given in the strange timezones with a no whole shift: 

* UTC−03:30	NST (Newfoundland Standard Time)
* UTC+03:30	IRST (Iran Standard Time)
* UTC+04:30	AFT (Afghanistan Time)
* UTC+05:30	IST (India Standard Time)
* UTC+05:45	NPT (Nepal Time)
* UTC+06:30	MMT (Myanmar Time)
* UTC+08:45	ACWST (Australian Central Western Standard Time)
* UTC+09:30	ACST (Australian Central Standard Time)
* UTC+10:30	LHST (Lord Howe Standard Time)
* UTC+12:45	CHAST (Chatham Island Standard Time)

## Difficulty Level 5

Time is given in one of the formats:
* "2025-07-02T15:04:05+02:00" (ISO 8601 format).
* "Tue, 02 Jul 2025 15:04:05 +0200" (RFC 2822 format).
* 1720220645 (Unix timestamp in seconds).
* "Now+PT5S" (Iso8601 duration format, meaning "now + 5 seconds").
* "Now+0:01:00" (Iso8601 duration format, meaning "now + 1 minute").

## Difficulty Level 6

Time is given as a summation of the time and duration:
* "2025-07-02T15:04:05+02:00 + PT5S" (ISO 8601 format).
* "Tue, 02 Jul 2025 15:04:05 +0200 + PT5S" (RFC 2822 format).
* "PT5S + 1720220645" (Unix timestamp in seconds).
 
## Difficulty Level 7

Time is given as an expression including time, duration with summation and subtraction:
* "2025-07-02T15:04:05+02:00 + PT1M5S - PT1M".
* several times parts in one expression: "Now + 2025-07-02T15:04:05+02:00 + PT1M5S - 2025-07-02T15:04:05+02:00 + PT1M". 

## Difficulty Level 8

Natural language processing:

* "5 minutes from now"
* "Let it be 2 hours and 30 minutes from now"
* "Half past 3, please"
* "Viertel nach 4" (German for "quarter past 4")

Implementation detail: generate a ot of patterns with AI and use them for generation.





