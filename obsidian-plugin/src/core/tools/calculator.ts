/**
 * Safe arithmetic and date calculator for chat assistance.
 * Replaces python_eval_tool with a deterministic, safe parser (no eval / no Function).
 */
import moment from "moment";

export function evaluateCalculation(expression: string): string {
	const trimmed = expression.trim();
	if (!trimmed) {
		return "Error: Empty expression.";
	}

	try {
		// 1. Check for date difference: "YYYY-MM-DD" - "YYYY-MM-DD" or daysBetween(...)
		const diffMatch = trimmed.match(
			/(?:daysBetween\s*\(\s*["']?(\d{4}-\d{2}-\d{2})["']?\s*,\s*["']?(\d{4}-\d{2}-\d{2})["']?\s*\)|["']?(\d{4}-\d{2}-\d{2})["']?\s*-\s*["']?(\d{4}-\d{2}-\d{2})["']?)/i
		);
		if (diffMatch) {
			const d1Str = diffMatch[1] || diffMatch[3];
			const d2Str = diffMatch[2] || diffMatch[4];
			const m1 = moment(d1Str, "YYYY-MM-DD", true);
			const m2 = moment(d2Str, "YYYY-MM-DD", true);
			if (!m1.isValid() || !m2.isValid()) {
				return `Error: Invalid date format in expression (expected YYYY-MM-DD).`;
			}
			const diff = Math.abs(m1.diff(m2, "days"));
			return `${diff} days (between ${d1Str} and ${d2Str})`;
		}

		// 2. Check for date offset: "YYYY-MM-DD" + N [days] or addDays("YYYY-MM-DD", N)
		const addMatch = trimmed.match(
			/(?:addDays\s*\(\s*["']?(\d{4}-\d{2}-\d{2})["']?\s*,\s*(-?\d+)\s*\)|["']?(\d{4}-\d{2}-\d{2})["']?\s*\+\s*(\d+)(?:\s*days?)?)/i
		);
		if (addMatch) {
			const dateStr = addMatch[1] || addMatch[3];
			const days = parseInt(addMatch[2] || addMatch[4], 10);
			const m = moment(dateStr, "YYYY-MM-DD", true);
			if (!m.isValid()) return `Error: Invalid date format '${dateStr}'.`;
			const res = m.clone().add(days, "days").format("YYYY-MM-DD");
			return res;
		}

		// 3. Check for date subtraction: "YYYY-MM-DD" - N [days] or subDays("YYYY-MM-DD", N)
		const subMatch = trimmed.match(
			/(?:subDays\s*\(\s*["']?(\d{4}-\d{2}-\d{2})["']?\s*,\s*(\d+)\s*\)|["']?(\d{4}-\d{2}-\d{2})["']?\s*-\s*(\d+)(?:\s*days?)?)/i
		);
		if (subMatch) {
			const dateStr = subMatch[1] || subMatch[3];
			const days = parseInt(subMatch[2] || subMatch[4], 10);
			const m = moment(dateStr, "YYYY-MM-DD", true);
			if (!m.isValid()) return `Error: Invalid date format '${dateStr}'.`;
			const res = m.clone().subtract(days, "days").format("YYYY-MM-DD");
			return res;
		}

		// 4. Check for dayOfWeek("YYYY-MM-DD")
		const dowMatch = trimmed.match(/dayOfWeek\s*\(\s*["']?(\d{4}-\d{2}-\d{2})["']?\s*\)/i);
		if (dowMatch) {
			const m = moment(dowMatch[1], "YYYY-MM-DD", true);
			if (!m.isValid()) return `Error: Invalid date format '${dowMatch[1]}'.`;
			return m.format("dddd");
		}

		// 5. Check for daysInMonth(year, month)
		const dimMatch = trimmed.match(/daysInMonth\s*\(\s*(\d{4})\s*,\s*(\d{1,2})\s*\)/i);
		if (dimMatch) {
			const y = parseInt(dimMatch[1], 10);
			const mo = parseInt(dimMatch[2], 10);
			const m = moment(`${y}-${String(mo).padStart(2, "0")}-01`, "YYYY-MM-DD", true);
			if (!m.isValid()) return `Error: Invalid year/month ${y}-${mo}.`;
			return String(m.daysInMonth());
		}

		// 6. Safe arithmetic parser (tokens: numbers, +, -, *, /, %, ^, parentheses, sqrt, abs, round, floor, ceil)
		return String(parseArithmetic(trimmed));
	} catch (err: any) {
		return `Error: ${err.message || String(err)}`;
	}
}

/**
 * Recursive descent arithmetic parser for simple mathematical expressions.
 */
function parseArithmetic(input: string): number {
	let pos = 0;
	const s = input.replace(/\s+/g, "");

	function peek(): string {
		return s[pos] || "";
	}

	function consume(char?: string): string {
		if (char && s[pos] !== char) {
			throw new Error(`Expected '${char}' at character ${pos}`);
		}
		return s[pos++];
	}

	function parseExpression(): number {
		let val = parseTerm();
		while (peek() === "+" || peek() === "-") {
			const op = consume();
			const rhs = parseTerm();
			if (op === "+") val += rhs;
			else val -= rhs;
		}
		return val;
	}

	function parseTerm(): number {
		let val = parseFactor();
		while (peek() === "*" || peek() === "/" || peek() === "%") {
			const op = consume();
			const rhs = parseFactor();
			if (op === "*") val *= rhs;
			else if (op === "/") {
				if (rhs === 0) throw new Error("Division by zero");
				val /= rhs;
			} else {
				if (rhs === 0) throw new Error("Modulo by zero");
				val %= rhs;
			}
		}
		return val;
	}

	function parseFactor(): number {
		let val = parsePrimary();
		if (peek() === "^") {
			consume("^");
			const exp = parseFactor();
			val = Math.pow(val, exp);
		}
		return val;
	}

	function parsePrimary(): number {
		if (peek() === "-") {
			consume("-");
			return -parsePrimary();
		}
		if (peek() === "+") {
			consume("+");
			return parsePrimary();
		}
		if (peek() === "(") {
			consume("(");
			const val = parseExpression();
			consume(")");
			return val;
		}

		// Function calls: sqrt, abs, round, floor, ceil
		const funcMatch = s.slice(pos).match(/^(sqrt|abs|round|floor|ceil)\(/i);
		if (funcMatch) {
			const fn = funcMatch[1].toLowerCase();
			pos += fn.length + 1; // skip "func("
			const arg = parseExpression();
			consume(")");
			switch (fn) {
				case "sqrt":
					if (arg < 0) throw new Error("Square root of negative number");
					return Math.sqrt(arg);
				case "abs":
					return Math.abs(arg);
				case "round":
					return Math.round(arg);
				case "floor":
					return Math.floor(arg);
				case "ceil":
					return Math.ceil(arg);
			}
		}

		// Number literal
		const numMatch = s.slice(pos).match(/^\d+(?:\.\d+)?/);
		if (numMatch) {
			pos += numMatch[0].length;
			return parseFloat(numMatch[0]);
		}

		throw new Error(`Unexpected character '${peek()}' at index ${pos}`);
	}

	const result = parseExpression();
	if (pos < s.length) {
		throw new Error(`Unexpected token at index ${pos}: '${s.slice(pos)}'`);
	}
	return result;
}
