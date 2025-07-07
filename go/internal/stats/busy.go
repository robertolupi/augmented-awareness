package stats

import (
	"sort"
	"strings"
	"time"
)

type BusyReport struct {
	// NoTags is the total time spent on events without tags.
	NoTags *Histogram
	// Total is the total time spent on all events with tags.
	Total *Histogram
	// Tags is a map of tag names to histograms, where each histogram contains the time spent on events with that tag.
	Tags map[string]*Histogram
}

type BusyReportTag struct {
	Tag       string
	Histogram *Histogram
	Percent   float64
}

func NewBusyReport(period Period, bucketSize time.Duration) (*BusyReport, error) {
	total, err := NewTimeHistogram(period, bucketSize)
	if err != nil {
		return nil, err
	}
	noTags, err := NewTimeHistogram(period, bucketSize)
	if err != nil {
		return nil, err
	}
	tags := make(map[string]*Histogram)
	return &BusyReport{
		Total:  total,
		NoTags: noTags,
		Tags:   tags,
	}, nil
}

func (br *BusyReport) AddEvent(start time.Time, duration time.Duration, tags []string) error {
	if len(tags) == 0 {
		br.NoTags.Add(start, duration)
		return nil
	}
	br.Total.Add(start, duration)
	for _, tag := range tags {
		if tag == "" {
			continue
		}
		if _, ok := br.Tags[tag]; !ok {
			histogram, err := NewTimeHistogram(br.Total.Period, br.Total.BucketSize)
			if err != nil {
				return err
			}
			br.Tags[tag] = histogram
		}
		br.Tags[tag].Add(start, duration)
	}
	return nil
}

// ExpandTags expands the tags in the BusyReport.
// If there are events with tags that have a common ancestor, it will create a histogram for the ancestor tag.
//
// Example:
// #father/son #father/daughter #mother/son
// will result in:
// #father #father/son #father/daughter #mother/son
//
// Note that #mother is not present because it is not a common ancestor of multiple tags.
func (br *BusyReport) ExpandTags() {
	expanded := make(map[string]*Histogram)
	count := make(map[string]int)
	for tag, histogram := range br.Tags {
		expanded[tag] = histogram
		count[tag] = 1
	}
	for tag, histogram := range br.Tags {
		if tag == "" {
			continue
		}
		parts := strings.Split(tag, "/")
		for i := len(parts) - 1; i > 0; i-- {
			subTag := strings.Join(parts[:i], "/")
			if _, ok := expanded[subTag]; !ok {
				expanded[subTag] = histogram.Copy()
				count[subTag] = 0
			} else {
				expanded[subTag].Merge(histogram)
				count[subTag]++
			}
		}
	}
	for tag := range expanded {
		if count[tag] > 0 {
			continue
		}
		delete(expanded, tag)
	}
	br.Tags = expanded
}

// SortedTags generates a report of the busy statistics.
// It returns a slice of BusyReportTag, sorted by duration in descending order.
func (br *BusyReport) SortedTags() []BusyReportTag {
	tags := make([]BusyReportTag, 0, len(br.Tags))
	for tag, histogram := range br.Tags {
		tags = append(tags, BusyReportTag{
			Tag:       tag,
			Histogram: histogram,
			Percent:   float64(histogram.Duration) / float64(br.Total.Duration) * 100,
		})
	}

	sort.Slice(tags, func(i, j int) bool {
		return tags[i].Histogram.Duration > tags[j].Histogram.Duration
	})

	return tags
}
