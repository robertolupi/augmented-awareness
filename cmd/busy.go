package cmd

import (
	"fmt"
	"github.com/spf13/cobra"
	"journal/internal/obsidian"
	"journal/internal/stats"
	"log"
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

			report, err := stats.NewBusyReport(stats.PeriodDaily, busyBucketSize)
			if err != nil {
				log.Fatalf("Failed to create busy report: %v", err)
			}

			for _, page := range pages {

				section, err := page.FindSection(journalSection)
				if err != nil {
					log.Printf("Failed to find section %s in page %s: %v", journalSection, page.Path, err)
					continue
				}

				events, err := section.Events()
				if err != nil {
					log.Printf("No events in section %s in page %s: %v", journalSection, page.Path, err)
					continue
				}

				for _, event := range events {
					err := report.AddEvent(event.StartTime.Time(), event.Duration, event.Tags)
					if err != nil {
						log.Fatalf("Failed to add event to report: %v", err)
					}
				}
			}

			if busyExpandTags {
				report.ExpandTags()
			}

			// Sort tags by duration in descending order by duration
			sortedTags := report.SortedTags()
			formatString := "%40s\t%s  %.2f%%\n"
			fmt.Printf(formatString, "Total", report.Total, 100.0)
			fmt.Printf(formatString, "No tags", report.NoTags, float64(report.NoTags.Duration)/float64(report.Total.Duration)*100)
			fmt.Println("Tags sorted by duration:")
			for _, tagDuration := range sortedTags {
				fmt.Printf(formatString, tagDuration.Tag, tagDuration.Histogram, tagDuration.Percent)
			}
		},
	}
)

func initBusyCmd() {
	rootCmd.AddCommand(busyCmd)

	busyCmd.Flags().StringVar(&busyStartDate, "start", sixDaysAgo(), "Start date (YYYY-MM-DD)")
	busyCmd.Flags().StringVar(&busyEndDate, "end", today(), "End date (YYYY-MM-DD)")
	busyCmd.Flags().BoolVarP(&busyExpandTags, "expand-tags", "e", false, "Expand tags to show all sub-tags")
	busyCmd.Flags().DurationVar(&busyBucketSize, "bucket-size", 30*time.Minute, "Bucket size for histogram")
}
