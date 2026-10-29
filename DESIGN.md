---
name: WeltScout landing
description: Used-car search for dealers and brokers, with new listings sent to WhatsApp. Marketing site in 7 languages, light and dark.
colors:
  plan-blue: "#0055DC"
  plan-blue-bright: "#0066FF"
  plan-blue-deep: "#0040B1"
  plan-indigo: "#504EC9"
  panel-tint: "#F0F5FD"
  trial-green: "#11764B"
  trial-green-deep: "#065C38"
  trial-mint: "#3DDC97"
  trial-ink: "#06301A"
  night-navy: "#00122E"
  band-steel: "#253650"
  band-cobalt: "#002A82"
  ink-muted: "#5B6471"
  page: "#F5F7FA"
  surface: "#FFFFFF"
  surface-2: "#EEF2F7"
  surface-3: "#E6ECF4"
  dark-page: "#080B10"
  dark-surface: "#10151C"
  dark-ink: "#F4F7FB"
  dark-accent: "#99BFFF"
typography:
  display:
    fontFamily: "Geist, system-ui, sans-serif"
    fontSize: "clamp(40px, 3.6vw, 54px)"
    fontWeight: 600
    lineHeight: 1.02
    letterSpacing: "-0.05em"
    fontFeature: "\"ss01\""
  headline:
    fontFamily: "Geist, system-ui, sans-serif"
    fontSize: "clamp(32px, 4.2vw, 54px)"
    fontWeight: 600
    lineHeight: 1.04
    letterSpacing: "-0.035em"
  price:
    fontFamily: "Geist, system-ui, sans-serif"
    fontSize: "clamp(44px, 4.2vw, 56px)"
    fontWeight: 600
    lineHeight: 1
    letterSpacing: "-0.05em"
    fontFeature: "\"tnum\""
  title:
    fontFamily: "Geist, system-ui, sans-serif"
    fontSize: "24px"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "-0.02em"
  lead:
    fontFamily: "Geist, system-ui, sans-serif"
    fontSize: "19px"
    fontWeight: 400
    lineHeight: 1.6
  body:
    fontFamily: "Geist, system-ui, sans-serif"
    fontSize: "17px"
    fontWeight: 400
    lineHeight: 1.6
  label:
    fontFamily: "Geist, system-ui, sans-serif"
    fontSize: "14px"
    fontWeight: 600
    lineHeight: 1.3
rounded:
  pill: "999px"
  card: "24px"
  panel: "16px"
  small: "12px"
  band: "32px"
spacing:
  sec-y: "clamp(80px, 6.1vw + 56px, 144px)"
  band-y: "clamp(56px, 4.2vw + 40px, 104px)"
  block-gap: "clamp(48px, 3vw + 36px, 80px)"
  sec-head: "clamp(32px, 2.4vw + 24px, 60px)"
  lead-gap: "clamp(12px, 0.6vw + 10px, 20px)"
  card-p: "clamp(20px, 1.15vw + 15.5px, 32px)"
  gutter: "24px"
