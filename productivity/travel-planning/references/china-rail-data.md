# China rail schedule research — sources that work, and the traps

Verified on 杭州↔铜仁 (a remote destination with very few direct trains) and 杭州↔贵阳/怀化 (trunk-line hubs).

## The shape of the problem
On remote routes the binding question is **how few direct trains exist**, and their departure times — not the fare or the duration. Two asymmetries bite:

1. **Outbound ≠ return.** A comfortable afternoon train out may pair with a single early-morning train back. Always enumerate both directions as separate queries.
2. **A single early return departure silently destroys the last day.** 08:22 out means a ~06:00 wake-up and zero on-site time. Quantify this cost in hours and show the transfer alternative beside it — let the user decide whether to buy the last day back.

## Working sources (in order)
1. **web_search snippets of OTA pages** — best first move. The pages themselves are JS-rendered/walled (ctrip mobile returns "whaleguard block", qunar/trip.com need a JS session), but their **server-rendered snippet text** carries the useful payload: 车次, 发车/到达时刻, 历时, 二等/一等/商务座价, and even 中转方案 with per-leg times and 换乘 wait. Query shape: `<from> <to> 高铁 时刻表 车次` or `<from>到<to> 火车票 高铁时刻表`.
2. **Timetable aggregator sites** (server-rendered HTML, readable via web_search snippets or browser): station pages listing all departures, and per-train pages with the full stop sequence. Useful for cross-checking one train's exact times and for discovering what else leaves a small station.
3. **Hub-station pages** — for a remote station with 1–2 direct trains, list the nearby hub on the trunk line and check hub→home frequency there. Hubs on 沪昆/京广-class lines have dozens of departures a day, which is what makes the transfer viable.

Treat every timetable you find as a snapshot: schedules change at each 调图 (quarterly), and aggregator data can be a season stale. State times as "as of the current schedule" and tell the user to confirm on 12306 before buying. **Never present a timetable row as a bookable seat.**

## Ticketing facts that change the plan
- **Pre-sale window is ~15 days** for most routes; a specific future date may simply not be on sale yet. Check before promising a fare.
- **Station-name precision matters.** Cities often have several stations far apart (e.g. a 市区 station vs a 南站 tens of km away in another county); buying the wrong one costs 50 min and a taxi. Read the station name, not the city name.
- **起售时间 (release time) is per-station and is not the departure time** — it's the moment tickets go on sale (e.g. a given station's tickets release 10:45 daily). Worth giving the user as an alarm when seats are scarce.
- For the remote end, the transfer plan usually needs a **包车** between station and trailhead; price it per car, not per person, and state it's an estimate if unverified.

## Decision-table format the user responds to
Rather than prose about trains, give a small table: candidate option → departure/arrival → total hours → what it costs the itinerary ("no Sunday activity" / "free morning + arrives 21:20"). Then recommend one and ask them to confirm the real bookable option on 12306.
