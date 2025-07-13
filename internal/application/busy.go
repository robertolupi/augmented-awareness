package application

import (
	"fmt"
	"journal/internal/stats"
	"strings"
	"time"
)

func (a *App) BusyReport(startDate string, endDate string, expandTags bool, bucketSize time.Duration) (string, error) {
	pages, err := a.Vault.PageRange(startDate, endDate)
	if err != nil {
		return "", err
	}
	report, err := stats.NewBusyReport(stats.PeriodDaily, bucketSize)
	if err != nil {
		return "", err
	}
	for _, page := range pages {
		section, err := page.FindSection(a.JournalSection)
		if err != nil {
			continue
		}

		events, err := section.Events()
		if err != nil {
			continue
		}

		for _, event := range events {
			err := report.AddEvent(event.StartTime.Time(), event.Duration, event.Tags)
			if err != nil {
				return "", err
			}
		}
	}
	if expandTags {
		report.ExpandTags()
	}

	var buf strings.Builder
	fmt.Fprint(&buf, "Busy report from ", startDate, " to ", endDate, ":\n")
	formatString := "%40s\t%s  %.2f%%\n"
	fmt.Fprintf(&buf, formatString, "Total", report.Total, 100.0)
	fmt.Fprintf(&buf, formatString, "No tags", report.NoTags, float64(report.NoTags.Duration)/float64(report.Total.Duration)*100)
	for _, tagDuration := range report.SortedTags() {
		fmt.Fprintf(&buf, formatString, tagDuration.Tag, tagDuration.Histogram, tagDuration.Percent)
	}
	return buf.String(), nil
}
