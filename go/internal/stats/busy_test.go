package stats

import (
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
)

func TestNewBusyReport(t *testing.T) {
	br, err := NewBusyReport(PeriodDaily, 15*time.Minute)
	assert.NoError(t, err)
	assert.NotNil(t, br)
	assert.NotNil(t, br.Total)
	assert.NotNil(t, br.NoTags)
	assert.NotNil(t, br.Tags)
}

func TestBusyReport_AddEvent(t *testing.T) {
	br, err := NewBusyReport(PeriodDaily, 15*time.Minute)
	assert.NoError(t, err)

	start := time.Now()
	duration := time.Hour

	// Event with no tags
	err = br.AddEvent(start, duration, nil)
	assert.NoError(t, err)
	assert.Equal(t, duration, br.NoTags.Duration)
	assert.Equal(t, time.Duration(0), br.Total.Duration)

	// Event with tags
	err = br.AddEvent(start, duration, []string{"tag1", "tag2"})
	assert.NoError(t, err)
	assert.Equal(t, duration, br.Total.Duration)
	assert.Equal(t, duration, br.Tags["tag1"].Duration)
	assert.Equal(t, duration, br.Tags["tag2"].Duration)

	// Tags histogram should have the same period and bucket size as the report
	assert.Equal(t, br.Total.Period, br.Tags["tag1"].Period)
	assert.Equal(t, br.Total.BucketSize, br.Tags["tag1"].BucketSize)
}

func TestBusyReport_ExpandTags(t *testing.T) {
	br, err := NewBusyReport(PeriodDaily, 15*time.Minute)
	assert.NoError(t, err)

	start := time.Now()
	duration := time.Hour

	br.AddEvent(start, duration, []string{"a/b/c"})
	br.AddEvent(start, duration, []string{"a/b/d"})
	br.AddEvent(start, duration, []string{"x/y"})

	br.ExpandTags()

	assert.Contains(t, br.Tags, "a/b")
	assert.Contains(t, br.Tags, "a")
	assert.NotContains(t, br.Tags, "x")

	assert.Equal(t, 2*duration, br.Tags["a/b"].Duration)
	assert.Equal(t, 2*duration, br.Tags["a"].Duration)
}

func TestBusyReport_SortedTags(t *testing.T) {
	br, err := NewBusyReport(PeriodDaily, 15*time.Minute)
	assert.NoError(t, err)

	start := time.Now()

	br.AddEvent(start, time.Hour, []string{"tag1"})
	br.AddEvent(start, 2*time.Hour, []string{"tag2"})
	br.AddEvent(start, 3*time.Hour, []string{"tag3"})

	sorted := br.SortedTags()

	assert.Len(t, sorted, 3)
	assert.Equal(t, "tag3", sorted[0].Tag)
	assert.Equal(t, "tag2", sorted[1].Tag)
	assert.Equal(t, "tag1", sorted[2].Tag)
}
