A loose collection of experiments to build *quantified-self* tools for living a more wholesome life.

# Journal management tool

This program manages a journal of events in Markdown pages, stored in an Obsidian Vault.

Pages are created in Obsidian, they are named after dates (YYYY-MM-DD) and contains a list of events in the
specified section.

Events have the following format:

```markdown

# Events and Journal

Other text can be present in the section, and it will be ignored.

06:05 an event without an end
07:15 - 08:00 an event with an end
text can be interspersed, and it will be ignored.
09:00 - 09:30 events can have hashtags like #tag
```

