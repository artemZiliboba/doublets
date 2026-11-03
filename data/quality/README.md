# Word quality inputs

- `excluded_words.txt`: manually reviewed exclusions, one token per line.
- Optional `frequency_ru.txt`: UTF-8 text with `word number` per line (space, tab or semicolon separator).
- Frequency values can be counts, normalized frequencies, or ranks converted to a higher-is-more-common score; they must be non-negative, finite numeric values.
- Only include a frequency file whose license allows your intended use. Record its origin and version.
- The core dictionary is a frequency-filtered **candidate** list, not linguistically verified. Review it before using it as the only game lexicon.
- When no frequency file is provided, core is intentionally empty rather than pretending the extended dictionary is curated.
