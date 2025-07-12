package obsidian

import (
	"github.com/stretchr/testify/assert"
	"journal/internal/datetime"
	"testing"
	"time"
)

func mustTimeFromString(t *testing.T, str string) datetime.Time {
	t.Helper()
	tt, err := datetime.TimeFromString(str)
	if err != nil {
		t.Fatalf("Failed to parse time %s: %v", str, err)
	}
	return tt
}

func TestMaybeParseEvent(t *testing.T) {
	assert.Nil(t, MaybeParseEvent(1, ""), "empty line doesn't contain an event")
	assert.Nil(t, MaybeParseEvent(1, "not an event"), "line without time doesn't contain an event")

	ev := MaybeParseEvent(1, "03:00 - 04:00 #tag1 #tag2 Some text")
	assert.NotNil(t, ev, "line with time should contain an event")
	assert.Equal(t, ev.StartTime, mustTimeFromString(t, "03:00"))
	assert.Equal(t, ev.EndTime, mustTimeFromString(t, "04:00"))
	assert.Equal(t, ev.Duration, time.Hour) // 1 hour duration
	assert.ElementsMatch(t, ev.Tags, []string{"tag1", "tag2"})
	assert.Equal(t, ev.Text, "#tag1 #tag2 Some text")
}

func TestMaybeParseEventOvernight(t *testing.T) {
	ev := MaybeParseEvent(1, "23:00 - 01:00 #tag1 #tag2 Some text")
	assert.NotNil(t, ev, "overnight event should be parsed")
	assert.Equal(t, ev.StartTime, mustTimeFromString(t, "23:00"))
	assert.Equal(t, ev.EndTime, mustTimeFromString(t, "01:00").AddMinutes(24*60)) // end time is next day
	assert.Equal(t, ev.Duration, 2*time.Hour)                                     // 2 hours duration
	assert.ElementsMatch(t, ev.Tags, []string{"tag1", "tag2"})
	assert.Equal(t, ev.Text, "#tag1 #tag2 Some text")
}

func TestMaybeParseEventNoEndTime(t *testing.T) {
	ev := MaybeParseEvent(1, "03:00 Some text #tag1 #tag2")
	assert.NotNil(t, ev, "line with start time but no end time should contain an event")
	assert.Equal(t, ev.StartTime, mustTimeFromString(t, "03:00"))
	assert.Zero(t, ev.EndTime)
	assert.True(t, ev.EndTime.IsEmpty(), "end time should be empty when not specified")
	assert.Equal(t, ev.Duration, 0*time.Hour) // no duration if no end time
	assert.ElementsMatch(t, ev.Tags, []string{"tag1", "tag2"})
	assert.Equal(t, ev.Text, "Some text #tag1 #tag2")
}

func TestEvent_String(t *testing.T) {
	ev := Event{
		Line:      1,
		StartTime: mustTimeFromString(t, "03:00"),
		EndTime:   mustTimeFromString(t, "04:00"),
		Duration:  time.Hour,
		Text:      "Some text #tag1 #tag2",
		Tags:      []string{"tag1", "tag2"},
	}
	expected := "03:00 - 04:00 Some text #tag1 #tag2"
	assert.Equal(t, expected, ev.String(), "Event string representation should match expected format")
}
