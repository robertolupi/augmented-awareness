package obsidian

import (
	"fmt"
	"journal/internal/datetime"
)

func DailyRetroPageName(date datetime.Date) string {
	// r2025-01-01 for January 1, 2025
	return "r" + date.String()
}

func WeeklyRetroPageName(date datetime.Date) string {
	// r2025-W01 for the first week of 2025
	year, week := date.Time().ISOWeek()
	return fmt.Sprintf("r%d-W%02d", year, week)
}

func MonthlyRetroPageName(date datetime.Date) string {
	// r2025-01 for January 2025
	return "r" + date.Time().Format("2006-01")
}

func YearlyRetroPageName(date datetime.Date) string {
	// r2025 for the year 2025
	return "r" + date.Time().Format("2006")
}
