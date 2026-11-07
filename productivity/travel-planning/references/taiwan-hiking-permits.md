# Taiwan high-mountain permits and the November window

Taiwan's 百岳 are permit-gated, and the binding constraint is almost never fitness — it is the
bed lottery and the traveller's nationality. Resolve both before comparing routes.

## 1. Entry eligibility (passport-specific, check first)

| Traveller | Status |
|---|---|
| Mainland Chinese resident | Island-wide individual tourism suspended since 2019-08-01. Since 2026-04-29 only Fujian (9 cities) + Shanghai residents may travel, and **only to Kinmen/Matsu** — not the main island. No tourist channel from Zhejiang or other provinces. |
| US / most foreign passports | Visa-exempt entry for tourism; qualifies for 玉山's foreign-national advance quota. |
| Overseas mainland residents | Can apply for an entry permit through Taiwan's overseas missions if resident abroad — different track from mainland applicants. |

Do not design a Taiwan itinerary for a mainland-resident passport holder without confirming they have a non-tourist entry basis (business, family, study) or a second passport.

## 2. 玉山主峰 · 排雲山莊

- 136 beds (raised from 116 in August 2026), NT$480 per person per night.
- **General application**: 5 days to 2 months before the entry date, 07:00–23:00.
- **Lottery**: one month before, 15:00–16:00. Losers may join 排隊遞補 after 16:00.
- **Foreign-national advance**: 35 days to 4 months before; **24 beds/day, Sunday–Thursday only** (public holidays excluded); allocated by application order, not lottery.
- **The entry point matters**: choose `Paiyun Lodge Advanced Application` (2 Days, Tatataka–Yushan–Tatataka) on the English site. Selecting `Standard Application` / 一般申請 puts the party outside the reserved pool — the application is wasted.
- Party ratio: up to 5 foreigners may add 1 local; 6+ may add 2; local cap 4 per day. Passport copy uploaded at application.
- A date showing 相關訊息 instead of bed numbers is closed — usually beds reserved for a charity or trail-cleanup event. Click through to the `nodestop` page for the stated reason.

## 3. Querying live availability (official)

`https://hike.taiwan.gov.tw/bed_6.aspx` (玉山宿營地查詢). It is ASP.NET WebForms:

1. Set the select `#con_rooms` to `"3"` (排雲山莊) and dispatch a `change` event.
2. Click `#con_btnsearch`; wait for the postback.
3. The calendar prints per day: 餘額 (beds free) / 排隊預約 (queue) / 審核中 / 核准入園.
4. Month arrows: `#con_lbUpMonth`, `#con_lbDownMonth`.
5. Days 1–6 blank = inside the 5-day minimum window, not "full".
6. `外籍提前 N+M` lines (N foreigners + M locals) appear only for dates inside the foreign window (≥35 days out). A whole month without them means that channel is closed for the month.
7. Quote the page timestamp; availability moves hourly.

## 4. Other high-mountain routes

- **雪山主東峰**: 369 山莊 has been closed to applications since 2023-05-20 for reconstruction. Options are 369 臨時營地 (24 sites, no lottery, first-come) or 七卡山莊. Park permit 5 days–2 months ahead, 07:00 first-come. Higher total load than 玉山 (~11–12 h walking, T3 in the cirque).
- **嘉明湖**: 3 days, huts via the 林業及自然保育署 system (向陽/嘉明湖山屋) — rules and lottery timing live on the same portal.
- **奇萊南華**: 天池山莊 lottery; long but gentle 13 km forest-road approach each way.
- **合歡群峰**: road-accessible 3,000 m day hikes (石門山, 主峰, 東峰) — useful acclimatisation day, minimal permitting.

## 5. November fit

- **Northeast monsoon splits the island**: north and east (Taipei, Yilan, Keelung) turn wet and grey; central/south high mountains enter their dry season. Put multi-day routes in the centre/south (玉山, 嘉明湖, 奇萊) and keep the north for day walks.
- **太平山 台灣山毛櫸步道**: golden beech late October–late November. Weekend traffic control on 翠峰景觀道路 (200 vehicles) runs roughly late Oct–late Nov; trail is 3.8 km one way, enter before 11:00.
- **草嶺古道芒花季**: silver grass on the 8.5 km Fulong→Dali route, typically the whole of November (2026: 10/31–11/29).
- Typhoons still form into late October; after any typhoon, re-check the trail-open status page before travelling — mountain trails close and reopen within days.

## Pitfalls

- **餘額 > 0 does not mean bookable.** The 排隊預約 queue has priority and is often hundreds of teams deep; the beds drain before a new application is reached.
- **The foreign quota is first-come, not a lottery.** The `外籍提前` count is what has already been registered; pick dates well under 24, not dates that merely look empty.
- **A 35-day floor silently closes a whole month.** If the trip is less than five weeks out, the foreign channel is gone no matter how many beds show, and the general route is waitlist-only because that date's lottery already ran.
- **Do not quote a bed count without its timestamp.** The calendar is live and changes during the day.
