---
title: Class Quality Assessor
emoji: 🎓
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# Class Quality Assessor

Upload an online-class recording (and its `.vtt` transcript if you have one) to get a Poor / Average / Good / Excellent
verdict with timestamped, evidence-based observations.

* Processing is done inside this Space. Audio, video and frames are not sent to any external service.
* Uploaded files and temporary data are deleted when processing ends; nothing is stored or logged.
* Without a transcript the app transcribes locally (small CPU model, time-capped); the verdict is then less certain and says why.