components:
  button-primary:
    backgroundColor: "{colors.plan-blue}"
    textColor: "{colors.surface}"
    rounded: "{rounded.pill}"
    height: "48px"
    padding: "0 23px"
  button-primary-hover:
    backgroundColor: "{colors.plan-blue-bright}"
  button-primary-active:
    backgroundColor: "{colors.plan-blue-deep}"
  button-secondary:
    backgroundColor: "transparent"
    textColor: "{colors.night-navy}"
    rounded: "{rounded.pill}"
    height: "48px"
  button-secondary-hover:
    backgroundColor: "{colors.surface-2}"
  button-on-color:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.plan-blue-deep}"
    rounded: "{rounded.pill}"
    height: "56px"
  button-nav:
    rounded: "{rounded.pill}"
    height: "44px"
  card:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.card}"
    padding: "{spacing.card-p}"
  panel:
    backgroundColor: "{colors.panel-tint}"
    rounded: "{rounded.panel}"
  card-highlight:
    backgroundColor: "{colors.plan-blue}"
    textColor: "{colors.surface}"
    rounded: "{rounded.card}"
    padding: "{spacing.card-p}"
  pill-trial:
    backgroundColor: "{colors.trial-mint}"
    textColor: "{colors.trial-ink}"
    rounded: "{rounded.pill}"
    padding: "4px 12px 4px 10px"
  proof-band:
    backgroundColor: "{colors.plan-blue}"
    textColor: "{colors.surface}"
    rounded: "{rounded.band}"
    padding: "{spacing.band-y}"
  proof-receipt:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.night-navy}"
    rounded: "{rounded.card}"
    padding: "{spacing.card-p}"
  proof-bar:
    backgroundColor: "{colors.plan-blue}"
    rounded: "{rounded.pill}"
    height: "8px"
  segmented:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.pill}"
    padding: "5px"
  segmented-selected:
    backgroundColor: "{colors.night-navy}"
    textColor: "{colors.page}"
    rounded: "{rounded.pill}"
  input:
    backgroundColor: "{colors.page}"
    textColor: "{colors.night-navy}"
    rounded: "{rounded.small}"
    padding: "13px 14px"
---

# Design System: WeltScout landing

## 1. Overview

**Creative North Star: "The Dealer's Workbench"**

The page should work like a good tool on a dealer's bench: real screenshots of the app, real numbers from those screenshots, prices and the trial in plain sight, nothing that has to be taken on faith. PRODUCT.md puts it as *"Trgovsko praktično: kot dobro orodje za trgovce"* (practical, like a good tool for dealers). The visitor is usually a dealer on the lot or in a small office with a phone in hand, so 390 px is the primary viewport and every section has to read at a glance.

The system is one sans family (Geist) with strong weight and size contrast, a light page in cool greys with white cards, and two committed colour roles. Blue is the action and plan colour; green is the trial, WhatsApp and success colour. Depth comes from hairlines and very soft shadows. Three "blue moments" carry the brand gradient with soft circles and a blue lift: the trial fact card, the proof band ("10 filtrov. 11 držav. 854 zadetkov.") and the Business + plan card. Everything else stays quiet so those three win.

It rejects what PRODUCT.md lists as anti-references: a page that looks AI-made ("generični SaaS, prelivno besedilo, sijoče kroglice, enake kartice z ikonami, Inter povsod"), invented numbers, customer logos or testimonials, and names or logos of foreign portals used as decoration.

**Owner decisions (28. 10. 2026)** override any rule below that would contradict them: the facts strip is four cards with "7 dni" as a blue card; "Priporočamo" is a green pill; Business + is blue; the hero keeps the "★★★★★ 4,9 · več kot 120 podjetij" line; the trial wording is "7 dni brezplačno, brez omejitev"; the proof band is blue.

**Rule changes on 28. 10.** (this document is owned by the design work, not fixed):
- *One Lift* became *Blue Moments*. The owner asked for the facts cards and a blue proof band, so the gradient-with-circles surface now marks three moments instead of one. PRODUCT.md's "sijoče kroglice" is read as glowing decoration scattered over the page; three deliberate brand surfaces are not that.
- The facts strip is cards again (owner), not the hairline strip from the critique.
- Trial pills moved to the price line of every plan; the pricing header pill pair was dropped because the H2 already states the trial.
- One radius scale: pill, 24 card, 16 panel, 12 small, 32 band. The nav, hero frame and mobile menu moved onto it.
- The proof band became a search receipt (owner: "čist predesigniri tole sekcijo"): one paper card with the query, hits per portal, the total, four hits and an on-demand recording. The evidence chips, the stock photo and the long lead are gone; the band stays blue.

**Key Characteristics:**
- Product first: app recordings, the WhatsApp phone, the results list with real prices.
- Two colour roles only: blue acts, green reassures.
- Hairline cards on a light grey page; nested panels are a tint, never a second border.
- One vertical rhythm from tokens (`--sec-y`, `--block-gap`, `--sec-head`, `--lead-gap`), fluid from 390 to 1440 px.
- One orchestrated motion moment (the H1 word reveal), everything else answers the visitor.
- Seven languages, so every component survives the longest of them (de, fr, nl).

