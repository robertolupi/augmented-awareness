package datetime

import "time"

// Time represents a time in the HH:MM format
type Time string

const EmptyTime Time = ""

func TimeFromString(timeStr string) (Time, error) {
	if timeStr == "" {
		return EmptyTime, nil
	}

	parsedTime, err := time.Parse("15:04", timeStr)
	if err != nil {
		return "", err
	}
	return Time(parsedTime.Format("15:04")), nil
}

func TimeToString(date time.Time) string {
	return date.Format("2006-01-02")
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

func TimeNow() Time {
	return Time(time.Now().Format("15:04"))
}

func (t Time) String() string {
	return string(t)
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

const EmptyDate Date = ""

func DateRange(start string, end string) ([]Date, error) {
	startDate, err := time.Parse("2006-01-02", start)
	if err != nil {
		return nil, err
	}
	endDate, err := time.Parse("2006-01-02", end)
	if err != nil {
		return nil, err
	}

	var dates []Date
	for d := startDate; d.Before(endDate) || d.Equal(endDate); d = d.AddDate(0, 0, 1) {
		dates = append(dates, Date(d.Format("2006-01-02")))
	}
	return dates, nil
}

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

func (d Date) String() string {
	return string(d)
}

func (d Date) AddDays(delta int) Date {
	if d.IsEmpty() {
		return ""
	}
	t := d.Time()
	t = t.AddDate(0, 0, delta)
	return Date(t.Format("2006-01-02"))
}

func fromToday(months int, days int) Date {
	return Date(time.Now().AddDate(0, months, days).Format("2006-01-02"))
}

func Today() Date { return fromToday(0, 0) }

func Yesterday() Date {
	return fromToday(0, -1)
}

func OneMonthAgo() Date {
	return fromToday(-1, 0)
}

func SixDaysAgo() Date {
	return fromToday(0, -6)
}
