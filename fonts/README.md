# Vendored font check (the Atkinson subsets are broken)

`fonts/atkinson-0.woff2` and `fonts/atkinson-2.woff2` cannot render Latin text.

Both cmap subtables (platform 0/3 and 3/1) map every codepoint **+0x100** into
the Private Use Area. `cmap[0x41]` is `None`; `cmap[0x100]` is `Amacron`. So
`A`, `B`, `F`, `M`, `P`, every digit, `.` `,` `%` and the French accents are all
unmapped, and the browser silently substitutes a fallback face.

## Why the obvious checks pass

- `document.fonts` reports `loaded`, and `document.fonts.check(...)` is `true`:
  the file downloads and parses.
- The canvas width probe says every character is "in the font": comparing
  `"Inter", sans-serif` against `sans-serif` gives the same width because the
  family is not present, so the browser falls through to the generic. A
  measurement that only compares against a generic cannot detect a missing
  face.
- The **live blog** has been shipping these files: `blog/blog.css` declares
  `font-family:'Atkinson Hyperlegible'` and the rendered text is a fallback,
  not Atkinson.

Only a no-fallback render shows it: `font-family:'Atk'` with nothing after it
draws real letterforms (the browser still finds a system face) but
`fontTools` shows the codepoints simply do not exist in the file. The
authoritative signal is the cmap table, and a rendered screenshot is the
confirmation.

## What was done instead

`fonts/inter-latin.woff2` + `fonts/inter-latin-ext.woff2` (Inter, variable
100-900, latin + latin-ext) are now vendored and `@font-face`d from
`index.html`'s own `<style>`. Verified in-browser: 0 substituted glyphs, the
only font request is `/fonts/inter-latin.woff2`, and no `fonts.googleapis`
request remains.

The broken Atkinson files were left in place — `blog/blog.css` still points
at them. **Fixing the blog's font is outstanding work.**

## Checks that would have caught this

```python
from fontTools.ttLib import TTFont
cmap = TTFont('fonts/atkinson-0.woff2').getBestCmap()
missing = [c for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,"
           if ord(c) not in cmap]
assert not missing, f"unmapped ASCII: {missing}"
```
