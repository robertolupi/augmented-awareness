package obsidian

import "time"

// Time represents a time in the HH:MM format
type Time string

func TimeFromString(timeStr string) (Time, error) {
	parsedTime, err := time.Parse("15:04", timeStr)
	if err != nil {
		return "", err
	}
	return Time(parsedTime.Format("15:04")), nil
}

func (t Time) IsEmpty() bool {
	return t == ""
}

func (t Time) Time() time.Time {
	parsedTime, err := time.Parse("15:04", string(t))
	if err != nil {
		return time.Time{}
	}
	return parsedTime
}

func (t Time) AddMinutes(delta int) Time {
	if t.IsEmpty() {
		return ""
	}
	tt := t.Time()
	tt = tt.Add(time.Duration(delta) * time.Minute)
	return Time(tt.Format("15:04"))
}

// Date represents a date in the YYYY-MM-DD format
type Date string

func DateFromString(dateStr string) (Date, error) {
	parsedDate, err := time.Parse("2006-01-02", dateStr)
	if err != nil {
		return "", err
	}
	return Date(parsedDate.Format("2006-01-02")), nil
}

func (d Date) IsEmpty() bool {
	return d == ""
}

func (d Date) Time() time.Time {
	parsedDate, err := time.Parse("2006-01-02", string(d))
	if err != nil {
		return time.Time{}
	}
	return parsedDate
}

func (d Date) AddDays(delta int) Date {
	if d.IsEmpty() {
		return ""
	}
	t := d.Time()
	t = t.AddDate(0, 0, delta)
	return Date(t.Format("2006-01-02"))
}

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
