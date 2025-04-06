# augmented-awareness
Augmented Awareness (short name: *Aww* [^1]) will eventually contain a toolset for offline-first, and later local-first, quantified self projects.

It aims to support several data sources, analyses and processes ([see here for a list of ideas](https://rlupi.com/how-augmented-awareness-evolved-over-time)), and currently it can:

- [x] Read Obsidian vault (Markdown files) and collect tasks, schedule (events), tags, raw page content (`aww.observe.obsidian`);
- [x] Read ActivityWatch data: afk status, current window, web browsing history;
- [x] Make Obsidian tasks, events (`aww.orient.schedule`), activitywatch (`aww.observe.activitywatch`) data available as a arrow table, which can be converted to pandas dataframes or exported to files (just create a Jupyter notebook and explore the API);
- [x] Answer questions or provide tips about the schedule (`aww.py obsidian tips` command) via local LLM;
- [ ] Draft ideas about the overall architecture (`doc`). WIP.

It also contains an implementation for a cute IoT pomodoro timer (`iot/pomodoro`), which will be later integrated with the data collection system.

[^1]: Originally *AgAu*, renamed to avoid conflicts.
