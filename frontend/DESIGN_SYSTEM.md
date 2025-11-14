# Athena Nature-Inspired Design System

## Design Philosophy

The Athena dashboard embraces an **organic growth aesthetic** where UI elements use natural patterns: roots anchoring foundations, branches connecting sections, and leaves representing data points. The design creates a living, breathing interface that feels grounded yet dynamic.

**IMPORTANT**: The nature-inspired design applies to **visual elements only** (shapes, colors, animations). All copy and text should remain **simple, clear, and professional**. Use standard business terminology - not nature metaphors.

## Living Document

This design system is a living document. **Any repeatable design pattern changes must be reflected here immediately**. Before implementing design changes:
1. Check if it affects a reusable pattern
2. Update this document first
3. Then implement in code
4. Ensure consistency across all pages

---

## Color Palette: Sage Luxury

```
Roots & Foundation
--earth-dark:    #736E58  (Deep roots, grounding elements)
--earth-black:   #000000  (Text, strongest contrast)

Trunk & Structure
--sage-dark:     #7E9D85  (Primary interactive elements, headers)
--sage-medium:   #9DBB9C  (Secondary elements, borders)

Canopy & Atmosphere
--sage-light:    #E4ECE6  (Backgrounds, subtle surfaces)
--sage-white:    #F8FAF9  (Pure backgrounds - derived)

Growth & Highlights
--gold-accent:   #D6A84E  (Attention, CTAs, highlights)
```

### Color Usage Patterns
- **Backgrounds**: Layer sage-light with subtle gradients mimicking dappled sunlight
- **Interactive Elements**: sage-dark for primary, gold-accent for emphasis
- **Text Hierarchy**: earth-black (primary), sage-dark (secondary), sage-medium (tertiary)
- **Borders**: Use sage-medium with organic curves, never sharp corners

---

## Typography

### Font Families
- **Display/Headers**: 'Fraunces' (serif with organic curves, plant-like terminals)
  - Fallback: 'Crimson Pro', serif
- **Body Text**: 'Libre Baskerville' (readable, elegant serif with warmth)
  - Fallback: 'Georgia', serif
- **UI Elements**: 'Jost' (clean sans-serif for data/metrics)
  - Fallback: 'Avenir', sans-serif

### Type Scale (Growth-Inspired)
```
Root:    12px / 0.75rem  (Small labels, captions)
Sprout:  14px / 0.875rem (Body text, descriptions)
Stem:    16px / 1rem     (Base size, paragraphs)
Branch:  20px / 1.25rem  (H4, card titles)
Limb:    28px / 1.75rem  (H3, section headers)
Trunk:   36px / 2.25rem  (H2, page titles)
Canopy:  48px / 3rem     (H1, hero text)
```

---

## Spatial System: Organic Rhythm

Use Fibonacci-inspired spacing for natural, balanced layouts:
```
8px, 13px, 21px, 34px, 55px, 89px
```

### Layout Patterns
- **Asymmetric Balance**: Avoid perfect grids; let elements "grow" naturally
- **Negative Space**: Generous breathing room (forest floor metaphor)
- **Vertical Flow**: Content flows downward like water through roots

---

## Shape Language

### Primary Motifs

**1. Branching Connections**
```css
/* Curved connectors between elements */
.branch-connector {
  position: relative;
  &::before {
    content: '';
    position: absolute;
    border-left: 2px solid var(--sage-medium);
    border-radius: 0 0 0 12px;
  }
}
```

**2. Organic Curves (No Sharp Corners)**
- Border radius: minimum 8px, prefer 12-20px
- Use asymmetric radii for natural feel: `border-radius: 16px 20px 18px 14px`

**3. Root Anchors**
- Footer elements have subtle "root tendrils" extending downward
- Use dashed/dotted borders with gradient fade: `border-image: linear-gradient(to bottom, sage-dark, transparent)`

