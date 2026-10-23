import { ItemView, TFile, WorkspaceLeaf, moment } from "obsidian";
import type AwwRetroPlugin from "../main";
import {
	BusyReport,
	TimeHistogram,
	buildBusyReport,
	formatDurationMin,
} from "../core/busy";
import { parseJournalOrRetroPath } from "../core/paths";

export const BUSY_VIEW_TYPE = "aww-busy-view";

const SVG_NS = "http://www.w3.org/2000/svg";
const SVG_WIDTH = 240;
const SVG_HEIGHT = 48;
const BAR_AREA_HEIGHT = 36;
const TICK_HOURS = [0, 6, 12, 18];

const WINDOW_OPTIONS: { days: number; label: string }[] = [
	{ days: 1, label: "Last day" },
	{ days: 7, label: "Last 7 days" },
	{ days: 30, label: "Last 30 days" },
];

export class AwwBusyView extends ItemView {
	private plugin: AwwRetroPlugin;
	private days = 7;
	private hierarchical = true;
	private renderTimer: number | null = null;

	private bodyEl!: HTMLElement;
	private rangeEl!: HTMLElement;

	constructor(leaf: WorkspaceLeaf, plugin: AwwRetroPlugin) {
		super(leaf);
		this.plugin = plugin;
	}

	getViewType(): string {
		return BUSY_VIEW_TYPE;
	}

	getDisplayText(): string {
		return "Time tracking";
	}

	getIcon(): string {
		return "bar-chart-3";
	}

	async onOpen(): Promise<void> {
		const container = this.contentEl;
		container.empty();
		container.addClass("aww-busy-view-container");

		this.buildHeader(container);
		this.bodyEl = container.createDiv({ cls: "aww-busy-body" });

		this.registerEvent(
			this.app.workspace.on("file-open", () => {
				void this.render();
			})
		);
		this.registerEvent(
			this.app.vault.on("modify", (file) => {
				if (
					file instanceof TFile &&
					file.path.startsWith(
						this.plugin.settings.journalDir + "/"
					)
				) {
					this.scheduleRender();
				}
			})
		);

		await this.render();
	}

	async onClose(): Promise<void> {
		if (this.renderTimer !== null) {
			window.clearTimeout(this.renderTimer);
			this.renderTimer = null;
		}
	}

	private scheduleRender(): void {
		if (this.renderTimer !== null) {
			window.clearTimeout(this.renderTimer);
		}
		this.renderTimer = window.setTimeout(() => {
			this.renderTimer = null;
			void this.render();
		}, 500);
	}

	private buildHeader(container: HTMLElement): void {
		const header = container.createDiv({ cls: "aww-busy-header" });

		const controls = header.createDiv({ cls: "aww-busy-controls" });

		const windowSelect = controls.createEl("select", {
			cls: "dropdown aww-busy-window-select",
		});
		for (const opt of WINDOW_OPTIONS) {
			windowSelect.add(new Option(opt.label, String(opt.days)));
		}
		windowSelect.value = String(this.days);
		windowSelect.addEventListener("change", () => {
			this.days = Number(windowSelect.value);
			void this.render();
		});

		const hierarchyLabel = controls.createEl("label", {
			cls: "aww-busy-hierarchy-toggle",
		});
		const hierarchyToggle = hierarchyLabel.createEl("input", {
			attr: { type: "checkbox" },
		});
		hierarchyToggle.checked = this.hierarchical;
		hierarchyToggle.addEventListener("change", () => {
			this.hierarchical = hierarchyToggle.checked;
			void this.render();
		});
		hierarchyLabel.appendText(" Hierarchical tags");

		this.rangeEl = header.createDiv({ cls: "aww-busy-range" });
	}

	private resolveEndDate(): moment.Moment {
		const activeFile = this.app.workspace.getActiveFile();
		if (activeFile) {
			const parsed = parseJournalOrRetroPath(
				activeFile.path,
				this.plugin.settings.journalDir,
				this.plugin.settings.retroDir
			);
			if (parsed) {
				return parsed.date;
			}
		}
		return moment();
	}

