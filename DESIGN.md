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
  field: "12px"
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
    padding: "8px 18px 8px 14px"
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
    rounded: "{rounded.field}"
    padding: "13px 14px"
---

# Design System: WeltScout landing

## 1. Overview

**Creative North Star: "The Dealer's Workbench"**

The page should work like a good tool on a dealer's bench: real screenshots of the app, real numbers from those screenshots, prices and the trial in plain sight, nothing that has to be taken on faith. PRODUCT.md puts it as *"Trgovsko praktično: kot dobro orodje za trgovce"* (practical, like a good tool for dealers). The visitor is usually a dealer on the lot or in a small office with a phone in hand, so 390 px is the primary viewport and every section has to read at a glance.

The system is one sans family (Geist) with strong weight and size contrast, a light page in cool greys with white cards, and two committed colour roles. Blue is the action and plan colour; green is the trial, WhatsApp and success colour. Depth comes from hairlines and very soft shadows, never from glows. One element per page section may be "lifted" (the Business + plan card); everything else stays quiet so that card wins.

It rejects what PRODUCT.md lists as anti-references: a page that looks AI-made ("generični SaaS, prelivno besedilo, sijoče kroglice, enake kartice z ikonami, Inter povsod"), invented numbers, customer logos or testimonials, and names or logos of foreign portals used as decoration.

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
- **Night Navy** (#00122E), **Band Steel** (#253650), **Band Cobalt** (#002A82): the band gradient (`--g-hero-noc`, 135deg) for the proof band and the closing band. Night Navy is also the light-theme ink.

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
- **Display** (600, clamp(40px, 3.6vw, 54px) at ≥980 px, clamp(44px, 4.4vw, 64px) between 601 and 979 px, clamp(32px, 10vw, 38px) on phones; line-height 1.02; tracking −0.05em): the hero H1 only. Two sentences: a neutral first line and a bold (700) Trial Green second line. Each sentence stays at most 3 lines at 390 px in all 7 languages.
- **Headline** (600, clamp(32px, 4.2vw, 54px), 1.04, −0.035em, max 20ch, balanced wrap): section h2.
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
- **Lifted** (`0 30px 70px -30px color-mix(in srgb, var(--blue-600) 70%, transparent), inset 0 0 0 1px rgba(255,255,255,.16)`): the Business + card only.
- **Button** (`inset 0 1px 0 rgba(255,255,255,.2), 0 1px 2px rgba(0,18,46,.18), 0 8px 18px -10px color-mix(in srgb, var(--blue-600) 60%, transparent)`): primary buttons; pressed swaps it for `inset 0 2px 5px rgba(0,8,53,.35)`.

### Named Rules
**The One Lift Rule.** Only the Business + card has a coloured shadow and soft circles. No glows on badges, facts or bands.

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

### Chips and pills
- **Trial pill:** Trial Mint fill, Trial Ink label, check mark before the text. Large in the pricing header (17px) and closing band (15px), small inside plan cards (14px).
- **Filter chips** (proof band, contact interests): pill, Surface 2 or translucent white; selected is Night Navy with page-coloured text.
- **Segmented control** (billing toggle, "Trije koraki" tabs): a white pill track with a hairline; the selected segment is a Night Navy pill. On phones the tabs become separate wrapping pills.

### Cards / Containers
- **Corner Style:** 24px for every standalone card; 16px for nested panels and media inside cards.
- **Background:** Surface on the light page, Dark Surface in dark theme.
- **Shadow Strategy:** the Card shadow (see Elevation); the Lifted one only on Business +.
- **Border:** the 1px hairline is part of the Card shadow; nested panels have no border.
- **Internal Padding:** `--card-p` (20px at 390 to 32px at 1440). Cards with a media panel use 12px around the panel and `--card-p` for text.
- **Highlighted card:** Business + only. Plan Blue to Plan Indigo gradient with two soft white circles top right, white text throughout (secondary text white too, because the circles lower contrast).

### Inputs / Fields
- **Style:** page-coloured fill, 1px slate-500 stroke, radius 12px, 16px text (no zoom on iOS), padding 13px 14px, labels above in 14px weight 600.
- **Focus:** border Bright Blue plus a 4px blue ring at 18% opacity.
- **Error:** border `#C2410C`, inline message checked on blur in plain language; a failed send keeps every value and offers the e-mail address.

### Navigation
- **Top bar:** full-width Plan Blue band with the trial offer, a "Brez kartice" pill and an underlined "Začni zdaj →" link; rotates messages and has a pause control.
- **Nav:** a white floating pill with text links (hover Surface 2), language switch with flags, "Prijava", and a 44px primary button. On phones a burger opens a card menu with a 48px button and language chips; the current language keeps its ink fill, including on hover.

### Facts strip (signature)
Four facts in one hairline-divided strip (top and bottom rules, vertical hairlines between cells; 2×2 on tablets, label-and-value rows on phones). Emphasis is colour only: the trial figure ("7 dni") is Trial Green. No cards, no gradient.

### Product mocks (signature)
The hero app frame (browser chrome around a real 27. 10. recording; a portrait still from the phone recording on screens ≤ 600px, the results still on larger screens) and the WhatsApp phone with a real listing. They are the strongest proof on the page; keep them sharp and never decorate them.

### Motion
- **One page-load moment:** the first H1 sentence rises word by word (opacity and translateY only, 600ms each, stagger ≤ 60ms) and the second lands as one line; everything settles within 1s. Hyphenated compounds keep their break point.
- **Response motion:** pressed buttons, FAQ open/close, tab progress, the rotating top bar, autoplaying recordings only while visible.
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
- **Don't** put soft circles or coloured glows on anything but the Business + card.
- **Don't** nest a bordered panel inside a bordered card.
- **Don't** move buttons on hover; change their colour.
- **Don't** use tracked all-caps labels or an eyebrow chip above the H1.
- **Don't** add a third accent colour, and don't use Trial Mint as text on the light page.