**4. Leaf Clusters**
- Group 3-5 small elements in organic arrangements
- Stats/badges as "leaves" on a branch
- Use transforms: `rotate()` slight variations (-3deg to 3deg)

---

## Animation Principles

### Core Animations

**1. Growth from Roots (Page Load)**
```
Duration: 1.2s
Easing: cubic-bezier(0.34, 1.56, 0.64, 1) /* elastic */

1. Roots spread from bottom (0-400ms)
2. Trunk rises (400-700ms)
3. Branches extend (700-1000ms)
4. Leaves/content fade in with stagger (1000-1200ms)
```

**2. Leaf Rustle (Hover/Idle)**
```css
@keyframes leafRustle {
  0%, 100% { transform: rotate(0deg) translateY(0); }
  25% { transform: rotate(1deg) translateY(-2px); }
  75% { transform: rotate(-1deg) translateY(-1px); }
}
/* Apply with random delays for natural effect */
```

**3. Branch Sway (Background Elements)**
```css
@keyframes branchSway {
  0%, 100% { transform: translateX(0) rotate(0deg); }
  50% { transform: translateX(8px) rotate(1deg); }
}
/* Slow: 8s duration */
```

**4. Root Pulse (Loading States)**
```css
@keyframes rootPulse {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 1; }
}
/* Emanate from bottom upward */
```

### Animation Guidelines
- Use staggered delays (100-150ms) for related elements
- Prefer CSS transforms over positional properties
- Keep animations subtle: 1-2deg rotations, 2-4px translations
- Default duration: 0.3s for interactions, 1-3s for ambiance

---

## Component Patterns

### 1. Organic Cards
```tsx
<div className="organic-card">
  {/* Decorative branch in corner */}
  <svg className="branch-decoration" />

  {/* Content with natural flow */}
  <div className="card-content">
    {/* Title as "trunk" */}
    {/* Stats as "leaves" */}
  </div>

  {/* Root anchor at bottom */}
  <div className="root-anchor" />
</div>
```

**Styles:**
- Asymmetric rounded corners
- Subtle box-shadow: `0 4px 20px rgba(115, 110, 88, 0.08)`
- Background: layered gradients for depth
- Decorative SVG branches in corners (sage-medium, 20% opacity)

### 2. Branching Navigation
- Vertical nav as tree trunk (left side)
- Items branch off to the right
- Active state: leaf highlight (gold-accent glow)
- Connectors: curved lines from trunk to items

### 3. Root Footer
- Gradient fade from sage-light to earth-dark
- Dotted "root tendrils" extending into negative space
- Content clusters like root nodules

### 4. Growth Metrics (Stats)
- Numbers grow from 0 with spring animation
- Icon treatment: organic shapes (rounded, flowing)
- Arrange in asymmetric clusters (not rigid grid)
- Background: concentric circles (tree ring metaphor)

### 5. Attention Badges
- Shape: leaf (rounded with pointed tip)
- Color: gold-accent with subtle pulse
- Position: naturally "sprout" from parent element

---

## Decorative Elements

### SVG Motifs (Reusable)

**1. Branch Divider**
```svg
<svg viewBox="0 0 400 40" className="branch-divider">
  <path d="M0,20 Q100,10 200,20 T400,20"
        stroke="currentColor"
        fill="none"
        stroke-width="2"/>
  <circle cx="50" cy="15" r="3" fill="currentColor" opacity="0.6"/>
  <circle cx="180" cy="25" r="3" fill="currentColor" opacity="0.6"/>
  <circle cx="320" cy="18" r="3" fill="currentColor" opacity="0.6"/>
</svg>
```

**2. Leaf Scatter Background**
```tsx
{/* Randomized leaves in background */}
<div className="leaf-scatter">
  {Array.from({length: 12}).map((_, i) => (
    <div
      key={i}
      className="leaf-particle"
      style={{
        left: `${Math.random() * 100}%`,
        top: `${Math.random() * 100}%`,
        animationDelay: `${Math.random() * 3}s`
      }}
    />
  ))}
</div>
```

