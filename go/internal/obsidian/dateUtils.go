package obsidian

import "time"

func DateFromPage(page string) (time.Time, error) {
	parsedTime, err := time.Parse("2006-01-02", page)
	if err != nil {
		return time.Time{}, err
	}
	return parsedTime, nil
}

func DateToPage(date time.Time) string {
	return date.Format("2006-01-02")
}