## 2. Colors

A cool, light palette: navy ink on pale grey, with one blue that acts and one green that reassures.

### Primary
- **Plan Blue** (#0055DC): every primary button, accent text (eyebrows, links, plan names), the Business + card gradient start, the top announcement bar. In dark theme accent text switches to Dark Accent; buttons stay Plan Blue.
- **Bright Blue** (#0066FF): hover state of primary buttons only. Colour lifts on hover; position never does.
- **Deep Blue** (#0040B1): pressed primary buttons, and text on white buttons placed on coloured surfaces.
- **Plan Indigo** (#504EC9): end of the Business + gradient (160deg from Plan Blue). Used nowhere else.

### Secondary
- **Trial Green** (#11764B): the second H1 line ("Novi oglasi naravnost na tvoj WhatsApp."), the trial figure on the facts strip. Canonical value: `color-mix(in srgb, --ok 80%, --ok-hi)` (token `--ok-tx`), 5.3:1 on the page. In dark theme it is Trial Mint.
- **Trial Green Deep** (#065C38): success messages and prices inside product mocks (`--ok`, `--paper-ok`).
- **Trial Mint** (#3DDC97): fill of every trial pill ("7 dni brezplačno", "Brez kartice"), the "Priporočamo" badge, dark-theme green text.
- **Trial Ink** (#06301A): text on Trial Mint.

### Tertiary
- **Night Navy** (#00122E), **Band Steel** (#253650), **Band Cobalt** (#002A82): the band gradient (`--g-hero-noc`, 135deg) for the closing band (the proof band uses the Blue Moments gradient). Night Navy is also the light-theme ink.

### Neutral
- **Page** (#F5F7FA): light page background. **Surface** (#FFFFFF): cards, nav pill, form card. **Surface 2/3** (#EEF2F7, #E6ECF4): hover fills, chips, quiet buttons.
- **Panel Tint** (#F0F5FD): nested panels inside cards; canonical value `color-mix(in oklch, --acc 6%, --surf)` (`--panel-bg`).
- **Ink Muted** (#5B6471): secondary text and small print (`--tx2`, `--tx3` in light).
- Hairlines: `rgba(0,18,46,.08 / .13 / .2)` (`--line`, `--line2`, `--line3`); white at .07/.12/.2 in dark.
- **Dark Page / Dark Surface / Dark Ink** (#080B10, #10151C, #F4F7FB): the dark theme; **Dark Accent** (#99BFFF) for accent text there.

### Named Rules
**The Two Roles Rule.** Blue means "do this" (buttons, plan emphasis, links). Green means "this is safe" (trial, no card, WhatsApp, success). Never swap them, and never add a third accent.

**The Text Is Solid Rule.** Text is always one solid colour. Gradients belong to surfaces (the Business + card, the bands), never to letters.

**The Green Contrast Rule.** Green text on the light page is Trial Green or darker (≥ 4.5:1). Trial Mint is a fill, not a light-theme text colour.

## 3. Typography

**Display Font:** Geist (with system-ui, sans-serif), weights 400 to 700, stylistic set `ss01`.
**Body Font:** Geist.

**Character:** One technical sans carries everything. Hierarchy comes from size jumps and tight negative tracking on headings, not from a second family.

### Hierarchy
- **Display** (600, clamp(40px, 3.6vw, 54px) at ≥1200 px, clamp(44px, 4.4vw, 64px) between 601 and 1199 px, clamp(32px, 10vw, 38px) on phones; line-height 1.02; tracking −0.05em): the hero H1 only. Two sentences: a neutral first line and a bold (700) green second line. In the light theme the second line is Trial Ink (#06301A) on a Trial Mint highlighter band over the lower 38% of every row (`box-decoration-break: clone`; 8.2:1 on the mint, 13.5:1 on the page; mint text alone would be 1.65:1); background only, so rows and `--fit` do not change. In the dark theme it stays Trial Mint text. Each sentence stays at most 3 lines at 390 px in all 7 languages. **H1 fit:** the keyword line (first sentence) never takes a third row at 320, 390 or 1440 px. `<h1 style="--fit:N">` holds the width in em that this line needs for two rows, and the two lines are sized `min(1em, 100cqi / var(--fit))` with the H1 as an inline-size container: where the line already fits, the breakpoint size above stays (sl), otherwise both lines shrink together just enough. The green line (second sentence) gets two rows the same way, but only while that keeps the H1 at least as large as the smallest H1 the keyword lines already need in any language (the largest keyword-line `--fit`); a longer green line keeps its third row rather than shrinking the heading further (fr). `deploy/h1_fit.py` measures `--fit` in a browser and writes it into the 7 sources; run it after any change to the H1 copy.
- **Headline** (600, clamp(32px, 4.2vw, 54px), 1.04, −0.035em, max 20ch, balanced wrap): section h2. The proof band's numbers are the one larger statement (clamp(40px, 4.8vw, 64px), −0.045em, line-height 1, tabular figures).
- **Price** (600, clamp(44px, 4.2vw, 56px), 1, −0.05em, tabular figures): plan prices.
- **Title** (600, 20 to 30px, 1.2, −0.02em): card titles, plan names (20px), tab panel heading (30px).
- **Lead** (400, 19px, 1.6, max 58ch, pretty wrap; the hero lead is 17px on phones): the line under a heading.
- **Body** (400, 17px, 1.6): running text; keep lines under 75ch.
- **Label** (600, 13 to 14px, sentence case): eyebrows in accent blue, card labels in muted ink. Small print is 13px muted ink.

### Named Rules
**The Sentence Case Rule.** No tracked all-caps labels. Eyebrows and labels are sentence case, 14px, weight 600.

**The Longest Language Rule.** Size type for German, French and Dutch, not Slovenian. If a heading breaks badly in one language, change the size token or the copy, never add a per-language override.

## 4. Elevation

A hybrid of hairlines and very soft ambient shadow. At rest a card is a white surface with a 1px hairline (`--line2`) and an ambient shadow you notice only when it is missing. In dark theme the shadow becomes a faint outer hairline. Exactly one element per page is lifted: the Business + card with its blue shadow. Bands are flat colour.

### Shadow Vocabulary
- **Card** (`box-shadow: inset 0 0 0 1px var(--line2), var(--sh)`; light `--sh` = `0 1px 2px rgba(0,18,46,.05), 0 8px 24px -12px rgba(0,18,46,.12)`): every card (token `--card-sh`).
- **Large** (`--sh-lg` = `0 2px 4px rgba(0,18,46,.04), 0 40px 80px -32px rgba(0,30,90,.28)`): the open FAQ item and the hero app frame.
- **Lifted** (`--hl-sh`: `0 30px 70px -30px color-mix(in srgb, var(--blue-600) 70%, transparent), inset 0 0 0 1px rgba(255,255,255,.16)`): the three blue moments only.
- **Button** (`inset 0 1px 0 rgba(255,255,255,.2), 0 1px 2px rgba(0,18,46,.18), 0 8px 18px -10px color-mix(in srgb, var(--blue-600) 60%, transparent)`): primary buttons; pressed swaps it for `inset 0 2px 5px rgba(0,8,53,.35)`.

### Named Rules
**The Blue Moments Rule.** Exactly three surfaces carry the Plan Blue to Plan Indigo gradient with soft white circles and the Lifted shadow: the "7 dni" fact card, the proof band and the Business + card. Nothing else glows: no halo behind the hero frame, no glow on badges, no circles on the closing band.

**The Tint-Not-Border Rule.** A panel inside a card (trial panel, FAST price, bento visual, tab screenshot, the "Primer" note) is a tint with radius 16px and no border. Two concentric borders read as a card inside a card.

## 5. Components

### Buttons
Tactile and calm: a pill that changes colour, never jumps.
- **Shape:** full pill (999px).
- **Sizes:** 44px in the nav and small asides, 48px by default (pricing, FAST, contact, WhatsApp section, mobile menu), 56px for the hero and the closing band. Padding is about 0.48 × height; label 16px weight 600 (15px at 44, 17px at 56 on the closing band).
- **Primary:** Plan Blue with a faint top highlight (`linear-gradient(180deg, rgba(255,255,255,.16), transparent 62%)`), white label, Button shadow.
- **Hover / Pressed / Focus:** hover is Bright Blue; pressed is Deep Blue with an inset shadow; focus is a 2px accent outline at 3px offset (white on coloured surfaces).
- **Secondary:** transparent with a `--line3` hairline and ink label; hover fills Surface 2.
- **On colour:** on the Business + card and the closing band, primary becomes white with a Deep Blue label, and secondary becomes a translucent white outline.
- **Text link:** accent colour, weight 600, 1px underline at 4px offset, thickening to 2px on hover; links that lead on carry an arrow that moves 3px right on hover.

### Hero hook, buttons and FAST card
- **Hook line:** one bold line (17px, weight 600, ink) between the hero lead and the buttons says what WeltScout replaces and how long the setup takes ("v eni minuti" only for setting up the search, as the Trije koraki section states; never for results).
- **Hero buttons:** always one row from 601 px in every language. The hero is two columns (copy | stage) from 1200 px; its copy column is never narrower than the button row (`minmax(min-content, .82fr)` with a nowrap row), so each language takes the width its own labels need and nothing is set per language. Below 1200 px the hero is one column (copy up to 680px, stage under it); on phones (≤600 px) the buttons stack. The demo button reads play icon, a short label ("Kako deluje") and the duration in muted ink ("56 s").
- **Hero trial lines:** under the buttons one list row: the two trial pills ("7 dni brezplačno", "Brez kartice", Trial Mint, 14px) and the price beside them at the same 14px in ink weight 600 with tabular figures ("Nato od 129,90 € na mesec."); on phones it wraps 2 + 1. The trial condition ("Poln dostop, ko ob registraciji vpišeš podjetje in kanal za obvestila.") stays visible as one muted 13px line under it. The price never leaves the area next to the CTA.
- **FAST:** its own card under the plans in the pricing language: eyebrow, plan-size name (clamp(28px, 2.6vw, 40px)), description at 17px, and a tint panel with the offer line in price type ("Po dogovoru", no invented price) and a primary button.

### Chips and pills
- **Trial pill:** Trial Mint fill, Trial Ink label, check mark before the text, everywhere (top bar, hero note, plan cards, closing band). On every plan card the trial sits right under the price line as two pills, "7 dni brezplačno, brez omejitev" and "Brez kartice" (14px), followed by the plan's own note in muted text. The long pill may wrap; its radius (1.1em) keeps a single line a full pill and two lines a soft capsule. The closing band uses 15px.
- **Filter chips** (contact interests): pill, Surface 2; selected is Night Navy with page-coloured text. The proof band writes its filters as one line of text instead.
- **Segmented control** (billing toggle, "Trije koraki" tabs): a white pill track with a hairline; the selected segment is a Night Navy pill. On phones the tabs become separate wrapping pills.

### Cards / Containers
- **Corner Style:** one scale. Full pill for buttons, chips and the segmented control; 24px for every standalone card, the nav bar, the hero app frame and the mobile menu; 16px for nested panels and media inside cards; 12px for small things (fields, screenshots inside panels, flag tiles, the skip link); 32px for full-width bands (24px under 900 px).
- **Background:** Surface on the light page, Dark Surface in dark theme.
- **Shadow Strategy:** the Card shadow (see Elevation); the Lifted one only on the three blue moments.
- **Border:** the 1px hairline is part of the Card shadow; nested panels have no border.
- **Internal Padding:** `--card-p` (20px at 390 to 32px at 1440). Cards with a media panel use 12px around the panel and `--card-p` for text.
- **Highlighted card:** the Business + card and the "7 dni" fact card. Plan Blue to Plan Indigo gradient (`--hl-bg`) with two soft white circles top right, white text throughout (secondary text white too, because the circles lower contrast).

### Inputs / Fields
- **Style:** page-coloured fill, 1px slate-500 stroke, radius 12px, 16px text (no zoom on iOS), padding 13px 14px, labels above in 14px weight 600.
- **Focus:** border Bright Blue plus a 4px blue ring at 18% opacity.
- **Error:** border `#C2410C`, inline message checked on blur in plain language; a failed send keeps every value and offers the e-mail address.
- **Sending:** the submit button is disabled with a 16px spinner and "Pošiljam …"; one request at a time (a second submit is ignored).
- **Sent:** the fields give way to a confirmation in the same card, held at the card's height so nothing below moves: a green check in a 12% Trial Green disc draws itself (circle 0.45 s, tick 0.3 s) with one soft ring, the heading "Sporočilo je poslano." (clamp(26px, 2.4vw, 34px)) takes focus, the reply line names the channel and the address the visitor typed (no reply time: no page promises one), then "Medtem preizkusi brezplačno" (primary) and "Pošlji novo sporočilo" (secondary, resets the form and returns focus to the first field). A live region reads the reply line. Reduced motion, `?still` and the motion switch show the check already drawn.
- **Send failed:** the same card in red at the same held height, so nothing below moves on failure either: an alert icon in a 10% red disc, the heading "Sporočila ni bilo mogoče poslati." takes focus (`role="alert"`), the text says the message is still in the form and offers info@weltscout.com, then "Poskusi znova" (primary, sends the same values again with the spinner) and "Uredi sporočilo" (secondary, brings back the filled fields and focuses the message). The e-mail field carries the server's own pattern, so an address the server would refuse is caught in the field first. Red is `--fail` on the form (#B42318 light, #FDA29B dark, the inline error colours).

### Navigation
- **Top bar:** full-width Plan Blue band with the trial offer, a mint "Brez kartice" pill and an underlined "Začni zdaj →" link; rotates messages and has a pause control.
- **Nav:** a white floating bar (radius 24px) with text links (hover Surface 2), language switch with flags, "Prijava", and a 44px primary button. On phones a burger opens a card menu with a 48px button and language chips; the current language keeps its ink fill, including on hover.

### Facts strip (signature)
Four fact cards in a row (2×2 on tablets and phones), label in muted 13px, figure in 28 to 36px weight 600 with tabular figures, one line of explanation. The trial card ("7 dni") is a blue moment (`--hl-bg`, Lifted shadow, white text); the other three are plain cards. Owner decision, 28. 10.

### Proof band (signature)
The "10 filtrov. 11 držav. 854 zadetkov." section is the large blue moment: a full-width band (radius 32px) in the Plan Blue to Plan Indigo gradient with soft circles (`--hl-band`) and the Lifted shadow, identical in light and dark. Inside it sits one paper card that reads like the receipt of one real search, so the visitor can check every number himself. Rebuilt on 28. 10. after the owner rejected the chips, photo and recording-as-hero version.
- **Statement:** white eyebrow and the three numbers as the H2 (clamp(40px, 4.8vw, 64px), weight 600, tracking −0.045em, line-height 1) on the left; on the right, bottom-aligned, one short sentence as the lead (Blue 100, max 40ch) and the recording date with the app's default filter in 13px small print. No other copy.
- **Receipt card:** paper (white; #ECEEF1 in dark), radius 24px, `--card-p`, the large soft shadow (`--sh-lg`), not the Lifted one. Inside the card `--acc` is Plan Blue and `--panel-bg` is the blue tint on paper, so focus rings and the panel keep their contrast in dark theme too.
  - **Query:** a 16px-radius tint panel with a search icon, the saved search name ("Audi A4 Avant TDI 2019+", 20px weight 600) and the 10 filters as one line of running text separated by middots (a list, separators are decorative). No chips. The 44px primary button "Poglej posnetek iskanja · 56 s" sits on the right (full width under the filters on phones; under 360px the duration is dropped and the label may wrap).
  - **Hits per portal:** one row per portal exactly as the app counts them in the final frame of the recording: flag, portal (15px weight 600), country (13px muted), an 8px Plan Blue bar on a blue tint track whose length is the row's share of the total, and the number (16px, tabular). Sorted by count. Portals with 0 hits never get rows: they share one muted line under the list ("Avto.net, Njuškalo, AutoScout24 NL in LU: za ta filter brez zadetkov"), because four rows of 0 read as a fault to the SI and HR buyer.
  - **Total:** "Skupaj 854" under a 2px ink rule, the number 22px weight 700. The rows must add up to it, and it must equal the H2 and the "4 od 854" heading: whoever changes one number re-adds all of them in all 7 languages.
  - **Sample:** "4 od 854 zadetkov tega iskanja" with four results (flag, title, year · km · kW, portal and country, price in Trial Green Deep), no photos: the recordings show only two of the four cars.
  - **Recording:** closed by default. The card button, or any link with `data-play` (the hero's "Kako deluje" button), opens it inline under the query, plays it muted with native controls and moves focus to it; the hero link also scrolls the card into view. The speed-up note sits beside it (under it below 900px). Without JavaScript the recording is simply shown.
- **Layout:** query on top; below it two columns (hits per portal | sample) split by a hairline from 1101px, one column under that.

### Product mocks (signature)
The hero app frame (browser chrome around a real 27. 10. recording, enlargeable on click: a 44px Plan Blue circle (`--blue-600`, `--blue-500` and a 1.06 scale on hover) with a white expand glyph and a 2px white ring sits in the frame's bottom-left corner, always visible, on touch too; the cursor is a plain pointer; a portrait still from the phone recording on screens ≤ 600px, the results still on larger screens) and the WhatsApp phone with a real listing. They are the strongest proof on the page; keep them sharp and never decorate them.

### Footer
The page ends on the brand, on Surface (Dark Surface in dark), with no gradient: the closing band right above it already carries the trial and the main button, so the footer does not repeat them. Rebuilt on 28. 10.
- **Brand column:** logo, the one-sentence claim as a statement (clamp(18px, 0.6vw + 15px, 22px), ink, max 28ch), e-mail, the social icons from `{{SOCIAL}}` (build.py) and the ★ 4,9 line.
- **Cookie consent:** a compact card bottom right from 900px; on phones a bottom bar edge to edge (one short sentence: purpose, provider, only with consent, plus the cookie-policy link; 13px/1.3 text, two equal 44px buttons "Sprejmem" / "Zavrnem" side by side, 6px padding plus the safe area), 96px or about 12% of the viewport, so the H1 and the primary button stay above it at 390 × 844 in all 7 languages and at 360 × 740 wherever the hero leaves the room (not nl and fr, whose button ends 67 and 13px above the screen edge). Nothing is pre-selected; both choices look the same.
- **Link columns:** "Izdelek" and "Podjetje", titles 14px weight 600 in muted ink as `h2` (they follow the page's h2 sections, so heading order holds), links 16px with 40px rows; the cookie-settings control looks like a link. Both columns stay visible on phones, side by side.
- **Utility row:** languages with flags (the current one framed) on the left, the theme switch on the right; then the legal line on its own under a hairline.
- **Wordmark:** "WeltScout" as the closing graphic, Geist 600, tracking −0.07em, sized to the footer's content width with container units (`100cqi / 4.45`), in the panel tint (`--panel-bg`), cut by the footer's bottom edge. It is drawn as CSS generated content on an empty `aria-hidden` element: a logotype used as decoration, so it carries no contrast requirement and is not text for assistive technology. No new token.

### Motion
- **One page-load moment:** the first H1 sentence rises word by word (opacity and translateY only, 600ms each, stagger ≤ 60ms) and the second lands as one line; everything settles within 1s. Hyphenated compounds keep their break point. The stage (recording, phone, caption, motion switch) rises 14px without fading, so its small text never passes through a low-contrast frame; the copy column fades. The offscreen pause of the hero applies only after this entrance has finished, so leaving the hero early never freezes it half faded.
- **Response motion:** pressed buttons, FAQ open/close, tab progress, the rotating top bar, autoplaying recordings only while visible, and the proof receipt's portal bars, which grow once from the left when the list enters the view (transform only, 0.5s each with a 40ms stagger, all done within 0.8s). Numbers never count up there. The hero visual opens large on click (a native modal over a dark veil blurred 10px): it grows from the thumbnail's own box to the centre in 400ms with the ease-out expo and shrinks back to it on close (X, Esc, the veil, the browser's back button). A close during the opening reverses from wherever the animation is. On phones (width or height ≤ 600px) only the app frame opens, edge to edge, so the WhatsApp phone no longer covers the recording; it grows from the frame and shrinks back into it. Opening adds one history entry without changing the URL, so the back button closes it; X, Esc and the veil step back only over that entry, and `#dokaz` or any other hash stays. Focus goes to Close and back to the trigger. Reduced motion, `?still` and the motion switch only fade (200ms).
- **Primary CTA arrow:** hidden on the compact nav button on phones and on every primary button at 360 px and below, where the longest labels need the room.
- **Primary CTA states:** every primary button (hero, nav, plans, closing band) carries the arrow; hover and focus show a Bright Blue halo and move the arrow 4 px; pressed scales to .98. No positional lift: buttons still do not jump. Only the hero button moves on its own.
- **Hero CTA pulse:** the one attention signal on the page. A Bright Blue ring expands from the button and fades (box-shadow, 1.2 s), the button swells to 1.04 and back (transform, 0.7 s) and a sheen crosses it (background-position, 0.9 s). First 0.8 s after the button comes into view, then every 3.5 s (one pulse per 3.5 s, far under the three-flashes limit). It stops when the button leaves the view and comes back with it, stops at once with the motion switch, and never returns after the first hover or focus. The sheen is capped so the label keeps at least 4.5:1 at every frame. Reduced motion and `?still`: no pulse. No other button pulses.
- **Easing:** `cubic-bezier(.16,1,.3,1)` (ease-out expo). No bounce.
- **Respect:** `prefers-reduced-motion` and `?still` show the final static state; the "Ustavi gibanje" control pauses every animation and recording, and remembers the choice.

## 6. Do's and Don'ts

### Do:
- **Do** use Plan Blue (#0055DC) for every action and Trial Green / Trial Mint for every trial, WhatsApp and success message.
- **Do** put spacing on the tokens: `--sec-y` between sections (one gap, never two paddings back to back), `--block-gap` inside a section, `--sec-head` under a heading block, `--lead-gap` under a heading.
- **Do** give every standalone card radius 24px, the Card shadow and `--card-p` padding; give nested panels radius 16px and a tint only.
- **Do** check every text colour on a gradient or image by sampling the pixels under it; axe cannot measure those.
- **Do** design at 390 px first and test 320, 390 and 1440 px in all 7 languages, light and dark.
- **Do** show the product with real recordings and real numbers from those recordings.

### Don't:
- **Don't** make a page that looks AI-made: "generični SaaS, prelivno besedilo, sijoče kroglice, enake kartice z ikonami, Inter povsod" (PRODUCT.md). Concretely: no gradient or shimmering text, no glowing orbs or halos, no grid of identical icon cards, no Inter.
- **Don't** invent numbers, customer logos or testimonials ("Izmišljene številke, logotipi strank in pričevanja").
- **Don't** use names or logos of foreign portals as decoration ("Imena in logotipi tujih portalov", D15); portals appear only where the product shows them.
- **Don't** make speed or "unlimited" claims (D19); the trial wording "7 dni brezplačno, brez omejitev" is an owner decision and is the only exception.
- **Don't** put soft circles or coloured glows on anything but the three blue moments (the "7 dni" fact card, the proof band, the Business + card).
- **Don't** nest a bordered panel inside a bordered card.
- **Don't** move buttons on hover; change their colour.
- **Don't** use tracked all-caps labels or an eyebrow chip above the H1.
- **Don't** add a third accent colour, and don't use Trial Mint as text on the light page.
