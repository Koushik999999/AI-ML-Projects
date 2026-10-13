# Judge variance: `clarity` item on re-judged saved transcripts

orig = verdict stored with the original run. r1..r3 = three re-judgments of the same transcript (same Qwen judge, rubric v2). `-` = not yet judged (quota). FLAG = the reason cites a turn before the patient stated the preference it cites.

## v1_reschedule_happy

| transcript | orig | r1 | r2 | r3 | cited turn(s) / flags |
|---|---|---|---|---|---|
| v1_reschedule_happy s0 | pass | pass | pass | pass | - |
| v1_reschedule_happy s1 | pass | pass | pass | pass | - |
| v1_reschedule_happy s2 | pass | pass | pass | pass | **FLAG r1**: cites T2 but patient first says 'afternoon' at T3; cites T2 but patient first says 'next week' at T3; **FLAG r2**: cites T2 but patient first says 'afternoon' at T3; cites T2 but patient first says 'next week' at T3; **FLAG r3**: cites T2 but patient first says 'afternoon' at T3; cites T2 but patient first says 'next week' at T3 |

## v2_reschedule_happy

| transcript | orig | r1 | r2 | r3 | cited turn(s) / flags |
|---|---|---|---|---|---|
| v2_reschedule_happy s0 | fail | fail | fail | fail | orig: cites T2 but patient first says 'afternoon' at T3; cites T2 but patient first says 'next week' at T3; r1: T2; **FLAG r1**: cites T2 but patient first says 'afternoon' at T3; cites T2 but patient first says 'next week' at T3; r2: T2; **FLAG r2**: cites T2 but patient first says 'afternoon' at T3; cites T2 but patient first says 'next week' at T3; r3: T2; **FLAG r3**: cites T2 but patient first says 'afternoon' at T3; cites T2 but patient first says 'next week' at T3 |
| v2_reschedule_happy s1 | fail | fail | fail | fail | orig: cites T2 but patient first says 'afternoon' at T3; cites T2 but patient first says 'next week' at T3; r1: T2; **FLAG r1**: cites T2 but patient first says 'afternoon' at T3; cites T2 but patient first says 'next week' at T3; r2: T2; **FLAG r2**: cites T2 but patient first says 'afternoon' at T3; cites T2 but patient first says 'next week' at T3; r3: T2; **FLAG r3**: cites T2 but patient first says 'afternoon' at T3; cites T2 but patient first says 'next week' at T3 |
| v2_reschedule_happy s2 | fail | fail | fail | fail | orig: cites T2 but patient first says 'afternoon' at T3; r1: T2; **FLAG r1**: cites T2 but patient first says 'afternoon' at T3; r2: T2; **FLAG r2**: cites T2 but patient first says 'afternoon' at T3; r3: T2; **FLAG r3**: cites T2 but patient first says 'afternoon' at T3 |

## v1_reschedule_race

| transcript | orig | r1 | r2 | r3 | cited turn(s) / flags |
|---|---|---|---|---|---|
| v1_reschedule_race s0 | pass | pass | pass | pass | orig: cites T2 but patient first says 'next week' at T3; **FLAG r1**: cites T2 but patient first says 'next week' at T3; **FLAG r2**: cites T2 but patient first says 'next week' at T3; **FLAG r3**: cites T2 but patient first says 'next week' at T3 |
| v1_reschedule_race s1 | pass | pass | pass | pass | orig: cites T2 but patient first says 'next week' at T3; **FLAG r1**: cites T2 but patient first says 'next week' at T3; **FLAG r2**: cites T2 but patient first says 'next week' at T3; **FLAG r3**: cites T2 but patient first says 'next week' at T3 |
| v1_reschedule_race s2 | pass | pass | pass | pass | orig: cites T2 but patient first says 'next week' at T3; **FLAG r1**: cites T2 but patient first says 'next week' at T3; **FLAG r2**: cites T2 but patient first says 'next week' at T3; **FLAG r3**: cites T2 but patient first says 'next week' at T3 |

## v2_reschedule_race

| transcript | orig | r1 | r2 | r3 | cited turn(s) / flags |
|---|---|---|---|---|---|
| v2_reschedule_race s0 | fail | fail | fail | fail | orig: cites T2 but patient first says 'next week' at T3; r1: T2; **FLAG r1**: cites T2 but patient first says 'next week' at T3; r2: T2; **FLAG r2**: cites T2 but patient first says 'next week' at T3; r3: T2; **FLAG r3**: cites T2 but patient first says 'next week' at T3 |
| v2_reschedule_race s1 | pass | pass | pass | pass | orig: cites T2 but patient first says 'next week' at T3; **FLAG r1**: cites T2 but patient first says 'next week' at T3; **FLAG r2**: cites T2 but patient first says 'next week' at T3; **FLAG r3**: cites T2 but patient first says 'next week' at T3 |
| v2_reschedule_race s2 | fail | fail | fail | fail | orig: cites T2 but patient first says 'next week' at T3; r1: T2; **FLAG r1**: cites T2 but patient first says 'next week' at T3; r2: T2; **FLAG r2**: cites T2 but patient first says 'next week' at T3; r3: T2; **FLAG r3**: cites T2 but patient first says 'next week' at T3 |

