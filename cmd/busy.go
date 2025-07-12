package cmd

import (
	"fmt"
	"github.com/spf13/cobra"
	"journal/internal/datetime"
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
			var pages []*obsidian.Page

			pages, err := vault.PageRange(busyStartDate, busyEndDate)
			if err != nil {
				log.Fatalf("Failed to read pages: %v", err)
			}
			fmt.Printf("Found %d journal pages: %v\n", len(pages), pages)

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

	busyCmd.Flags().StringVar(&busyStartDate, "start", datetime.SixDaysAgo().String(), "Start date (YYYY-MM-DD)")
	busyCmd.Flags().StringVar(&busyEndDate, "end", datetime.Today().String(), "End date (YYYY-MM-DD)")
	busyCmd.Flags().BoolVarP(&busyExpandTags, "expand-tags", "e", false, "Expand tags to show all sub-tags")
	busyCmd.Flags().DurationVar(&busyBucketSize, "bucket-size", 30*time.Minute, "Bucket size for histogram")
}