**3. Root Network (Page Background)**
- Ultra-subtle (5% opacity)
- Organic bezier curves
- Start from bottom, spread upward
- Fixed position, no scroll

---

## Interaction States

### Hover
```css
.interactive-element:hover {
  transform: translateY(-2px) rotate(0.5deg);
  box-shadow: 0 8px 24px rgba(126, 157, 133, 0.15);
  border-color: var(--gold-accent);
}
```

### Focus (Accessibility)
```css
.interactive-element:focus-visible {
  outline: 3px solid var(--gold-accent);
  outline-offset: 4px;
  border-radius: 12px;
}
```

### Active/Selected
```css
.interactive-element.active {
  background: linear-gradient(135deg, var(--sage-dark), var(--sage-medium));
  color: white;
  box-shadow: inset 0 2px 8px rgba(0,0,0,0.1);
}
```

### Disabled
```css
.interactive-element:disabled {
  opacity: 0.4;
  filter: grayscale(50%);
  cursor: not-allowed;
}
```

---

## Accessibility Considerations

1. **Color Contrast**: All text meets WCAG AA (sage-dark on sage-light = 4.8:1)
2. **Motion**: Respect `prefers-reduced-motion` - disable sway/rustle, keep only functional transitions
3. **Focus Indicators**: Gold accent ensures visibility
4. **Semantic HTML**: Decorative SVGs use `aria-hidden="true"`

---

## Copy & Content Guidelines

**The nature-inspired design is VISUAL ONLY.** All copy must be simple, clear, and professional.

### ❌ Avoid Nature Metaphors in Copy
- Don't: "Your Garden", "Plants Needing Attention", "Blooming Projects"
- Don't: "Plant New Seed", "Flourishing", "Tend to clients"
- Don't: "Seasonal Calendar", "Rooted in excellence"

### ✅ Use Professional Business Language
- Do: "Dashboard", "Clients Needing Attention", "Active Projects"
- Do: "Add New Client", "All clients are up to date", "Manage clients"
- Do: "Calendar", "Excellence in service"

### Content Principle
**Visual = Organic. Copy = Clear.**

---

## Implementation Checklist

When creating new pages/components, ensure:

- [ ] Colors from Sage Luxury palette only
- [ ] Typography uses Fraunces/Libre Baskerville/Jost
- [ ] No sharp corners (minimum 8px radius)
- [ ] At least one organic decorative element (branch, leaf, root)
- [ ] Subtle entrance animation with stagger
- [ ] Hover states include slight rotation or translation
- [ ] Spacing follows Fibonacci scale
- [ ] Asymmetric balance in layout
- [ ] Reduced motion fallback for animations
- [ ] **Copy uses professional language, NOT nature metaphors**
- [ ] Actual logo files used (not recreated SVGs)

---

## File Structure
```
/components/nature-ui/
  ├── BranchDivider.tsx
  ├── LeafBadge.tsx
  ├── OrganicCard.tsx
  ├── RootFooter.tsx
  ├── GrowthMetric.tsx
  └── animations.css

/public/decorative/
  ├── branch-patterns.svg
  ├── leaf-shapes.svg
  └── root-network.svg
```

---

## Logo Usage

The Athena logo consists of two elements:
1. **Tree Icon** (`design/!Athena full logo.png` - tree portion): Used standalone in compact spaces
2. **Full Logo** (`design/!Athena full logo.png`): Tree + "athena" wordmark for headers

### Logo Guidelines
- Tree uses the sage green palette
- Maintain aspect ratio (do not stretch)
- Minimum size: 32px height for tree icon
- Clear space: Minimum 8px padding around logo
- Always use the actual logo files, not recreated SVGs

### Logo Locations
- **Header**: Mini tree icon (32-48px) + wordmark
- **Loading Screen**: Full logo (200-300px) with growth animation
- **Favicon**: Tree icon only

---

**Philosophy**: Visual design should feel like it grew naturally, not placed mechanically. Copy should be clear and professional.