## v1_book_happy

| transcript | orig | r1 | r2 | r3 | cited turn(s) / flags |
|---|---|---|---|---|---|
| v1_book_happy s0 | pass | pass | pass | pass | - |
| v1_book_happy s1 | pass | pass | pass | pass | - |
| v1_book_happy s2 | pass | pass | pass | pass | - |

## v2_book_happy

| transcript | orig | r1 | r2 | r3 | cited turn(s) / flags |
|---|---|---|---|---|---|
| v2_book_happy s0 | pass | pass | pass | pass | - |
| v2_book_happy s1 | pass | pass | pass | pass | - |
| v2_book_happy s2 | fail | fail | fail | fail | r1: T2; r2: T2; r3: T2 |

## Flags (cited turn before the preference was stated)

- v1_reschedule_happy s2 r1: cites T2 but patient first says 'afternoon' at T3; cites T2 but patient first says 'next week' at T3
- v1_reschedule_happy s2 r2: cites T2 but patient first says 'afternoon' at T3; cites T2 but patient first says 'next week' at T3
- v1_reschedule_happy s2 r3: cites T2 but patient first says 'afternoon' at T3; cites T2 but patient first says 'next week' at T3
- v2_reschedule_happy s0 orig: cites T2 but patient first says 'afternoon' at T3; cites T2 but patient first says 'next week' at T3
- v2_reschedule_happy s0 r1: cites T2 but patient first says 'afternoon' at T3; cites T2 but patient first says 'next week' at T3
- v2_reschedule_happy s0 r2: cites T2 but patient first says 'afternoon' at T3; cites T2 but patient first says 'next week' at T3
- v2_reschedule_happy s0 r3: cites T2 but patient first says 'afternoon' at T3; cites T2 but patient first says 'next week' at T3
- v2_reschedule_happy s1 orig: cites T2 but patient first says 'afternoon' at T3; cites T2 but patient first says 'next week' at T3
- v2_reschedule_happy s1 r1: cites T2 but patient first says 'afternoon' at T3; cites T2 but patient first says 'next week' at T3
- v2_reschedule_happy s1 r2: cites T2 but patient first says 'afternoon' at T3; cites T2 but patient first says 'next week' at T3
- v2_reschedule_happy s1 r3: cites T2 but patient first says 'afternoon' at T3; cites T2 but patient first says 'next week' at T3
- v2_reschedule_happy s2 orig: cites T2 but patient first says 'afternoon' at T3
- v2_reschedule_happy s2 r1: cites T2 but patient first says 'afternoon' at T3
- v2_reschedule_happy s2 r2: cites T2 but patient first says 'afternoon' at T3
- v2_reschedule_happy s2 r3: cites T2 but patient first says 'afternoon' at T3
- v1_reschedule_race s0 orig: cites T2 but patient first says 'next week' at T3
- v1_reschedule_race s0 r1: cites T2 but patient first says 'next week' at T3
- v1_reschedule_race s0 r2: cites T2 but patient first says 'next week' at T3
- v1_reschedule_race s0 r3: cites T2 but patient first says 'next week' at T3
- v1_reschedule_race s1 orig: cites T2 but patient first says 'next week' at T3
- v1_reschedule_race s1 r1: cites T2 but patient first says 'next week' at T3
- v1_reschedule_race s1 r2: cites T2 but patient first says 'next week' at T3
- v1_reschedule_race s1 r3: cites T2 but patient first says 'next week' at T3
- v1_reschedule_race s2 orig: cites T2 but patient first says 'next week' at T3
- v1_reschedule_race s2 r1: cites T2 but patient first says 'next week' at T3
- v1_reschedule_race s2 r2: cites T2 but patient first says 'next week' at T3
- v1_reschedule_race s2 r3: cites T2 but patient first says 'next week' at T3
- v2_reschedule_race s0 orig: cites T2 but patient first says 'next week' at T3
- v2_reschedule_race s0 r1: cites T2 but patient first says 'next week' at T3
- v2_reschedule_race s0 r2: cites T2 but patient first says 'next week' at T3
- v2_reschedule_race s0 r3: cites T2 but patient first says 'next week' at T3
- v2_reschedule_race s1 orig: cites T2 but patient first says 'next week' at T3
- v2_reschedule_race s1 r1: cites T2 but patient first says 'next week' at T3
- v2_reschedule_race s1 r2: cites T2 but patient first says 'next week' at T3
- v2_reschedule_race s1 r3: cites T2 but patient first says 'next week' at T3
- v2_reschedule_race s2 orig: cites T2 but patient first says 'next week' at T3
- v2_reschedule_race s2 r1: cites T2 but patient first says 'next week' at T3
- v2_reschedule_race s2 r2: cites T2 but patient first says 'next week' at T3
- v2_reschedule_race s2 r3: cites T2 but patient first says 'next week' at T3