	private async render(): Promise<void> {
		const endDate = this.resolveEndDate();
		const startDate = endDate.clone().subtract(this.days - 1, "days");
		this.rangeEl.setText(
			`${startDate.format("YYYY-MM-DD")} — ${endDate.format("YYYY-MM-DD")}`
		);

		const report = await buildBusyReport(this.app, {
			endDate,
			days: this.days,
			journalDir: this.plugin.settings.journalDir,
			journalSection: this.plugin.settings.journalSection,
		});
		if (this.hierarchical) {
			report.expandTags();
		}

		this.bodyEl.empty();
		if (
			report.total.durationMin === 0 &&
			report.noTags.durationMin === 0
		) {
			this.bodyEl.createDiv({
				cls: "aww-busy-empty",
				text: "No time-tracked events in this range.",
			});
			return;
		}

		this.renderRow("Total", report.total, 100, "aww-busy-row-total");
		this.renderRow(
			"No tags",
			report.noTags,
			report.total.durationMin === 0
				? 0
				: (report.noTags.durationMin / report.total.durationMin) * 100,
			"aww-busy-row-notags"
		);
		for (const entry of report.sortedTags()) {
			this.renderRow(`#${entry.tag}`, entry.histogram, entry.percent);
		}
	}

	private renderRow(
		label: string,
		histogram: TimeHistogram,
		percent: number,
		extraCls?: string
	): void {
		const row = this.bodyEl.createDiv({
			cls: extraCls ? `aww-busy-row ${extraCls}` : "aww-busy-row",
		});
		const rowHeader = row.createDiv({ cls: "aww-busy-row-header" });
		rowHeader.createSpan({ cls: "aww-busy-tag", text: label });
		rowHeader.createSpan({
			cls: "aww-busy-duration",
			text: `${formatDurationMin(histogram.durationMin)} · ${percent.toFixed(1)}%`,
		});
		row.appendChild(this.buildHistogramSvg(histogram));
	}

	private buildHistogramSvg(histogram: TimeHistogram): SVGSVGElement {
		const svg = document.createElementNS(SVG_NS, "svg");
		svg.setAttribute("viewBox", `0 0 ${SVG_WIDTH} ${SVG_HEIGHT}`);
		svg.setAttribute("preserveAspectRatio", "none");
		svg.addClass("aww-busy-histogram");

		const buckets = histogram.buckets;
		const max = histogram.maxBucket();
		const barWidth = SVG_WIDTH / buckets.length;

		for (let i = 0; i < buckets.length; i++) {
			if (buckets[i] === 0) {
				continue;
			}
			const barHeight = Math.max(
				1,
				(buckets[i] / max) * BAR_AREA_HEIGHT
			);
			const rect = document.createElementNS(SVG_NS, "rect");
			rect.setAttribute("x", String(i * barWidth));
			rect.setAttribute("y", String(BAR_AREA_HEIGHT - barHeight));
			rect.setAttribute("width", String(Math.max(barWidth - 0.5, 0.5)));
			rect.setAttribute("height", String(barHeight));
			rect.addClass("aww-busy-bar");
			svg.appendChild(rect);
		}

		const axis = document.createElementNS(SVG_NS, "line");
		axis.setAttribute("x1", "0");
		axis.setAttribute("y1", String(BAR_AREA_HEIGHT + 0.5));
		axis.setAttribute("x2", String(SVG_WIDTH));
		axis.setAttribute("y2", String(BAR_AREA_HEIGHT + 0.5));
		axis.addClass("aww-busy-axis");
		svg.appendChild(axis);

		for (const hour of TICK_HOURS) {
			const label = document.createElementNS(SVG_NS, "text");
			label.setAttribute("x", String((hour / 24) * SVG_WIDTH));
			label.setAttribute("y", String(SVG_HEIGHT - 2));
			label.addClass("aww-busy-tick");
			label.textContent = String(hour).padStart(2, "0");
			svg.appendChild(label);
		}

		return svg;
	}
}
