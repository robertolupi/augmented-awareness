package stats

import (
	"testing"
	"time"
)

func TestNewTimeHistogram(t *testing.T) {
	tests := []struct {
		name       string
		period     Period
		bucketSize time.Duration
		wantErr    bool
	}{
		{
			name:       "valid daily with hourly buckets",
			period:     PeriodDaily,
			bucketSize: time.Hour,
			wantErr:    false,
		},
		{
			name:       "valid weekly with daily buckets",
			period:     PeriodWeekly,
			bucketSize: 24 * time.Hour,
			wantErr:    false,
		},
		{
			name:       "invalid period not multiple of bucket size",
			period:     PeriodDaily,
			bucketSize: 7 * time.Hour,
			wantErr:    true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			h, err := NewTimeHistogram(tt.period, tt.bucketSize)
			if (err != nil) != tt.wantErr {
				t.Errorf("NewTimeHistogram() error = %v, wantErr %v", err, tt.wantErr)
				return
			}
			if err != nil {
				return
			}

			// Verify the histogram was created correctly
			if h.Period != tt.period {
				t.Errorf("NewTimeHistogram() Period = %v, want %v", h.Period, tt.period)
			}
			if h.BucketSize != tt.bucketSize {
				t.Errorf("NewTimeHistogram() BucketSize = %v, want %v", h.BucketSize, tt.bucketSize)
			}

			expectedBuckets := int(tt.period / Period(tt.bucketSize))
			if len(h.Buckets) != expectedBuckets {
				t.Errorf("NewTimeHistogram() Buckets length = %v, want %v", len(h.Buckets), expectedBuckets)
			}
		})
	}
}

func TestTimeHistogram_Add(t *testing.T) {

	// Test cases
	baseTime := time.Date(2023, 1, 1, 0, 0, 0, 0, time.UTC)
	tests := []struct {
		name        string
		startTime   time.Time
		duration    time.Duration
		wantBuckets []int
	}{
		{
			name:      "add one hour at start of day",
			startTime: baseTime,
			duration:  time.Hour,
			wantBuckets: func() []int {
				buckets := make([]int, 24)
				buckets[0] = 1
				return buckets
			}(),
		},
		{
			name:      "add two hours spanning buckets",
			startTime: baseTime.Add(1*time.Hour + 30*time.Minute),
			duration:  2 * time.Hour,
			wantBuckets: func() []int {
				buckets := make([]int, 24)
				buckets[1] = 1
				buckets[2] = 1
				return buckets
			}(),
		},
		{
			name:      "add duration spanning day boundary",
			startTime: baseTime.Add(23 * time.Hour),
			duration:  2 * time.Hour,
			wantBuckets: func() []int {
				buckets := make([]int, 24)
				buckets[23] = 1
				buckets[0] = 1
				return buckets
			}(),
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Create a fresh histogram for each test
			h, _ := NewTimeHistogram(PeriodDaily, time.Hour)

			h.Add(tt.startTime, tt.duration)

			// Check if buckets match expected values
			for i, want := range tt.wantBuckets {
				if h.Buckets[i] != want {
					t.Errorf("Bucket[%d] = %d, want %d", i, h.Buckets[i], want)
				}
			}
		})
	}
}

func TestTimeHistogram_Merge(t *testing.T) {
	// Create two histograms with the same configuration
	h1, _ := NewTimeHistogram(PeriodDaily, time.Hour)
	h2, _ := NewTimeHistogram(PeriodDaily, time.Hour)

	// Add some data to both histograms
	baseTime := time.Date(2023, 1, 1, 0, 0, 0, 0, time.UTC)
	h1.Add(baseTime, time.Hour)
	h2.Add(baseTime.Add(2*time.Hour), time.Hour)

	// Expected result after merge
	expectedBuckets := make([]int, 24)
	expectedBuckets[0] = 1
	expectedBuckets[2] = 1

	// Test merge
	err := h1.Merge(h2)
	if err != nil {
		t.Errorf("Merge() error = %v", err)
	}

	// Verify merged buckets
	for i, want := range expectedBuckets {
		if h1.Buckets[i] != want {
			t.Errorf("After merge: Bucket[%d] = %d, want %d", i, h1.Buckets[i], want)
		}
	}

	// Test merge with incompatible histograms
	h3, _ := NewTimeHistogram(PeriodWeekly, time.Hour)
	err = h1.Merge(h3)
	if err == nil {
		t.Error("Merge() with incompatible period should return error")
	}

	h4, _ := NewTimeHistogram(PeriodDaily, 2*time.Hour)
	err = h1.Merge(h4)
	if err == nil {
		t.Error("Merge() with incompatible bucket size should return error")
	}
}

func TestTimeHistogram_AddEdgeCases(t *testing.T) {
	// Create a daily histogram with hourly buckets
	h, _ := NewTimeHistogram(PeriodDaily, time.Hour)

	// Test adding zero duration
	baseTime := time.Date(2023, 1, 1, 10, 0, 0, 0, time.UTC)
	h.Add(baseTime, 0)

	// Verify no buckets were incremented
	for i, count := range h.Buckets {
		if count != 0 {
			t.Errorf("Bucket[%d] = %d after adding zero duration, want 0", i, count)
		}
	}

	// Test adding very large duration (multiple periods)
	h, _ = NewTimeHistogram(PeriodDaily, time.Hour)
	h.Add(baseTime, 48*time.Hour)

	// Verify all buckets were incremented twice
	for i, count := range h.Buckets {
		if count != 2 {
			t.Errorf("Bucket[%d] = %d after adding 48 hours, want 2", i, count)
		}
	}
}
