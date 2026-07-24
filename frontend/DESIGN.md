---
name: Enterprise Precision
colors:
  surface: '#f7f9fb'
  surface-dim: '#d8dadc'
  surface-bright: '#f7f9fb'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f4f6'
  surface-container: '#eceef0'
  surface-container-high: '#e6e8ea'
  surface-container-highest: '#e0e3e5'
  on-surface: '#191c1e'
  on-surface-variant: '#44474c'
  inverse-surface: '#2d3133'
  inverse-on-surface: '#eff1f3'
  outline: '#74777d'
  outline-variant: '#c4c6cd'
  surface-tint: '#4f6073'
  primary: '#041627'
  on-primary: '#ffffff'
  primary-container: '#1a2b3c'
  on-primary-container: '#8192a7'
  inverse-primary: '#b7c8de'
  secondary: '#505f76'
  on-secondary: '#ffffff'
  secondary-container: '#d0e1fb'
  on-secondary-container: '#54647a'
  tertiary: '#001a0f'
  on-tertiary: '#ffffff'
  tertiary-container: '#00311f'
  on-tertiary-container: '#00a572'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d2e4fb'
  primary-fixed-dim: '#b7c8de'
  on-primary-fixed: '#0b1d2d'
  on-primary-fixed-variant: '#38485a'
  secondary-fixed: '#d3e4fe'
  secondary-fixed-dim: '#b7c8e1'
  on-secondary-fixed: '#0b1c30'
  on-secondary-fixed-variant: '#38485d'
  tertiary-fixed: '#6ffbbe'
  tertiary-fixed-dim: '#4edea3'
  on-tertiary-fixed: '#002113'
  on-tertiary-fixed-variant: '#005236'
  background: '#f7f9fb'
  on-background: '#191c1e'
  surface-variant: '#e0e3e5'
  status-pending: '#F59E0B'
  status-shipped: '#3B82F6'
  status-error: '#EF4444'
  border-subtle: '#E2E8F0'
  surface-elevated: '#FFFFFF'
typography:
  display-sm:
    fontFamily: Hanken Grotesk
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
  headline-md:
    fontFamily: Hanken Grotesk
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  headline-sm:
    fontFamily: Hanken Grotesk
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
  body-md:
    fontFamily: Hanken Grotesk
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Hanken Grotesk
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 18px
  data-mono:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: -0.02em
  label-caps:
    fontFamily: Hanken Grotesk
    fontSize: 11px
    fontWeight: '700'
    lineHeight: 16px
    letterSpacing: 0.05em
  headline-sm-mobile:
    fontFamily: Hanken Grotesk
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 4px
  container-margin: 16px
  gutter: 12px
  stack-sm: 8px
  stack-md: 16px
  stack-lg: 24px
---

## Brand & Style

The brand personality is **Technical, Authoritative, and Efficient**. Designed for B2B stakeholders who manage complex supply chains, the design system prioritizes data density and rapid information retrieval over decorative flair. It targets procurement officers, warehouse managers, and vendors who require a "tool-like" experience rather than a "content-like" one.

The chosen design style is **Corporate / Modern** with a strong emphasis on **Minimalism**. By using generous whitespace within high-density structures, the interface remains legible and calm even when displaying large datasets (SKUs, inventory counts, and financial figures). The aesthetic is defined by crisp lines, a disciplined color palette, and a focus on functional clarity.

## Colors

The palette is anchored by **Deep Navy (#1A2B3C)**, used for primary navigation and high-level headers to convey trust and stability. **Slate Gray (#64748B)** serves as the secondary color, ideal for metadata, secondary actions, and iconography that should not compete with primary content. **Success Green (#10B981)** is reserved for growth indicators, positive stock levels, and "Order Delivered" states.

The background utilizes a clean **Neutral Slate (#F8FAFC)** to reduce eye strain during prolonged sessions. Status-specific semantic colors (Amber for pending, Blue for shipped, Red for errors) are used sparingly to highlight critical data points in a high-density environment.

## Typography

This design system utilizes **Hanken Grotesk** for its exceptional legibility and modern, sharp terminals which suit an enterprise environment. It is used for all UI copy and headings to maintain a cohesive, professional appearance.

A secondary font, **JetBrains Mono**, is introduced specifically for **Technical Data Roles**. Use this for SKU IDs, Inventory counts, Order Numbers, and API-related strings. The monospaced nature ensures that numeric values align vertically in lists and tables, allowing users to scan and compare quantities with zero ambiguity. Label styles use all-caps with increased tracking for clear categorization in compact layouts.

## Layout & Spacing

The layout follows a **Fluid Grid** model optimized for high-density mobile viewing. We employ a 4px baseline grid to ensure all components align precisely. 

- **Margins:** A consistent 16px horizontal margin is applied to the main viewport.
- **Density:** To accommodate complex B2B data, we use "tight" vertical spacing (stack-sm) for related data groups (e.g., a product name and its SKU) and "standard" spacing (stack-md) between distinct sections.
- **Mobile Reflow:** For complex tables, the design system utilizes "Pinned Column" behaviors or "Data Cards" where table rows are transformed into expandable cards to maintain readability on small screens.

## Elevation & Depth

This design system uses **Tonal Layers** and **Low-contrast Outlines** rather than heavy shadows to maintain a clean, flat aesthetic. 

- **Level 0 (Background):** Neutral Slate (#F8FAFC).
- **Level 1 (Cards/Surface):** Pure White (#FFFFFF) with a 1px Slate (#E2E8F0) border. No shadow is used for static elements.
- **Level 2 (Active/Interactive):** Subtle ambient shadow (4px blur, 10% opacity, Navy tint) used only for floating action buttons or active modals to indicate they are "above" the data plane.
- **Separators:** Use 1px borders to define regions. Avoid using color blocks for separation to keep the UI light and fast.

## Shapes

The shape language is **Soft (0.25rem)**. This subtle rounding provides a modern touch without feeling overly "consumer" or "playful." 

- **Standard Components:** Buttons, Input fields, and Cards use the base 4px (0.25rem) radius.
- **Large Components:** Bottom sheets and prominent dashboard widgets use 8px (0.5rem) to distinguish major layout containers.
- **Data Indicators:** Status badges and chips use a "Pill" shape (fully rounded) to contrast against the sharp, rectangular nature of the data grids.

## Components

### Buttons & Actions
- **Primary:** Solid Deep Navy with White text. Bold, 14px type.
- **Secondary:** Ghost style with Slate Gray border and text.
- **Success Action:** Solid Success Green for "Confirm Order" or "Receive Stock."

### Data Cards (Mobile Table Alternative)
Cards are the primary vehicle for SKUs and Inventory. Each card should feature a header with the SKU in `data-mono`, a clear title, and a bottom row for status chips. Use horizontal "Key-Value" pairs within cards for attributes like "Location" or "Lead Time."

### Inputs & Forms
Inputs use a white background with a 1px Slate border. On focus, the border transitions to Deep Navy. Labels are always visible (never placeholder-only) using the `label-caps` style for maximum clarity.

### AI Procurement Agent (CUI)
The AI chat interface should be distinct from the rest of the UI. Use a slightly tinted background (e.g., very light Navy) for AI-generated messages and a distinct "Bot" icon. The typography remains Hanken Grotesk but employs a slightly wider line height for conversational flow.

### Status Chips
Small, high-contrast badges. The background should be a 10% opacity version of the status color (e.g., 10% Success Green) with a 100% opacity text for high legibility without visual clutter.
