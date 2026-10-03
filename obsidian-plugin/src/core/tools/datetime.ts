/**
 * Datetime tool for current timestamp and relevant Obsidian periodic note links.
 */
import moment from "moment";

export function getDatetimeContext(now: moment.Moment = moment()): string {
	const dayStr = now.format("YYYY-MM-DD");
	const monthStr = now.format("YYYY-MM");
	const yearStr = now.format("YYYY");
	const isoYear = now.isoWeekYear();
	const isoWeek = String(now.isoWeek()).padStart(2, "0");

	const lines = [
		`Now is ${now.format("dddd, YYYY-MM-DD HH:mm:ss")}`,
		"The pages relevant to today are:",
		` - Year: [[Y${yearStr}]]`,
		` - Month: [[${monthStr}]]`,
		` - Day: [[${dayStr}]]`,
		` - Week: [[${isoYear}-W${isoWeek}]]`,
	];

	return lines.join("\n");
}
