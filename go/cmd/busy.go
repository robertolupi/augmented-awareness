package cmd

import (
	"fmt"
	"github.com/spf13/cobra"
	"journal/internal/obsidian"
	"journal/internal/stats"
	"log"
	"sort"
	"strings"
	"time"
)

var (
	busyStartDate  string
	busyEndDate    string
	busyExpandTags bool
	busyBucketSize time.Duration

	busyCmd = &cobra.Command{
		Use:   "busy",
		Short: "Show how I spent my time",
		Long:  `Show how I spent my time in the last week.`,
		Run: func(cmd *cobra.Command, args []string) {
			if err := initVault(); err != nil {
				log.Fatalf("Failed to initialize vault: %v", err)
			}

			var dateRange []string
			if busyStartDate != "" && busyEndDate != "" {
				start, err := time.Parse("2006-01-02", busyStartDate)
				if err != nil {
					log.Fatalf("Failed to parse start date: %v", err)
				}
				end, err := time.Parse("2006-01-02", busyEndDate)
				if err != nil {
					log.Fatalf("Failed to parse end date: %v", err)
				}

				for d := start; d.Before(end) || d.Equal(end); d = d.AddDate(0, 0, 1) {
					dateRange = append(dateRange, d.Format("2006-01-02"))
				}
			}

			var pages []*obsidian.Page
			var dates []string
			for _, date := range dateRange {
				page, err := vault.Page(date)
				if err != nil {
					log.Printf("Failed to get journal page for %s: %v", date, err)
					continue
				}
				pages = append(pages, page)
				dates = append(dates, date)
			}
			fmt.Printf("Found %d journal pages: %v\n", len(pages), dates)

			tags := make(map[string]*stats.Histogram)
			total, err := stats.NewTimeHistogram(stats.PeriodDaily, busyBucketSize)
			noTags, err := stats.NewTimeHistogram(stats.PeriodDaily, busyBucketSize)
			if err != nil {
				log.Fatalf("Failed to create histogram: %v", err)
			}

			for _, page := range pages {

				events, err := page.Events(journalSection)
				if err != nil {
					log.Printf("No events in journal page: %v", err)
					continue
				}

				for _, event := range events {
					add := true
					if len(event.Tags) == 0 {
						noTags.Add(event.Start, event.Duration)
					}
					for _, tag := range event.Tags {
						if tag == "" {
							continue
						}
						if _, ok := tags[tag]; !ok {
							tags[tag], _ = stats.NewTimeHistogram(stats.PeriodDaily, busyBucketSize)
						}
						tags[tag].Add(event.Start, event.Duration)
						if add {
							total.Add(event.Start, event.Duration)
							add = false
						}
					}
				}
			}

			if busyExpandTags {
				tags = expandTags(tags)
			}

			// Sort tags by duration in descending order by duration
			type line struct {
				Tag       string
				Histogram *stats.Histogram
				Percent   float64
			}
			var lines []line
			for tag, duration := range tags {
				lines = append(lines, line{Tag: tag, Histogram: duration})
			}
			for i := range lines {
				lines[i].Percent = float64(lines[i].Histogram.Duration) / float64(total.Duration) * 100
			}
			sort.Slice(lines, func(i, j int) bool {
				return lines[i].Histogram.Duration > lines[j].Histogram.Duration
			})
			formatString := "%40s\t%s  %.2f%%\n"
			fmt.Printf(formatString, "Total", total, 100.0)
			fmt.Printf(formatString, "No tags", noTags, float64(noTags.Duration)/float64(total.Duration)*100)
			fmt.Println("Tags sorted by duration:")
			for _, tagDuration := range lines {
				fmt.Printf(formatString, tagDuration.Tag, tagDuration.Histogram, tagDuration.Percent)
			}
		},
	}
)

func expandTags(tagsByDuration map[string]*stats.Histogram) map[string]*stats.Histogram {
	expanded := make(map[string]*stats.Histogram)
	count := make(map[string]int)
	for tag, histogram := range tagsByDuration {
		expanded[tag] = histogram
		count[tag] = 1
	}
	for tag, histogram := range tagsByDuration {
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
	return expanded
}

func initBusyCmd() {
	rootCmd.AddCommand(busyCmd)

	busyCmd.Flags().StringVar(&busyStartDate, "start", sixDaysAgo(), "Start date (YYYY-MM-DD)")
	busyCmd.Flags().StringVar(&busyEndDate, "end", today(), "End date (YYYY-MM-DD)")
	busyCmd.Flags().BoolVarP(&busyExpandTags, "expand-tags", "e", false, "Expand tags to show all sub-tags")
	busyCmd.Flags().DurationVar(&busyBucketSize, "bucket-size", 30*time.Minute, "Bucket size for histogram")
}
