# Design System: VACA (Vibetraffic Autonomous Content Agent)
**Project ID:** vaca-karpix-2026

## 1. Visual Theme & Atmosphere
The design follows a premium **iOS-inspired aesthetic** optimized for Telegram Mini Apps. It is **Clean, Modern, and Functional**, prioritizing readability and high-quality micro-interactions. The atmosphere is professional yet accessible, with a focus on high-density information management in a streamlined "Inbox" format.

## 2. Color Palette & Roles
* **iOS System Blue (#007aff):** Primary accent color for major actions, active navigation tabs, and focus highlights.
* **Apple Success Green (#34c759):** Functional color for positive status dots, success notifications, and accepted content states.
* **Apple Danger Red (#ff3b30):** Functional color for destructive actions (delete), error notifications, and rejected content states.
* **Glassmorphism White/Dark:** Semi-transparent background for fixed headers and footers with a strong blur effect.
* **Muted Silver-Grey (#8e8e93):** Used for hint text, secondary metadata, and non-active navigation icons.

## 3. Typography Rules
* **Font Family:** `-apple-system`, SF Pro Text, SF Pro Display. Optimized for high legibility on mobile devices.
* **Hierarchy:**
    * **Main Headers:** 24px, Bold (700), letter-spacing: -0.5px. Used for page titles.
    * **Section Headers:** 20px, Bold (700), letter-spacing: -0.5px.
    * **Body Text:** 15px, Regular (400), line-height: 1.4.
    * **Metadata/Labels:** 13px, Regular (400).
    * **Navigation Labels:** 10px, Medium (500).

## 4. Component Stylings
* **Buttons:**
    * **Shape:** Rounded corners (10px).
    * **States:** Full background color for primary actions; subtle background with accent text for secondary actions.
    * **Interaction:** Opacity shift (0.7) on active press.
* **Cards & Containers:**
    * **Shape:** Generously rounded corners (12px).
    * **Background:** Subtle elevation using secondary background tokens.
    * **Density:** Comfortable padding (20px) to prevent visual clutter.
* **Notifications (Toast):**
    * **Shape:** Rounded (14px).
    * **Motion:** Slide-up from bottom with a slight bounce (cubic-bezier).
    * **Depth:** Diffused shadow (0 8px 24px) for clear separation from content.

## 5. Layout Principles
* **Native Feel:** Uses fixed headers and bottom navigation to mimic native iOS application structure.
* **Glassmorphism:** Employs `backdrop-filter: blur(20px)` on persistent UI elements.
* **Safe Areas:** Respects `env(safe-area-inset-*)` for modern notch-display compatibility.
* **Responsive Grid:** Centered single-column layout (max-width 600px) designed for one-handed mobile usage.
