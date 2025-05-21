package obsidian

import (
	"regexp"
	"strings"
	"time"
)

type Event struct {
	Line      int
	StartTime Time
	EndTime   Time
	Duration  time.Duration
	Text      string
	Tags      []string
}

func (event Event) String() string {
	var sb strings.Builder
	sb.WriteString(event.StartTime.String())
	if !event.EndTime.IsEmpty() {
		sb.WriteString(" - ")
		sb.WriteString(event.EndTime.String())
	}
	sb.WriteString(" ")
	sb.WriteString(event.Text)
	return sb.String()
}

// Events are lines that look like this:
// 03:00 - 04:00 #tag1 #tag2 Some text
// 03:00 Some text #tag1 #tag2

var eventRegex = regexp.MustCompile(`^(\d{2}:\d{2})\s*(-\s*(\d{2}:\d{2}))?\s*(.*?)$`)

func MaybeParseEvent(lineNo int, line string) *Event {
	matches := eventRegex.FindStringSubmatch(line)
	if matches == nil {
		return nil
	}

	var start, end Time
	var err error

	start, err = TimeFromString(matches[1])
	if err != nil {
		return nil
	}

	end, err = TimeFromString(matches[3])
	if err != nil {
		return nil
	}

	var duration time.Duration
	if !end.IsEmpty() {
		duration = end.Time().Sub(start.Time())
		if duration < 0 {
			return nil
		}
	}

	text := strings.TrimSpace(matches[4])

	var tags []string
	fields := strings.Fields(text)
	for _, field := range fields {
		if strings.HasPrefix(field, "#") {
			tags = append(tags, field[1:])
		}
	}

	return &Event{
		Line:      lineNo,
		StartTime: start,
		EndTime:   end,
		Duration:  duration,
		Text:      text,
		Tags:      tags,
	}
}
