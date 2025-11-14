# Nature-Inspired Design - Quick Start Guide

## TL;DR

Your dashboard now has a **garden/tree growth theme** with organic shapes, nature-inspired colors, and flowing animations. Everything grows from roots upward.

---

## Visual Identity

**Color Palette**: Sage greens + earth tones + gold accents
**Fonts**: Fraunces (fancy headers) + Libre Baskerville (readable body) + Jost (clean UI)
**Shape**: Rounded, organic, asymmetric (no sharp corners)
**Motion**: Elements "grow" in, leaves "rustle", branches "sway"

---

## Import the Components

```tsx
import {
  OrganicCard,      // Main container component
  GrowthMetric,     // For stats/numbers
  LeafBadge,        // For tags/labels
  BranchDivider,    // Section separator
  GrowingLogo       // Animated logo
} from '@/components/nature-ui'
```

---

## Common Patterns

### 1. Create a Stat Card

```tsx
<GrowthMetric
  label="Active Clients"
  value={25}
  color="sage"  // or "gold" or "earth"
  icon={<Users className="w-full h-full" />}
/>
```

### 2. Create a Content Card

```tsx
<OrganicCard
  className="p-fib4"     // Use Fibonacci spacing
  variant="glass"        // or "default" or "accent"
  withBranch             // Adds decorative branch in corner
  hover                  // Enables lift effect
>
  <h3 className="text-branch font-display text-sage-dark">
    Card Title
  </h3>
  <p className="text-sprout font-ui text-earth-dark/70">
    Card description
  </p>
</OrganicCard>
```

### 3. Add a Badge

```tsx
<LeafBadge variant="warning">  // or "success" or "info"
  Needs attention
</LeafBadge>
```

### 4. Add a Divider

```tsx
<BranchDivider className="my-fib4" />
```

---

## Color Classes (Most Used)

```tsx
// Backgrounds
className="bg-sage-white"        // Page background
className="bg-sage-light"        // Light surfaces
className="bg-sage-dark"         // Primary accent
className="bg-gold-accent"       // Emphasis/warnings
className="bg-white"             // Card surfaces

// Text
className="text-sage-dark"       // Primary interactive text
className="text-earth-dark"      // Body text
className="text-gold-accent"     // Highlights
```

---

## Typography Classes

```tsx
// Fonts
className="font-display"         // Headers (Fraunces - fancy)
className="font-body"            // Long text (Libre Baskerville)
className="font-ui"              // Labels, buttons (Jost)

// Sizes (from small to large)
className="text-root"            // 12px - tiny labels
className="text-sprout"          // 14px - small text
className="text-stem"            // 16px - body
className="text-branch"          // 20px - card titles
className="text-limb"            // 28px - section headers
className="text-trunk"           // 36px - page titles
className="text-canopy"          // 48px - hero text
```

---

## Spacing Classes (Fibonacci Scale)

```tsx
className="p-fib1"               // 8px padding
className="gap-fib2"             // 13px gap
className="mb-fib3"              // 21px margin-bottom
className="p-fib4"               // 34px padding
className="my-fib5"              // 55px margin y-axis
className="mt-fib6"              // 89px margin-top
```

---

## Animations

```tsx
// Add to className
className="animate-leaf-rustle"  // Gentle swaying
className="animate-branch-sway"  // Slow drift
className="animate-root-pulse"   // Fade in/out
className="animate-grow-in"      // Pop in from bottom

// Staggered entrance (inline style)
style={{
  animation: 'growIn 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) 0.2s backwards'
}}

// Change delay for each item:
{items.map((item, idx) => (
  <div style={{ animation: `growIn 0.4s ease ${idx * 0.1}s backwards` }}>
    ...
  </div>
))}
```

---

## Border Radius

```tsx
className="rounded-organic"      // Standard (16px 20px 18px 14px)
className="rounded-organic-sm"   // Small (8px 10px 9px 7px)
className="rounded-organic-lg"   // Large (24px 28px 26px 22px)
```

---

## Utility Classes

```tsx
className="organic-card"         // Pre-styled card (bg + border + shadow)
className="organic-hover"        // Adds lift effect on hover
className="organic-border"       // Rounded border with sage color
```

---

## Page Template (Copy-Paste)

```tsx
export default function MyPage() {
  return (
    <div className="min-h-screen bg-sage-white">
      {/* Header */}
      <header className="bg-gradient-to-r from-white via-sage-light/30 to-white border-b-2 border-sage-medium/20">
        <div className="max-w-7xl mx-auto px-fib4 py-fib3">
          <h1 className="text-limb font-display text-sage-dark">
            Page Title
          </h1>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-fib4 py-fib5">
        {/* Stats Row */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-fib3 mb-fib5">
          <GrowthMetric label="Metric 1" value={42} color="sage" />
          <GrowthMetric label="Metric 2" value={18} color="gold" />
        </div>

        {/* Content Card */}
        <OrganicCard className="p-fib5" withBranch>
          <h2 className="text-branch font-display text-sage-dark mb-fib3">
            Section Title
          </h2>
          <p className="text-sprout font-ui text-earth-dark/70">
            Content goes here
          </p>
        </OrganicCard>
      </main>
    </div>
  )
}
```

---

## Copy Guidelines

**Nature-inspired design is VISUAL ONLY.** Use professional, clear language in all copy:

- ✅ "Dashboard" (not "Garden")
- ✅ "Clients" (not "Plants")
- ✅ "Active Projects" (not "Blooming Projects")
- ✅ "Calendar" (not "Seasons")
- ✅ "Add New Client" (not "Plant Seed")
- ✅ "All clients are up to date" (not "Flourishing")

**Visual = Organic. Copy = Clear.**

---

## Don'ts

- ❌ Don't use sharp corners (always rounded)
- ❌ Don't use colors outside the palette
- ❌ Don't use generic fonts (Inter, Arial, etc.)
- ❌ Don't use even spacing (stick to Fibonacci)
- ❌ Don't create rigid grids (asymmetry is natural)
- ❌ Don't skip entrance animations
- ❌ **Don't use nature metaphors in copy** (visual only!)
- ❌ Don't recreate logo with SVG (use actual logo files)

---

## Design Files

- `DESIGN_SYSTEM.md` - Full design documentation
- `IMPLEMENTATION_SUMMARY.md` - Detailed implementation guide
- `QUICK_START.md` - This file (quick reference)

---

## Example: Converting Generic to Organic

**Before:**
```tsx
<div className="bg-white rounded-lg shadow p-6 border">
  <h3 className="text-xl font-bold mb-2">Title</h3>
  <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded">
    Tag
  </span>
</div>
```

**After:**
```tsx
<OrganicCard className="p-fib4" withBranch hover>
  <h3 className="text-branch font-display text-sage-dark mb-fib2">
    Title
  </h3>
  <LeafBadge variant="info">Tag</LeafBadge>
</OrganicCard>
```

---

## Need Help?

1. Check `DESIGN_SYSTEM.md` for full patterns
2. Look at `app/page.tsx` for working examples
3. Use components from `components/nature-ui/`

**Remember**: Visual design should feel organic and alive. Copy should be clear and professional.
