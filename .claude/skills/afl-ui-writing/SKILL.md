---
name: afl-ui-writing
description: The AFL game's UI and writing rules (not boring, visual identity, readability, colour/type/components/copy, consistency, review test). Use before touching any screen, UI copy, layout, colour or vignette framing, even a small one. Moved from CLAUDE.md so it loads only when needed. Extends the general UI rules in docs/VISUAL_STYLE_GUIDE.md.
---

# AFL UI and writing rules

The shared visual language lives in `scripts/ui/UiKit.gd`; use it before
inventing anything local.
The visual identity rules (tokens, type roles, the component kit, screen templates,
art and proof rules) are in [docs/VISUAL_STYLE_GUIDE.md](docs/VISUAL_STYLE_GUIDE.md);
read it before touching any screen or vignette. Its evidence is
[docs/research/VISUAL_AUDIT_2026-10-10.md](docs/research/VISUAL_AUDIT_2026-10-10.md).

**Not boring (director, 2026-10-08: "dark mode doesn't need to be boring
mode").** The UI must have life. Approved pillars: club colour as atmosphere
(your club's colours carry your screens, both clubs' on match day), big type
and motion (the scoreboard face for headline facts; count-ups, reveals,
transitions), and the 2.5D art and textures of the ground beyond the match.
Proposed, to be shown on the hub first: each screen leads with one hero
element. Gradients and glows, colourful
(club-tinted) surfaces and bold decoration (turf, chalk, crowd motifs) are
now allowed when used deliberately; they override the restraint rules below
where the two conflict. Still never at the cost of readability or usability.

**Visual identity.** Avoid dark green/charcoal rounded cards everywhere, gold as
the universal accent, nested rounded rectangles, piles of pills/chips/badges,
every fact in its own card, generic dashboard grids, big corner radii, excess separators, decorative stat boxes and icons. Prefer flat,
editorial layouts: typography, alignment, spacing, restrained surfaces.

**Readability is a pillar (design bible, director 2026-10-13).** It applies to
every screen. Sections feel distinct: club colours and strategic bold set them
apart, because text that is all one colour and weight harms readability. A
player's or club's allegiance is obvious at a glance, without reading the name.
No text the coach needs is overlooked: nothing he decides on sits in uniform
grey. Club colour must stay readable (check contrast for dark clubs on the dark
page) and must not be mistaken for GOOD/BAD or the primary action.

**Colour, type, components, copy.** The exact rules are in
[docs/VISUAL_STYLE_GUIDE.md](docs/VISUAL_STYLE_GUIDE.md): colour and where it goes
(§2.1-2.2), type roles (§2.3), the component kit (§3), copy (§5). Before adding a
pill, card, badge or progress bar, ask whether typography, spacing or alignment
could say it. Font changes are project-wide decisions.

**Consistency.** Reuse what works; don't invent a mini design system per
screen, and don't copy a template-looking pattern because it exists. Apply
these rules whenever a screen is materially touched, without turning that into
an uncontrolled redesign.

**Review test.** Without the AFL names and logos, would the screen still look
like this game, or like any AI-generated sports-management app? If the latter,
simplify it. Authored and restrained, not weird; never at the cost of
usability.
