package datetime

import (
	"testing"
	"time"
)

// Tests for Time type
func TestTimeFromString(t *testing.T) {
	tests := []struct {
		name     string
		timeStr  string
		expected Time
		wantErr  bool
	}{
		{"Valid time", "14:30", "14:30", false},
		{"Midnight", "00:00", "00:00", false},
		{"End of day", "23:59", "23:59", false},
		{"Invalid format", "14-30", "", true},
		{"Invalid hour", "25:00", "", true},
		{"Invalid minute", "14:60", "", true},
		{"Empty string", "", "", false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := TimeFromString(tt.timeStr)
			if (err != nil) != tt.wantErr {
				t.Errorf("TimeFromString() error = %v, wantErr %v", err, tt.wantErr)
				return
			}
			if got != tt.expected {
				t.Errorf("TimeFromString() = %v, want %v", got, tt.expected)
			}
		})
	}
}

func TestTimeIsEmpty(t *testing.T) {
	tests := []struct {
		name     string
		time     Time
		expected bool
	}{
		{"Empty time", "", true},
		{"Non-empty time", "14:30", false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := tt.time.IsEmpty(); got != tt.expected {
				t.Errorf("Time.IsEmpty() = %v, want %v", got, tt.expected)
			}
		})
	}
}

func TestTimeToTime(t *testing.T) {
	tests := []struct {
		name     string
		time     Time
		expected time.Time
		isZero   bool
	}{
		{
			name:   "Valid time",
			time:   "14:30",
			isZero: false,
		},
		{
			name:   "Empty time",
			time:   "",
			isZero: true,
		},
		{
			name:   "Invalid time",
			time:   "invalid",
			isZero: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := tt.time.Time()
			if got.IsZero() != tt.isZero {
				t.Errorf("Time.Time() IsZero = %v, want %v", got.IsZero(), tt.isZero)
			}

			if !tt.isZero {
				expectedHour, expectedMinute := got.Hour(), got.Minute()
				parsedHour, parsedMinute := 0, 0

				// Parse the time string to get expected hour and minute
				if timeObj, err := time.Parse("15:04", string(tt.time)); err == nil {
					parsedHour, parsedMinute = timeObj.Hour(), timeObj.Minute()
				}

				if expectedHour != parsedHour || expectedMinute != parsedMinute {
					t.Errorf("Time.Time() = %v:%v, want %v:%v",
						expectedHour, expectedMinute, parsedHour, parsedMinute)
				}
			}
		})
	}
}

func TestTimeAddMinutes(t *testing.T) {
	tests := []struct {
		name     string
		time     Time
		delta    int
		expected Time
	}{
		{"Add 30 minutes", "14:30", 30, "15:00"},
		{"Add 60 minutes", "14:30", 60, "15:30"},
		{"Add negative minutes", "14:30", -30, "14:00"},
		{"Add 0 minutes", "14:30", 0, "14:30"},
		{"Cross day boundary forward", "23:45", 30, "00:15"},
		{"Cross day boundary backward", "00:15", -30, "23:45"},
		{"Empty time", "", 30, ""},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := tt.time.AddMinutes(tt.delta); got != tt.expected {
				t.Errorf("Time.AddMinutes() = %v, want %v", got, tt.expected)
			}
		})
	}
}

// Tests for Date type
func TestDateFromString(t *testing.T) {
	tests := []struct {
		name     string
		dateStr  string
		expected Date
		wantErr  bool
	}{
		{"Valid date", "2023-10-15", "2023-10-15", false},
		{"First day of month", "2023-10-01", "2023-10-01", false},
		{"Last day of month", "2023-10-31", "2023-10-31", false},
		{"Leap year", "2024-02-29", "2024-02-29", false},
		{"Invalid format", "2023/10/15", "", true},
		{"Invalid month", "2023-13-15", "", true},
		{"Invalid day", "2023-10-32", "", true},
		{"Non-leap year Feb 29", "2023-02-29", "", true},
		{"Empty string", "", "", true},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := DateFromString(tt.dateStr)
			if (err != nil) != tt.wantErr {
				t.Errorf("DateFromString() error = %v, wantErr %v", err, tt.wantErr)
				return
			}
			if got != tt.expected {
				t.Errorf("DateFromString() = %v, want %v", got, tt.expected)
			}
		})
	}
}

func TestDateIsEmpty(t *testing.T) {
	tests := []struct {
		name     string
		date     Date
		expected bool
	}{
		{"Empty date", "", true},
		{"Non-empty date", "2023-10-15", false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := tt.date.IsEmpty(); got != tt.expected {
				t.Errorf("Date.IsEmpty() = %v, want %v", got, tt.expected)
			}
		})
	}
}

