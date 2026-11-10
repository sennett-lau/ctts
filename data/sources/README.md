# Data sources

One card per source. Copy [`_TEMPLATE.md`](_TEMPLATE.md). The `status` in the front matter controls use:
`included` (in at least one mix), `candidate` (not yet used), `partial`, `EXCLUDED` (with reason).

| Card | Status | Approx. hours | Role |
|---|---|---|---|
| [hk-youtube-conversational](hk-youtube-conversational.md) | included | 96.3 (cleaned) | Conversational prosody, particles, code-switching |
| [cv-zh-hk](cv-zh-hk.md) | included | ~53 | HK speaker diversity |
| [mdcc](mdcc.md) | included | ~57 | Clean studio HK read speech |
| [mce](mce.md) | included | ~25 | Cantonese–English code-switching |
| [zoengjyutgaai](zoengjyutgaai.md) | candidate | 40 cap | Long-form storytelling |
| [legco](legco.md) | candidate | ? | Formal register |
| [cv-yue-EXCLUDED](cv-yue-EXCLUDED.md) | EXCLUDED | 0 | Not HK: causes PRD accent |

Hours come from the blueprint and the agent brief. They become verified numbers when P1 builds each source.

## YouTube channels

Channel-level list behind [hk-youtube-conversational](hk-youtube-conversational.md), plus candidates.
"Used" = its train split. "OrcinusOrca" = what the `OrcinusOrca/YouTube-Cantonese` dataset holds for the channel.
"On YouTube" = live count from `yt-dlp --flat-playlist` on 2026-11-10 (only checked for the channels requested that day).

| Channel | URL | Status | Used (h / videos) | OrcinusOrca (videos / h) | On YouTube (2026-11-10) | Content |
|---|---|---|---|---|---|---|
| 阿豬 Ah Ju | https://www.youtube.com/@ahju | included | 19.07 / 122 | 132 / 28.81 | not checked | solo speaker, finance & lifestyle |
| BBO Black Box Office | https://www.youtube.com/@bboblackboxoffice | included | 16.85 / 112 | 122 / 32.66 | not checked | multi-speaker travel & lifestyle |
| Mill MILK | https://www.youtube.com/@mm.millmilk | included | 11.02 / 160 | 958 / 271.25 | not checked | street interviews, features (multi-speaker) |
| mingjai14 | https://www.youtube.com/@mingjai14 | included | 10.60 / 157 | 158 / 43.85 | 479 videos / 107.2 h, 14 streams / 15.1 h | solo narrator, storytelling & HK culture |
| UNWIRE.HK | https://www.youtube.com/@unwire | included | 9.40 / 276 | 345 / 48.53 | not checked | tech reviews, Cantonese–English code-switching |
| The Do Show | https://www.youtube.com/@thedoshow0909 | included | 9.38 / 22 | 23 / 17.78 | 73 videos / 46.6 h | celebrity interviews (Putonghua guests filtered) |
| Price.com.hk 香港格價網 | https://www.youtube.com/@pricehongkongofficial | included | 7.55 / 282 | 959 / 131.94 | not checked | consumer tech reviews |
| JFFLive 床哥心事台 highlights | fan highlight uploads (8 uploaders, not one channel) | included | 12.41 / 50 | not in dataset | – | call-in live stream, heavy slang |
| The MultiTalk | https://www.youtube.com/@themultitalk | **candidate** | – | not in dataset | 488 videos / 385.6 h, 1 stream / 2.8 h | talk and podcast shows, multi-speaker |
| FHProductionHK | https://www.youtube.com/@fhproductionhk | **candidate** | – | not in dataset | public: 418 videos / 80.3 h, 13 streams / 17.6 h (members-only: 117 videos / 9.1 h, 205 streams / 210.4 h) | multi-speaker sketches and variety series, some music videos |

The MultiTalk shows by video count: Sporty Pop Con叻 51, 《吹水》 32, 收市閒情千頌C 32, SPOTITALK 31, Enter Enter 21,
ROOM.33 20, Courtside With Emil 10, the rest fewer than 10. All its videos are 10 min or longer.

FHProductionHK: members-only uploads cannot be downloaded, so only the public part counts. None of 6 sampled
public videos had creator subtitles, so tri-label arbitration would have only two labels (or OCR of burned-in
captions, as for the 床哥 highlights). Music videos need to be dropped and BGM / sound effects removed.

### Other OrcinusOrca channels, not used yet

| Channel (dataset id) | Videos | Hours |
|---|---|---|
| SunChannelHK | 1,160 | 409.18 |
| hieggo1001 | 1,251 | 279.30 |
| greenbeanmediaofficial | 594 | 179.97 |
| MPWeekly | 1,119 | 156.45 |
| JERSON8964 | 500 | 97.60 |
| DangerousPerson2.0 | 114 | 70.53 |
| hkcrime | 99 | 35.06 |
| maviskuku | 165 | 29.21 |
| pinkytalks | 125 | 20.72 |

Not yet checked for HK accent or speaker mix.

### Adding a channel

1. Check it is HK Cantonese and note the speaker mix (solo or multi-speaker).
2. Download audio and creator subtitles. On 2026-11-10, listing channel tabs needed
   `--extractor-args youtubetab:skip=authcheck`. Per-video extraction failed with `KeyError('INNERTUBE_CONTEXT')`
   while a cookies file was loaded from the yt-dlp config; with `--ignore-config` and yt-dlp 2026.10.26 it worked.
3. Label with tri-label arbitration ([`../pipelines/tri-label-arbitration.md`](../pipelines/tri-label-arbitration.md)).
4. For TTS, apply the single-speaker filter (`single_speaker_cos_sim >= 0.75`) to multi-speaker channels.
5. Add the channel to [hk-youtube-conversational](hk-youtube-conversational.md) and to the table above.
