package cmd

import (
	"fmt"
	"github.com/spf13/cobra"
	"journal/internal/datetime"
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
			report, err := app.BusyReport(busyStartDate, busyEndDate, busyExpandTags, busyBucketSize)
			if err != nil {
				log.Fatalf("Failed to generate busy report: %v", err)
			}
			fmt.Println(report)
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