func TestDateToTime(t *testing.T) {
	tests := []struct {
		name     string
		date     Date
		expected time.Time
		isZero   bool
	}{
		{
			name:   "Valid date",
			date:   "2023-10-15",
			isZero: false,
		},
		{
			name:   "Empty date",
			date:   "",
			isZero: true,
		},
		{
			name:   "Invalid date",
			date:   "invalid",
			isZero: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := tt.date.Time()
			if got.IsZero() != tt.isZero {
				t.Errorf("Date.Time() IsZero = %v, want %v", got.IsZero(), tt.isZero)
			}

			if !tt.isZero {
				expectedYear, expectedMonth, expectedDay := got.Date()
				parsedYear, parsedMonth, parsedDay := 0, time.Month(0), 0

				// Parse the date string to get expected year, month, and day
				if dateObj, err := time.Parse("2006-01-02", string(tt.date)); err == nil {
					parsedYear, parsedMonth, parsedDay = dateObj.Date()
				}

				if expectedYear != parsedYear || expectedMonth != parsedMonth || expectedDay != parsedDay {
					t.Errorf("Date.Time() = %v-%v-%v, want %v-%v-%v",
						expectedYear, expectedMonth, expectedDay, parsedYear, parsedMonth, parsedDay)
				}
			}
		})
	}
}

func TestDateAddDays(t *testing.T) {
	tests := []struct {
		name     string
		date     Date
		delta    int
		expected Date
	}{
		{"Add 1 day", "2023-10-15", 1, "2023-10-16"},
		{"Add 30 days", "2023-10-15", 30, "2023-11-14"},
		{"Add negative days", "2023-10-15", -5, "2023-10-10"},
		{"Add 0 days", "2023-10-15", 0, "2023-10-15"},
		{"Cross month boundary forward", "2023-10-31", 1, "2023-11-01"},
		{"Cross month boundary backward", "2023-11-01", -1, "2023-10-31"},
		{"Cross year boundary forward", "2023-12-31", 1, "2024-01-01"},
		{"Cross year boundary backward", "2024-01-01", -1, "2023-12-31"},
		{"Leap year Feb 28 to 29", "2024-02-28", 1, "2024-02-29"},
		{"Leap year Feb 29 to Mar 1", "2024-02-29", 1, "2024-03-01"},
		{"Empty date", "", 5, ""},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := tt.date.AddDays(tt.delta); got != tt.expected {
				t.Errorf("Date.AddDays() = %v, want %v", got, tt.expected)
			}
		})
	}
}

func TestDateFromPage(t *testing.T) {
	tests := []struct {
		name     string
		page     string
		expected time.Time
		wantErr  bool
	}{
		{
			name:     "Valid page date",
			page:     "2023-10-15",
			expected: time.Date(2023, 10, 15, 0, 0, 0, 0, time.UTC),
			wantErr:  false,
		},
		{
			name:     "Invalid format",
			page:     "2023/10/15",
			expected: time.Time{},
			wantErr:  true,
		},
		{
			name:     "Empty string",
			page:     "",
			expected: time.Time{},
			wantErr:  true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := DateFromString(tt.page)
			if (err != nil) != tt.wantErr {
				t.Errorf("TimeFromPage() error = %v, wantErr %v", err, tt.wantErr)
				return
			}
			if !tt.wantErr {
				expectedYear, expectedMonth, expectedDay := tt.expected.Date()
				gotYear, gotMonth, gotDay := got.Time().Date()

				if gotYear != expectedYear || gotMonth != expectedMonth || gotDay != expectedDay {
					t.Errorf("TimeFromPage() = %v-%v-%v, want %v-%v-%v",
						gotYear, gotMonth, gotDay, expectedYear, expectedMonth, expectedDay)
				}
			}
		})
	}
}

func TestDateToPage(t *testing.T) {
	tests := []struct {
		name     string
		date     time.Time
		expected string
	}{
		{
			name:     "Regular date",
			date:     time.Date(2023, 10, 15, 0, 0, 0, 0, time.UTC),
			expected: "2023-10-15",
		},
		{
			name:     "First day of month",
			date:     time.Date(2023, 10, 1, 0, 0, 0, 0, time.UTC),
			expected: "2023-10-01",
		},
		{
			name:     "Last day of month",
			date:     time.Date(2023, 10, 31, 0, 0, 0, 0, time.UTC),
			expected: "2023-10-31",
		},
		{
			name:     "Leap year Feb 29",
			date:     time.Date(2024, 2, 29, 0, 0, 0, 0, time.UTC),
			expected: "2024-02-29",
		},
		{
			name:     "Zero time",
			date:     time.Time{},
			expected: "0001-01-01",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := TimeToString(tt.date); got != tt.expected {
				t.Errorf("TimeToString() = %v, want %v", got, tt.expected)
			}
		})
	}
}