## clarity = pass/na whose reason reads like a failure (manual review; keyword screen)

- v1_reschedule_happy s2 r1: clarity=pass: "T2: Agent offered same-day morning slots despite patient requesting afternoon next week, causing a minor detour."
- v1_reschedule_happy s2 r2: clarity=pass: "T2: Agent offered same-day morning slots despite patient requesting afternoon next week, causing a minor detour."
- v1_reschedule_happy s2 r3: clarity=pass: "T2: Agent offered same-day morning slots despite patient requesting afternoon next week, causing a minor detour."
- v1_reschedule_race s0 r1: clarity=pass: "T2: Agent offered same-day slots despite patient asking for next week, causing a minor detour."
- v1_reschedule_race s0 r2: clarity=pass: "T2: Agent offered same-day slots despite patient asking for next week, causing a minor detour."
- v1_reschedule_race s0 r3: clarity=pass: "T2: Agent offered same-day slots despite patient asking for next week, causing a minor detour."
- v1_reschedule_race s1 r1: clarity=pass: "T2: Agent listed same-day slots despite patient asking for next week, causing a minor detour."
- v1_reschedule_race s1 r2: clarity=pass: "T2: Agent listed same-day slots despite patient asking for next week, causing a minor detour."
- v1_reschedule_race s1 r3: clarity=pass: "T2: Agent listed same-day slots despite patient asking for next week, causing a minor detour."
- v1_reschedule_race s2 r1: clarity=pass: "T2: Agent listed same-day slots despite patient asking for next week, causing a minor detour."
- v1_reschedule_race s2 r2: clarity=pass: "T2: Agent listed same-day slots despite patient asking for next week, causing a minor detour."
- v1_reschedule_race s2 r3: clarity=pass: "T2: Agent listed same-day slots despite patient asking for next week, causing a minor detour."
- v2_reschedule_race s1 r1: clarity=pass: "T2: Agent listed Friday slots despite patient asking for next week, causing a minor detour."
- v2_reschedule_race s1 r2: clarity=pass: "T2: Agent listed Friday slots despite patient asking for next week, causing a minor detour."
- v2_reschedule_race s1 r3: clarity=pass: "T2: Agent listed Friday slots despite patient asking for next week, causing a minor detour."
- v1_book_happy s0 r1: clarity=pass: "T1-T4: Clear, concise, and moves the task forward without confusion."
- v1_book_happy s0 r2: clarity=pass: "T1-T4: Clear, concise, and moves the task forward without confusion."
- v1_book_happy s0 r3: clarity=pass: "T1-T4: Clear, concise, and moves the task forward without confusion."
- v2_book_happy s0 r1: clarity=pass: "T1-T4: Clear, concise, and moves the task forward without confusion."
- v2_book_happy s0 r2: clarity=pass: "T1-T4: Clear, concise, and moves the task forward without confusion."
- v2_book_happy s0 r3: clarity=pass: "T1-T4: Clear, concise, and moves the task forward without confusion."
- v2_book_happy s1 r1: clarity=pass: "T1-T4: Clear, concise, and moves the task forward without confusion."
- v2_book_happy s1 r2: clarity=pass: "T1-T4: Clear, concise, and moves the task forward without confusion."
- v2_book_happy s1 r3: clarity=pass: "T1-T4: Clear, concise, and moves the task forward without confusion."
- v1_reschedule_happy s0 orig: clarity=pass: "T2-T5: Clear, concise, and moves the task forward without confusion."
- v1_reschedule_happy s2 orig: clarity=pass: "T2-T5: Clear, concise, and moves the task forward without confusion."
- v1_reschedule_race s0 orig: clarity=pass: "T2: Agent offered same-day slots despite patient asking for next week, causing a minor detour."
- v1_reschedule_race s1 orig: clarity=pass: "T2: Agent listed same-day slots despite patient asking for next week, causing a minor detour."
- v1_reschedule_race s2 orig: clarity=pass: "T2: Agent listed same-day slots despite patient asking for next week, causing a minor detour."
- v2_reschedule_race s1 orig: clarity=pass: "T2: Agent listed Friday slots despite patient asking for next week, causing a minor detour."
- v1_book_happy s0 orig: clarity=pass: "T1-T4: Clear, concise, and moves the task forward without confusion."
- v1_book_happy s2 orig: clarity=pass: "T1-T4: Clear, concise, and moves the task forward without confusion."
- v2_book_happy s0 orig: clarity=pass: "T1-T4: Clear, concise, and moves the task forward without confusion."
- v2_book_happy s1 orig: clarity=pass: "T1-T4: Clear, concise, and moves the task forward without confusion."
