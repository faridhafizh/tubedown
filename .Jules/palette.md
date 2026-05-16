## 2026-05-08 - Disable Native Browser Input Features on Terminal Emulators\n**Learning:** Terminal emulators that use native HTML input fields (like `<input type="text">`) suffer from poor UX if native browser features like autocomplete dropdowns and red squiggly spellcheck lines are left enabled, as they break the terminal illusion.\n**Action:** Always disable these features using `autocomplete="off"` (`autoComplete` in React), `spellcheck="false"` (`spellCheck` in React), `autocorrect="off"` (`autoCorrect` in React), and `autocapitalize="off"` (`autoCapitalize` in React) on web-based terminal inputs.

## 2024-05-20 - Mobile Trap in Keyboard-only Modals
**Learning:** Help panels or modal dialogs that specify "Press ESC to close" without providing an explicit close button or click-to-dismiss functionality trap mobile touch-device users, as they lack an ESC key.
**Action:** Always ensure modals have alternative dismissal methods (like clicking the modal, a close button, or clicking outside) and update the helper text to indicate these alternatives to the user.

## 2026-05-11 - Dynamic Elements for ARIA Context
**Learning:** When creating repeating dynamic elements (like progress bars for downloads), using generic `aria-label` or failing to associate context makes the experience confusing for screen readers. By dynamically generating IDs (e.g., `id=\"task-title-${task.id}\"`) and referencing them via `aria-labelledby`, we ensure each progress bar is correctly associated with its specific dynamic task name, providing clear context.
**Action:** When mapping over dynamic data to create accessible components like progress bars or form groups, always dynamically generate and link IDs and `aria-labelledby`/`for` attributes based on the unique item ID. Also ensure custom dialog components fully support accessibility patterns, including `aria-modal=\"true\"` and explicit exit triggers like `Escape`.

## 2026-05-12 - Preserving Focus Visibility on Custom Inputs
**Learning:** When styling custom input areas (like terminal prompts) where the default browser outline is removed (`outline: none`), keyboard users lose track of focus. Using `:focus-within` on the container restores a visible focus indicator without breaking the custom styling. Similarly, focusable non-input elements (like dialogs) need explicit `:focus-visible` styles to guide keyboard navigation.
**Action:** Whenever `outline: none` is used, implement a custom focus indicator using `:focus-visible` for individual elements or `:focus-within` for composite input components.

## 2026-05-13 - Accessible Scrollable Regions & Placeholder Contrast
**Learning:** Custom scrollable regions (like terminal output bodies defined with `overflow-y: auto`) are inaccessible to keyboard-only users unless they receive focus. Additionally, ultra-dark colors used for hacker themes (e.g., `#006600` on `#1a1a1a`) often fail WCAG contrast requirements for placeholder text, making inputs appear broken or empty to users with low vision.
**Action:** Always add `tabindex="0"`, a descriptive `aria-label`, and a clear `:focus-visible` outline to custom scrollable containers. Adjust placeholder colors using semi-transparent high-contrast colors (e.g., `rgba(0, 255, 65, 0.5)`) to maintain aesthetics while meeting contrast standards.

## 2024-05-16 - Semantic Forms for Mobile Keyboards & Global Focus Management
**Learning:** Terminal-style custom inputs that rely solely on `keydown.enter` fail to trigger the "Go" / "Enter" action button correctly on mobile software keyboards. They must be wrapped in a semantic `<form>` tag with an `onSubmit` handler to work correctly across devices. Also, aggressive global "click anywhere to focus" handlers ruin text-selection UX, making it impossible for users to copy terminal logs without bringing up their keyboard.
**Action:** Always wrap interactive text inputs in `<form>` elements to enable native submit events (`@submit.prevent` or `onSubmit`). Furthermore, check if text is selected (`window.getSelection()?.toString().length > 0`) before forcibly giving focus to an input field in global event listeners.
