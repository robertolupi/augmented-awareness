/**
 * Time-tracking statistics, ported from the Go implementation
 * (internal/stats/histogram.go and internal/stats/busy.go).
 *
 * A TimeHistogram splits the 24h day into fixed-size buckets and counts,
 * per bucket, how many bucket-sized slices of tracked time fall into it.
 * The exact total duration is tracked separately. All times are minutes
 * since midnight.
 */
import { App, TFile, moment, normalizePath } from "obsidian";
import { findSectionEvents } from "./events";
import { dailyJournalPath } from "./paths";

export const MINUTES_PER_DAY = 24 * 60;
export const DEFAULT_BUCKET_MINUTES = 30;

export class TimeHistogram {
	readonly bucketMinutes: number;
	buckets: number[];
	/** Exact total time added to the histogram, in minutes. */
	durationMin = 0;

	constructor(bucketMinutes: number = DEFAULT_BUCKET_MINUTES) {
		if (MINUTES_PER_DAY % bucketMinutes !== 0) {
			throw new Error(
				`24h period is not a multiple of bucket size ${bucketMinutes}m`
			);
		}
		this.bucketMinutes = bucketMinutes;
		this.buckets = new Array(MINUTES_PER_DAY / bucketMinutes).fill(0);
	}

	add(startMin: number, durationMin: number): void {
		let bucketIndex = Math.floor(startMin / this.bucketMinutes);
		for (let d = durationMin; d > 0; d -= this.bucketMinutes) {
			this.buckets[bucketIndex]++;
			bucketIndex = (bucketIndex + 1) % this.buckets.length;
		}
		this.durationMin += durationMin;
	}

	copy(): TimeHistogram {
		const clone = new TimeHistogram(this.bucketMinutes);
		clone.buckets = [...this.buckets];
		clone.durationMin = this.durationMin;
		return clone;
	}

	merge(other: TimeHistogram): void {
		if (this.bucketMinutes !== other.bucketMinutes) {
			throw new Error(
				"cannot merge histograms with different bucket sizes"
			);
		}
		for (let i = 0; i < this.buckets.length; i++) {
			this.buckets[i] += other.buckets[i];
		}
		this.durationMin += other.durationMin;
	}

	maxBucket(): number {
		let max = 1;
		for (const count of this.buckets) {
			if (count > max) {
				max = count;
			}
		}
		return max;
	}
}

export interface BusyReportTag {
	tag: string;
	histogram: TimeHistogram;
	/** Percent of the total tagged time. */
	percent: number;
}

export class BusyReport {
	/** Total time spent on events with tags. */
	readonly total: TimeHistogram;
	/** Total time spent on events without tags. */
	readonly noTags: TimeHistogram;
	readonly tags = new Map<string, TimeHistogram>();

	constructor(readonly bucketMinutes: number = DEFAULT_BUCKET_MINUTES) {
		this.total = new TimeHistogram(bucketMinutes);
		this.noTags = new TimeHistogram(bucketMinutes);
	}

	addEvent(startMin: number, durationMin: number, tags: string[]): void {
		if (tags.length === 0) {
			this.noTags.add(startMin, durationMin);
			return;
		}
		this.total.add(startMin, durationMin);
		for (const tag of tags) {
			if (tag === "") {
				continue;
			}
			let histogram = this.tags.get(tag);
			if (!histogram) {
				histogram = new TimeHistogram(this.bucketMinutes);
				this.tags.set(tag, histogram);
			}
			histogram.add(startMin, durationMin);
		}
	}

	/**
	 * Create ancestor histograms for hierarchical tags. An ancestor is kept
	 * only when shared by at least two tags (unless it is a real tag itself).
	 * Example: #father/son + #father/daughter produce #father, while a lone
	 * #mother/son does not produce #mother.
	 */
	expandTags(): void {
		const expanded = new Map<string, TimeHistogram>();
		const count = new Map<string, number>();
		for (const [tag, histogram] of this.tags) {
			expanded.set(tag, histogram);
			count.set(tag, 1);
		}
		for (const [tag, histogram] of this.tags) {
			if (tag === "") {
				continue;
			}
			const parts = tag.split("/");
			for (let i = parts.length - 1; i > 0; i--) {
				const subTag = parts.slice(0, i).join("/");
				const existing = expanded.get(subTag);
				if (!existing) {
					expanded.set(subTag, histogram.copy());
					count.set(subTag, 0);
				} else {
					existing.merge(histogram);
					count.set(subTag, (count.get(subTag) ?? 0) + 1);
				}
			}
		}
		for (const tag of expanded.keys()) {
			if ((count.get(tag) ?? 0) === 0) {
				expanded.delete(tag);
			}
		}
		this.tags.clear();
		for (const [tag, histogram] of expanded) {
			this.tags.set(tag, histogram);
		}
	}

	/** Tags sorted by duration, descending. */
	sortedTags(): BusyReportTag[] {
		const out: BusyReportTag[] = [];
		for (const [tag, histogram] of this.tags) {
			out.push({
				tag,
				histogram,
				percent:
					this.total.durationMin === 0
						? 0
						: (histogram.durationMin / this.total.durationMin) * 100,
			});
		}
		out.sort((a, b) => b.histogram.durationMin - a.histogram.durationMin);
		return out;
	}
}

/** Format a duration in minutes as e.g. "3h 30m", "45m". */
export function formatDurationMin(durationMin: number): string {
	const total = Math.round(durationMin);
	const h = Math.floor(total / 60);
	const m = total % 60;
	if (h === 0) {
		return `${m}m`;
	}
	return m === 0 ? `${h}h` : `${h}h ${m}m`;
}

export interface BusyReportOptions {
	/** Last day of the rolling window (inclusive). */
	endDate: moment.Moment;
	/** Window size in days (1, 7, 30, ...). */
	days: number;
	journalDir: string;
	journalSection: string;
	bucketMinutes?: number;
}

/**
 * Build a BusyReport over the rolling window
 * [endDate - (days - 1), endDate], reading daily journal pages from the
 * vault. Missing pages and pages without the journal section are skipped.
 * Mirrors application.BusyReport in internal/application/busy.go.
 */
export async function buildBusyReport(
	app: App,
	opts: BusyReportOptions
): Promise<BusyReport> {
	const report = new BusyReport(opts.bucketMinutes ?? DEFAULT_BUCKET_MINUTES);
	for (let i = opts.days - 1; i >= 0; i--) {
		const date = opts.endDate.clone().subtract(i, "days");
		const path = dailyJournalPath(date.format("YYYY-MM-DD"), opts.journalDir);
		const file = app.vault.getAbstractFileByPath(normalizePath(path));
		if (!(file instanceof TFile)) {
			continue;
		}
		const content = await app.vault.cachedRead(file);
		for (const event of findSectionEvents(content, opts.journalSection)) {
			report.addEvent(event.startMin, event.durationMin, event.tags);
		}
	}
	return report;
}
