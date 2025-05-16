package stats

import (
	"fmt"
	"time"
)

type Period time.Duration

const (
	PeriodDaily  = Period(24 * time.Hour)
	PeriodWeekly = Period(7 * 24 * time.Hour)
)

// Histogram is a histogram for time-based data.
type Histogram struct {
	Period     Period
	BucketSize time.Duration
	// buckets is a map of bucket start time to count.
	Buckets []int
	// total time added to the histogram.
	Duration time.Duration
}

// NewTimeHistogram creates a new Histogram with the given period and bucket size.
func NewTimeHistogram(period Period, bucketSize time.Duration) (*Histogram, error) {
	if period%Period(bucketSize) != 0 {
		return nil, fmt.Errorf("period %v is not a multiple of bucket size %v", period, bucketSize)
	}
	numBuckets := int(period / Period(bucketSize))
	return &Histogram{
		Period:     period,
		BucketSize: bucketSize,
		Buckets:    make([]int, numBuckets),
	}, nil
}

// Add adds a value to the histogram.
func (h *Histogram) Add(startTime time.Time, duration time.Duration) {
	periodStart := startTime.Truncate(time.Duration(h.Period))
	delta := startTime.Sub(periodStart)
	bucketIndex := int(delta / time.Duration(h.BucketSize))
	for d := duration; d > 0; d -= h.BucketSize {
		h.Buckets[bucketIndex]++
		bucketIndex = (bucketIndex + 1) % len(h.Buckets)
	}
	h.Duration += duration
}

func (h *Histogram) Copy() *Histogram {
	// Create a new histogram with the same period and bucket size.
	newHistogram := &Histogram{
		Period:     h.Period,
		BucketSize: h.BucketSize,
		Buckets:    make([]int, len(h.Buckets)),
		Duration:   h.Duration,
	}
	copy(newHistogram.Buckets, h.Buckets)
	return newHistogram
}

// Merge merges another histogram into this one.
func (h *Histogram) Merge(other *Histogram) error {
	if h.Period != other.Period || h.BucketSize != other.BucketSize {
		return fmt.Errorf("cannot merge histograms with different periods or bucket sizes")
	}
	for i := range h.Buckets {
		h.Buckets[i] += other.Buckets[i]
	}
	h.Duration += other.Duration
	return nil
}

var (
	blocks = []rune{
		'▁', '▂', '▃', '▄', '▅', '▆', '▇', '█',
	}
)

func (h *Histogram) String() string {
	// Create a string of blocks based on the histogram data.
	var blocksStr string
	maxValue := 1
	for _, count := range h.Buckets {
		if count > maxValue {
			maxValue = count
		}
	}
	for _, count := range h.Buckets {
		index := int(float64(count) / float64(maxValue) * float64(len(blocks)-1))
		blocksStr += string(blocks[index])
	}
	return fmt.Sprintf("%s %14s", blocksStr, h.Duration)
}
