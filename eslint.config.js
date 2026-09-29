import eslintParserHTML from "@html-eslint/parser";
import betterTailwind from "eslint-plugin-better-tailwindcss";
import { defineConfig } from "eslint/config";

// Blank out Jinja tags with same-length whitespace so the HTML parser sees plain
// class lists and --fix offsets still match the original file. A macro call's
// class="…" argument survives as `<i class="…"/>`, so icon classes get linted too.
const blank = (s) => s.replace(/[^\n]/g, " ");
const maskTag = (tag) => {
  const arg = /\bclass=("[^"]*"|'[^']*')/.exec(tag);
  if (!tag.startsWith("{{") || !arg) return blank(tag);
  const end = arg.index + arg[0].length;
  return `<i${blank(tag.slice(2, arg.index))}${arg[0]}${blank(tag.slice(end, -2))}/>`;
};
const jinja = {
  preprocess: (text) => [text.replace(/\{\{[\s\S]*?\}\}|\{%[\s\S]*?%\}|\{#[\s\S]*?#\}/g, maskTag)],
  postprocess: (messages) => messages.flat(),
  supportsAutofix: true,
};

export default defineConfig({
  files: ["app/templates/**/*.html"],
  plugins: { "better-tailwindcss": betterTailwind, jinja: { processors: { jinja } } },
  processor: "jinja/jinja",
  languageOptions: { parser: eslintParserHTML },
  settings: { "better-tailwindcss": { entryPoint: "app/static/css/theme.css" } },
  rules: {
    "better-tailwindcss/no-conflicting-classes": "error",
    "better-tailwindcss/no-duplicate-classes": "error",
    "better-tailwindcss/no-deprecated-classes": "error",
    // Non-Tailwind classes: JS hooks and the plain-CSS components in theme.css.
    "better-tailwindcss/no-unknown-classes": ["error", {
      ignore: [
        "action-container", "article-thumb", "btn-copy", "counter", "date-type-btn",
        "dropdown", "edit-btn", "faq-item", "footer-social", "form-group", "gallery-grid",
        "gallery-item", "lightbox-.+", "modal-admin", "modal-admin-panel", "modal-lightbox",
        "report-card", "review-section", "site-header", "step", "step-container",
      ],
    }],
    "better-tailwindcss/enforce-canonical-classes": "error",
  },
});
